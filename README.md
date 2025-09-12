# Dynamic GA Graph with Dynamic Clustering

動的グラフの多目的最適化によるレイアウト生成システム

## 概要

このプロジェクトは、時系列で変化するグラフに対して、NSGA-II遺伝的アルゴリズムを用いて多目的最適化を行い、美しいレイアウトを生成するシステムです。

### 主な機能

- **動的グラフ処理**: 時系列で変化するグラフデータの処理
- **多目的最適化**: NSGA-IIによる3つの目的関数の同時最適化
  - Sprawl（広がり度）
  - Clutter（ノード重なりペナルティ）
  - Time Smoothness（時間的滑らかさ）
- **可視化**: 散布図、箱ひげ図、ハイパーボリューム進化の可視化
- **ベースライン比較**: SuperGraph手法との比較評価

## プロジェクト構造

```
dynamic_ga_graph_with_dynamic_clustering/
├── java_dynamic_class/          # Java実装（評価関数、グラフ処理）
│   └── ocha/itolab/koala/batch/py4j/
│       ├── nsga2.py            # NSGA-II実装
│       ├── show_scatter_plot.py # 散布図生成
│       ├── calc_hypervolum.py   # ハイパーボリューム計算・可視化
│       └── data_process/        # データ処理モジュール
├── baseline/                    # ベースライン手法
│   ├── baseline_motif.py       # SuperGraph手法実装
│   └── evaluate_baseline_motif.py # ベースライン評価
├── data/                       # データセット
│   ├── Cit-HepPh/             # Cit-HepPhデータセット
│   └── NBAF_coauthors/        # NBAF共著者データセット
├── Koala-manygen/             # Java実装（レガシー）
└── _plot_result/             # 実験結果出力
```

## 環境構築

### 1. 定数ファイルの設定

#### Python定数ファイル
`java_dynamic_class/ocha/itolab/koala/batch/py4j/constants.py`を作成：

```python
JAR_PATH = "{プロジェクトルート}/dynamic_ga_graph_with_dynamic_clustering/test/share/py4j/py4j0.10.9.5.jar"
CLASS_PATH = "{プロジェクトルート}/dynamic_ga_graph_with_dynamic_clustering/java_dynamic_class"
PNG_PATH = "{プロジェクトルート}/dynamic_ga_graph_with_dynamic_clustering/_plot_result/"
SUPERGRAPH_PNG_PATH = "{プロジェクトルート}/dynamic_ga_graph_with_dynamic_clustering/_supergraph_result/"
NBAF_COAUTHORS_CSV_PATH = "{プロジェクトルート}/dynamic_ga_graph_with_dynamic_clustering/Koala-manygen/NBAF_Coauthorship_12dim.csv"
CIT_HEP_PH_DIR_PATH = "{プロジェクトルート}/dynamic_ga_graph_with_dynamic_clustering/data/Cit-HepPh/"
NBAF_COAUTHORS_DIR_PATH = "{プロジェクトルート}/dynamic_ga_graph_with_dynamic_clustering/data/NBAF_coauthors/"
```

#### Java定数ファイル
`Koala-manygen/src/ocha/itolab/koala/constants/Dataset.java`を作成：

※ {プロジェクトルート}は、実際のプロジェクトのルートディレクトリの絶対パスに置き換える。
(coms/配下は、DynaMoの実行結果をこのフォルダに配置する。)

```java
package ocha.itolab.koala.constants;

public enum Dataset {
    CIT_HEP_PH(
            "{プロジェクトルート}/data/Cit-HepPh/",
            "{プロジェクトルート}/data/Cit-HepPh/filtered_coms/",
            "Cit-HepPh"),
    NBAF_COAUTHORS(
            "{プロジェクトルート}/data/NBAF_coauthors/",
            "{プロジェクトルート}/data/NBAF_coauthors/filtered_coms/",
            "NBAF_coauthors");

    private String dataDirPath;
    private String comsPath;
    private String name;

    Dataset(final String dataDirPath, final String comsPath, final String name) {
        this.dataDirPath = dataDirPath;
        this.comsPath = comsPath;
        this.name = name;
    }

    public String getDataDirPath() { return this.dataDirPath; }
    public String getComsPath() { return this.comsPath; }
    public String getName() { return this.name; }
}
```

