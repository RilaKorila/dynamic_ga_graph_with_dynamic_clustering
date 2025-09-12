# style_anim_out/metanode_coordinates_n.csv ファイルを読み込む
import pandas as pd
import math, random, os
from typing import Dict, Optional


class Metanode:
    def __init__(self, df):
        self.x = df["x"]
        self.y = df["y"]
        self.radius = df["draw_radius"]


## Sprawlを計算（JavaのSprawlterEvaluator.calcSprawlを参考）
def calc_sprawl(df):
    """
    JavaのSprawlterEvaluator.calcSprawlを参考にした実装
    """
    zoom = 500.0
    node_area = 2.0 * 2.0 * math.pi  # Javaのnode_areaに対応

    minx = miny = float("inf")
    maxx = maxy = float("-inf")

    # 各metanodeの境界を計算
    for _, row in df.iterrows():
        x, y, r = row["x"], row["y"], row["draw_radius"]
        if r == 0:
            continue
        x1 = (x - r) * zoom
        x2 = (x + r) * zoom
        y1 = (y - r) * zoom
        y2 = (y + r) * zoom

        minx = min(minx, x1, x2)
        miny = min(miny, y1, y2)
        maxx = max(maxx, x1, x2)
        maxy = max(maxy, y1, y2)

    # sprawl = (maxx - minx) * (maxy - miny) / (ノード数 * node_area)
    drawing_area = (maxx - minx) * (maxy - miny)
    total_node_area = len(df) * node_area

    return drawing_area / total_node_area if total_node_area > 0 else 0.0


## Node-Node重なりペナルティを計算
def calc_node_node_penalty(df):
    """
    JavaのSprawlterEvaluator.calcNodeNodePenaltyを参考にした実装
    """
    penalty = 0.0

    for i in range(len(df)):
        for j in range(i + 1, len(df)):
            row1, row2 = df.iloc[i], df.iloc[j]
            if row1["draw_radius"] == 0 or row2["draw_radius"] == 0:
                continue
            x1, y1, r1 = row1["x"], row1["y"], row1["draw_radius"]
            x2, y2, r2 = row2["x"], row2["y"], row2["draw_radius"]

            # 円の中心間距離
            dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

            # 重なりがない場合はスキップ
            if (r1 + r2) < dist:
                continue

            # 一方の円が他方を完全に含む場合
            diffr = abs(r1 - r2)
            if dist < diffr:
                p0 = math.sqrt(min(r1, r2) ** 2 * math.pi)
            else:
                # 部分的重なりの場合
                cos1 = (dist**2 + r1**2 - r2**2) / (2 * dist * r1)
                cos2 = (dist**2 + r2**2 - r1**2) / (2 * dist * r2)

                # 重なり面積の計算
                p0 = (
                    r1**2 * math.acos(cos1)
                    + r2**2 * math.acos(cos2)
                    - 0.5
                    * math.sqrt(4 * dist**2 * r1**2 - (dist**2 + r1**2 - r2**2) ** 2)
                )

            penalty += p0

    return penalty


## Node-Edge重なりペナルティを計算
def calc_node_edge_penalty(df, edges_df):
    """
    JavaのSprawlterEvaluator.calcNodeEdgePenaltyを参考にした実装
    """
    penalty = 0.0

    # 各エッジについて
    for _, edge in edges_df.iterrows():
        # エッジの両端の座標
        ex1, ey1 = edge["x1"], edge["y1"]
        ex2, ey2 = edge["x2"], edge["y2"]

        # エッジの方程式: ax + by + c = 0
        ea = ex2 - ex1
        eb = ey2 - ey1
        ec = -(ea * ex1 + eb * ey1)

        # 各metanodeについて
        for _, node in df.iterrows():
            cx, cy, r = node["x"], node["y"], node["draw_radius"]
            if r == 0:
                continue

            # 点と直線の距離
            D = abs(ea * cx + eb * cy + ec)
            eab = ea**2 + eb**2

            if eab == 0:
                continue

            det = eab * r**2 - D**2
            if det <= 0:
                continue

            det = math.sqrt(det)

            # 円と直線の交点
            cx1 = cx + (ea * D - eb * det) / eab
            cy1 = cy + (eb * D + ea * det) / eab
            cx2 = cx + (ea * D + eb * det) / eab
            cy2 = cy + (eb * D - ea * det) / eab

            # 交点がエッジの範囲外の場合はスキップ
            if (cx1 > max(ex1, ex2) and cx2 > max(ex1, ex2)) or (
                cx1 < min(ex1, ex2) and cx2 < min(ex1, ex2)
            ):
                continue

            # 重なり部分の長さ
            len_overlap = math.sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2)
            penalty += len_overlap

    return penalty


