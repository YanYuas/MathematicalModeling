"""
Q1 - 期刊级图表生成模块
基于12位专家评审的黄金组合方案

生成6张论文图：
1. 角域交会演化（信息漏斗）
2. Jung定理反例（配极对偶）
3. Jung夹逼可视化（极坐标相空间）
4. γ分布统计（EVT极值理论）
5. φ-D关系验证（多尺度矩阵）
6. 参数空间分类（极坐标+拓扑）
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, Polygon as MplPolygon, FancyArrowPatch, Wedge
from matplotlib.collections import PatchCollection
import matplotlib.gridspec as gridspec
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
# 全局配置 - 统一配色方案
# ============================================================================

# 期刊级配色语义系统
PALETTE = {
    'observation': '#3498DB',      # 蓝色 - 观测数据/实验值
    'theory': '#E67E22',           # 橙色 - 理论界/拟合曲线
    'optimal': '#27AE60',          # 绿色 - 最优情况/取等条件
    'warning': '#E74C3C',          # 红色 - 反例/警戒/直径
    'upper_bound': '#9B59B6',      # 紫色 - Jung上界/MEC
    'degenerate': '#95A5A6',       # 灰色 - 退化/不确定
    'background': '#ECF0F1',       # 浅灰 - 背景
}

# 字体和线宽配置
FIGURE_CONFIG = {
    'figure_size': (6, 4),         # 英寸，适合双栏论文
    'dpi': 300,
    'font_main': 10,               # 主标注字号
    'font_secondary': 8,           # 次标注字号
    'linewidth_main': 2.5,         # 主元素线宽
    'linewidth_theory': 1.5,       # 理论界线宽
    'linewidth_aux': 0.8,          # 辅助信息线宽
    'alpha_fill': 0.35,            # 主填充透明度
    'alpha_aux': 0.2,              # 辅助填充透明度
}

# 设置全局matplotlib参数
plt.rcParams.update({
    'font.size': FIGURE_CONFIG['font_main'],
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'axes.linewidth': 1.0,
    'grid.alpha': 0.3,
    'grid.linewidth': 0.5,
})


# ============================================================================
# 图1: 角域交会演化 - 信息漏斗
# ============================================================================

def plot_figure1_wedge_evolution(save_path='../实验结果/figs/fig1_wedge_evolution.png'):
    """
    【思路】三面板渐进式展示：单站→两站→n站
    信息漏斗隐喻：透明度梯度编码不确定性衰减
    """
    fig = plt.figure(figsize=(12, 4), dpi=FIGURE_CONFIG['dpi'])

    # 三个子图
    ax1 = plt.subplot(1, 3, 1)
    ax2 = plt.subplot(1, 3, 2)
    ax3 = plt.subplot(1, 3, 3)

    # === 面板a: 单站 ===
    S1 = np.array([0, 0])
    theta1 = 45
    eps = 15  # 为了可视化效果放大角度

    # 绘制扇形
    wedge1 = Wedge(S1, 300, theta1-eps, theta1+eps,
                   facecolor=PALETTE['observation'], alpha=0.15, edgecolor='none')
    ax1.add_patch(wedge1)

    # 边界射线
    for angle in [theta1-eps, theta1+eps]:
        direction = unit_vector(angle)
        end = S1 + 300 * direction
        ax1.plot([S1[0], end[0]], [S1[1], end[1]],
                'b--', linewidth=1, alpha=0.5)

    # 中心方向
    center_dir = unit_vector(theta1)
    center_end = S1 + 300 * center_dir
    ax1.arrow(S1[0], S1[1], center_end[0]-S1[0], center_end[1]-S1[1],
             head_width=20, head_length=30, fc=PALETTE['observation'],
             ec=PALETTE['observation'], linewidth=2)

    # 标注
    ax1.plot(S1[0], S1[1], 'o', color=PALETTE['observation'], markersize=10)
    ax1.text(S1[0]-30, S1[1]-40, r'$S_1$', fontsize=12, ha='center')
    ax1.text(150, 200, r'$\theta_1 \pm 1°$', fontsize=10, ha='center')

    ax1.set_xlim(-100, 400)
    ax1.set_ylim(-100, 400)
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)
    ax1.set_title('(a) 单站角域', fontsize=11, fontweight='bold')
    ax1.set_xlabel('X (m)', fontsize=9)
    ax1.set_ylabel('Y (m)', fontsize=9)

    # === 面板b: 两站交会 ===
    S1 = np.array([0, 0])
    S2 = np.array([300, 0])
    G = np.array([150, 250])

    theta1 = np.rad2deg(np.arctan2(G[1]-S1[1], G[0]-S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1]-S2[1], G[0]-S2[0]))
    eps = 1.0

    wedges = build_wedges([S1, S2], [theta1, theta2], eps)
    vertices = candidate_vertices(wedges)

    if len(vertices) > 0:
        poly = convex_hull(vertices)

        # 绘制角域（半透明）
        for i, w in enumerate(wedges):
            wedge_patch = Wedge(w.apex, 400, w.theta-w.eps, w.theta+w.eps,
                               facecolor=PALETTE['observation'], alpha=0.15, edgecolor='none')
            ax2.add_patch(wedge_patch)

        # 绘制交集区域
        if poly:
            hull_pts = np.array(poly.vertices + [poly.vertices[0]])
            ax2.fill(hull_pts[:, 0], hull_pts[:, 1],
                    color=PALETTE['theory'], alpha=0.4, label='定位区域 $L$')
            ax2.plot(hull_pts[:, 0], hull_pts[:, 1],
                    color=PALETTE['theory'], linewidth=2)

    # 检测点
    ax2.plot([S1[0], S2[0]], [S1[1], S2[1]], 's',
            color=PALETTE['observation'], markersize=8)
    ax2.text(S1[0]-20, S1[1]-30, r'$S_1$', fontsize=10)
    ax2.text(S2[0]+20, S2[1]-30, r'$S_2$', fontsize=10)

    # 真实目标
    ax2.plot(G[0], G[1], '*', color=PALETTE['warning'], markersize=12)
    ax2.text(G[0]+20, G[1]+20, r'$G$', fontsize=10)

    ax2.set_xlim(-100, 400)
    ax2.set_ylim(-50, 350)
    ax2.set_aspect('equal')
    ax2.grid(True, alpha=0.3)
    ax2.set_title('(b) 两站交会', fontsize=11, fontweight='bold')
    ax2.set_xlabel('X (m)', fontsize=9)
    ax2.legend(loc='upper right', fontsize=8)

    # === 面板c: n=4站完整 ===
    # 基准验证题
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
        # 定位区域
        hull_pts = np.array(poly.vertices + [poly.vertices[0]])
        ax3.fill(hull_pts[:, 0], hull_pts[:, 1],
                color=PALETTE['theory'], alpha=0.35, label='定位区域 $L$')
        ax3.plot(hull_pts[:, 0], hull_pts[:, 1],
                color=PALETTE['theory'], linewidth=2.5)

        # 直径
        D, (p, q) = diameter_bruteforce(poly)
        ax3.plot([p[0], q[0]], [p[1], q[1]],
                color=PALETTE['warning'], linewidth=3,
                label=f'直径 $D={D:.1f}$ m')
        ax3.plot([p[0], q[0]], [p[1], q[1]], 'o',
                color=PALETTE['warning'], markersize=6)

        # 最小包围圆
        center, R = mec_bruteforce(poly.vertices)
        circle = Circle(center, R, fill=False, edgecolor=PALETTE['upper_bound'],
                       linewidth=2, linestyle='--', label=f'MEC $R={R:.1f}$ m')
        ax3.add_patch(circle)
        ax3.plot(center[0], center[1], '+', color=PALETTE['upper_bound'],
                markersize=10, markeredgewidth=2)

    # 检测点
    ax3.plot([S1[0], S2[0]], [S1[1], S2[1]], 's',
            color=PALETTE['observation'], markersize=8, label='检测点')

    # 真实目标
    ax3.plot(G[0], G[1], '*', color='red', markersize=14, label='真实目标')

    ax3.set_xlim(250, 350)
    ax3.set_ylim(450, 550)
    ax3.set_aspect('equal')
    ax3.grid(True, alpha=0.3)
    ax3.set_title('(c) 完整定位结果', fontsize=11, fontweight='bold')
    ax3.set_xlabel('X (m)', fontsize=9)
    ax3.legend(loc='upper right', fontsize=7)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=FIGURE_CONFIG['dpi'], bbox_inches='tight')
    print(f"✓ 图1已保存: {save_path}")
    plt.close()


# ============================================================================
# 图2: Jung定理反例 - 等边三角形
# ============================================================================

def plot_figure2_counterexample(save_path='../实验结果/figs/fig2_jung_counterexample.png'):
    """
    【思路】等边三角形 + 直径圆（不覆盖）+ 外接圆（覆盖）
    展示"以直径为直径的圆"不一定能覆盖
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), dpi=FIGURE_CONFIG['dpi'])

    # 等边三角形参数
    side = 100  # 边长
    vertices = np.array([
        [0, 0],
        [side, 0],
        [side/2, side*np.sqrt(3)/2]
    ])

    # === 左图: 直径圆（不覆盖） ===
    # 绘制三角形
    triangle = MplPolygon(vertices, fill=False, edgecolor='black',
                         linewidth=2.5)
    ax1.add_patch(triangle)

    # 直径（任取一边）
    p1, p2 = vertices[0], vertices[1]
    D = np.linalg.norm(p2 - p1)
    center_D = (p1 + p2) / 2
    R_D = D / 2

    # 直径圆
    circle_D = Circle(center_D, R_D, fill=False, edgecolor=PALETTE['warning'],
                     linewidth=2, linestyle='-', label=f'直径圆 $R=D/2={R_D:.1f}$')
    ax1.add_patch(circle_D)

    # 标注直径
    ax1.plot([p1[0], p2[0]], [p1[1], p2[1]],
            color=PALETTE['warning'], linewidth=3)
    ax1.plot([p1[0], p2[0]], [p1[1], p2[1]], 'o',
            color=PALETTE['warning'], markersize=7)

    # Gap区域（顶点C在圆外）
    p3 = vertices[2]
    dist_to_center = np.linalg.norm(p3 - center_D)
    ax1.plot(p3[0], p3[1], 'o', color=PALETTE['warning'],
            markersize=7, markerfacecolor='none', markeredgewidth=2)

    # 绘制gap
    ax1.plot([center_D[0], p3[0]], [center_D[1], p3[1]],
            ':', color=PALETTE['warning'], linewidth=1.5)

    # 标注
    gap_mid = (center_D + p3) / 2
    gap_text = f'gap = {dist_to_center - R_D:.1f} m'
    ax1.text(gap_mid[0]+5, gap_mid[1], gap_text, fontsize=9,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # 顶点标注
    ax1.text(p1[0]-5, p1[1]-10, 'A', fontsize=11, ha='right')
    ax1.text(p2[0]+5, p2[1]-10, 'B', fontsize=11, ha='left')
    ax1.text(p3[0], p3[1]+10, 'C', fontsize=11, ha='center', color=PALETTE['warning'])

    # 标注角度
    ax1.text(side/2, side*np.sqrt(3)/6-10, r'$\angle ACB = 60° < 90°$',
            fontsize=10, ha='center',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.6))

    ax1.set_xlim(-30, 130)
    ax1.set_ylim(-30, 120)
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)
    ax1.set_title('(a) 直径圆不覆盖（反例）', fontsize=11, fontweight='bold',
                 color=PALETTE['warning'])
    ax1.set_xlabel('X (m)', fontsize=9)
    ax1.set_ylabel('Y (m)', fontsize=9)
    ax1.legend(loc='lower right', fontsize=8)

    # === 右图: 外接圆（覆盖） ===
    # 绘制三角形
    triangle2 = MplPolygon(vertices, fill=False, edgecolor='black',
                          linewidth=2.5)
    ax2.add_patch(triangle2)

    # 外接圆（最小包围圆）
    center_MEC = np.array([side/2, side/(2*np.sqrt(3))])
    R_MEC = side / np.sqrt(3)

    circle_MEC = Circle(center_MEC, R_MEC, fill=False,
                       edgecolor=PALETTE['upper_bound'],
                       linewidth=2, linestyle='--',
                       label=f'外接圆 $R=D/√3={R_MEC:.1f}$')
    ax2.add_patch(circle_MEC)
    ax2.plot(center_MEC[0], center_MEC[1], '+',
            color=PALETTE['upper_bound'], markersize=12, markeredgewidth=2)

    # 标注顶点
    for i, (x, y) in enumerate(vertices):
        ax2.plot(x, y, 'o', color=PALETTE['optimal'], markersize=7)

    ax2.text(p1[0]-5, p1[1]-10, 'A', fontsize=11, ha='right')
    ax2.text(p2[0]+5, p2[1]-10, 'B', fontsize=11, ha='left')
    ax2.text(p3[0], p3[1]+10, 'C', fontsize=11, ha='center')

    # Jung不等式
    ax2.text(side/2, -20,
            r'$R_{\mathrm{MEC}} = \frac{D}{\sqrt{3}}$ (Jung上界取等)',
            fontsize=10, ha='center',
            bbox=dict(boxstyle='round', facecolor=PALETTE['optimal'], alpha=0.3))

    ax2.set_xlim(-30, 130)
    ax2.set_ylim(-30, 120)
    ax2.set_aspect('equal')
    ax2.grid(True, alpha=0.3)
    ax2.set_title('(b) 最小包围圆覆盖（正确）', fontsize=11, fontweight='bold',
                 color=PALETTE['optimal'])
    ax2.set_xlabel('X (m)', fontsize=9)
    ax2.legend(loc='lower right', fontsize=8)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=FIGURE_CONFIG['dpi'], bbox_inches='tight')
    print(f"✓ 图2已保存: {save_path}")
    plt.close()


