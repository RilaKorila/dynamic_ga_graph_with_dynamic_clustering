import subprocess
import time

import constants
import os
from nsga2 import NSGA2
from py4j.java_gateway import JavaGateway

# node数 x 2　が遺伝子の長さ
## ObjectFunction.java の _arr配列の長さも変える
# CHROMOSOME_LENGTH = 75 * 2  # Experiment 1-S

# 現在のディレクトリを取得
current_dir = os.getcwd()

# クラスパスを指定してシェルコマンドを実行
args = [
    "java",
    "-cp",
    constants.JAR_PATH + ":" + constants.CLASS_PATH,
    "ocha.itolab.koala.batch.py4j.ObjectFunction",
]
p = subprocess.Popen(args)


# サーバー起動前に処理が下へ行くのを防ぐ
time.sleep(3)

gateway = JavaGateway(start_callback_server=True)

double_class = gateway.jvm.Double

# gatewayで関数を呼び出す
koala_to_sprawlter = gateway.entry_point


NN_RATIO = 1.0
NE_RATIO = 1.0
EE_RATIO = 0.5


# GAの目的関数を定義
# ここでjavaファイルを呼び出す
def get_evaluation_results(generation, id, individual, timestamp):
    """遺伝子の情報を与え、その遺伝子によって描画されるグラフレイアウトの評価を返す関数

    Args:
        generation(int): 何番目の世代か、を表現する整数
        id(int): その世代の何番目の遺伝子か、を表現する整数
        individual (float[]): 遺伝子を表現する配列
        timestamp(int): dynamic graphのタイムスタンプ

    Returns:
        [sprawl, NN, NE, EE]: 与えられた遺伝子のsprawl, clutterの評価のペア

    Note:
        Javaからは、sprawl, NN, NE, EEを受け取る。
        受け取った NN, NE, EE からclutterを算出する。
    """
    # resは、[sprawl, NN, NE, EE] のfloat配列
    java_individual = __convert_java_double_list(individual)
    res = koala_to_sprawlter.obfunc(generation, id, java_individual, timestamp)

    return res

def write_layout_file(generation, pop, timestamp):
    """
    その世代の遺伝子情報をまとめて受け取り、それぞれに対してcsvに出力する関数を呼び出す

     Args:
        pop(float[][]): 遺伝子を表現する配列を持つ配列

    Returns:
        なし
    """
    for i, ind in enumerate(pop):
        __call_java_file_writer(generation, i, ind, timestamp)


def __call_java_file_writer(generation, id, individual, timestamp):
    """
    与えられた遺伝子情報を初期値としてKoalaのレイアウトを作成し、レイアウト詳細をcsvに出力する

    Args:
        generation(int): 何番目の世代か、を表現する整数
        id(int): その世代の何番目の遺伝子か、を表現する整数
        individual (float[]): 遺伝子を表現する配列
        timestamp: dinamic graphのタイムスタンプ

    Returns:
        なし
    """
    java_individual = __convert_java_double_list(individual)
    koala_to_sprawlter.writeCsv(generation, id, java_individual, timestamp)

def __convert_java_double_list(pylist: list[float]):
    """
    PythonのリストをJavaのリストに変換する関数

    Args:
        pylist(list): Pythonのリスト

    Returns:
        java_list(list): Javaのリスト double[]
    """
    java_double_array = gateway.new_array(gateway.jvm.double, len(pylist))
    for i, val in enumerate(pylist):
        java_double_array[i] = val

    return java_double_array

###### main関数: GAプログラムを呼び出す
# ga = GA(myfunc, CHROMOSOME_LENGTH)
# ga.GA_main_eaMuCommaLambda()

start = time.perf_counter() # 計測開始

# NSGA-IIを呼び出す
ga = NSGA2(get_evaluation_results, write_layout_file)
ga.main()

end = time.perf_counter() #計測終了
print('処理にかかった時間：{:.2f}秒'.format(end-start))

# NSGA-IIIを呼び出す
# ga = NSGA3(myfunc, CHROMOSOME_LENGTH)
# ga.main()

# プロセスをkill
gateway.shutdown()
