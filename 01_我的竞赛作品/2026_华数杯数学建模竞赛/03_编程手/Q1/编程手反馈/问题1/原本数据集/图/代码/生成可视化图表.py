#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VLSI布图数据可视化脚本
生成5种图表展示数据集特征
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from pathlib import Path
import re

# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei']  # 黑体
rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
rcParams['font.size'] = 10

# 输出目录
OUTPUT_DIR = Path(r"C:\Users\29845\Desktop\华数杯\问题1\原始数据集\图")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 数据文件路径
JSON_FILE = Path(r"C:\Users\29845\Desktop\华数杯\问题1\原本数据集\模块分类详细.json")
BLOCKS_DIR = Path(r"C:\Users\29845\Desktop\华数杯\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件")


def load_data():
    """加载统计数据"""
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_blocks_file(filepath):
    """解析.blocks文件获取纵横比数据"""
    aspect_ratios = []

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
                aspect_ratios.append(aspect_ratio)

    return aspect_ratios


def plot_1_stacked_bar(data):
    """图表1：模块分类堆叠柱状图"""
    fig, ax = plt.subplots(figsize=(10, 6))

    datasets = ['n100', 'n200', 'n300']
    x = np.arange(len(datasets))

    near_square = [data[ds]['square_like']['ratio'] for ds in datasets]
    middle = [data[ds]['middle']['ratio'] for ds in datasets]
    strip = [data[ds]['strip_like']['ratio'] for ds in datasets]

    # 绘制堆叠柱状图
    p1 = ax.bar(x, near_square, color='#2A9D8F', label='近方形 (<1.2)', width=0.6)
    p2 = ax.bar(x, middle, bottom=near_square, color='#B8B8B8', label='中间块 (1.2-2.5)', width=0.6)
    p3 = ax.bar(x, strip, bottom=np.array(near_square)+np.array(middle),
                color='#E63946', label='长条块 (>2.5)', width=0.6)

    # 在长条块区域标注百分比
    for i, v in enumerate(strip):
        y_pos = near_square[i] + middle[i] + v/2
        weight = 'bold' if i == 0 else 'normal'
        size = 14 if i == 0 else 12
        ax.text(i, y_pos, f'{v}%', ha='center', va='center',
                fontweight=weight, fontsize=size, color='white')

    # 添加箭头标注
    ax.annotate('长条块占比递减\n优化难度下降',
                xy=(2, 95), xytext=(1.5, 85),
                arrowprops=dict(arrowstyle='->', color='red', lw=2),
                fontsize=11, color='red', ha='center',
                bbox=dict(boxstyle='round', facecolor='#FFE5E5', alpha=0.8))

    ax.set_ylabel('模块占比 (%)', fontsize=13, fontweight='bold')
    ax.set_xlabel('数据集', fontsize=13, fontweight='bold')
    ax.set_title('图1 三组数据集模块分类对比（突出长条块占比差异）',
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(datasets, fontsize=12)
    ax.set_ylim(0, 105)
    ax.legend(loc='upper right', fontsize=11, framealpha=0.9)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '图1_模块分类堆叠柱状图.png', dpi=300, bbox_inches='tight')
    print(f"已保存: 图1_模块分类堆叠柱状图.png")
    plt.close()