## Edge-Edge重なりペナルティを計算
def calc_edge_edge_penalty(edges_df):
    """
    JavaのSprawlterEvaluator.calcEdgeEdgePenaltyを参考にした実装
    """
    PENALTY_CONST = 1.0
    penalty = 0.0

    for i in range(len(edges_df)):
        for j in range(i + 1, len(edges_df)):
            edge1, edge2 = edges_df.iloc[i], edges_df.iloc[j]
            if edge1["draw_radius"] == 0 or edge2["draw_radius"] == 0:
                continue
            # エッジ1の座標
            x11, y11 = edge1["x1"], edge1["y1"]
            x12, y12 = edge1["x2"], edge1["y2"]
            x1v, y1v = x12 - x11, y12 - y11
            len1 = math.sqrt(x1v**2 + y1v**2)

            if len1 < 1e-8:
                continue

            # エッジ2の座標
            x21, y21 = edge2["x1"], edge2["y1"]
            x22, y22 = edge2["x2"], edge2["y2"]
            x2v, y2v = x22 - x21, y22 - y21
            len2 = math.sqrt(x2v**2 + y2v**2)

            if len2 < 1e-8:
                continue

            # エッジの交差判定
            if not check_edge_crossing(x11, y11, x12, y12, x21, y21, x22, y22):
                continue

            # 内積によるペナルティ計算
            inner = abs(x1v * x2v + y1v * y2v) / (len1 * len2) + PENALTY_CONST
            penalty += inner

    return penalty


def check_edge_crossing(x11, y11, x12, y12, x21, y21, x22, y22):
    """
    2つの線分が交差しているかを判定
    """

    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    A, B = (x11, y11), (x12, y12)
    C, D = (x21, y21), (x22, y22)

    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)


## Time Smoothnessを計算
def calc_time_smoothness(df_prev, df_curr, similar_communities=None):
    """
    JavaのTimeSmoothnessEvaluatorを参考にした実装
    """
    total_distance = 0.0

    if similar_communities is None:
        # 単純な1対1マッピング
        for i in range(min(len(df_prev), len(df_curr))):
            x1, y1 = df_prev.iloc[i]["x"], df_prev.iloc[i]["y"]
            x2, y2 = df_curr.iloc[i]["x"], df_curr.iloc[i]["y"]
            node_count = df_curr.iloc[i]["node_count"]

            distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
            penalty = distance * node_count
            total_distance += penalty
    else:
        # 類似コミュニティマッピングを使用
        for curr_id, similarities in similar_communities.items():
            for prev_id, similarity in similarities:
                if curr_id < len(df_curr) and prev_id < len(df_prev):
                    x1, y1 = df_prev.iloc[prev_id]["x"], df_prev.iloc[prev_id]["y"]
                    x2, y2 = df_curr.iloc[curr_id]["x"], df_curr.iloc[curr_id]["y"]
                    node_count = df_curr.iloc[curr_id]["node_count"]

                    distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                    penalty = distance * node_count * similarity
                    total_distance += penalty

    return total_distance


