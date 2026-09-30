#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图4：纵横比-面积散点图（美化版）
证明"长条块不是因为大，而是形状不规则"
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
BLOCKS_DIR = Path(r"C:\Users\29845\Desktop\华数杯\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件")


def parse_blocks_file(filepath):
    """解析.blocks文件获取详细数据"""
    modules = []

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
            area = width * height

            if width > 0 and height > 0:
                aspect_ratio = max(width, height) / min(width, height)
                modules.append({
                    'area': area,
                    'aspect_ratio': aspect_ratio
                })

    return modules


def main():
    """主函数"""
    print("生成图4：纵横比-面积散点图...")

    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 8))

    datasets = ['n100', 'n200', 'n300']
    colors = ['#E15759', '#4E79A7', '#59A14F']
    markers = ['o', 's', '^']

    all_strip_x, all_strip_y = [], []

    for idx, ds in enumerate(datasets):
        filepath = BLOCKS_DIR / f"{ds}.blocks"
        modules = parse_blocks_file(filepath)

        areas = np.array([m['area'] for m in modules])
        ratios = np.array([m['aspect_ratio'] for m in modules])

        # 归一化面积
        areas_norm = areas / np.max(areas)

        # 分类
        near_square = ratios < 1.2
        strip = ratios > 2.5
        middle = ~(near_square | strip)

        # 1. 中间块（背景层）
        ax.scatter(areas_norm[middle], ratios[middle],
                   c='#B0B0B0', alpha=0.15, s=35, marker=markers[idx],
                   linewidths=0, zorder=1)

        # 2. 近方形（数据层）
        ax.scatter(areas_norm[near_square], ratios[near_square],
                   c=colors[idx], alpha=0.6, s=55, marker=markers[idx],
                   edgecolors='white', linewidths=1.0, zorder=2,
                   label=f'{ds} modules')

        # 收集长条块数据
        all_strip_x.extend(areas_norm[strip])
        all_strip_y.extend(ratios[strip])

    # 3. 所有长条块统一绘制（焦点层）
    all_strip_x = np.array(all_strip_x)
    all_strip_y = np.array(all_strip_y)

    # 光晕效果
    ax.scatter(all_strip_x, all_strip_y, c='#E15759', alpha=0.2, s=120,
               linewidths=0, zorder=3)
    # 主散点
    ax.scatter(all_strip_x, all_strip_y, c='#C1272D', alpha=0.85, s=90,
               edgecolors='#8B0000', linewidths=1.8, zorder=4,
               label='Strip modules (R>2.5)')

    # 阈值线
    ax.axhline(1.2, color='#59A14F', linestyle='--', alpha=0.5, linewidth=2.0,
               label='Near-square threshold (R=1.2)')
    ax.axhline(2.5, color='#E15759', linestyle='--', alpha=0.5, linewidth=2.0,
               label='Strip threshold (R=2.5)')

    # 智能标注（找长条块质心）
    if len(all_strip_x) > 0:
        centroid_x = np.median(all_strip_x)
        centroid_y = np.median(all_strip_y)

        ax.annotate('Strip modules span\nall area ranges\n→ Shape irregularity\nis the root cause',
                    xy=(centroid_x, centroid_y),
                    xytext=(0.65, 3.5),
                    fontsize=11, fontweight='bold', color='#C1272D',
                    bbox=dict(boxstyle='round,pad=0.7', facecolor='#FFE5E5',
                             alpha=0.95, edgecolor='#C1272D', linewidth=2.5),
                    arrowprops=dict(arrowstyle='->', color='#C1272D',
                                   lw=2.2, connectionstyle='arc3,rad=0.3'),
                    ha='center')

    # 标题和标签
    ax.set_title('Aspect Ratio vs. Normalized Area: Strip Module Distribution',
                 fontsize=14, fontweight='bold', color='#2C2C2C', pad=15)
    ax.set_xlabel('Normalized Area', fontsize=12, fontweight='bold')
    ax.set_ylabel('Aspect Ratio (R)', fontsize=12, fontweight='bold')
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0.8, 4.5)

    # 图例
    ax.legend(loc='upper left', fontsize=9, frameon=True, framealpha=0.95,
              edgecolor='#CCCCCC', bbox_to_anchor=(0.02, 0.98))

    # 网格
    ax.grid(alpha=0.2, linestyle=':', linewidth=0.8, color='#D0D0D0')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '图4_纵横比面积散点图_优化版.png',
                dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.1)
    print(f"已保存: {OUTPUT_DIR / '图4_纵横比面积散点图_优化版.png'}")
    plt.close()


if __name__ == '__main__':
    main()
