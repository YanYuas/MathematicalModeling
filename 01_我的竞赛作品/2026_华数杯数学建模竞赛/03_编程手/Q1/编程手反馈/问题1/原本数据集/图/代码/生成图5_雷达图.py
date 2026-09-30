#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图5：雷达图综合对比（美化版）
多维度对比，突出"n100在长条块控制维度最弱"
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from math import pi

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


def load_data():
    """加载统计数据"""
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """主函数"""
    print("生成图5：雷达图综合对比...")

    # 加载数据
    data = load_data()

    # 创建图表
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

    categories = ['Near-square\nratio', 'Strip\ncontrol',
                  'Aspect\noptimization', 'Space\nutilization',
                  'Module\nscale']
    N = len(categories)
    angles = [n / N * 2 * pi for n in range(N)]
    angles += angles[:1]

    # 数据（归一化到0-100分制）
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
    linewidths = [3.5, 2.5, 2.5]
    alphas = [0.25, 0.12, 0.12]
    datasets = ['n100', 'n200', 'n300']

    for idx, ds in enumerate(datasets):
        values = scores[ds]
        values += values[:1]

        ax.plot(angles, values, 'o-', linewidth=linewidths[idx],
                color=colors[idx], label=ds, markersize=8 if idx==0 else 7,
                zorder=5-idx)
        ax.fill(angles, values, alpha=alphas[idx], color=colors[idx])

    # 突出n100弱点
    theta_strip = angles[1]
    ax.scatter(theta_strip, scores['n100'][1],
               s=250, facecolors='none', edgecolors='#E15759',
               linewidths=3.5, zorder=10)

    # 添加标注
    ax.annotate('n100 weakness:\nLowest strip control',
                xy=(theta_strip, scores['n100'][1]),
                xytext=(theta_strip+0.9, 55),
                arrowprops=dict(arrowstyle='->', color='#E15759',
                               lw=2.5, connectionstyle='arc3,rad=0.2'),
                fontsize=10, color='#E15759', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                         edgecolor='#E15759', linewidth=2.0))

    # 坐标轴设置
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10, fontweight='bold',
                        color='#2C2C2C')
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'],
                        fontsize=9, color='#4A4A4A')

    # 网格
    ax.grid(True, linestyle='--', alpha=0.3, linewidth=0.8, color='#CCCCCC')

    # 标题
    ax.set_title('Multi-dimensional Dataset Comparison\n(Higher scores indicate better performance)',
                 fontsize=14, fontweight='bold', color='#2C2C2C', pad=20)

    # 图例
    ax.legend(loc='upper right', bbox_to_anchor=(1.18, 1.08),
              fontsize=10, frameon=True, framealpha=0.95,
              edgecolor='#CCCCCC')

    plt.tight_layout(pad=2.0)
    plt.savefig(OUTPUT_DIR / '图5_雷达图综合对比_优化版.png',
                dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.1)
    print(f"已保存: {OUTPUT_DIR / '图5_雷达图综合对比_优化版.png'}")
    plt.close()


if __name__ == '__main__':
    main()
