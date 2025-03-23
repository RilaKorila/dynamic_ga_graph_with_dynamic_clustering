from constants import CIT_HepPh_DIR_PATH
from collections import defaultdict

### Cit-HepPhのデータを加工するメソッド
# 他のデータではつかい回さない (dynamic_graph.pyでIFを揃えてデータをハンドリングするため)
def get_graph_sequence_from_original_file(time_count: int):
    """
    ntwk/配下のファイルを読み込み、graph_sequence を返す
    
    フォーマット:
    start_node_id   end_node_id
    """

    for timestamp in range(1, time_count + 1):
        fname = f"{CIT_HepPh_DIR_PATH}ntwk/{timestamp}"

        nodes = set()
        edges = set()
        graph_sequence = []
        
        with open(fname, "r") as f:
            lines = f.readlines()

            for line in lines:
                start_node_id, end_node_id = line.strip().split("\t")
                nodes.add(start_node_id)
                nodes.add(end_node_id)
                edges.add((start_node_id, end_node_id))
        
        # グラフを追加
        graph_sequence.append((list(nodes), list(edges)))
    
    return graph_sequence

def setup_data():
    """
    Cit-HepPhのデータを加工し、必要なファイル群を作成する。
    """
    print("=========== setup_data ===========")
    timestamp = 1 # TODO 複数のtimestampでも対応できるようにする

    edges = __get_edges(timestamp)
    nodes = __get_nodes(timestamp)

    # _coms_{n}_nodes.csv において、そのtimestampで生きているノードだけを抽出
    __filter_coms(timestamp, nodes)

    # Sprawlが読み込めるようにフォーマットに変換
    __write_connectivity(nodes, edges)

def __get_edges(timestamp):
    fname = f"{CIT_HepPh_DIR_PATH}ntwk/{timestamp}"

    edges = set()
    with open(fname, "r") as f:
        lines = f.readlines()

        for line in lines:
            start_node_id, end_node_id = line.strip().split("\t")
            edges.add((start_node_id, end_node_id))
    return edges

def __get_nodes(timestamp):
    fname = f"{CIT_HepPh_DIR_PATH}ntwk/{timestamp}"

    nodes = set()
    with open(fname, "r") as f:
        lines = f.readlines()

        for line in lines:
            start_node_id, end_node_id = line.strip().split("\t")
            nodes.add(start_node_id)
            nodes.add(end_node_id)
    return nodes


def __filter_coms(timestamp, alive_nodes):
    # coms/配下のファイルから、存在するndoesだけを抽出
    com_fname = f"{CIT_HepPh_DIR_PATH}coms/runDynamicModularity_Cit-HepPh_com_{timestamp}_nodes.csv"
    filtered_com_fname = f"{CIT_HepPh_DIR_PATH}filtered_coms/runDynamicModularity_Cit-HepPh_com_{timestamp}_nodes.csv"

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

def __write_connectivity(nodes, edges):
    """
    エッジの情報を Sprawlが読み込むフォーマットに変換し, csvファイルとして書き出す

    フォーマット:
    #connectivity
    node_id,author_name
    outgoing_nodes
    incoming_nodes
    """
    fname = f"{CIT_HepPh_DIR_PATH}Cit-HepPh_connectivity.csv"
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
            print(f"outgoing: {len(outgoing)}")
            f.write(",".join(outgoing) + "\n")
            # 内向きエッジ  
            incoming = incoming_edges.get(node_id, [])
            print(f"incoming: {len(incoming)}")
            f.write(",".join(incoming) + "\n")