def plot_2_boxplot(data):
    """图表2：纵横比分布箱线图"""
    fig, ax = plt.subplots(figsize=(10, 7))

    datasets = ['n100', 'n200', 'n300']
    ratios_data = []

    # 加载原始纵横比数据
    for ds in datasets:
        filepath = BLOCKS_DIR / f"{ds}.blocks"
        ratios = parse_blocks_file(filepath)
        ratios_data.append(ratios)

    positions = [1, 2, 3]

    # 绘制箱线图
    bp = ax.boxplot(ratios_data, positions=positions, widths=0.5,
                    patch_artist=True, showmeans=True,
                    meanprops=dict(marker='D', markerfacecolor='orange', markersize=8),
                    medianprops=dict(color='darkblue', linewidth=2))

    # 美化箱线图
    for patch in bp['boxes']:
        patch.set_facecolor('#457B9D')
        patch.set_alpha(0.7)

    # 叠加长条块散点
    for i, ratios in enumerate(ratios_data):
        strip_ratios = [r for r in ratios if r > 2.5]
        x_jitter = np.random.normal(positions[i], 0.04, len(strip_ratios))
        ax.scatter(x_jitter, strip_ratios, c='#E63946', alpha=0.5, s=30,
                   label='长条块 (>2.5)' if i == 0 else '')

    # 标注最大值
    max_values = [data[ds]['max_aspect_ratio'] for ds in datasets]
    for i, (pos, max_val) in enumerate(zip(positions, max_values)):
        ax.text(pos+0.15, max_val, f'{max_val:.2f}', fontsize=10,
                fontweight='bold', color='#E63946')

    # 添加参考线
    ax.axhline(1.0, color='#2A9D8F', linestyle='--', alpha=0.6,
               linewidth=2, label='方形约束 (R=1.0)')
    ax.axhline(2.5, color='#E63946', linestyle='--', alpha=0.6,
               linewidth=2, label='长条块阈值 (R=2.5)')

    ax.set_ylabel('纵横比', fontsize=13, fontweight='bold')
    ax.set_xlabel('数据集', fontsize=13, fontweight='bold')
    ax.set_title('图2 纵横比分布箱线图（展示极端值分布）',
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(positions)
    ax.set_xticklabels(datasets, fontsize=12)
    ax.set_ylim(0.8, 4.5)
    ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '图2_纵横比箱线图.png', dpi=300, bbox_inches='tight')
    print(f" 已保存: 图2_纵横比箱线图.png")
    plt.close()


def plot_3_deadspace(data):
    """图表3：死区率对比柱状图"""
    fig, ax = plt.subplots(figsize=(10, 6))

    datasets = ['n100', 'n200', 'n300']
    x = np.arange(len(datasets))
    dead_space = [data[ds]['deadspace_rate'] for ds in datasets]

    bars = ax.bar(x, dead_space, width=0.5, color='#264653', alpha=0.8,
                  edgecolor='black', linewidth=1.5)

    # 标注数值
    for i, v in enumerate(dead_space):
        ax.text(i, v+0.15, f'{v:.2f}%', ha='center', fontsize=13,
                fontweight='bold', color='#264653')

    # 添加工业阈值参考线
    ax.axhline(5.0, color='#2A9D8F', linestyle='--', linewidth=2.5,
               label='工业可接受阈值 (5%)')

    # 添加文本框说明
    ax.text(1.5, 4.2, '死区率 < 0.5%\n算法已接近理论极限',
            bbox=dict(boxstyle='round,pad=0.8', facecolor='wheat', alpha=0.7,
                      edgecolor='#E76F51', linewidth=2),
            ha='center', fontsize=12, fontweight='bold', color='#264653')

    ax.set_ylim(0, 6)
    ax.set_ylabel('死区率 (%)', fontsize=13, fontweight='bold')
    ax.set_xlabel('数据集', fontsize=13, fontweight='bold')
    ax.set_title('图3 理论死区率对比（证明优化空间有限）',
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(datasets, fontsize=12)
    ax.legend(loc='upper right', fontsize=11, framealpha=0.9)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '图3_死区率柱状图.png', dpi=300, bbox_inches='tight')
    print(f" 已保存: 图3_死区率柱状图.png")
    plt.close()


