import array
import random

import matplotlib.pyplot as plt
import numpy as np
from constants import PNG_PATH, SUPERGRAPH_PNG_PATH, COMMUNITY_DETECTION_RESULT_PATH
from deap import base, creator, tools
from deap.benchmarks.tools import hypervolume
from history_evaluation_stats import HistoryEvaluationStats
from my_mutation import muSmall
from layouts import define_layout, visualize_sammarized_graph
from dynamic_graph import DynamicGraph
from community_detect import apply_louvain_community_detection, write_community_detection_result

class NSGA2:
    def __init__(self, obfunc, write_layout_file_func):
        ## 問題固有のパラメタ
        # 遺伝子が取り得る値の範囲を指定
        self.MIN_COORDINATE, self.MAX_COORDINATE = -10.0, 10.0
        # 1つの個体内の遺伝子の数を指定 (4の倍数でないとselTournamentDCDでエラー)
        self.NDIM = 20  # Experiment 1-S

        # supergraphを作成する (community detectionも含む)
        dynamic_graph = DynamicGraph()
        
        # Supergraph を構築し、Louvain で Community Detection を適用
        communities = apply_louvain_community_detection(dynamic_graph.supergraph)
        write_community_detection_result(communities, COMMUNITY_DETECTION_RESULT_PATH)

        self.sammarized_graph = dynamic_graph.create_sammarized_graph(communities)

        self.gene_len = len(communities) * 2 
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

        # 遺伝子を生成する関数 "create_layout"を登録
        self.toolbox.register("create_layout", self.create_initial_layout)

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
        self.historyEvaluationStats = HistoryEvaluationStats(self.obfunc, self.gene_len)
        self.toolbox.register("evaluate", self.historyEvaluationStats.evaluate_fitness)

    def create_initial_layout(self):
        pos = define_layout(self.sammarized_graph)

        ## 検証用 ##
        visualize_sammarized_graph(self.sammarized_graph, pos, f"{SUPERGRAPH_PNG_PATH}initial_layout{self.layout_counter}.png")
        self.layout_counter += 1
        ###########

        # x_1, y_1, x_2, y_2, ... , x_n, y_n の順番で返す
        p_list = []
        for (x, y) in pos.values():
            p_list.append(x)
            p_list.append(y)

        if len(p_list) != self.gene_len:
            raise Exception("community数に対して、遺伝子の長さが異なります")
        return p_list
    
    # def create_initial_layout(self):
    #  print(self.gene_len)
    #  return [ 0.5 for i in range(self.gene_len)]
    

    def main(self, fname="output.txt"):
        self.setting()

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
        self.historyEvaluationStats.add_individuals(invalid_ind, 0)
        self.historyEvaluationStats.write_csv()

        # 既存の評価関数
        fitnesses = self.toolbox.map(
            self.toolbox.evaluate,
            invalid_ind,
            [0 for i in range(self.NDIM)],
            [i for i in range(self.NDIM)],
        )
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
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
        self.write_layout_file_func(0, pop, self.gene_len)

        record = stats.compile(pop)
        logbook.record(gen=0, evals=len(invalid_ind), **record)

        with open(PNG_PATH + fname, "a") as f:
            f.write(logbook.stream)

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
            self.historyEvaluationStats.add_individuals(invalid_ind, gen)
            self.historyEvaluationStats.write_csv()

            # 既存の評価関数
            fitnesses = self.toolbox.map(
                self.toolbox.evaluate,
                invalid_ind,
                [gen for i in range(self.NDIM)],
                [i for i in range(self.NDIM)],
            )
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            # 過去の世代と新しい世代の中から
            # 次世代を選択
            pop = self.toolbox.select(pop + offspring, MU)

            # 選ばれた次世代の情報をcsvに出力
            # if gen % 10 == 0:
            #     self.write_layout_file_func(gen, pop, self.gene_len)

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
        self.write_layout_file_func(gen, pop, self.gene_len)

        # 実験：final condition決定用
        self.viz_finally_normalized_scatter_plot()

        return pop, self.pop_init, logbook

    ## 初期サンプルと各世代(gen)の可視化
    def viz(self, pop, gen, fname="fitness.txt"):
        fitnesses_init = np.array(
            [list(self.pop_init[i].fitness.values) for i in range(len(self.pop_init))]
        )
        fitnesses = np.array([list(pop[i].fitness.values) for i in range(len(pop))])

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

        # save fitness coordinates in a txt file
        with open(PNG_PATH + fname, "a") as f:
            if gen == 1:
                f.write("\n" + "initial generation\n")
                np.savetxt(f, fitnesses_init, delimiter=",")

            f.write("\n" + str(gen) + "generation\n")
            np.savetxt(f, fitnesses, delimiter=",")

        plt.legend(loc="upper right")
        plt.title("fitnesses")
        plt.xlabel("sprawl")
        plt.ylabel("clutter")
        plt.grid(True)

        fig.savefig(PNG_PATH + "result" + str(gen) + ".png")

    def viz_finally_normalized_scatter_plot(self):
        # csv 出力
        self.historyEvaluationStats.output_scatter_plot()

        # 散布図描画
        initial_pops = self.historyEvaluationStats.get_initial_pops()
        final_pops = self.historyEvaluationStats.get_final_pops()

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
