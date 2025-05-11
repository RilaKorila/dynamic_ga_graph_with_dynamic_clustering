from community_tracking import track_communities

if __name__ == "__main__":
        ## テスト

    # dynamic_community数が最小のケース (全てのtimestampで1つ前のtimestampに類似のcommunityが存在)
    print("== テスト：dynamic_community数が最小のケース ==")
    same_community_partitions = [
        [ {"A", "B", "C"}, {"D", "E", "F"}, {"G", "H"}, {"I"} ],           # t = 0
        [ {"A", "B", "C"}, {"D", "E", "F"}, {"G", "H"}, {"I"} ],           # t = 1
        [ {"A", "B", "C"}, {"D", "E", "F"}, {"G", "H"}, {"I"} ],           # t = 2   
    ]

    actual_dynamic_communities = track_communities(same_community_partitions)

    expect_dynamic_communities = [
        [(0, {"A", "B", "C"}), (1, {"A", "B", "C"}), (2, {"A", "B", "C"})],
        [(0, {"D", "E", "F"}), (1, {"D", "E", "F"}), (2, {"D", "E", "F"})],
        [(0, {"G", "H"}), (1, {"G", "H"}), (2, {"G", "H"})],
        [(0, {"I"}), (1, {"I"}), (2, {"I"})]
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

    same_community_partitions = [
        [ {"A", "B", "C"}],           # t = 0
        [ {"D", "E", "F"}],           # t = 1
        [ {"G", "H"}, {"I"} ],        # t = 2   
    ]

    actual_dynamic_communities = track_communities(same_community_partitions)
    expect_dynamic_communities = [
        [(0, {"A", "B", "C"})],
        [(1, {"D", "E", "F"})],
        [(2, {"G", "H"})],
        [(2, {"I"})],
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

    same_community_partitions = [
        [ {"A", "B", "C"}],           # t = 0
        [ {"D", "E", "F"}],           # t = 1
        [ {"A", "B", "C"} ],        # t = 2   
    ]

    actual_dynamic_communities = track_communities(same_community_partitions)
    expect_dynamic_communities = [
        [(0, {"A", "B", "C"}), (2, {"A", "B", "C"})],
        [(1, {"D", "E", "F"})]
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
    print("== テスト：timestamp 1,3 の コミュニティが似ているケース(ゆるいマッチング) ==")

    same_community_partitions = [
        [ {"A", "B", "C"}],           # t = 0
        [ {"D", "E", "F"}],           # t = 1
        [ {"A"} ],        # t = 2   
    ]

    actual_dynamic_communities = track_communities(same_community_partitions, 0.1)
    expect_dynamic_communities = [
        [(0, {"A", "B", "C"}), (2, {"A"})], # ゆるいマッチングのため、timestamp 1, 3 のコミュニティは同じものとして扱われる
        [(1, {"D", "E", "F"})]
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
    print("== テスト：timestamp 1,3 の コミュニティが似ているケース(厳しいマッチング) ==")

    same_community_partitions = [
        [ {"A", "B", "C"}],           # t = 0
        [ {"D", "E", "F"}],           # t = 1
        [ {"A"} ],        # t = 2   
    ]

    actual_dynamic_communities = track_communities(same_community_partitions, 0.9)
    expect_dynamic_communities = [
        [(0, {"A", "B", "C"})],
        [(1, {"D", "E", "F"})],
        [(2, {"A"})] # 厳しいマッチングのため、timestamp 1, 3 のコミュニティは別々に扱われる
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

    print("== テスト：timestamp 1,3 の コミュニティが似ているケース(厳しいマッチング) ==")

    same_community_partitions = [
        [ {"A", "B", "C"}],           # t = 0
        [ {"D", "E", "F"}],           # t = 1
        [ {"A"} ],        # t = 2   
    ]

    actual_dynamic_communities = track_communities(same_community_partitions, 0.9)
    expect_dynamic_communities = [
        [(0, {"A", "B", "C"})],
        [(1, {"D", "E", "F"})],
        [(2, {"A"})] # 厳しいマッチングのため、timestamp 1, 3 のコミュニティは別々に扱われる
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

    same_community_partitions = [
        [ {"A", "B", "C"}, {"D", "E", "F"}, {"G", "H"}, {"I"} ],           # t = 0
        [ {"D", "E", "F"}, {"G", "H"}, {"A", "B", "C"}, {"I"} ],           # t = 1
        [ {"I"}, {"A", "B", "C"}, {"G", "H"}, {"D", "E", "F"}],           # t = 2   
    ]

    actual_dynamic_communities = track_communities(same_community_partitions)

    expect_dynamic_communities = [
        [(0, {"A", "B", "C"}), (1, {"A", "B", "C"}), (2, {"A", "B", "C"})],
        [(0, {"D", "E", "F"}), (1, {"D", "E", "F"}), (2, {"D", "E", "F"})],
        [(0, {"G", "H"}), (1, {"G", "H"}), (2, {"G", "H"})],
        [(0, {"I"}), (1, {"I"}), (2, {"I"})]
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
