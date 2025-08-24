from collections import defaultdict
from community_detect import get_community_detection_result
from community_tracking import track_communities
import json
import os
import networkx as nx

# データ変更
# import data_process.CitHepPh as data_process

# from data_process.facebook as data_process
# import data_process.timesmoothnessSample as data_process
import data_process.NBAF_coauthors as data_process

# データ変更
# from constants import CIT_HEP_PH_DIR_PATH as DATA_DIR_PATH

from constants import NBAF_COAUTHORS_DIR_PATH as DATA_DIR_PATH

# from constants import FACEBOOK_DIR_PATH as DATA_DIR_PATH
# from constants import TIMESMOOTHNESS_SAMPLE_DIR_PATH as DATA_DIR_PATH


DATASET_NAME = data_process.DATASET_NAME


class PreviousSimilarCommunity:
    def __init__(self, id, similarity) -> None:
        self.id = id
        self.similarity = similarity


#### DynamicGraphクラス ####
class DynamicGraph:
    def __init__(self, timestamps):
        self.timestamps = timestamps

        # 使用するデータに依存した setup_data メソッドを呼び出す
        data_process.setup_data(self.timestamps)

        ## データを取得 （使用するデータを変えるときはここを変更する）
        self.graph_sequence_dict = data_process.get_graph_sequence_from_original_file(
            self.timestamps
        )

        # timestampとcommunityの紐付け
        self.communities_dict = {
            timestamp: get_community_detection_result(timestamp)
            for timestamp in self.timestamps
        }
        # timestampとsummarized_graphの紐付け
        self.summarized_graphs = {
            timestamp: self.create_summarized_graph(community, timestamp)
            for timestamp, community in self.communities_dict.items()
        }

        # 動的コミュニティの追跡結果を保存
        self.time_ordered_dynamic_communities_dict = (
            self.get_time_ordered_dynamic_communities_dict()
        )

        self.write_dynamic_communities_to_file(
            DATA_DIR_PATH + "dynamic_communities/",
            self.time_ordered_dynamic_communities_dict,
        )

        # グラフを構成するnode情報を読み込む
        self.graph_info_dict = {
            timestamp: data_process.load_graph_info(timestamp)
            for timestamp in self.timestamps
        }

        self.similar_cluster_dict_of_all_timestamps = (
            self.get_similar_cluster_dict_of_all_timestamps()
        )

        self.write_similar_cluster_dict_of_all_timestamps_to_file(
            DATA_DIR_PATH + "similar_cluster_dict/"
        )

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
                    if summarized_graph.has_node(
                        community_id_of_source
                    ) and summarized_graph.has_node(community_id_of_target):
                        # すでにエッジが存在する場合は重みを増やす
                        if summarized_graph.has_edge(
                            community_id_of_source, community_id_of_target
                        ):
                            summarized_graph[community_id_of_source][
                                community_id_of_target
                            ]["weight"] += 1
                        else:
                            # 新しいエッジを作成
                            summarized_graph.add_edge(
                                community_id_of_source, community_id_of_target, weight=1
                            )

        return summarized_graph

    def get_time_ordered_dynamic_communities_dict(self):
        """
        Returns:
            dict[int, list[set[int]]]: timestampごとの動的コミュニティをリストを作成し、timestampをkey, 集約結果をvalueとしたdict
        """
        communities = list(self.communities_dict.values())
        # theta値は調整可能。値が大きいほど厳密なマッチングになる
        all_dynamic_communities = track_communities(communities, theta=0.1)

        time_ordered_dynamic_communities_dict = {}

        # 各タイムスタンプに対して動的コミュニティを整理
        for timestamp in self.timestamps:
            dynamic_communities = [set() for _ in range(len(all_dynamic_communities))]

            for dynamic_community_id, community_list in enumerate(
                all_dynamic_communities
            ):
                for time_idx, community in community_list:
                    if timestamp == self.timestamps[time_idx]:
                        dynamic_communities[dynamic_community_id] = community
                        break

            time_ordered_dynamic_communities_dict[timestamp] = dynamic_communities

        return time_ordered_dynamic_communities_dict

    def get_dynamic_community_by_timestamp(
        self, all_dynamic_communities, target_timestamp
    ):
        """
        timestampに対応する動的コミュニティを取得する

        Args:
        - target_timestamp (int): 取得する動的コミュニティのtimestamp

        Returns:
        - dynamic_community (list(set[int])): 動的コミュニティのノードの集合。要素の0番目は、dynamic_community_id=0のコミュニティに属するノード群。
        """
        dynamic_community_ordered_by_dynamic_community_id = []
        for dynamic_community_id, dynamic_community in enumerate(
            all_dynamic_communities
        ):
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

    def get_graph_info(self, timestamp):
        return self.graph_info_dict[timestamp]

    def get_similar_cluster_dict_of_all_timestamps(self):
        similar_cluster_dict_of_all_timestamps = {}
        for i in range(1, len(self.timestamps)):
            pre_timestamp = self.timestamps[i - 1]
            cur_timestamp = self.timestamps[i]

            similar_cluster_dict_of_all_timestamps[cur_timestamp] = (
                self._get_similar_cluster_dict(cur_timestamp, pre_timestamp)
            )

        return similar_cluster_dict_of_all_timestamps

    def _get_similar_cluster_dict(self, timestamp, previous_timestamp):
        JACCARD_THRESHOLD = 0.1

        def __calc_jaccard_similarity(c1, c2) -> float:
            return len(c1 & c2) / len(c1 | c2) if c1 | c2 else 0.0

        cluster_similarity_dict = defaultdict(list)
        current_graph_info = self.graph_info_dict[timestamp]
        previous_graph_info = self.graph_info_dict[previous_timestamp]

        current_cluster_ids = list(current_graph_info.keys())
        previous_cluster_ids = list(previous_graph_info.keys())

        for current_cluster_id in current_cluster_ids:
            for previous_cluster_id in previous_cluster_ids:
                sim = __calc_jaccard_similarity(
                    current_graph_info[current_cluster_id],
                    previous_graph_info[previous_cluster_id],
                )

                if sim > JACCARD_THRESHOLD:
                    cluster_similarity_dict[current_cluster_id].append(
                        PreviousSimilarCommunity(previous_cluster_id, sim)
                    )

        return cluster_similarity_dict

    def get_previous_similarity_dict(self, timestamp):
        return self.similar_cluster_dict_of_all_timestamps.get(timestamp, {})

    def get_similar_cluster_dict(self, timestamp):
        """
        キーが current dynamic graphに含まれるcommunity_id,
        バリューがそのcommunityと類似度の高いprevious_timestampのcommunity_idのリストで構成される
        辞書型の変数を返す
        """
        similar_cluster_dict = {}

        tmp = self.similar_cluster_dict_of_all_timestamps[timestamp]
        for k, v in tmp.items():
            similar_cluster_dict[k] = list(map(lambda x: x.id, v))

        return similar_cluster_dict

    def write_dynamic_communities_to_file(
        self, file_path, time_ordered_dynamic_communities_dict
    ):
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
                        f.write(
                            ",".join(str(node) for node in sorted(dynamic_community))
                            + "\n"
                        )

        self._check_assigned_dynamic_community_id()

    def _check_assigned_dynamic_community_id(self):
        """
        coms/配下のファイルに含まれるノードIDと、timestampごとに分割したdynamic_communityに含まれるノードIDが各timestampで一致していることを確認する
        """
        for timestamp in self.timestamps:
            # coms/配下のファイルと、dynamic_community_1.txt の内容を比較する
            coms_file_path = (
                DATA_DIR_PATH
                + f"filtered_coms/runDynamicModularity_{DATASET_NAME}_com_{str(timestamp)}_nodes.csv"
            )

            # dynamic clusteringの結果
            dynamic_clustering_result_nodes_list = list()
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
            with open(
                DATA_DIR_PATH
                + "dynamic_communities/dynamic_community_"
                + str(timestamp)
                + ".txt",
                "r",
            ) as f:
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
                    print(
                        "WARNING: dynamic_community_"
                        + str(timestamp)
                        + ".txt に存在しないノードが含まれています。"
                    )
                    print(nodes)
            for nodes in dynamic_clustering_result_nodes_list:
                if nodes not in dc_nodes_list:
                    print(
                        "WARNING: dynamic_community_"
                        + str(timestamp)
                        + ".txt の内容が不足しています。"
                    )

    def write_similar_cluster_dict_of_all_timestamps_to_file(self, file_path):
        """
        すべてのタイムスタンプの類似クラスタ辞書をJSONファイルに出力する

        Args:
            file_path (str): 出力先ディレクトリのパス
        """
        # 出力ディレクトリを作成
        os.makedirs(file_path, exist_ok=True)

        # 各タイムスタンプペアについて類似クラスタ辞書をJSONファイルに出力
        for i in range(1, len(self.timestamps)):
            current_timestamp = self.timestamps[i]
            previous_timestamp = self.timestamps[i - 1]

            # 類似クラスタ辞書を取得
            similar_cluster_dict = self.similar_cluster_dict_of_all_timestamps[
                current_timestamp
            ]

            # JSON形式に変換（PreviousCommunityオブジェクトを辞書に変換）
            json_dict = defaultdict(list)
            for (
                current_cluster_id,
                previous_communities,
            ) in similar_cluster_dict.items():
                for previous_community in previous_communities:
                    json_dict[str(current_cluster_id)].append(
                        {
                            "previous_cluster_id": previous_community.id,
                            "similarity": previous_community.similarity,
                        }
                    )

            # ファイル名を作成
            filename = (
                f"similar_cluster_dict_{previous_timestamp}_to_{current_timestamp}.json"
            )
            filepath = file_path + filename

            # JSONファイルに出力
            with open(filepath, "w") as f:
                json.dump(json_dict, f, indent=2)

            print(f"Similar cluster dict saved to: {filepath}")
