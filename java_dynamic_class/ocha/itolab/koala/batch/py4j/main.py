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
def get_evaluation_results(generation, id, individual, gene_length):
    """遺伝子の情報を与え、その遺伝子によって描画されるグラフレイアウトの評価を返す関数

    Args:
        generation(int): 何番目の世代か、を表現する整数
        id(int): その世代の何番目の遺伝子か、を表現する整数
        individual (float[]): 遺伝子を表現する配列
        gene_length(int): 遺伝子の長さ

    Returns:
        [sprawl, NN, NE, EE]: 与えられた遺伝子のsprawl, clutterの評価のペア

    Note:
        Javaからは、sprawl, NN, NE, EEを受け取る。
        受け取った NN, NE, EE からclutterを算出する。
    """

    double_array = gateway.new_array(double_class, gene_length)

    for n, indi in enumerate(individual):
        double_array[n] = float(indi)

    for n, elem in enumerate(double_array):
        res = koala_to_sprawlter.obfunc(generation, id, elem, n, gene_length)
        # resは、[sprawl, NN, NE, EE] のfloat配列

    return res


def write_layout_file(generation, pop, gene_length):
    """
    その世代の遺伝子情報をまとめて受け取り、それぞれに対してcsvに出力する関数を呼び出す

     Args:
        pop(float[][]): 遺伝子を表現する配列を持つ配列

    Returns:
        なし
    """
    for i, ind in enumerate(pop):
        __call_java_file_writer(generation, i, ind, gene_length)


def __call_java_file_writer(generation, id, individual, gene_length):
    """
    与えられた遺伝子情報を初期値としてKoalaのレイアウトを作成し、レイアウト詳細をcsvに出力する

     Args:
        generation(int): 何番目の世代か、を表現する整数
        id(int): その世代の何番目の遺伝子か、を表現する整数
        individual (float[]): 遺伝子を表現する配列

    Returns:
        なし
    """
    double_array = gateway.new_array(double_class, gene_length)

    for n, indi in enumerate(individual):
        double_array[n] = float(indi)

    for n, elem in enumerate(double_array):
        koala_to_sprawlter.writeCsv(generation, id, elem, n, gene_length)


###### main関数: GAプログラムを呼び出す
# ga = GA(myfunc, CHROMOSOME_LENGTH)
# ga.GA_main_eaMuCommaLambda()

start = time.perf_counter() # 計測開始

# NSGA-IIを呼び出す
ga = NSGA2(get_evaluation_results, write_layout_file)

koala_to_sprawlter.set_gene_length(ga.gene_len) 
ga.main()

end = time.perf_counter() #計測終了
print('処理にかかった時間：{:.2f}秒'.format(end-start))

# NSGA-IIIを呼び出す
# ga = NSGA3(myfunc, CHROMOSOME_LENGTH)
# ga.main()

# プロセスをkill
gateway.shutdown()
