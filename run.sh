#!/bin/zsh

# 結果を格納するフォルダのパスを指定
csv_folder="./_csv_result"
plot_folder="./_plot_result"
supergraph_folder="./_supergraph_result"

# 仮想環境起動
source ./env/bin/activate

# 結果を格納するフォルダの存在を確認
if [ ! -d $csv_folder ]; then
    mkdir $csv_folder
    echo "_csv_result を作成しました！"
fi
if [ ! -d $plot_folder ]; then
    mkdir $plot_folder
    echo "_plot_result を作成しました！"
fi
if [ ! -d $supergraph_folder ]; then
    mkdir $supergraph_folder
    echo "_supergraph_folder を作成しました！"
fi

# .DS_Storeが残ることがあるので削除
if [ -f "$csv_folder/.DS_Store" ]; then
    rm "$csv_folder/.DS_Store"
    echo ".DS_Store が存在したので削除しました"
fi
if [ -f "$plot_folder/.DS_Store" ]; then
    rm "$plot_folder/.DS_Store"
    echo ".DS_Store が存在したので削除しました"
fi

# フォルダが存在する場合、フォルダ内のファイル数をカウント
csv_file_count=$(ls -A $csv_folder | wc -l)
plot_file_count=$(ls -A $csv_folder | wc -l)

# ファイルが存在するかチェック
if [ $csv_file_count -gt 0 ] || [ $plot_file_count -gt 0 ]; then
    echo "フォルダ内にファイルがすでに存在しそう👀 確認してください!"
    parent_folder=$(dirname $csv_folder)
    open $parent_folder
else
    echo "最適化を始めます!!"
    cd ./java_dynamic_class/ocha/itolab/koala/batch/py4j
    python3 main.py
fi

## クラスファイルの確認用コマンド
# ls -R ./java_dynamic_class/ocha/itolab/koala/batch/py4j/


# 仮想環境閉じる
deactivate
