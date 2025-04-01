import subprocess
import time

import constants
from nsga2 import NSGA2
from py4j.java_gateway import JavaGateway
from dynamic_graph import DynamicGraph

# node数 x 2　が遺伝子の長さ
## ObjectFunction.java の _arr配列の長さも変える
# CHROMOSOME_LENGTH = 75 * 2  # Experiment 1-S

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

def optimize_layouts():
    # timestamps = [ i for i in range(1, 4)]
    timestamps = [1, 2, 3]
    results = []
    previous_best_layouts = None
    
    # 各タイムスタンプでの最適化を実行
    for i, timestamp in enumerate(timestamps):
        print(f"Optimizing layout {i+1} of {len(timestamps)}...")

        dynamic_graph = DynamicGraph(timestamps)
        
        ga = NSGA2(
            obfunc=get_evaluation_results,
            write_layout_file_func=write_layout_file,
            dynamic_graph=dynamic_graph,
            timestamp=timestamp,
            previous_best_layouts=previous_best_layouts,  # 前のタイムスタンプの良い解を渡す
            previous_timestamp=timestamps[i-1] if i > 0 else None  # 前のタイムスタンプを渡す
        )
        
        # 最適化実行
        pop, pop_init, logbook = ga.main()
        
        # 結果を保存
        results.append({
            'timestamp': timestamp,
            'population': pop,
            'initial_population': pop_init,
            'logbook': logbook
        })
        
        # 次のレイアウトのベースとして使用する上位n個の解を選択
        previous_best_layouts = select_best_layouts(pop, n=5)  # 上位5個を選択
    
    return results

def select_best_layouts(population, n=5):
    """パレートフロントから上位n個の良い解を選択する
    
    Args:
        population: 最適化後の個体群
        n: 選択する解の数
    
    Returns:
        選択された上位n個の解のリスト
    """
    # パレートフロントの個体をsprawlとclutterの重み付け和でソート
    weighted_scores = []
    for ind in population:
        sprawl, clutter = ind.fitness.values
        # sprawlとclutterの重み付け和を計算（重みは調整可能）
        weighted_score = 0.5 * sprawl + 0.5 * clutter
        weighted_scores.append((ind, weighted_score))
    
    # スコアでソート
    weighted_scores.sort(key=lambda x: x[1])
    
    # 上位n個の解を返す
    return [ind for ind, _ in weighted_scores[:n]]

end = time.perf_counter() #計測終了
print('処理にかかった時間：{:.2f}秒'.format(end-start))

# NSGA-IIIを呼び出す
# ga = NSGA3(myfunc, CHROMOSOME_LENGTH)
# ga.main()

if __name__ == "__main__":

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

    # gatewayで関数を呼び出す
    koala_to_sprawlter = gateway.entry_point

    start = time.perf_counter()
    
    # 最適化実行
    results = optimize_layouts()
    
    end = time.perf_counter()
    print('処理にかかった時間：{:.2f}秒'.format(end-start))
    
    # プロセスをkill
    gateway.shutdown()
