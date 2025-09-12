# step9_dynamic_graph_viz.py
# ------------------------------------------------------------
# 動的グラフ（時系列のTSVエッジリスト）を入力として、
# super-graph / super-community / super-layout を1度だけ作成。
# 各時刻の community ごとに生成したパターン（chain/loop/clique/egocentric/undefined）
# について変化の視覚符号化を行い、補間フレームとGIFを出力します。
# ------------------------------------------------------------

from __future__ import annotations
import os
import re
import glob
import math
import argparse
import shutil
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Iterable, Optional

import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

# -------------- 共通ユーティリティ --------------


def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def natural_key(s: str) -> List:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


# -------------- データ読み込み（TSV：u \t v） --------------


def load_graphs_from_tsv_dir(
    dir_path: str, pattern: str = "*.tsv", make_undirected: bool = True
) -> List[Tuple[str, nx.Graph]]:
    paths = sorted(glob.glob(os.path.join(dir_path, pattern)), key=natural_key)
    graphs: List[Tuple[str, nx.Graph]] = []
    GType = nx.Graph if make_undirected else nx.DiGraph
    for p in paths:
        ts = os.path.splitext(os.path.basename(p))[0]
        G = GType()
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                u, v = parts[0], parts[1]
                if u == v:
                    continue
                G.add_edge(u, v)
        graphs.append((ts, G))
    return graphs


# -------------- Super-graph / Communities / Layout --------------

import community as community_louvain  # pip install python-louvain


@dataclass
class SuperGraphArtifacts:
    Gs: nx.Graph
    node_to_comm: Dict[str, int]
    comm_to_nodes: Dict[int, List[str]]
    comm_positions: Dict[int, Tuple[float, float]]
    meta_graph: nx.Graph


def build_supergraph(graphs: Iterable[Tuple[str, nx.Graph]]) -> nx.Graph:
    Gs = nx.Graph()
    for _, G in graphs:
        Gs.add_nodes_from(G.nodes())
        Gs.add_edges_from(G.edges())
    return Gs


def detect_super_communities(Gs: nx.Graph) -> Dict[str, int]:
    if community_louvain is not None and Gs.number_of_edges() > 0:
        part = community_louvain.best_partition(Gs)  # node -> community id
        return {str(n): int(c) for n, c in part.items()}
    # Fallback: 連結成分で代替
    node_to_comm: Dict[str, int] = {}
    for cid, comp in enumerate(nx.connected_components(Gs)):
        for n in comp:
            node_to_comm[str(n)] = cid
    return node_to_comm


def build_meta_graph(Gs: nx.Graph, node_to_comm: Dict[str, int]) -> nx.Graph:
    H = nx.Graph()
    for c in set(node_to_comm.values()):
        H.add_node(c, size=0)
    for n in Gs.nodes():
        c = node_to_comm[str(n)]
        H.nodes[c]["size"] = H.nodes[c].get("size", 0) + 1
    for u, v in Gs.edges():
        cu = node_to_comm[str(u)]
        cv = node_to_comm[str(v)]
        if cu == cv:
            continue
        w = H.get_edge_data(cu, cv, {}).get("weight", 0) + 1
        H.add_edge(cu, cv, weight=w)
    return H


def compute_super_layout(
    meta_graph: nx.Graph, seed: int = 42, k: Optional[float] = None
) -> Dict[int, Tuple[float, float]]:
    # ノード数に基づいてkパラメータを自動調整
    n_nodes = meta_graph.number_of_nodes()
    if k is None:
        k = max(2.0, math.sqrt(n_nodes) * 1.5)  # より大きな間隔を確保

    # スプリングレイアウトを計算
    pos = nx.spring_layout(
        meta_graph,
        seed=seed,
        k=k,
        weight="weight",
        iterations=500,  # より多くの反復で収束を改善
        threshold=1e-4,  # より厳密な収束条件
    )

    return {int(c): (float(x), float(y)) for c, (x, y) in pos.items()}


