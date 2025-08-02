import abc
import csv
import os

from constants import PNG_PATH


class CsvWriter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def write_header(cls) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def write_row(cls, row) -> None:
        raise NotImplementedError()


class StatsCsvWriter(CsvWriter):
    fname = PNG_PATH + "evaluation_stats.csv"

    @classmethod
    def write_header(cls):
        with open(cls.fname, "a") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "NNmax",
                    "NNmin",
                    "NEmax",
                    "NEmin",
                    "EEmax",
                    "EEmin",
                    "time_smoothness_max",
                    "time_smoothness_min",
                    "NNave",
                    "NNstd",
                    "NEave",
                    "NEstd",
                    "EEave",
                    "EEstd",
                    "time_smoothness_ave",
                    "time_smoothness_std",
                ]
            )

    @classmethod
    def write_row(cls, row):
        with open(cls.fname, "a") as f:
            writer = csv.writer(f)
            writer.writerow(row)


class PenaltyCsvWriter(CsvWriter):
    fname = PNG_PATH + "clutter_each_generation.csv"

    @classmethod
    def write_header(cls):
        with open(cls.fname, "a") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "gen",
                    "nnpen",
                    "nepen",
                    "eepen",
                    "normalized_clutter",
                    "sprawl",
                    "time_smoothness",
                ]
            )

    @classmethod
    def write_row(cls, row):
        with open(cls.fname, "a") as f:
            writer = csv.writer(f)
            writer.writerow(row)


class ClutterSprawlCsvWriter(CsvWriter):
    @classmethod
    def set_timestamp(cls, timestamp):
        directory = (
            PNG_PATH + f"{timestamp}/"
        )  # directoryが存在していなかったら作成する
        os.makedirs(directory, exist_ok=True)

        cls.fname = directory + "clutter_sprawl_all_generation.csv"

    @classmethod
    def write_header(cls):
        with open(cls.fname, "a") as f:
            writer = csv.writer(f)
            writer.writerow(["gen", "normalized_clutter", "sprawl", "time_smoothness"])

    @classmethod
    def write_row(cls, row):
        with open(cls.fname, "a") as f:
            writer = csv.writer(f)
            writer.writerow(row)
