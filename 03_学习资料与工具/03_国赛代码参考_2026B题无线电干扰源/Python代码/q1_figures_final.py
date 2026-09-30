"""
Q1图表 - 最终美化版（完整6张）
基于Ink & Ochre配色方案 + 专业审核意见

设计原则：
1. 一张图一个结论
2. 克制底色 + 单一强调色
3. 非对称英雄面板
4. 数据保持不变，只改视觉
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, Polygon as MplPolygon, Wedge, Arc, FancyArrowPatch
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.patches import ConnectionPatch
import matplotlib.gridspec as gridspec
from typing import List, Tuple
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from q1_main import (
    build_wedges, candidate_vertices, convex_hull,
    diameter_bruteforce, mec_bruteforce, unit_vector
)

# ============================================================================
# 全局配色 - Ink & Ochre (方案A)
# ============================================================================

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
FIG_通栏 = (7.1, 4.5)
FIG_双栏 = (3.4, 2.6)
DPI = 300

plt.rcParams.update({
    'font.size': 9,
    'font.family': 'sans-serif',
    'axes.linewidth': 0.8,
    'axes.edgecolor': PALETTE['slate'],
    'text.color': PALETTE['ink'],
    'xtick.color': PALETTE['slate'],
    'ytick.color': PALETTE['slate'],
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
})


# ============================================================================
# 图1: 角域交会演化 - 右主左辅布局
# ============================================================================

def plot_figure1_final(save_path='../实验结果/figs/fig1_final.png'):
    """
    【设计意图】右栏英雄面板展示完整交会，左栏两格展示演化过程
    【视觉叙事】不确定性从左到右收敛成精确定位
    """
    fig = plt.figure(figsize=FIG_通栏, dpi=DPI, facecolor=PALETTE['paper'])

    gs = gridspec.GridSpec(2, 3, width_ratios=[1, 1, 2.2], hspace=0.3, wspace=0.3)
    ax_left_top = plt.subplot(gs[0, 0])
    ax_left_bot = plt.subplot(gs[1, 0])
    ax_hero = plt.subplot(gs[:, 1:])

    for ax in [ax_left_top, ax_left_bot, ax_hero]:
        ax.set_facecolor(PALETTE['paper'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    # === 左上：单站角域 ===
    S1 = np.array([0, 0])
    theta1, eps = 45, 15

    wedge1 = Wedge(S1, 250, theta1-eps, theta1+eps,
                   facecolor=PALETTE['field'], alpha=0.12, edgecolor='none')
    ax_left_top.add_patch(wedge1)

    for angle in [theta1-eps, theta1+eps]:
        direction = unit_vector(angle)
        end = S1 + 250 * direction
        ax_left_top.plot([S1[0], end[0]], [S1[1], end[1]],
                        color=PALETTE['geometry'], linewidth=LW['aux'], linestyle='--', alpha=0.5)

    ax_left_top.plot(S1[0], S1[1], 'o', color=PALETTE['geometry'], markersize=6)
    ax_left_top.text(S1[0]-20, S1[1]-30, r'$S_1$', fontsize=9)
    ax_left_top.text(130, 150, 'wide\nuncertainty', fontsize=8, ha='center', style='italic',
                    color=PALETTE['slate'])

    ax_left_top.set_xlim(-50, 300)
    ax_left_top.set_ylim(-50, 300)
    ax_left_top.set_aspect('equal')
    ax_left_top.set_xticks([])
    ax_left_top.set_yticks([])
    ax_left_top.text(0.05, 0.95, 'a', transform=ax_left_top.transAxes,
                    fontsize=11, weight='bold', va='top')

    # === 左下：两站交会 ===
    S1 = np.array([0, 0])
    S2 = np.array([200, 0])
    G = np.array([100, 170])

    theta1 = np.rad2deg(np.arctan2(G[1]-S1[1], G[0]-S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1]-S2[1], G[0]-S2[0]))
    eps = 8

    wedges = build_wedges([S1, S2], [theta1, theta2], eps)
    vertices = candidate_vertices(wedges)

    if len(vertices) > 0:
        poly = convex_hull(vertices)
        if poly:
            hull_pts = np.array(poly.vertices + [poly.vertices[0]])
            ax_left_bot.fill(hull_pts[:, 0], hull_pts[:, 1],
                           color=PALETTE['field'], alpha=0.28)
            ax_left_bot.plot(hull_pts[:, 0], hull_pts[:, 1],
                           color=PALETTE['geometry'], linewidth=LW['theory'])

    ax_left_bot.plot([S1[0], S2[0]], [S1[1], S2[1]], 's',
                    color=PALETTE['geometry'], markersize=5)
    ax_left_bot.text(100, 200, 'narrowing', fontsize=8, ha='center',
                    style='italic', color=PALETTE['slate'])

    ax_left_bot.set_xlim(-30, 230)
    ax_left_bot.set_ylim(-30, 230)
    ax_left_bot.set_aspect('equal')
    ax_left_bot.set_xticks([])
    ax_left_bot.set_yticks([])
    ax_left_bot.text(0.05, 0.95, 'b', transform=ax_left_bot.transAxes,
                    fontsize=11, weight='bold', va='top')

    # === 右侧：英雄面板 - 完整交会结果 ===
    S1 = np.array([0.0, 0.0])
    S2 = np.array([600.0, 0.0])
    G = np.array([300.0, 500.0])

    theta1 = np.rad2deg(np.arctan2(G[1]-S1[1], G[0]-S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1]-S2[1], G[0]-S2[0]))
    eps = 1.0

    wedges = build_wedges([S1, S2], [theta1, theta2], eps)
    vertices = candidate_vertices(wedges)
    poly = convex_hull(vertices)

    if poly:
        hull_pts = np.array(poly.vertices + [poly.vertices[0]])
        ax_hero.fill(hull_pts[:, 0], hull_pts[:, 1],
                    color=PALETTE['field'], alpha=0.55,
                    label='Localization region $L$')
        ax_hero.plot(hull_pts[:, 0], hull_pts[:, 1],
                    color=PALETTE['geometry'], linewidth=LW['main'])

        D, (p, q) = diameter_bruteforce(poly)
        ax_hero.plot([p[0], q[0]], [p[1], q[1]],
                    color=PALETTE['ochre'], linewidth=LW['main']+0.5,
                    label=f'Diameter $D={D:.1f}$ m')
        ax_hero.plot([p[0], q[0]], [p[1], q[1]], 'o',
                    color=PALETTE['ochre'], markersize=6)

        center, R = mec_bruteforce(poly.vertices)
        circle = Circle(center, R, fill=False, edgecolor=PALETTE['sage'],
                       linewidth=LW['theory'], linestyle='--',
                       label=f'MEC $R={R:.1f}$ m')
        ax_hero.add_patch(circle)
        ax_hero.plot(center[0], center[1], '+', color=PALETTE['sage'],
                    markersize=10, markeredgewidth=LW['theory'])

    ax_hero.plot([S1[0], S2[0]], [S1[1], S2[1]], 's',
                color=PALETTE['geometry'], markersize=7, label='Stations')
    ax_hero.plot(G[0], G[1], '*', color=PALETTE['rust'], markersize=12, label='True target')

    ax_hero.set_xlim(270, 330)
    ax_hero.set_ylim(465, 525)
    ax_hero.set_aspect('equal')
    ax_hero.set_xlabel('X (m)', fontsize=9)
    ax_hero.set_ylabel('Y (m)', fontsize=9)
    ax_hero.legend(loc='upper left', fontsize=7, frameon=True,
                  facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'])
    ax_hero.text(0.05, 0.95, 'c', transform=ax_hero.transAxes,
                fontsize=11, weight='bold', va='top')

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=DPI, bbox_inches='tight', facecolor=PALETTE['paper'])
    plt.savefig(save_path.replace('.png', '.svg'), bbox_inches='tight', facecolor=PALETTE['paper'])
    print(f"✓ 图1已保存: {save_path}")
    plt.close()


# ============================================================================
# 图3: Jung夹逼 - 60°扇区剖开
# ============================================================================

def plot_figure3_final(save_path='../实验结果/figs/fig3_final.png'):
    """
    【设计意图】扇区剖面展示夹逼厚度，右侧半径尺量化
    【视觉叙事】D/2 ≤ R_MEC ≤ D/√3 变成可见的环带
    """
    fig, (ax_sector, ax_ruler) = plt.subplots(1, 2, figsize=FIG_双栏,
                                               gridspec_kw={'width_ratios': [2.5, 1]},
                                               dpi=DPI, facecolor=PALETTE['paper'])

    ax_sector.set_facecolor(PALETTE['paper'])
    ax_ruler.set_facecolor(PALETTE['paper'])

    # 基准数据
    S1 = np.array([0.0, 0.0])
    S2 = np.array([600.0, 0.0])
    G = np.array([300.0, 500.0])

    theta1 = np.rad2deg(np.arctan2(G[1]-S1[1], G[0]-S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1]-S2[1], G[0]-S2[0]))
    eps = 1.0

    wedges = build_wedges([S1, S2], [theta1, theta2], eps)
    vertices = candidate_vertices(wedges)
    poly = convex_hull(vertices)

    if poly:
        D, (p_d, q_d) = diameter_bruteforce(poly)
        center_mec, R_mec = mec_bruteforce(poly.vertices)

        R_lower = D / 2
        R_upper = D / np.sqrt(3)

        # === 60°扇区（蛋糕切片） ===
        sector_angle = 60
        sector_start = 60

        # 下界环
        wedge_lower = Wedge(center_mec, R_lower, sector_start, sector_start+sector_angle,
                           facecolor=PALETTE['sage'], alpha=0.15,
                           edgecolor=PALETTE['sage'], linewidth=LW['theory'])
        ax_sector.add_patch(wedge_lower)

        # 实际MEC
        wedge_mec = Wedge(center_mec, R_mec, sector_start, sector_start+sector_angle,
                         facecolor=PALETTE['ochre'], alpha=0.25,
                         edgecolor=PALETTE['ochre'], linewidth=LW['main'])
        ax_sector.add_patch(wedge_mec)

        # 上界轮廓
        arc_upper = Arc(center_mec, 2*R_upper, 2*R_upper, angle=0,
                       theta1=sector_start, theta2=sector_start+sector_angle,
                       color=PALETTE['slate'], linewidth=LW['theory'], linestyle=':')
        ax_sector.add_patch(arc_upper)

        # 扇区边界射线
        for angle in [sector_start, sector_start+sector_angle]:
            rad = np.deg2rad(angle)
            end = center_mec + R_upper * 1.1 * np.array([np.cos(rad), np.sin(rad)])
            ax_sector.plot([center_mec[0], end[0]], [center_mec[1], end[1]],
                          color=PALETTE['ink'], linewidth=LW['aux'], alpha=0.4)

        # 圆心
        ax_sector.plot(center_mec[0], center_mec[1], '+',
                      color=PALETTE['ink'], markersize=8, markeredgewidth=1.5)

        # 标注
        mid_angle = sector_start + sector_angle/2
        rad_mid = np.deg2rad(mid_angle)

        label_r1 = center_mec + (R_lower*0.7) * np.array([np.cos(rad_mid), np.sin(rad_mid)])
        ax_sector.text(label_r1[0], label_r1[1], r'$D/2$', fontsize=9,
                      ha='center', color=PALETTE['sage'], weight='bold')

        label_r2 = center_mec + (R_mec*0.85) * np.array([np.cos(rad_mid), np.sin(rad_mid)])
        ax_sector.text(label_r2[0], label_r2[1], r'$R_{\mathrm{MEC}}$',
                      fontsize=10, ha='center', color=PALETTE['ochre'], weight='bold')

        label_r3 = center_mec + (R_upper*0.92) * np.array([np.cos(rad_mid), np.sin(rad_mid)])
        ax_sector.text(label_r3[0], label_r3[1], r'$D/\sqrt{3}$',
                      fontsize=9, ha='center', color=PALETTE['slate'])

        ax_sector.set_xlim(center_mec[0]-R_upper*1.2, center_mec[0]+R_upper*0.3)
        ax_sector.set_ylim(center_mec[1]-R_upper*0.3, center_mec[1]+R_upper*1.2)
        ax_sector.set_aspect('equal')
        ax_sector.spines['top'].set_visible(False)
        ax_sector.spines['right'].set_visible(False)
        ax_sector.set_xticks([])
        ax_sector.set_yticks([])
        ax_sector.set_title('60° sector view', fontsize=10, pad=10)

        # === 右侧：半径尺 ===
        ax_ruler.set_xlim(0, 1)
        ax_ruler.set_ylim(R_lower*0.95, R_upper*1.05)

        # 三个刻度
        y_vals = [R_lower, R_mec, R_upper]
        labels = [r'$D/2$', r'$R_{\mathrm{MEC}}$', r'$D/\sqrt{3}$']
        colors = [PALETTE['sage'], PALETTE['ochre'], PALETTE['slate']]

        for y, label, color in zip(y_vals, labels, colors):
            ax_ruler.axhline(y, color=color, linewidth=LW['theory'], linestyle='-')
            ax_ruler.text(0.5, y, f'{y:.2f} m', fontsize=8, ha='center',
                         va='bottom', color=color, weight='bold')
            ax_ruler.text(0.1, y, label, fontsize=9, ha='left', va='center',
                         color=color, weight='bold')

        # γ标注
        gamma = R_mec / R_lower
        ax_ruler.text(0.5, (R_lower+R_mec)/2,
                     f'$γ={gamma:.4f}$\nequality!',
                     fontsize=8, ha='center', style='italic',
                     bbox=dict(boxstyle='round,pad=0.4',
                              facecolor=PALETTE['sage'], alpha=0.2,
                              edgecolor=PALETTE['sage'], linewidth=0.8))

        ax_ruler.spines['top'].set_visible(False)
        ax_ruler.spines['right'].set_visible(False)
        ax_ruler.spines['bottom'].set_visible(False)
        ax_ruler.spines['left'].set_visible(False)
        ax_ruler.set_xticks([])
        ax_ruler.set_yticks([])
        ax_ruler.set_title('Radius scale', fontsize=10, pad=10)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=DPI, bbox_inches='tight', facecolor=PALETTE['paper'])
    plt.savefig(save_path.replace('.png', '.svg'), bbox_inches='tight', facecolor=PALETTE['paper'])
    print(f"✓ 图3已保存: {save_path}")
    plt.close()


# ============================================================================
# 主函数
# ============================================================================

def generate_all_final_figures():
    """生成所有最终美化版图表"""
    print("=" * 60)
    print("Q1图表 - 最终美化版生成")
    print("配色：Ink & Ochre | 数据：保持不变 | 视觉：全面优化")
    print("=" * 60)

    print("\n生成图1（角域交会演化 - 右主左辅）...")
    plot_figure1_final()

    print("\n生成图3（Jung夹逼 - 60°扇区剖开）...")
    plot_figure3_final()

    print("\n=" * 60)
    print("✅ 图1和图3最终版完成")
    print("图2已有重构版（q1_figures_v2.py）")
    print("图4-6需要参数扫描数据")
    print("=" * 60)


if __name__ == "__main__":
    generate_all_final_figures()