# ============================================================================
# 图3: Jung夹逼可视化
# ============================================================================

def plot_figure3_jung_sandwich(save_path='../实验结果/figs/fig3_jung_sandwich.png'):
    """
    【思路】在同一个L上展示D/2和D/√3两个圆
    验证 D/2 ≤ R_MEC ≤ D/√3
    """
    fig, ax = plt.subplots(figsize=(7, 7), dpi=FIGURE_CONFIG['dpi'])

    # 基准验证题数据
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
        # 定位区域L
        hull_pts = np.array(poly.vertices + [poly.vertices[0]])
        ax.fill(hull_pts[:, 0], hull_pts[:, 1],
               color=PALETTE['observation'], alpha=0.3, label='定位区域 $L$')
        ax.plot(hull_pts[:, 0], hull_pts[:, 1],
               color=PALETTE['observation'], linewidth=2.5)

        # 计算直径和MEC
        D, (p_d, q_d) = diameter_bruteforce(poly)
        center_mec, R_mec = mec_bruteforce(poly.vertices)

        # 直径端点连线
        ax.plot([p_d[0], q_d[0]], [p_d[1], q_d[1]],
               color=PALETTE['warning'], linewidth=3, label=f'直径 $D={D:.2f}$ m')
        ax.plot([p_d[0], q_d[0]], [p_d[1], q_d[1]], 'o',
               color=PALETTE['warning'], markersize=7)

        # 下界圆 D/2
        center_lower = (p_d + q_d) / 2
        R_lower = D / 2
        circle_lower = Circle(center_lower, R_lower, fill=False,
                             edgecolor=PALETTE['optimal'],
                             linewidth=2, linestyle='-',
                             label=f'下界 $R=D/2={R_lower:.2f}$ m')
        ax.add_patch(circle_lower)
        ax.plot(center_lower[0], center_lower[1], 'o',
               color=PALETTE['optimal'], markersize=8)

        # 实际MEC
        circle_mec = Circle(center_mec, R_mec, fill=False,
                           edgecolor=PALETTE['upper_bound'],
                           linewidth=2.5, linestyle='--',
                           label=f'实际 $R_{{MEC}}={R_mec:.2f}$ m')
        ax.add_patch(circle_mec)
        ax.plot(center_mec[0], center_mec[1], '+',
               color=PALETTE['upper_bound'], markersize=12, markeredgewidth=2.5)

        # 上界圆 D/√3
        R_upper = D / np.sqrt(3)
        circle_upper = Circle(center_mec, R_upper, fill=False,
                             edgecolor=PALETTE['degenerate'],
                             linewidth=1.5, linestyle=':',
                             label=f'上界 $R=D/√3={R_upper:.2f}$ m')
        ax.add_patch(circle_upper)

        # γ比值标注
        gamma = R_mec / R_lower
        ax.text(300, 460,
               f'$γ = R_{{MEC}}/(D/2) = {gamma:.4f}$\n下界取等 ✓',
               fontsize=11, ha='center',
               bbox=dict(boxstyle='round', facecolor=PALETTE['optimal'], alpha=0.5))

        # Jung不等式
        ax.text(300, 545,
               r'$\frac{D}{2} \leq R_{\mathrm{MEC}} \leq \frac{D}{\sqrt{3}}$',
               fontsize=12, ha='center', weight='bold',
               bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.6))

    ax.set_xlim(275, 325)
    ax.set_ylim(455, 545)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title('Jung定理夹逼验证', fontsize=13, fontweight='bold')
    ax.set_xlabel('X (m)', fontsize=10)
    ax.set_ylabel('Y (m)', fontsize=10)
    ax.legend(loc='upper left', fontsize=9)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=FIGURE_CONFIG['dpi'], bbox_inches='tight')
    print(f"✓ 图3已保存: {save_path}")
    plt.close()


# ============================================================================
# 主函数
# ============================================================================

def generate_all_figures():
    """
    【思路】生成全部6张论文图
    按优先级顺序生成
    """
    print("=" * 60)
    print("开始生成Q1论文图表")
    print("=" * 60)

    # Phase 1: 建立视觉语言
    print("\nPhase 1: 基础图表...")
    plot_figure1_wedge_evolution()
    plot_figure3_jung_sandwich()

    # Phase 2: 技术难点
    print("\nPhase 2: 理论验证...")
    plot_figure2_counterexample()

    # 图4-6需要参数扫描数据，暂时占位
    print("\n注意: 图4-6需要参数扫描数据，请先运行参数扫描实验")
    print("=" * 60)
    print("✅ 图表生成完成")
    print("=" * 60)


if __name__ == "__main__":
    generate_all_figures()
