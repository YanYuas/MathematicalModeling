"""
Q1图2创新设计 - 极坐标与拓扑变换版本
实验美学家：非线性坐标 + Kandinsky抽象风格

设计理念：
- 变体1：传统笛卡尔（baseline）
- 变体2：极坐标展开（角度作径向映射）
- 变体3：对数极坐标（gap放大）
- 变体4：Kandinsky抽象（纯几何符号）

保持Ink & Ochre配色，数据不变，坐标系统创新
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, Polygon as MplPolygon, Wedge, Arc
import matplotlib.gridspec as gridspec
from typing import List, Tuple
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

# 全局配色
PALETTE = {
    "ink": "#1C1C1C",
    "slate": "#5B6B73",
    "paper": "#F7F4EE",
    "field": "#C5D4E0",
    "geometry": "#2C4A6E",
    "ochre": "#C47B2B",
    "rust": "#8C3A2A",
    "sage": "#4F6F5C",
}

LW = {'main': 2.2, 'theory': 1.4, 'aux': 0.7}
DPI = 300


# ============================================================================
# 变体2：极坐标展开 - 角度作为径向维度
# ============================================================================

def plot_fig2_polar_unwrap(save_path='../实验结果/figs/fig2_polar_unwrap.png'):
    """
    【创新点】将三角形的角度关系映射到极坐标
    - 径向轴：从圆心到顶点的半径
    - 角度轴：∠ACB的值（60°, 90°对比）
    - Thales圆变成极坐标中的临界线

    【视觉叙事】60°在90°临界线下方 → 直径圆失败
    """
    fig = plt.figure(figsize=(7.1, 4.5), dpi=DPI, facecolor=PALETTE['paper'])

    gs = gridspec.GridSpec(1, 2, width_ratios=[1.2, 1], wspace=0.35)
    ax_cart = plt.subplot(gs[0])
    ax_polar = plt.subplot(gs[1], projection='polar')

    # === 左侧：传统视图（参考） ===
    ax_cart.set_facecolor(PALETTE['paper'])

    side = 100
    vertices = np.array([
        [0, 0],
        [side, 0],
        [side/2, side*np.sqrt(3)/2]
    ])

    triangle = MplPolygon(vertices, fill=False,
                         edgecolor=PALETTE['ink'], linewidth=LW['main'])
    ax_cart.add_patch(triangle)

    # 顶点标注
    labels = ['A', 'B', 'C']
    for i, (v, label) in enumerate(zip(vertices, labels)):
        ax_cart.plot(v[0], v[1], 'o', color=PALETTE['ink'], markersize=6)
        ax_cart.text(v[0], v[1]+5 if i==2 else v[1]-8, label,
                    fontsize=11, ha='center', weight='bold')

