import matplotlib.pyplot as plt
import numpy as np
import sys
import os
from constants import PNG_PATH

def __create_directory(directory_name):
    os.makedirs(directory_name, exist_ok=True)
    return directory_name

def save_basic_scatter(initial_plot_x, initial_plot_y, optimized_plot_x, optimized_plot_y, 
                      x_label, y_label, title, fname, axis_limits):
    """散布図を描画して保存する"""
    fig, ax = plt.subplots(figsize=(6, 5))

    # 初期世代と最適化後の点をプロット
    ax.plot(initial_plot_x, initial_plot_y, "b.", label="Initial")
    ax.plot(optimized_plot_x, optimized_plot_y, "r.", label="Optimized")

    # ラベルの追加
    for i, (x, y) in enumerate(zip(initial_plot_x, initial_plot_y)):
        ax.annotate(str(i), (x, y), fontsize=8)
    for i, (x, y) in enumerate(zip(optimized_plot_x, optimized_plot_y)):
        ax.annotate(str(i), (x, y), fontsize=8)

    ax.set_xlim(axis_limits['xmin'], axis_limits['xmax'])
    ax.set_ylim(axis_limits['ymin'], axis_limits['ymax'])

    # グラフの設定
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.legend(loc="upper right")
    ax.grid(True)

    # 保存して閉じる
    print(f"{fname}に保存")
    fig.savefig(fname)
    plt.close(fig)


def load_generations_from_file(filepath):
    generations = []
    current_generation = []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.endswith("generation"):
                if current_generation:
                    generations.append(current_generation)
                    current_generation = []
            else:
                point = list(map(float, line.split(',')))
                current_generation.append(point)

        if current_generation:
            generations.append(current_generation)

    return generations

def get_axis_limits(generations, x_idx, y_idx):
    """
    散布図の軸の上限・下限を取得する。
    与えられた2軸(x_idx, y_idx)に対する最小・最大値を取得し、適度な余裕を持たせる
    
    Args:
        generations (list): 全世代のデータ
        x_idx (int): X軸のインデックス
        y_idx (int): Y軸のインデックス
    """
    all_points = np.vstack([np.array(gen) for gen in generations])
    
    # X軸の範囲を計算
    min_x = np.min(all_points[:, x_idx])
    max_x = np.max(all_points[:, x_idx])
    # 値の大きさに応じて余裕を持たせる（NSGA2の実装を参考）
    if abs(max_x) > 100:
        margin_x = (max_x - min_x) / 100.0  # 大きい値の場合は控えめな余裕
    else:
        margin_x = (max_x - min_x) / 10.0   # 小さい値の場合は大きめな余裕
    x_range = (min_x - margin_x, max_x + margin_x)

    # Y軸の範囲を計算
    min_y = np.min(all_points[:, y_idx])
    max_y = np.max(all_points[:, y_idx])
    # 値の大きさに応じて余裕を持たせる
    if abs(max_y) > 100:
        margin_y = (max_y - min_y) / 100.0
    else:
        margin_y = (max_y - min_y) / 10.0
    y_range = (min_y - margin_y, max_y + margin_y)

    return x_range, y_range


def plot_generation_scatters(generations, output_dir):
    """
    全世代の散布図を生成する
    """
    axis_pairs = [
        ("sprawl", "clutter"),
        ("sprawl", "time_smoothness"),
        ("clutter", "time_smoothness")
    ]

    # 軸のインデックスマッピング
    axis_map = {"sprawl": 0, "clutter": 1, "time_smoothness": 2}
    

    # 初期世代のデータ
    initial_gen = np.array(generations[0])
    
    for gen_idx, gen_data in enumerate(generations[1:], 1):
        gen_data = np.array(gen_data)
        
        for x_label, y_label in axis_pairs:
            x_idx = axis_map[x_label]
            y_idx = axis_map[y_label]

            (x_min, x_max), (y_min, y_max) = get_axis_limits(generations, x_idx, y_idx)
            axis_limits = {
                "xmin": x_min,
                "xmax": x_max,
                "ymin": y_min,
                "ymax": y_max,
            }

            dir_name = __create_directory(f"{output_dir}/{x_label}_vs_{y_label}/")
            
            save_basic_scatter(
                initial_gen[:, x_idx], initial_gen[:, y_idx],
                gen_data[:, x_idx], gen_data[:, y_idx],
                x_label, y_label,
                f"Generation {gen_idx}: {x_label} vs {y_label}",
                f"{dir_name}result_gen{gen_idx}.png",
                axis_limits
            )

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scatter_plot_from_txt.py <input_txt_path> <output_directory>")
        sys.exit(1)

    input_txt_path = sys.argv[1]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)
    os.chdir(output_dir)


    dir_name = __create_directory(PNG_PATH + f"{output_dir}")        

    generations = load_generations_from_file(PNG_PATH + input_txt_path)
    plot_generation_scatters(generations, dir_name)
