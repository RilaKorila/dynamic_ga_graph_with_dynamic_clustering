import array
import random, os

import numpy as np
from constants import PNG_PATH, SUPERGRAPH_PNG_PATH
from deap import base, creator, tools
from deap.benchmarks.tools import hypervolume
from history_evaluation_stats import HistoryEvaluationStats
from layouts import define_layout, visualize_summarized_graph


class NSGA2:
    def __init__(
        self,
        obfunc,
        write_layout_file_func,
        dynamic_graph,
        timestamp,
        previous_best_layouts=[],
        previous_timestamp=None,
    ):
        self.timestamp = timestamp
        self.previous_timestamp = previous_timestamp
        self.previous_best_layouts = previous_best_layouts
        self.has_previous_layout = len(previous_best_layouts) > 0

        ## 問題固有のパラメタ
        # 遺伝子が取り得る値の範囲を指定
        self.MIN_COORDINATE, self.MAX_COORDINATE = -10.0, 10.0
        # 1つの個体内の遺伝子の数を指定 (4の倍数でないとselTournamentDCDでエラー)
        self.NDIM = 20  # 1世代あたりの個体数 Experiment 1-S
        self.NGEN = 40  # 繰り返し世代数・Experiment 1-S

        self.layout_counter = 0

        # 適合度を最小化することで最適化されるような適合度クラスの作成
        if "FitnessMin" not in creator.__dict__:
            # creator.create("FitnessMin", base.Fitness, weights=(-1.0,)) 検証用
            creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0, -1.0))

        # 個体クラスIndividualを作成
        if "Individual" not in creator.__dict__:
            creator.create(
                "Individual", array.array, typecode="d", fitness=creator.FitnessMin  # type: ignore
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

        # 個体を生成する関数"individual"を登録
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
            creator.Individual,  # initIterateの1つ目の引数: container # type: ignore
            self.toolbox.create_layout,  # initIterateの2つ目の引数: generator # type: ignore
        )

        # 個体集団を生成する関数"population"を登録
        self.toolbox.register(
            "population", tools.initRepeat, list, self.toolbox.individual  # type: ignore
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
        self.dynamic_graph = dynamic_graph
        self.graph_info = dynamic_graph.get_graph_info(timestamp)

        if self.has_previous_layout:
            self.similar_cluster_pos_dict = dynamic_graph.get_similar_cluster_dict(
                self.timestamp
            )

        # 遺伝子長の計算
        self.current_layout_gene_len = (
            len(self.communities) * 2
        )  # 現在のレイアウトの遺伝子長
        self.previous_layout_gene_len = (
            len(self.previous_best_layouts[0]) if self.has_previous_layout else 0
        )
        self.total_gene_len = (
            self.current_layout_gene_len + self.previous_layout_gene_len
        )

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
            eta=5.0,
        )

        ## 突然変異
        # 変異を行う関数"mutate"を登録
        self.toolbox.register(
            "mutate",
            self.mutate_only_current_layout,
            low=self.MIN_COORDINATE,
            up=self.MAX_COORDINATE,
            eta=5.0,
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
        self.history_evaluation_stats = HistoryEvaluationStats(
            self.obfunc,
            self.previous_timestamp,
            self.timestamp,
            self.dynamic_graph,
            self.has_previous_layout,
            self.current_layout_gene_len,
        )
        self.toolbox.register(
            "evaluate", self.history_evaluation_stats.evaluate_fitness
        )

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
        visualize_summarized_graph(
            self.summarized_graph,
            pos,
            f"{dir_name}initial_layout{self.layout_counter}.png",
        )
        self.layout_counter += 1
        ###########

        # 現在のレイアウトの座標リストを作成
        current_layout_list = []
        for x, y in pos.values():
            current_layout_list.append(x)
            current_layout_list.append(y)

        if self.has_previous_layout:
            # 前のtimestampがある場合には、選択されたlayout番号を保存
            random_index = random.randint(0, len(self.previous_best_layouts) - 1)
            self.save_selected_genes(random_index, self.timestamp)

        # 前のタイムスタンプのレイアウトがある場合は、それと組み合わせる
        # TODO previous_best_layoutsの数は調整できるようにしたい
        previous_layout = (
            self.previous_best_layouts[random_index][:]
            if self.has_previous_layout
            else []
        )

        if self.has_previous_layout:
            # 前のタイムスタンプのレイアウトがある場合、類似クラスタは位置をそのまま使用する
            cluster_id_list = list(self.graph_info.keys())
            for cluster_id in cluster_id_list:
                if self.similar_cluster_pos_dict.get(cluster_id):
                    # 類似のclusterが存在する場合
                    previous_similar_cluster_ids = self.similar_cluster_pos_dict[
                        cluster_id
                    ]

                    # 類似のclusterが複数ある場合は順に処理する
                    for previous_similar_cluster_id in previous_similar_cluster_ids:
                        previous_pos_x = previous_layout[
                            int(previous_similar_cluster_id) * 2
                        ]
                        previous_pos_y = previous_layout[
                            int(previous_similar_cluster_id) * 2 + 1
                        ]

                        # current_layout_list のなかで previous_layout_of_similar_clusters に含まれているものはswap
                        current_layout_list[int(cluster_id) * 2] = previous_pos_x
                        current_layout_list[int(cluster_id) * 2 + 1] = previous_pos_y

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
        MU = self.NDIM  # 集団内の個体数
        CXPB = 0.9  # 交叉率

        # 世代ループ中のログに何を出力するかの設定
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)

        logbook = tools.Logbook()
        logbook.header = ("gen", "evals", "std", "min", "avg", "max")  # type: ignore

        # 第一世代の生成
        pop = self.toolbox.population(n=MU)  # type: ignore
        self.pop_init = pop[:]
        invalid_ind = [ind for ind in pop if not ind.fitness.valid]

        self.write_comment("初期世代")

        # 初期世代の評価
        self.evaluate(invalid_ind, 0)

        self.write_indi(invalid_ind)
        pop = self.toolbox.select(pop, len(pop))  # type: ignore

        # 軸の上限と下限をfitnesses_initから算出
        fitnesses_init = np.array(
            [list(self.pop_init[i].fitness.values) for i in range(len(self.pop_init))]
        )

        # self.ref_hv = [max(fitnesses_init[:, 0])] 検証用
        self.ref_hv = [
            max(fitnesses_init[:, 0]),
            max(fitnesses_init[:, 1]),
            max(fitnesses_init[:, 2]),
        ]

        # 初期レイアウトをcsv出力
        self.write_layout_files(0, pop)

        record = stats.compile(pop)
        logbook.record(gen=0, evals=len(invalid_ind), **record)

        # ファイルにログを書き込む
        self.write_log(PNG_PATH + fname, logbook)

        # 最適計算の実行
        for gen in range(1, self.NGEN):
            # 終了条件をhvに変える → while条件へ
            # gen = 1
            # hv = 0.0
            # hv_counter = 0
            # while (hv < 5.35 or hv_counter < 4):
            # 子母集団生成
            offspring = tools.selTournamentDCD(pop, len(pop))
            offspring = [self.toolbox.clone(ind) for ind in offspring]  # type: ignore

            # 交叉と突然変異
            for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
                # 交叉させる個体を選択
                if random.random() <= CXPB:
                    # 交叉
                    self.toolbox.mate(ind1, ind2)  # type: ignore

                # 突然変異
                self.toolbox.mutate(ind1)  # type: ignore
                self.toolbox.mutate(ind2)  # type: ignore

                # 交叉と突然変異させた個体は適応度を削除する
                del ind1.fitness.values, ind2.fitness.values

            # 適応度を削除した個体について適応度の再評価を行う
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            self.write_comment(f"{gen}世代目")
            self.write_indi(invalid_ind)

            # 評価
            self.evaluate(invalid_ind, gen)

            # 過去の世代と新しい世代の中から
            # 次世代を選択
            pop = self.toolbox.select(pop + offspring, MU)  # type: ignore

            # 統計情報を記録
            record = stats.compile(pop)
            logbook.record(gen=gen, evals=len(invalid_ind), **record)

            # hypervolumeを算出
            hv = hypervolume(pop, self.ref_hv)

            # ファイルにログを書き込む
            self.write_log(PNG_PATH + fname, logbook)
            self.write_hv(PNG_PATH + self.hv_fname, gen, hv)

            # 評価値をtxtファイルに保存
            self.save_fitness_coordinates(pop, gen)

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
        self.write_layout_files(gen, pop)

        # csv 出力
        self.history_evaluation_stats.output_csv(self.NGEN, self.NDIM)

        return pop, self.pop_init, logbook

    def write_indi(self, indi):
        fname = f"{PNG_PATH}indi.txt"
        with open(fname, "a") as f:
            for x in indi:
                f.write(str(x))
                f.write("\n")
            f.write("\n\n")

    def write_comment(self, comment):
        fname = f"{PNG_PATH}indi.txt"
        with open(fname, "a") as f:
            f.write(comment)
            f.write("\n")

    def evaluate(self, invalid_ind, gen):
        """
        適応度を評価する。評価結果は、ind.fitness.valuesに書き込む。

        Args:
            invalid_ind (list): 評価する個体
            gen (int): 世代番号
        """
        self.history_evaluation_stats.add_individuals(invalid_ind, gen)
        self.history_evaluation_stats.write_csv()

        # 既存の評価関数を2つのレイアウトで個別に評価
        for id, ind in enumerate(invalid_ind):
            # 現在のレイアウトの評価
            current_fitness = self.toolbox.evaluate(gen, id, ind)  # type: ignore
            # 前のレイアウトがない場合は現在のレイアウトの評価のみ
            sprawl = current_fitness[0]
            clutter = current_fitness[1]
            time_smoothness = current_fitness[2]

            ind.fitness.values = (sprawl, clutter, time_smoothness)
            # ind.fitness.values = (time_smoothness,) # 検証用

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

    def save_fitness_coordinates(self, pop, gen):
        fitnesses_init = np.array(
            [list(self.pop_init[i].fitness.values) for i in range(len(self.pop_init))]
        )
        fitnesses = np.array([list(pop[i].fitness.values) for i in range(len(pop))])

        dir_name = self.__create_directory(PNG_PATH + f"{self.timestamp}/")
        # save fitness coordinates in a txt file
        with open(dir_name + "fitness.txt", "a") as f:
            if gen == 1:
                f.write("\n" + "initial generation\n")
                np.savetxt(f, fitnesses_init, delimiter=",")

            f.write("\n" + str(gen) + "generation\n")
            np.savetxt(f, fitnesses, delimiter=",")

    def save_selected_genes(self, index, timestamp):
        """選択された遺伝子情報をtxtファイルに保存する
        """
        with open(PNG_PATH +"selected_genes_in_nsga2.txt", "a") as f:
            f.write(f"timestamp: {timestamp}\n")
            f.write(f"previous_layout_id:{index}\n")
            f.write(f"current_layout_id:{self.layout_counter}\n")

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
        ind1_layout = ind1[: self.current_layout_gene_len]
        ind2_layout = ind2[: self.current_layout_gene_len]
        ind1_layout, ind2_layout = tools.cxSimulatedBinaryBounded(
            ind1_layout, ind2_layout, eta, low, up
        )

        # 書き換える
        ind1[: self.current_layout_gene_len] = ind1_layout
        ind2[: self.current_layout_gene_len] = ind2_layout

        # 過去のレイアウト部分のみを交叉
        if self.has_previous_layout:
            ind1_previous_layout = ind1[self.current_layout_gene_len :]
            ind2_previous_layout = ind2[self.current_layout_gene_len :]

            # 交叉後の個体を返す [現在のtimestampのレイアウト, previous_timestampのレイアウト] の順
            ind1[self.current_layout_gene_len :] = ind1_previous_layout
            ind2[self.current_layout_gene_len :] = ind2_previous_layout

        return ind1, ind2

    def mutate_only_current_layout(
        self, ind, eta, low, up, indpb, sigma_prev=0.05, prev_mutpb=0.02
    ):
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
        ind_current_layout = ind[: self.current_layout_gene_len]

        # tools.mutPolynomialBounded は tapleを返すので、[0]を取る
        mutated_ind_current = tools.mutPolynomialBounded(
            ind_current_layout, eta, low, up, indpb
        )[0]

        if self.has_previous_layout:
            ind_previous = ind[self.current_layout_gene_len :]
            # 非常に弱い変異（ガウス）を加える（確率は低く）
            for i in range(0, len(ind_previous), 2):
                if random.random() < prev_mutpb:
                    ind_previous[i] += random.gauss(0, sigma_prev)  # x
                    ind_previous[i + 1] += random.gauss(0, sigma_prev)  # y

            ind[:] = mutated_ind_current + ind_previous

        else:
            ind[:] = mutated_ind_current

        # mutate メソッドは tuple を返すので、このメソッドも揃える
        return (ind,)

    def write_layout_files(self, generation, pop):
        """
        その世代の遺伝子情報をまとめて受け取り、それぞれに対してcsvに出力する関数を呼び出す

        Args:
            generation(int): 世代番号
            pop(float[][]): 遺伝子を表現する配列の配列

        Returns:
            なし
        """
        for id, ind in enumerate(pop):
            # 現在のレイアウトを出力
            fname = f"layout{generation}-{id}.csv"
            ind_current = ind[: self.current_layout_gene_len]
            self.write_layout_file_func(ind_current, self.timestamp, fname)

            # 過去のレイアウトがある場合は、過去のレイアウトも出力
            if self.has_previous_layout:
                fname = f"previous_layout{generation}-{id}.csv"
                ind_previous = ind[self.current_layout_gene_len :]
                self.write_layout_file_func(
                    ind_previous, self.previous_timestamp, fname
                )