def build_supergraph_artifacts(
    graphs: List[Tuple[str, nx.Graph]], seed: int = 42
) -> SuperGraphArtifacts:
    Gs = build_supergraph(graphs)
    node_to_comm = detect_super_communities(Gs)
    comm_to_nodes: Dict[int, List[str]] = {}
    for n, c in node_to_comm.items():
        comm_to_nodes.setdefault(c, []).append(n)
    meta_graph = build_meta_graph(Gs, node_to_comm)
    comm_positions = compute_super_layout(meta_graph, seed=seed)
    return SuperGraphArtifacts(
        Gs, node_to_comm, comm_to_nodes, comm_positions, meta_graph
    )


# -------------- パターン判定（ルールベース） --------------


@dataclass
class PatternThresholds:
    cyc_ratio: float = 0.3  # 最大サイクル長 >= cyc_ratio*n → loop候補
    den_high: float = 0.5  # density >= 0.6 → clique
    den_low: float = 0.5  # density <= 0.4 → loop候補
    maxdeg_ratio: float = 0.5  # max_degree >= 0.6*n → egocentric
    depth_ratio: float = 0.4  # 擬似深さ >= 0.5*n → chain


def graph_density(G: nx.Graph) -> float:
    n = G.number_of_nodes()
    m = G.number_of_edges()
    if n <= 1:
        return 0.0
    return (2.0 * m) / (n * (n - 1))


def largest_cycle_size(G: nx.Graph) -> int:
    if G.number_of_edges() == 0 or G.number_of_nodes() == 0:
        return 0
    try:
        cycles = nx.cycle_basis(G.to_undirected())
        return max((len(c) for c in cycles), default=0)
    except Exception:
        return 0


def max_degree(G: nx.Graph) -> int:
    # G.degree() : Dict[str, int] (a DegreeView mapping nodes to their degree)
    return max((d for _, d in G.degree()), default=0)  # type: ignore


def pseudo_depth(G: nx.Graph) -> int:
    """最大偏心度（コンポーネント毎）を擬似深さとして採用。"""
    if G.number_of_nodes() == 0:
        return 0
    H = G.to_undirected()
    md = 0
    for comp_nodes in nx.connected_components(H):
        comp = H.subgraph(comp_nodes)
        if comp.number_of_nodes() == 1:
            md = max(md, 0)
            continue
        try:
            ecc = nx.eccentricity(comp)
            md = max(md, max(ecc.values()))
        except Exception:
            start = next(iter(comp.nodes()))
            lengths = nx.single_source_shortest_path_length(comp, start)
            md = max(md, max(lengths.values()))
    return md


@dataclass
class PatternResult:
    pattern: str
    n: int
    m: int
    density: float
    maxdeg: int
    depth: int
    largest_cycle: int
    scores: Dict[str, float] = field(default_factory=dict)


def match_pattern_rule_based(
    G: nx.Graph, thr: PatternThresholds = PatternThresholds()
) -> PatternResult:
    n = G.number_of_nodes()
    m = G.number_of_edges()
    if n == 0:
        return PatternResult("undefined", 0, 0, 0.0, 0, 0, 0)
    den = graph_density(G)
    mxdeg = max_degree(G)
    dep = pseudo_depth(G)
    cyc = largest_cycle_size(G)
    if den >= thr.den_high:
        pat = "clique"
    elif mxdeg >= math.ceil(thr.maxdeg_ratio * n):
        pat = "egocentric"
    elif (den <= thr.den_low) and (cyc >= math.ceil(thr.cyc_ratio * n)):
        pat = "loop"
    elif dep >= math.ceil(thr.depth_ratio * n):
        pat = "chain"
    else:
        pat = "undefined"
    return PatternResult(pat, n, m, den, mxdeg, dep, cyc)


# -------------- 時刻ごとのパーティション --------------


