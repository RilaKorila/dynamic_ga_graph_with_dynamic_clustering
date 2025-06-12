from collections import defaultdict
import csv
import matplotlib.pyplot as plt
from constants import CIT_HEP_PH_DIR_PATH as DATASET_DIR_PATH
from constants import PNG_PATH

### 動作確認用のスクリプト

def count_nodes_per_id(file_path):
    """
    dynamic_community_n.txt ファイルを読み込み、各 id ごとの node_id の数をカウントする。
    1行目が community_id:、次の行がその community_id に属する node_id がカンマ区切りで記載されている形式に対応。

    :param 
    - file_path: dynamic_community_n.txt のパス

    :return: 
    - id_to_node_count: 各 id ごとの node_id の数を格納した辞書
    """
    id_to_node_count = {}
    current_id = None

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.endswith(':'):
                # Extract community_id from the line
                current_id = line[:-1].strip()
                id_to_node_count[current_id] = 0
            elif line:
                # Count node_ids for the current community_id
                node_ids = line.split(',')
                id_to_node_count[current_id] += len(node_ids)
            else:
                # Handle empty lines
                id_to_node_count[current_id] += 0


    return id_to_node_count

def count_edges(file_path):
    """
    ntwkファイルからedge数をカウントする
    """
    edges = set()
    with open(file_path, "r") as f:
        lines = f.readlines()

        for line in lines:
            start_node_id, end_node_id = line.strip().split("\t")
            edges.add((start_node_id, end_node_id))
    return edges

def get_fitness_data(file_path, gen_name):
    """
    fitness.txt を読み込んで、各評価のmax, min, mean, stdを計算
    """ 
    clutters = []
    sprawls = []
    timesmoothnesses = []
    current_gen = None
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue  # 空行は無視
            
            # タイトル行の判定
            if gen_name in line:
                current_gen = line  # 例: "35generation"
                continue
            
            if current_gen is None:
                continue  # タイトルが来るまではスキップ
            
            # データ行の処理
            try:
                clutter, sprawl, timesmoothness = map(float, line.split(","))
                clutters.append(clutter)
                sprawls.append(sprawl)
                timesmoothnesses.append(timesmoothness)
            except ValueError:
                break
        
    return {"clutter": clutters, "sprawl": sprawls, "timesmoothness": timesmoothnesses}

def __draw_boxplot(before_date, after_data, label, fname):
    """
    箱ひげ図の描画
    """
    print(before_date)
    print(after_data)
    plt.figure(figsize=(5, 5))
    plt.boxplot([before_date, after_data], labels=['Initial Generation', 'Final Generation'])
    plt.ylabel(label)
    plt.title(f'{label} Comparison')
    plt.savefig(fname)

def show_fitness_boxplot(timestamp):
    """
    clutter_each_generation.csvを読み込んで、各指標のboxplotを描画する。
    比較しやすいように、before/afterで横並びにする。
    
    カラム 例:
    gen	nnpen	nepen	eepen	normalized_clutter	sprawl	time_smoothness
    """
    # csvを1行ずつ読み込む
    base_url = "/Users/ayana/Desktop/GraphDrawing論文掲載/facebook 40世代/_plot_result/"
    with open(f"{base_url}{timestamp}/clutter_each_generation.csv", "r") as f:
        reader = csv.reader(f)

        # 1行目はヘッダーなのでスキップ
        next(reader)

        nnpens_before = []
        nepens_before = []
        eepens_before = []
        sprawls_before = []
        timesmoothneesses_before = []

        nnpens_after = []
        nepens_after = []
        eepens_after = []
        sprawls_after = []
        timesmoothneesses_after = []

        before_gen = 0
        after_gen = 39
        for row in reader:
            gen, nnpen, nepen, eepen, normalized_clutter, sprawl, time_smoothness = row

            if before_gen == int(gen):
                nnpens_before.append(float(nnpen))
                nepens_before.append(float(nepen))
                eepens_before.append(float(eepen))
                sprawls_before.append(float(sprawl))
                timesmoothneesses_before.append(float(time_smoothness))
            elif after_gen == int(gen):
                nnpens_after.append(float(nnpen))
                nepens_after.append(float(nepen))
                eepens_after.append(float(eepen))
                sprawls_after.append(float(sprawl))
                timesmoothneesses_after.append(float(time_smoothness))

    base_url = f"./{timestamp}/t{timestamp}_"
    __draw_boxplot(nnpens_before, nnpens_after, "NN Penalty", f"{base_url}nnpen.png")
    __draw_boxplot(nepens_before, nepens_after, "NE Penalty", f"{base_url}nepen.png")
    __draw_boxplot(eepens_before, eepens_after, "EE Penalty", f"{base_url}eepen.png")
    __draw_boxplot(sprawls_before, sprawls_after, "Sprawl Penalty", f"{base_url}sprawl.png")
    __draw_boxplot(timesmoothneesses_before, timesmoothneesses_after, "TimeSmoothness Penalty", f"{base_url}timesmoothness.png")

if __name__ == "__main__": # データ変更
    base_url = "./data/Cit-HepPh/dynamic_communities/"
    # base_url = "./data/facebook/dynamic_communities/" 
    # base_url = "./data/timesmoothnessSample/dynamic_communities/"

    timestamps = [1, 2, 3]

    result = defaultdict(list)
    for timestamp in timestamps:
        nodes_count = 0
        counts = count_nodes_per_id(f"{base_url}dynamic_community_{timestamp}.txt")
        for community_id, count in counts.items():
            result[community_id].append(count)
            nodes_count += count
        # node数をカウント
        print(f"{base_url}dynamic_community_{timestamp}.txt のノード数: {nodes_count}")

    with open("memo.txt", "w") as output_file:
        output_file.write("community_id,ts_1,ts_2,ts_3\n")
        for community_id, count_list in result.items():
            output_file.write(f"{community_id},{','.join(map(str, count_list))}\n")

    # edge数をカウント
    for timestamp in timestamps:
        fname = f"{DATASET_DIR_PATH}ntwk/{timestamp}"
        edges = count_edges(fname)
        print(f"{fname} のエッジ数: {len(edges)}")
        show_fitness_boxplot(timestamp)
