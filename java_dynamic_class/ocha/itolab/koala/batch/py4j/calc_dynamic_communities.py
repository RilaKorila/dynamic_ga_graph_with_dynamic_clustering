from collections import defaultdict

### 動作確認用のスクリプト

def count_nodes_per_id(file_path):
    """
    dynamic_community_n.txt ファイルを読み込み、各 id ごとの node_id の数をカウントする。
    1行目が community_id:、次の行がその community_id に属する node_id がカンマ区切りで記載されている形式に対応。

    :param 
    - file_path: dynamic_community_n.txt のパス

    :return: 
    - id_to_node_count: 各 id ごとの node_id の数を格納した辞書
    """
    id_to_node_count = {}
    current_id = None

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.endswith(':'):
                # Extract community_id from the line
                current_id = line[:-1].strip()
                id_to_node_count[current_id] = 0
            elif line:
                # Count node_ids for the current community_id
                node_ids = line.split(',')
                id_to_node_count[current_id] += len(node_ids)
            else:
                # Handle empty lines
                id_to_node_count[current_id] += 0


    return id_to_node_count


if __name__ == "__main__":
    # base_url = "./data/Cit-HepPh/dynamic_communities/"
    # base_url = "./data/facebook/dynamic_communities/"
    base_url = "./data/timesmoothnessSample/dynamic_communities/"

    result = defaultdict(list)
    for i in range(1, 4):
        counts = count_nodes_per_id(f"{base_url}dynamic_community_{i}.txt")
        for community_id, count in counts.items():
            result[community_id].append(count)

    with open("memo.txt", "w") as output_file:
        output_file.write("community_id,ts_1,ts_2,ts_3\n")
        for community_id, count_list in result.items():
            output_file.write(f"{community_id},{','.join(map(str, count_list))}\n")