### 2. Java環境の準備


```bash
# Javaファイルのコンパイル
sh compile_java.sh # Windows の場合は、compile_java.shの中身をコロンではなく、セミコロンに変えること
```




### 3. Python環境の準備

```bash
# 仮想環境の作成と有効化
python -m venv env
source env/bin/activate  # Linux/Mac
# env\Scripts\activate   # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

## 使用方法

### 1. メイン実験の実行

```bash
# 動的グラフの多目的最適化を実行
sh run.sh
```

### 2. 結果の可視化

#### 散布図の生成
```bash
sh show_fitness_scatters.sh

```

#### ハイパーボリューム進化の可視化
```bash
python java_dynamic_class/ocha/itolab/koala/batch/py4j/calc_hypervolum.py
```

#### ベースライン比較（箱ひげ図）
```bash
python baseline/evaluate_baseline_motif.py
```

### 3. レイアウトのHTML出力

```bash
# CSVファイルをHTMLに変換
sh export_as_html.sh
```

## 主要コンポーネント

### NSGA-II実装 (`nsga2.py`)

- **多目的最適化**: 3つの目的関数の同時最適化
- **遺伝的操作**: 交叉、突然変異、選択の実装
- **動的レイアウト**: 前時刻のレイアウト情報を活用した時間的連続性の保持

### 評価関数

1. **Sprawl**: グラフの広がり度（小さい方が良い）
2. **Clutter**: ノード間の重なりペナルティ（小さい方が良い）
3. **Time Smoothness**: 時間的滑らかさ（小さい方が良い）

### 可視化ツール

- **散布図**: 目的関数間の関係を可視化
- **箱ひげ図**: 複数手法の比較評価
- **ハイパーボリューム**: 多目的最適化の進化を追跡

## 実験設定

### パラメータ

- **個体数**: 20
- **世代数**: 40
- **交叉率**: 0.9
- **座標範囲**: -10.0 ～ 10.0

### データセット

- **Cit-HepPh**: 物理学論文の引用ネットワーク
- **NBAF_coauthors**: 共著者ネットワーク

## 出力ファイル

- `_csv_result/`: 実験結果（レイアウトCSV）
- `_plot_result/`: 実験結果（PNG、各種統計情報）

- `_supergraph_result/`: SuperGraph手法の結果
- `boxplots_out/`: 箱ひげ図


## トラブルシューティング

### ハイパーボリュームが0になる問題

- **原因**: 参照点の設定が不適切
- **解決策**: `nsga2.py`の`self.ref_hv`を固定値に設定





### Python依存関係エラー

```bash
# 個別インストール
pip install deap py4j numpy matplotlib pandas networkx
```

## 技術詳細

### 遺伝子操作

- **交叉**: `tools.cxSimulatedBinaryBounded` - NSGA-II準拠の実数値交叉 ([source](https://deap.readthedocs.io/en/master/_modules/deap/tools/crossover.
html#cxSimulatedBinaryBounded))
- **突然変異**: `tools.mutPolynomialBounded` - 多項式突然変異 ([source](https://deap.readthedocs.io/en/master/_modules/deap/tools/mutation.html#mutPolynomialBounded))
- **選択**: `tools.selNSGA2` - NSGA-IIの非支配ソート選択 ([source](https://deap.readthedocs.io/en/master/_modules/deap/tools/emo.html#selNSGA2))

### 評価関数の実装

- **Java実装**: 高速なグラフ処理と評価計算
- **Python連携**: Py4JによるJava-Python連携

### データ形式

- **入力**: TSV形式のエッジリスト
- **出力**: CSV形式の座標データ
- **可視化**: PNG、HTML形式

## 参考資料

- [DEAPライブラリ](https://dse-souken.com/2021/05/25/ai-19/)
- [Py4J - Java Python連携](https://qiita.com/riverwell/items/e90cbbfdac439e6e9d30)
- [NSGA-IIアルゴリズム](https://ieeexplore.ieee.org/document/996017)



