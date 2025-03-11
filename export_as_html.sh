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

### 出力する世代を指定
echo "何世代目をhtmlに変換する?? : "
# ユーザーからの入力を変数に格納
read target_generation

# 結果格納用のフォルダを作成
current_time=$(date "+%Y%m%d%H%M")
html_folder="${parent_html_folder}${current_time}_dynamic/"
mkdir ${html_folder}
echo "フォルダ '${html_folder}' が作成されました。"


### csv_viewerのプログラムを実行

# 移動
cd ../csv_viewer/

# 環境を起動
source streamlit_csv/bin/activate

# 実行

# supergraphsの可視化
# 引数：CSV_FOLDER, html_folder, node_color, node_size, target_generation
node_color="vectors" # vertexごとに彩色. node_nums, vectors, node_degree, high_node_degree  のどれか
node_size="same"
python createHtmls.py ${csv_folder} ${html_folder} ${node_color} ${node_size} ${target_generation}

## dynamic graphの可視化
# 引数：CSV_FOLDER,  html_folder, node_color, target_generation
node_color="gray" # TODO 既存のColor関連メソッドが正常に動作するかはみていないため、一旦grayを指定
python create_dynamic_graph_htmls.py ${csv_folder} ${html_folder} ${node_color} ${target_generation}

# 環境を閉じる
deactivate

# 結果を確認
open $parent_html_folder


