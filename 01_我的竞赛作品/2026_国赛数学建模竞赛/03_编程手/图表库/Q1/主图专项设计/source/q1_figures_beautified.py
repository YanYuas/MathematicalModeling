# -*- coding: utf-8 -*-
"""
Q1 图表统一美化版 v2.0
基于 infographic-design 规范 + Ink & Ochre 配色 + 真实扫描数据

设计原则：
1. 一张图一个结论，视觉层级极强
2. 克制底色(paper) + 单一强调色(ochre) + 局部高对比
3. 辅助信息主动退后(slate/aux线宽)
4. 数据全部来自 q1_scan_results.json，禁止编造
5. 中文标注使用 Microsoft YaHei，公式使用 LaTeX
6. 所有图表统一导出 300dpi PNG + SVG
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle, Polygon, Wedge, Arc, FancyArrowPatch
from matplotlib.collections import PatchCollection
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.patches import ConnectionPatch
import matplotlib.gridspec as gridspec
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from q1_main import (
    build_wedges, candidate_vertices, convex_hull,
    diameter_bruteforce, mec_bruteforce, unit_vector
)

# ============================================================================
# 全局配色 - Ink & Ochre v2.0（微调：提高对比度，统一色阶）
# ============================================================================

PALETTE = {
    "ink":      "#1A1A1A",   # 主文字、主轮廓、轴线
    "slate":    "#6B7B83",   # 次要文字、辅助线、网格
    "paper":    "#FAF7F0",   # 画布底色（暖白，比旧版更亮）
    "field":    "#B8CFE0",   # 角域/区域填充（浅蓝，比旧版略深）
    "geometry": "#26466D",   # 观测站、射线、多边形边（深蓝）
    "ochre":    "#C47B2B",   # 唯一强调色：直径D、关键发现、高亮
    "rust":     "#8C3A2A",   # 失败/不覆盖/gap/反例（暗红）
    "sage":     "#3D6B52",   # 成功/取等/最优/γ=1（深绿，比旧版略深）
    "gold":     "#D4A843",   # 辅助强调：源点、特殊标记
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

# 输出路径：直接到图表库的分类目录（与论文手引用路径一致）
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')  # 上升到
FIG_DIR_GEO = os.path.join(BASE_DIR, '02_几何示意')
FIG_DIR_PARAM = os.path.join(BASE_DIR, '03_参数扫描')
FIG_DIR_STAT = os.path.join(BASE_DIR, '04_统计分布')
FIG_DIR_FLOW = os.path.join(BASE_DIR, '05_算法流程')
for d in [FIG_DIR_GEO, FIG_DIR_PARAM, FIG_DIR_STAT, FIG_DIR_FLOW]:
    os.makedirs(d, exist_ok=True)

# 加载真实扫描数据
SCAN_DATA = None
def load_scan_data():
    global SCAN_DATA
    if SCAN_DATA is None:
        scan_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'q1_scan_results.json')
        with open(scan_path, 'r', encoding='utf-8') as f:
            SCAN_DATA = json.load(f)
    return SCAN_DATA


def save_fig(fig, name, use_tight=True):
    """统一保存：PNG + SVG，paper底色，按内容分类保存
    use_tight=False时不使用bbox_inches='tight'，避免角域填充扩展画布"""
    # 根据文件名判断分类
    if name.startswith('fig5_1_6') or name.startswith('fig5_1_8') or name.startswith('fig5_1_11') or name.startswith('fig5_1_12') or name.startswith('fig5_1_13'):
        out_dir = FIG_DIR_PARAM
    elif name.startswith('fig5_1_7'):
        out_dir = FIG_DIR_STAT
    elif name.startswith('fig5_1_9'):
        out_dir = FIG_DIR_FLOW
    else:  # fig5_1_0 ~ fig5_1_5, fig5_1_10+
        out_dir = FIG_DIR_GEO

    png_path = os.path.join(out_dir, name + '.png')
    svg_path = os.path.join(out_dir, name + '.svg')
    if use_tight:
        fig.savefig(png_path, dpi=DPI, bbox_inches='tight', facecolor=PALETTE['paper'])
        fig.savefig(svg_path, bbox_inches='tight', facecolor=PALETTE['paper'])
    else:
        fig.savefig(png_path, dpi=DPI, facecolor=PALETTE['paper'])
        fig.savefig(svg_path, facecolor=PALETTE['paper'])
    print(f"  [OK] {name}.png + .svg -> {os.path.basename(out_dir)}/")
    plt.close(fig)


def style_ax(ax, xlabel=None, ylabel=None, title=None, equal=False):
    """统一坐标轴样式"""
    ax.set_facecolor(PALETTE['paper'])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(PALETTE['slate'])
    ax.spines['bottom'].set_color(PALETTE['slate'])
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10, color=PALETTE['ink'])
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10, color=PALETTE['ink'])
    if title:
        ax.set_title(title, fontsize=12, color=PALETTE['ink'], pad=10, weight='bold')
    if equal:
        ax.set_aspect('equal')


# ============================================================================
# 图5.1-1: 基准算例 — 角域交会 + 定位区域 + 直径 + MEC（主打图）
# ============================================================================

def fig_5_1_1_baseline():
    """基准算例：双面板设计
    左面板：全局视图（S₁/S₂/G/角域/角度标注θ₁θ₂）
    右面板：定位区域放大（直径/MEC/顶点/信息卡片）"""
    from matplotlib.patches import FancyArrowPatch, ConnectionPatch

    fig = plt.figure(figsize=(14, 6.5), facecolor=PALETTE['paper'])
    gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1.4], wspace=0.12)

    S1 = np.array([0.0, 0.0])
    S2 = np.array([600.0, 0.0])
    G = np.array([300.0, 500.0])
    eps = 1.0

    theta1 = np.rad2deg(np.arctan2(G[1]-S1[1], G[0]-S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1]-S2[1], G[0]-S2[0]))

    wedges = build_wedges([S1, S2], [theta1, theta2], eps)
    vertices = candidate_vertices(wedges)
    poly = convex_hull(vertices)

    # ================================================================
    # 左面板：全局视图
    # ================================================================
    ax_global = plt.subplot(gs[0, 0])
    ax_global.set_facecolor(PALETTE['paper'])

    # 角域填充（极淡）
    for station, theta in [(S1, theta1), (S2, theta2)]:
        wedge_patch = Wedge(station, 700, theta-eps, theta+eps,
                            facecolor=PALETTE['field'], alpha=0.12, edgecolor='none')
        ax_global.add_patch(wedge_patch)

    # 角域边界射线（淡虚线）
    for station, theta in [(S1, theta1), (S2, theta2)]:
        for angle in [theta-eps, theta+eps]:
            direction = unit_vector(angle)
            end = station + 700 * direction
            ax_global.plot([station[0], end[0]], [station[1], end[1]],
                          color=PALETTE['geometry'], linewidth=0.8, linestyle=':', alpha=0.4)

    # 中心示向度射线（粗实线）
    for station, theta, color in [(S1, theta1, PALETTE['geometry']),
                                    (S2, theta2, PALETTE['geometry'])]:
        direction = unit_vector(theta)
        end = station + 650 * direction
        ax_global.plot([station[0], end[0]], [station[1], end[1]],
                      color=color, linewidth=1.5, alpha=0.7)

    # 定位区域（小但可见）
    if poly:
        hull_pts = np.array(poly.vertices + [poly.vertices[0]])
        ax_global.fill(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['field'], alpha=0.6)
        ax_global.plot(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['geometry'],
                      linewidth=1.8, solid_capstyle='round')

    # 检测点
    ax_global.plot(S1[0], S1[1], 's', color=PALETTE['geometry'], markersize=11,
                  markeredgecolor='white', markeredgewidth=1.5, zorder=6)
    ax_global.plot(S2[0], S2[1], 's', color=PALETTE['geometry'], markersize=11,
                  markeredgecolor='white', markeredgewidth=1.5, zorder=6)
    # 源点
    ax_global.plot(G[0], G[1], '*', color=PALETTE['gold'], markersize=16,
                  markeredgecolor=PALETTE['ink'], markeredgewidth=0.8, zorder=8)

    # 标注
    ax_global.text(S1[0], S1[1]-30, 'S₁', fontsize=12, weight='bold',
                  color=PALETTE['geometry'], ha='center', va='top')
    ax_global.text(S2[0], S2[1]-30, 'S₂', fontsize=12, weight='bold',
                  color=PALETTE['geometry'], ha='center', va='top')
    ax_global.text(G[0]+18, G[1]+5, 'G', fontsize=12, weight='bold',
                  color=PALETTE['gold'], ha='left', va='center')

    # ===== 角度标注（核心改进！用圆弧+文字，美观清晰） =====
    arc_radius = 80
    # θ₁标注：在S₁处画圆弧，从x轴正方向到示向度
    arc1 = Arc(S1, 2*arc_radius, 2*arc_radius, angle=0,
               theta1=0, theta2=theta1,
               color=PALETTE['ochre'], linewidth=1.8, alpha=0.8)
    ax_global.add_patch(arc1)
    # θ₁文字标注（在圆弧中间位置）
    mid_angle1 = theta1 / 2
    text_r1 = arc_radius * 1.35
    ax_global.text(S1[0] + text_r1*np.cos(np.deg2rad(mid_angle1)),
                  S1[1] + text_r1*np.sin(np.deg2rad(mid_angle1)),
                  f'θ₁={theta1:.1f}°', fontsize=10.5, weight='bold',
                  color=PALETTE['ochre'], ha='center', va='center',
                  bbox=dict(boxstyle='round,pad=0.25', facecolor=PALETTE['paper'],
                           edgecolor=PALETTE['ochre'], linewidth=0.8, alpha=0.9))

    # θ₂标注：在S₂处画圆弧，从示向度到x轴负方向（180°）
    arc2 = Arc(S2, 2*arc_radius, 2*arc_radius, angle=0,
               theta1=theta2, theta2=180,
               color=PALETTE['ochre'], linewidth=1.8, alpha=0.8)
    ax_global.add_patch(arc2)
    # θ₂文字标注（在圆弧中间位置）
    mid_angle2 = (theta2 + 180) / 2
    text_r2 = arc_radius * 1.35
    ax_global.text(S2[0] + text_r2*np.cos(np.deg2rad(mid_angle2)),
                  S2[1] + text_r2*np.sin(np.deg2rad(mid_angle2)),
                  f'θ₂={theta2:.1f}°', fontsize=10.5, weight='bold',
                  color=PALETTE['ochre'], ha='center', va='center',
                  bbox=dict(boxstyle='round,pad=0.25', facecolor=PALETTE['paper'],
                           edgecolor=PALETTE['ochre'], linewidth=0.8, alpha=0.9))

    # 基线标注
    ax_global.annotate('', xy=(S1[0], S1[1]-45), xytext=(S2[0], S2[1]-45),
                      arrowprops=dict(arrowstyle='<->', color=PALETTE['slate'], lw=1.2))
    ax_global.text(300, S1[1]-60, '基线 S₁S₂ = 600 m', fontsize=9.5, ha='center',
                  color=PALETTE['slate'], weight='bold', style='italic')

    # 放大框：在全局视图上用虚线框出右面板的放大区域
    zoom_x1, zoom_x2 = 255, 345
    zoom_y1, zoom_y2 = 445, 550
    rect = plt.Rectangle((zoom_x1, zoom_y1), zoom_x2-zoom_x1, zoom_y2-zoom_y1,
                         fill=False, edgecolor=PALETTE['rust'], linewidth=1.5,
                         linestyle='--', alpha=0.7)
    ax_global.add_patch(rect)
    ax_global.text((zoom_x1+zoom_x2)/2, zoom_y2+8, '放大区域', fontsize=8.5,
                  color=PALETTE['rust'], ha='center', va='bottom', style='italic')

    # 全局视图样式
    ax_global.set_title('(a) 全局几何关系', fontsize=12, weight='bold',
                       color=PALETTE['ink'], pad=10)
    ax_global.set_xlim(-50, 650)
    ax_global.set_ylim(-80, 580)
    ax_global.set_aspect('equal')
    ax_global.set_xticks([0, 200, 400, 600])
    ax_global.set_yticks([0, 200, 400])
    ax_global.tick_params(labelsize=8.5, colors=PALETTE['slate'])
    ax_global.set_xlabel('X (m)', fontsize=9.5, color=PALETTE['ink'], labelpad=5)
    ax_global.set_ylabel('Y (m)', fontsize=9.5, color=PALETTE['ink'], labelpad=5)
    for spine in ['top', 'right']:
        ax_global.spines[spine].set_visible(False)
    ax_global.spines['left'].set_color(PALETTE['slate'])
    ax_global.spines['bottom'].set_color(PALETTE['slate'])
    ax_global.grid(True, alpha=0.1, linestyle='-', linewidth=0.5)

    # ================================================================
    # 右面板：定位区域放大
    # ================================================================
    ax_zoom = plt.subplot(gs[0, 1])
    ax_zoom.set_facecolor(PALETTE['paper'])

    # 角域背景（极淡，只显示边界）
    for station, theta in [(S1, theta1), (S2, theta2)]:
        for angle in [theta-eps, theta+eps]:
            direction = unit_vector(angle)
            end = station + 800 * direction
            ax_zoom.plot([station[0], end[0]], [station[1], end[1]],
                        color=PALETTE['geometry'], linewidth=0.6, linestyle=':', alpha=0.25,
                        clip_on=True)

    # 定位区域（渐变效果+粗边框）
    if poly:
        hull_pts = np.array(poly.vertices + [poly.vertices[0]])
        # 多层半透明填充模拟渐变
        for i, alpha in enumerate([0.15, 0.25, 0.35]):
            scale = 1.0 - i * 0.08
            center_poly = np.mean(poly.vertices, axis=0)
            scaled = center_poly + (hull_pts - center_poly) * scale
            ax_zoom.fill(scaled[:, 0], scaled[:, 1], color=PALETTE['field'], alpha=alpha)
        # 主填充
        ax_zoom.fill(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['field'], alpha=0.5,
                    label='定位区域 L（凸四边形）')
        # 粗边框
        ax_zoom.plot(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['geometry'],
                    linewidth=2.5, solid_capstyle='round', zorder=4)

        # 4个顶点（橙色圆点+白边）+ 顶点标注
        vertex_labels = ['V₁', 'V₂', 'V₃', 'V₄']
        for i, v in enumerate(poly.vertices):
            ax_zoom.plot(v[0], v[1], 'o', color=PALETTE['ochre'], markersize=9,
                        markeredgecolor='white', markeredgewidth=1.5, zorder=6)
            # 顶点标注（智能偏移：根据顶点相对中心位置）
            center_poly = np.mean(poly.vertices, axis=0)
            dx, dy = v[0] - center_poly[0], v[1] - center_poly[1]
            offset = 9
            if abs(dx) > abs(dy):
                tx, ty = v[0] + np.sign(dx)*offset, v[1]
                ha = 'left' if dx > 0 else 'right'
                va = 'center'
            else:
                tx, ty = v[0], v[1] + np.sign(dy)*offset
                ha = 'center'
                va = 'bottom' if dy > 0 else 'top'
            ax_zoom.text(tx, ty, vertex_labels[i], fontsize=9.5, weight='bold',
                        color=PALETTE['ochre'], ha=ha, va=va, zorder=9)

        # 直径（粗橙色+端点）
        D, (p, q) = diameter_bruteforce(poly)
        ax_zoom.plot([p[0], q[0]], [p[1], q[1]], color=PALETTE['ochre'],
                    linewidth=3.2, solid_capstyle='round', zorder=5,
                    label=f'直径 D = {D:.3f} m')
        ax_zoom.plot([p[0], q[0]], [p[1], q[1]], 'o', color=PALETTE['ochre'],
                    markersize=10, markeredgecolor='white', markeredgewidth=1.5, zorder=7)
        # D值标注（移到更靠右的位置，用箭头指向直径线，避免与虚线重叠）
        mid_x, mid_y = (p[0]+q[0])/2, (p[1]+q[1])/2
        ax_zoom.annotate(f'D = {D:.2f} m', xy=(mid_x+5, mid_y),
                        xytext=(mid_x+22, mid_y+3), fontsize=10, weight='bold',
                        color=PALETTE['ochre'], ha='left', va='center',
                        arrowprops=dict(arrowstyle='->', color=PALETTE['ochre'], lw=1.2),
                        bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['paper'],
                                 edgecolor=PALETTE['ochre'], linewidth=1, alpha=0.97),
                        zorder=8)

        # 最小包围圆（绿色虚线）
        center, R = mec_bruteforce(poly.vertices)
        circle = Circle(center, R, fill=False, edgecolor=PALETTE['sage'],
                       linewidth=2.0, linestyle='--', zorder=3,
                       label=f'最小包围圆 R_MEC = {R:.3f} m')
        ax_zoom.add_patch(circle)
        ax_zoom.plot(center[0], center[1], '+', color=PALETTE['sage'],
                    markersize=14, markeredgewidth=2.2, zorder=6)

        # 关键数值信息卡片（左上角）
        gamma = R / (D / 2)
        info_text = (f'  直径 D          = {D:.3f} m\n'
                    f'  最小包围圆 R_MEC = {R:.3f} m\n'
                    f'  缺口比 γ        = {gamma:.4f}\n'
                    f'  Jung界          = [1.0000, 1.1547]')
        ax_zoom.text(0.02, 0.98, info_text, transform=ax_zoom.transAxes,
                    fontsize=9.5, va='top', ha='left',
                    color=PALETTE['ink'],
                    bbox=dict(boxstyle='round,pad=0.5', facecolor=PALETTE['paper'],
                             edgecolor=PALETTE['sage'], linewidth=1.5, alpha=0.97),
                    zorder=10)

    # 源点G
    ax_zoom.plot(G[0], G[1], '*', color=PALETTE['gold'], markersize=20,
                markeredgecolor=PALETTE['ink'], markeredgewidth=1.0, zorder=8,
                label='真实干扰源 G')
    ax_zoom.text(G[0]-15, G[1]-8, 'G', fontsize=12, weight='bold', color=PALETTE['gold'],
                ha='right', va='center', zorder=9)

    # 放大视图样式
    ax_zoom.set_title('(b) 定位区域放大（直径与最小包围圆）', fontsize=12,
                     weight='bold', color=PALETTE['ink'], pad=10)
    ax_zoom.set_xlim(255, 345)
    ax_zoom.set_ylim(445, 550)
    ax_zoom.set_aspect('equal')
    ax_zoom.tick_params(labelsize=9, colors=PALETTE['slate'])
    ax_zoom.set_xlabel('X 坐标 (m)', fontsize=10, color=PALETTE['ink'], labelpad=6)
    ax_zoom.set_ylabel('Y 坐标 (m)', fontsize=10, color=PALETTE['ink'], labelpad=6)
    for spine in ['top', 'right']:
        ax_zoom.spines[spine].set_visible(False)
    ax_zoom.spines['left'].set_color(PALETTE['slate'])
    ax_zoom.spines['bottom'].set_color(PALETTE['slate'])
    ax_zoom.grid(True, alpha=0.12, linestyle='-', linewidth=0.5)

    # 图例（右下角）
    ax_zoom.legend(loc='lower right', fontsize=8.5, frameon=True,
                  facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'],
                  framealpha=0.95, borderpad=0.7, labelspacing=0.5)

    # 左右面板连接线（从全局放大框到右面板）
    con = ConnectionPatch(xyA=(zoom_x2, (zoom_y1+zoom_y2)/2), coordsA=ax_global.transData,
                         xyB=(0, 0.5), coordsB=ax_zoom.transAxes,
                         color=PALETTE['rust'], linewidth=1.2, linestyle='--', alpha=0.5,
                         arrowstyle='->', mutation_scale=15)
    fig.add_artist(con)

    fig.suptitle('图5.1-1  基准算例：双站交会定位区域与几何特征量',
                fontsize=14, weight='bold', color=PALETTE['ink'], y=1.01)
    plt.tight_layout()
    save_fig(fig, 'fig5_1_1_baseline', use_tight=False)


# ============================================================================
# 图5.1-2: 角域构造演化 — 从单站不确定到双站精确定位
# ============================================================================

def fig_5_1_2_wedge_evolution():
    """重新设计：三面板演化叙事，步骤编号+演化箭头+统一视觉风格"""
    from matplotlib.patches import FancyArrowPatch

    fig = plt.figure(figsize=(14, 5), facecolor=PALETTE['paper'])
    gs = gridspec.GridSpec(1, 3, width_ratios=[1, 1, 1.4], wspace=0.25)

    # 统一的子图样式函数
    def style_subplot(ax, title, step_num):
        ax.set_facecolor(PALETTE['paper'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(PALETTE['slate'])
        ax.spines['bottom'].set_color(PALETTE['slate'])
        ax.set_title(title, fontsize=12, weight='bold', color=PALETTE['ink'], pad=12)
        ax.set_xticks([])
        ax.set_yticks([])
        # 步骤编号圆形（移到更靠外的位置，避免与标题重叠）
        circle = plt.Circle((0.045, 0.88), 0.038, transform=ax.transAxes,
                           facecolor=PALETTE['geometry'], edgecolor='white', linewidth=2, zorder=10)
        ax.add_patch(circle)
        ax.text(0.045, 0.88, str(step_num), transform=ax.transAxes,
               fontsize=11, weight='bold', color='white', ha='center', va='center', zorder=11)

    # --- 面板a: 单站角域 ---
    ax_a = plt.subplot(gs[0, 0])
    S1 = np.array([0, 0])
    theta, eps = 45, 15
    # 角域填充（渐变感：多层）
    for r, alpha in [(250, 0.15), (200, 0.2), (150, 0.25)]:
        wedge1 = Wedge(S1, r, theta-eps, theta+eps,
                       facecolor=PALETTE['field'], alpha=alpha, edgecolor='none')
        ax_a.add_patch(wedge1)
    # 角域边界
    wedge_border = Wedge(S1, 250, theta-eps, theta+eps,
                         facecolor='none', edgecolor=PALETTE['geometry'],
                         linewidth=1.2, linestyle='--', alpha=0.6)
    ax_a.add_patch(wedge_border)
    # 中心示向度射线
    direction = unit_vector(theta)
    end = S1 + 250 * direction
    ax_a.plot([S1[0], end[0]], [S1[1], end[1]],
             color=PALETTE['geometry'], linewidth=2.0, alpha=0.8, solid_capstyle='round')
    # 检测点
    ax_a.plot(S1[0], S1[1], 's', color=PALETTE['geometry'], markersize=14,
             markeredgecolor='white', markeredgewidth=1.5, zorder=6)
    ax_a.text(S1[0], S1[1]-28, '检测站 S₁', fontsize=10, ha='center',
             weight='bold', color=PALETTE['geometry'])
    # 不确定区域标注
    ax_a.text(175, 175, '宽不确定区域', fontsize=11, ha='center',
             weight='bold', color=PALETTE['geometry'],
             bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['paper'],
                      edgecolor=PALETTE['field'], linewidth=1.5, alpha=0.95))
    ax_a.text(175, 145, '（仅方向，无距离）', fontsize=9, ha='center',
             style='italic', color=PALETTE['slate'])
    style_subplot(ax_a, '单站测向', 1)
    ax_a.set_xlim(-50, 300)
    ax_a.set_ylim(-60, 300)
    ax_a.set_aspect('equal')

    # --- 面板b: 双站交会 ---
    ax_b = plt.subplot(gs[0, 1])
    S1 = np.array([0, 0])
    S2 = np.array([200, 0])
    G = np.array([100, 170])
    theta1 = np.rad2deg(np.arctan2(G[1]-S1[1], G[0]-S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1]-S2[1], G[0]-S2[0]))
    eps = 8
    # 两个角域（不同色调）
    w1 = Wedge(S1, 280, theta1-eps, theta1+eps,
               facecolor=PALETTE['field'], alpha=0.2, edgecolor='none')
    w2 = Wedge(S2, 280, theta2-eps, theta2+eps,
               facecolor=PALETTE['ochre'], alpha=0.12, edgecolor='none')
    ax_b.add_patch(w1); ax_b.add_patch(w2)
    # 角域边界射线
    for station, theta in [(S1, theta1), (S2, theta2)]:
        for angle in [theta-eps, theta+eps]:
            direction = unit_vector(angle)
            end = station + 280 * direction
            ax_b.plot([station[0], end[0]], [station[1], end[1]],
                     color=PALETTE['geometry'], linewidth=0.9, linestyle='--', alpha=0.45)
    # 定位区域
    wedges = build_wedges([S1, S2], [theta1, theta2], eps)
    vertices = candidate_vertices(wedges)
    poly = convex_hull(vertices)
    if poly:
        hull_pts = np.array(poly.vertices + [poly.vertices[0]])
        ax_b.fill(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['geometry'], alpha=0.55)
        ax_b.plot(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['geometry'], linewidth=2.0)
    # 检测点
    ax_b.plot([S1[0], S2[0]], [S1[1], S2[1]], 's', color=PALETTE['geometry'],
             markersize=12, markeredgecolor='white', markeredgewidth=1.5, zorder=6)
    ax_b.text(S1[0], S1[1]-22, 'S₁', fontsize=10, ha='center', weight='bold', color=PALETTE['geometry'])
    ax_b.text(S2[0], S2[1]-22, 'S₂', fontsize=10, ha='center', weight='bold', color=PALETTE['geometry'])
    # 区域收窄标注
    ax_b.text(100, 230, '区域收窄', fontsize=11, ha='center',
             weight='bold', color=PALETTE['geometry'],
             bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['paper'],
                      edgecolor=PALETTE['geometry'], linewidth=1.5, alpha=0.95))
    ax_b.text(100, 205, '（双站约束）', fontsize=9, ha='center',
             style='italic', color=PALETTE['slate'])
    style_subplot(ax_b, '双站交会', 2)
    ax_b.set_xlim(-30, 230)
    ax_b.set_ylim(-40, 260)
    ax_b.set_aspect('equal')

    # --- 面板c: 精确结果 ---
    ax_c = plt.subplot(gs[0, 2])
    S1 = np.array([0.0, 0.0])
    S2 = np.array([600.0, 0.0])
    G = np.array([300.0, 500.0])
    eps = 1.0
    theta1 = np.rad2deg(np.arctan2(G[1]-S1[1], G[0]-S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1]-S2[1], G[0]-S2[0]))
    wedges = build_wedges([S1, S2], [theta1, theta2], eps)
    vertices = candidate_vertices(wedges)
    poly = convex_hull(vertices)
    if poly:
        hull_pts = np.array(poly.vertices + [poly.vertices[0]])
        ax_c.fill(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['field'], alpha=0.55)
        ax_c.plot(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['geometry'], linewidth=2.2)
        # 直径
        D, (p, q) = diameter_bruteforce(poly)
        ax_c.plot([p[0], q[0]], [p[1], q[1]], color=PALETTE['ochre'],
                 linewidth=2.8, solid_capstyle='round', zorder=5)
        ax_c.plot([p[0], q[0]], [p[1], q[1]], 'o', color=PALETTE['ochre'],
                 markersize=8, markeredgecolor='white', markeredgewidth=1.2, zorder=6)
        # MEC
        center, R = mec_bruteforce(poly.vertices)
        circle = Circle(center, R, fill=False, edgecolor=PALETTE['sage'],
                       linewidth=1.8, linestyle='--', zorder=4)
        ax_c.add_patch(circle)
        ax_c.plot(center[0], center[1], '+', color=PALETTE['sage'],
                 markersize=12, markeredgewidth=2, zorder=6)
        # 数值标注
        ax_c.text(0.03, 0.97, f'D = {D:.2f} m\nR_MEC = {R:.2f} m\nγ = {R/(D/2):.4f}',
                 transform=ax_c.transAxes, fontsize=9.5, va='top',
                 bbox=dict(boxstyle='round,pad=0.5', facecolor=PALETTE['paper'],
                          edgecolor=PALETTE['sage'], linewidth=1.2, alpha=0.95))
    ax_c.plot(G[0], G[1], '*', color=PALETTE['gold'], markersize=16,
             markeredgecolor=PALETTE['ink'], markeredgewidth=0.8, zorder=7)
    ax_c.text(G[0]+10, G[1], 'G', fontsize=11, weight='bold', color=PALETTE['gold'])
    style_subplot(ax_c, '精确定位（ε=1°）', 3)
    ax_c.set_xlabel('X (m)', fontsize=10, color=PALETTE['ink'])
    ax_c.set_ylabel('Y (m)', fontsize=10, color=PALETTE['ink'])
    ax_c.set_xlim(275, 325)
    ax_c.set_ylim(470, 530)
    ax_c.set_aspect('equal')
    ax_c.set_xticks([280, 290, 300, 310, 320])
    ax_c.set_yticks([480, 490, 500, 510, 520])
    ax_c.tick_params(labelsize=8, colors=PALETTE['slate'])

    # --- 面板间演化箭头（用figure坐标，位置精确） ---
    arrow_positions = [
        (0.315, 0.345),  # a→b
        (0.620, 0.650),  # b→c
    ]
    for x_start, x_end in arrow_positions:
        arrow = FancyArrowPatch(
            (x_start, 0.5), (x_end, 0.5),
            arrowstyle='->,head_width=0.35,head_length=0.5',
            mutation_scale=22, color=PALETTE['ochre'], linewidth=2.8,
            transform=fig.transFigure, zorder=20)
        fig.patches.append(arrow)

    fig.suptitle('图5.1-2  角域构造演化：从单站宽不确定到双站精确定位',
                 fontsize=14, weight='bold', color=PALETTE['ink'], y=1.02)
    plt.tight_layout()
    save_fig(fig, 'fig5_1_2_wedge_evolution')


# ============================================================================
# 图5.1-3: Jung定理反例 — 等边三角形直径圆不能覆盖
# ============================================================================

def fig_5_1_3_jung_counterexample():
    """等边三角形：直径圆（虚线rust）不能覆盖顶点C；MEC（实线sage）可以覆盖
    Thales半圆展示90°轨迹，C点在半圆外（60°<90°）"""
    fig, ax = plt.subplots(figsize=(7, 6), facecolor=PALETTE['paper'])

    side = 100
    vertices = np.array([[0, 0], [side, 0], [side/2, side*np.sqrt(3)/2]])

    # 等边三角形
    triangle = Polygon(vertices, fill=False, edgecolor=PALETTE['ink'], linewidth=LW['main'])
    ax.add_patch(triangle)

    # 顶点标注
    labels = ['A', 'B', 'C']
    offsets = [(-10, -14), (10, -14), (0, 10)]
    for v, label, offset in zip(vertices, labels, offsets):
        ax.plot(v[0], v[1], 'o', color=PALETTE['ink'], markersize=6)
        ax.text(v[0]+offset[0], v[1]+offset[1], label, fontsize=12,
               ha='center', weight='bold', color=PALETTE['ink'])

    # 直径（底边AB）
    p1, p2 = vertices[0], vertices[1]
    D = np.linalg.norm(p2 - p1)
    center_D = (p1 + p2) / 2
    R_D = D / 2
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=PALETTE['ochre'],
           linewidth=LW['main']+0.5, solid_capstyle='round')
    # 直径标注移到线上方，避免与底部结论文本框重叠
    ax.text(side/2, 6, f'直径 D = {D:.0f} m', fontsize=10, ha='center',
           weight='bold', color=PALETTE['ochre'],
           bbox=dict(boxstyle='round,pad=0.2', facecolor=PALETTE['paper'],
                    edgecolor=PALETTE['ochre'], linewidth=0.8, alpha=0.9))

    # Thales半圆（90°轨迹）
    thales = Circle(center_D, R_D, fill=False, edgecolor=PALETTE['slate'],
                   linewidth=LW['theory'], linestyle='--', label='Thales轨迹（∠=90°）')
    ax.add_patch(thales)
    ax.text(center_D[0], R_D+8, '90°', fontsize=9, ha='center', color=PALETTE['slate'])

    # 直径圆（失败，虚线rust）
    circle_D = Circle(center_D, R_D, fill=False, edgecolor=PALETTE['rust'],
                     linewidth=LW['theory'], linestyle=':', alpha=0.7,
                     label='直径圆（❌ 不能覆盖）')
    ax.add_patch(circle_D)

    # MEC（成功，实线sage）
    center_MEC = np.array([side/2, side/(2*np.sqrt(3))])
    R_MEC = side / np.sqrt(3)
    circle_MEC = Circle(center_MEC, R_MEC, fill=False, edgecolor=PALETTE['sage'],
                       linewidth=LW['main'], linestyle='-', alpha=0.85,
                       label=f'最小包围圆（✅ 可覆盖，R={R_MEC:.1f}m）')
    ax.add_patch(circle_MEC)
    ax.plot(center_MEC[0], center_MEC[1], '+', color=PALETTE['sage'],
           markersize=10, markeredgewidth=1.8)

    # gap标注：C点到Thales半圆的距离
    p3 = vertices[2]
    direction = (p3 - center_D) / np.linalg.norm(p3 - center_D)
    thales_point = center_D + R_D * direction
    ax.plot([thales_point[0], p3[0]], [thales_point[1], p3[1]],
           color=PALETTE['rust'], linewidth=LW['theory'], linestyle='-', alpha=0.6)
    gap = np.linalg.norm(p3 - center_D) - R_D
    gap_mid = (thales_point + p3) / 2
    ax.text(gap_mid[0]+10, gap_mid[1], f'缺口 = {gap:.1f}m', fontsize=8,
           color=PALETTE['rust'],
           bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['paper'],
                    edgecolor=PALETTE['rust'], linewidth=0.8))

    # 60°标注（视觉中心）
    ax.text(p3[0], p3[1]-18, r'$\angle ACB = 60° < 90°$', fontsize=12,
           ha='center', weight='bold', color=PALETTE['rust'],
           bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                    edgecolor=PALETTE['rust'], linewidth=1.5))

    # 核心结论
    ax.text(0.5, 0.02,
            '顶点C落在Thales半圆外（60°<90°）\n⇒ 以直径D为直径的圆不能覆盖等边三角形\n'
            '⇒ Jung定理：R_MEC ≤ D/√3，最坏缺口 2/√3 ≈ 15.5%',
            transform=ax.transAxes, fontsize=9, ha='center', va='bottom',
            bbox=dict(boxstyle='round,pad=0.5', facecolor=PALETTE['paper'],
                     edgecolor=PALETTE['slate'], linewidth=0.8, alpha=0.95))

    style_ax(ax, xlabel='X (m)', ylabel='Y (m)',
              title='图5.1-3 Jung定理反例：等边三角形直径圆不能覆盖', equal=True)
    ax.set_xlim(-15, 115)
    ax.set_ylim(-25, 115)
    ax.legend(loc='upper right', fontsize=8, framealpha=0.95,
              facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'])

    save_fig(fig, 'fig5_1_3_jung_counterexample')


# ============================================================================
# 图5.1-4: Jung夹逼 — 60°扇区剖面 + 半径尺（量化夹逼厚度）
# ============================================================================

def fig_5_1_4_jung_sandwich():
    """重新设计：60°扇区剖面 + 垂直半径尺 + 颜色条夹逼 + 左右关联"""
    from matplotlib.patches import ConnectionPatch

    fig = plt.figure(figsize=(11, 5.5), facecolor=PALETTE['paper'])
    gs = gridspec.GridSpec(1, 2, width_ratios=[2.2, 1], wspace=0.15)

    # 基准数据
    S1 = np.array([0.0, 0.0])
    S2 = np.array([600.0, 0.0])
    G = np.array([300.0, 500.0])
    eps = 1.0
    theta1 = np.rad2deg(np.arctan2(G[1]-S1[1], G[0]-S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1]-S2[1], G[0]-S2[0]))
    wedges = build_wedges([S1, S2], [theta1, theta2], eps)
    vertices = candidate_vertices(wedges)
    poly = convex_hull(vertices)

    D, _ = diameter_bruteforce(poly)
    center_mec, R_mec = mec_bruteforce(poly.vertices)
    R_lower = D / 2
    R_upper = D / np.sqrt(3)
    gamma = R_mec / R_lower

    # ===== 左面板：60°扇区剖面 =====
    ax_sector = plt.subplot(gs[0, 0])
    sector_angle = 60
    sector_start = 60

    # 背景：从D/2到D/√3的渐变环带（多层半透明）
    for i in range(20):
        r = R_lower + (R_upper - R_lower) * (i / 20)
        alpha = 0.06 + 0.02 * (i / 20)
        wedge = Wedge(center_mec, r, sector_start, sector_start+sector_angle,
                      facecolor=PALETTE['ochre'], alpha=alpha, edgecolor='none')
        ax_sector.add_patch(wedge)

    # D/2内圈（绿色）
    wedge_lower = Wedge(center_mec, R_lower, sector_start, sector_start+sector_angle,
                        facecolor=PALETTE['sage'], alpha=0.25,
                        edgecolor=PALETTE['sage'], linewidth=2.0)
    ax_sector.add_patch(wedge_lower)

    # R_MEC线（橙色，与D/2重合时用虚线区分）
    if abs(R_mec - R_lower) < 0.01:
        wedge_mec = Wedge(center_mec, R_mec, sector_start, sector_start+sector_angle,
                          facecolor='none', edgecolor=PALETTE['ochre'],
                          linewidth=2.5, linestyle='--')
        ax_sector.add_patch(wedge_mec)

    # D/√3上界（灰色虚线）
    arc_upper = Arc(center_mec, 2*R_upper, 2*R_upper, angle=0,
                   theta1=sector_start, theta2=sector_start+sector_angle,
                   color=PALETTE['slate'], linewidth=2.0, linestyle=':')
    ax_sector.add_patch(arc_upper)

    # 扇区边界射线
    for angle in [sector_start, sector_start+sector_angle]:
        rad = np.deg2rad(angle)
        end = center_mec + R_upper * 1.12 * np.array([np.cos(rad), np.sin(rad)])
        ax_sector.plot([center_mec[0], end[0]], [center_mec[1], end[1]],
                      color=PALETTE['ink'], linewidth=1.5, alpha=0.7)

    # 圆心
    ax_sector.plot(center_mec[0], center_mec[1], '+', color=PALETTE['ink'],
                   markersize=12, markeredgewidth=2.0, zorder=5)

    # 半径标注（沿中线）
    mid_angle = sector_start + sector_angle / 2
    rad_mid = np.deg2rad(mid_angle)
    # D/2标注
    pos_lower = center_mec + R_lower * 0.55 * np.array([np.cos(rad_mid), np.sin(rad_mid)])
    ax_sector.text(pos_lower[0], pos_lower[1], 'D/2', fontsize=11, ha='center',
                  color=PALETTE['sage'], weight='bold')
    # R_MEC标注（在D/2和D/√3之间）
    pos_mec = center_mec + (R_lower + R_upper) * 0.42 * np.array([np.cos(rad_mid), np.sin(rad_mid)])
    ax_sector.text(pos_mec[0], pos_mec[1], 'R_MEC', fontsize=11, ha='center',
                  color=PALETTE['ochre'], weight='bold')
    # D/√3标注
    pos_upper = center_mec + R_upper * 0.92 * np.array([np.cos(rad_mid), np.sin(rad_mid)])
    ax_sector.text(pos_upper[0], pos_upper[1], 'D/√3', fontsize=11, ha='center',
                  color=PALETTE['slate'], weight='bold')

    # 60°角度标注
    angle_label_pos = center_mec + R_upper * 0.25 * np.array([np.cos(rad_mid), np.sin(rad_mid)])
    ax_sector.text(angle_label_pos[0], angle_label_pos[1], '60°', fontsize=10,
                  color=PALETTE['ink'], style='italic', alpha=0.7)

    ax_sector.set_facecolor(PALETTE['paper'])
    ax_sector.set_title('60°扇区剖面', fontsize=13, weight='bold', color=PALETTE['ink'], pad=12)
    ax_sector.set_xlim(center_mec[0]-R_upper*1.3, center_mec[0]+R_upper*0.4)
    ax_sector.set_ylim(center_mec[1]-R_upper*0.35, center_mec[1]+R_upper*1.3)
    ax_sector.set_aspect('equal')
    ax_sector.set_xticks([])
    ax_sector.set_yticks([])
    for spine in ax_sector.spines.values():
        spine.set_visible(False)

    # ===== 右面板：垂直半径尺 =====
    ax_ruler = plt.subplot(gs[0, 1])
    ax_ruler.set_xlim(0, 1)
    ax_ruler.set_ylim(R_lower * 0.96, R_upper * 1.04)

    # 背景颜色条（从D/2到D/√3的渐变）
    for i in range(30):
        y = R_lower + (R_upper - R_lower) * (i / 30)
        alpha = 0.1 + 0.03 * (i / 30)
        ax_ruler.axhspan(y, y + (R_upper - R_lower) / 30,
                         xmin=0.35, xmax=0.55, facecolor=PALETTE['ochre'], alpha=alpha)

    # D/2 = R_MEC 重合线（绿色粗线）
    ax_ruler.axhline(R_lower, color=PALETTE['sage'], linewidth=3.0, xmin=0.3, xmax=0.6, zorder=5)
    ax_ruler.text(0.25, R_lower, 'D/2 = R_MEC', fontsize=10, ha='right', va='center',
                  color=PALETTE['sage'], weight='bold')
    ax_ruler.text(0.65, R_lower, f'{R_lower:.3f} m', fontsize=10, ha='left', va='center',
                  color=PALETTE['sage'], weight='bold')

    # D/√3 上界线（灰色虚线）
    ax_ruler.axhline(R_upper, color=PALETTE['slate'], linewidth=2.0, linestyle=':',
                    xmin=0.3, xmax=0.6, zorder=5)
    ax_ruler.text(0.25, R_upper, 'D/√3', fontsize=10, ha='right', va='center',
                  color=PALETTE['slate'], weight='bold')
    ax_ruler.text(0.65, R_upper, f'{R_upper:.3f} m', fontsize=10, ha='left', va='center',
                  color=PALETTE['slate'], weight='bold')

    # γ标注（带箭头指向重合线）
    gamma_y = (R_lower + R_upper) / 2
    ax_ruler.annotate(f'γ = {gamma:.4f}\n下界取等',
                     xy=(0.45, R_lower), xytext=(0.45, gamma_y),
                     fontsize=10, ha='center', va='center', color=PALETTE['sage'],
                     weight='bold',
                     arrowprops=dict(arrowstyle='->', color=PALETTE['sage'], lw=1.8),
                     bbox=dict(boxstyle='round,pad=0.5', facecolor=PALETTE['paper'],
                              edgecolor=PALETTE['sage'], linewidth=1.2, alpha=0.95))

    # 夹逼范围标注
    ax_ruler.text(0.45, R_upper * 1.015, 'Jung夹逼范围', fontsize=9, ha='center',
                  color=PALETTE['ink'], style='italic', alpha=0.7)

    ax_ruler.set_facecolor(PALETTE['paper'])
    ax_ruler.set_title('半径尺', fontsize=13, weight='bold', color=PALETTE['ink'], pad=12)
    ax_ruler.set_xticks([])
    ax_ruler.set_yticks([])
    for spine in ax_ruler.spines.values():
        spine.set_visible(False)

    # ===== 左右关联连接线 =====
    # 左面板D/2弧中点 → 右面板D/2线
    con1 = ConnectionPatch(xyA=(center_mec[0] + R_lower*np.cos(rad_mid),
                                center_mec[1] + R_lower*np.sin(rad_mid)),
                          coordsA=ax_sector.transData,
                          xyB=(0.3, R_lower), coordsB=ax_ruler.transData,
                          color=PALETTE['sage'], linewidth=1.2, linestyle='--', alpha=0.5)
    fig.add_artist(con1)
    # 左面板D/√3弧中点 → 右面板D/√3线
    con2 = ConnectionPatch(xyA=(center_mec[0] + R_upper*np.cos(rad_mid),
                                center_mec[1] + R_upper*np.sin(rad_mid)),
                          coordsA=ax_sector.transData,
                          xyB=(0.3, R_upper), coordsB=ax_ruler.transData,
                          color=PALETTE['slate'], linewidth=1.2, linestyle='--', alpha=0.5)
    fig.add_artist(con2)

    fig.suptitle(f'图5.1-4  Jung夹逼：D/2 = {R_lower:.3f} ≤ R_MEC = {R_mec:.3f} ≤ D/√3 = {R_upper:.3f} m',
                 fontsize=14, weight='bold', color=PALETTE['ink'], y=1.02)
    plt.tight_layout()
    save_fig(fig, 'fig5_1_4_jung_sandwich')


print("=" * 70)
print("Q1 图表统一美化版 v2.0 — 几何示意图部分加载完成")
print("=" * 70)


# ============================================================================
# 图5.1-5: 顶点过滤示意 — 6候选交点 → 4真顶点
# ============================================================================

def fig_5_1_5_vertex_filtering():
    """左：4条边界射线两两求交得6个候选交点（含2个假交点在检测点处）
    右：落在所有角域内的4个真顶点构成定位区域"""
    from matplotlib.patches import Polygon as MplPoly

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6), facecolor=PALETTE['paper'])

    S1 = (0, 0)
    S2 = (600, 0)
    G = (300, 500)
    EPS_DEG = 1.0
    EPS_RAD = np.radians(EPS_DEG)

    theta1 = np.degrees(np.arctan2(G[1]-S1[1], G[0]-S1[0]))
    theta2 = np.degrees(np.arctan2(G[1]-S2[1], G[0]-S2[0]))

    def ray_intersection(p1, deg1, p2, deg2):
        d1 = (np.cos(np.radians(deg1)), np.sin(np.radians(deg1)))
        d2 = (np.cos(np.radians(deg2)), np.sin(np.radians(deg2)))
        det = d1[0]*d2[1] - d1[1]*d2[0]
        if abs(det) < 1e-10:
            return None
        t = ((p2[0]-p1[0])*d2[1] - (p2[1]-p1[1])*d2[0]) / det
        return (p1[0] + t*d1[0], p1[1] + t*d1[1])

    def point_in_wedge(p, station, theta_deg, eps_deg):
        angle = np.degrees(np.arctan2(p[1]-station[1], p[0]-station[0])) % 360
        tol = 1e-6
        low = (theta_deg - eps_deg - tol) % 360
        high = (theta_deg + eps_deg + tol) % 360
        if low <= high:
            return low <= angle <= high
        return angle >= low or angle <= high

    rays = [
        ('S1_low', S1, theta1 - EPS_DEG),
        ('S1_high', S1, theta1 + EPS_DEG),
        ('S2_low', S2, theta2 - EPS_DEG),
        ('S2_high', S2, theta2 + EPS_DEG),
    ]

    candidates = []
    for i in range(len(rays)):
        for j in range(i+1, len(rays)):
            name1, p1, d1 = rays[i]
            name2, p2, d2 = rays[j]
            pt = ray_intersection(p1, d1, p2, d2)
            if pt:
                in_w1 = point_in_wedge(pt, S1, theta1, EPS_DEG)
                in_w2 = point_in_wedge(pt, S2, theta2, EPS_DEG)
                candidates.append({'name': f'{name1}×{name2}', 'point': pt,
                                  'is_vertex': in_w1 and in_w2})

    true_vertices = [c['point'] for c in candidates if c['is_vertex']]
    center = (sum(p[0] for p in true_vertices)/len(true_vertices),
              sum(p[1] for p in true_vertices)/len(true_vertices))
    true_vertices.sort(key=lambda p: np.arctan2(p[1]-center[1], p[0]-center[0]))

    # --- 左图：全部候选交点 ---
    ax = ax1
    for name, p, d in rays:
        end = (p[0] + 700*np.cos(np.radians(d)), p[1] + 700*np.sin(np.radians(d)))
        ax.plot([p[0], end[0]], [p[1], end[1]], 'k-', alpha=0.35, linewidth=0.7)

    w1 = Wedge(S1, 700, theta1-EPS_DEG, theta1+EPS_DEG, alpha=0.1, color='blue', clip_on=True)
    w2 = Wedge(S2, 700, theta2-EPS_DEG, theta2+EPS_DEG, alpha=0.1, color='red', clip_on=True)
    ax.add_patch(w1); ax.add_patch(w2)

    ax.plot(*S1, 's', color=PALETTE['geometry'], markersize=10, label='检测点')
    ax.plot(*S2, 's', color=PALETTE['geometry'], markersize=10)
    ax.text(S1[0], S1[1]-35, 'S₁', fontsize=10, ha='center', weight='bold', color=PALETTE['geometry'])
    ax.text(S2[0], S2[1]-35, 'S₂', fontsize=10, ha='center', weight='bold', color=PALETTE['geometry'])
    ax.plot(*G, '*', color=PALETTE['gold'], markersize=16, label='源')
    ax.text(G[0]+15, G[1]+10, 'G', fontsize=11, weight='bold', color=PALETTE['ink'])

    for c in candidates:
        if c['is_vertex']:
            ax.plot(*c['point'], 'o', color=PALETTE['ochre'], markersize=9, zorder=5)
        else:
            ax.plot(*c['point'], 'x', color=PALETTE['rust'], markersize=11,
                   markeredgewidth=2, zorder=5)
            # 假交点标注：移到点上方，避免与检测点标注重叠
            px, py = c['point']
            if px < 300:
                ax.annotate('假交点', xy=c['point'], xytext=(px-15, py+20),
                           fontsize=8, color=PALETTE['rust'], fontstyle='italic', ha='right')
            else:
                ax.annotate('假交点', xy=c['point'], xytext=(px+15, py+20),
                           fontsize=8, color=PALETTE['rust'], fontstyle='italic', ha='left')

    style_ax(ax, xlabel='X (m)', ylabel='Y (m)', title='(a) 4条射线两两求交 → 6个候选交点', equal=True)
    ax.set_xlim(-50, 650); ax.set_ylim(-50, 600)
    ax.legend(loc='lower right', fontsize=9)
    ax.text(0.05, 0.95, 'a', transform=ax.transAxes, fontsize=14, weight='bold', va='top')

    # --- 右图：过滤后真顶点 ---
    ax = ax2
    w1 = Wedge(S1, 700, theta1-EPS_DEG, theta1+EPS_DEG, alpha=0.08, color='blue')
    w2 = Wedge(S2, 700, theta2-EPS_DEG, theta2+EPS_DEG, alpha=0.08, color='red')
    ax.add_patch(w1); ax.add_patch(w2)

    poly = MplPoly(true_vertices, closed=True, alpha=0.5, color=PALETTE['field'],
                   edgecolor=PALETTE['geometry'], linewidth=LW['main'], label='定位区域 L')
    ax.add_patch(poly)

    ax.plot(*S1, 's', color=PALETTE['geometry'], markersize=10)
    ax.plot(*S2, 's', color=PALETTE['geometry'], markersize=10)
    ax.plot(*G, '*', color=PALETTE['gold'], markersize=16)

    for i, v in enumerate(true_vertices):
        ax.plot(*v, 'o', color=PALETTE['ochre'], markersize=10, zorder=5)
        # 智能偏移：根据顶点相对中心(300,500)的位置选择标注方向
        cx, cy = 300.0, 500.0
        dx, dy = v[0] - cx, v[1] - cy
        if abs(dx) < 5 and dy > 0:      # 顶部
            offset, ha = (0, 16), 'center'
        elif abs(dx) < 5 and dy < 0:    # 底部
            offset, ha = (0, -26), 'center'
        elif dx < 0:                      # 左侧
            offset, ha = (-60, 0), 'right'
        else:                              # 右侧
            offset, ha = (18, 0), 'left'
        ax.annotate(f'V{i+1}\n({v[0]:.1f},{v[1]:.1f})', xy=v,
                   xytext=(v[0]+offset[0], v[1]+offset[1]), fontsize=8,
                   fontweight='bold', ha=ha,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['paper'],
                            edgecolor=PALETTE['ochre'], linewidth=0.8, alpha=0.95))

    # 过滤规则文本框移到右侧空白区，避免与V4标注重叠
    ax.text(0.62, 0.97, '过滤规则：\n交点必须同时落在\nS₁和S₂的角域内\n6候选 → 4真顶点',
           transform=ax.transAxes, fontsize=9, va='top',
           bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['paper'],
                    edgecolor=PALETTE['sage'], linewidth=1, alpha=0.95))

    style_ax(ax, xlabel='X (m)', ylabel='Y (m)', title='(b) 角域内过滤 → 4个真顶点', equal=True)
    ax.set_xlim(250, 350); ax.set_ylim(450, 550)
    ax.legend(loc='lower left', fontsize=9)
    ax.text(0.05, 0.95, 'b', transform=ax.transAxes, fontsize=14, weight='bold', va='top')

    fig.suptitle('图5.1-5 顶点过滤：边界射线求交 → 角域内过滤 → 凸多边形定位区域',
                 fontsize=13, weight='bold', y=1.02)
    plt.tight_layout()
    save_fig(fig, 'fig5_1_5_vertex_filtering')


# ============================================================================
# 图5.1-6: 参数扫描 — D vs φ 和 D vs ε（双面板，替代3D图）
# ============================================================================

def fig_5_1_6_param_scan():
    """左：D随交会角φ变化（φ越小D越大，φ=90°时D最小）
    右：D随误差半角ε变化（D∝ε线性增长）"""
    data = load_scan_data()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), facecolor=PALETTE['paper'])

    # --- 左：D vs φ ---
    scan_phi = data['scan_phi']
    phi_vals = [r['phi'] for r in scan_phi]
    D_vals = [r['D'] for r in scan_phi]

    ax1.plot(phi_vals, D_vals, 'o-', color=PALETTE['geometry'], linewidth=LW['main'],
            markersize=7, label='实测 D(φ)')

    # 理论曲线：D = 2ε_rad * L / sinφ（φ≥90°时等号）
    eps_rad = np.radians(1.0)
    L = 600.0  # S1S2距离
    phi_theory = np.linspace(min(phi_vals), max(phi_vals), 100)
    D_theory = 2 * eps_rad * L / np.sin(np.radians(phi_theory))
    ax1.plot(phi_theory, D_theory, '--', color=PALETTE['ochre'], linewidth=LW['theory'],
            label=r'理论：$D = 2\varepsilon_{rad} \cdot L / \sin\varphi$')

    # 标注基准点
    idx_61 = min(range(len(phi_vals)), key=lambda i: abs(phi_vals[i]-61.92))
    ax1.annotate(f'基准算例\nφ={phi_vals[idx_61]:.1f}°, D={D_vals[idx_61]:.2f}m',
                xy=(phi_vals[idx_61], D_vals[idx_61]),
                xytext=(phi_vals[idx_61]+15, D_vals[idx_61]+5),
                fontsize=9, color=PALETTE['rust'],
                arrowprops=dict(arrowstyle='->', color=PALETTE['rust'], lw=1),
                bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['paper'], alpha=0.9))

    style_ax(ax1, xlabel='交会角 φ (°)', ylabel='定位区域直径 D (m)',
              title='(a) D 随交会角 φ 的变化')
    ax1.legend(fontsize=9, loc='upper right')
    ax1.grid(True, alpha=0.25)
    ax1.text(0.05, 0.95, 'a', transform=ax1.transAxes, fontsize=13, weight='bold', va='top')

    # --- 右：D vs ε ---
    scan_eps = data['scan_eps']
    eps_vals = [r['eps'] for r in scan_eps]
    D_eps = [r['D'] for r in scan_eps]

    ax2.plot(eps_vals, D_eps, 's-', color=PALETTE['geometry'], linewidth=LW['main'],
            markersize=7, label='实测 D(ε)')

    # 理论线性拟合
    coeffs = np.polyfit(eps_vals, D_eps, 1)
    eps_fit = np.linspace(min(eps_vals), max(eps_vals), 50)
    D_fit = np.polyval(coeffs, eps_fit)
    ax2.plot(eps_fit, D_fit, '--', color=PALETTE['ochre'], linewidth=LW['theory'],
            label=f'线性拟合：D = {coeffs[0]:.2f}·ε + {coeffs[1]:.2f}')

    # 标注ε=1°
    idx_1 = min(range(len(eps_vals)), key=lambda i: abs(eps_vals[i]-1.0))
    ax2.annotate(f'题设 ε=1°\nD={D_eps[idx_1]:.2f}m',
                xy=(eps_vals[idx_1], D_eps[idx_1]),
                xytext=(eps_vals[idx_1]+0.3, D_eps[idx_1]+3),
                fontsize=9, color=PALETTE['rust'],
                arrowprops=dict(arrowstyle='->', color=PALETTE['rust'], lw=1),
                bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['paper'], alpha=0.9))

    style_ax(ax2, xlabel='误差半角 ε (°)', ylabel='定位区域直径 D (m)',
              title='(b) D 随误差半角 ε 的变化（D ∝ ε）')
    ax2.legend(fontsize=9, loc='upper left')
    ax2.grid(True, alpha=0.25)
    ax2.text(0.05, 0.95, 'b', transform=ax2.transAxes, fontsize=13, weight='bold', va='top')

    fig.suptitle('图5.1-6 参数扫描：D 与交会角 φ、误差半角 ε 的关系',
                 fontsize=13, weight='bold', y=1.02)
    plt.tight_layout()
    save_fig(fig, 'fig5_1_6_param_scan')


# ============================================================================
# 图5.1-7: γ缺口比分布 — 蒙特卡洛真实数据（Raincloud plot）
# ============================================================================

def fig_5_1_7_gamma_distribution():
    """γ = R_MEC / (D/2) 的分布，来自真实蒙特卡洛扫描
    展示：Jung理论界[1.0, 1.1547]、实测集中在1.0附近、γ≤1.01"""
    from scipy.stats import gaussian_kde

    data = load_scan_data()
    gamma_mc = data['gamma_mc']

    # 合并所有n的γ值
    all_gamma = []
    for n_key in gamma_mc:
        vals = gamma_mc[n_key]
        if isinstance(vals, dict) and 'gammas' in vals:
            all_gamma.extend(vals['gammas'])
        elif isinstance(vals, list):
            all_gamma.extend(vals)

    all_gamma = np.array(all_gamma)
    all_gamma = all_gamma[np.isfinite(all_gamma)]
    all_gamma = all_gamma[(all_gamma >= 0.99) & (all_gamma <= 1.2)]

    JUNG_LOWER = 1.0
    JUNG_UPPER = 2.0 / np.sqrt(3)  # ≈1.1547

    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=PALETTE['paper'])

    # Jung理论窄带背景
    ax.axvspan(JUNG_LOWER, JUNG_UPPER, alpha=0.1, facecolor=PALETTE['field'], zorder=0)

    # 边界虚线
    ax.axvline(JUNG_LOWER, linestyle='--', linewidth=LW['theory'],
              color=PALETTE['sage'], alpha=0.7, label=f'Jung下界 γ={JUNG_LOWER:.0f}')
    ax.axvline(JUNG_UPPER, linestyle='--', linewidth=LW['theory'],
              color=PALETTE['rust'], alpha=0.7, label=f'Jung上界 γ={JUNG_UPPER:.4f} (2/√3)')

    # γ≤1.01标注线
    ax.axvline(1.01, linestyle=':', linewidth=LW['main'], color=PALETTE['ochre'],
              alpha=0.8, label='本题实测上界 γ≤1.01')

    # KDE（有界反射）
    mirror_lower = 2 * JUNG_LOWER - all_gamma[all_gamma < JUNG_LOWER + 0.02]
    mirror_upper = 2 * JUNG_UPPER - all_gamma[all_gamma > JUNG_UPPER - 0.02]
    reflected = np.concatenate([mirror_lower, all_gamma, mirror_upper])
    kde = gaussian_kde(reflected, bw_method='scott')
    x_range = np.linspace(JUNG_LOWER - 0.005, JUNG_UPPER + 0.005, 500)
    density = kde(x_range)
    mask = (x_range >= JUNG_LOWER) & (x_range <= JUNG_UPPER)
    ax.fill_between(x_range[mask], 0, density[mask], alpha=0.4,
                   facecolor=PALETTE['ochre'], edgecolor=PALETTE['ochre'],
                   linewidth=LW['main'], label=f'核密度估计（n={len(all_gamma)}）')

    # 抖动散点
    np.random.seed(42)
    sample_idx = np.random.choice(len(all_gamma), size=min(500, len(all_gamma)), replace=False)
    jitter_y = -0.3 + np.random.normal(0, 0.08, size=len(sample_idx))
    ax.scatter(all_gamma[sample_idx], jitter_y, s=15, alpha=0.5,
              c=PALETTE['ink'], edgecolors='white', linewidths=0.4, zorder=5,
              label='抽样散点')

    # 统计信息
    stats_text = (f'n = {len(all_gamma)}\n'
                  f'mean = {np.mean(all_gamma):.6f}\n'
                  f'median = {np.median(all_gamma):.6f}\n'
                  f'max = {np.max(all_gamma):.6f}\n'
                  f'std = {np.std(all_gamma):.2e}')
    ax.text(0.02, 0.97, stats_text, transform=ax.transAxes, fontsize=9, va='top',
           bbox=dict(boxstyle='round,pad=0.5', facecolor=PALETTE['paper'],
                    edgecolor=PALETTE['slate'], alpha=0.95))

    # 核心结论
    ax.text(0.98, 0.97,
           '关键发现：\n'
           '• 全部实测 γ ≤ 1.01\n'
           '• 远低于Jung上界 1.1547\n'
           '• 等边三角形在本题区域族内不可达\n'
           '• 定位区域是"2ε-近平行四边形"，γ≈1',
           transform=ax.transAxes, fontsize=9, va='top', ha='right',
           bbox=dict(boxstyle='round,pad=0.5', facecolor=PALETTE['sage'], alpha=0.12,
                    edgecolor=PALETTE['sage'], linewidth=1))

    style_ax(ax, xlabel=r'$\gamma = R_{MEC} / (D/2)$（缺口比）',
              ylabel='概率密度 / 散点', title='图5.1-7 γ缺口比分布（蒙特卡洛真实数据）')
    ax.set_xlim(0.9995, 1.015)
    ax.set_ylim(-0.8, max(density[mask]) * 1.25)
    ax.legend(loc='center right', fontsize=8, framealpha=0.95)
    ax.grid(True, alpha=0.2, axis='y')

    plt.tight_layout()
    save_fig(fig, 'fig5_1_7_gamma_distribution')


# ============================================================================
# 图5.1-8: 检测点数n扫描 + 网格扫描热力图
# ============================================================================

def fig_5_1_8_n_and_grid():
    """左：D和γ随检测点数n的变化（n=2~6）
    右：(φ, ε)参数空间D值热力图（54组真实扫描数据）"""
    data = load_scan_data()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), facecolor=PALETTE['paper'])

    # --- 左：n扫描 ---
    scan_n = data['scan_n']
    n_vals = [r['n'] for r in scan_n]
    D_n = [r['D'] for r in scan_n]
    gamma_n = [r['gamma'] for r in scan_n]

    color1 = PALETTE['geometry']
    ax1.plot(n_vals, D_n, 'o-', color=color1, linewidth=LW['main'], markersize=9,
            label='直径 D (m)')
    ax1.set_xlabel('检测点数 n', fontsize=11)
    ax1.set_ylabel('定位区域直径 D (m)', fontsize=11, color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)

    ax1b = ax1.twinx()
    color2 = PALETTE['ochre']
    ax1b.plot(n_vals, gamma_n, 's--', color=color2, linewidth=LW['theory'], markersize=8,
             label='缺口比 γ')
    ax1b.set_ylabel('缺口比 γ', fontsize=11, color=color2)
    ax1b.tick_params(axis='y', labelcolor=color2)
    ax1b.axhline(1.01, linestyle=':', color=PALETTE['rust'], linewidth=LW['aux'], alpha=0.6)
    ax1b.text(max(n_vals)+0.1, 1.01, 'γ≤1.01', fontsize=8, color=PALETTE['rust'], va='center')

    # 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1b.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right', fontsize=9)

    style_ax(ax1, title='(a) D 和 γ 随检测点数 n 的变化')
    ax1.set_xticks(n_vals)
    ax1.grid(True, alpha=0.2)
    ax1.text(0.05, 0.95, 'a', transform=ax1.transAxes, fontsize=13, weight='bold', va='top')

    # --- 右：网格热力图 ---
    scan_grid = data['scan_grid']
    phi_grid = sorted(set(r['phi'] for r in scan_grid))
    eps_grid = sorted(set(r['eps'] for r in scan_grid))

    D_grid = np.zeros((len(eps_grid), len(phi_grid)))
    for r in scan_grid:
        i = eps_grid.index(r['eps'])
        j = phi_grid.index(r['phi'])
        D_grid[i, j] = r['D']

    im = ax2.imshow(D_grid, aspect='auto', cmap='YlOrRd',
                    extent=[min(phi_grid), max(phi_grid), min(eps_grid), max(eps_grid)],
                    origin='lower', interpolation='bilinear')
    cbar = plt.colorbar(im, ax=ax2, pad=0.02)
    cbar.set_label('直径 D (m)', fontsize=10)

    # 等高线
    cs = ax2.contour(phi_grid, eps_grid, D_grid, colors=PALETTE['ink'],
                     linewidths=0.8, alpha=0.6)
    ax2.clabel(cs, inline=True, fontsize=8, fmt='%.1f')

    # 标注基准点
    ax2.plot(61.92, 1.0, '*', color=PALETTE['gold'], markersize=18,
            markeredgecolor=PALETTE['ink'], markeredgewidth=1, zorder=5)
    ax2.annotate('基准算例\n(φ=61.9°, ε=1°)\nD=39.60m', xy=(61.92, 1.0),
                xytext=(70, 1.5), fontsize=9, color=PALETTE['ink'],
                arrowprops=dict(arrowstyle='->', color=PALETTE['ink'], lw=1),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9))

    style_ax(ax2, xlabel='交会角 φ (°)', ylabel='误差半角 ε (°)',
              title='(b) (φ, ε) 参数空间 D 值热力图')
    ax2.text(0.05, 0.95, 'b', transform=ax2.transAxes, fontsize=13, weight='bold', va='top')

    fig.suptitle('图5.1-8 检测点数扫描与参数空间热力图（真实扫描数据）',
                 fontsize=13, weight='bold', y=1.02)
    plt.tight_layout()
    save_fig(fig, 'fig5_1_8_n_and_grid')


# ============================================================================
# 图5.1-10: 交会定位区域构造（双面板：全局几何 + 区域放大）
# ============================================================================

def fig_5_1_10_geometry_construction():
    """左：两站交会全局几何（真实比例，角域+定位区域位置）
    右：定位区域L放大（4顶点坐标+直径+MEC+γ标注）"""
    from matplotlib.patches import ConnectionPatch

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.5),
                                     gridspec_kw={'width_ratios': [1.2, 1]},
                                     facecolor=PALETTE['paper'])

    S1 = np.array([0.0, 0.0])
    S2 = np.array([600.0, 0.0])
    G = np.array([300.0, 500.0])
    eps = 1.0

    theta1 = np.rad2deg(np.arctan2(G[1]-S1[1], G[0]-S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1]-S2[1], G[0]-S2[0]))

    wedges = build_wedges([S1, S2], [theta1, theta2], eps)
    vertices = candidate_vertices(wedges)
    poly = convex_hull(vertices)

    # ========== 左面板：全局几何 ==========
    ax = ax1

    # 角域填充
    for station, theta in [(S1, theta1), (S2, theta2)]:
        wedge_patch = Wedge(station, 700, theta-eps, theta+eps,
                            facecolor=PALETTE['field'], alpha=0.15, edgecolor='none',
                            clip_on=True)
        ax.add_patch(wedge_patch)

    # 角域边界射线（虚线）
    for station, theta in [(S1, theta1), (S2, theta2)]:
        for angle in [theta-eps, theta+eps]:
            direction = unit_vector(angle)
            end = station + 700 * direction
            ax.plot([station[0], end[0]], [station[1], end[1]],
                   color=PALETTE['geometry'], linewidth=LW['aux'],
                   linestyle='--', alpha=0.5, clip_on=True)

    # 中心示向度射线（实线）
    for station, theta, label in [(S1, theta1, 'θ₁'), (S2, theta2, 'θ₂')]:
        direction = unit_vector(theta)
        end = station + 650 * direction
        ax.plot([station[0], end[0]], [station[1], end[1]],
               color=PALETTE['geometry'], linewidth=LW['theory'], alpha=0.7,
               clip_on=True)
        # θ标注移到射线末端外侧，避免与源点G重叠
        label_pos = station + 680 * direction
        ax.text(label_pos[0], label_pos[1], label, fontsize=12, color=PALETTE['geometry'],
               weight='bold', ha='center', va='center')

    # 定位区域（全局中很小，用红色框标注）
    if poly:
        hull_pts = np.array(poly.vertices + [poly.vertices[0]])
        ax.fill(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['ochre'], alpha=0.7)
        ax.plot(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['rust'], linewidth=LW['main'])

        # 定位区域标注框
        x_min, x_max = min(v[0] for v in poly.vertices), max(v[0] for v in poly.vertices)
        y_min, y_max = min(v[1] for v in poly.vertices), max(v[1] for v in poly.vertices)
        rect = plt.Rectangle((x_min-8, y_min-8), x_max-x_min+16, y_max-y_min+16,
                             fill=False, edgecolor=PALETTE['rust'], linewidth=1.5,
                             linestyle='--')
        ax.add_patch(rect)
        ax.annotate('定位区域 L\n(40 m 量级)\n放大见 (b)',
                   xy=((x_min+x_max)/2, (y_min+y_max)/2),
                   xytext=(420, 380), fontsize=10, color=PALETTE['rust'],
                   arrowprops=dict(arrowstyle='->', color=PALETTE['rust'], lw=1.5),
                   bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['paper'],
                            edgecolor=PALETTE['rust'], linewidth=1))

    # 检测点
    ax.plot(S1[0], S1[1], 's', color=PALETTE['geometry'], markersize=12, zorder=5)
    ax.plot(S2[0], S2[1], 's', color=PALETTE['geometry'], markersize=12, zorder=5)
    ax.text(S1[0], S1[1]-40, 'S₁ (0, 0)', fontsize=11, ha='center',
           weight='bold', color=PALETTE['geometry'])
    ax.text(S2[0], S2[1]-40, 'S₂ (600, 0)', fontsize=11, ha='center',
           weight='bold', color=PALETTE['geometry'])

    # 真实源
    ax.plot(G[0], G[1], '*', color=PALETTE['gold'], markersize=18, zorder=6,
           markeredgecolor=PALETTE['ink'], markeredgewidth=0.8)
    ax.text(G[0]+20, G[1]+15, '真实源 G\n(300, 500)', fontsize=10,
           color=PALETTE['ink'], weight='bold',
           bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['paper'], alpha=0.9))

    # 基线标注
    ax.annotate('', xy=(0, -60), xytext=(600, -60),
               arrowprops=dict(arrowstyle='<->', color=PALETTE['slate'], lw=1.2))
    ax.text(300, -75, '基线 S₁S₂ = 600 m', fontsize=10, ha='center',
           color=PALETTE['slate'], weight='bold')

    # 角域标注
    ax.text(150, 250, '角域 W₁\n(2ε = 2°)', fontsize=10, color=PALETTE['geometry'],
           style='italic',
           bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['paper'], alpha=0.8))
    ax.text(450, 250, '角域 W₂\n(2ε = 2°)', fontsize=10, color=PALETTE['geometry'],
           style='italic',
           bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['paper'], alpha=0.8))

    style_ax(ax, xlabel='X 坐标 (m)', ylabel='Y 坐标 (m)',
              title='(a) 两站交会全局几何（真实比例）')
    ax.set_xlim(-80, 680)
    ax.set_ylim(-100, 620)
    ax.set_aspect('equal')
    ax.text(0.03, 0.97, 'a', transform=ax.transAxes, fontsize=16, weight='bold', va='top')

    # ========== 右面板：定位区域放大 ==========
    ax = ax2

    if poly:
        hull_pts = np.array(poly.vertices + [poly.vertices[0]])
        ax.fill(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['field'], alpha=0.5,
               label='定位区域 L')
        ax.plot(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['geometry'],
               linewidth=LW['main'])

        # 4顶点标注 — 根据顶点相对中心(300,500)的位置智能选择偏移方向
        cx, cy = 300.0, 500.0
        for i, v in enumerate(poly.vertices):
            ax.plot(v[0], v[1], 'o', color=PALETTE['ochre'], markersize=9, zorder=5)
            dx, dy = v[0] - cx, v[1] - cy
            # 根据顶点方位选择标注偏移：上→上方，下→下方，左→左侧，右→右侧
            if abs(dx) < 5 and dy > 0:      # 顶部顶点
                offset = (0, 18)
                ha = 'center'
            elif abs(dx) < 5 and dy < 0:    # 底部顶点
                offset = (0, -28)
                ha = 'center'
            elif dx < 0:                      # 左侧顶点
                offset = (-65, 0)
                ha = 'right'
            else:                              # 右侧顶点
                offset = (20, 0)
                ha = 'left'
            ax.annotate(f'V{i+1}\n({v[0]:.1f}, {v[1]:.1f})', xy=v,
                       xytext=(v[0]+offset[0], v[1]+offset[1]), fontsize=8.5,
                       color=PALETTE['ink'], weight='bold', ha=ha,
                       bbox=dict(boxstyle='round,pad=0.25', facecolor=PALETTE['paper'],
                                edgecolor=PALETTE['ochre'], linewidth=0.8, alpha=0.95))

        # 直径
        D, (p, q) = diameter_bruteforce(poly)
        ax.plot([p[0], q[0]], [p[1], q[1]], color=PALETTE['ochre'],
               linewidth=LW['main']+0.6, solid_capstyle='round',
               label=f'直径 D = {D:.3f} m')
        ax.plot([p[0], q[0]], [p[1], q[1]], 'o', color=PALETTE['ochre'],
               markersize=7, zorder=6)

        # MEC
        center, R = mec_bruteforce(poly.vertices)
        circle = Circle(center, R, fill=False, edgecolor=PALETTE['sage'],
                       linewidth=LW['theory'], linestyle='--',
                       label=f'最小包围圆 R_MEC = {R:.3f} m')
        ax.add_patch(circle)
        ax.plot(center[0], center[1], '+', color=PALETTE['sage'],
               markersize=14, markeredgewidth=2, zorder=6)

        # γ标注
        gamma = R / (D / 2)
        ax.text(0.03, 0.97,
                f'γ = R_MEC / (D/2) = {gamma:.4f}\n'
                f'（Jung下界取等）',
                transform=ax.transAxes, fontsize=9.5, va='top',
                bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['sage'],
                         alpha=0.15, edgecolor=PALETTE['sage'], linewidth=1.2))

        # 真实源
        ax.plot(G[0], G[1], '*', color=PALETTE['gold'], markersize=16, zorder=7,
               markeredgecolor=PALETTE['ink'], markeredgewidth=0.8)
        ax.text(G[0]+8, G[1]+8, 'G', fontsize=12, weight='bold', color=PALETTE['ink'])

    style_ax(ax, xlabel='X 坐标 (m)', ylabel='Y 坐标 (m)',
              title=f'(b) 定位区域 L 放大：D = {D:.2f} m, R_MEC = {R:.2f} m')
    ax.set_xlim(275, 325)
    ax.set_ylim(470, 530)
    ax.set_aspect('equal')
    ax.legend(loc='lower left', fontsize=8.5, framealpha=0.95)
    ax.text(0.03, 0.97, 'b', transform=ax.transAxes, fontsize=16, weight='bold', va='top')

    # 连接两个面板的放大指示线
    con = ConnectionPatch(xyA=((x_min+x_max)/2, (y_min+y_max)/2), coordsA=ax1.transData,
                          xyB=(300, 500), coordsB=ax2.transData,
                          color=PALETTE['rust'], linewidth=1.2, linestyle=':', alpha=0.6)
    fig.add_artist(con)

    fig.suptitle('图5.1-10 交会定位区域构造：从全局几何到精确定位区域',
                 fontsize=14, weight='bold', y=1.02)
    plt.tight_layout()
    save_fig(fig, 'fig5_1_10_geometry_construction')


# ============================================================================
# 图5.1-11: 灵敏度三联图（ε / n / 距离）
# ============================================================================

def fig_5_1_11_sensitivity_triplet():
    """三个子图展示D对三个关键参数的灵敏度：
    (a) ε灵敏度：D ∝ ε（小误差近似，线性增长）
    (b) n灵敏度：加站D单调不增，收益递减
    (c) 距离灵敏度：φ=90°时D最小（源在基线中垂线上）"""
    data = load_scan_data()

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5),
                                          facecolor=PALETTE['paper'])

    # ========== (a) ε灵敏度 ==========
    ax = ax1
    scan_eps = data['scan_eps']
    eps_vals = [r['eps'] for r in scan_eps]
    D_eps = [r['D'] for r in scan_eps]

    ax.plot(eps_vals, D_eps, 'o-', color=PALETTE['geometry'], linewidth=LW['main'],
            markersize=8, label='实测 D(ε)', zorder=3)

    # 线性拟合
    coeffs = np.polyfit(eps_vals, D_eps, 1)
    eps_fit = np.linspace(0, max(eps_vals)*1.1, 50)
    D_fit = np.polyval(coeffs, eps_fit)
    ax.plot(eps_fit, D_fit, '--', color=PALETTE['ochre'], linewidth=LW['theory'],
            label=f'线性拟合 D={coeffs[0]:.1f}·ε{coeffs[1]:+.1f}')

    # 标注ε=1°
    idx_1 = min(range(len(eps_vals)), key=lambda i: abs(eps_vals[i]-1.0))
    ax.annotate(f'题设 ε=1°\nD={D_eps[idx_1]:.2f}m',
                xy=(eps_vals[idx_1], D_eps[idx_1]),
                xytext=(eps_vals[idx_1]+0.8, D_eps[idx_1]+20),
                fontsize=9, color=PALETTE['rust'],
                arrowprops=dict(arrowstyle='->', color=PALETTE['rust'], lw=1.2),
                bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['paper'], alpha=0.95))

    # 小误差近似标注
    ax.text(0.05, 0.92,
            '小误差近似：\nD ≈ 39.6·ε m\n(ε=1°时D=39.6m)',
            transform=ax.transAxes, fontsize=9, va='top',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['sage'],
                     alpha=0.12, edgecolor=PALETTE['sage'], linewidth=1))

    style_ax(ax, xlabel='测向误差 ε (°)', ylabel='定位区域直径 D (m)',
              title='(a) ε 灵敏度：D ∝ ε')
    ax.legend(fontsize=8.5, loc='upper left')
    ax.grid(True, alpha=0.25)
    ax.set_xlim(0, max(eps_vals)*1.15)
    ax.set_ylim(0, max(D_eps)*1.15)
    ax.text(0.03, 0.97, 'a', transform=ax.transAxes, fontsize=15, weight='bold', va='top')

    # ========== (b) n灵敏度 ==========
    ax = ax2
    scan_n = data['scan_n']
    n_vals = [r['n'] for r in scan_n]
    D_n = [r['D'] for r in scan_n]

    bars = ax.bar(n_vals, D_n, width=0.6, color=PALETTE['geometry'], alpha=0.8,
                  edgecolor=PALETTE['ink'], linewidth=0.8, label='实测 D(n)')

    # 数值标注
    for bar, d in zip(bars, D_n):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{d:.1f}', ha='center', va='bottom', fontsize=9, weight='bold',
                color=PALETTE['ink'])

    # 收益递减标注
    if len(D_n) >= 2:
        reduction = D_n[0] - D_n[-1]
        ax.text(0.05, 0.92,
                f'加站收益递减：\n2站→{n_vals[-1]}站\nD减少{reduction:.1f}m\n({reduction/D_n[0]*100:.1f}%)',
                transform=ax.transAxes, fontsize=9, va='top',
                bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['ochre'],
                         alpha=0.15, edgecolor=PALETTE['ochre'], linewidth=1))

    style_ax(ax, xlabel='检测站数量 n', ylabel='定位区域直径 D (m)',
              title='(b) n 灵敏度：加站收益递减')
    ax.set_xticks(n_vals)
    ax.set_ylim(0, max(D_n)*1.2)
    ax.grid(True, alpha=0.25, axis='y')
    ax.text(0.03, 0.97, 'b', transform=ax.transAxes, fontsize=15, weight='bold', va='top')

    # ========== (c) 距离灵敏度 ==========
    ax = ax3
    scan_phi = data['scan_phi']
    L = 600.0  # 基线长度

    # 从φ计算源到基线中点的距离d
    # φ = 2*arctan((L/2)/d) => d = (L/2)/tan(φ/2)
    distances = []
    D_dist = []
    for r in scan_phi:
        phi = r['phi']
        if phi > 0 and phi < 180:
            d = (L/2) / np.tan(np.radians(phi/2))
            distances.append(d)
            D_dist.append(r['D'])

    # 按距离排序
    sorted_pairs = sorted(zip(distances, D_dist))
    distances = [p[0] for p in sorted_pairs]
    D_dist = [p[1] for p in sorted_pairs]

    ax.plot(distances, D_dist, 's-', color=PALETTE['geometry'], linewidth=LW['main'],
            markersize=7, label='实测 D(d)', zorder=3)

    # 理论曲线：D = 2ε_rad * L / sinφ = 2ε_rad * L * (d²+(L/2)²) / (d*L)
    # 简化：D ∝ (d² + (L/2)²) / d
    eps_rad = np.radians(1.0)
    d_theory = np.linspace(min(distances)*0.8, max(distances)*1.1, 200)
    D_theory = 2 * eps_rad * L * (d_theory**2 + (L/2)**2) / (d_theory * L)
    ax.plot(d_theory, D_theory, '--', color=PALETTE['ochre'], linewidth=LW['theory'],
            label='理论式')

    # 标注φ=90°（d=L/2=300m）
    d_optimal = L/2
    D_optimal_idx = min(range(len(distances)), key=lambda i: abs(distances[i]-d_optimal))
    ax.annotate(f'φ=90° (d=300m)\nD最小={D_dist[D_optimal_idx]:.2f}m',
                xy=(distances[D_optimal_idx], D_dist[D_optimal_idx]),
                xytext=(distances[D_optimal_idx]+200, D_dist[D_optimal_idx]+30),
                fontsize=9, color=PALETTE['rust'],
                arrowprops=dict(arrowstyle='->', color=PALETTE['rust'], lw=1.2),
                bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['paper'], alpha=0.95))

    # 最优距离标注
    ax.axvline(d_optimal, color=PALETTE['sage'], linewidth=LW['aux'], linestyle=':', alpha=0.6)
    ax.text(d_optimal+10, ax.get_ylim()[1]*0.9 if ax.get_ylim()[1] > 0 else 100,
            '最优距离\nd=L/2=300m', fontsize=8, color=PALETTE['sage'], va='top')

    style_ax(ax, xlabel='源到基线中点距离 d (m)', ylabel='定位区域直径 D (m)',
              title='(c) 距离灵敏度：φ=90° 时 D 最小')
    ax.legend(fontsize=8.5, loc='upper right')
    ax.grid(True, alpha=0.25)
    ax.text(0.03, 0.97, 'c', transform=ax.transAxes, fontsize=15, weight='bold', va='top')

    fig.suptitle('图5.1-11 灵敏度三联图：D 对 ε、n、距离的敏感性分析',
                 fontsize=14, weight='bold', y=1.02)
    plt.tight_layout()
    save_fig(fig, 'fig5_1_11_sensitivity_triplet')


# ============================================================================
# 图5.1-12: 参数空间四类分区（θ₁, θ₂平面）
# ============================================================================

def fig_5_1_12_param_space_partition():
    """(θ₁, θ₂)平面四类分区：
    1. 空（数据矛盾）：角域不相交
    2. 无界（近平行）：|θ₁-θ₂| ≤ 2ε
    3. 三角形（退化）：定位区域3顶点
    4. 四边形（正常）：定位区域4顶点
    右侧展示四类的几何形态示例"""
    from matplotlib.colors import ListedColormap

    S1 = np.array([0.0, 0.0])
    S2 = np.array([600.0, 0.0])
    eps = 1.0
    L = 600.0

    # 计算(θ₁, θ₂)网格的分类
    theta_range = np.linspace(0, 360, 181)  # 2°步长
    classification = np.zeros((len(theta_range), len(theta_range)), dtype=int)
    # 0=空, 1=无界, 2=三角形, 3=四边形

    print("  计算参数空间分类（181×181网格）...")
    for i, t1 in enumerate(theta_range):
        for j, t2 in enumerate(theta_range):
            # 无界判断：|θ₁-θ₂| ≤ 2ε（考虑角度差的最小值）
            diff = abs((t1 - t2 + 180) % 360 - 180)
            if diff <= 2 * eps:
                classification[i, j] = 1
                continue

            # 尝试构建角域和定位区域
            try:
                wedges = build_wedges([S1, S2], [t1, t2], eps)
                vertices = candidate_vertices(wedges)
                if len(vertices) == 0:
                    classification[i, j] = 0  # 空
                else:
                    poly = convex_hull(vertices)
                    nv = len(poly.vertices) if poly else 0
                    if nv <= 2:
                        classification[i, j] = 0  # 空/退化
                    elif nv == 3:
                        classification[i, j] = 2  # 三角形
                    else:
                        classification[i, j] = 3  # 四边形
            except Exception:
                classification[i, j] = 0

    # 绘图
    fig = plt.figure(figsize=(15, 6), facecolor=PALETTE['paper'])
    gs = gridspec.GridSpec(1, 2, width_ratios=[1.2, 1], wspace=0.3)

    # ========== 左：分类热力图 ==========
    ax = plt.subplot(gs[0, 0])

    colors = [PALETTE['slate'], PALETTE['field'], PALETTE['ochre'], PALETTE['sage']]
    cmap = ListedColormap(colors)
    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5]
    norm = plt.matplotlib.colors.BoundaryNorm(bounds, cmap.N)

    im = ax.imshow(classification, extent=[0, 360, 0, 360], origin='lower',
                   cmap=cmap, norm=norm, aspect='auto', interpolation='nearest')

    # 标注基准算例
    theta1_base = np.rad2deg(np.arctan2(500, 300))
    theta2_base = np.rad2deg(np.arctan2(500, -300))
    ax.plot(theta1_base, theta2_base, '*', color=PALETTE['gold'], markersize=18,
            markeredgecolor=PALETTE['ink'], markeredgewidth=1.2, zorder=5)
    ax.annotate(f'基准算例\n(θ₁={theta1_base:.1f}°, θ₂={theta2_base:.1f}°)\n→ 四边形',
                xy=(theta1_base, theta2_base),
                xytext=(theta1_base+60, theta2_base-40),
                fontsize=9, color=PALETTE['ink'],
                arrowprops=dict(arrowstyle='->', color=PALETTE['ink'], lw=1.2),
                bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['paper'], alpha=0.95))

    # 无界分界线
    ax.plot([0, 360], [2*eps, 360+2*eps], 'k--', linewidth=0.8, alpha=0.5)
    ax.plot([0, 360], [-2*eps, 360-2*eps], 'k--', linewidth=0.8, alpha=0.5)

    style_ax(ax, xlabel='检测站 S₁ 的示向度 θ₁ (°)',
              ylabel='检测站 S₂ 的示向度 θ₂ (°)',
              title='(a) (θ₁, θ₂) 平面四类分区（基线 600 m, ε=1°）')
    ax.set_xticks([0, 60, 120, 180, 240, 300, 360])
    ax.set_yticks([0, 60, 120, 180, 240, 300, 360])

    # 图例
    legend_elements = [
        mpatches.Patch(facecolor=colors[0], edgecolor='gray', label='空（数据矛盾）'),
        mpatches.Patch(facecolor=colors[1], edgecolor='gray', label='无界（近平行）'),
        mpatches.Patch(facecolor=colors[2], edgecolor='gray', label='三角形（退化）'),
        mpatches.Patch(facecolor=colors[3], edgecolor='gray', label='四边形（正常）'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9, framealpha=0.95)

    # ========== 右：四类几何形态示例 ==========
    ax2 = plt.subplot(gs[0, 1])
    ax2.set_facecolor(PALETTE['paper'])
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    ax2.axis('off')
    ax2.set_title('(b) 四类几何形态示例', fontsize=12, weight='bold', pad=10)

    # 四个示例的位置和参数
    examples = [
        (2.5, 7.5, '空（数据矛盾）', [0, 0], [100, 100], colors[0]),
        (7.5, 7.5, '无界（近平行）', [45, 45], [45, 45], colors[1]),
        (2.5, 2.5, '三角形（退化）', [60, 120], [60, 120], colors[2]),
        (7.5, 2.5, '四边形（正常）', [59, 121], [59, 121], colors[3]),
    ]

    for cx, cy, label, t1_list, t2_list, color in examples:
        # 绘制简化的角域交会示意
        s1 = (cx-1.2, cy-0.8)
        s2 = (cx+1.2, cy-0.8)

        # 检测点
        ax2.plot(s1[0], s1[1], 's', color=PALETTE['geometry'], markersize=6)
        ax2.plot(s2[0], s2[1], 's', color=PALETTE['geometry'], markersize=6)

        # 简化的角域射线
        for t in t1_list:
            rad = np.radians(t)
            end = (s1[0] + 1.5*np.cos(rad), s1[1] + 1.5*np.sin(rad))
            ax2.plot([s1[0], end[0]], [s1[1], end[1]], color=PALETTE['geometry'],
                    linewidth=0.8, alpha=0.6)
        for t in t2_list:
            rad = np.radians(180-t)
            end = (s2[0] + 1.5*np.cos(rad), s2[1] + 1.5*np.sin(rad))
            ax2.plot([s2[0], end[0]], [s2[1], end[1]], color=PALETTE['geometry'],
                    linewidth=0.8, alpha=0.6)

        # 标签
        ax2.text(cx, cy+1.3, label, fontsize=9, ha='center', weight='bold',
                bbox=dict(boxstyle='round,pad=0.25', facecolor=color, alpha=0.3,
                         edgecolor=color, linewidth=1))

    fig.suptitle('图5.1-12 参数空间四类分区：(θ₁, θ₂) 平面的定位区域形态分类',
                 fontsize=14, weight='bold', y=1.02)
    plt.tight_layout()
    save_fig(fig, 'fig5_1_12_param_space_partition')


# ============================================================================
# 图5.1-13: φ-D 曲线与理论式验证
# ============================================================================

def fig_5_1_13_phi_D_theory():
    """左：直径D、横向跨距T与理论式（基线L=600m, ε=1°）
    右：与理论式的相对偏差（验证理论式精度）"""
    data = load_scan_data()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5),
                                     gridspec_kw={'width_ratios': [1.3, 1]},
                                     facecolor=PALETTE['paper'])

    scan_phi = data['scan_phi']
    phi_vals = np.array([r['phi'] for r in scan_phi])
    D_vals = np.array([r['D'] for r in scan_phi])
    h_vals = np.array([r['h'] for r in scan_phi])  # 横向跨距

    L = 600.0
    eps = 1.0
    eps_rad = np.radians(eps)
    sin2eps = np.sin(2 * eps_rad)

    # 理论式：D = L * sin2ε / sinφ（φ≥90°时精确，φ<90°时T精确）
    phi_theory = np.linspace(min(phi_vals), max(phi_vals), 200)
    D_theory = L * sin2eps / np.sin(np.radians(phi_theory))

    # ========== 左：D、T与理论式 ==========
    ax = ax1

    ax.plot(phi_vals, D_vals, 'o-', color=PALETTE['geometry'], linewidth=LW['main'],
            markersize=7, label='直径 D（实测）', zorder=4)
    ax.plot(phi_vals, h_vals, 's-', color=PALETTE['ochre'], linewidth=LW['theory'],
            markersize=6, label='横向跨距 T（实测）', zorder=3)
    ax.plot(phi_theory, D_theory, '--', color=PALETTE['sage'], linewidth=LW['theory'],
            label=r'理论式：$D = L \cdot \sin 2\varepsilon / \sin\varphi$', zorder=2)

    # φ=90°标注
    idx_90 = min(range(len(phi_vals)), key=lambda i: abs(phi_vals[i]-90))
    ax.axvline(90, color=PALETTE['slate'], linewidth=LW['aux'], linestyle=':', alpha=0.6)
    ax.annotate(f'φ=90°\nD最小={D_vals[idx_90]:.2f}m',
                xy=(90, D_vals[idx_90]),
                xytext=(105, D_vals[idx_90]+80),
                fontsize=9, color=PALETTE['rust'],
                arrowprops=dict(arrowstyle='->', color=PALETTE['rust'], lw=1.2),
                bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['paper'], alpha=0.95))

    # 理论式说明
    ax.text(0.03, 0.97,
            '理论式分段：\n'
            r'$\varphi < 90°: T = L\sin2\varepsilon/\sin\varphi$（精确）' + '\n'
            r'$\varphi > 90°: D = L\sin2\varepsilon/\sin\varphi$（精确）' + '\n'
            r'$\varphi = 90°: D$ 取最小值',
            transform=ax.transAxes, fontsize=8.5, va='top',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['sage'],
                     alpha=0.12, edgecolor=PALETTE['sage'], linewidth=1))

    style_ax(ax, xlabel='交会角 φ (°)', ylabel='定位区域尺度 (m)',
              title='(a) 直径 D、横向跨距 T 与理论式（基线 L=600 m, ε=1°）')
    ax.legend(fontsize=8.5, loc='upper right')
    ax.grid(True, alpha=0.25)
    ax.set_ylim(0, max(D_vals)*1.15)
    ax.text(0.03, 0.97, 'a', transform=ax.transAxes, fontsize=15, weight='bold', va='top')

    # ========== 右：相对偏差 ==========
    ax = ax2

    # 计算D的相对偏差（与理论式）
    D_theory_at_phi = L * sin2eps / np.sin(np.radians(phi_vals))
    rel_error_D = np.abs(D_vals - D_theory_at_phi) / D_theory_at_phi * 100

    # 计算T的相对偏差（与理论式，φ<90°时）
    mask_less90 = phi_vals < 90
    rel_error_T = np.full_like(phi_vals, np.nan)
    rel_error_T[mask_less90] = np.abs(h_vals[mask_less90] - D_theory_at_phi[mask_less90]) / D_theory_at_phi[mask_less90] * 100

    ax.semilogy(phi_vals, rel_error_D, 'o-', color=PALETTE['geometry'],
                linewidth=LW['main'], markersize=6, label='D 相对偏差')
    ax.semilogy(phi_vals[mask_less90], rel_error_T[mask_less90], 's-',
                color=PALETTE['ochre'], linewidth=LW['theory'], markersize=5,
                label='T 相对偏差（φ<90°）')

    # 10^-10精度线
    ax.axhline(1e-10, color=PALETTE['sage'], linewidth=LW['aux'], linestyle=':', alpha=0.6)
    ax.text(max(phi_vals)*0.95, 1.5e-10, '机器精度 ~10⁻¹⁰', fontsize=8,
           color=PALETTE['sage'], ha='right')

    # 标注
    ax.text(0.03, 0.97,
            '两条曲线在各自区间\n降至机器精度（~10⁻¹⁰）\n'
            '说明理论式为闭式非近似',
            transform=ax.transAxes, fontsize=9, va='top',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['sage'],
                     alpha=0.12, edgecolor=PALETTE['sage'], linewidth=1))

    style_ax(ax, xlabel='交会角 φ (°)', ylabel='相对偏差（对数刻度）',
              title='(b) 与理论式的相对偏差')
    ax.legend(fontsize=8.5, loc='lower left')
    ax.grid(True, alpha=0.25, which='both')
    ax.set_ylim(1e-12, 1)
    ax.text(0.03, 0.97, 'b', transform=ax.transAxes, fontsize=15, weight='bold', va='top')

    fig.suptitle('图5.1-13 φ-D 曲线与理论式验证：闭式理论式达到机器精度',
                 fontsize=14, weight='bold', y=1.02)
    plt.tight_layout()
    save_fig(fig, 'fig5_1_13_phi_D_theory')


# ============================================================================
# 主函数
# ============================================================================

def generate_all_beautified_figures():
    """生成所有美化版图表"""
    print("\n" + "=" * 70)
    print("Q1 图表统一美化版 v2.0 — 开始生成")
    print(f"输出目录: {FIG_DIR}")
    print("=" * 70)

    print("\n【1/8】图5.1-1 基准算例...")
    fig_5_1_1_baseline()

    print("\n【2/8】图5.1-2 角域构造演化...")
    fig_5_1_2_wedge_evolution()

    print("\n【3/8】图5.1-3 Jung反例...")
    fig_5_1_3_jung_counterexample()

    print("\n【4/8】图5.1-4 Jung夹逼...")
    fig_5_1_4_jung_sandwich()

    print("\n【5/8】图5.1-5 顶点过滤...")
    fig_5_1_5_vertex_filtering()

    print("\n【6/8】图5.1-6 参数扫描...")
    fig_5_1_6_param_scan()

    print("\n【7/8】图5.1-7 γ分布...")
    fig_5_1_7_gamma_distribution()

    print("\n【8/9】图5.1-8 n扫描+热力图...")
    fig_5_1_8_n_and_grid()

    print("\n【9/10】图5.1-10 交会定位区域构造...")
    fig_5_1_10_geometry_construction()

    print("\n【10/11】图5.1-11 灵敏度三联图...")
    fig_5_1_11_sensitivity_triplet()

    print("\n【11/12】图5.1-12 参数空间四类分区...")
    fig_5_1_12_param_space_partition()

    print("\n【12/12】图5.1-13 φ-D曲线与理论式验证...")
    fig_5_1_13_phi_D_theory()

    print("\n" + "=" * 70)
    print("✅ 全部 12 张美化版图表生成完成！")
    print("=" * 70)


if __name__ == "__main__":
    generate_all_beautified_figures()
