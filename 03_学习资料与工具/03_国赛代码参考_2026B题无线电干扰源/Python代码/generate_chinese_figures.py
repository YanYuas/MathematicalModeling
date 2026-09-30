"""
Q1 中文图表生成脚本
基于交接文档要求生成4张P0优先级图表
配色：Ink & Ochre方案
分辨率：300 DPI
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, Wedge, Arc
import matplotlib.gridspec as gridspec
import sys
import os

# 添加q1_main.py所在路径
sys.path.insert(0, os.path.dirname(__file__))
from q1_main import (
    build_wedges, candidate_vertices, convex_hull,
    diameter_bruteforce, mec_bruteforce, unit_vector
)

# ============================================================================
# 中文字体配置（必读）
# ============================================================================
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['figure.dpi'] = 150
matplotlib.rcParams['savefig.dpi'] = 300

# ============================================================================
# Ink & Ochre 配色方案
# ============================================================================
PALETTE = {
    "ink": "#1C1C1C",        # 深墨色
    "slate": "#5B6B73",      # 板岩灰
    "paper": "#F7F4EE",      # 纸质底色
    "field": "#C5D4E0",      # 云灰
    "geometry": "#2C4A6E",   # 几何蓝
    "ochre": "#C47B2B",      # 赭石色
    "rust": "#8C3A2A",       # 锈红色
    "sage": "#4F6F5C",       # 鼠尾草绿
}

LW = {'main': 2.2, 'theory': 1.4, 'aux': 0.7}
DPI = 300
OUTPUT_DIR = '../实验结果/figs'

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# 图1：Q1_MAIN_01_角域示意.png（单站楔形）
# ============================================================================

def generate_figure_01():
    """
    单站角域楔形示意图
    展示单个检测站发出的2°角域
    """
    print("正在生成图1：单站角域示意...")

    fig, ax = plt.subplots(figsize=(7, 7), dpi=DPI, facecolor=PALETTE['paper'])
    ax.set_facecolor(PALETTE['paper'])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # 检测站位置
    S1 = np.array([0, 0])
    theta1 = 45  # 中心方向
    eps = 15     # 夸张的角度便于展示

    # 绘制楔形区域
    wedge = Wedge(S1, 250, theta1-eps, theta1+eps,
                  facecolor=PALETTE['field'], alpha=0.15, edgecolor='none')
    ax.add_patch(wedge)

    # 绘制边界射线
    for angle in [theta1-eps, theta1+eps]:
        direction = unit_vector(angle)
        end = S1 + 250 * direction
        ax.plot([S1[0], end[0]], [S1[1], end[1]],
                color=PALETTE['geometry'], linewidth=LW['theory'],
                linestyle='--', alpha=0.7)

    # 绘制中心射线
    direction = unit_vector(theta1)
    end = S1 + 250 * direction
    ax.plot([S1[0], end[0]], [S1[1], end[1]],
            color=PALETTE['ochre'], linewidth=LW['main'], alpha=0.8)

    # 标注检测站
    ax.plot(S1[0], S1[1], 'o', color=PALETTE['rust'], markersize=12)
    ax.text(S1[0]-20, S1[1]-30, r'检测站 $S_1$', fontsize=12,
            fontweight='bold', color=PALETTE['ink'])

    # 标注角度
    arc = Arc(S1, 80, 80, angle=0, theta1=theta1-eps, theta2=theta1+eps,
              color=PALETTE['ochre'], linewidth=2)
    ax.add_patch(arc)
    ax.text(50, 40, r'$2\epsilon = 2°$', fontsize=11, color=PALETTE['ochre'])

    # 标注不确定性
    ax.text(150, 180, '大不确定性\n（单站无法定位）', fontsize=11, ha='center',
            style='italic', color=PALETTE['slate'],
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                     edgecolor=PALETTE['slate'], alpha=0.8))

    # 标注射线
    ax.text(180, 220, r'$\theta + \epsilon$', fontsize=10, color=PALETTE['geometry'])
    ax.text(180, 120, r'$\theta - \epsilon$', fontsize=10, color=PALETTE['geometry'])

    ax.set_xlim(-50, 300)
    ax.set_ylim(-50, 300)
    ax.set_aspect('equal')
    ax.set_xlabel('X坐标 (m)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y坐标 (m)', fontsize=12, fontweight='bold')
    ax.set_title('单站角域示意图', fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.2, linestyle=':', color=PALETTE['slate'])

    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'Q1_MAIN_01_角域示意.png')
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight', facecolor=PALETTE['paper'])
    plt.savefig(output_path.replace('.png', '.svg'), bbox_inches='tight', facecolor=PALETTE['paper'])
    print(f"✓ 已保存: {output_path}")
    plt.close()


# ============================================================================
# 图2：Q1_MAIN_02_交会定位区域构造.png（两站交会）
# ============================================================================

def generate_figure_02():
    """
    两站交会定位区域构造
    展示完整的交会定位过程和结果
    """
    print("正在生成图2：两站交会定位区域构造...")

    # 基准算例数据
    S1 = np.array([0.0, 0.0])
    S2 = np.array([600.0, 0.0])
    G = np.array([300.0, 500.0])

    theta1 = np.rad2deg(np.arctan2(G[1]-S1[1], G[0]-S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1]-S2[1], G[0]-S2[0]))
    eps = 1.0

    fig, ax = plt.subplots(figsize=(10, 8), dpi=DPI, facecolor=PALETTE['paper'])
    ax.set_facecolor(PALETTE['paper'])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # 构造并绘制定位区域
    wedges = build_wedges([S1, S2], [theta1, theta2], eps)
    vertices = candidate_vertices(wedges)
    poly = convex_hull(vertices)

    if poly:
        hull_pts = np.array(poly.vertices + [poly.vertices[0]])
        ax.fill(hull_pts[:, 0], hull_pts[:, 1],
                color=PALETTE['field'], alpha=0.35, label='定位区域 $L$')
        ax.plot(hull_pts[:, 0], hull_pts[:, 1],
                color=PALETTE['geometry'], linewidth=LW['main'])

        # 标注顶点
        for i, v in enumerate(poly.vertices):
            ax.plot(v[0], v[1], 'o', color=PALETTE['geometry'], markersize=8)
            ax.text(v[0]+5, v[1]+8, f'V{i+1}\n({v[0]:.1f},{v[1]:.1f})',
                   fontsize=9, color=PALETTE['ink'])

        # 绘制直径
        D, (p, q) = diameter_bruteforce(poly)
        ax.plot([p[0], q[0]], [p[1], q[1]],
                color=PALETTE['ochre'], linewidth=LW['main']+0.5,
                label=f'直径 $D={D:.1f}$ m', zorder=10)
        ax.plot([p[0], q[0]], [p[1], q[1]], 'o',
                color=PALETTE['ochre'], markersize=8)

        # 绘制最小包围圆
        center, R = mec_bruteforce(poly.vertices)
        circle = Circle(center, R, fill=False, edgecolor=PALETTE['sage'],
                       linewidth=LW['theory'], linestyle='--',
                       label=f'最小包围圆 $R={R:.1f}$ m')
        ax.add_patch(circle)
        ax.plot(center[0], center[1], '+', color=PALETTE['sage'],
                markersize=12, markeredgewidth=2)

    # 绘制检测站
    ax.plot([S1[0], S2[0]], [S1[1], S2[1]], 's',
            color=PALETTE['geometry'], markersize=10, label='检测站', zorder=15)
    ax.text(S1[0]-20, S1[1]-25, '$S_1$', fontsize=12, fontweight='bold')
    ax.text(S2[0]+10, S2[1]-25, '$S_2$', fontsize=12, fontweight='bold')

    # 绘制真源
    ax.plot(G[0], G[1], '*', color=PALETTE['rust'], markersize=15,
            label='真源', zorder=15)
    ax.text(G[0]+10, G[1]+15, '真源 $G$', fontsize=11, color=PALETTE['rust'],
           fontweight='bold')

    # 绘制边界射线（虚线）
    for angle_offset in [-eps, eps]:
        for S, theta in [(S1, theta1), (S2, theta2)]:
            angle = theta + angle_offset
            direction = unit_vector(angle)
            end = S + 600 * direction
            ax.plot([S[0], end[0]], [S[1], end[1]],
                   color=PALETTE['geometry'], linewidth=LW['aux'],
                   linestyle=':', alpha=0.4)

    # 标注角度范围
    ax.text(100, 100, r'$\theta_1 \pm 1°$', fontsize=10,
           color=PALETTE['geometry'], style='italic')
    ax.text(500, 100, r'$\theta_2 \pm 1°$', fontsize=10,
           color=PALETTE['geometry'], style='italic')

    ax.set_xlim(270, 330)
    ax.set_ylim(465, 535)
    ax.set_aspect('equal')
    ax.set_xlabel('X坐标 (m)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y坐标 (m)', fontsize=12, fontweight='bold')
    ax.set_title('两站交会定位区域构造', fontsize=14, fontweight='bold', pad=15)
    ax.legend(loc='upper left', fontsize=10, frameon=True,
             facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'])
    ax.grid(True, alpha=0.2, linestyle=':', color=PALETTE['slate'])

    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'Q1_MAIN_02_交会定位区域构造.png')
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight', facecolor=PALETTE['paper'])
    plt.savefig(output_path.replace('.png', '.svg'), bbox_inches='tight', facecolor=PALETTE['paper'])
    print(f"✓ 已保存: {output_path}")
    plt.close()


# ============================================================================
# 图3：Q1_MAIN_03_等边三角形反例.png（Jung反例）
# ============================================================================

def generate_figure_03():
    """
    等边三角形反例
    展示直径圆无法覆盖、外接圆可以覆盖
    """
    print("正在生成图3：等边三角形反例...")

    fig, ax = plt.subplots(figsize=(9, 8), dpi=DPI, facecolor=PALETTE['paper'])
    ax.set_facecolor(PALETTE['paper'])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # 等边三角形（边长a=100）
    a = 100
    A = np.array([0, 0])
    B = np.array([a, 0])
    C = np.array([a/2, a*np.sqrt(3)/2])

    # 绘制三角形
    triangle = np.array([A, B, C, A])
    ax.plot(triangle[:, 0], triangle[:, 1],
           color=PALETTE['geometry'], linewidth=LW['main']+0.5, zorder=10)
    ax.fill(triangle[:-1, 0], triangle[:-1, 1],
           color=PALETTE['field'], alpha=0.15)

    # 标注顶点
    for point, label in [(A, 'A'), (B, 'B'), (C, 'C')]:
        ax.plot(point[0], point[1], 'o', color=PALETTE['ink'], markersize=10)
        offset = {'A': (-8, -12), 'B': (8, -12), 'C': (0, 8)}
        ax.text(point[0]+offset[label][0], point[1]+offset[label][1],
               label, fontsize=14, fontweight='bold', color=PALETTE['ink'])

    # 直径AB和直径圆（失败）
    D = a
    center_D = (A + B) / 2
    R_D = D / 2

    circle_D = Circle(center_D, R_D, fill=False, edgecolor=PALETTE['rust'],
                     linewidth=LW['theory'], linestyle='--', alpha=0.8,
                     label=f'直径圆 ($R=D/2={R_D:.1f}$) 无法覆盖')
    ax.add_patch(circle_D)

    # 标注直径
    ax.plot([A[0], B[0]], [A[1], B[1]], color=PALETTE['ochre'],
           linewidth=LW['main'], zorder=5)
    ax.text(a/2, -5, f'直径 $D={D:.1f}$', fontsize=11, ha='center',
           color=PALETTE['ochre'], fontweight='bold')

    # 外接圆（成功）
    R_circum = D / np.sqrt(3)
    center_circum = (A + B + C) / 3 + np.array([0, a/(2*np.sqrt(3))])

    circle_circum = Circle(center_circum, R_circum, fill=False,
                          edgecolor=PALETTE['sage'],
                          linewidth=LW['theory']+0.5, alpha=0.9,
                          label=f'外接圆 ($R=D/√3={R_circum:.1f}$) 覆盖')
    ax.add_patch(circle_circum)
    ax.plot(center_circum[0], center_circum[1], '+', color=PALETTE['sage'],
           markersize=12, markeredgewidth=2)

    # Thales轨迹（90°轨迹）
    theta_thales = np.linspace(0, np.pi, 100)
    x_thales = center_D[0] + R_D * np.cos(theta_thales)
    y_thales = center_D[1] + R_D * np.sin(theta_thales)
    ax.plot(x_thales, y_thales, color=PALETTE['slate'],
           linewidth=LW['aux'], linestyle=':', alpha=0.6,
           label='Thales轨迹 (90°)')

    # 标注关键角度
    # 从C到A和B的连线
    ax.plot([C[0], A[0]], [C[1], A[1]], color=PALETTE['slate'],
           linewidth=LW['aux'], linestyle=':', alpha=0.4)
    ax.plot([C[0], B[0]], [C[1], B[1]], color=PALETTE['slate'],
           linewidth=LW['aux'], linestyle=':', alpha=0.4)

    # 标注60°角
    arc_angle = Arc(C, 15, 15, angle=0, theta1=240, theta2=300,
                   color=PALETTE['rust'], linewidth=2)
    ax.add_patch(arc_angle)
    ax.text(C[0]-8, C[1]-12, '60° < 90°', fontsize=10, color=PALETTE['rust'],
           fontweight='bold')

    # 标注说明
    ax.text(a/2, a*np.sqrt(3)/2 + 25,
           '反例说明：顶点C落在直径圆外\n∠ACB = 60° < 90°（违反Thales判据）',
           fontsize=11, ha='center', color=PALETTE['ink'],
           bbox=dict(boxstyle='round,pad=0.6', facecolor='white',
                    edgecolor=PALETTE['ochre'], linewidth=2, alpha=0.9))

    ax.set_xlim(-15, 115)
    ax.set_ylim(-20, 110)
    ax.set_aspect('equal')
    ax.set_xlabel('X坐标', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y坐标', fontsize=12, fontweight='bold')
    ax.set_title('等边三角形反例：直径圆失败', fontsize=14, fontweight='bold', pad=15)
    ax.legend(loc='upper right', fontsize=10, frameon=True,
             facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'])
    ax.grid(True, alpha=0.2, linestyle=':', color=PALETTE['slate'])

    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'Q1_MAIN_03_等边三角形反例.png')
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight', facecolor=PALETTE['paper'])
    plt.savefig(output_path.replace('.png', '.svg'), bbox_inches='tight', facecolor=PALETTE['paper'])
    print(f"✓ 已保存: {output_path}")
    plt.close()


# ============================================================================
# 图4：Q1_MAIN_04_Jung夹逼图.png（三层圆）
# ============================================================================

def generate_figure_04():
    """
    Jung夹逼图
    展示D/2、R_MEC、D/√3三层圆的夹逼关系
    """
    print("正在生成图4：Jung夹逼图...")

    # 使用基准算例数据
    S1 = np.array([0.0, 0.0])
    S2 = np.array([600.0, 0.0])
    G = np.array([300.0, 500.0])

    theta1 = np.rad2deg(np.arctan2(G[1]-S1[1], G[0]-S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1]-S2[1], G[0]-S2[0]))
    eps = 1.0

    wedges = build_wedges([S1, S2], [theta1, theta2], eps)
    vertices = candidate_vertices(wedges)
    poly = convex_hull(vertices)

    if not poly:
        print("警告：无法构造定位区域")
        return

    D, (p_d, q_d) = diameter_bruteforce(poly)
    center_mec, R_mec = mec_bruteforce(poly.vertices)

    R_lower = D / 2
    R_upper = D / np.sqrt(3)

    fig, (ax_main, ax_scale) = plt.subplots(1, 2, figsize=(14, 7),
                                            gridspec_kw={'width_ratios': [2.5, 1]},
                                            dpi=DPI, facecolor=PALETTE['paper'])

    for ax in [ax_main, ax_scale]:
        ax.set_facecolor(PALETTE['paper'])

    # ===左图：主视图（定位区域+三层圆）===
    hull_pts = np.array(poly.vertices + [poly.vertices[0]])
    ax_main.fill(hull_pts[:, 0], hull_pts[:, 1],
                color=PALETTE['field'], alpha=0.25, label='定位区域 $L$')
    ax_main.plot(hull_pts[:, 0], hull_pts[:, 1],
                color=PALETTE['geometry'], linewidth=LW['main'])

    # 三层圆
    # 下界圆
    circle_lower = Circle(center_mec, R_lower, fill=False,
                         edgecolor=PALETTE['sage'],
                         linewidth=LW['theory']+0.5, linestyle='-',
                         label=f'下界 $D/2={R_lower:.2f}$ m', zorder=5)
    ax_main.add_patch(circle_lower)

    # 实际MEC
    circle_mec = Circle(center_mec, R_mec, fill=False,
                       edgecolor=PALETTE['ochre'],
                       linewidth=LW['main']+1, linestyle='-',
                       label=f'实际 $R_{{MEC}}={R_mec:.2f}$ m', zorder=6)
    ax_main.add_patch(circle_mec)

    # 上界圆
    circle_upper = Circle(center_mec, R_upper, fill=False,
                         edgecolor=PALETTE['slate'],
                         linewidth=LW['theory'], linestyle='--',
                         label=f'上界 $D/√3={R_upper:.2f}$ m', zorder=4)
    ax_main.add_patch(circle_upper)

    # 圆心
    ax_main.plot(center_mec[0], center_mec[1], '+',
                color=PALETTE['ink'], markersize=14, markeredgewidth=2.5)

    # 直径
    ax_main.plot([p_d[0], q_d[0]], [p_d[1], q_d[1]],
                color=PALETTE['ochre'], linewidth=LW['theory'],
                linestyle=':', alpha=0.6)
    ax_main.text((p_d[0]+q_d[0])/2, (p_d[1]+q_d[1])/2 - 3,
                f'$D={D:.2f}$ m', fontsize=10, ha='center',
                color=PALETTE['ochre'], fontweight='bold')

    ax_main.set_xlim(center_mec[0]-R_upper*1.3, center_mec[0]+R_upper*1.3)
    ax_main.set_ylim(center_mec[1]-R_upper*1.3, center_mec[1]+R_upper*1.3)
    ax_main.set_aspect('equal')
    ax_main.set_xlabel('X坐标 (m)', fontsize=12, fontweight='bold')
    ax_main.set_ylabel('Y坐标 (m)', fontsize=12, fontweight='bold')
    ax_main.set_title('Jung夹逼关系示意', fontsize=14, fontweight='bold', pad=15)
    ax_main.legend(loc='upper left', fontsize=10, frameon=True,
                  facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'])
    ax_main.grid(True, alpha=0.2, linestyle=':', color=PALETTE['slate'])

    # ===右图：半径尺度===
    ax_scale.set_xlim(0, 1)
    ax_scale.set_ylim(R_lower*0.95, R_upper*1.05)

    # 三个刻度线
    y_vals = [R_lower, R_mec, R_upper]
    labels = [r'$D/2$', r'$R_{\mathrm{MEC}}$', r'$D/\sqrt{3}$']
    colors = [PALETTE['sage'], PALETTE['ochre'], PALETTE['slate']]

    for y, label, color in zip(y_vals, labels, colors):
        ax_scale.axhline(y, color=color, linewidth=3, linestyle='-', alpha=0.8)
        ax_scale.text(0.5, y, f'{y:.2f} m', fontsize=11, ha='center',
                     va='bottom', color=color, fontweight='bold',
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor=color, linewidth=1.5, alpha=0.9))
        ax_scale.text(0.1, y, label, fontsize=12, ha='left', va='center',
                     color=color, fontweight='bold')

    # γ标注
    gamma = R_mec / R_lower
    mid_y = (R_lower + R_mec) / 2
    ax_scale.text(0.5, mid_y,
                 f'γ = {gamma:.4f}\n下界取等！',
                 fontsize=10, ha='center', style='italic',
                 color=PALETTE['sage'], fontweight='bold',
                 bbox=dict(boxstyle='round,pad=0.4',
                          facecolor=PALETTE['sage'], alpha=0.15,
                          edgecolor=PALETTE['sage'], linewidth=1.5))

    # Jung不等式区间标注
    ax_scale.annotate('', xy=(0.85, R_upper), xytext=(0.85, R_lower),
                     arrowprops=dict(arrowstyle='<->', color=PALETTE['ink'],
                                   linewidth=2))
    ax_scale.text(0.92, (R_lower+R_upper)/2, 'Jung区间', fontsize=10,
                 rotation=90, va='center', color=PALETTE['ink'],
                 fontweight='bold')

    ax_scale.spines['top'].set_visible(False)
    ax_scale.spines['right'].set_visible(False)
    ax_scale.spines['bottom'].set_visible(False)
    ax_scale.spines['left'].set_visible(False)
    ax_scale.set_xticks([])
    ax_scale.set_yticks([])
    ax_scale.set_title('半径尺度', fontsize=13, fontweight='bold', pad=15)

    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'Q1_MAIN_04_Jung夹逼图.png')
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight', facecolor=PALETTE['paper'])
    plt.savefig(output_path.replace('.png', '.svg'), bbox_inches='tight', facecolor=PALETTE['paper'])
    print(f"✓ 已保存: {output_path}")
    plt.close()


# ============================================================================
# 主函数
# ============================================================================

def main():
    """生成所有4张P0图表"""
    print("=" * 70)
    print("Q1 中文图表生成工具")
    print("配色：Ink & Ochre | 分辨率：300 DPI | 字体：SimHei/Microsoft YaHei")
    print("=" * 70)
    print()

    try:
        generate_figure_01()
        print()
        generate_figure_02()
        print()
        generate_figure_03()
        print()
        generate_figure_04()
        print()
        print("=" * 70)
        print("✅ 所有图表生成完成！")
        print(f"输出目录：{OUTPUT_DIR}")
        print("=" * 70)
    except Exception as e:
        print(f"❌ 错误：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
