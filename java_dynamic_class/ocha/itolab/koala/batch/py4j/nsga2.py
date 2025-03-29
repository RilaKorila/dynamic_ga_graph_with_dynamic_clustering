import array
import random, os

import matplotlib.pyplot as plt
import numpy as np
from constants import PNG_PATH, SUPERGRAPH_PNG_PATH
from deap import base, creator, tools
from deap.benchmarks.tools import hypervolume
from history_evaluation_stats import HistoryEvaluationStats
from my_mutation import muSmall
from layouts import define_layout, visualize_sammarized_graph
from dynamic_graph import DynamicGraph
from community_detect import get_community_detection_result

class NSGA2:
    def __init__(self, obfunc, write_layout_file_func):
        ## 問題固有のパラメタ
        # 遺伝子が取り得る値の範囲を指定
        self.MIN_COORDINATE, self.MAX_COORDINATE = -10.0, 10.0
        # 1つの個体内の遺伝子の数を指定 (4の倍数でないとselTournamentDCDでエラー)
        self.NDIM = 20  # Experiment 1-S

        # supergraphを作成する (community detectionも含む)
        dynamic_graph = DynamicGraph()

        self.first_layout_timestamp = 1
        self.second_layout_timestamp = 2
        
        # Community Detection 
        self.first_layout_communities = get_community_detection_result(self.first_layout_timestamp)  # 1つ目のレイアウト用
        self.second_layout_communities = get_community_detection_result(self.second_layout_timestamp)  # 2つ目のレイアウト用

        # それぞれのレイアウト用のグラフを作成
        self.sammarized_graph_first = dynamic_graph.create_summarized_graph(self.first_layout_communities, self.first_layout_timestamp)
        self.sammarized_graph_second = dynamic_graph.create_summarized_graph(self.second_layout_communities, self.second_layout_timestamp)

        # それぞれのレイアウトの遺伝子長を計算
        self.gene_len_first = len(self.first_layout_communities) * 2
        self.gene_len_second = len(self.second_layout_communities) * 2
        # 2つのレイアウトの合計遺伝子長
        self.total_gene_len = self.gene_len_first + self.gene_len_second
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

    def setting(self):
        ## 選択
        # 個体選択法"select"を登録
        self.toolbox.register("select", tools.selNSGA2)

        ## 交叉
        # 交叉を行う関数"mate"を登録
        self.toolbox.register(
            "mate",
            tools.cxSimulatedBinaryBounded,
            low=self.MIN_COORDINATE,
            up=self.MAX_COORDINATE,
            eta=20.0,
        )

        ## 突然変異
        # 変異を行う関数"mutate"を登録
        self.toolbox.register(
            "mutate",
            tools.mutPolynomialBounded,
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
        self.first_layout_history_evaluation_stats = HistoryEvaluationStats(self.obfunc, self.first_layout_timestamp)
        self.second_layout_hisotory_evaluation_stats = HistoryEvaluationStats(self.obfunc, self.second_layout_timestamp)
        self.toolbox.register("evaluate_first_layout", self.first_layout_history_evaluation_stats.evaluate_fitness)
        self.toolbox.register("evaluate_second_layout", self.second_layout_hisotory_evaluation_stats.evaluate_fitness)

    def create_individual(self):
        # create_initial_layout を2回呼び出して、2つのレイアウトを作成
        first_layout_plist = self.create_initial_layout(self.sammarized_graph_first, self.gene_len_first, self.first_layout_timestamp)
        second_layout_plist = self.create_initial_layout(self.sammarized_graph_second, self.gene_len_second, self.second_layout_timestamp)

        # 2つのレイアウトを組み合わせて、新しい個体を作成
        return first_layout_plist + second_layout_plist

    def create_initial_layout(self, graph, gene_len, timestamp):
        pos = define_layout(graph)

        ## 検証用 ##
        dir_name = self.__create_directory(SUPERGRAPH_PNG_PATH + f"{timestamp}/")
        visualize_sammarized_graph(graph, pos, f"{dir_name}initial_layout{self.layout_counter}.png")
        self.layout_counter += 1
        ###########

        # x_1, y_1, x_2, y_2, ... , x_n, y_n の順番で返す
        p_list = []
        for (x, y) in pos.values():
            p_list.append(x)
            p_list.append(y)

        if len(p_list) != gene_len:
            raise Exception("community数に対して、遺伝子の長さが異なります")
        return p_list
    
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

        ## clutterのstatsを算出
        self.first_layout_history_evaluation_stats.add_individuals(invalid_ind, 0)
        self.first_layout_history_evaluation_stats.write_csv()
        self.second_layout_hisotory_evaluation_stats.add_individuals(invalid_ind, 0)
        self.second_layout_hisotory_evaluation_stats.write_csv()

        # 既存の評価関数を2つのレイアウトで個別に評価
        for ind in invalid_ind:
            # 1つ目のレイアウトの評価
            first_layout_plist = ind[:self.gene_len_first]
            fitness1 = self.toolbox.evaluate_first_layout(
                first_layout_plist,
                0,
                0
            )

            # 2つ目のレイアウトの評価
            second_layout_plist = ind[self.gene_len_first:]
            fitness2 = self.toolbox.evaluate_second_layout(
                second_layout_plist,
                0,
                0
            )

            # 2つのレイアウトの評価値の平均を取る # TODO どの値をfitnessにするか考える
            sprawl = (fitness1[0] + fitness2[0]) / 2
            clutter = (fitness1[1] + fitness2[1]) / 2
            ind.fitness.values = (sprawl, clutter)

        pop = self.toolbox.select(pop, len(pop))

        # 軸の上限と下限をfitnesses_initから算出
        fitnesses_init = np.array(
            [list(self.pop_init[i].fitness.values) for i in range(len(self.pop_init))]
        )

        # 軸の設定(軸の最小値/最大値は、プロット点の最小値/最大値より少しずらす)
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
        # Hyper Volume算出用のreference point
        self.ref_hv = [max(fitnesses_init[:, 0]), max(fitnesses_init[:, 1])]

        # 初期レイアウトをcsv出力
        self.write_layout_file_func(0, pop, self.first_layout_timestamp)
        self.write_layout_file_func(0, pop, self.second_layout_timestamp)

        record = stats.compile(pop)
        logbook.record(gen=0, evals=len(invalid_ind), **record)

        with open(PNG_PATH + fname, "a") as f:
            f.write(logbook.stream)
            f.write("\n")

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

            ## clutterのstatsを算出
            self.first_layout_history_evaluation_stats.add_individuals(invalid_ind, gen)
            self.first_layout_history_evaluation_stats.write_csv()
            self.second_layout_hisotory_evaluation_stats.add_individuals(invalid_ind, gen)
            self.second_layout_hisotory_evaluation_stats.write_csv()

            # 既存の評価関数を2つのレイアウトで個別に評価
            for ind in invalid_ind:
                # 1つ目のレイアウトの評価
                first_layout_plist = ind[:self.gene_len_first]
                first_layout_fitness = self.toolbox.evaluate_first_layout(
                    first_layout_plist,
                    gen,
                    gen
                )

                # 2つ目のレイアウトの評価
                second_layout_plist = ind[self.gene_len_first:]
                second_layout_fitness = self.toolbox.evaluate_second_layout(
                    second_layout_plist,
                    gen,
                    gen
                )

                # 2つのレイアウトの評価値の平均を取る
                sprawl = (first_layout_fitness[0] + second_layout_fitness[0]) / 2
                clutter = (first_layout_fitness[1] + second_layout_fitness[1]) / 2
                ind.fitness.values = (sprawl, clutter) # TODO fitness の算出方法を考える

            # 過去の世代と新しい世代の中から
            # 次世代を選択
            pop = self.toolbox.select(pop + offspring, MU)

            # 統計情報を記録
            record = stats.compile(pop)
            logbook.record(gen=gen, evals=len(invalid_ind), **record)

            # hypervolumeを表示
            hv = hypervolume(pop, self.ref_hv)

            with open(PNG_PATH + fname, "a") as f:
                f.write(logbook.stream)
                f.write("\n")

            with open(PNG_PATH + self.hv_fname, "a") as f:
                f.write("%d, %f" % (gen, hv))
                f.write("\n")

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
        with open(PNG_PATH + self.hv_fname, "a") as f:
            f.write("%d, %f" % (gen, hv))
            f.write("\n")

        # 最終的に残った遺伝子を全てファイル出力
        self.write_layout_file_func(gen, pop, self.first_layout_timestamp)  
        self.write_layout_file_func(gen, pop, self.second_layout_timestamp)  

        # 実験：final condition決定用
        self.viz_final_result()

        return pop, self.pop_init, logbook

    ## 初期サンプルと各世代(gen)の可視化
    def viz(self, pop, gen):
        fitnesses_init = np.array(
            [list(self.pop_init[i].fitness.values) for i in range(len(self.pop_init))]
        )
        fitnesses = np.array([list(pop[i].fitness.values) for i in range(len(pop))])

        # first_layout と second_layout に分割
        first_layout_fitnesses_init = fitnesses_init[:self.gene_len_first]
        second_layout_fitnesses_init = fitnesses_init[self.gene_len_first:]
        first_layout_fitnesses = fitnesses[:self.gene_len_first]
        second_layout_fitnesses = fitnesses[self.gene_len_first:]

        self.__vis_each_result_scatterplot(first_layout_fitnesses_init, first_layout_fitnesses, gen, self.first_layout_timestamp)
        self.__vis_each_result_scatterplot(second_layout_fitnesses_init, second_layout_fitnesses, gen, self.second_layout_timestamp)

        self.__save_fitness_coordinates(first_layout_fitnesses_init, first_layout_fitnesses, self.first_layout_timestamp, gen)
        self.__save_fitness_coordinates(second_layout_fitnesses_init, second_layout_fitnesses, self.second_layout_timestamp, gen)

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

    def __save_fitness_coordinates(self, fitnesses_init, fitnesses, timestamp, gen):
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
        self.first_layout_history_evaluation_stats.output_csv()

        # 散布図描画
        self.__viz_scatter_plot(self.first_layout_history_evaluation_stats.get_initial_pops(),
                                 self.first_layout_history_evaluation_stats.get_final_pops())

        ## 2つ目のレイアウト
        # csv 出力
        self.second_layout_hisotory_evaluation_stats.output_csv()

        # 散布図描画
        self.__viz_scatter_plot(self.second_layout_hisotory_evaluation_stats.get_initial_pops(),
                                 self.second_layout_hisotory_evaluation_stats.get_final_pops())


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
