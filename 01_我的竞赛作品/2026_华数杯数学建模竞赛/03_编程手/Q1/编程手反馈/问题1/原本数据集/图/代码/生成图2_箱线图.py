#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图2：纵横比箱线图（美化版）
展示极端值分布，证明"少数极端模块是优化难点"
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re

# 全局学术风格配置
plt.rcParams.update({
    'font.family': 'Arial',
    'font.size': 10,
    'axes.labelsize': 10,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 8,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.linewidth': 1.2,
    'grid.linewidth': 0.5,
    'lines.linewidth': 2.0,
    'patch.linewidth': 1.0,
    'axes.unicode_minus': False,
    'mathtext.fontset': 'stix'
})

# 路径配置
OUTPUT_DIR = Path(r"C:\Users\29845\Desktop\华数杯\问题1\原本数据集\图")
JSON_FILE = Path(r"C:\Users\29845\Desktop\华数杯\问题1\原本数据集\模块分类详细.json")
BLOCKS_DIR = Path(r"C:\Users\29845\Desktop\华数杯\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件")


def load_data():
    """加载统计数据"""
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_blocks_file(filepath):
    """解析.blocks文件获取纵横比数据"""
    ratios = []

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        pattern = r'b\d+\s+block\s+\d+\s+\((\d+),\s*(\d+)\)\s+\((\d+),\s*(\d+)\)\s+\((\d+),\s*(\d+)\)\s+\((\d+),\s*(\d+)\)'

        for match in re.finditer(pattern, content):
            coords = [
                (int(match.group(1)), int(match.group(2))),
                (int(match.group(3)), int(match.group(4))),
                (int(match.group(5)), int(match.group(6))),
                (int(match.group(7)), int(match.group(8)))
            ]

            x_coords = [c[0] for c in coords]
            y_coords = [c[1] for c in coords]

            width = max(x_coords) - min(x_coords)
            height = max(y_coords) - min(y_coords)

            if width > 0 and height > 0:
                aspect_ratio = max(width, height) / min(width, height)
                ratios.append(aspect_ratio)

    return ratios


def main():
    """主函数"""
    print("生成图2：纵横比箱线图...")

    # 加载数据
    data = load_data()

    # 创建图表
    fig, ax = plt.subplots(figsize=(10, 7))

    datasets = ['n100', 'n200', 'n300']
    ratios_data = []
    max_values = []

    # 加载原始纵横比数据
    for ds in datasets:
        filepath = BLOCKS_DIR / f"{ds}.blocks"
        ratios = parse_blocks_file(filepath)
        ratios_data.append(ratios)
        max_values.append(data[ds]['max_aspect_ratio'])

    positions = [1, 2, 3]

    # 绘制箱线图
    bp = ax.boxplot(ratios_data, positions=positions, widths=0.5,
                    patch_artist=True, showmeans=True,
                    meanprops=dict(marker='D', markerfacecolor='#F28E2B',
                                  markersize=8, markeredgecolor='white'),
                    medianprops=dict(color='#2C2C2C', linewidth=2.5),
                    whiskerprops=dict(linewidth=1.5, color='#4A4A4A'),
                    capprops=dict(linewidth=1.5, color='#4A4A4A'))

    # 美化箱体
    for patch in bp['boxes']:
        patch.set_facecolor('#4E79A7')
        patch.set_alpha(0.85)
        patch.set_edgecolor('#2C2C2C')
        patch.set_linewidth(1.5)

    # 叠加长条块散点
    for i, ratios in enumerate(ratios_data):
        strip_ratios = [r for r in ratios if r > 2.5]
        x_jitter = np.random.normal(positions[i], 0.04, len(strip_ratios))
        ax.scatter(x_jitter, strip_ratios, c='#E15759', alpha=0.7, s=50,
                   edgecolors='#8B0000', linewidths=1.0, zorder=5,
                   label='Strip modules (R>2.5)' if i == 0 else '')

    # 极值标注（星形标记+标注框）
    for i, (pos, max_val) in enumerate(zip(positions, max_values)):
        # 星形标记
        ax.scatter(pos, max_val, marker='*', s=200, c='#E15759',
                   edgecolors='white', linewidths=2, zorder=10)
        # 带箭头的标注
        ax.annotate(f'{max_val:.2f}', xy=(pos, max_val),
                    xytext=(10, 8), textcoords='offset points',
                    fontsize=11, fontweight='bold', color='#E15759',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                             edgecolor='#E15759', linewidth=2),
                    arrowprops=dict(arrowstyle='-', color='#E15759',
                                   linewidth=1.0, linestyle=':'))

    # 参考线
    ax.axhline(1.0, color='#59A14F', linestyle='-.', alpha=0.7,
               linewidth=2.2, label='Square constraint (R=1.0)', zorder=1)
    ax.axhline(2.5, color='#E15759', linestyle='--', alpha=0.85,
               linewidth=2.2, label='Strip threshold (R=2.5)', zorder=1)

    # 标题和标签
    ax.set_title('Aspect Ratio Distribution with Outlier Highlighting',
                 fontsize=14, fontweight='bold', color='#2C2C2C', pad=15)
    ax.set_ylabel('Aspect Ratio (R)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Dataset', fontsize=12, fontweight='bold')
    ax.set_xticks(positions)
    ax.set_xticklabels(datasets, fontsize=11)
    ax.set_ylim(0.8, 4.5)

    # 图例
    ax.legend(loc='upper left', fontsize=10, frameon=True,
              framealpha=0.95, edgecolor='#CCCCCC',
              bbox_to_anchor=(0.02, 0.98))

    # 网格
    ax.grid(axis='y', alpha=0.25, linestyle='--', linewidth=0.8, color='#CCCCCC')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '图2_纵横比箱线图_优化版.png',
                dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.1)
    print(f"已保存: {OUTPUT_DIR / '图2_纵横比箱线图_优化版.png'}")
    plt.close()


if __name__ == '__main__':
    main()
