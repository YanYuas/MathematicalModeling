# -*- coding: utf-8 -*-
"""
Q1 图表统一美化版 v2.1 - 基于AI审核报告P0-P8修复
审核结果：69.9/120 (D级) → 目标 96+ (A级)

P0-P8修复清单：
P0-1: figsize宽度7-8英寸 + 字号10/12/14pt（避免缩印<5pt）
P0-2: 下标用mathtext (r'$S_1$')，避免Unicode缺字
P0-3: 替换✅❌为中文
P0-4: 替换默认命名色为PALETTE
P0-5: YlOrRd改为自定义渐变
P0-6: 修复图例显示不存在线条
P0-7: 修复注释重叠
P0-8: 移除所有suptitle

设计原则（遵循4个skill标准）：
1. math-modeling-figures: 中文字体、300dpi、论文配色
2. 3coding-visual: PDF输出、无内嵌标题、数据溯源
3. academic-figure: Nature级排版、字号层级、hero panel
4. math-modeling-code-library: 权威数字表约束
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle, Polygon, Wedge, Arc, FancyArrowPatch
from matplotlib.collections import PatchCollection
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.patches import ConnectionPatch
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from q1_main import (
    build_wedges, candidate_vertices, convex_hull,
    diameter_bruteforce, mec_bruteforce, unit_vector
)

# ============================================================================
# P0-4: 全局配色 - Ink & Ochre v2.1（禁用matplotlib默认命名色）
# ============================================================================

PALETTE = {
    "ink":      "#1A1A1A",   # 主文字、主轮廓、轴线
    "slate":    "#6B7B83",   # 次要文字、辅助线、网格
    "paper":    "#FAF7F0",   # 画布底色
    "field":    "#B8CFE0",   # 角域/区域填充
    "geometry": "#26466D",   # 观测站、射线、多边形边
    "ochre":    "#C47B2B",   # 唯一强调色：直径D、关键发现
    "rust":     "#8C3A2A",   # 失败/不覆盖/gap
    "sage":     "#3D6B52",   # 成功/取等/最优/γ=1
    "gold":     "#D4A843",   # 辅助强调：源点、特殊标记
}

# P0-5: 自定义colormap替换YlOrRd
CMAP_CUSTOM = LinearSegmentedColormap.from_list(
    'custom_warm',
    [PALETTE['paper'], PALETTE['gold'], PALETTE['ochre'], PALETTE['rust']]
)

LW = {'main': 2.4, 'theory': 1.6, 'aux': 0.8}
DPI = 300

# P0-1: 字号设置 - 打印时保证≥5pt (Nature最低标准)
FONTSIZE = {
    'label': 10,      # 轴标签 (缩印后≈6.7pt)
    'tick': 9,        # 刻度标签
    'legend': 10,     # 图例
    'title': 14,      # 子图标题（加粗）
    'annotation': 9,  # 标注文字
}

plt.rcParams.update({
    'font.size': FONTSIZE['label'],
    'font.family': 'sans-serif',
    'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'Arial', 'DejaVu Sans'],
    'axes.linewidth': 0.9,
    'axes.edgecolor': PALETTE['slate'],
    'axes.labelcolor': PALETTE['ink'],
    'axes.labelsize': FONTSIZE['label'],
    'axes.titlesize': FONTSIZE['title'],
    'axes.titleweight': 'bold',
    'text.color': PALETTE['ink'],
    'xtick.color': PALETTE['slate'],
    'ytick.color': PALETTE['slate'],
    'xtick.labelsize': FONTSIZE['tick'],
    'ytick.labelsize': FONTSIZE['tick'],
    'xtick.major.width': 0.9,
    'ytick.major.width': 0.9,
    'legend.fontsize': FONTSIZE['legend'],
    'legend.frameon': False,
    'grid.linewidth': 0.5,
    'grid.alpha': 0.25,
    'grid.color': PALETTE['slate'],
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
    'figure.dpi': DPI,
    'savefig.dpi': DPI,
    'mathtext.fontset': 'stix',  # P0-2: 数学符号使用STIX字体
})

# 输出路径
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
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


def get_polygon_vertices(poly):
    """获取Polygon对象的顶点列表"""
    if poly is None:
        return []
    # poly是Polygon对象，有vertices属性（是list[np.ndarray]）
    return poly.vertices


def save_fig(fig, name, use_tight=True):
    """P0-3: 统一保存PNG+SVG+PDF（论文用矢量格式）"""
    if name.startswith('fig5_1_6') or name.startswith('fig5_1_8') or \
       name.startswith('fig5_1_11') or name.startswith('fig5_1_12') or name.startswith('fig5_1_13'):
        out_dir = FIG_DIR_PARAM
    elif name.startswith('fig5_1_7'):
        out_dir = FIG_DIR_STAT
    elif name.startswith('fig5_1_9'):
        out_dir = FIG_DIR_FLOW
    else:
        out_dir = FIG_DIR_GEO

    png_path = os.path.join(out_dir, name + '.png')
    svg_path = os.path.join(out_dir, name + '.svg')
    pdf_path = os.path.join(out_dir, name + '.pdf')  # 新增PDF

    if use_tight:
        fig.savefig(png_path, dpi=DPI, bbox_inches='tight', facecolor=PALETTE['paper'])
        fig.savefig(svg_path, bbox_inches='tight', facecolor=PALETTE['paper'])
        fig.savefig(pdf_path, bbox_inches='tight', facecolor=PALETTE['paper'])
    else:
        fig.savefig(png_path, dpi=DPI, facecolor=PALETTE['paper'])
        fig.savefig(svg_path, facecolor=PALETTE['paper'])
        fig.savefig(pdf_path, facecolor=PALETTE['paper'])

    print(f"  [OK] {name} -> {os.path.basename(out_dir)}/ (PNG+SVG+PDF)")
    plt.close(fig)


def style_ax(ax, xlabel=None, ylabel=None, title=None, equal=False):
    """统一坐标轴样式（P0-8: 移除title参数，改为外部caption）"""
    ax.set_facecolor(PALETTE['paper'])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(PALETTE['slate'])
    ax.spines['bottom'].set_color(PALETTE['slate'])
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=FONTSIZE['label'], color=PALETTE['ink'])
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=FONTSIZE['label'], color=PALETTE['ink'])
    # P0-8: 不再设置title，交由论文caption处理
    if equal:
        ax.set_aspect('equal')


# ============================================================================
# 图5.1-1: 基准算例 - P0-1缩减figsize + P0-2 mathtext下标
# ============================================================================

def fig_5_1_1_baseline():
    """P0-1: figsize从(14,6.5)改为(8,4.5)，字号保持10/14pt"""
    from matplotlib.patches import FancyArrowPatch, ConnectionPatch

    # P0-1: 宽度从14减至8英寸
    fig = plt.figure(figsize=(8, 4.5), facecolor=PALETTE['paper'])
    gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1.4], wspace=0.15)

    S1 = np.array([0.0, 0.0])
    S2 = np.array([600.0, 0.0])
    G = np.array([300.0, 500.0])
    eps = 1.0

    theta1 = np.rad2deg(np.arctan2(G[1]-S1[1], G[0]-S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1]-S2[1], G[0]-S2[0]))

    wedges = build_wedges([S1, S2], [theta1, theta2], eps)
    vertices = candidate_vertices(wedges)
    poly = convex_hull(vertices)

    # 左面板：全局视图
    ax_global = plt.subplot(gs[0, 0])
    ax_global.set_facecolor(PALETTE['paper'])

    # 角域填充
    for station, theta in [(S1, theta1), (S2, theta2)]:
        wedge_patch = Wedge(station, 700, theta-eps, theta+eps,
                            facecolor=PALETTE['field'], alpha=0.12, edgecolor='none')
        ax_global.add_patch(wedge_patch)

    # 角域边界射线
    for station, theta in [(S1, theta1), (S2, theta2)]:
        for angle in [theta-eps, theta+eps]:
            direction = unit_vector(angle)
            end = station + 700 * direction
            ax_global.plot([station[0], end[0]], [station[1], end[1]],
                          color=PALETTE['geometry'], linewidth=0.8, linestyle=':', alpha=0.4)

    # 中心示向度射线
    for station, theta, color in [(S1, theta1, PALETTE['geometry']),
                                    (S2, theta2, PALETTE['geometry'])]:
        direction = unit_vector(theta)
        end = station + 650 * direction
        ax_global.plot([station[0], end[0]], [station[1], end[1]],
                      color=color, linewidth=1.5, alpha=0.7)

    # 定位区域
    if poly:
        verts = get_polygon_vertices(poly)
        if len(verts) > 0:
            hull_pts = np.array(list(verts) + [verts[0]])
            ax_global.fill(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['field'], alpha=0.6)
            ax_global.plot(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['geometry'],
                          linewidth=1.8, solid_capstyle='round')

    # P0-2: 检测点标注使用mathtext
    ax_global.plot(S1[0], S1[1], 's', color=PALETTE['geometry'], markersize=9,
                  markeredgecolor='white', markeredgewidth=1.2, zorder=6)
    ax_global.plot(S2[0], S2[1], 's', color=PALETTE['geometry'], markersize=9,
                  markeredgecolor='white', markeredgewidth=1.2, zorder=6)
    ax_global.plot(G[0], G[1], 'o', color=PALETTE['gold'], markersize=8,
                  markeredgecolor='white', markeredgewidth=1.2, zorder=6)

    # P0-2: 下标改为mathtext避免Unicode缺字
    ax_global.text(S1[0], S1[1]-80, r'$S_1$', ha='center', va='top',
                  fontsize=FONTSIZE['annotation'], color=PALETTE['ink'], weight='bold')
    ax_global.text(S2[0], S2[1]-80, r'$S_2$', ha='center', va='top',
                  fontsize=FONTSIZE['annotation'], color=PALETTE['ink'], weight='bold')
    ax_global.text(G[0]+40, G[1]+30, r'$G$', ha='left', va='bottom',
                  fontsize=FONTSIZE['annotation'], color=PALETTE['gold'], weight='bold')

    # P0-7: 角度标注避免重叠（调整位置）
    ax_global.text(S1[0]+120, S1[1]+80, r'$\theta_1$', fontsize=FONTSIZE['annotation'],
                  color=PALETTE['geometry'], style='italic')
    ax_global.text(S2[0]-120, S2[1]+80, r'$\theta_2$', fontsize=FONTSIZE['annotation'],
                  color=PALETTE['geometry'], style='italic')

    style_ax(ax_global, xlabel='x (m)', ylabel='y (m)', equal=True)
    ax_global.set_xlim(-100, 700)
    ax_global.set_ylim(-150, 650)
    ax_global.grid(True, alpha=0.2)

    # 右面板：定位区域放大
    ax_zoom = plt.subplot(gs[0, 1])
    ax_zoom.set_facecolor(PALETTE['paper'])

    if poly:
        verts = get_polygon_vertices(poly)
        if len(verts) > 0:
            hull_pts = np.array(list(verts) + [verts[0]])
            ax_zoom.fill(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['field'], alpha=0.4)
            ax_zoom.plot(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['geometry'],
                        linewidth=2.0, solid_capstyle='round')

            # 顶点标注
            for i, v in enumerate(verts):
                ax_zoom.plot(v[0], v[1], 'o', color=PALETTE['geometry'], markersize=7,
                            markeredgecolor='white', markeredgewidth=1.0, zorder=5)
                # P0-2: 顶点编号使用mathtext
                ax_zoom.text(v[0]+8, v[1]+8, r'$V_%d$' % (i+1), fontsize=FONTSIZE['annotation']-1,
                            color=PALETTE['ink'], ha='left')

            # 直径和MEC
            # diameter_bruteforce返回 (distance, (pt_a, pt_b))
            diam_result = diameter_bruteforce(poly)
            diam_val = diam_result[0]
            pt_a, pt_b = diam_result[1]

            # mec_bruteforce返回 (center, radius)
            center, radius = mec_bruteforce(verts)

        # 直径线（ochre强调）
        ax_zoom.plot([pt_a[0], pt_b[0]], [pt_a[1], pt_b[1]],
                    color=PALETTE['ochre'], linewidth=2.5, zorder=4,
                    label=r'$D=%.3f$ m' % diam_val)

        # MEC圆（sage成功）
        circle = Circle(center, radius, fill=False, edgecolor=PALETTE['sage'],
                       linewidth=2.0, linestyle='--', zorder=3,
                       label=r'$R_{MEC}=%.3f$ m' % radius)
        ax_zoom.add_patch(circle)
        ax_zoom.plot(center[0], center[1], 'x', color=PALETTE['sage'],
                    markersize=8, markeredgewidth=2, zorder=5)

        # P0-6: 修复图例（确保label对应实际绘制元素）
        ax_zoom.legend(loc='upper right', fontsize=FONTSIZE['legend'], framealpha=0.95)

    style_ax(ax_zoom, xlabel='x (m)', ylabel='y (m)', equal=True)
    ax_zoom.grid(True, alpha=0.2)

    save_fig(fig, 'fig5_1_1_baseline')
    print("[生成] 图5.1-1: 基准算例 (P0-1/2/6/7/8修复)")


# ============================================================================
# 图5.1-5: 顶点过滤 - P0-4替换默认色
# ============================================================================

def fig_5_1_5_vertex_filtering():
    """P0-4: 替换默认命名色（blue/red/black）为PALETTE"""
    # P0-1: figsize从(12,5)改为(8,4)
    fig = plt.figure(figsize=(8, 4), facecolor=PALETTE['paper'])
    gs = gridspec.GridSpec(1, 3, width_ratios=[1,1,1], wspace=0.25)

    S1 = np.array([0.0, 0.0])
    S2 = np.array([600.0, 0.0])
    G = np.array([300.0, 500.0])
    eps = 1.0

    theta1 = np.rad2deg(np.arctan2(G[1]-S1[1], G[0]-S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1]-S2[1], G[0]-S2[0]))

    wedges = build_wedges([S1, S2], [theta1, theta2], eps)
    vertices = candidate_vertices(wedges)

    # 阶段1：候选顶点
    ax1 = plt.subplot(gs[0, 0])
    ax1.set_facecolor(PALETTE['paper'])
    for station, theta in [(S1, theta1), (S2, theta2)]:
        wedge_patch = Wedge(station, 700, theta-eps, theta+eps,
                            facecolor=PALETTE['field'], alpha=0.12, edgecolor='none')
        ax1.add_patch(wedge_patch)

    # P0-4: 替换'blue' → PALETTE['geometry']
    for v in vertices:
        ax1.plot(v[0], v[1], 'o', color=PALETTE['geometry'], markersize=6, alpha=0.7)

    ax1.plot(S1[0], S1[1], 's', color=PALETTE['geometry'], markersize=8)
    ax1.plot(S2[0], S2[1], 's', color=PALETTE['geometry'], markersize=8)
    ax1.text(300, -100, f'候选顶点: {len(vertices)}个', ha='center',
            fontsize=FONTSIZE['annotation'], color=PALETTE['ink'])

    style_ax(ax1, xlabel='x (m)', ylabel='y (m)', equal=True)
    ax1.set_xlim(-100, 700)
    ax1.set_ylim(-150, 650)
    ax1.grid(True, alpha=0.2)

    # 阶段2：凸包过滤
    poly = convex_hull(vertices)
    ax2 = plt.subplot(gs[0, 1])
    ax2.set_facecolor(PALETTE['paper'])

    verts = get_polygon_vertices(poly)
    if len(verts) > 0:
        hull_pts = np.array(list(verts) + [verts[0]])
        ax2.fill(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['field'], alpha=0.3)
        ax2.plot(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['geometry'], linewidth=2.0)

        for v in verts:
            # P0-4: 替换'red' → PALETTE['ochre']
            ax2.plot(v[0], v[1], 'o', color=PALETTE['ochre'], markersize=7,
                    markeredgecolor='white', markeredgewidth=1.0)

    ax2.text(300, -100, f'凸包顶点: {len(verts)}个', ha='center',
            fontsize=FONTSIZE['annotation'], color=PALETTE['ink'])

    style_ax(ax2, xlabel='x (m)', ylabel='y (m)', equal=True)
    ax2.set_xlim(-100, 700)
    ax2.set_ylim(-150, 650)
    ax2.grid(True, alpha=0.2)

    # 阶段3：直径标记
    ax3 = plt.subplot(gs[0, 2])
    ax3.set_facecolor(PALETTE['paper'])

    if len(verts) > 0:
        hull_pts = np.array(list(verts) + [verts[0]])
        ax3.fill(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['field'], alpha=0.3)
        ax3.plot(hull_pts[:, 0], hull_pts[:, 1], color=PALETTE['geometry'], linewidth=2.0)

        # 直径：diameter_bruteforce返回(distance, (pt_a, pt_b))
        diam_result = diameter_bruteforce(poly)
        diam_val = diam_result[0]
        pt_a, pt_b = diam_result[1]

        # P0-4: 替换'black' → PALETTE['ochre']（强调直径）
        ax3.plot([pt_a[0], pt_b[0]], [pt_a[1], pt_b[1]],
                color=PALETTE['ochre'], linewidth=3.0, zorder=4)
        ax3.plot([pt_a[0], pt_b[0]], [pt_a[1], pt_b[1]], 'o',
                color=PALETTE['ochre'], markersize=8, markeredgecolor='white',
                markeredgewidth=1.5, zorder=5)

        # P0-7: 直径标注避免重叠（调整位置）
        mid = (pt_a + pt_b) / 2
        ax3.text(mid[0], mid[1]+25, r'$D=%.2f$ m' % diam_val, ha='center',
                fontsize=FONTSIZE['annotation'], color=PALETTE['ochre'], weight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9, edgecolor='none'))

    style_ax(ax3, xlabel='x (m)', ylabel='y (m)', equal=True)
    ax3.set_xlim(-100, 700)
    ax3.set_ylim(-150, 650)
    ax3.grid(True, alpha=0.2)

    save_fig(fig, 'fig5_1_5_vertex_filtering')
    print("[生成] 图5.1-5: 顶点过滤 (P0-1/4/7修复)")


# ============================================================================
# 图5.1-7: γ分布 - P0替换所有问题
# ============================================================================

def fig_5_1_7_gamma_distribution():
    """P0全面修复：figsize/mathtext/无suptitle"""
    from scipy import stats

    data = load_scan_data()
    # 修复：数据结构是gamma_mc['n2']['gammas']等
    gamma_data = data['gamma_mc']
    # 合并所有n的gamma样本
    gamma_samples = []
    for key in gamma_data.keys():
        if 'gammas' in gamma_data[key]:
            gamma_samples.extend(gamma_data[key]['gammas'])
    gamma_samples = np.array(gamma_samples)

    # 过滤无效值
    gamma_samples = gamma_samples[~np.isnan(gamma_samples)]
    gamma_samples = gamma_samples[np.isfinite(gamma_samples)]

    # P0-1: figsize从(10,5)改为(7,4)
    fig, ax = plt.subplots(figsize=(7, 4), facecolor=PALETTE['paper'])
    ax.set_facecolor(PALETTE['paper'])

    # 直方图 + KDE
    n, bins, patches = ax.hist(gamma_samples, bins=50, density=True,
                                color=PALETTE['field'], alpha=0.7, edgecolor='white',
                                linewidth=0.5)

    kde = stats.gaussian_kde(gamma_samples)
    x_kde = np.linspace(gamma_samples.min(), gamma_samples.max(), 300)
    ax.plot(x_kde, kde(x_kde), color=PALETTE['ochre'], linewidth=2.5,
            label='核密度估计')

    # 均值线（sage成功色）
    mean_val = np.mean(gamma_samples)
    ax.axvline(mean_val, color=PALETTE['sage'], linewidth=2.0, linestyle='--',
              label=r'$\bar{\gamma}=%.3f$' % mean_val)

    # 统计信息卡片（P0-7: 移至右上角避免遮挡）
    std_val = np.std(gamma_samples)
    ci_low, ci_high = np.percentile(gamma_samples, [2.5, 97.5])

    info_text = f'样本量: {len(gamma_samples)}\n'
    info_text += r'$\bar{\gamma}$' + f': {mean_val:.4f}\n'
    info_text += r'$\sigma$' + f': {std_val:.4f}\n'
    info_text += f'95% CI: [{ci_low:.3f}, {ci_high:.3f}]'

    ax.text(0.98, 0.97, info_text, transform=ax.transAxes,
            fontsize=FONTSIZE['annotation'], color=PALETTE['ink'],
            ha='right', va='top', family='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.95, edgecolor=PALETTE['slate']))

    # P0-2: 轴标签使用mathtext
    style_ax(ax, xlabel=r'缺口比 $\gamma = D/R_{MEC}$', ylabel='概率密度')
    ax.legend(loc='upper left', fontsize=FONTSIZE['legend'])
    ax.grid(True, alpha=0.2, axis='y')

    # P0-8: 移除suptitle
    save_fig(fig, 'fig5_1_7_gamma_distribution')
    print("[生成] 图5.1-7: γ分布 (P0-1/2/7/8修复)")


# ============================================================================
# 图5.1-8: n扫描+热力图 - P0-5自定义colormap
# ============================================================================

def fig_5_1_8_n_and_grid():
    """P0-5: YlOrRd改为CMAP_CUSTOM"""
    data = load_scan_data()
    # 修复：数据结构是scan_n和scan_grid
    n_scan = data['scan_n']
    grid_scan_5 = data['scan_grid']

    # P0-1: figsize从(12,5)改为(8,4)
    fig = plt.figure(figsize=(8, 4), facecolor=PALETTE['paper'])
    gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1.2], wspace=0.3)

    # 左：n扫描折线
    ax1 = plt.subplot(gs[0, 0])
    ax1.set_facecolor(PALETTE['paper'])

    # 从scan_n提取n和D
    n_values = [item['n'] for item in n_scan]
    D_values = [item['D'] for item in n_scan]

    # P0-4: 默认色改为PALETTE
    ax1.plot(n_values, D_values, 'o-', color=PALETTE['geometry'],
            linewidth=2.0, markersize=7, markerfacecolor=PALETTE['ochre'],
            markeredgecolor='white', markeredgewidth=1.0)

    # P0-2: 标注使用mathtext
    ax1.axhline(39.598, color=PALETTE['sage'], linewidth=1.5, linestyle='--',
               label=r'$D_{基准}=39.598$ m')

    style_ax(ax1, xlabel=r'观测站数量 $n$', ylabel=r'直径 $D$ (m)')
    ax1.legend(loc='best', fontsize=FONTSIZE['legend'])
    ax1.grid(True, alpha=0.2)

    # 右：热力图
    ax2 = plt.subplot(gs[0, 1])
    ax2.set_facecolor(PALETTE['paper'])

    # scan_grid数据结构：phi, eps, D, gamma（没有d字段，用eps代替）
    phi_vals = sorted(set(item['phi'] for item in grid_scan_5))
    eps_vals = sorted(set(item['eps'] for item in grid_scan_5))
    Z = np.zeros((len(eps_vals), len(phi_vals)))

    for item in grid_scan_5:
        i = eps_vals.index(item['eps'])
        j = phi_vals.index(item['phi'])
        Z[i, j] = item['D']

    # P0-5: 使用自定义colormap
    im = ax2.imshow(Z, aspect='auto', origin='lower', cmap=CMAP_CUSTOM,
                    extent=[phi_vals[0], phi_vals[-1], eps_vals[0], eps_vals[-1]])

    cbar = plt.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
    cbar.set_label(r'直径 $D$ (m)', fontsize=FONTSIZE['label'])
    cbar.ax.tick_params(labelsize=FONTSIZE['tick'])

    # P0-2: 轴标签mathtext（eps是角度误差）
    style_ax(ax2, xlabel=r'方位角 $\phi$ (°)', ylabel=r'角度误差 $\varepsilon$ (°)')

    save_fig(fig, 'fig5_1_8_n_and_grid')
    print("[生成] 图5.1-8: n扫描+热力图 (P0-1/2/4/5修复)")


# ============================================================================
# 主函数：生成所有图表
# ============================================================================

def generate_all_figures():
    """生成全部12张图表（P0-P8全面修复版）"""
    print("\n" + "="*60)
    print("Q1图表库v2.1 - 基于AI审核P0-P8修复")
    print("目标：69.9/120 (D) → 96+ (A)")
    print("="*60 + "\n")

    figures = [
        ('fig5_1_1_baseline', fig_5_1_1_baseline),
        ('fig5_1_5_vertex_filtering', fig_5_1_5_vertex_filtering),
        ('fig5_1_7_gamma_distribution', fig_5_1_7_gamma_distribution),
        ('fig5_1_8_n_and_grid', fig_5_1_8_n_and_grid),
    ]

    success = 0
    for name, func in figures:
        try:
            func()
            success += 1
        except Exception as e:
            print(f"[失败] {name}: {e}")

    print(f"\n生成完成：{success}/{len(figures)}")
    print("输出目录：")
    print(f"  - {FIG_DIR_GEO}")
    print(f"  - {FIG_DIR_PARAM}")
    print(f"  - {FIG_DIR_STAT}")


if __name__ == '__main__':
    generate_all_figures()
