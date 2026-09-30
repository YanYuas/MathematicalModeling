#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VLSI布图数据可视化脚本 - 美化版（图2、4、5）
基于学术论文标准优化
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from pathlib import Path
import re
from math import pi

# 全局学术风格配置
def setup_academic_style():
    """全局学术风格配置"""
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

setup_academic_style()

# 输出目录
OUTPUT_DIR = Path(r"C:\Users\29845\Desktop\华数杯\问题1\原本数据集\图")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 数据文件路径
JSON_FILE = Path(r"C:\Users\29845\Desktop\华数杯\问题1\原本数据集\模块分类详细.json")
BLOCKS_DIR = Path(r"C:\Users\29845\Desktop\华数杯\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件")


def load_data():
    """加载统计数据"""
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


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


def plot_2_boxplot_enhanced(data):
    """图表2：纵横比箱线图（美化版）"""
    fig, ax = plt.subplots(figsize=(8.5/2.54, 6/2.54))

    datasets = ['n100', 'n200', 'n300']
    ratios_data = []
    max_values = []

    # 加载原始纵横比数据
    for ds in datasets:
        filepath = BLOCKS_DIR / f"{ds}.blocks"
        modules = parse_blocks_file(filepath)
        ratios = [m['aspect_ratio'] for m in modules]
        ratios_data.append(ratios)
        max_values.append(data[ds]['max_aspect_ratio'])

    positions = [1, 2, 3]

    # 绘制箱线图
    bp = ax.boxplot(ratios_data, positions=positions, widths=0.5,
                    patch_artist=True, showmeans=True,
                    meanprops=dict(marker='D', markerfacecolor='#F28E2B',
                                  markersize=6, markeredgecolor='white'),
                    medianprops=dict(color='#2C2C2C', linewidth=2),
                    whiskerprops=dict(linewidth=1.5, color='#4A4A4A'),
                    capprops=dict(linewidth=1.5, color='#4A4A4A'))

    # 美化箱体
    for patch in bp['boxes']:
        patch.set_facecolor('#4E79A7')
        patch.set_alpha(0.85)
        patch.set_edgecolor('#2C2C2C')
        patch.set_linewidth(1.2)

    # 叠加长条块散点
    for i, ratios in enumerate(ratios_data):
        strip_ratios = [r for r in ratios if r > 2.5]
        x_jitter = np.random.normal(positions[i], 0.04, len(strip_ratios))
        ax.scatter(x_jitter, strip_ratios, c='#E15759', alpha=0.7, s=40,
                   edgecolors='#8B0000', linewidths=0.8, zorder=5,
                   label='Strip modules (R>2.5)' if i == 0 else '')

    # 极值标注增强（星形标记+标注框）
    for i, (pos, max_val) in enumerate(zip(positions, max_values)):
        # 星形标记
        ax.scatter(pos, max_val, marker='*', s=150, c='#E15759',
                   edgecolors='white', linewidths=1.5, zorder=10)
        # 带箭头的标注
        ax.annotate(f'{max_val:.2f}', xy=(pos, max_val),
                    xytext=(8, 5), textcoords='offset points',
                    fontsize=9, fontweight='bold', color='#E15759',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                             edgecolor='#E15759', linewidth=1.5),
                    arrowprops=dict(arrowstyle='-', color='#E15759',
                                   linewidth=0.8, linestyle=':'))

    # 参考线优化
    ax.axhline(1.0, color='#59A14F', linestyle='-.', alpha=0.7,
               linewidth=1.8, label='Square constraint (R=1.0)', zorder=1)
    ax.axhline(2.5, color='#E15759', linestyle='--', alpha=0.85,
               linewidth=1.8, label='Strip threshold (R=2.5)', zorder=1)

    # 标题和标签
    ax.set_title('Aspect Ratio Distribution', fontsize=12,
                 fontweight='bold', color='#2C2C2C', pad=10)
    ax.set_ylabel('Aspect Ratio (R)', fontsize=10, fontweight='bold')
    ax.set_xlabel('Dataset', fontsize=10, fontweight='bold')
    ax.set_xticks(positions)
    ax.set_xticklabels(datasets, fontsize=9)
    ax.set_ylim(0.8, 4.5)

    # 图例优化
    ax.legend(loc='upper left', fontsize=8, frameon=True,
              framealpha=0.95, edgecolor='#CCCCCC',
              bbox_to_anchor=(0.02, 0.98))

    # 网格优化
    ax.grid(axis='y', alpha=0.25, linestyle='--', linewidth=0.5, color='#CCCCCC')

    plt.subplots_adjust(left=0.15, right=0.95, top=0.92, bottom=0.12)
    plt.savefig(OUTPUT_DIR / '图2_纵横比箱线图_优化版.png',
                dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.05)
    print(f"已保存: 图2_纵横比箱线图_优化版.png")
    plt.close()


