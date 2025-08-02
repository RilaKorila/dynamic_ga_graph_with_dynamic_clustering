import networkx as nx
from matplotlib import pyplot as plt
import numpy as np


############ GAから呼び出される関数 ############
def define_layout(summarized_graph):
    pos = spring_layout(summarized_graph)  # 初期のレイアウト
    positive_pos = __parallel_move_layout(pos)
    return positive_pos


###########################################


## 検証用 summarized_graphの描画
def visualize_summarized_graph(summarized_graph, pos, file_name):
    """
    Visualizes the supergraph with Louvain community detection results.
    (ただし、同一metanode内のedgeは描画しない)

    Parameters:
    - summarized_graph:
        Weighted NetworkX graph (ノードサイズは metanodesのサイズに比例, エッジの太さもmetaedgeのサイズに比例)
    - pos:
        summarized_graphにlayout関数を適用した結果(実施するたびに結果が変わってしまうので、引数として渡す)
    - file_name: str
        保存先のファイルパス（.png など）
    """

    G = summarized_graph.copy()

    edges_to_remove = [
        (u, v) for u, v in G.edges() if u == v
    ]  # 同一metanode内のedgeは除く
    G.remove_edges_from(edges_to_remove)

    # ノードサイズを取得し、スケール
    node_sizes = [summarized_graph.nodes[node]["size"] for node in G.nodes()]
    scaled_node_sizes = __scale_size(node_sizes, 200, 800)

    # エッジの太さを取得し、スケール
    edge_weights = [summarized_graph[u][v]["weight"] for u, v in G.edges()]
    scaled_edge_weights = __scale_size(edge_weights, 5, 20)

    # グラフの描画
    fig = plt.figure(figsize=(8, 6))
    nx.draw(
        G,
        pos,
        with_labels=False,
        edge_color="gray",
        node_size=scaled_node_sizes,
        width=scaled_edge_weights,
        node_color="lightblue",  # 青色
        alpha=0.6,  # 透明度
        edgecolors="black",  # ノードの枠線の色
        linewidths=1,  # 枠線の太さ
    )

    fig.savefig(file_name)
    plt.close(fig)


def __scale_size(raw_weights, min_val, max_val):
    # 対数スケーリングを適用（1を加えることで重み1のエッジも表示されるようにする）
    log_weights = [np.log1p(w) for w in raw_weights]

    # スケーリングして適切な範囲10-50に収める
    if log_weights:  # リストが空でない場合
        min_w, max_w = min(log_weights), max(log_weights)
        edge_weights = [
            min_val + max_val * (w - min_w) / (max_w - min_w) if max_w != min_w else 10
            for w in log_weights
        ]
    else:
        edge_weights = []
    return edge_weights


## サブメソッド
def __parallel_move_layout(pos):
    # マイナスの座標がなくなるように並行移動
    x_list = [pos[node][0] for node in pos]
    y_list = [pos[node][1] for node in pos]
    min_x = min(x_list)
    min_y = min(y_list)

    moved_pos = {}
    if min_x < 0 or min_y < 0:
        for node_id in pos.keys():
            # min_x, min_yの分だけ並行移動(最小の座標は0になる)
            moved_pos[node_id] = (
                pos[node_id][0] + abs(min_x),
                pos[node_id][1] + abs(min_y),
            )

    return moved_pos


def get_summarized_graph(G_super, communities):
    """
    Creates a summarized graph from the supergraph and communities.

    Parameters:
    - G_super: Weighted NetworkX graph (Supergraph)
    - communities: Dictionary mapping nodes to community labels

    Returns:
    - summarized_graph: Weighted NetworkX graph (Summarized graph)
    """
    community_id_dict = {}  # nodeがどのcommunityに属しているかを管理
    for i, community in enumerate(communities):
        for node in community:
            community_id_dict[node] = i

    summarized_graph = nx.Graph()

    # metanodeの作成
    for community_id, community in enumerate(communities):
        # community_idを nodeのidとする
        # len(community)を nodeのsizeとする
        summarized_graph.add_node(community_id, size=len(community))

    # metaedgeの作成: metanodeを構成するnodeが元々持っていたedgeを束ねたものをmetaedgeとする
    for community_id, community in enumerate(communities):
        # communityに属するnode全て走査
        for node in community:
            for source, target in G_super.edges(
                node
            ):  # nodeが持つedgeは （source, target）と表現
                community_id_of_source = community_id_dict[source]
                community_id_of_target = community_id_dict[target]

                # もし、community_id_of_sourceとcommunity_id_of_targetが同じでない場合、metaedgeを作成
                metaedge_data = summarized_graph.get_edge_data(
                    community_id_of_source, community_id_of_target
                )
                if metaedge_data is None:
                    new_meta_edge_weight = 1
                else:
                    new_meta_edge_weight = metaedge_data["weight"] + 1

                # すでにedgeが存在するときはedgeの重みを更新 : datadict.update(attr)
                summarized_graph.add_edge(
                    community_id_of_source,
                    community_id_of_target,
                    weight=new_meta_edge_weight,
                )

    return summarized_graph


############# 具体的なレイアウトアルゴリズム #############
def spring_layout(G):
    return nx.spring_layout(
        G,
        k=2.0,  # ノード間の距離を大きく
        iterations=50,  # イテレーション回数を増やす
        scale=2,  # 全体的なスケールを大きく
    )
