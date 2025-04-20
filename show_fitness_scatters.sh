#!/bin/bash

## 出力するtimestampを指定
echo "どのtimestampをhtmlに変換する?? : "
read target_timestamp # 標準入力を変数に格納

TXT_FILE="${target_timestamp}/fitness.txt"
OUTPUT_DIR="${target_timestamp}"
PYTHON_SCRIPT="java_dynamic_class/ocha/itolab/koala/batch/py4j/show_scatter_plot.py"

# Pythonスクリプトを呼び出し（PYTHONPATHやvenvがあれば必要に応じて調整）
python3 "$PYTHON_SCRIPT" "$TXT_FILE" "$OUTPUT_DIR"
