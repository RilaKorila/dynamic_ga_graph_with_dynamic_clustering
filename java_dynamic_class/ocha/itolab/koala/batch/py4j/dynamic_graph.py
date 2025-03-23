from data_process.CitHepPh import get_graph_sequence_from_original_file, setup_data
import networkx as nx

#### DynamicGraphクラス ####
class DynamicGraph:
    def __init__(self):
        ## データを取得 （使用するデータを変えるときはここを変更する）
        self.graph_sequence = get_graph_sequence_from_original_file(1)
        setup_data()
        self.weight_type = "overlap" # ノードの Live Time オーバーラップ
        # self.weight_type = "frequency" # エッジの出現回数
        self.node_time_live = self.compute_node_time_live()
        self.edge_time_live = self.compute_edge_time_live()
        self.supergraph = self.build_supergraph()

    def compute_node_time_live(self):
        """
        Computes the live time of each node in a dynamic graph sequence.

        Parameters:
        - graph_sequence: List of graphs [(V1, E1), (V2, E2), ..., (Vk, Ek)]
                        where each (Vi, Ei) represents the nodes and edges at time step i.

        Returns:
        - node_time_live: Dictionary mapping each node to its live time set {i, ...}.
        """
        node_time_live = {}

        for i, (V_i, _) in enumerate(self.graph_sequence):
            for v in V_i:
                if v not in node_time_live:
                    node_time_live[v] = set()
                node_time_live[v].add(i)

        return node_time_live

    def compute_edge_time_live(self):
        """
        Computes the live time of each edge in a dynamic graph sequence.

        Parameters:
        - graph_sequence: List of graphs [(V1, E1), (V2, E2), ..., (Vk, Ek)]
                        where each (Vi, Ei) represents the nodes and edges at time step i.

        Returns:
        - edge_time_live: Dictionary mapping each edge (u, v) to its live time set {i, ...}.
        """
        edge_time_live = {}

        for i, (_, E_i) in enumerate(self.graph_sequence):
            for (u, v) in E_i:
                edge = tuple(sorted([u, v]))  # 無向グラフの場合、(u, v) と (v, u) を統一
                if edge not in edge_time_live:
                    edge_time_live[edge] = set()
                edge_time_live[edge].add(i)

        return edge_time_live

    def build_supergraph(self):
        """
        Constructs a supergraph from a dynamic graph sequence with edge weights based on Live Time.

        Parameters:
        - node_time_live: Dictionary mapping each node to its live time set {i, ...}
        - edge_time_live: Dictionary mapping each edge to its live time set {i, ...}
        - weight_type: "overlap" (Live Time overlap) or "frequency" (edge occurrence count)

        Returns:
        - G_super: Weighted NetworkX graph (Supergraph)
        """
        G_super = nx.Graph()

        # ノードの追加
        for node, _ in self.node_time_live.items():
            G_super.add_node(node)

        # エッジの追加（Live Time に基づく重み設定）
        for (u, v), live_time in self.edge_time_live.items():
            if self.weight_type == "overlap":
                weight = len(self.node_time_live[u] & self.node_time_live[v])  # ノードの Live Time オーバーラップ
            elif self.weight_type == "frequency":
                weight = len(live_time)  # エッジの出現回数
            else:
                raise ValueError("Invalid weight_type. Use 'overlap' or 'frequency'.")

            G_super.add_edge(u, v, weight=weight)

        return G_super

    def create_sammarized_graph(self, communities):
        """
        Creates a summarized graph from the supergraph and communities.

        Parameters:
        - G_super: Weighted NetworkX graph (Supergraph) 
        - communities: Dictionary mapping nodes to community labels

        Returns:
        - summarized_graph: Weighted NetworkX graph (Summarized graph)
        """
        community_id_dict = {} # nodeがどのcommunityに属しているかを管理
        for i, community in enumerate(communities):
            for node in community:
                community_id_dict[node] = i

        sammarized_graph = nx.Graph()

        # metanodeの作成
        for community_id, community in enumerate(communities):
            # community_idを nodeのidとする
            # len(community)を nodeのsizeとする
            sammarized_graph.add_node(community_id, size=len(community))

        # metaedgeの作成: metanodeを構成するnodeが元々持っていたedgeを束ねたものをmetaedgeとする
        for community_id, community in enumerate(communities):
            # communityに属するnode全て走査
            for node in community:
                for source, target in self.supergraph.edges(node): # nodeが持つedgeは （source, target）と表現
                    community_id_of_source = community_id_dict[source]
                    community_id_of_target = community_id_dict[target]

                    # もし、community_id_of_sourceとcommunity_id_of_targetが同じでない場合、metaedgeを作成
                    metaedge_data = sammarized_graph.get_edge_data(community_id_of_source, community_id_of_target)
                    if metaedge_data is None:
                        new_meta_edge_weight = 1
                    else:
                        new_meta_edge_weight = metaedge_data["weight"] + 1

                    # すでにedgeが存在するときはedgeの重みを更新 : datadict.update(attr)
                    sammarized_graph.add_edge(community_id_of_source,  community_id_of_target, weight=new_meta_edge_weight)
        

        return sammarized_graph
        