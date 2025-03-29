from data_process.CitHepPh import get_graph_sequence_from_original_file, setup_data
import networkx as nx

#### DynamicGraphクラス ####
class DynamicGraph:
    def __init__(self):
        ## データを取得 （使用するデータを変えるときはここを変更する）
        self.graph_sequence = get_graph_sequence_from_original_file()
        setup_data()

    def create_summarized_graph(self, communities, timestamp):
        """
        特定のタイムスタンプにおけるコミュニティからsummarized_graphを作成する。
        (summarized_graphは、communityを1つのnodeとみなし抽象化したgraph。dynamic graph ではtimestampごとに存在する)

        Args:
        - communities (list(set)): 各communityが持つnodeの集合 をリストにしたもの
        - timestamp (int): summarized_graphを作成するtimestamp

        Returns:
        - summarized_graph: 重み付きNetworkXグラフ
        """
        community_id_dict = {}  # nodeがどのcommunityに属しているかを管理
        for i, community in enumerate(communities):
            for node in community:
                community_id_dict[node] = i

        summarized_graph = nx.Graph()

        # 特定のtimestampにおけるgraphのノードとエッジを取得
        nodes, edges = self.graph_sequence[timestamp]

        # metanodeの作成
        for community_id, community in enumerate(communities):
            # コミュニティに属する現在のタイムスタンプに存在するノードの数を計算
            active_nodes = len([node for node in community if node in nodes])
            if active_nodes > 0:  # アクティブなノードが存在する場合のみmetanodeを作成
                summarized_graph.add_node(community_id, size=active_nodes)

        # metaedgeの作成
        for edge in edges:
            source, target = edge
            if source in community_id_dict and target in community_id_dict:
                community_id_of_source = community_id_dict[source]
                community_id_of_target = community_id_dict[target]

                if community_id_of_source != community_id_of_target:
                    # 異なるコミュニティ間のエッジの場合
                    if summarized_graph.has_node(community_id_of_source) and summarized_graph.has_node(community_id_of_target):
                        # すでにエッジが存在する場合は重みを増やす
                        if summarized_graph.has_edge(community_id_of_source, community_id_of_target):
                            summarized_graph[community_id_of_source][community_id_of_target]['weight'] += 1
                        else:
                            # 新しいエッジを作成
                            summarized_graph.add_edge(community_id_of_source, community_id_of_target, weight=1)

        return summarized_graph
        