@dataclass
class TimeSlicePartition:
    timestamp: str
    comm_subgraphs: Dict[int, nx.Graph]
    comm_patterns: Dict[int, PatternResult]


def build_partition_for_time(
    timestamp: str, Gt: nx.Graph, artifacts: SuperGraphArtifacts
) -> TimeSlicePartition:
    comm_subgraphs: Dict[int, nx.Graph] = {}
    comm_patterns: Dict[int, PatternResult] = {}
    Vt = set(map(str, Gt.nodes()))
    for cid, nodes in artifacts.comm_to_nodes.items():
        nodes_t = list(Vt.intersection(nodes))
        if not nodes_t:
            continue
        subg = Gt.subgraph(nodes_t).copy()
        comm_subgraphs[cid] = subg
        comm_patterns[cid] = match_pattern_rule_based(subg)
    return TimeSlicePartition(timestamp, comm_subgraphs, comm_patterns)


# -------------- 8. 埋め込み（内側=前, 外側=今 のラベル） --------------


@dataclass
class EmbedViewItem:
    outer: str  # 現在パターン
    inner: Optional[str]  # 前時刻パターン（初回は None）


@dataclass
class EmbedView:
    timestamp: str
    comm_embed: Dict[int, EmbedViewItem]


def build_embed_views(slices: List[TimeSlicePartition]) -> List[EmbedView]:
    out: List[EmbedView] = []
    prev_patterns: Dict[int, str] = {}
    for sl in slices:
        item: Dict[int, EmbedViewItem] = {}
        for cid, pr in sl.comm_patterns.items():
            inner = prev_patterns.get(cid)
            item[cid] = EmbedViewItem(outer=pr.pattern, inner=inner)
        prev_patterns = {cid: pr.pattern for cid, pr in sl.comm_patterns.items()}
        out.append(EmbedView(sl.timestamp, item))
    return out


# -------------- パイプライン全体 --------------


@dataclass
class PipelineResult:
    artifacts: SuperGraphArtifacts
    slices: List[TimeSlicePartition]
    embed_views: List[EmbedView]


def run_pipeline_from_dir(
    dir_path: str, pattern: str = "*.tsv", seed: int = 42
) -> PipelineResult:
    graphs = load_graphs_from_tsv_dir(dir_path, pattern=pattern)
    if not graphs:
        raise RuntimeError(f"No TSV files in {dir_path=} matching {pattern=}")
    artifacts = build_supergraph_artifacts(graphs, seed=seed)
    slices: List[TimeSlicePartition] = []
    for ts, Gt in graphs:
        slices.append(build_partition_for_time(ts, Gt, artifacts))
    embed_views = build_embed_views(slices)
    return PipelineResult(artifacts, slices, embed_views)


# -------------- 9. 変化の視覚符号化（アニメ＆スタイル） --------------


# 五角形頂点（パターン形状を描くための基底）
def pentagon_points(k: int = 5, radius: float = 1.0, angle0: float = math.pi / 2.0):
    pts = []
    for i in range(k):
        ang = angle0 + 2 * math.pi * i / k
        pts.append((radius * math.cos(ang), radius * math.sin(ang)))
    return pts


PENTAGON = pentagon_points()


