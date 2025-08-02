from typing import List, Set, Tuple


def __jaccard_similarity(c1: Set[int], c2: Set[int]) -> float:
    return len(c1 & c2) / len(c1 | c2) if c1 | c2 else 0.0


def track_communities(
    partitions: List[List[Set[int]]], theta: float = 0.3
) -> List[List[Tuple[int, Set[int]]]]:
    """
    Jaccard係数を用いた動的コミュニティの追跡。

    Args:
        partitions: List[List[Set[int]]] 各timestamp でのcommunity分割の結果をリスト形式で表現。
        theta: float コミュニティの類似度の閾値。（0 に近づくほど「ゆるく」追跡し、1 に近づくほど「厳しく」追跡。）
    Returns:
        List[List[Tuple[int, Set[int]]]] 動的コミュニティのリスト。
    """
    dynamic_communities: List[List[Tuple[int, Set[int]]]] = []

    labeled_partitions = []
    for t, partition in enumerate(partitions):
        labeled_partitions.append([(t, community) for community in partition])

    # t=0 の各コミュニティを初期化
    for t, community in labeled_partitions[0]:
        dynamic_communities.append([(t, community)])

    for t in range(1, len(partitions)):

        for _, (cur_timestamp, cur_community) in enumerate(labeled_partitions[t]):
            best_similarity = 0.0
            best_dc_index = -1

            for dc_index, dc in enumerate(dynamic_communities):
                last_timestamp, last_community = dc[-1]
                sim = __jaccard_similarity(last_community, cur_community)

                if sim >= theta and sim > best_similarity:
                    best_similarity = sim
                    best_dc_index = dc_index

            if best_dc_index != -1:
                dynamic_communities[best_dc_index].append(
                    (cur_timestamp, cur_community)
                )
            else:
                dynamic_communities.append([(cur_timestamp, cur_community)])

    return dynamic_communities


def write_dynamic_communities_to_file(
    dynamic_communities: List[List[Tuple[int, Set[int]]]], file_path: str
):
    with open(file_path, "w") as f:
        for dc in dynamic_communities:
            f.write(str(dc) + "\n")


if __name__ == "__main__":
    partitions = [
        [{"A", "B", "C"}, {"D", "E", "F"}, {"G", "H"}],  # t = 0
        [{"A", "C"}, {"B", "D", "E"}, {"F", "G", "H"}],  # t = 1
        [{"A", "B"}, {"C", "D"}, {"E", "F"}, {"G", "H"}],  # t = 2
        [{"A", "B", "C"}, {"D", "E"}, {"F"}, {"G", "H"}],  # t = 3
        [{"A", "B", "C", "D"}, {"E", "F"}, {"G", "H"}],  # t = 4
    ]
    print(track_communities(partitions))
