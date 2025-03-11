import math

from constants import PNG_PATH
from csv_writer import ClutterSprawlCsvWriter, PenaltyCsvWriter, StatsCsvWriter

NN_RATIO = 1.0
NE_RATIO = 1.0
EE_RATIO = 0.5


class EvaluationStats:
    def __init__(self, receive_from_java_func, gene_length):
        print("世代ごとに評価値をスケール")
        self.csv_fname = PNG_PATH + "evaluation_stats.csv"
        self.individuals = []
        self.receive_from_java_func = receive_from_java_func
        self.gene_length = gene_length
        self.__set_column_to_csv()

    def set_individuals(self, individuals, generation):
        self.individuals = individuals
        self.calc_stats(generation)
        self.print_stats()

    def calc_stats(self, generation):
        sprawls = []
        nnpens = []
        nepens = []
        eepens = []
        for id, individual in enumerate(self.individuals):
            results = self.receive_from_java_func(generation, id, individual, self.gene_length)
            sprawl, nnpen, nepen, eepen = results
            sprawls.append(sprawl)
            nnpens.append(nnpen)
            nepens.append(nepen)
            eepens.append(eepen)

        self.NNmax = max(nnpens)
        self.NNmin = min(nnpens)
        self.NEmax = max(nepens)
        self.NEmin = min(nepens)
        self.EEmax = max(eepens)
        self.EEmin = min(eepens)
        self.NNave = self.__ave(nnpens)
        self.NNstd = self.__std(nnpens)
        self.NEave = self.__ave(nepens)
        self.NEstd = self.__std(nepens)
        self.EEave = self.__ave(eepens)
        self.EEstd = self.__std(eepens)

    def __ave(self, arr):
        return sum(arr) / len(arr)

    def __std(self, arr):
        mean = sum(arr) / len(arr)
        squared_deviations = sum((x - mean) ** 2 for x in arr)
        return math.sqrt(squared_deviations / len(arr))

    def evaluate_fitness(self, individual, generation, id):
        """GAの目的関数。1つの遺伝子を受け取り、その評価値を返す。返り値はiteratorでないといけないので、pairで返す

        Args:
            individual (float[]): 遺伝子を表現する配列

        Returns:
            Pair(float, float): 与えられた遺伝子のsprawl, clutterの評価のペア

        Note:
            clutterの算出方法は3種類
            正規化, 標準化, 定数でわる, の3種類の処理をかけたpenaltyをそれぞれ係数でたしあわせて算出する
        """
        results = self.receive_from_java_func(generation, id, individual, self.gene_length)
        sprawl = results[0]
        clutter = self.__calc_standardized_clutter(results)

        # 実験用
        row = [generation, results[1], results[2], results[3], clutter, sprawl]
        PenaltyCsvWriter.write_row(row)

        return (sprawl, clutter)

    def __calc_normalized_clutter(self, results):
        _, nnpen, nepen, eepen = results

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
        _, nnpen, nepen, eepen = results

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
        _, nnpen, nepen, eepen = results
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
            self.NNave,
            self.NNstd,
            self.NEave,
            self.NEstd,
            self.EEave,
            self.EEstd,
        ]
        StatsCsvWriter.write_row(row)