def pattern_edges(name: Optional[str]):
    """五角形上に描くエッジ集合でパターン形状を表現。"""
    if name == "chain":
        return [(0, 1), (1, 2), (2, 3), (3, 4)]
    if name == "loop":
        return [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
    if name == "clique":
        E = []
        for i in range(5):
            for j in range(i + 1, 5):
                E.append((i, j))
        return E
    if name == "egocentric":
        return [(0, 1), (0, 2), (0, 3), (0, 4)]
    return []


def classify_size_change(prev_n: int, curr_n: int) -> str:
    """拡大・縮小・出現・消滅を簡易判定。相対15%＋2ノード閾。"""
    if prev_n == 0 and curr_n > 0:
        return "appear"
    if prev_n > 0 and curr_n == 0:
        return "disappear"
    if prev_n == 0:
        return "stable"
    rel = (curr_n - prev_n) / max(1, prev_n)
    if rel > 0.15 and (curr_n - prev_n) >= 2:
        return "grow"
    if rel < -0.15 and (prev_n - curr_n) >= 2:
        return "shrink"
    return "stable"


def draw_transition_frame(
    ax,
    result: PipelineResult,
    i_from: int,
    t01: float,
    size_scale=(0.05, 0.15),
    edge_alpha=0.25,
) -> None:
    """
    連続する2時刻 i_from -> i_from+1 を t01 in [0,1] で線形補間して描画。
      - 出現/消滅: 半径0→r / r→0 補間
      - サイズ変化: 枠線スタイル（太実線=拡大/出現、細点線=縮小/消滅、細実線=不変）
      - 構造変化: 中央インジケータ（赤=変化あり, 緑=不変, 白=片側欠落）
      - パターン形状: 五角形上のエッジ集合をクロスフェード（prev α=1−t, next α=t）
    """
    artifacts = result.artifacts
    sl_prev = result.slices[i_from]
    sl_next = result.slices[i_from + 1]
    ev_prev = result.embed_views[i_from]
    ev_next = result.embed_views[i_from + 1]

    # サイズ正規化（全時刻での最大ノード数に対する平方根スケール）
    all_sizes = [
        sub.number_of_nodes()
        for s in result.slices
        for sub in s.comm_subgraphs.values()
    ]
    max_size = max(all_sizes) if all_sizes else 1

    # メタグラフ（コミュニティ間エッジ）
    weights = nx.get_edge_attributes(artifacts.meta_graph, "weight")
    wmax = max(weights.values()) if weights else 1
    for u, v, data in artifacts.meta_graph.edges(data=True):
        x1, y1 = artifacts.comm_positions[u]
        x2, y2 = artifacts.comm_positions[v]
        lw = 0.5 + 2.0 * (data.get("weight", 1) / max(1.0, wmax))
        ax.plot([x1, x2], [y1, y2], linewidth=lw, alpha=edge_alpha, color="gray")

    # 各コミュニティ（固定座標）でドーナツ＋インジケータ＋パターン形状
    pat_order = ["chain", "loop", "clique", "egocentric", "undefined"]

    def pat_color(p: Optional[str]) -> str:
        if p is None:
            return "white"
        idx = pat_order.index(p) if p in pat_order else len(pat_order) - 1
        return f"C{idx}"

    for cid, (x, y) in artifacts.comm_positions.items():
        sub_prev = sl_prev.comm_subgraphs.get(cid)
        sub_next = sl_next.comm_subgraphs.get(cid)
        n_prev = sub_prev.number_of_nodes() if sub_prev is not None else 0
        n_next = sub_next.number_of_nodes() if sub_next is not None else 0

        r0 = (
            size_scale[0]
            + (size_scale[1] - size_scale[0]) * math.sqrt(n_prev / max_size)
            if n_prev > 0
            else 0.0
        )
        r1 = (
            size_scale[0]
            + (size_scale[1] - size_scale[0]) * math.sqrt(n_next / max_size)
            if n_next > 0
            else 0.0
        )
        r = (1 - t01) * r0 + t01 * r1
        if r <= 0:
            continue  # このフレームでは見えない

        pat_prev = (
            ev_prev.comm_embed.get(cid).outer if cid in ev_prev.comm_embed else None  # type: ignore
        )
        pat_curr = (
            ev_next.comm_embed.get(cid).outer if cid in ev_next.comm_embed else None  # type: ignore
        )

        # 枠線スタイル（サイズ変化）
        change = classify_size_change(n_prev, n_next)
        if change in ("grow", "appear"):
            lw, ls = 1.8, "solid"
        elif change in ("shrink", "disappear"):
            lw, ls = 0.8, (0, (2, 2))  # 細点線
        else:
            lw, ls = 1.0, "solid"

        # 外側ドーナツの色（前半はprev色、後半はcurr色）
        facecolor = pat_color(pat_prev) if t01 < 0.5 else pat_color(pat_curr)
        outer = Circle(
            (x, y),
            r,
            facecolor=facecolor,
            edgecolor="black",
            linewidth=lw,
            linestyle=ls,
            alpha=0.95,
        )
        ax.add_patch(outer)

        # 中央インジケータ（構造変化）
        if (pat_prev is None) or (pat_curr is None):
            ind_color = "white"
        else:
            ind_color = "green" if pat_prev == pat_curr else "red"
        inner = Circle(
            (x, y),
            r * 0.35,
            facecolor=ind_color,
            edgecolor="black",
            linewidth=0.5,
            alpha=0.95,
        )
        ax.add_patch(inner)

        # 五角形上のパターン形状（クロスフェード）
        R = r * 0.55
        pts = [(x + R * px, y + R * py) for (px, py) in PENTAGON]
        E_prev = pattern_edges(pat_prev)
        E_next = pattern_edges(pat_curr)
        for a, b in E_prev:
            x1, y1 = pts[a]
            x2, y2 = pts[b]
            ax.plot([x1, x2], [y1, y2], linewidth=1.2, alpha=(1 - t01), color="gray")
        for a, b in E_next:
            x1, y1 = pts[a]
            x2, y2 = pts[b]
            ax.plot([x1, x2], [y1, y2], linewidth=1.2, alpha=t01, color="gray")

        # ID表示（小さく）
        ax.text(x, y, str(cid), ha="center", va="center", fontsize=6)


def save_coordinates(
    result: PipelineResult, out_dir: str, target_timestamp: str
) -> None:
    """
    メタノード（コミュニティ）の座標をCSVファイルに保存
    target_timestamp: 特定の時刻を指定（Noneの場合は全時刻の最大サイズで正規化）
    """
    import csv

    # 描画サイズの計算（draw_transition_frameと同じ計算式）
    size_scale = (0.05, 0.15)  # draw_transition_frameのデフォルト値

    # 特定の時刻でのサイズ正規化
    target_slice = None
    for slice in result.slices:
        if slice.timestamp == target_timestamp:
            target_slice = slice
            break

    if target_slice is None:
        raise ValueError(f"Timestamp {target_timestamp} not found in slices")

    # その時刻での最大ノード数
    target_sizes = [
        sub.number_of_nodes() for sub in target_slice.comm_subgraphs.values()
    ]
    max_size = max(target_sizes) if target_sizes else 1

    print(
        f"[INFO] Using timestamp {target_timestamp} for size normalization (max_size={max_size})"
    )

    # メタノード座標の保存
    coords_file = os.path.join(out_dir, f"metanode_coordinates_{target_timestamp}.csv")
    with open(coords_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metanode_id", "x", "y", "node_count", "draw_radius"])

        for cid, (x, y) in result.artifacts.comm_positions.items():
            # 特定の時刻でのノード数
            target_sub = target_slice.comm_subgraphs.get(cid)
            node_count = target_sub.number_of_nodes() if target_sub is not None else 0

            # 描画に使われる半径を計算
            draw_radius = (
                size_scale[0]
                + (size_scale[1] - size_scale[0]) * math.sqrt(node_count / max_size)
                if node_count > 0
                else 0.0
            )
            writer.writerow([cid, x, y, node_count, draw_radius])

    # ノードとコミュニティのマッピングの保存
    mapping_file = os.path.join(out_dir, f"node_to_community_{target_timestamp}.csv")
    with open(mapping_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "community_id"])

        for node_id, comm_id in result.artifacts.node_to_comm.items():
            writer.writerow([node_id, comm_id])

    # 個別ノード座標の保存（コミュニティ中心からの相対位置）
    node_coords_file = os.path.join(out_dir, f"node_coordinates_{target_timestamp}.csv")
    with open(node_coords_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "community_id", "community_x", "community_y"])

        for node_id, comm_id in result.artifacts.node_to_comm.items():
            comm_x, comm_y = result.artifacts.comm_positions[comm_id]
            writer.writerow([node_id, comm_id, comm_x, comm_y])


