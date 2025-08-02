from constants import NBAF_COAUTHORS_CSV_PATH

### NBAF_Coauthorship_12dim.csvのデータを加工するメソッド
# 他のデータではつかい回さない (dynamic_graph.pyでIFを揃えてデータをハンドリングするため)

fname = NBAF_COAUTHORS_CSV_PATH


def get_graph_sequence_from_original_csvfile():
    """
    fname のcsvファイルを読み込み、graph_sequence を返す

    フォーマット:
    #connectivity
    node_id,author_name
    outgoing_nodes
    incoming_nodes
    """

    nodes = set()
    edges = set()

    with open(fname, "r", encoding="latin-1") as f:
        lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith("#connectivity"):
                i += 1
                while i < len(lines):
                    # vectorが含まれていたら処理中断
                    if "vector" in lines[i].lower():
                        break
                    # ノード情報の行
                    node_info = lines[i].strip().split(",")
                    if (
                        len(node_info) < 2 or node_info[0] == ""
                    ):  # 空行やフォーマット外の行をスキップ
                        i += 1
                        continue

                    current_node = node_info[0]
                    nodes.add(current_node)

                    # 外向きエッジの処理
                    i += 1
                    if i < len(lines):
                        outgoing = lines[i].strip().split(",")
                        for target in outgoing:
                            if target and target != "":
                                edges.add(tuple(sorted([current_node, target])))
                                nodes.add(target)

                    # 内向きエッジの処理
                    i += 1
                    if i < len(lines):
                        incoming = lines[i].strip().split(",")
                        for source in incoming:
                            if source and source != "":
                                edges.add(tuple(sorted([source, current_node])))
                                nodes.add(source)

                    i += 1
            else:
                i += 1

    return [(list(nodes), list(edges))]
