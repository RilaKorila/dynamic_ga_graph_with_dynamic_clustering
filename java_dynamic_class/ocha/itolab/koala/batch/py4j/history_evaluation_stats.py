import math

from constants import PNG_PATH
from csv_writer import ClutterSprawlCsvWriter, PenaltyCsvWriter, StatsCsvWriter

NN_RATIO = 1.0
NE_RATIO = 1.0
EE_RATIO = 0.5


class HistoryEvaluationStats:
    def __init__(
        self,
        receive_from_java_func,
        previous_timestamp,
        timestamp,
        dynamic_graph,
        has_previous_layout,
        current_layout_gene_len,
    ):
        print("過去の全ての世代を基準に評価値をスケール")
        ClutterSprawlCsvWriter.set_timestamp(timestamp)  # タイムスタンプを設定
        self.csv_fname = PNG_PATH + f"{timestamp}/" + "evaluation_stats.csv"
        self.sprawls = []
        self.nnpens = []
        self.nepens = []
        self.eepens = []
        self.time_smoothnesses = []
        self.receive_from_java_func = receive_from_java_func
        self.timestamp = timestamp
        self.previous_timestamp = previous_timestamp
        self.dynamic_graph = dynamic_graph
        self.has_previous_layout = has_previous_layout
        self.current_layout_gene_len = current_layout_gene_len
        self.__set_column_to_csv()

    def add_individuals(self, individuals, generation):
        self.__calc_penalties(generation, individuals)
        self.__calc_stats()
        self.print_stats()

    def __calc_penalties(self, generation, individuals):
        """
        NN, NE, EEの, time_smoothnessの算出をし、それぞれのリストに計算結果を保存する。ここでは正規化はされない。
        """
        dynamic_community = (
            self.dynamic_graph.time_ordered_dynamic_communities_dict.get(self.timestamp)
        )

        # 1つ目のtimestampの場合は、previous_dynamic_community は None
        if self.has_previous_layout:
            previous_dynamic_community = (
                self.dynamic_graph.time_ordered_dynamic_communities_dict.get(
                    self.previous_timestamp
                )
            )
        else:
            previous_dynamic_community = None

        for id, individual in enumerate(individuals):
            current_layout_plist = individual[: self.current_layout_gene_len]
            if self.has_previous_layout:
                previous_layout_plist = individual[self.current_layout_gene_len :]
            else:
                previous_layout_plist = None
            results = self.receive_from_java_func(
                generation,
                id,
                previous_layout_plist,
                current_layout_plist,
                self.timestamp,
                previous_dynamic_community,
                dynamic_community,
            )
            sprawl, nnpen, nepen, eepen, time_smoothness = results
            self.nnpens.append(nnpen)
            self.nepens.append(nepen)
            self.eepens.append(eepen)
            self.sprawls.append(sprawl)
            self.time_smoothnesses.append(time_smoothness)

    def __calc_stats(self):
        """
        各ペナルティの最大値、最小値、その他統計情報を更新する。
        """
        self.NNmax = max(self.nnpens)
        self.NNmin = min(self.nnpens)
        self.NEmax = max(self.nepens)
        self.NEmin = min(self.nepens)
        self.EEmax = max(self.eepens)
        self.EEmin = min(self.eepens)
        self.time_smoothness_max = max(self.time_smoothnesses)
        self.time_smoothness_min = min(self.time_smoothnesses)
        self.NNave = self.__ave(self.nnpens)
        self.NNstd = self.__std(self.nnpens)
        self.NEave = self.__ave(self.nepens)
        self.NEstd = self.__std(self.nepens)
        self.EEave = self.__ave(self.eepens)
        self.EEstd = self.__std(self.eepens)
        self.time_smoothness_ave = self.__ave(self.time_smoothnesses)
        self.time_smoothness_std = self.__std(self.time_smoothnesses)

    def __ave(self, arr):
        return sum(arr) / len(arr)

    def __std(self, arr):
        mean = sum(arr) / len(arr)
        squared_deviations = sum((x - mean) ** 2 for x in arr)
        return math.sqrt(squared_deviations / len(arr))

    def evaluate_fitness(self, generation, id, individual):
        """GAの目的関数。1つの遺伝子を受け取り、その評価値を返す。返り値はiteratorでないといけないので、pairで返す

        Args:
            generation (int): 世代番号
            id (int): 個体番号
            individual (float[]): 遺伝子を表現する配列([current_layout, previous_layout]の順で並んでいる)

        Returns:
            Pair(float, float, float): 与えられた遺伝子のsprawl, clutter, timesmoothnessの評価のペア

        Note:
            clutterの算出方法は3種類
            正規化, 標準化, 定数でわる, の3種類の処理をかけたpenaltyをそれぞれ係数でたしあわせて算出する
        """
        previous_dynamic_community = (
            self.dynamic_graph.time_ordered_dynamic_communities_dict.get(
                self.previous_timestamp
            )
        )
        dynamic_community = (
            self.dynamic_graph.time_ordered_dynamic_communities_dict.get(self.timestamp)
        )

        current_layout_plist = individual[: self.current_layout_gene_len]
        if self.has_previous_layout:
            previous_layout_plist = individual[self.current_layout_gene_len :]
        else:
            previous_layout_plist = None

        results = self.receive_from_java_func(
            generation,
            id,
            previous_layout_plist,
            current_layout_plist,
            self.timestamp,
            previous_dynamic_community,
            dynamic_community,
        )
        sprawl = results[0]
        clutter = self.__calc_normalized_clutter(results[1], results[2], results[3])
        time_smoothness = results[4]

        # 実験用
        row = [
            generation,
            results[1],
            results[2],
            results[3],
            clutter,
            sprawl,
            time_smoothness,
        ]
        PenaltyCsvWriter.write_row(row)

        return (sprawl, clutter, time_smoothness)

    def __calc_normalized_clutter(self, nnpen, nepen, eepen):
        """
        Javaから受け取ったNN, NE, EEの各ペナルティ値を正規化した上で、Clutter値を算出する。
        正規化には、これまで登場した全てのindividualの集団の中での最大値・最小値を使う。
        """

        normalized_nnpen = (
            (nnpen - self.NNmin) / (self.NNmax - self.NNmin)
            if self.NNmax - self.NNmin != 0.0
            else 0.0
        )
        normalized_nepen = (
            (nepen - self.NEmin) / (self.NEmax - self.NEmin)
            if self.NEmax - self.NEmin != 0.0
            else 0.0
        )
        normalized_eepen = (
            (eepen - self.EEmin) / (self.EEmax - self.EEmin)
            if self.EEmax - self.EEmin != 0.0
            else 0.0
        )

        clutter = (
            NN_RATIO * normalized_nnpen
            + NE_RATIO * normalized_nepen
            + EE_RATIO * normalized_eepen
        )
        return clutter

    def __calc_standardized_clutter(self, results):
        _, nnpen, nepen, eepen, _ = results

        standardized_nnpen = (
            (nnpen - self.NNave) / self.NNstd if self.NNstd != 0.0 else 0.0
        )
        standardized_nepen = (
            (nepen - self.NEave) / self.NEstd if self.NEstd != 0.0 else 0.0
        )
        standardized_eepen = (
            (eepen - self.EEave) / self.EEstd if self.EEstd != 0.0 else 0.0
        )

        clutter = (
            NN_RATIO * standardized_nnpen
            + NE_RATIO * standardized_nepen
            + EE_RATIO * standardized_eepen
        )
        return clutter

    def __calc_scaled_clutter(self, results):
        _, nnpen, nepen, eepen, _ = results
        NN_MAX = 0.3
        NE_MAX = 2400.0
        EE_MAX = 60000.0

        scaled_nnpen = nnpen / NN_MAX
        scaled_nepen = nepen / NE_MAX
        scaled_eepen = eepen / EE_MAX

        clutter = (
            NN_RATIO * scaled_nnpen + NE_RATIO * scaled_nepen + EE_RATIO * scaled_eepen
        )
        return clutter

    def print_stats(self):
        """
        EvaluationStatsの中身を標準出力
        """
        print("-- EvaluatoionStats --")
        print("NNmax", self.NNmax, "NNmax", self.NNmin)
        print("NEmax", self.NEmax, "NEmin", self.NEmin)
        print("EEmax", self.EEmax, "EEmin", self.EEmin)
        print(
            "time_smoothness_max",
            self.time_smoothness_max,
            "time_smoothness_min",
            self.time_smoothness_min,
        )

    def __set_column_to_csv(self):
        StatsCsvWriter.write_header()
        PenaltyCsvWriter.write_header()
        ClutterSprawlCsvWriter.write_header()

    def write_csv(self):
        row = [
            self.NNmax,
            self.NNmin,
            self.NEmax,
            self.NEmin,
            self.EEmax,
            self.EEmin,
            self.time_smoothness_max,
            self.time_smoothness_min,
            self.NNave,
            self.NNstd,
            self.NEave,
            self.NEstd,
            self.EEave,
            self.EEstd,
            self.time_smoothness_ave,
            self.time_smoothness_std,
        ]
        StatsCsvWriter.write_row(row)

    def output_csv(self, ngen, population_length):
        """
        過去のNN, NE, EEの全てをcsvに出力する。
        ただし、最終世代の最大値・最小値で正規化することとする

        inputs:
            ngen (int): 繰り返し世代数
            population_length (int): 1世代あたりの個体数
        """

        for gen in range(ngen):
            for i in range(population_length):
                nnpen = self.nnpens[gen * population_length + i]
                nepen = self.nepens[gen * population_length + i]
                eepen = self.eepens[gen * population_length + i]
                sprawl = self.sprawls[gen * population_length + i]
                time_smoothness = self.time_smoothnesses[gen * population_length + i]
                clutter = self.__calc_normalized_clutter(nnpen, nepen, eepen)

                ClutterSprawlCsvWriter.write_row(
                    [gen, clutter, sprawl, time_smoothness]
                )
