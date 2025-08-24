# dynamic_ga_graph_with_dynamic_clustering

## 環境構築方法

### 定数を管理するファイルを作成

以下の 2 つのプログラムを、指定の場所に作成する

#### 1 つ目: Python ファイル

##### 作成場所

> java_dynamic_class/ocha/itolab/koala/batch/py4j/constants.py

##### テンプレートの追加・編集

```python
JAR_PATH = "{プロジェクトルート}/dynamic_ga_graph_with_dynamic_clustering/test/share/py4j/py4j0.10.9.5.jar"
CLASS_PATH = "{プロジェクトルート}/dynamic_ga_graph_with_dynamic_clustering/java_dynamic_class"
PNG_PATH = "{プロジェクトルート}/dynamic_ga_graph_with_dynamic_clustering/_plot_result/"
SUPERGRAPH_PNG_PATH = "{プロジェクトルート}/dynamic_ga_graph_with_dynamic_clustering/_supergraph_result/"
NBAF_COAUTHORS_CSV_PATH = "{プロジェクトルート}/dynamic_ga_graph_with_dynamic_clustering/Koala-manygen/NBAF_Coauthorship_12dim.csv"
CIT_HEP_PH_DIR_PATH = "{プロジェクトルート}/dynamic_ga_graph_with_dynamic_clustering/data/Cit-HepPh/"
NBAF_COAUTHORS_DIR_PATH = "{プロジェクトルート}/dynamic_ga_graph_with_dynamic_clustering/data/NBAF_coauthors/"
```

※ {プロジェクトルート}は、実際のプロジェクトのルートディレクトリの絶対パスに置き換える。

#### 2 つ目: Java ファイル

##### 作成場所

> Koala-manygen/src/ocha/itolab/koala/constants/Dataset.java

