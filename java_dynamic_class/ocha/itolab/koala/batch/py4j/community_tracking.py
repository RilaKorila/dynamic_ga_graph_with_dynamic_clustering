from typing import List, Set, Tuple

def __jaccard_similarity(c1: Set[int], c2: Set[int]) -> float:
    return len(c1 & c2) / len(c1 | c2) if c1 | c2 else 0.0

def track_communities(partitions: List[List[Set[int]]], theta: float = 0.3) -> List[List[Tuple[int, Set[int]]]]:
    """
    Jaccard係数を用いた動的コミュニティの追跡。

    Args:
        partitions: List[List[Set[int]]] 各timestamp でのcommunity分割の結果をリスト形式で表現。
        theta: float コミュニティの類似度の閾値。（0 に近づくほど「ゆるく」追跡し、1 に近づくほど「厳しく」追跡。）
    Returns:
        List[List[Tuple[int, Set[int]]]] 動的コミュニティのリスト。
    """
    dynamic_communities = []

    # timestamp t のコミュニティ C にラベルをつけておく
    labeled_partitions = []
    for t, partition in enumerate(partitions):
        labeled_partitions.append([(t, community) for community in partition])

    # 最初の時間のコミュニティはそのまま動的コミュニティとして登録
    for t, community in labeled_partitions[0]:
        dynamic_communities.append([(t, community)])

    # t=1 以降を順に処理
    for t in range(1, len(partitions)):

        # 時刻tのコミュニティを順に比較
        for i, (cur_timestamp, cur_community) in enumerate(labeled_partitions[t]):
            is_similar_community_found = False

            for dc in dynamic_communities:
                # dc: [(1, [ts=1でそのdc_idに属するnode]), (2, [ts=2でそのdc_idに属するnode]), ... ] 
                last_timestamp, last_com = dc[-1] # 1つ前のtimestampで、そのdc_idに該当するcommunity

                sim = __jaccard_similarity(last_com, cur_community)

                if sim >= theta:
                    # 1つ前のtimestampに類似のcommunityがあった場合
                    is_similar_community_found = True
                    dc.append((cur_timestamp, cur_community))

            # 1つ前のtimestampの全てのcommunityを見ても類似のcommunityがなかった場合
            if not is_similar_community_found:
                dynamic_communities.append([(cur_timestamp, cur_community)])

    return dynamic_communities

def write_dynamic_communities_to_file(dynamic_communities: List[List[Tuple[int, Set[int]]]], file_path: str):
    with open(file_path, "w") as f:
        for dc in dynamic_communities:
            f.write(str(dc) + "\n")

if __name__ == "__main__":
    partitions = [
        [ {"A", "B", "C"}, {"D", "E", "F"}, {"G", "H"} ],               # t = 0
        [ {"A", "C"}, {"B", "D", "E"}, {"F", "G", "H"} ],              # t = 1
        [ {"A", "B"}, {"C", "D"}, {"E", "F"}, {"G", "H"} ],           # t = 2
        [ {"A", "B", "C"}, {"D", "E"}, {"F"}, {"G", "H"} ],           # t = 3
        [ {"A", "B", "C", "D"}, {"E", "F"}, {"G", "H"} ]              # t = 4
    ]
    print(track_communities(partitions))
