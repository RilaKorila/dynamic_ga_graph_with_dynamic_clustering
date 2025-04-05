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

    # 各 time step t のコミュニティ C にラベルをつけておく
    labeled_partitions = []
    for t, part in enumerate(partitions):
        labeled_partitions.append([(t, c) for c in part])

    # 最初の時間のコミュニティはそのまま動的コミュニティとして登録
    for t, c in labeled_partitions[0]:
        dynamic_communities.append([(t, c)])

    # t=1 以降を順に処理
    for t in range(1, len(partitions)):
        used = set()

        for dc in dynamic_communities:
            _, last_c = dc[-1]
            best_match = -1
            best_score = 0.0

            for i, (curr_t, curr_c) in enumerate(labeled_partitions[t]):
                if i in used:
                    continue
                sim = __jaccard_similarity(last_c, curr_c)
                if sim >= theta and sim > best_score:
                    best_match = i
                    best_score = sim

            if best_match >= 0:
                dc.append(labeled_partitions[t][best_match])
                used.add(best_match)

        # まだ割り当てられていないコミュニティは新しい動的コミュニティとして登録
        for i, (curr_t, curr_c) in enumerate(labeled_partitions[t]):
            if i not in used:
                dynamic_communities.append([(curr_t, curr_c)])

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
