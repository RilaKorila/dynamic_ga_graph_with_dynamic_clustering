#!/bin/zsh

### 準備
# パスを指定 
csv_folder="/Users/ayana/vis/dynamic_ga_graph_with_dynamic_clustering/_csv_result/"
parent_html_folder="/Users/ayana/vis/dynamic_ga_graph_with_dynamic_clustering/_html_results/"

# 結果を格納するフォルダの存在を確認
if [ ! -d $parent_html_folder ]; then
    mkdir $parent_html_folder
    echo "_html_folder を作成しました！"
fi

# 結果格納用のフォルダを作成
current_time=$(date "+%Y%m%d%H%M")
csv_folder="/Users/ayana/vis/dynamic_ga_graph_with_dynamic_clustering/_csv_result/"
html_folder="${parent_html_folder}timestamp_${target_timestamp}_${target_generation}世代_${current_time}/"
mkdir ${html_folder}
echo "フォルダ '${html_folder}' が作成されました。"


### csv_viewerのプログラムを実行

# 移動
cd ../csv_viewer/

# 環境を起動
source streamlit_csv/bin/activate

# 実行

# 特定のtimestamp の graph可視化
# 引数：CSV_FOLDER, html_folder, node_color, node_size, target_generation
# vertexごとに彩色. node_nums, vectors, node_degree, high_node_degree  のどれか
# dynamic_graphの時は、dynamic_community_idも選択可能
node_color="dynamic_community_id" 
node_size="same"
# dataset_name="Cit-HepPh"
# dataset_name="facebook"
dataset_name="timesmoothnessSample"
target_timestamp="2"
previous_timestamp="1"
python createDynamicGraphHtmls.py ${csv_folder} ${html_folder} ${target_timestamp} ${previous_timestamp} ${dataset_name}

# 環境を閉じる
deactivate

# 結果を確認
open $parent_html_folder


