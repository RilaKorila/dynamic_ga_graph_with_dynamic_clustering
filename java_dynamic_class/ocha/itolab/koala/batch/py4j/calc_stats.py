import subprocess
import time

import constants
from nsga2 import NSGA2
from py4j.java_gateway import JavaGateway

# node数 x 2　が遺伝子の長さ
## ObjectFunction.java の _arr配列の長さも変える
CHROMOSOME_LENGTH = 2000 * 2

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


# GAの目的関数を定義
# ここでjavaファイルを呼び出す
def myfunc(individual):
    double_array = gateway.new_array(double_class, CHROMOSOME_LENGTH)

    for n, indi in enumerate(individual):
        double_array[n] = float(indi)

    for n, elem in enumerate(double_array):
        res = koala_to_sprawlter.obfunc(elem, n, CHROMOSOME_LENGTH)

    return (res[0], res[1])


# NSGA-IIを呼び出す
ga = NSGA2(myfunc, CHROMOSOME_LENGTH)
ga.first_generation()

# プロセスをkill
gateway.shutdown()