## メイン評価関数
def evaluate_baseline_motif(
    metanode_file: str,
    prev_metanode_file: Optional[str] = None,
    edges_file: Optional[str] = None,
) -> Dict[str, float]:
    """
    baseline motifの評価を実行
    """
    df = pd.read_csv(metanode_file)

    results = {}

    # Sprawl計算
    results["sprawl"] = calc_sprawl(df)

    # Node-Node重なりペナルティ
    results["node_node_penalty"] = calc_node_node_penalty(df)

    # Edge関連のペナルティ（エッジファイルが提供されている場合）
    if edges_file:
        edges_df = pd.read_csv(edges_file)
        results["node_edge_penalty"] = calc_node_edge_penalty(df, edges_df)
        results["edge_edge_penalty"] = calc_edge_edge_penalty(edges_df)

    # Time Smoothness（前時刻のファイルが提供されている場合）
    if prev_metanode_file:
        df_prev = pd.read_csv(prev_metanode_file)
        results["time_smoothness"] = calc_time_smoothness(df_prev, df)

    return results


def load_layout_csv(file_path: str) -> pd.DataFrame:
    # x, y, draw_radiusの列を取得

    # #clustersの文字が出てくるまではスキップ
    is_clusters_info = False
    is_cluster_info_line = True
    data_rows = []  # リストでデータを蓄積
    with open(file_path, "r") as f:
        for line in f:
            if "#clusters" in line:
                is_clusters_info = True
            elif is_clusters_info:
                # clusetesの行以降のデータを取得
                if is_cluster_info_line:
                    is_cluster_info_line = False
                    # dfに追加
                    info = line.split(",")
                    id = info[0]
                    x = float(info[1])
                    y = float(info[2])
                    draw_radius = float(info[3])
                else:
                    is_cluster_info_line = True
                    node_count = len(line.split(",")[1:])
                    data_rows.append(
                        {
                            "id": id,
                            "x": x,
                            "y": y,
                            "draw_radius": draw_radius,
                            "node_count": node_count,
                        }
                    )
                    continue
            else:
                continue

    # 最後に一度だけDataFrameを作成
    df = pd.DataFrame(data_rows)
    return df


# 使用例
# boxplot_dynamic_layouts.py
# -----------------------------------------------------------
# 各 timestamp で 3手法 × 5回 の評価値を集め、
# 指標ごと（node_node_penalty / sprawl / time_smoothness）に
# 1枚の図にまとめて箱ひげ図を作成します。
# -----------------------------------------------------------

import os
from typing import Dict, List, Tuple, Optional
import pandas as pd
import matplotlib.pyplot as plt


# ====== 入力設定（必要に応じて調整） ======
# 例）timestamps = list(range(5, 17))
# timestamps = [i for i in range(5, 17)]  # サンプル。複数使うなら [5,6,...,16] のように。
timestamps = [i for i in range(2, 5)]  # SGのデータはtimestamp 2から始まる

# SG（baseline）の 5回分の出力場所テンプレート（あなたの例に合わせています）
#   style_anim_out1回目/metanode_coordinates_{t}.csv
#   style_anim_out1回目/metanode_coordinates_{t-1}.csv
SG_DIR_TEMPLATE = "style_anim_out{run_index}回目"  # run_index: 1..5
SG_FILE_TEMPLATE_CURR = "metanode_coordinates_{t}.csv"
SG_FILE_TEMPLATE_PREV = "metanode_coordinates_{tprev}.csv"

# OUR/INIT の CSV 出力（あなたのパスに合わせる）
# 例：
#   /Users/ayana/Desktop/.../_csv_result/{t}/layout{generation}-{id}.csv
#   /Users/ayana/Desktop/.../_csv_result/{t-1}/previous_layout{generation}-{id}.csv
OUR_BASE = "/Users/ayana/Desktop/Cit4/_csv_result"
INIT_BASE = "/Users/ayana/Desktop/Cit_ST"