def render_step9_animation(
    result: PipelineResult, out_dir: str, steps: int = 6, dpi: int = 160
) -> Tuple[List[str], Optional[str]]:
    """
    連続する全時刻区間について、補間フレームを生成しPNG保存。
    可能ならGIFも生成（imageio 必要）。
    """
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    ensure_dir(out_dir)

    frame_paths: List[str] = []

    # 最初のtimestampの座標を保存
    if result.slices:
        save_coordinates(result, out_dir, result.slices[0].timestamp)

    for i in range(len(result.slices) - 1):
        t_from = result.slices[i].timestamp
        t_to = result.slices[i + 1].timestamp
        for s in range(steps + 1):
            t01 = s / steps
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.set_aspect("equal")
            ax.axis("off")
            ax.set_title(f"{t_from} → {t_to}   (t={t01:.2f})")

            draw_transition_frame(ax, result, i, t01)

            # ビューボックス調整
            xs = [p[0] for p in result.artifacts.comm_positions.values()]
            ys = [p[1] for p in result.artifacts.comm_positions.values()]
            if xs and ys:
                pad = 0.25
                ax.set_xlim(min(xs) - pad, max(xs) + pad)
                ax.set_ylim(min(ys) - pad, max(ys) + pad)

            out_path = os.path.join(out_dir, f"trans_{i}_{s:02d}.png")
            fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
            plt.close(fig)
            frame_paths.append(out_path)

            # 座標を保存
            save_coordinates(result, out_dir, t_to)

    # GIF化（任意）
    gif_path = None
    try:
        import imageio.v2 as imageio

        imgs = [imageio.imread(p) for p in frame_paths]
        gif_path = os.path.join(out_dir, "step9_animation.gif")
        imageio.mimsave(gif_path, imgs, duration=0.6)  # type: ignore # 1フレーム ~0.6秒
    except Exception:
        pass

    return frame_paths, gif_path


