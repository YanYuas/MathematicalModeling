"""
Q1 - 期刊级图表生成模块 (重构版)
基于专业审核意见：Ink & Ochre配色 + 非对称布局 + 视觉叙事

核心原则：
1. 一张图只强调一个结论
2. 视觉层级极强
3. 辅助信息主动退后
4. 克制底色 + 单一强调色 + 局部高对比 + 大量留白
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, Polygon as MplPolygon, FancyArrowPatch, Wedge, Arc
from matplotlib.collections import PatchCollection
import matplotlib.gridspec as gridspec
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.patches import ConnectionPatch
from typing import List, Tuple
import sys
import os

# 导入Q1主程序的函数
sys.path.insert(0, os.path.dirname(__file__))
from q1_main import (
    build_wedges, candidate_vertices, convex_hull,
    diameter_bruteforce, mec_bruteforce, welzl_mec,
    unit_vector, angdiff
)

# ============================================================================
# 全局配置 - 方案A: Ink & Ochre (专业审核推荐)
# ============================================================================

PALETTE_A = {
    "ink": "#1C1C1C",        # 轴线、公式、主轮廓
    "slate": "#5B6B73",      # 次要标注、网格替代
    "paper": "#F7F4EE",      # 画布/浅底（也可用纯白#FFFFFF）
    "field": "#C5D4E0",      # 角域、不确定区域填充
    "geometry": "#2C4A6E",   # 观测站、射线、多边形边
    "ochre": "#C47B2B",      # 唯一强调色：直径D、关键发现
    "rust": "#8C3A2A",       # gap / 不覆盖 / 失败
    "sage": "#4F6F5C",       # 取等、最优、γ=1
}

# 线宽标准（严格遵循）
LINEWIDTH = {
    'main': 2.2,      # 主元素
    'theory': 1.4,    # 理论界
    'aux': 0.7,       # 辅助信息
}

# 字体和画布配置
FIGURE_CONFIG = {
    '通栏': (7.1, 4.5),    # 通栏复合图
    '双栏': (3.4, 2.6),    # 双栏单图
    'dpi': 300,
    'font_size': 9,        # 终稿字号
    'label_size': 10,      # 面板标签 a,b,c
}

# 设置全局matplotlib参数
plt.rcParams.update({
    'font.size': FIGURE_CONFIG['font_size'],
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'axes.linewidth': 0.8,
    'axes.edgecolor': PALETTE_A['slate'],
    'axes.labelcolor': PALETTE_A['ink'],
    'text.color': PALETTE_A['ink'],
    'xtick.color': PALETTE_A['slate'],
    'ytick.color': PALETTE_A['slate'],
    'xtick.major.width': 0.8,
    'ytick.major.width': 0.8,
    'grid.linewidth': 0.4,
    'grid.alpha': 0.3,
    'grid.color': PALETTE_A['slate'],
    # SVG和PDF导出设置
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
})


# ============================================================================
# 图2: Jung定理反例 - Thales半圆 + gap放大镜（最小可验证版本）
# ============================================================================

def plot_figure2_counterexample_v2(save_path='../实验结果/figs/fig2_jung_v2.png'):
    """
    【核心改进】
    1. 单画布：直径圆和外接圆叠在同一个三角形上
    2. Thales半圆：让60°<90°成为几何位置，不是标签
    3. gap放大镜：8-12×放大月牙缺口
    4. 配色：rust表示失败，sage表示成功

    【视觉叙事】点C落在Thales半圆外 → 60°<90° → 直径圆失败
    """
    fig = plt.figure(figsize=FIGURE_CONFIG['双栏'], dpi=FIGURE_CONFIG['dpi'])

    # 主画布背景色
    fig.patch.set_facecolor(PALETTE_A['paper'])

    ax = plt.subplot(1, 1, 1)
    ax.set_facecolor(PALETTE_A['paper'])

    # 等边三角形参数
    side = 100  # 边长
    vertices = np.array([
        [0, 0],
        [side, 0],
        [side/2, side*np.sqrt(3)/2]
    ])

    # ===== 核心几何元素 =====

    # 1. 等边三角形（主轮廓）
    triangle = MplPolygon(vertices, fill=False,
                         edgecolor=PALETTE_A['ink'],
                         linewidth=LINEWIDTH['main'])
    ax.add_patch(triangle)

    # 顶点标注
    labels = ['A', 'B', 'C']
    offsets = [(-8, -12), (8, -12), (0, 8)]
    for i, (v, label, offset) in enumerate(zip(vertices, labels, offsets)):
        ax.plot(v[0], v[1], 'o', color=PALETTE_A['ink'], markersize=5)
        ax.text(v[0]+offset[0], v[1]+offset[1], label,
               fontsize=11, ha='center', weight='bold',
               color=PALETTE_A['ink'])

    # 2. 直径（底边AB）
    p1, p2 = vertices[0], vertices[1]
    D = np.linalg.norm(p2 - p1)
    center_D = (p1 + p2) / 2
    R_D = D / 2

    # 标注直径
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]],
           color=PALETTE_A['ochre'], linewidth=LINEWIDTH['main']+0.5)
    mid_D = (p1 + p2) / 2
    ax.text(mid_D[0], mid_D[1]-8, r'$D$',
           fontsize=11, ha='center', weight='bold',
           color=PALETTE_A['ochre'])

    # 3. 【关键创新1】Thales半圆（∠=90°的轨迹）
    # 以AB为直径的半圆，所有满足∠ACB=90°的点C都在这个半圆上
    thales_circle = Circle(center_D, R_D, fill=False,
                          edgecolor=PALETTE_A['slate'],
                          linewidth=LINEWIDTH['theory'],
                          linestyle='--',
                          label='Thales locus (90°)')
    ax.add_patch(thales_circle)

    # 在半圆上标注90°
    angle_90_point = center_D + R_D * np.array([0, 1])
    ax.text(angle_90_point[0], angle_90_point[1]+5, '90°',
           fontsize=9, ha='center', color=PALETTE_A['slate'])

    # 4. 直径圆（失败，用虚线rust）
    circle_D = Circle(center_D, R_D, fill=False,
                     edgecolor=PALETTE_A['rust'],
                     linewidth=LINEWIDTH['theory'],
                     linestyle=':',
                     alpha=0.7,
                     label='Diameter circle (fails)')
    ax.add_patch(circle_D)

    # 5. 外接圆（成功，用实线sage）
    center_MEC = np.array([side/2, side/(2*np.sqrt(3))])
    R_MEC = side / np.sqrt(3)

    circle_MEC = Circle(center_MEC, R_MEC, fill=False,
                       edgecolor=PALETTE_A['sage'],
                       linewidth=LINEWIDTH['main'],
                       linestyle='-',
                       alpha=0.8,
                       label='MEC (covers)')
    ax.add_patch(circle_MEC)

    # 外接圆圆心标注
    ax.plot(center_MEC[0], center_MEC[1], '+',
           color=PALETTE_A['sage'], markersize=8, markeredgewidth=1.5)

    # 6. 【关键创新2】点C到Thales半圆的距离（gap的几何本质）
    p3 = vertices[2]
    dist_to_thales = np.linalg.norm(p3 - center_D) - R_D

    # 从C点向Thales半圆画垂线
    direction = (p3 - center_D) / np.linalg.norm(p3 - center_D)
    thales_point = center_D + R_D * direction

    ax.plot([thales_point[0], p3[0]], [thales_point[1], p3[1]],
           color=PALETTE_A['rust'], linewidth=LINEWIDTH['theory'],
           linestyle='-', alpha=0.6)

    # gap标注
    gap_mid = (thales_point + p3) / 2
    ax.text(gap_mid[0]+8, gap_mid[1], f'gap={dist_to_thales:.1f}m',
           fontsize=8, color=PALETTE_A['rust'],
           bbox=dict(boxstyle='round,pad=0.3',
                    facecolor=PALETTE_A['paper'],
                    edgecolor=PALETTE_A['rust'],
                    linewidth=0.8))

    # 7. 【关键创新3】60°标注（不是普通annotation，是视觉中心）
    # 在顶点C处标注实际角度
    ax.text(p3[0], p3[1]-15, r'$\angle ACB = 60°$',
           fontsize=12, ha='center', weight='bold',
           color=PALETTE_A['rust'],
           bbox=dict(boxstyle='round,pad=0.4',
                    facecolor='white',
                    edgecolor=PALETTE_A['rust'],
                    linewidth=1.5))

    # 8. 【关键创新4】Inset放大镜 - 放大gap区域
    # 创建inset（右上角，8x放大）
    axins = inset_axes(ax, width="35%", height="35%",
                       loc='upper right',
                       bbox_to_anchor=(0.05, 0.05, 1, 1),
                       bbox_transform=ax.transAxes)

    axins.set_facecolor(PALETTE_A['paper'])

    # 放大区域：C点附近
    zoom_range = 15
    axins.set_xlim(p3[0]-zoom_range, p3[0]+zoom_range)
    axins.set_ylim(thales_point[1]-zoom_range, p3[1]+zoom_range)

    # 在inset中绘制放大的gap
    # 三角形边
    edge1 = np.array([vertices[0], vertices[2]])
    edge2 = np.array([vertices[1], vertices[2]])
    axins.plot(edge1[:, 0], edge1[:, 1], color=PALETTE_A['ink'],
              linewidth=LINEWIDTH['main'])
    axins.plot(edge2[:, 0], edge2[:, 1], color=PALETTE_A['ink'],
              linewidth=LINEWIDTH['main'])

    # 直径圆弧（局部）
    theta1 = np.rad2deg(np.arctan2(p3[1]-center_D[1], p3[0]-center_D[0]))
    arc_D = Arc(center_D, 2*R_D, 2*R_D, angle=0,
               theta1=theta1-30, theta2=theta1+30,
               color=PALETTE_A['rust'], linewidth=LINEWIDTH['theory'],
               linestyle=':')
    axins.add_patch(arc_D)

    # Thales半圆弧（局部）
    axins.plot([thales_point[0], p3[0]], [thales_point[1], p3[1]],
              color=PALETTE_A['rust'], linewidth=2, linestyle='-')

    # gap填充
    # 绘制月牙形gap区域
    n_points = 50
    angles = np.linspace(theta1-25, theta1+25, n_points)
    circle_arc = center_D[:, np.newaxis] + R_D * np.array([
        np.cos(np.deg2rad(angles)),
        np.sin(np.deg2rad(angles))
    ])

    # 填充gap
    gap_region = MplPolygon(
        np.column_stack([circle_arc[0], circle_arc[1]]),
        facecolor=PALETTE_A['rust'], alpha=0.25,
        edgecolor='none', hatch='///')
    axins.add_patch(gap_region)

    # inset中的标注
    axins.text(p3[0], p3[1]+8, '60° < 90°',
              fontsize=8, ha='center', weight='bold',
              color=PALETTE_A['rust'])

    axins.set_xticks([])
    axins.set_yticks([])
    for spine in axins.spines.values():
        spine.set_edgecolor(PALETTE_A['rust'])
        spine.set_linewidth(1.2)

    # 用ConnectionPatch连接主图和inset
    con1 = ConnectionPatch(xyA=(p3[0]-12, p3[1]-5), coordsA=ax.transData,
                          xyB=(p3[0]-zoom_range, p3[1]+zoom_range), coordsB=axins.transData,
                          color=PALETTE_A['rust'], linewidth=0.8, linestyle='--', alpha=0.5)
    fig.add_artist(con1)

    con2 = ConnectionPatch(xyA=(p3[0]+12, p3[1]-5), coordsA=ax.transData,
                          xyB=(p3[0]+zoom_range, p3[1]+zoom_range), coordsB=axins.transData,
                          color=PALETTE_A['rust'], linewidth=0.8, linestyle='--', alpha=0.5)
    fig.add_artist(con2)

    # ===== 主图设置 =====
    ax.set_xlim(-20, 120)
    ax.set_ylim(-25, 110)
    ax.set_aspect('equal')

    # 去除上边框和右边框（顶刊标准）
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # 稀疏刻度，不要网格
    ax.set_xlabel('X (m)', fontsize=9, color=PALETTE_A['slate'])
    ax.set_ylabel('Y (m)', fontsize=9, color=PALETTE_A['slate'])

    # 图例（简洁，放左上）
    ax.legend(loc='upper left', fontsize=7, frameon=True,
             facecolor=PALETTE_A['paper'], edgecolor=PALETTE_A['slate'],
             framealpha=0.9)

    # 核心结论直接写在图上（不用大标题）
    ax.text(50, 95,
           'Vertex C falls outside Thales circle\n' + r'$\Rightarrow$ diameter circle fails to cover',
           fontsize=9, ha='center',
           bbox=dict(boxstyle='round,pad=0.5',
                    facecolor=PALETTE_A['paper'],
                    edgecolor=PALETTE_A['slate'],
                    linewidth=0.8, alpha=0.95))

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # 同时导出SVG和PNG
    plt.savefig(save_path, dpi=FIGURE_CONFIG['dpi'],
               bbox_inches='tight', facecolor=PALETTE_A['paper'])
    plt.savefig(save_path.replace('.png', '.svg'),
               bbox_inches='tight', facecolor=PALETTE_A['paper'])

    print(f"✓ 图2 v2已保存: {save_path}")
    print(f"✓ SVG版本: {save_path.replace('.png', '.svg')}")
    plt.close()


# ============================================================================
# 主函数
# ============================================================================

def generate_improved_figures():
    """
    【思路】按审核意见，先重做图2（最小可验证版本）
    若通过，再依次改进其他图
    """
    print("=" * 60)
    print("Q1图表重构 - 基于专业审核意见")
    print("配色方案：Ink & Ochre (方案A)")
    print("=" * 60)

    print("\n开始生成图2（Thales半圆 + gap放大镜）...")
    plot_figure2_counterexample_v2()

    print("\n=" * 60)
    print("✅ 最小可验证版本完成")
    print("请查看效果后再继续改进其他图")
    print("=" * 60)


if __name__ == "__main__":
    generate_improved_figures()
