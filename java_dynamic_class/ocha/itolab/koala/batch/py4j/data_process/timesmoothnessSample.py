from constants import TIMESMOOTHNESS_SAMPLE_DIR_PATH as DATASET_DIR_PATH
from constants import GRAPH_JSON_DIR
from collections import defaultdict
import os, json


### timesmoothnessSampleのデータを加工するメソッド
# 他のデータではつかい回さない (dynamic_graph.pyでIFを揃えてデータをハンドリングするため)

DATASET_NAME = "timesmoothnessSample"


def get_graph_sequence_from_original_file(timestamps):
    """
    ntwk/配下のファイルを読み込み、graph_sequence を返す

    ntwk/配下のファイルのフォーマットは、
    start_node_id   end_node_id

    Args:
        timestamps (list): 使用するtimestampのリスト
    Returns:
    - graph_sequence_dict (dict): timestampをキーとして、ノードとエッジのリストを値とする辞書
    """

    graph_sequence_dict = {}

    for timestamp in timestamps:
        fname = f"{DATASET_DIR_PATH}ntwk/{timestamp}"

        nodes = set()
        edges = set()

        with open(fname, "r") as f:
            lines = f.readlines()

            for line in lines:
                start_node_id, end_node_id = line.strip().split("\t")
                nodes.add(start_node_id)
                nodes.add(end_node_id)
                edges.add((start_node_id, end_node_id))

        # グラフを追加
        graph_sequence_dict[timestamp] = (list(nodes), list(edges))

    return graph_sequence_dict


def setup_data(timestamps):
    """
    データを加工し、必要なファイル群を作成する。
    """
    print("=========== TimesmoothnessSample: setup_data ===========")

    for timestamp in timestamps:
        edges = __get_edges(timestamp)
        nodes = __get_nodes(timestamp)

        # _coms_{n}_nodes.csv では、そのtimestampでは生きていないノードIDも含んでしまっているため、
        # ntwk/配下のデータを参照して、そのtimestampで生きているノードだけを抽出し、結果をcsvファイルとして出力
        __write_filtered_coms(timestamp, nodes)

        # Sprawlが読み込めるようにフォーマットに変換
        __write_connectivity(nodes, edges, timestamp)


def __get_edges(timestamp):
    fname = f"{DATASET_DIR_PATH}ntwk/{timestamp}"

    edges = set()
    with open(fname, "r") as f:
        lines = f.readlines()

        for line in lines:
            start_node_id, end_node_id = line.strip().split("\t")
            edges.add((start_node_id, end_node_id))
    return edges


def __get_nodes(timestamp):
    fname = f"{DATASET_DIR_PATH}ntwk/{timestamp}"

    nodes = set()
    with open(fname, "r") as f:
        lines = f.readlines()

        for line in lines:
            start_node_id, end_node_id = line.strip().split("\t")
            nodes.add(start_node_id)
            nodes.add(end_node_id)
    return nodes


def __write_filtered_coms(timestamp, alive_nodes):
    """
    _coms_{n}_nodes.csv では、そのtimestampでは生きていないノードIDも含んでしまっているため、
    ntwk/配下のデータを参照して、そのtimestampで生きているノードだけを抽出し、結果をcsvファイルとして出力。
    """
    com_fname = f"{DATASET_DIR_PATH}coms/runDynamicModularity_timesmoothnessSample_com_{timestamp}_nodes.csv"
    filtered_com_fname = f"{DATASET_DIR_PATH}filtered_coms/runDynamicModularity_timesmoothnessSample_com_{timestamp}_nodes.csv"

    # communityを取得
    com_nodes = {}
    with open(com_fname, "r") as f:
        lines = f.readlines()
        for community_id, line in enumerate(lines):
            com_nodes[community_id] = line.strip().split(",")

    # 生きているnodeのみ残す
    graph_info = {}
    filtered_data = []

    for community_id, nodes in com_nodes.items():
        filtered_nodes = list(filter(lambda node_id: node_id in alive_nodes, nodes))
        graph_info[community_id] = filtered_nodes
        filtered_data.append(filtered_nodes)  # 配列に追加

    # 一括でファイルに書き出し
    __write_csv_batch(filtered_com_fname, filtered_data)

    # jsonにも書き出す
    dump_graph_info(graph_info, timestamp)


def dump_graph_info(graph_info, timestamp):
    """
    graphの情報(cluster_idとそこに属するnodes)をjsonファイルに保存する
    """
    # Convert sets to lists for JSON serialization
    serializable_graph_info = {
        cluster_id: list(nodes) for cluster_id, nodes in graph_info.items()
    }

    graph_json_path = os.path.join(GRAPH_JSON_DIR, f"graph_info_{timestamp}.json")
    with open(graph_json_path, "w") as f:
        json.dump(serializable_graph_info, f)


def load_graph_info(timestamp):
    """
    graphの情報(cluster_idとそこに属するnodes)をjsonファイルから読み込む
    """
    graph_json_path = os.path.join(GRAPH_JSON_DIR, f"graph_info_{timestamp}.json")
    with open(graph_json_path, "r") as f:
        graph_info = json.load(f)
        # Convert lists back to sets
        return {
            cluster_id: set(map(int, nodes)) for cluster_id, nodes in graph_info.items()
        }


def __write_csv_batch(fname, data_list):
    """
    配列に貯めたデータを一括でファイルに書き出す
    既存ファイルがある場合は上書きする
    """
    with open(fname, "w") as f:  # "w"で上書きモード
        for nodes in data_list:
            f.write(",".join(nodes) + "\n")


def __write_connectivity(nodes, edges, timestamp):
    """
    エッジの情報を Sprawlが読み込むフォーマットに変換し, csvファイルとして書き出す

    フォーマット:
    #connectivity
    node_id,author_name
    outgoing_nodes
    incoming_nodes
    """
    fname = f"{DATASET_DIR_PATH}connectivity_timestamp_{timestamp}.csv"
    # 各ノードの外向き・内向きエッジを管理する辞書を作成
    outgoing_edges = defaultdict(list)
    incoming_edges = defaultdict(list)

    # エッジ情報を辞書に格納
    for start_node_id, end_node_id in edges:
        outgoing_edges[start_node_id].append(end_node_id)
        incoming_edges[end_node_id].append(start_node_id)

    # ファイルに書き出し
    with open(fname, "w") as f:
        f.write("#connectivity\n")

        for node_id in nodes:
            # ノード情報
            f.write(f"{node_id},node_label_{node_id}\n")
            # 外向きエッジ
            outgoing = outgoing_edges.get(node_id, [])
            f.write(",".join(outgoing) + "\n")
            # 内向きエッジ
            incoming = incoming_edges.get(node_id, [])
            f.write(",".join(incoming) + "\n")