# -------------- CLI --------------


def main():
    parser = argparse.ArgumentParser(
        description="Step-9 dynamic visualization (変化の視覚符号化)"
    )
    parser.add_argument(
        "--data", type=str, default=None, help="TSVディレクトリ（u\\tv）"
    )
    parser.add_argument(
        "--pattern", type=str, default="*.tsv", help="ファイルパターン（既定：*.tsv）"
    )
    parser.add_argument(
        "--out", type=str, default="./style_anim_out", help="出力ディレクトリ"
    )
    parser.add_argument("--seed", type=int, default=7, help="super-layout 用 seed")
    parser.add_argument(
        "--steps", type=int, default=6, help="補間フレーム数（区間あたり）"
    )
    args = parser.parse_args()

    data_dir = args.data

    print(f"[INFO] data_dir={data_dir}")
    graphs = load_graphs_from_tsv_dir(data_dir, pattern=args.pattern)
    if not graphs:
        raise SystemExit(f"TSVが見つかりません: {data_dir} / {args.pattern}")

    result = run_pipeline_from_dir(data_dir, pattern=args.pattern, seed=args.seed)
    frames, gif_path = render_step9_animation(
        result, out_dir=args.out, steps=args.steps
    )
    print(f"[INFO] frames: {len(frames)} files in {args.out}")
    if gif_path:
        print(f"[INFO] gif: {gif_path}")
    else:
        print(
            "[INFO] imageio が無いため GIF は作成されませんでした。 `pip install imageio` で有効化できます。"
        )


# python baseline/baseline_motif.py --data data/NBAF_coauthors/ntwk/ --pattern "*" --out ./style_anim_out


if __name__ == "__main__":
    main()