# OUR/INIT で評価する gene/id の候補（5回ぶん）
OUR_CASES: List[Tuple[int, int]] = [
    (19, 7),
    (19, 8),
    (19, 9),
    (19, 10),
    (19, 11),
    (19, 3),
    (19, 1),
    (19, 14),
    (19, 15),
    (19, 16),
]  # (generation, id)
INIT_CASES: List[Tuple[int, int]] = [
    (0, 7),
    (0, 8),
    (0, 9),
    (0, 10),
    (0, 11),
    (0, 3),
    (0, 1),
    (0, 14),
    (0, 15),
    (0, 16),
]  # ランダム初期など想定

# 出力先
OUT_DIR = "boxplots_out"
os.makedirs(OUT_DIR, exist_ok=True)

# ====== 収集ヘルパ ======


def _safe_exists(path: str) -> bool:
    return path and os.path.exists(path)  # type: ignore


def collect_sg_metrics(timestamps: List[int], runs: List[int]) -> List[Dict]:
    """
    SG（baseline）: evaluate_baseline_motif(curr_csv, prev_csv) を呼び出して辞書を返す想定。
    """
    rows = []
    for t in timestamps:
        tprev = t - 1
        for r in runs:
            d = SG_DIR_TEMPLATE.format(run_index=r)
            curr = os.path.join(d, SG_FILE_TEMPLATE_CURR.format(t=t))
            prev = os.path.join(d, SG_FILE_TEMPLATE_PREV.format(tprev=tprev))
            if not (_safe_exists(curr) and _safe_exists(prev)):
                # 見つからない場合はスキップ
                print(f"[SG] missing: {curr} or {prev}")
                continue
            res = evaluate_baseline_motif(
                curr, prev
            )  # -> dict: {node_node_penalty, sprawl, time_smoothness, ...}
            rows.append(
                {
                    "method": "SG",
                    "timestamp": t,
                    "run": r,
                    "node_node_penalty": res.get("node_node_penalty"),
                    "sprawl": res.get("sprawl"),
                    "time_smoothness": res.get("time_smoothness"),
                }
            )
    return rows


def _calc_our_like_once(
    base_dir: str,
    t: int,
    generation: int,
    _id: int,
    is_init: bool = False,
    is_first_timestamp: bool = False,
) -> Optional[Dict]:
    """
    OUR / INIT 共通：レイアウトCSV2枚（curr/prev）から3指標を計算。
    """
    curr = os.path.join(base_dir, f"{t}", f"layout{generation}-{_id}.csv")

    if is_init:
        # ST用のデータは previous がつかない
        prev = os.path.join(base_dir, f"{t-1}", f"layout{generation}-{_id}.csv")
    else:
        prev = os.path.join(
            base_dir, f"{t-1}", f"previous_layout{generation}-{_id}.csv"
        )
    curr_df = load_layout_csv(curr)
    if not is_first_timestamp:
        prev_df = load_layout_csv(prev)
        time_smoothness = calc_time_smoothness(prev_df, curr_df)
    else:
        time_smoothness = 0.0

    return {
        "node_node_penalty": calc_node_node_penalty(curr_df),
        "sprawl": calc_sprawl(curr_df),
        "time_smoothness": time_smoothness,
    }


def collect_our_metrics(
    timestamps: List[int], cases: List[Tuple[int, int]]
) -> List[Dict]:
    rows = []
    for t in timestamps:
        is_first_timestamp = t == timestamps[0]
        for idx, (gen, _id) in enumerate(cases, start=1):
            res = _calc_our_like_once(
                OUR_BASE,
                t,
                gen,
                _id,
                is_init=False,
                is_first_timestamp=is_first_timestamp,
            )
            if res is None:
                # print(f"[OUR] missing: t={t}, gen={gen}, id={_id}")
                continue
            rows.append({"method": "OUR", "timestamp": t, "run": idx, **res})
    return rows


def collect_init_metrics(
    timestamps: List[int], cases: List[Tuple[int, int]]
) -> List[Dict]:
    rows = []
    for t in timestamps:
        is_first_timestamp = t == timestamps[0]
        for idx, (gen, _id) in enumerate(cases, start=1):
            res = _calc_our_like_once(
                INIT_BASE,
                t,
                gen,
                _id,
                is_init=True,
                is_first_timestamp=is_first_timestamp,
            )
            if res is None:
                # print(f"[INIT] missing: t={t}, gen={gen}, id={_id}")
                continue
            rows.append({"method": "ST", "timestamp": t, "run": idx, **res})
    return rows


