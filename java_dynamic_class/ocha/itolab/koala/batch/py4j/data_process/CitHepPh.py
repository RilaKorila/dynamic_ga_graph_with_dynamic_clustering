from constants import CIT_HEP_PH_DIR_PATH
from collections import defaultdict
import os
### Cit-HepPhのデータを加工するメソッド
# 他のデータではつかい回さない (dynamic_graph.pyでIFを揃えてデータをハンドリングするため)
def get_graph_sequence_from_original_file():
    """
    ntwk/配下のファイルを読み込み、graph_sequence を返す
    
    ntwk/配下のファイルのフォーマットは、
    start_node_id   end_node_id

    Returns:
    - graph_sequence (dict): timestampをキーとして、ノードとエッジのリストを値とする辞書
    """

    timestamp_count = __get_timestamp_count()
    graph_sequence = {}
    
    for timestamp in range(1, timestamp_count + 1):
        fname = f"{CIT_HEP_PH_DIR_PATH}ntwk/{timestamp}"

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
        graph_sequence[timestamp] = (list(nodes), list(edges))
    
    return graph_sequence

def setup_data():
    """
    Cit-HepPhのデータを加工し、必要なファイル群を作成する。
    """
    print("=========== setup_data ===========")

    timestamp_count = __get_timestamp_count()
    
    for timestamp in range(1, timestamp_count + 1):
        edges = __get_edges(timestamp)
        nodes = __get_nodes(timestamp)

        # _coms_{n}_nodes.csv では、そのtimestampでは生きていないノードIDも含んでしまっているため、
        # ntwk/配下のデータを参照して、そのtimestampで生きているノードだけを抽出し、結果をcsvファイルとして出力
        __write_filtered_coms(timestamp, nodes)

        # Sprawlが読み込めるようにフォーマットに変換
        __write_connectivity(nodes, edges, timestamp)

def __get_timestamp_count():
    """
    Cit-HepPhのデータのtimestampの数を返す
    """
    # coms/配下のファイルの数を数える
    dir_name = f"{CIT_HEP_PH_DIR_PATH}coms/"
    timestamp_count = len(os.listdir(dir_name))

    return timestamp_count

def __get_edges(timestamp):
    fname = f"{CIT_HEP_PH_DIR_PATH}ntwk/{timestamp}"

    edges = set()
    with open(fname, "r") as f:
        lines = f.readlines()

        for line in lines:
            start_node_id, end_node_id = line.strip().split("\t")
            edges.add((start_node_id, end_node_id))
    return edges

def __get_nodes(timestamp):
    fname = f"{CIT_HEP_PH_DIR_PATH}ntwk/{timestamp}"

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
    com_fname = f"{CIT_HEP_PH_DIR_PATH}coms/runDynamicModularity_Cit-HepPh_com_{timestamp}_nodes.csv"
    filtered_com_fname = f"{CIT_HEP_PH_DIR_PATH}filtered_coms/runDynamicModularity_Cit-HepPh_com_{timestamp}_nodes.csv"

    # communityを取得
    com_nodes = {}
    with open(com_fname, "r") as f:
        lines = f.readlines()
        for community_id, line in enumerate(lines):
            com_nodes[community_id] = line.strip().split(",")

    # 生きているnodeのみ残す
    for community_id, nodes in com_nodes.items():
        filtered_nodes = list(filter(lambda node_id: node_id in alive_nodes, nodes))
        __write_csv(filtered_com_fname, filtered_nodes)

def __write_csv(fname, nodes):
    # filtered_coms/配下にcsvファイルを作成
    with open(fname, "a") as f:
        f.write(",".join(nodes))

def __write_connectivity(nodes, edges, timestamp):
    """
    エッジの情報を Sprawlが読み込むフォーマットに変換し, csvファイルとして書き出す

    フォーマット:
    #connectivity
    node_id,author_name
    outgoing_nodes
    incoming_nodes
    """
    fname = f"{CIT_HEP_PH_DIR_PATH}connectivity_timestamp_{timestamp}.csv"
    # 各ノードの外向き・内向きエッジを管理する辞書を作成
    outgoing_edges = defaultdict(list)
    incoming_edges = defaultdict(list)

    # エッジ情報を辞書に格納
    for (start_node_id, end_node_id) in edges:        
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
