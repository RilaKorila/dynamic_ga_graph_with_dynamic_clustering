import array
import random, os

import matplotlib.pyplot as plt
import numpy as np
from constants import PNG_PATH, SUPERGRAPH_PNG_PATH
from deap import base, creator, tools
from deap.benchmarks.tools import hypervolume
from history_evaluation_stats import HistoryEvaluationStats
from my_mutation import muSmall
from layouts import define_layout, visualize_summarized_graph

class NSGA2:
    def __init__(self, obfunc, write_layout_file_func, dynamic_graph, timestamp, previous_best_layouts=None, previous_timestamp=None):
        self.timestamp = timestamp
        self.previous_timestamp = previous_timestamp
        self.previous_best_layouts = previous_best_layouts
        self.has_previous_layout = previous_best_layouts is not None

        ## 問題固有のパラメタ   
        # 遺伝子が取り得る値の範囲を指定
        self.MIN_COORDINATE, self.MAX_COORDINATE = -10.0, 10.0
        # 1つの個体内の遺伝子の数を指定 (4の倍数でないとselTournamentDCDでエラー)
        self.NDIM = 20  # Experiment 1-S

        self.layout_counter = 0

        # 適合度を最小化することで最適化されるような適合度クラスの作成
        creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
        # 個体クラスIndividualを作成
        creator.create(
            "Individual", array.array, typecode="d", fitness=creator.FitnessMin
        )

        ### 各種関数の設定
        # Toolboxの作成
        self.toolbox = base.Toolbox()

        # 遺伝子を生成する関数"attribute"を登録
        self.toolbox.register(
            "attribute", random.uniform, self.MIN_COORDINATE, self.MAX_COORDINATE
        )

        # 遺伝子を生成する関数 "create_individual"を登録 (ここで生成される遺伝子は2つ分のレイアウトの座標リスト)
        self.toolbox.register("create_layout", self.create_individual)

        self.debug_layout_counter = 0

        # 個体を生成する関数”individual"を登録
        # gen_len回 toolbox.attributeを実行し、その値をcreator.Individualに格納して返す関数individualを定義 => tools.initRpeatを引数なしで呼び出せるように変化
        # self.toolbox.register(
        #     "individual",
        #     tools.initRepeat,
        #     creator.Individual,  # initRepeatの1つ目の引数
        #     self.toolbox.attribute,  # initRepeatの2つ目の引数
        #     gen_len,  # initRepeatの3つ目の引数
        # )
        # initRepeat; https://github.com/DEAP/deap/blob/a321a568d68c56295652030ab0947cd377026ec1/deap/tools/init.py#L2

        # initIterate: https://github.com/DEAP/deap/blob/a321a568d68c56295652030ab0947cd377026ec1/deap/tools/init.py#L26C1-L51C34
        self.toolbox.register(
            "individual",
            tools.initIterate,
            creator.Individual,  # initIterateの1つ目の引数: container
            self.toolbox.create_layout,  # initIterateの2つ目の引数: generator
        )

        # 個体集団を生成する関数"population"を登録
        self.toolbox.register(
            "population", tools.initRepeat, list, self.toolbox.individual
        )

        ## 目的関数の設定
        self.obfunc = obfunc

        ## layout.csvを出力用の関数を設定
        self.write_layout_file_func = write_layout_file_func

        # hypervolume出力用の変数宣言を追加
        self.hv_fname = "hypervolumn_plot.txt"

        # 現在のタイムスタンプのグラフとコミュニティのみを生成 
        self.communities = dynamic_graph.get_communities(timestamp)
        self.summarized_graph = dynamic_graph.get_summarized_graph(timestamp)

        # 遺伝子長の計算
        self.current_layout_gene_len = len(self.communities) * 2  # 現在のレイアウトの遺伝子長
        self.previous_layout_gene_len = len(self.previous_best_layouts[0]) if self.has_previous_layout else 0
        self.total_gene_len = self.current_layout_gene_len + self.previous_layout_gene_len

    def setting(self):
        ## 選択
        # 個体選択法"select"を登録
        self.toolbox.register("select", tools.selNSGA2)

        ## 交叉
        # 交叉を行う関数"mate"を登録
        self.toolbox.register(
            "mate",
            self.crossover_only_current_layout,
            low=self.MIN_COORDINATE,
            up=self.MAX_COORDINATE,
            eta=20.0,
        )

        ## 突然変異
        # 変異を行う関数"mutate"を登録
        self.toolbox.register(
            "mutate",
            self.mutate_only_current_layout,
            low=self.MIN_COORDINATE,
            up=self.MAX_COORDINATE,
            eta=40.0,
            indpb=1.0 / self.NDIM,
        )

        # オリジナルのmutation関数に変更
        # self.toolbox.register(
        #     "mutate",
        #     muSmall,
        #     low=self.MIN_COORDINATE,
        #     up=self.MAX_COORDINATE,
        # )
        # 評価関数"evaluate"を登録
        # self.toolbox.register("evaluate", self.obfunc)


        # 評価関数"evaluate"を登録
        self.history_evaluation_stats = HistoryEvaluationStats(self.obfunc, self.timestamp)
        self.toolbox.register("evaluate", self.history_evaluation_stats.evaluate_fitness)

        if self.has_previous_layout:
            self.previous_history_evaluation_stats = HistoryEvaluationStats(self.obfunc, self.previous_timestamp)
            self.toolbox.register("evaluate_previous_layout", self.previous_history_evaluation_stats.evaluate_fitness)


    def create_individual(self):
        """個体を生成する
        
        現在のタイムスタンプの初期レイアウトと、前のタイムスタンプのレイアウトを組み合わせる
        順序は [current_layout, previous_layout]

        前のタイムスタンプの良い解が存在する場合は、一定の確率でそれらを使用し、それ以外は新規に生成する。
        """
        # 現在のタイムスタンプのレイアウトを生成
        pos = define_layout(self.summarized_graph)
        
        ## 検証用 ##
        dir_name = self.__create_directory(SUPERGRAPH_PNG_PATH + f"{self.timestamp}/")
        visualize_summarized_graph(self.summarized_graph, pos, 
                                 f"{dir_name}initial_layout{self.layout_counter}.png")
        self.layout_counter += 1
        ###########

        # 現在のレイアウトの座標リストを作成
        current_layout_list = []
        for (x, y) in pos.values():
            current_layout_list.append(x)
            current_layout_list.append(y)

        # 前のタイムスタンプのレイアウトがある場合は、それと組み合わせる
        # TODO previous_best_layoutsの数は調整できるようにしたい
        previous_layout = random.choice(self.previous_best_layouts)[:] if self.has_previous_layout else []
        # 現在のレイアウトと前のレイアウトを結合（現在が先）
        combined_layout = current_layout_list.copy()
        combined_layout.extend(previous_layout)
        if len(combined_layout) != self.total_gene_len:
            raise Exception("community数に対して、遺伝子の長さが異なります")
        
        return combined_layout
    
    # def create_initial_layout(self):
    #  print(self.gene_len)
    #  return [ 0.5 for i in range(self.gene_len)]
    

    def main(self, fname="output.txt"):
        self.setting()

        # NDIMを2倍に変更（2つのレイアウト分）
        NGEN = 20  # 繰り返し世代数・Experiment 1-S
        MU = self.NDIM  # 集団内の個体数
        CXPB = 0.9  # 交叉率

        # 世代ループ中のログに何を出力するかの設定
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)

        logbook = tools.Logbook()
        logbook.header = "gen", "evals", "std", "min", "avg", "max"

        # 第一世代の生成
        pop = self.toolbox.population(n=MU)
        self.pop_init = pop[:]
        invalid_ind = [ind for ind in pop if not ind.fitness.valid]

        # 初期世代の評価
        self.evaluate(invalid_ind, 0)

        pop = self.toolbox.select(pop, len(pop))

        # 軸の上限と下限をfitnesses_initから算出
        fitnesses_init = np.array(
            [list(self.pop_init[i].fitness.values) for i in range(len(self.pop_init))]
        )

        # 軸の設定(軸の最小値/最大値は、プロット点の最小値/最大値より少しずらす)
        self.set_axis(fitnesses_init)

        # Hyper Volume算出用のreference point
        self.ref_hv = [max(fitnesses_init[:, 0]), max(fitnesses_init[:, 1])]

        # 初期レイアウトをcsv出力
        self.write_layout_file_func(0, pop, self.timestamp)
        if self.has_previous_layout:
            self.write_layout_file_func(0, pop, self.previous_timestamp)

        record = stats.compile(pop)
        logbook.record(gen=0, evals=len(invalid_ind), **record)

        # ファイルにログを書き込む
        self.write_log(PNG_PATH + fname, logbook)

        # 最適計算の実行
        for gen in range(1, NGEN):
            # 終了条件をhvに変える → while条件へ
            # gen = 1
            # hv = 0.0
            # hv_counter = 0
            # while (hv < 5.35 or hv_counter < 4):
            # 子母集団生成
            offspring = tools.selTournamentDCD(pop, len(pop))
            offspring = [self.toolbox.clone(ind) for ind in offspring]

            # 交叉と突然変異
            for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
                # 交叉させる個体を選択
                if random.random() <= CXPB:
                    # 交叉
                    self.toolbox.mate(ind1, ind2)

                # 突然変異
                self.toolbox.mutate(ind1)
                self.toolbox.mutate(ind2)

                # 交叉と突然変異させた個体は適応度を削除する
                del ind1.fitness.values, ind2.fitness.values

            # 適応度を削除した個体について適応度の再評価を行う
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]

            # 評価
            self.evaluate(invalid_ind, gen)

            # 過去の世代と新しい世代の中から
            # 次世代を選択
            pop = self.toolbox.select(pop + offspring, MU)

            # 統計情報を記録
            record = stats.compile(pop)
            logbook.record(gen=gen, evals=len(invalid_ind), **record)

            # hypervolumeを算出
            hv = hypervolume(pop, self.ref_hv) 

            # ファイルにログを書き込む
            self.write_log(PNG_PATH + fname, logbook)
            self.write_hv(PNG_PATH + self.hv_fname, gen, hv)

            # 散布図を保存
            self.viz(pop, gen)

            # 終了条件をhvに変えたことにより変更
            # gen += 1
            # if hv >= 5.5:
            #     hv_counter += 1

        # 最終世代のハイパーボリュームを出力
        # [11.0, 11.0] は Reference Point (参照点): 目的関数と同じだけ指定
        # ハイパーボリュームの値が大きい = パレートラインが広範囲に広がっている = 良いパレートライン
        hv = hypervolume(pop, self.ref_hv)
        print("Final population hypervolume is %f" % hv)
        self.write_hv(PNG_PATH + self.hv_fname, gen, hv)

        # 最終的に残った遺伝子を全てファイル出力
        self.write_layout_file_func(gen, pop, self.timestamp)  
        if self.has_previous_layout:
            self.write_layout_file_func(gen, pop, self.previous_timestamp)  

        # 実験：final condition決定用
        self.viz_final_result()

        return pop, self.pop_init, logbook

    def set_axis(self, fitnesses_init):
        """
        散布図用の軸の上限・下限を算出する

        Args:
            fitnesses_init (numpy.ndarray): 初期世代の適応度
        """
        self.PLOT_XLIM_MIN = (
            min(fitnesses_init[:, 0]) - max(fitnesses_init[:, 0]) / 100.0
        )
        self.PLOT_XLIM_MAX = (
            max(fitnesses_init[:, 0]) + max(fitnesses_init[:, 0]) / 100.0
        )
        self.PLOT_YLIM_MIN = (
            min(fitnesses_init[:, 1]) - max(fitnesses_init[:, 1]) / 10.0
        )
        self.PLOT_YLIM_MAX = (
            max(fitnesses_init[:, 1]) + max(fitnesses_init[:, 1]) / 10.0
        )
    
    def evaluate(self, invalid_ind, gen):
        """
        適応度を評価する。評価結果は、ind.fitness.valuesに書き込む。

        Args:
            invalid_ind (list): 評価する個体
            gen (int): 世代番号
        """
        self.history_evaluation_stats.add_individuals(invalid_ind, gen)
        self.history_evaluation_stats.write_csv()
        if self.has_previous_layout:
            self.previous_history_evaluation_stats.add_individuals(invalid_ind, gen)
            self.previous_history_evaluation_stats.write_csv()

        # 既存の評価関数を2つのレイアウトで個別に評価
        for ind in invalid_ind:
            # 現在のレイアウトの評価
            current_layout_plist = ind[:self.current_layout_gene_len]
            current_fitness = self.toolbox.evaluate(
                current_layout_plist,
                gen,
                gen
            )

            # 前のレイアウトがある場合は評価
            if self.has_previous_layout:
                previous_layout_plist = ind[self.current_layout_gene_len:]
                previous_fitness = self.toolbox.evaluate_previous_layout(
                    previous_layout_plist,
                    gen,
                    gen
                )
                # 2つのレイアウトの評価値の平均を取る
                sprawl = (current_fitness[0] + previous_fitness[0]) / 2
                clutter = (current_fitness[1] + previous_fitness[1]) / 2
            else:
                # 前のレイアウトがない場合は現在のレイアウトの評価のみ
                sprawl = current_fitness[0]
                clutter = current_fitness[1]
            
            ind.fitness.values = (sprawl, clutter)

    def write_log(self, path, logbook):
        """
        ログを書き込む

        Args:
            path (str): ログを書き込むファイルへのパス
            logbook (deap.tools.Logbook): ログブック
        """
        with open(path, "a") as f:
            f.write(logbook.stream)
            f.write("\n")

    def write_hv(self, path, gen, hv):
        """
        HyperVolumeをファイルに書き込む    

        Args:
            path (str): HyperVolumeを書き込むファイルへのパス
            gen (int): 世代番号
            hv (float): HyperVolume
        """
        with open(path, "a") as f:
            f.write("%d, %f" % (gen, hv))
            f.write("\n")

    ## 初期サンプルと各世代(gen)の可視化
    def viz(self, pop, gen):
        fitnesses_init = np.array(
            [list(self.pop_init[i].fitness.values) for i in range(len(self.pop_init))]
        )
        fitnesses = np.array([list(pop[i].fitness.values) for i in range(len(pop))])

        # 現在のレイアウトと前のレイアウトに分割
        current_layout_fitnesses_init = fitnesses_init[:self.current_layout_gene_len]
        current_layout_fitnesses = fitnesses[:self.current_layout_gene_len]
        
        # 現在のレイアウトの可視化
        self.__vis_each_result_scatterplot(current_layout_fitnesses_init, 
                                         current_layout_fitnesses, 
                                         gen, 
                                         self.timestamp)
        self.__save_fitness_coordinates(current_layout_fitnesses_init, 
                                      current_layout_fitnesses, 
                                      gen,
                                      self.timestamp)
        
        # 前のレイアウトがある場合は可視化
        if self.has_previous_layout:
            previous_layout_fitnesses_init = fitnesses_init[self.current_layout_gene_len:]
            previous_layout_fitnesses = fitnesses[self.current_layout_gene_len:]
            
            self.__vis_each_result_scatterplot(previous_layout_fitnesses_init, 
                                             previous_layout_fitnesses, 
                                             gen, 
                                             self.previous_timestamp)
            self.__save_fitness_coordinates(previous_layout_fitnesses_init, 
                                          previous_layout_fitnesses, 
                                          gen,
                                          self.previous_timestamp)

    def __vis_each_result_scatterplot(self, fitnesses_init, fitnesses, gen, timestamp):
        fig = plt.figure()
        plt.plot(fitnesses_init[:, 0], fitnesses_init[:, 1], "b.", label="Initial")
        plt.plot(fitnesses[:, 0], fitnesses[:, 1], "r.", label="Optimized")

        if np.isnan(self.PLOT_XLIM_MIN):
            self.PLOT_XLIM_MIN = 0
        if np.isnan(self.PLOT_XLIM_MAX):
            self.PLOT_XLIM_MAX = 1
        if np.isnan(self.PLOT_YLIM_MIN):
            self.PLOT_YLIM_MIN = 0
        if np.isnan(self.PLOT_YLIM_MAX):
            self.PLOT_YLIM_MAX = 1

        plt.xlim(self.PLOT_XLIM_MIN, self.PLOT_XLIM_MAX)
        plt.ylim(self.PLOT_YLIM_MIN, self.PLOT_YLIM_MAX)

        # add label to each plot: init
        for i, (x, y) in enumerate(zip(fitnesses_init[:, 0], fitnesses_init[:, 1])):
            plt.annotate(str(i), (x, y))

        # add label to each plot: the generation
        for i, (x, y) in enumerate(zip(fitnesses[:, 0], fitnesses[:, 1])):
            plt.annotate(str(i), (x, y))

        plt.legend(loc="upper right")
        plt.title("fitnesses")
        plt.xlabel("sprawl")
        plt.ylabel("clutter")
        plt.grid(True)

        dir_name = self.__create_directory(PNG_PATH + f"{timestamp}/")
        fig.savefig(dir_name + "result" + str(gen) + ".png")

    def __save_fitness_coordinates(self, fitnesses_init, fitnesses, gen, timestamp):
        dir_name = self.__create_directory(PNG_PATH + f"{timestamp}/")
        # save fitness coordinates in a txt file
        with open(dir_name + "fitness.txt", "a") as f:
            if gen == 1:
                f.write("\n" + "initial generation\n")
                np.savetxt(f, fitnesses_init, delimiter=",")

            f.write("\n" + str(gen) + "generation\n")
            np.savetxt(f, fitnesses, delimiter=",")

    def viz_final_result(self):
        ## 1つ目のレイアウト
        # csv 出力
        self.history_evaluation_stats.output_csv()
        # 散布図描画
        self.__viz_scatter_plot(self.history_evaluation_stats.get_initial_pops(),
                                 self.history_evaluation_stats.get_final_pops())

        ## 2つ目のレイアウト
        if self.has_previous_layout:
            # csv 出力
            self.previous_history_evaluation_stats.output_csv()
            # 散布図描画
            self.__viz_scatter_plot(self.previous_history_evaluation_stats.get_initial_pops(),
                                    self.previous_history_evaluation_stats.get_final_pops())


    def __viz_scatter_plot(self, initial_pops, final_pops):
        fig = plt.figure()
        plt.plot(initial_pops["sprawl"], initial_pops["clutter"], "b.", label="Initial")
        plt.plot(final_pops["sprawl"], final_pops["clutter"], "r.", label="Optimized")

        plt.xlim(self.PLOT_XLIM_MIN, self.PLOT_XLIM_MAX)
        plt.ylim(self.PLOT_YLIM_MIN, self.PLOT_YLIM_MAX)

        # add label to each plot: init
        for i, (x, y) in enumerate(
            zip(initial_pops["sprawl"], initial_pops["clutter"])
        ):
            plt.annotate(str(i), (x, y))

        # add label to each plot: the generation
        for i, (x, y) in enumerate(zip(final_pops["sprawl"], final_pops["clutter"])):
            plt.annotate(str(i), (x, y))

        plt.legend(loc="upper right")
        plt.title("fitnesses")
        plt.xlabel("sprawl")
        plt.ylabel("clutter")
        plt.grid(True)

        fig.savefig(PNG_PATH + "final_plot_result.png")

    def __create_directory(self, directory_name):
        os.makedirs(directory_name, exist_ok=True)
        return directory_name

    def crossover_only_current_layout(self, ind1, ind2, eta, low, up):
        """現在のレイアウトと過去のレイアウトを分けて交叉を行う関数
        
        Args:
            ind1 (list): 交叉する個体1
            ind2 (list): 交叉する個体2
            eta (float): 交叉の集中度 （交叉の混雑度。高いetaは親に似た交叉体を生成し、
                低いetaはより大きく異なる解を生成する。）
            low (list): 探索空間の下限
            up (list): 探索空間の上限

        Returns:
            tuple: 交叉後の個体1と個体2のタプル
        """
        # 現在のレイアウト部分のみを交叉
        ind1_current_layout = ind1[:self.current_layout_gene_len]
        ind2_current_layout = ind2[:self.current_layout_gene_len]
        ind1_current_layout, ind2_current_layout = tools.cxSimulatedBinaryBounded(ind1_current_layout, ind2_current_layout, eta, low, up)

        # 過去のレイアウト部分のみを交叉
        if self.has_previous_layout:
            ind1_previous_layout = ind1[self.current_layout_gene_len:]
            ind2_previous_layout = ind2[self.current_layout_gene_len:]

            # 交叉後の個体を返す [現在のtimestampのレイアウト, previous_timestampのレイアウト] の順
            ind1_current_layout = ind1_current_layout.extend(ind1_previous_layout)
            ind2_current_layout = ind2_current_layout.extend(ind2_previous_layout)

        return ind1_current_layout, ind2_current_layout

    def mutate_only_current_layout(self, ind, eta, low, up, indpb):
        """現在のレイアウトのみを突然変異させる関数
        
        Args:
            ind (list): 突然変異させる個体
            eta (float): 突然変異の集中度（突然変異の混雑度。高いetaは親に似た突然変異体を生成し、
                低いetaはより大きく異なる解を生成する。）
            low (list): 探索空間の下限
            up (list): 探索空間の上限
            indpb (float): 突然変異の確率

        Returns:
            A tuple of one individual.
        """
        ind_current_layout = ind[:self.current_layout_gene_len]
        # tools.mutPolynomialBounded は tapleを返すので、[0]を取る
        mutated_ind = tools.mutPolynomialBounded(ind_current_layout, eta, low, up, indpb)[0]

        if self.has_previous_layout:
            # previous_layoutは突然変異せずそのまま
            ind_previous_layout = ind[self.current_layout_gene_len:]
            mutated_ind = mutated_ind.extend(ind_previous_layout)

        # mutate メソッドは tuple を返すので、このメソッドも揃える
        return mutated_ind,