##### テンプレートの追加・編集

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

    public String getDataDirPath() {
        return this.dataDirPath;
    }

    public String getComsPath() {
        return this.comsPath;
    }

    public String getName() {
        return this.name;
    }
}
```

※ {プロジェクトルート}は、実際のプロジェクトのルートディレクトリの絶対パスに置き換える。
(coms/配下は、DynaMoの実行結果をこのフォルダに配置する。)

### Java の準備 (基本的に Mac かつ Eclipse 入れてない場合)

1. ターミナルで `sh compile_java.sh` を実行。Java ファイルをことごとくコンパイル。(**ただし、Windows の場合は、コロンではなく、セミコロンに変えること**)。また、Eclipse でまとめてコンパイルできるなら、省略できるプロセスかも...?
1. Java の設定は OK なはずなので、次は Python の準備へ

### Python の準備

1. Python をインストール
1. 仮想環境を構築。環境名は**env**とする[詳細な方法はこちら](https://qiita.com/fiftystorm36/items/b2fd47cf32c7694adc2e) 。
1. (初回のみ) 仮想環境を起動。`ga-graph`のフォルダにて、以下のコマンドを実行
   > source env/bin/activate
1. `pip install -r requirement.txt`で必要なライブラリをインストール。もしエラーが出たら必要なものを 1 つづつ入れる(deap, py4j, numpy, matplotlib)

## 実験手順

1. 環境が整ったら、ターミナルで`sh run.sh`実行

1. 実験後は、ターミナルで`sh export_as_html.sh`を実行し、任意の世代の csv ファイルを html に変換。(その前に csv_viewer のコード環境を作る必要がある)

---

以下、メモ

## Java 側の py4j の起動方法

javac でコンパイル

> javac -cp test/share/py4j/py4j0.10.9.5.jar AdditionApplication.java

実行

> java -cp test/share/py4j/py4j0.10.9.5.jar: AdditionApplication

-cp で classpath を指定している。linux の場合、実行の際には jar ファイル名の後に、**:コロン** が必要。Windoows の場合は、セミコロン。

### Windows 版コマンド

javac -cp ..\test\share\py4j\py4j0.10.9.5.jar;..\java_dynamic_class\ -d ..\java_dynamic_class\ -d ..\java_dynamic_class\ src\ocha\itolab\koala\core\data\*.java

- -d オプションが、class ファイルの格納場所を指定
- cp py4j の jar ファイルと他の class ファイルが入ったディレクトリを指定

## Java プログラムが実行できないとき

- ソースコード内で package を import 使用している時は、実行コマンドにもパッケージ名を追加. [参考](https://teratail.com/questions/53923)

## openGL のために必要なファイル

[こちら](https://jogamp.org/deployment/v2.3.2/jar/)か 4 つダウンロード

- gluegen-rt-natives-xxxx.jar
- gluegen-rt.jar
- jogl-all-natives-xxxx.jar
- jogl-all.jar

※ なお xxxx には「macosx-universal」「windows-i586」など自分の使っている OS に対応する単語が入る

## OpenGL のコンパイル

### 注意

Windows のパス名は \ ではなく、\\\ を使う

### 環境構築

- 必要な jar ファイルをダウンロード
- itolab scrapbox に従って Eclipse 環境を整える。
- 以下のサイトから必要な jar ファイルをダウンロードし、Eclipse の環境に加える
  - http://www.java2s.com/Code/Jar/g/Downloadgluegenrtnativeswindowsamd64jar.htm
  - http://www.java2s.com/Code/Jar/g/Downloadgluegenrtnativeswindowsamd64jar.htm
  - https://jar-download.com/artifacts/org.jogamp.jogl/jogl-all/2.3.2/source-code

### 実行方法

1. Eclipse 上でコンパイルし、ObjectFunction プログラムを実行(Java を起動)。Server Gateway Started! が表示されることを確認

1. class ファイルがあるディレクトリで、以下のコマンドを実行(Python を起動)

   > python main.py

   を実行。

# 参考資料

- Java と Python の橋渡し[URL](https://qiita.com/riverwell/items/e90cbbfdac439e6e9d30)
- [DEAP ライブラリ](https://dse-souken.com/2021/05/25/ai-19/)

---

## Aesthetic Evaluation

### 背景

- 描画結果の csv ファイルを読み込んで、見た目の評価をしたい
- 基礎計算になるので python ではなく java で実装
- 最適化ロジックとは切り離したいので別の階層で実行

## 遺伝子操作

以下の遺伝子操作について詳しい実装を調べる

- crossover(交叉): tools.cxSimulatedBinaryBounded ([source](https://deap.readthedocs.io/en/master/_modules/deap/tools/crossover.html#cxSimulatedBinaryBounded))
  - inputs: ind1, ind2, eta, low, up
  - return: ind1, ind2
  - original NSGA-II に似ている。と書いてある。同じではないらしい
  - 交叉：遺伝子の一部を交換すること. よって、ind1, ind2 を渡して、中身を一部交換した後に、返り値が ind1, ind2
- mutation: tools.mutPolynomialBounded ([source](https://deap.readthedocs.io/en/master/_modules/deap/tools/mutation.html#mutPolynomialBounded))
  - inputs: individual, eta, low, up, indpb
    - eta が大きいと親に似る. eta が小さいと全然違う個体ができる
  - return: individual,
    - 選ばれた遺伝子が書き換えられた状態の indivisuals を返す
  - original NSGA-II に実装されていたもの
  - 突然変異：ある遺伝子 individual が、一部変わる(親にはない遺伝情報を与える)。よって individual(単体)を受け取り、individual(単体)を返す
- select: tools.selNSGA2 ([source](https://deap.readthedocs.io/en/master/_modules/deap/tools/emo.html#selNSGA2))
  - inputs: individuals, k, nd='standard'
  - return: chosen_indivisuals (a list of selected individuals)
  - original NSGA-II に実装されていたもの
  - pop + offspring から pop の長さ分だけ取り出す、という処理を走らせていた

### 変えるなら

- mate(交叉)が NSGA-II 由来ではないので変えても良さそう
- mutation も、グラフにおいてもその操作が「似ている」のかは検討の余地あり


## グラフレイアウトの描画(csv ->  html)

シェルスクリプトにcsv_viewerの中のPythonファイルを呼び出し、csvファイル群をhtmlファイル群に書き換える

1. シェルスクリプト内の絶対パスを指定

2. sh export_html.shで実行

3. おそらく入力を求められるので0と入力してEnter
（ここでは、0世代目のレイアウト（layout0-0.csvからlayout0-19.csv）の情報をすべて可視化したいと想定）
