# from data_process.CitHepPh import get_graph_sequence_from_original_file, setup_data
# from data_process.facebook import get_graph_sequence_from_original_file, setup_data
from data_process.timesmoothnessSample import get_graph_sequence_from_original_file, setup_data
from community_detect import get_community_detection_result
from community_tracking import track_communities
from constants import TIMESMOOTHNESS_SAMPLE_DIR_PATH as DATA_DIR_PATH

import networkx as nx

DATASET_NAME = "timesmoothnessSample"  # データセット名を指定。使用するデータに応じて変更すること。
# DATASET_NAME = "Cit-HepPh"  # データセット名を指定。使用するデータに応じて変更すること。

#### DynamicGraphクラス ####
class DynamicGraph:
    def __init__(self, timestamps):
        self.timestamps = timestamps

        # 使用するデータに依存した setup_data メソッドを呼び出す
        setup_data(self.timestamps)

        ## データを取得 （使用するデータを変えるときはここを変更する）
        self.graph_sequence_dict = get_graph_sequence_from_original_file(self.timestamps)

        # timestampとcommunityの紐付け
        self.communities_dict = {timestamp : get_community_detection_result(timestamp) 
                            for timestamp in self.timestamps}
        # timestampとsummarized_graphの紐付け
        self.summarized_graphs = {timestamp : self.create_summarized_graph(community, timestamp) 
                                  for timestamp, community in self.communities_dict.items()}
        
        # 動的コミュニティの追跡結果を保存
        self.time_ordered_dynamic_communities_dict = self.get_time_ordered_dynamic_communities_dict()

        self.write_dynamic_communities_to_file(DATA_DIR_PATH + "dynamic_communities/", self.time_ordered_dynamic_communities_dict)

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
        nodes, edges = self.graph_sequence_dict[timestamp]

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
    
    def get_time_ordered_dynamic_communities_dict(self):
        """
        Returns:
            dict[int, list[set[int]]]: timestampごとの動的コミュニティをリストを作成し、timestampをkey, 集約結果をvalueとしたdict
        """
        communities = list(self.communities_dict.values())
        # theta値は調整可能。値が大きいほど厳密なマッチングになる
        all_dynamic_communities = track_communities(communities, theta=0.25)

        time_ordered_dynamic_communities_dict = {}

        # 各タイムスタンプに対して動的コミュニティを整理
        for timestamp in self.timestamps:
            dynamic_communities = [set() for _ in range(len(all_dynamic_communities))]

            for dynamic_community_id, community_list in enumerate(all_dynamic_communities):
                for time_idx, community in community_list:
                    if timestamp == self.timestamps[time_idx]:
                        dynamic_communities[dynamic_community_id] = community
                        break

            time_ordered_dynamic_communities_dict[timestamp] = dynamic_communities

        return time_ordered_dynamic_communities_dict
    
    def get_dynamic_community_by_timestamp(self, all_dynamic_communities, target_timestamp):
        """
        timestampに対応する動的コミュニティを取得する

        Args:
        - target_timestamp (int): 取得する動的コミュニティのtimestamp

        Returns:
        - dynamic_community (list(set[int])): 動的コミュニティのノードの集合。要素の0番目は、dynamic_community_id=0のコミュニティに属するノード群。
        """
        dynamic_community_ordered_by_dynamic_community_id = []
        for dynamic_community_id, dynamic_community in enumerate(all_dynamic_communities):
            for time_idx, nodes in dynamic_community:
                if self.timestamps[time_idx] == target_timestamp:
                    dynamic_community_ordered_by_dynamic_community_id.append(nodes)
                else:
                    # 該当する動的コミュニティが存在しない場合は空のリストを追加
                    dynamic_community_ordered_by_dynamic_community_id.append(set())

        return dynamic_community_ordered_by_dynamic_community_id

    def get_summarized_graph(self, timestamp):
        return self.summarized_graphs[timestamp]

    def get_communities(self, timestamp):
        return self.communities_dict[timestamp]

    def write_dynamic_communities_to_file(self, file_path, time_ordered_dynamic_communities_dict):
        # 各タイムスタンプごとに動的コミュニティファイルを作成
        for timestamp in self.timestamps:
            fname = file_path + "dynamic_community_" + str(timestamp) + ".txt"
            with open(fname, "w") as f:
                dynamic_communities = time_ordered_dynamic_communities_dict[timestamp]
                for id, dynamic_community in enumerate(dynamic_communities):
                    f.write(str(id) + ":\n")
                    if len(dynamic_community) == 0:
                        f.write("\n")
                    else:
                        # dynamic_community を並び替えて、,でjoinして出力
                        f.write(",".join(str(node) for node in sorted(dynamic_community)) + "\n")

        self._check_assigned_dynamic_community_id()
    
    def _check_assigned_dynamic_community_id(self):
        """
        coms/配下のファイルに含まれるノードIDと、timestampごとに分割したdynamic_communityに含まれるノードIDが各timestampで一致していることを確認する
        """
        for timestamp in self.timestamps:
            # coms/配下のファイルと、dynamic_community_1.txt の内容を比較する
            coms_file_path = DATA_DIR_PATH + f"coms/runDynamicModularity_{DATASET_NAME}_com_{str(timestamp)}_nodes.csv"

            # dynamic clusteringの結果
            dynamic_clustering_result_nodes_list= list()
            with open(coms_file_path, "r") as f:
                coms_file_content = f.read()
                for line in coms_file_content.split("\n"):
                    if line.strip() == "":
                        continue
                    nodes = line.split(",")
                    sorted_nodes = sorted(nodes)
                    dynamic_clustering_result_nodes_list.append(sorted_nodes)

            # community trackingの結果
            dc_nodes_list = list()
            with open(DATA_DIR_PATH + "dynamic_communities/dynamic_community_" + str(timestamp) + ".txt", "r") as f:
                dynamic_community_file_content = f.read()
                for line in dynamic_community_file_content.split("\n"):
                    if line.strip() == "":
                        continue
                    if line[-1] == ":":
                        continue
                    nodes = line.split(",")
                    sorted_dc_nodes = sorted(nodes)
                    dc_nodes_list.append(sorted_dc_nodes)

            for nodes in dc_nodes_list:
                if nodes not in dynamic_clustering_result_nodes_list:
                    print("WARNING: dynamic_community_" + str(timestamp) + ".txt に存在しないノードが含まれています。")
                    print(nodes)
            for nodes in dynamic_clustering_result_nodes_list:
                if nodes not in dc_nodes_list:
                    print("WARNING: dynamic_community_" + str(timestamp) + ".txt の内容が不足しています。")
