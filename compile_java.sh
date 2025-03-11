#!/bin/zsh

# 移動
cd Koala-manygen/

# 全部コンパイル
# 循環参照しているのでまとめてコンパイルする
javac -cp ../env/share/py4j/py4j0.10.9.5.jar:../java_dynamic_class/ -d ../java_dynamic_class/ \
    src/ocha/itolab/koala/constants/*.java \
    src/ocha/itolab/koala/core/data/*.java \
    src/ocha/itolab/koala/core/mesh/*.java \
    src/ocha/itolab/koala/core/forcedirected/*.java \
    src/ocha/itolab/koala/core/*.java \
    src/ocha/itolab/koala/evaluate/sprawlter/SprawlterEvaluator.java \
    src/ocha/itolab/koala/batch/py4j/*.java


# 戻る
cd ..

echo "コンパイルが完了しました🎉"
