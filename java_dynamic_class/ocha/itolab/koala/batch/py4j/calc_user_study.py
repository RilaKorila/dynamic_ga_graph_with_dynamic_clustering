import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats


def draw_box_plot(
    df,
    score_columns,
    dataset_name,
    metric,
    color_start,
    title_head="Relative Comparison",
):
    # 検定結果を格納する辞書
    p_values = {}

    # Wilcoxon 符号付順位検定（中央値3と比較）
    for col in score_columns:
        data = df[col].to_numpy()
        stat, p = stats.wilcoxon(data - 3, alternative="greater")
        p_values[col] = p
        print(f"{col}: Wilcoxon stat={stat}, p-value={p}")

    # データをプロット用に縦持ちに変換（long format）
    df_long = df.melt(
        id_vars="Participants",
        value_vars=score_columns,
        var_name="Layout",
        value_name="Score",
    )

    # カラーパレット準備
    custom_palette = []
    for i in range(color_start, 15):
        if i < 5:
            custom_palette.append("#A8D5BA")
        elif i < 10:
            custom_palette.append("#FFF2B2")
        else:
            custom_palette.append("#AED9E0")

    # Figure定義
    fig, ax = plt.subplots(figsize=(8, 6))

    # violinplot描画
    sns.violinplot(data=df_long, x="Layout", y="Score", palette=custom_palette, ax=ax)

    # 有意水準を上に描画（p値が5%以下なら*マーク）
    for i, col in enumerate(score_columns):
        p = p_values[col]
        y = df[col].max() + 0.3  # y位置を調整
        if p < 0.001:
            mark = "***"
        elif p < 0.01:
            mark = "**"
        elif p < 0.05:
            mark = "*"
        else:
            mark = "n.s."  # not significant
        plt.text(i, y, mark, ha="center", va="bottom", fontsize=12)

    ax.set_ylim(-1, 7.5)
    plt.title(f"{title_head} Evaluation per Layout")
    plt.savefig(f"./violinplot_{dataset_name}_{metric}.png")


if __name__ == "__main__":
    # CSVの読み込み
    df = pd.read_csv(
        "/Users/ayana/vis/dynamic_ga_graph_with_dynamic_clustering/java_dynamic_class/ocha/itolab/koala/batch/py4j/cit.csv"
    )

    # Participants列は不要なので除外
    # score_columns = ['T1', 'T2', 'T3', 'T4', 'T5', 'C1', 'C2', 'C3', 'C4', 'C5', 'S1', 'S2', 'S3', 'S4', 'S5']

    score_columns = ["T1", "T2", "T3", "T4", "T5"]
    draw_box_plot(df, score_columns, "cit", "time", 0)

    score_columns = ["C1", "C2", "C3", "C4", "C5"]
    draw_box_plot(df, score_columns, "cit", "clutter", 5)

    score_columns = ["S1", "S2", "S3", "S4", "S5"]
    draw_box_plot(df, score_columns, "cit", "sprawl", 10)

    score_columns = [
        "T1_absolute",
        "T2_absolute",
        "T3_absolute",
        "T4_absolute",
        "T5_absolute",
    ]
    draw_box_plot(df, score_columns, "cit", "time_absolute", 0, "Absolute")

    # CSVの読み込み
    df = pd.read_csv(
        "/Users/ayana/vis/dynamic_ga_graph_with_dynamic_clustering/java_dynamic_class/ocha/itolab/koala/batch/py4j/facebook.csv"
    )

    # Participants列は不要なので除外
    # score_columns = ['T1', 'T2', 'T3', 'T4', 'T5', 'C1', 'C2', 'C3', 'C4', 'C5', 'S1', 'S2', 'S3', 'S4', 'S5']

    score_columns = ["T1", "T2", "T3", "T4", "T5"]
    draw_box_plot(df, score_columns, "facebook", "time", 0)

    score_columns = ["C1", "C2", "C3", "C4", "C5"]
    draw_box_plot(df, score_columns, "facebook", "clutter", 5)

    score_columns = ["S1", "S2", "S3", "S4", "S5"]
    draw_box_plot(df, score_columns, "facebook", "sprawl", 10)

    score_columns = [
        "T1_absolute",
        "T2_absolute",
        "T3_absolute",
        "T4_absolute",
        "T5_absolute",
    ]
    draw_box_plot(df, score_columns, "facebook", "time_absolute", 0, "Absolute")
