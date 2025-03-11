#!/bin/zsh

# 環境を起動
source test/bin/activate

# ライブラリの並び替え
isort ./java_dynamic_class/ocha/itolab/koala/batch/py4j/*.py
isort ./*.py

# フォーマット
black ./java_dynamic_class/ocha/itolab/koala/batch/py4j/*.py
black ./*.py

# 環境を閉じる
deactivate
