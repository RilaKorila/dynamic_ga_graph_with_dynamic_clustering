from community_tracking import track_communities
from typing import List, Set

if __name__ == "__main__":
    ## テスト

    # dynamic_community数が最小のケース (全てのtimestampで1つ前のtimestampに類似のcommunityが存在)
    print("== テスト：dynamic_community数が最小のケース ==")
    same_community_partitions: List[List[Set[int]]] = [
        [{1, 2, 3}, {4, 5, 6}, {7, 8}, {9}],  # t = 0
        [{1, 2, 3}, {4, 5, 6}, {7, 8}, {9}],  # t = 1
        [{1, 2, 3}, {4, 5, 6}, {7, 8}, {9}],  # t = 2
    ]

    actual_dynamic_communities = track_communities(same_community_partitions)

    expect_dynamic_communities = [
        [(0, {1, 2, 3}), (1, {1, 2, 3}), (2, {1, 2, 3})],
        [(0, {4, 5, 6}), (1, {4, 5, 6}), (2, {4, 5, 6})],
        [(0, {7, 8}), (1, {7, 8}), (2, {7, 8})],
        [(0, {9}), (1, {9}), (2, {9})],
    ]

    if len(actual_dynamic_communities) != len(expect_dynamic_communities):
        print(" ------- テストが通りませんでした ------- ")
        print(f"期待値: {len(expect_dynamic_communities)}")
        print(f"実際の値: {len(actual_dynamic_communities)}")

    if actual_dynamic_communities[0] != expect_dynamic_communities[0]:
        print(" ------- テストが通りませんでした ------- ")
        print(f"期待値: {expect_dynamic_communities[0]}")
        print(f"実際の値: {actual_dynamic_communities[0]}")

    if actual_dynamic_communities[1] != expect_dynamic_communities[1]:
        print(" ------- テストが通りませんでした ------- ")
        print(f"期待値: {expect_dynamic_communities[1]}")
        print(f"実際の値: {actual_dynamic_communities[1]}")

    if actual_dynamic_communities[2] != expect_dynamic_communities[2]:
        print(" ------- テストが通りませんでした ------- ")
        print(f"期待値: {expect_dynamic_communities[2]}")
        print(f"実際の値: {actual_dynamic_communities[2]}")

    # dynamic_community数が最大のケース (いずれのtimestampでも1つ前のtimestampに類似のcommunityが存在しない)
    print("== テスト：dynamic_community数が最大のケース ==")

    same_community_partitions: List[List[Set[int]]] = [
        [{1, 2, 3}],  # t = 0
        [{4, 5, 6}],  # t = 1
        [{7, 8}, {9}],  # t = 2
    ]

    actual_dynamic_communities = track_communities(same_community_partitions)
    expect_dynamic_communities = [
        [(0, {1, 2, 3})],
        [(1, {4, 5, 6})],
        [(2, {7, 8})],
        [(2, {9})],
    ]

    if len(actual_dynamic_communities) != len(expect_dynamic_communities):
        print(" ------- テストが通りませんでした: dynamic_communitiesの長さ ------- ")
        print(f"期待値: {len(expect_dynamic_communities)}")
        print(f"実際の値: {len(actual_dynamic_communities)}")

    if actual_dynamic_communities[0] != expect_dynamic_communities[0]:
        print(" ------- テストが通りませんでした: dynamic_communities[0] ------- ")
        print(f"期待値: {expect_dynamic_communities[0]}")
        print(f"実際の値: {actual_dynamic_communities[0]}")

    if actual_dynamic_communities[1] != expect_dynamic_communities[1]:
        print(" ------- テストが通りませんでした: dynamic_communities[1] ------- ")
        print(f"期待値: {expect_dynamic_communities[1]}")
        print(f"実際の値: {actual_dynamic_communities[1]}")

    if actual_dynamic_communities[2] != expect_dynamic_communities[2]:
        print(" ------- テストが通りませんでした: dynamic_communities[2] ------- ")
        print(f"期待値: {expect_dynamic_communities[2]}")
        print(f"実際の値: {actual_dynamic_communities[2]}")

    if actual_dynamic_communities[3] != expect_dynamic_communities[3]:
        print(" ------- テストが通りませんでした: dynamic_communities[3] ------- ")
        print(f"期待値: {expect_dynamic_communities[3]}")
        print(f"実際の値: {actual_dynamic_communities[3]}")

    # timestamp 1, 3 の コミュニティが同じケース
    print("== テスト：timestamp 1,3 の コミュニティが同じケース ==")

    same_community_partitions: List[List[Set[int]]] = [
        [{1, 2, 3}],  # t = 0
        [{4, 5, 6}],  # t = 1
        [{1, 2, 3}],  # t = 2
    ]

    actual_dynamic_communities = track_communities(same_community_partitions)
    expect_dynamic_communities = [
        [(0, {1, 2, 3}), (2, {1, 2, 3})],
        [(1, {4, 5, 6})],
    ]

    if len(actual_dynamic_communities) != len(expect_dynamic_communities):
        print(" ------- テストが通りませんでした: dynamic_communitiesの長さ ------- ")
        print(f"期待値: {len(expect_dynamic_communities)}")
        print(f"実際の値: {len(actual_dynamic_communities)}")

    if actual_dynamic_communities[0] != expect_dynamic_communities[0]:
        print(" ------- テストが通りませんでした: dynamic_communities[0] ------- ")
        print(f"期待値: {expect_dynamic_communities[0]}")
        print(f"実際の値: {actual_dynamic_communities[0]}")

    if actual_dynamic_communities[1] != expect_dynamic_communities[1]:
        print(" ------- テストが通りませんでした: dynamic_communities[1] ------- ")
        print(f"期待値: {expect_dynamic_communities[1]}")
        print(f"実際の値: {actual_dynamic_communities[1]}")

    # timestamp 1, 3 の コミュニティが似ているケース
    print(
        "== テスト：timestamp 1,3 の コミュニティが似ているケース(ゆるいマッチング) =="
    )

    same_community_partitions: List[List[Set[int]]] = [
        [{1, 2, 3}],  # t = 0
        [{4, 5, 6}],  # t = 1
        [{1}],  # t = 2
    ]

    actual_dynamic_communities = track_communities(same_community_partitions, 0.1)
    expect_dynamic_communities = [
        [
            (0, {1, 2, 3}),
            (2, {1}),
        ],  # ゆるいマッチングのため、timestamp 1, 3 のコミュニティは同じものとして扱われる
        [(1, {4, 5, 6})],
    ]

    if len(actual_dynamic_communities) != len(expect_dynamic_communities):
        print(" ------- テストが通りませんでした: dynamic_communitiesの長さ ------- ")
        print(f"期待値: {len(expect_dynamic_communities)}")
        print(f"実際の値: {len(actual_dynamic_communities)}")

    if actual_dynamic_communities[0] != expect_dynamic_communities[0]:
        print(" ------- テストが通りませんでした: dynamic_communities[0] ------- ")
        print(f"期待値: {expect_dynamic_communities[0]}")
        print(f"実際の値: {actual_dynamic_communities[0]}")

    if actual_dynamic_communities[1] != expect_dynamic_communities[1]:
        print(" ------- テストが通りませんでした: dynamic_communities[1] ------- ")
        print(f"期待値: {expect_dynamic_communities[1]}")
        print(f"実際の値: {actual_dynamic_communities[1]}")

    # timestamp 1, 3 の コミュニティが似ているケース
    print(
        "== テスト：timestamp 1,3 の コミュニティが似ているケース(厳しいマッチング) =="
    )

    same_community_partitions: List[List[Set[int]]] = [
        [{1, 2, 3}],  # t = 0
        [{4, 5, 6}],  # t = 1
        [{1}],  # t = 2
    ]

    actual_dynamic_communities = track_communities(same_community_partitions, 0.9)
    expect_dynamic_communities = [
        [(0, {1, 2, 3})],
        [(1, {4, 5, 6})],
        [
            (2, {1})
        ],  # 厳しいマッチングのため、timestamp 1, 3 のコミュニティは別々に扱われる
    ]

    if len(actual_dynamic_communities) != len(expect_dynamic_communities):
        print(" ------- テストが通りませんでした: dynamic_communitiesの長さ ------- ")
        print(f"期待値: {len(expect_dynamic_communities)}")
        print(f"実際の値: {len(actual_dynamic_communities)}")

    if actual_dynamic_communities[0] != expect_dynamic_communities[0]:
        print(" ------- テストが通りませんでした: dynamic_communities[0] ------- ")
        print(f"期待値: {expect_dynamic_communities[0]}")
        print(f"実際の値: {actual_dynamic_communities[0]}")

    if actual_dynamic_communities[1] != expect_dynamic_communities[1]:
        print(" ------- テストが通りませんでした: dynamic_communities[1] ------- ")
        print(f"期待値: {expect_dynamic_communities[1]}")
        print(f"実際の値: {actual_dynamic_communities[1]}")

    print(
        "== テスト：timestamp 1,3 の コミュニティが似ているケース(厳しいマッチング) =="
    )

    same_community_partitions: List[List[Set[int]]] = [
        [{1, 2, 3}],  # t = 0
        [{4, 5, 6}],  # t = 1
        [{1}],  # t = 2
    ]

    actual_dynamic_communities = track_communities(same_community_partitions, 0.9)
    expect_dynamic_communities = [
        [(0, {1, 2, 3})],
        [(1, {4, 5, 6})],
        [
            (2, {1})
        ],  # 厳しいマッチングのため、timestamp 1, 3 のコミュニティは別々に扱われる
    ]

    if len(actual_dynamic_communities) != len(expect_dynamic_communities):
        print(" ------- テストが通りませんでした: dynamic_communitiesの長さ ------- ")
        print(f"期待値: {len(expect_dynamic_communities)}")
        print(f"実際の値: {len(actual_dynamic_communities)}")

    if actual_dynamic_communities[0] != expect_dynamic_communities[0]:
        print(" ------- テストが通りませんでした: dynamic_communities[0] ------- ")
        print(f"期待値: {expect_dynamic_communities[0]}")
        print(f"実際の値: {actual_dynamic_communities[0]}")

    if actual_dynamic_communities[1] != expect_dynamic_communities[1]:
        print(" ------- テストが通りませんでした: dynamic_communities[1] ------- ")
        print(f"期待値: {expect_dynamic_communities[1]}")
        print(f"実際の値: {actual_dynamic_communities[1]}")

    print("== テスト：共通のcommunityが遠いidに存在するケース ==")

    same_community_partitions: List[List[Set[int]]] = [
        [{1, 2, 3}, {4, 5, 6}, {7, 8}, {9}],  # t = 0
        [{4, 5, 6}, {7, 8}, {1, 2, 3}, {9}],  # t = 1
        [{9}, {1, 2, 3}, {7, 8}, {4, 5, 6}],  # t = 2
    ]

    actual_dynamic_communities = track_communities(same_community_partitions)

    expect_dynamic_communities = [
        [(0, {1, 2, 3}), (1, {1, 2, 3}), (2, {1, 2, 3})],
        [(0, {4, 5, 6}), (1, {4, 5, 6}), (2, {4, 5, 6})],
        [(0, {7, 8}), (1, {7, 8}), (2, {7, 8})],
        [(0, {9}), (1, {9}), (2, {9})],
    ]

    if len(actual_dynamic_communities) != len(expect_dynamic_communities):
        print(" ------- テストが通りませんでした: dynamic_communitiesの長さ ------- ")
        print(f"期待値: {len(expect_dynamic_communities)}")
        print(f"実際の値: {len(actual_dynamic_communities)}")

    if actual_dynamic_communities[0] != expect_dynamic_communities[0]:
        print(" ------- テストが通りませんでした: dynamic_communities[0] ------- ")
        print(f"期待値: {expect_dynamic_communities[0]}")
        print(f"実際の値: {actual_dynamic_communities[0]}")

    if actual_dynamic_communities[1] != expect_dynamic_communities[1]:
        print(" ------- テストが通りませんでした: dynamic_communities[1] ------- ")
        print(f"期待値: {expect_dynamic_communities[1]}")
        print(f"実際の値: {actual_dynamic_communities[1]}")

    if actual_dynamic_communities[2] != expect_dynamic_communities[2]:
        print(" ------- テストが通りませんでした: dynamic_communities[2] ------- ")
        print(f"期待値: {expect_dynamic_communities[2]}")
        print(f"実際の値: {actual_dynamic_communities[2]}")