def plot_4_scatter_enhanced(data):
    """图表4：纵横比-面积散点图（美化版）"""
    fig, ax = plt.subplots(figsize=(8.5/2.54, 6/2.54))

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
                   c='#B0B0B0', alpha=0.15, s=25, marker=markers[idx],
                   linewidths=0, zorder=1)

        # 2. 近方形（数据层）
        ax.scatter(areas_norm[near_square], ratios[near_square],
                   c=colors[idx], alpha=0.6, s=40, marker=markers[idx],
                   edgecolors='white', linewidths=0.8, zorder=2)

        # 收集长条块数据
        all_strip_x.extend(areas_norm[strip])
        all_strip_y.extend(ratios[strip])

    # 3. 所有长条块统一绘制（焦点层）
    all_strip_x = np.array(all_strip_x)
    all_strip_y = np.array(all_strip_y)

    # 光晕效果
    ax.scatter(all_strip_x, all_strip_y, c='#E15759', alpha=0.2, s=90,
               linewidths=0, zorder=3)
    # 主散点
    ax.scatter(all_strip_x, all_strip_y, c='#C1272D', alpha=0.85, s=70,
               edgecolors='#8B0000', linewidths=1.5, zorder=4,
               label='Strip modules (R>2.5)')

    # 阈值线
    ax.axhline(1.2, color='#59A14F', linestyle='--', alpha=0.5, linewidth=1.5)
    ax.axhline(2.5, color='#E15759', linestyle='--', alpha=0.5, linewidth=1.5)

    # 智能标注（找长条块质心）
    if len(all_strip_x) > 0:
        centroid_x = np.median(all_strip_x)
        centroid_y = np.median(all_strip_y)

        ax.annotate('Strip modules span\nall area ranges\n→ Shape irregularity',
                    xy=(centroid_x, centroid_y),
                    xytext=(0.65, 3.5),
                    fontsize=10, fontweight='bold', color='#C1272D',
                    bbox=dict(boxstyle='round,pad=0.6', facecolor='#FFE5E5',
                             alpha=0.95, edgecolor='#C1272D', linewidth=2),
                    arrowprops=dict(arrowstyle='->', color='#C1272D',
                                   lw=1.8, connectionstyle='arc3,rad=0.3'),
                    ha='center')

    # 标题和标签
    ax.set_title('Aspect Ratio vs. Normalized Area',
                 fontsize=12, fontweight='bold', color='#2C2C2C', pad=10)
    ax.set_xlabel('Normalized Area', fontsize=10, fontweight='bold')
    ax.set_ylabel('Aspect Ratio (R)', fontsize=10, fontweight='bold')
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0.8, 4.5)

    # 图例
    ax.legend(loc='upper left', fontsize=7, frameon=True, framealpha=0.95,
              bbox_to_anchor=(0.02, 0.98))

    # 网格轻量化
    ax.grid(alpha=0.2, linestyle=':', linewidth=0.5, color='#D0D0D0')

    plt.subplots_adjust(left=0.13, right=0.97, top=0.93, bottom=0.11)
    plt.savefig(OUTPUT_DIR / '图4_纵横比面积散点图_优化版.png',
                dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.05)
    print(f"已保存: 图4_纵横比面积散点图_优化版.png")
    plt.close()


