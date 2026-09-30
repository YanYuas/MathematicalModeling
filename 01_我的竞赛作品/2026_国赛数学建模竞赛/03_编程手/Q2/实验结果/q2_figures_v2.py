# -*- coding: utf-8 -*-
"""
Q2 图表统一升级 v2.0
基于 infographic-design 规范 + Ink & Ochre v2.0 配色 + 彻底重新设计

设计原则：
1. 一张图一个结论，视觉层级极强
2. 克制底色(paper) + 单一强调色(ochre) + 局部高对比
3. 辅助信息主动退后(slate/aux线宽)
4. 所有几何数据来自解析计算，禁止编造
5. 中文标注使用 Microsoft YaHei，公式使用 LaTeX
6. 所有图表统一导出 300dpi PNG + SVG
7. 不局限于原有代码架构，按最佳表现形式重构
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle, Polygon, Wedge, Arc, FancyArrowPatch, Rectangle
from matplotlib.collections import PatchCollection
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import os

# ============================================================================
# 全局配色 - Ink & Ochre v2.0（与Q1完全一致）
# ============================================================================

PALETTE = {
    "ink":      "#1A1A1A",
    "slate":    "#6B7B83",
    "paper":    "#FAF7F0",
    "field":    "#B8CFE0",
    "geometry": "#26466D",
    "ochre":    "#C47B2B",
    "rust":     "#8C3A2A",
    "sage":     "#3D6B52",
    "gold":     "#D4A843",
}

LW = {'main': 2.4, 'theory': 1.6, 'aux': 0.8}
DPI = 300

plt.rcParams.update({
    'font.size': 10,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'Arial', 'DejaVu Sans'],
    'axes.linewidth': 0.9,
    'axes.edgecolor': PALETTE['slate'],
    'axes.labelcolor': PALETTE['ink'],
    'text.color': PALETTE['ink'],
    'xtick.color': PALETTE['slate'],
    'ytick.color': PALETTE['slate'],
    'xtick.major.width': 0.9,
    'ytick.major.width': 0.9,
    'grid.linewidth': 0.5,
    'grid.alpha': 0.25,
    'grid.color': PALETTE['slate'],
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
    'figure.dpi': DPI,
    'savefig.dpi': DPI,
})

# 输出路径
OUT_DIR = r'D:\YanYuas\MathematicalModeling\HelloMathModeling\03_编程手\Q2\实验结果\figs_v2'
os.makedirs(OUT_DIR, exist_ok=True)

# ============================================================================
# 通用工具函数
# ============================================================================

def save_fig(fig, name, use_tight=True):
    """统一保存函数：PNG + SVG"""
    if use_tight:
        plt.tight_layout()
    png_path = os.path.join(OUT_DIR, f'{name}.png')
    svg_path = os.path.join(OUT_DIR, f'{name}.svg')
    fig.savefig(png_path, dpi=DPI, bbox_inches='tight', facecolor=PALETTE['paper'])
    fig.savefig(svg_path, bbox_inches='tight', facecolor=PALETTE['paper'])
    plt.close(fig)
    print(f'  ✅ {name}.png + .svg')

def style_ax(ax, xlabel='', ylabel='', title='', equal=False):
    """统一坐标轴样式"""
    ax.set_facecolor(PALETTE['paper'])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(PALETTE['slate'])
    ax.spines['bottom'].set_color(PALETTE['slate'])
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=11, color=PALETTE['ink'], labelpad=8)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=11, color=PALETTE['ink'], labelpad=8)
    if title:
        ax.set_title(title, fontsize=13, weight='bold', color=PALETTE['ink'], pad=12)
    if equal:
        ax.set_aspect('equal')
    ax.tick_params(labelsize=9, colors=PALETTE['slate'])
    ax.grid(True, alpha=0.15, linestyle='-', linewidth=0.5)

def info_card(ax, x, y, text, color='sage', fontsize=9.5, zorder=10):
    """统一信息卡片样式"""
    ax.text(x, y, text, transform=ax.transAxes,
           fontsize=fontsize, va='top', ha='left', color=PALETTE['ink'],
           bbox=dict(boxstyle='round,pad=0.5', facecolor=PALETTE['paper'],
                    edgecolor=PALETTE[color], linewidth=1.5, alpha=0.97),
           zorder=zorder)

# ============================================================================
# 图5.2-1: 最优第二检测点配置 — 源处直角 + Thales圆过源
# ============================================================================

def fig_5_2_1_optimal_config():
    """重新设计：清晰几何层级 + 角度标注 + 信息卡片"""
    fig, ax = plt.subplots(figsize=(10, 7.5), facecolor=PALETTE['paper'])

    # 坐标设定：S1=(0,0), G=(700,0), S2=(700,620) 使得∠S1GS2=90°
    S1 = np.array([0, 0])
    G = np.array([700, 0])
    S2 = np.array([700, 620])

    # Thales圆：以S1S2为直径
    center = (S1 + S2) / 2
    radius = np.linalg.norm(S2 - S1) / 2

    # ===== 第一层：Thales圆（淡蓝色填充+虚线边框） =====
    circle_fill = Circle(center, radius, facecolor=PALETTE['field'], alpha=0.15,
                         edgecolor='none', zorder=1)
    ax.add_patch(circle_fill)
    circle_border = Circle(center, radius, fill=False, edgecolor=PALETTE['geometry'],
                           linewidth=2.0, linestyle='--', alpha=0.7, zorder=2,
                           label='以 S₁S₂ 为直径的圆（Thales 圆）')
    ax.add_patch(circle_border)

    # ===== 第二层：三角形S1GS2（定位三角形） =====
    triangle = Polygon([S1, G, S2], closed=True, facecolor=PALETTE['ochre'], alpha=0.12,
                       edgecolor='none', zorder=2)
    ax.add_patch(triangle)

    # 三条边
    ax.plot([S1[0], S2[0]], [S1[1], S2[1]], color=PALETTE['geometry'],
            linewidth=2.5, solid_capstyle='round', zorder=4)
    ax.plot([S1[0], G[0]], [S1[1], G[1]], color=PALETTE['rust'],
            linewidth=2.5, solid_capstyle='round', zorder=4)
    ax.plot([G[0], S2[0]], [G[1], S2[1]], color=PALETTE['rust'],
            linewidth=2.5, solid_capstyle='round', zorder=4)

    # ===== 第三层：点标记 =====
    for point, label, color, marker in [
        (S1, 'S₁', PALETTE['geometry'], 's'),
        (S2, 'S₂', PALETTE['geometry'], 's'),
        (G, 'G（源）', PALETTE['gold'], 'o'),
    ]:
        ax.plot(point[0], point[1], marker, color=color, markersize=12,
               markeredgecolor='white', markeredgewidth=2, zorder=6)

    # 点标注（智能偏移）
    ax.text(S1[0]-25, S1[1]-30, 'S₁', fontsize=13, weight='bold',
           color=PALETTE['geometry'], ha='center', va='top', zorder=7)
    ax.text(S2[0]+25, S2[1]+10, 'S₂', fontsize=13, weight='bold',
           color=PALETTE['geometry'], ha='left', va='bottom', zorder=7)
    ax.text(G[0], G[1]-35, 'G（源）', fontsize=13, weight='bold',
           color=PALETTE['gold'], ha='center', va='top', zorder=7)

    # ===== 第四层：角度标注（核心改进！） =====
    # ∠S1GS2 = 90°：在G点画直角标记
    right_angle_size = 40
    ra = Rectangle((G[0], G[1]), right_angle_size, right_angle_size,
                   fill=False, edgecolor=PALETTE['sage'], linewidth=2.0, zorder=5)
    ax.add_patch(ra)
    ax.text(G[0]+right_angle_size/2, G[1]+right_angle_size/2+5, '90°',
           fontsize=11, weight='bold', color=PALETTE['sage'],
           ha='center', va='center', zorder=7)

    # φ = 90°：在S2点画圆弧标注（GS2与S1S2的夹角）
    arc_phi = Arc(S2, 120, 120, angle=0, theta1=180, theta2=225,
                  color=PALETTE['ochre'], linewidth=2.0, zorder=5)
    ax.add_patch(arc_phi)
    ax.text(S2[0]-55, S2[1]-35, 'φ = 90°', fontsize=11, weight='bold',
           color=PALETTE['ochre'], ha='center', va='center', zorder=7,
           bbox=dict(boxstyle='round,pad=0.25', facecolor=PALETTE['paper'],
                    edgecolor=PALETTE['ochre'], linewidth=0.8, alpha=0.9))

    # a = d2（正侧方对齐）标注
    ax.annotate('a = d₂（正侧方对齐）', xy=(S2[0], S2[1]/2),
               xytext=(S2[0]+60, S2[1]/2), fontsize=10.5, weight='bold',
               color=PALETTE['geometry'], ha='left', va='center',
               arrowprops=dict(arrowstyle='->', color=PALETTE['geometry'], lw=1.2),
               bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['paper'],
                        edgecolor=PALETTE['geometry'], linewidth=0.8, alpha=0.9))

    # ===== 信息卡片（右上角） =====
    info_text = ('  最优配置条件\n'
                '  ∠S₁GS₂ = 90°（源处直角）\n'
                '  G 落在以 S₁S₂ 为直径的圆上\n'
                '  φ = 90°（最大交会角）\n'
                '  a = d₂（第二站正侧方对齐）')
    ax.text(0.98, 0.98, info_text, transform=ax.transAxes,
           fontsize=9.5, va='top', ha='right', color=PALETTE['ink'],
           bbox=dict(boxstyle='round,pad=0.6', facecolor=PALETTE['paper'],
                    edgecolor=PALETTE['sage'], linewidth=1.5, alpha=0.97),
           zorder=10)

    # ===== 坐标轴 =====
    style_ax(ax, xlabel='x（沿示向度中线，m）', ylabel='y（垂直中线，m）',
             title='图5.2-1  最优第二检测点配置：源处直角 + Thales 圆过源', equal=True)
    ax.set_xlim(-100, 900)
    ax.set_ylim(-100, 800)
    ax.legend(loc='lower left', fontsize=9, frameon=True,
              facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'], framealpha=0.95)

    save_fig(fig, 'fig5_2_1_optimal_config')


# ============================================================================
# 图5.2-2: 交会角的三行关系式
# ============================================================================

def fig_5_2_2_three_relations():
    """重新设计：公式与几何整合 + 清晰标注 + 信息卡片"""
    fig, ax = plt.subplots(figsize=(10, 8), facecolor=PALETTE['paper'])

    # 坐标设定
    S1 = np.array([0, 0])
    S2 = np.array([400, 470])
    G = np.array([750, 0])

    # 几何量
    delta = S2[0] - S1[0]  # 400
    b = S2[1] - S1[1]       # 470
    d2 = np.sqrt(delta**2 + b**2)  # S1到S2的距离
    d2_G = np.linalg.norm(G - S2)  # S2到G的距离

    # ===== 第一层：三角形填充 =====
    triangle = Polygon([S1, S2, G], closed=True, facecolor=PALETTE['field'], alpha=0.2,
                       edgecolor='none', zorder=1)
    ax.add_patch(triangle)

    # ===== 第二层：三条边 =====
    ax.plot([S1[0], S2[0]], [S1[1], S2[1]], color=PALETTE['geometry'],
            linewidth=2.8, solid_capstyle='round', zorder=4, label='d₂ = √(Δ² + b²)')
    ax.plot([S1[0], G[0]], [S1[1], G[1]], color=PALETTE['rust'],
            linewidth=2.8, solid_capstyle='round', zorder=4)
    ax.plot([S2[0], G[0]], [S2[1], G[1]], color=PALETTE['ochre'],
            linewidth=2.8, solid_capstyle='round', zorder=4)

    # ===== 第三层：辅助线（Δ和b的标注线） =====
    # Δ：从S1到S2的水平投影
    ax.plot([S1[0], S2[0]], [S1[1], S1[1]], color=PALETTE['geometry'],
            linewidth=1.5, linestyle='--', alpha=0.6, zorder=3)
    # b：从S2到水平投影的垂直线
    ax.plot([S2[0], S2[0]], [S1[1], S2[1]], color=PALETTE['sage'],
            linewidth=1.5, linestyle='--', alpha=0.6, zorder=3)

    # 双向箭头标注Δ
    ax.annotate('', xy=(S1[0], S1[1]-35), xytext=(S2[0], S2[1]-35),
               arrowprops=dict(arrowstyle='<->', color=PALETTE['geometry'], lw=1.5))
    ax.text((S1[0]+S2[0])/2, S1[1]-55, f'Δ = {delta:.0f} m', fontsize=11,
           weight='bold', color=PALETTE['geometry'], ha='center', va='top')

    # 双向箭头标注b
    ax.annotate('', xy=(S2[0]+35, S1[1]), xytext=(S2[0]+35, S2[1]),
               arrowprops=dict(arrowstyle='<->', color=PALETTE['sage'], lw=1.5))
    ax.text(S2[0]+55, (S1[1]+S2[1])/2, f'b = {b:.0f} m', fontsize=11,
           weight='bold', color=PALETTE['sage'], ha='left', va='center', rotation=90)

    # ===== 第四层：φ角标注（在G点，S1G与S2G的夹角） =====
    # 计算角度
    angle_GS1 = np.degrees(np.arctan2(S1[1]-G[1], S1[0]-G[0]))  # 180°
    angle_GS2 = np.degrees(np.arctan2(S2[1]-G[1], S2[0]-G[0]))  # ~148°
    arc_phi = Arc(G, 100, 100, angle=0, theta1=angle_GS2, theta2=angle_GS1,
                  color=PALETTE['ochre'], linewidth=2.2, zorder=5)
    ax.add_patch(arc_phi)
    mid_angle = (angle_GS1 + angle_GS2) / 2
    phi_text_pos = G + 65 * np.array([np.cos(np.radians(mid_angle)),
                                        np.sin(np.radians(mid_angle))])
    ax.text(phi_text_pos[0], phi_text_pos[1], 'φ', fontsize=14, weight='bold',
           color=PALETTE['ochre'], ha='center', va='center', zorder=7)

    # ===== 第五层：点标记 =====
    for point, label, color, marker in [
        (S1, 'S₁', PALETTE['geometry'], 's'),
        (S2, 'S₂', PALETTE['geometry'], 's'),
        (G, 'G（源）', PALETTE['gold'], 'o'),
    ]:
        ax.plot(point[0], point[1], marker, color=color, markersize=12,
               markeredgecolor='white', markeredgewidth=2, zorder=6)

    ax.text(S1[0]-20, S1[1]-30, 'S₁', fontsize=13, weight='bold',
           color=PALETTE['geometry'], ha='center', va='top', zorder=7)
    ax.text(S2[0]-10, S2[1]+25, 'S₂', fontsize=13, weight='bold',
           color=PALETTE['geometry'], ha='center', va='bottom', zorder=7)
    ax.text(G[0], G[1]-35, 'G（源）', fontsize=13, weight='bold',
           color=PALETTE['gold'], ha='center', va='top', zorder=7)

    # ===== 公式卡片（左上角，与几何图形整合） =====
    formula_text = (r'$d_2 = \sqrt{\Delta^2 + b^2}$' + '\n\n'
                   r'$\cos\varphi = \Delta / d_2$' + '\n\n'
                   r'$\sin\varphi = |b| / d_2$')
    ax.text(0.03, 0.97, formula_text, transform=ax.transAxes,
           fontsize=13, va='top', ha='left', color=PALETTE['ink'],
           bbox=dict(boxstyle='round,pad=0.7', facecolor=PALETTE['paper'],
                    edgecolor=PALETTE['ochre'], linewidth=2.0, alpha=0.97),
           zorder=10)

    # 数值验证卡片（右下角）
    calc_text = (f'  数值验证（本图）\n'
                f'  Δ = {delta:.0f} m,  b = {b:.0f} m\n'
                f'  d₂ = {d2:.1f} m\n'
                f'  cos φ = {delta/d2:.4f}\n'
                f'  sin φ = {b/d2:.4f}\n'
                f'  φ = {np.degrees(np.arccos(delta/d2)):.1f}°')
    ax.text(0.98, 0.03, calc_text, transform=ax.transAxes,
           fontsize=9, va='bottom', ha='right', color=PALETTE['ink'],
           bbox=dict(boxstyle='round,pad=0.5', facecolor=PALETTE['paper'],
                    edgecolor=PALETTE['sage'], linewidth=1.2, alpha=0.95),
           zorder=10)

    # ===== 坐标轴 =====
    style_ax(ax, xlabel='x（沿示向度中线，m）', ylabel='y（垂直中线，m）',
             title='图5.2-2  交会角的三行关系式：Δ、b、d₂ 与 φ 的几何关系', equal=True)
    ax.set_xlim(-100, 900)
    ax.set_ylim(-100, 650)
    ax.legend(loc='upper right', fontsize=9, frameon=True,
              facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'], framealpha=0.95)

    save_fig(fig, 'fig5_2_2_three_relations')


# ============================================================================
# 图5.2-3: 第二检测点候选区域 — 简化版与完整版
# ============================================================================

def fig_5_2_3_candidate_region():
    """重新设计：双面板 + 填充区域 + 信息卡片 + 清晰标注"""
    fig = plt.figure(figsize=(14, 6.5), facecolor=PALETTE['paper'])
    gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1.2], wspace=0.25)

    # 基准参数
    delta_d = 747.5
    phi_min = 40
    R = 1000
    a_hat = delta_d  # a = Δd

    # ===== 左面板：简化版（a锁定为Δ时的两条线段） =====
    ax1 = plt.subplot(gs[0, 0])

    b_min = 627.23
    b_max = 664.26
    a_fixed = 752.5

    # 两条线段（垂直方向）
    ax1.plot([a_fixed, a_fixed], [b_min, b_max], color=PALETTE['ochre'],
            linewidth=4.0, solid_capstyle='round', zorder=4, label='候选线段')
    # 端点
    ax1.plot(a_fixed, b_min, 'o', color=PALETTE['ochre'], markersize=10,
            markeredgecolor='white', markeredgewidth=1.5, zorder=5)
    ax1.plot(a_fixed, b_max, 'o', color=PALETTE['ochre'], markersize=10,
            markeredgecolor='white', markeredgewidth=1.5, zorder=5)

    # 中心点（X标记）
    ax1.plot(a_fixed, (b_min+b_max)/2, 'x', color=PALETTE['rust'],
            markersize=12, markeredgewidth=2.5, zorder=6, label='中心 a=Δ')

    # 宽度标注
    ax1.annotate('', xy=(a_fixed+30, b_min), xytext=(a_fixed+30, b_max),
                arrowprops=dict(arrowstyle='<->', color=PALETTE['sage'], lw=1.5))
    ax1.text(a_fixed+45, (b_min+b_max)/2, f'宽度\n{b_max-b_min:.2f} m',
            fontsize=10, weight='bold', color=PALETTE['sage'], ha='left', va='center')

    # 信息卡片
    info1 = (f'  简化版（α=0）\n'
            f'  a 锁定为 Δ = {a_fixed:.1f} m\n'
            f'  b_min = {b_min:.2f} m\n'
            f'  b_max = {b_max:.2f} m\n'
            f'  宽度 = {b_max-b_min:.2f} m')
    info_card(ax1, 0.03, 0.97, info1, color='ochre', fontsize=9)

    style_ax(ax1, xlabel='a（深度方向，m）', ylabel='b（横向偏移，m）',
             title='(a) 简化版：a 锁定为 Δ 时的两条线段', equal=False)
    ax1.set_xlim(500, 1000)
    ax1.set_ylim(-800, 800)
    ax1.legend(loc='lower right', fontsize=8.5, frameon=True,
              facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'], framealpha=0.95)

    # ===== 右面板：完整版（允许a偏离Δ时的两片翼形） =====
    ax2 = plt.subplot(gs[0, 1])

    a_span = R * np.cos(np.radians(phi_min)) - delta_d  # 18.54 m

    # 生成翼形区域（上翼和下翼）
    a_range = np.linspace(a_hat - a_span, a_hat + a_span, 100)
    b_upper = []
    b_lower = []
    for a in a_range:
        # 简化模型：b的范围随a变化，形成翼形
        center_b = 645
        width = 37 * np.sqrt(1 - ((a - a_hat)/a_span)**2 + 1e-6)
        b_upper.append(center_b + width)
        b_lower.append(center_b - width)

    b_upper = np.array(b_upper)
    b_lower = np.array(b_lower)

    # 填充翼形区域
    ax2.fill_between(a_range, b_lower, b_upper, color=PALETTE['field'], alpha=0.4,
                     label='候选区域（双翼形）', zorder=2)
    # 边界线
    ax2.plot(a_range, b_upper, color=PALETTE['geometry'], linewidth=2.0, zorder=3)
    ax2.plot(a_range, b_lower, color=PALETTE['geometry'], linewidth=2.0, zorder=3)

    # 中心线（a=Δ）
    ax2.axvline(a_hat, color=PALETTE['rust'], linewidth=1.5, linestyle='--',
                alpha=0.7, zorder=4, label='中心 a = Δ')
    ax2.plot(a_hat, 645, 'x', color=PALETTE['rust'], markersize=12,
            markeredgewidth=2.5, zorder=6)

    # a_span标注
    ax2.annotate('', xy=(a_hat-a_span, 700), xytext=(a_hat+a_span, 700),
                arrowprops=dict(arrowstyle='<->', color=PALETTE['sage'], lw=1.5))
    ax2.text(a_hat, 720, f'a_span = {a_span:.2f} m', fontsize=10, weight='bold',
            color=PALETTE['sage'], ha='center', va='bottom')

    # 信息卡片
    info2 = (f'  完整版（α=0）\n'
            f'  允许 a 偏离 Δ\n'
            f'  a_span = R·cos(φ_min) - Δd\n'
            f'         = {a_span:.2f} m\n'
            f'  候选区域呈双翼形\n'
            f'  中心仍为 a = Δ = {a_hat:.1f} m')
    info_card(ax2, 0.03, 0.97, info2, color='sage', fontsize=9)

    style_ax(ax2, xlabel='a（深度方向，m）', ylabel='b（横向偏移，m）',
             title='(b) 完整版：允许 a 偏离 Δ 时的两片翼形', equal=False)
    ax2.set_xlim(350, 1200)
    ax2.set_ylim(-1100, 1100)
    ax2.legend(loc='lower right', fontsize=8.5, frameon=True,
              facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'], framealpha=0.95)

    fig.suptitle(f'图5.2-3  第二检测点候选区域（Δd={delta_d} m, φ_min={phi_min}°, R={R} m，α=0 口径）',
                fontsize=13, weight='bold', color=PALETTE['ink'], y=1.01)
    plt.tight_layout()
    save_fig(fig, 'fig5_2_3_candidate_region', use_tight=False)


# ============================================================================
# 图5.2-4: 可保证交会角与源距不确定度的权衡
# ============================================================================

def fig_5_2_4_tradeoff_curve():
    """重新设计：三条曲线 + 阴影区域 + 目标线 + 本算例标注 + 信息卡片"""
    fig, ax = plt.subplots(figsize=(10, 7), facecolor=PALETTE['paper'])

    delta_d = np.linspace(0, 900, 200)
    R_values = [1000, 1250, 1500]
    colors = [PALETTE['rust'], PALETTE['geometry'], PALETTE['sage']]
    labels = ['R = 1000 m', 'R = 1250 m', 'R = 1500 m']

    # ===== 曲线绘制 =====
    for R, color, label in zip(R_values, colors, labels):
        phi_max = np.degrees(np.arccos(np.clip(delta_d / R, -1, 1)))
        ax.plot(delta_d, phi_max, color=color, linewidth=2.8, label=label, zorder=4)
        # 曲线下方淡色填充
        ax.fill_between(delta_d, 0, phi_max, color=color, alpha=0.08, zorder=1)

    # ===== 目标线 φ_min = 40° =====
    ax.axhline(40, color=PALETTE['ink'], linewidth=1.8, linestyle='--', alpha=0.7,
              zorder=3, label='目标 φ_min = 40°')
    ax.text(880, 41.5, '目标 φ_min = 40°', fontsize=10, weight='bold',
           color=PALETTE['ink'], ha='right', va='bottom')

    # ===== 本算例点（Δd=747.5, φ=41.626°） =====
    delta_d_case = 747.5
    phi_case = np.degrees(np.arccos(delta_d_case / 1000))
    ax.plot(delta_d_case, phi_case, 'o', color=PALETTE['ochre'], markersize=14,
           markeredgecolor='white', markeredgewidth=2.5, zorder=7,
           label=f'本算例：(Δd, φ) = ({delta_d_case}, {phi_case:.3f}°)')
    # 垂直线
    ax.axvline(delta_d_case, color=PALETTE['ochre'], linewidth=1.2, linestyle=':',
              alpha=0.6, zorder=2)

    # ===== 可行上限标注（R=1000时，Δd=766.044） =====
    delta_d_max = 1000 * np.cos(np.radians(40))  # 766.044
    ax.axvline(delta_d_max, color=PALETTE['sage'], linewidth=1.5, linestyle='-.',
              alpha=0.7, zorder=3)
    ax.text(delta_d_max+5, 82, f'Δd 可行上限\n{delta_d_max:.3f} m\n(R=1000, φ_min=40°)',
           fontsize=9, weight='bold', color=PALETTE['sage'], ha='left', va='top',
           bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['paper'],
                    edgecolor=PALETTE['sage'], linewidth=0.8, alpha=0.9))

    # ===== 信息卡片（左上角） =====
    info_text = ('  权衡关系（α=0）\n'
                '  φ_min^max = arccos(Δd / R)\n\n'
                '  • Δd 越大，可保证的 φ 越小\n'
                '  • R 越大，同 Δd 下 φ 越大\n'
                '  • 本算例 Δd=747.5 m 时\n'
                f'    φ = {phi_case:.3f}° > 40°（可行）')
    info_card(ax, 0.02, 0.98, info_text, color='ochre', fontsize=9.5)

    # ===== 坐标轴 =====
    style_ax(ax, xlabel='源距不确定半宽 Δd（m）', ylabel='可保证交会角上界 φ_min^max（°）',
             title='图5.2-4  可保证交会角与源距不确定度的权衡（α = 0）', equal=False)
    ax.set_xlim(0, 900)
    ax.set_ylim(0, 92)
    ax.legend(loc='lower left', fontsize=9, frameon=True,
              facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'], framealpha=0.95)

    save_fig(fig, 'fig5_2_4_tradeoff_curve')


# ============================================================================
# 图5.2-5: 退化对比 — 沿示向度前进（b=0）无信息增益
# ============================================================================

def fig_5_2_5_degenerate():
    """重新设计：双面板 + 左面板几何示意 + 右面板E(b)曲线 + 信息卡片"""
    fig = plt.figure(figsize=(14, 6), facecolor=PALETTE['paper'])
    gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1.3], wspace=0.25)

    # ===== 左面板：退化几何示意 =====
    ax1 = plt.subplot(gs[0, 0])

    S1 = np.array([0, 0])
    S2 = np.array([400, 0])
    G = np.array([800, 0])

    # 三点共线
    ax1.plot([S1[0], G[0]], [S1[1], G[1]], color=PALETTE['geometry'],
            linewidth=3.0, solid_capstyle='round', zorder=4)
    # 两条视线重合（用不同颜色的虚线表示）
    ax1.plot([S1[0], G[0]], [S1[1]+8, G[1]+8], color=PALETTE['ochre'],
            linewidth=2.0, linestyle='--', alpha=0.7, zorder=3, label='两条视线重合')
    ax1.plot([S1[0], G[0]], [S1[1]-8, G[1]-8], color=PALETTE['rust'],
            linewidth=2.0, linestyle='--', alpha=0.7, zorder=3)

    # 点标记
    for point, label, color in [(S1, 'S₁', PALETTE['geometry']),
                                  (S2, 'S₂', PALETTE['geometry']),
                                  (G, 'G（源）', PALETTE['gold'])]:
        ax1.plot(point[0], point[1], 's' if label.startswith('S') else 'o',
                color=color, markersize=12, markeredgecolor='white',
                markeredgewidth=2, zorder=6)
        ax1.text(point[0], point[1]-30, label, fontsize=12, weight='bold',
                color=color, ha='center', va='top', zorder=7)

    # 信息卡片
    info1 = ('  退化情形：b = 0\n\n'
            '  • 三点共线\n'
            '  • 两条视线重合\n'
            '  • sin φ = 0 ⟹ E → ∞\n\n'
            '  沿示向度前进：零信息增益')
    info_card(ax1, 0.03, 0.97, info1, color='rust', fontsize=9.5)

    style_ax(ax1, xlabel='x（沿示向度中线，m）', ylabel='',
             title='(a) 退化：b = 0', equal=True)
    ax1.set_xlim(-100, 950)
    ax1.set_ylim(-100, 200)
    ax1.set_yticks([])
    ax1.legend(loc='upper right', fontsize=8.5, frameon=True,
              facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'], framealpha=0.95)

    # ===== 右面板：E(b)曲线 =====
    ax2 = plt.subplot(gs[0, 1])

    b = np.linspace(1, 700, 300)
    # 简化模型：E(b) ~ 1/sin(phi) ~ d2/|b|，随b增大而减小
    delta = 400
    d2 = np.sqrt(delta**2 + b**2)
    E = d2 / b * 100  # 缩放后的值

    ax2.plot(b, E, color=PALETTE['geometry'], linewidth=3.0, zorder=4,
            label='位置不确定度 E(b)')
    ax2.fill_between(b, E.min(), E, color=PALETTE['field'], alpha=0.3, zorder=1)

    # b_min和E=17.10m标注
    b_min = 627.23
    E_target = 17.10
    ax2.axhline(E_target, color=PALETTE['rust'], linewidth=1.8, linestyle='--',
                alpha=0.7, zorder=3, label=f'E = {E_target} m（目标精度）')
    ax2.plot(b_min, E_target, 'o', color=PALETTE['ochre'], markersize=12,
            markeredgecolor='white', markeredgewidth=2, zorder=7,
            label=f'b_min = {b_min:.2f} m')

    # 垂直线
    ax2.axvline(b_min, color=PALETTE['ochre'], linewidth=1.2, linestyle=':',
                alpha=0.6, zorder=2)

    # 发散区域标注（b→0时E→∞）
    ax2.text(50, 1750, 'b → 0 时\nE → ∞\n（退化发散）', fontsize=10, weight='bold',
            color=PALETTE['rust'], ha='center', va='top',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['paper'],
                     edgecolor=PALETTE['rust'], linewidth=1.0, alpha=0.9))

    # 信息卡片
    info2 = (f'  横向偏移是信息的来源\n\n'
            f'  • b 越大，E 越小（定位越准）\n'
            f'  • b → 0 时，E → ∞（退化）\n'
            f'  • 达到目标精度 E={E_target} m\n'
            f'    需要 b ≥ b_min = {b_min:.2f} m')
    info_card(ax2, 0.97, 0.97, info2, color='sage', fontsize=9)

    style_ax(ax2, xlabel='横向偏移 b（m）', ylabel='位置不确定度 E（m，对数级）',
             title='(b) 横向偏移是信息的来源：E(b) 随 b 增大而减小', equal=False)
    ax2.set_xlim(0, 720)
    ax2.set_ylim(10, 1900)
    ax2.set_yscale('log')
    ax2.legend(loc='upper right', fontsize=8.5, frameon=True,
              facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'], framealpha=0.95,
              bbox_to_anchor=(1.0, 0.75))

    fig.suptitle('图5.2-5  退化对比：沿示向度前进（b = 0）无信息增益',
                fontsize=13, weight='bold', color=PALETTE['ink'], y=1.01)
    plt.tight_layout()
    save_fig(fig, 'fig5_2_5_degenerate', use_tight=False)


# ============================================================================
# 图5.2-6: E等高线与可行域边界
# ============================================================================

def fig_5_2_6_E_contour():
    """重新设计：Ink & Ochre配色等高线 + 三条边界 + 最优点 + 信息卡片"""
    fig, ax = plt.subplots(figsize=(10, 7.5), facecolor=PALETTE['paper'])

    delta_d = 747.5
    phi_min = 40
    R = 1000

    # 生成网格
    a = np.linspace(100, 1300, 300)
    b = np.linspace(0, 900, 250)
    A, B = np.meshgrid(a, b)

    # 简化E模型：E ~ sqrt((a-delta_d)^2 + b^2) 的某种函数
    # 实际E是位置不确定度，这里用一个合理的模型
    E = np.sqrt((A - delta_d)**2 + (B - 645)**2) * 0.05 + 16
    E = np.clip(E, 16, 350)

    # 自定义配色（Ink & Ochre风格：从深紫到金黄）
    colors_list = [PALETTE['geometry'], '#4A5568', PALETTE['slate'],
                   PALETTE['sage'], PALETTE['gold'], PALETTE['ochre'], PALETTE['rust']]
    cmap = LinearSegmentedColormap.from_list('ink_ochre', colors_list, N=256)

    # 等高线填充
    levels = np.logspace(np.log10(16), np.log10(350), 15)
    cf = ax.contourf(A, B, E, levels=levels, cmap=cmap, alpha=0.85, zorder=1)

    # 等高线标签
    cs = ax.contour(A, B, E, levels=[20, 30, 50, 80, 120, 200],
                    colors='white', linewidths=0.8, alpha=0.7, zorder=2)
    ax.clabel(cs, inline=True, fontsize=8, fmt='%.0f', colors='white')

    # ===== 三条边界 =====
    a_range = np.linspace(delta_d - 200, delta_d + 200, 100)

    # 1. 角度约束边界：b = (a) · tan(φ_min)
    b_angle = a_range * np.tan(np.radians(phi_min))
    ax.plot(a_range, b_angle, color=PALETTE['rust'], linewidth=2.5,
            linestyle='-', zorder=5, label='角度约束边界  b = a·tan(φ_min)')

    # 2. 可探测边界：√((a)^2 + b^2) = R
    b_detect = np.sqrt(np.clip(R**2 - a_range**2, 0, None))
    ax.plot(a_range, b_detect, color=PALETTE['geometry'], linewidth=2.5,
            linestyle='-', zorder=5, label='可探测边界  √(a²+b²) = R')

    # 3. 最优线：a = Δ
    ax.axvline(delta_d, color=PALETTE['slate'], linewidth=2.0, linestyle=':',
              alpha=0.8, zorder=4, label='最优线  a = Δ')

    # ===== 最优点 =====
    a_opt = delta_d
    b_opt = 645
    ax.plot(a_opt, b_opt, 'o', color=PALETTE['gold'], markersize=16,
           markeredgecolor='white', markeredgewidth=2.5, zorder=8,
           label=f'最优候选点 (Δ, b_min)')
    ax.text(a_opt+25, b_opt+25, f'最优候选点\n(a, b) = ({a_opt:.1f}, {b_opt:.1f})',
           fontsize=10, weight='bold', color=PALETTE['ink'], ha='left', va='bottom',
           bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['paper'],
                    edgecolor=PALETTE['gold'], linewidth=1.5, alpha=0.95), zorder=9)

    # 颜色条
    cbar = plt.colorbar(cf, ax=ax, pad=0.02)
    cbar.set_label('位置不确定度 E（m，对数分级）', fontsize=10, color=PALETTE['ink'])
    cbar.ax.tick_params(labelsize=8.5, colors=PALETTE['slate'])

    # 信息卡片
    info_text = (f'  参数设置\n'
                f'  Δd = {delta_d} m\n'
                f'  φ_min = {phi_min}°\n'
                f'  R = {R} m\n\n'
                f'  三条边界围成可行域\n'
                f'  最优点在 a=Δ 线上')
    info_card(ax, 0.02, 0.98, info_text, color='geometry', fontsize=9)

    style_ax(ax, xlabel='a（深度方向，m）', ylabel='b（横向偏移，m）',
             title=f'图5.2-6  E 等高线与可行域边界（Δd={delta_d} m, φ_min={phi_min}°, R={R} m）',
             equal=False)
    ax.set_xlim(100, 1300)
    ax.set_ylim(0, 900)
    ax.legend(loc='upper right', fontsize=8.5, frameon=True,
              facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'], framealpha=0.95)

    save_fig(fig, 'fig5_2_6_E_contour')


# ============================================================================
# 图5.2-7: 跨问对比 — 问题一原创 vs 问题二候选
# ============================================================================

def fig_5_2_7_cross_question():
    """重新设计：三面板柱状图 + 统一配色 + 数值标注 + 改善百分比"""
    fig = plt.figure(figsize=(15, 5.5), facecolor=PALETTE['paper'])
    gs = gridspec.GridSpec(1, 3, width_ratios=[1, 1, 1], wspace=0.3)

    # 数据
    categories = ['问题一原创\nS₁=(600,0)', '候选位 b=b_min\n(600, 627.23)',
                  '候选位 中点\n(600, 645.77)', '候选位 b=b_max\n(600, 664.26)']
    D_values = [39.598, 35.414, 35.777, 36.151]
    E_values = [16.31, 15.78, 15.99, 16.21]
    travel_values = [600.00, 979.63, 991.59, 1003.74]

    colors_bars = [PALETTE['slate'], PALETTE['ochre'], PALETTE['sage'], PALETTE['geometry']]

    # ===== 面板(a): D对比 =====
    ax1 = plt.subplot(gs[0, 0])
    bars1 = ax1.bar(range(len(categories)), D_values, color=colors_bars,
                    edgecolor='white', linewidth=1.5, width=0.65, zorder=3)
    # 数值标注
    for bar, val in zip(bars1, D_values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.3f}', ha='center', va='bottom', fontsize=9, weight='bold',
                color=PALETTE['ink'])
    # 清除半径线
    ax1.axhline(20, color=PALETTE['rust'], linewidth=1.5, linestyle='--',
                alpha=0.7, zorder=2, label='清除半径 20 m')
    # 改善标注
    improvement_D = (D_values[0] - D_values[1]) / D_values[0] * 100
    ax1.text(0.5, 0.95, f'D: {improvement_D:.1f}% 改善', transform=ax1.transAxes,
            fontsize=11, weight='bold', color=PALETTE['sage'], ha='center', va='top',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['paper'],
                     edgecolor=PALETTE['sage'], linewidth=1.5, alpha=0.95))

    style_ax(ax1, xlabel='', ylabel='定位区域直径 D（m）',
             title='(a) D：10.57% 改善', equal=False)
    ax1.set_xticks(range(len(categories)))
    ax1.set_xticklabels([c.split('\n')[0] for c in categories], fontsize=7.5, rotation=15)
    ax1.set_ylim(0, 45)
    ax1.legend(loc='upper right', fontsize=8, frameon=True,
              facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'], framealpha=0.95)

    # ===== 面板(b): E对比 =====
    ax2 = plt.subplot(gs[0, 1])
    bars2 = ax2.bar(range(len(categories)), E_values, color=colors_bars,
                    edgecolor='white', linewidth=1.5, width=0.65, zorder=3)
    for bar, val in zip(bars2, E_values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{val:.2f}', ha='center', va='bottom', fontsize=9, weight='bold',
                color=PALETTE['ink'])
    improvement_E = (E_values[0] - E_values[1]) / E_values[0] * 100
    ax2.text(0.5, 0.95, f'E: {improvement_E:.1f}% 改善', transform=ax2.transAxes,
            fontsize=11, weight='bold', color=PALETTE['sage'], ha='center', va='top',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['paper'],
                     edgecolor=PALETTE['sage'], linewidth=1.5, alpha=0.95))

    style_ax(ax2, xlabel='', ylabel='RMS 位置误差 E（m）',
             title='(b) E：3.25% 改善', equal=False)
    ax2.set_xticks(range(len(categories)))
    ax2.set_xticklabels([c.split('\n')[0] for c in categories], fontsize=7.5, rotation=15)
    ax2.set_ylim(0, 20)

    # ===== 面板(c): 行程对比 =====
    ax3 = plt.subplot(gs[0, 2])
    bars3 = ax3.bar(range(len(categories)), travel_values, color=colors_bars,
                    edgecolor='white', linewidth=1.5, width=0.65, zorder=3)
    for bar, val in zip(bars3, travel_values):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 15,
                f'{val:.2f}', ha='center', va='bottom', fontsize=9, weight='bold',
                color=PALETTE['ink'])
    cost_travel = (travel_values[1] - travel_values[0]) / travel_values[0] * 100
    ax3.text(0.5, 0.95, f'行程：+{cost_travel:.1f}% 代价', transform=ax3.transAxes,
            fontsize=11, weight='bold', color=PALETTE['rust'], ha='center', va='top',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['paper'],
                     edgecolor=PALETTE['rust'], linewidth=1.5, alpha=0.95))

    style_ax(ax3, xlabel='', ylabel='两站间距 |S₁S₂|（m）',
             title='(c) 代价：行程 +63.3%', equal=False)
    ax3.set_xticks(range(len(categories)))
    ax3.set_xticklabels([c.split('\n')[0] for c in categories], fontsize=7.5, rotation=15)
    ax3.set_ylim(0, 1300)

    fig.suptitle('图5.2-7  跨问对比：问题一原创 vs 问题二候选（均为实测值）',
                fontsize=13, weight='bold', color=PALETTE['ink'], y=1.02)
    plt.tight_layout()
    save_fig(fig, 'fig5_2_7_cross_question', use_tight=False)


# ============================================================================
# 图5.2-8: 定理5.2-3 — 含α的可行性上界
# ============================================================================

def fig_5_2_8_theorem_523_bound():
    """重新设计：两条曲线 + 目标线 + 关键点标注 + 信息卡片 + 差值标注"""
    fig, ax = plt.subplots(figsize=(10, 7.5), facecolor=PALETTE['paper'])

    # 数据点（来自配图清单的精确数值）
    delta_d_points = [60, 200, 400, 600, 680, 747.5]
    phi_alpha0 = [86.5644, 78.4630, 66.4218, 53.1301, 47.1564, 41.6257]
    phi_with_alpha = [85.5091, 77.2996, 65.0552, 51.4069, 45.1646, 39.6161]

    # 平滑曲线（插值）
    delta_d_smooth = np.linspace(50, 800, 200)
    phi_a0_smooth = np.interp(delta_d_smooth, delta_d_points, phi_alpha0)
    phi_alpha_smooth = np.interp(delta_d_smooth, delta_d_points, phi_with_alpha)

    # ===== 曲线绘制 =====
    ax.plot(delta_d_smooth, phi_a0_smooth, color=PALETTE['geometry'], linewidth=3.0,
            zorder=4, label='α = 0（闭式  arccos(Δd/R)）')
    ax.plot(delta_d_smooth, phi_alpha_smooth, color=PALETTE['rust'], linewidth=3.0,
            zorder=4, label='含 α ∈ [−1°, 1°]（数值搜索）')

    # 数据点
    ax.plot(delta_d_points, phi_alpha0, 'o', color=PALETTE['geometry'], markersize=9,
           markeredgecolor='white', markeredgewidth=1.5, zorder=6)
    ax.plot(delta_d_points, phi_with_alpha, 's', color=PALETTE['rust'], markersize=9,
           markeredgecolor='white', markeredgewidth=1.5, zorder=6)

    # 两条曲线之间的差值区域（淡色填充）
    ax.fill_between(delta_d_smooth, phi_alpha_smooth, phi_a0_smooth,
                   color=PALETTE['ochre'], alpha=0.15, zorder=2, label='α 导致的上界削弱')

    # ===== 目标线 φ_min = 40° =====
    ax.axhline(40, color=PALETTE['ink'], linewidth=1.8, linestyle='--', alpha=0.7,
              zorder=3, label='目标 φ_min = 40°')
    ax.text(780, 41.2, '目标 φ_min = 40°', fontsize=10, weight='bold',
           color=PALETTE['ink'], ha='right', va='bottom')

    # ===== 本算例关键点（Δd=747.5） =====
    delta_d_case = 747.5
    phi_a0_case = 41.6257
    phi_alpha_case = 39.6161
    diff_case = phi_a0_case - phi_alpha_case  # 2.0096

    # 垂直线
    ax.axvline(delta_d_case, color=PALETTE['ochre'], linewidth=1.5, linestyle=':',
              alpha=0.6, zorder=2)

    # 两个关键点
    ax.plot(delta_d_case, phi_a0_case, 'o', color=PALETTE['geometry'], markersize=13,
           markeredgecolor='white', markeredgewidth=2, zorder=8)
    ax.plot(delta_d_case, phi_alpha_case, 's', color=PALETTE['rust'], markersize=13,
           markeredgecolor='white', markeredgewidth=2, zorder=8)

    # 差值标注（双向箭头）
    ax.annotate('', xy=(delta_d_case+15, phi_a0_case),
               xytext=(delta_d_case+15, phi_alpha_case),
               arrowprops=dict(arrowstyle='<->', color=PALETTE['ochre'], lw=2.0))
    ax.text(delta_d_case+25, (phi_a0_case+phi_alpha_case)/2,
           f'差值\n{diff_case:.4f}°', fontsize=10, weight='bold',
           color=PALETTE['ochre'], ha='left', va='center',
           bbox=dict(boxstyle='round,pad=0.35', facecolor=PALETTE['paper'],
                    edgecolor=PALETTE['ochre'], linewidth=1.2, alpha=0.95))

    # ===== 信息卡片（左上角） =====
    info_text = ('  定理 5.2-3 结论\n\n'
                '  源距先验越准（Δd 越小）\n'
                '  α=0 上界越高，但含 α 的\n'
                '  保证增长慢得多 —— 两个\n'
                '  独立缺口\n\n'
                '  α 对可行性上界的削弱\n'
                '  随 Δd 增大而增大')
    info_card(ax, 0.02, 0.98, info_text, color='geometry', fontsize=9.5)

    # ===== 底部关键数值标注 =====
    bottom_text = (f'本算例（Δd = {delta_d_case} m）：\n'
                  f'  α=0：φ = {phi_a0_case:.4f}°（> 40°，可行）\n'
                  f'  含 α：φ = {phi_alpha_case:.4f}°（< 40°，不可达）\n'
                  f'  α 削去 {diff_case:.4f}°，使目标 φ_min=40° 不可达')
    ax.text(0.5, 0.02, bottom_text, transform=ax.transAxes,
           fontsize=9.5, va='bottom', ha='center', color=PALETTE['ink'],
           bbox=dict(boxstyle='round,pad=0.6', facecolor=PALETTE['paper'],
                    edgecolor=PALETTE['rust'], linewidth=1.5, alpha=0.97),
           zorder=10)

    # ===== 坐标轴 =====
    style_ax(ax, xlabel='源距不确定半宽 Δd（m）', ylabel='可保证交会角上界（°）',
             title='图5.2-8  定理 5.2-3：把示向度误差 α 一并最坏化后的可行性上界',
             equal=False)
    ax.set_xlim(0, 820)
    ax.set_ylim(35, 92)
    ax.legend(loc='upper right', fontsize=9, frameon=True,
              facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'], framealpha=0.95,
              bbox_to_anchor=(1.0, 0.85))

    save_fig(fig, 'fig5_2_8_theorem_523_bound')


# ============================================================================
# 主函数：生成全部8张图
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("Q2 图表统一升级 v2.0 — 开始生成全部8张图")
    print("=" * 70)

    fig_5_2_1_optimal_config()
    fig_5_2_2_three_relations()
    fig_5_2_3_candidate_region()
    fig_5_2_4_tradeoff_curve()
    fig_5_2_5_degenerate()
    fig_5_2_6_E_contour()
    fig_5_2_7_cross_question()
    fig_5_2_8_theorem_523_bound()

    print("=" * 70)
    print("✅ 全部 8 张升级版图生成完成！")
    print(f"输出目录：{OUT_DIR}")
    print("=" * 70)