def plot_4_scatter(data):
    """图表4：纵横比-面积散点图"""
    fig, ax = plt.subplots(figsize=(12, 7))

    datasets = ['n100', 'n200', 'n300']
    colors = ['#E63946', '#457B9D', '#2A9D8F']
    markers = ['o', 's', '^']

    for idx, ds in enumerate(datasets):
        filepath = BLOCKS_DIR / f"{ds}.blocks"

        # 解析获取面积和纵横比
        areas = []
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
                area = width * height

                if width > 0 and height > 0:
                    aspect_ratio = max(width, height) / min(width, height)
                    areas.append(area)
                    ratios.append(aspect_ratio)

        # 归一化面积
        areas_norm = np.array(areas) / max(areas)
        ratios = np.array(ratios)

        # 分类绘制
        near_square = ratios < 1.2
        strip = ratios > 2.5
        middle = ~(near_square | strip)

        # 绘制散点（按类型分层）
        ax.scatter(areas_norm[middle], ratios[middle], c=colors[idx],
                   alpha=0.2, s=30, marker=markers[idx])
        ax.scatter(areas_norm[near_square], ratios[near_square], c='#2A9D8F',
                   alpha=0.5, s=40, marker=markers[idx],
                   label=f'{ds}-近方形' if idx == 0 else '')
        ax.scatter(areas_norm[strip], ratios[strip], c='#E63946',
                   alpha=0.7, s=60, marker=markers[idx], edgecolors='darkred',
                   linewidth=1.5, label=f'{ds}-长条块')

    # 添加阈值线
    ax.axhline(1.2, color='#2A9D8F', linestyle='--', alpha=0.5, linewidth=1.5)
    ax.axhline(2.5, color='#E63946', linestyle='--', alpha=0.5, linewidth=1.5)

    # 标注
    ax.annotate('长条块分布在各面积段\n→ 形状不规则是本质',
                xy=(0.6, 3.5), fontsize=11, color='#E63946',
                bbox=dict(boxstyle='round,pad=0.8', facecolor='#FFE5E5',
                          alpha=0.8, edgecolor='#E63946', linewidth=1.5),
                ha='center', fontweight='bold')

    ax.set_xlabel('模块面积（归一化）', fontsize=13, fontweight='bold')
    ax.set_ylabel('纵横比', fontsize=13, fontweight='bold')
    ax.set_title('图4 纵横比-面积散点图（双色编码：近方形vs长条块）',
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0.8, 4.5)
    ax.legend(loc='upper left', fontsize=9, framealpha=0.9, ncol=2)
    ax.grid(alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '图4_纵横比面积散点图.png', dpi=300, bbox_inches='tight')
    print(f" 已保存: 图4_纵横比面积散点图.png")
    plt.close()


def plot_5_radar(data):
    """图表5：三组数据集雷达图"""
    from math import pi

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

    categories = ['近方形占比', '长条块控制', '纵横比优化', '空间利用', '模块规模']
    N = len(categories)

    datasets = ['n100', 'n200', 'n300']

    # 归一化数据（0-100分制）
    scores = {
        'n100': [
            20,  # 近方形占比
            100 - 15,  # 长条块控制（占比越低越好）
            (5 - 1.71) / 4 * 100,  # 纵横比优化（越接近1越好）
            99.85,  # 空间利用（100-死区率）
            100 / 3  # 模块规模（归一化）
        ],
        'n200': [
            29,
            100 - 13.5,
            (5 - 1.67) / 4 * 100,
            99.60,
            200 / 3
        ],
        'n300': [
            28,
            100 - 9,
            (5 - 1.64) / 4 * 100,
            99.87,
            100
        ]
    }

    angles = [n / N * 2 * pi for n in range(N)]
    angles += angles[:1]

    colors = ['#E63946', '#457B9D', '#2A9D8F']

    for idx, ds in enumerate(datasets):
        values = scores[ds]
        values += values[:1]

        ax.plot(angles, values, 'o-', linewidth=2.5, color=colors[idx],
                label=ds, markersize=8)
        ax.fill(angles, values, alpha=0.15, color=colors[idx])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)

    # 添加说明文本
    ax.text(0, -15, '注：数值越大表示该维度表现越好',
            ha='center', fontsize=10, color='gray',
            transform=ax.transData)

    ax.set_title('图5 三组数据集多维度综合对比（雷达图）',
                 fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=12, framealpha=0.9)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '图5_雷达图综合对比.png', dpi=300, bbox_inches='tight')
    print(f" 已保存: 图5_雷达图综合对比.png")
    plt.close()


def main():
    """主函数"""
    print("开始生成数据可视化图表...\n")

    # 加载数据
    data = load_data()

    # 生成5张图
    print("[1/5] 生成模块分类堆叠柱状图...")
    plot_1_stacked_bar(data)

    print("[2/5] 生成纵横比箱线图...")
    plot_2_boxplot(data)

    print("[3/5] 生成死区率柱状图...")
    plot_3_deadspace(data)

    print("[4/5] 生成纵横比-面积散点图...")
    plot_4_scatter(data)

    print("[5/5] 生成雷达图...")
    plot_5_radar(data)

    print(f"\n全部图表已生成完成！")
    print(f"保存位置: {OUTPUT_DIR}")
    print("\n图表清单:")
    print("  - 图1_模块分类堆叠柱状图.png")
    print("  - 图2_纵横比箱线图.png")
    print("  - 图3_死区率柱状图.png")
    print("  - 图4_纵横比面积散点图.png")
    print("  - 图5_雷达图综合对比.png")


if __name__ == '__main__':
    main()