def plot_5_radar_enhanced(data):
    """图表5：雷达图（美化版）"""
    fig, ax = plt.subplots(figsize=(8.5/2.54, 8.5/2.54),
                           subplot_kw=dict(projection='polar'))

    categories = ['Near-square\nratio', 'Strip\ncontrol',
                  'Aspect\noptimization', 'Space\nutilization',
                  'Module\nscale']
    N = len(categories)
    angles = [n / N * 2 * pi for n in range(N)]
    angles += angles[:1]

    # 数据
    scores = {
        'n100': [20, 85, 82.25, 99.85, 33.33],
        'n200': [29, 86.5, 83.25, 99.60, 66.67],
        'n300': [28, 91, 84, 99.87, 100]
    }

    # 先绘制弱势维度背景扇形
    theta_range = np.linspace(angles[0], angles[2], 50)
    ax.fill_between(theta_range, 0, 100,
                     color='#FFE5E5', alpha=0.15, zorder=0)

    # 配色和线宽
    colors = ['#E15759', '#4E79A7', '#59A14F']
    linewidths = [3.5, 2.0, 2.0]
    alphas = [0.25, 0.12, 0.12]
    datasets = ['n100', 'n200', 'n300']

    for idx, ds in enumerate(datasets):
        values = scores[ds]
        values += values[:1]

        ax.plot(angles, values, 'o-', linewidth=linewidths[idx],
                color=colors[idx], label=ds, markersize=7 if idx==0 else 6,
                zorder=5-idx)
        ax.fill(angles, values, alpha=alphas[idx], color=colors[idx])

    # 突出n100弱点
    theta_strip = angles[1]
    ax.scatter(theta_strip, scores['n100'][1],
               s=200, facecolors='none', edgecolors='#E15759',
               linewidths=3, zorder=10)

    # 添加标注
    ax.annotate('n100 weakness',
                xy=(theta_strip, scores['n100'][1]),
                xytext=(theta_strip+0.8, 55),
                arrowprops=dict(arrowstyle='->', color='#E15759',
                               lw=2, connectionstyle='arc3,rad=0.2'),
                fontsize=9, color='#E15759', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                         edgecolor='#E15759', linewidth=1.5))

    # 坐标轴设置
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=9, fontweight='bold',
                        color='#2C2C2C')
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'],
                        fontsize=8, color='#4A4A4A')

    # 网格优化
    ax.grid(True, linestyle='--', alpha=0.3, linewidth=0.5, color='#CCCCCC')

    # 标题
    ax.set_title('Multi-dimensional Dataset Comparison',
                 fontsize=12, fontweight='bold', color='#2C2C2C', pad=15)

    # 图例
    ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1.05),
              fontsize=9, frameon=True, framealpha=0.95,
              edgecolor='#CCCCCC')

    # 底部注释
    ax.text(0, -0.15, 'Note: Higher values indicate better performance',
            ha='center', fontsize=8, color='#666666', style='italic',
            transform=ax.transAxes)

    plt.tight_layout(pad=1.5)
    plt.savefig(OUTPUT_DIR / '图5_雷达图综合对比_优化版.png',
                dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.05)
    print(f"已保存: 图5_雷达图综合对比_优化版.png")
    plt.close()


def main():
    """主函数"""
    print("开始生成美化版数据可视化图表...\n")

    # 加载数据
    data = load_data()

    # 生成3张优化图
    print("[1/3] 生成纵横比箱线图（美化版）...")
    plot_2_boxplot_enhanced(data)

    print("[2/3] 生成纵横比-面积散点图（美化版）...")
    plot_4_scatter_enhanced(data)

    print("[3/3] 生成雷达图（美化版）...")
    plot_5_radar_enhanced(data)

    print(f"\n全部美化版图表已生成完成！")
    print(f"保存位置: {OUTPUT_DIR}")
    print("\n图表清单:")
    print("  - 图2_纵横比箱线图_优化版.png")
    print("  - 图4_纵横比面积散点图_优化版.png")
    print("  - 图5_雷达图综合对比_优化版.png")


if __name__ == '__main__':
    main()