# ====== 可視化（箱ひげ） ======


def boxplot_one_metric(df: pd.DataFrame, metric: str, out_path: str):
    """
    1枚の図に、X=timestamp、各timestampに 3手法(SG/OUR/INIT) の箱ひげを横並びに描く。
    """
    methods = ["OUR", "ST", "SG"]
    ts_list = sorted(df["timestamp"].unique().tolist())
    groups = []  # 各箱に入る値配列
    positions = []  # 箱のX位置
    pos = 1.0  # x開始位置
    gap_between_methods = 0.1
    gap_between_timestamps = 0.4

    xtick_positions = []
    xtick_labels = []

    for t in ts_list:
        # timestamp t の3手法
        for m_idx, m in enumerate(methods):
            vals = (
                df[(df["timestamp"] == t) & (df["method"] == m)][metric].dropna().values
            )
            # 箱に入れる値が1個でも描ける（5個想定）
            groups.append(vals)
            positions.append(pos + m_idx * gap_between_methods)
        # xtick は3箱の中央
        center = pos + gap_between_methods
        xtick_positions.append(center)
        xtick_labels.append(str(t))
        pos += gap_between_timestamps  # 次のtimestampへ

    fig, ax = plt.subplots(figsize=(max(6, len(ts_list) * 2.2), 5))
    bp = ax.boxplot(
        groups, positions=positions, widths=0.08, patch_artist=True, manage_ticks=False
    )

    # 色（手法ごとに固定色）
    method_colors = {"SG": "#4C78A8", "OUR": "#F58518", "ST": "#54A24B"}
    for i, patch in enumerate(bp["boxes"]):
        # i から手法を逆算
        method_index = i % len(methods)
        m = methods[method_index]
        patch.set_facecolor(method_colors.get(m, "#999999"))
        patch.set_alpha(0.9)
        patch.set_edgecolor("#333333")
    for whisker in bp["whiskers"]:
        whisker.set_color("#333333")
    for cap in bp["caps"]:
        cap.set_color("#333333")
    for median in bp["medians"]:
        median.set_color("#222222")
        median.set_linewidth(0.9)

    # 軸まわり
    ax.set_xlabel("Timestamp", fontsize=14)
    ax.set_xticks(xtick_positions)
    ax.set_xticklabels(xtick_labels)

    # 縦グリッド（読みやすさ）
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)

    # 凡例（ダミーで作成）
    handles = [plt.Line2D([0], [0], color=method_colors[m], lw=8) for m in methods]
    ax.legend(
        handles,
        methods,
        title="Method",
        frameon=False,
        loc="best",
        title_fontsize=16,
        fontsize=14,
    )

    titles = {
        "node_node_penalty": "Node-Node Penalty",
        "sprawl": "Sprawl",
        "time_smoothness": "Time Smoothness",
    }
    ax.set_title(f"{titles[metric]}", fontsize=20)

    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def main():
    # ---- データ収集 ----
    our_rows = collect_our_metrics(timestamps, cases=OUR_CASES)
    init_rows = collect_init_metrics(timestamps, cases=INIT_CASES)
    sg_rows = collect_sg_metrics(timestamps, runs=[i for i in range(1, 11)])

    rows = sg_rows + our_rows + init_rows
    if not rows:
        raise SystemExit(
            "データが1件も収集できませんでした。パス設定を見直してください。"
        )

    df = pd.DataFrame(rows)
    # print(df.head())

    # ---- 指標ごとに 1枚 ----
    metrics = ["node_node_penalty", "sprawl", "time_smoothness"]
    for metric in metrics:
        out_path = os.path.join(OUT_DIR, f"box_{metric}.png")

        boxplot_one_metric(df, metric, out_path)
        print(f"[saved] {out_path}")


if __name__ == "__main__":
    main()
