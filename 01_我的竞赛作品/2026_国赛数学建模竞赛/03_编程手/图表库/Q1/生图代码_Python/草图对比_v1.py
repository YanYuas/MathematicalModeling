# -*- coding: utf-8 -*-
"""
草图对比脚本 —— 仅用于方案选型，不是最终交付

产出：
  草图A  图5.1-2 候选：共用参照系的角域收敛
  草图B  图5.1-8(b) 候选：3x3 楔形小图阵列

输出到 98_草图对比/
"""
import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge as MWedge, Polygon as MPolygon, FancyArrowPatch, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '实验结果'))
from q1_main import build_wedges, candidate_vertices, convex_hull, diameter_bruteforce, mec_bruteforce

OUT = os.path.join(HERE, '..', '98_草图对比')
os.makedirs(OUT, exist_ok=True)

PAL = {
    "ink": "#1A1A1A", "slate": "#6B7B83", "paper": "#FAF7F0",
    "field": "#B8CFE0", "geometry": "#26466D", "ochre": "#C47B2B",
    "rust": "#8C3A2A", "sage": "#3D6B52", "gold": "#D4A843",
}

matplotlib.rcParams.update({
    'font.size': 11,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
    'mathtext.fontset': 'stix',
    'axes.unicode_minus': False,
    'axes.edgecolor': PAL['slate'],
    'axes.labelcolor': PAL['ink'],
    'text.color': PAL['ink'],
    'xtick.color': PAL['slate'],
    'ytick.color': PAL['slate'],
    'figure.dpi': 200, 'savefig.dpi': 200,
    'svg.fonttype': 'none',
})

# 题设基准
L = 600.0
S1 = np.array([0.0, 0.0])
S2 = np.array([L, 0.0])
G = np.array([300.0, 500.0])
EPS_BASE = 1.0
TH1 = float(np.rad2deg(np.arctan2(G[1] - S1[1], G[0] - S1[0])))            # 59.036
TH2 = float(np.rad2deg(np.arctan2(G[1] - S2[1], G[0] - S2[0])))            # 120.964
if TH2 < 0:
    TH2 += 360.0


def solve(theta1, theta2, eps):
    """给示向度与半角，返回 (凸包顶点list, D, (pa,pb), (center,R))"""
    wedges = build_wedges([S1, S2], [theta1, theta2], eps)
    cand = candidate_vertices(wedges)
    poly = convex_hull(cand)
    if poly is None:
        return None
    verts = list(poly.vertices)
    if len(verts) < 3:
        return None
    D, (pa, pb) = diameter_bruteforce(poly)
    center, R = mec_bruteforce(verts)
    return verts, D, (pa, pb), (center, R)


def draw_baseline(ax, y=-140):
    """基线 + 两个站，三面板共用"""
    ax.plot([S1[0], S2[0]], [S1[1], S2[1]], color=PAL['geometry'], lw=2.0, zorder=4,
            solid_capstyle='round')
    for S, lab in [(S1, r'$S_1$'), (S2, r'$S_2$')]:
        ax.plot(S[0], S[1], 's', color=PAL['geometry'], ms=8,
                markeredgecolor='white', markeredgewidth=1.2, zorder=6)
        ax.text(S[0], y, lab, ha='center', va='top', fontsize=12,
                color=PAL['ink'], weight='bold')


def draw_wedge(ax, S, theta, eps, color, alpha=0.20, r=760, zorder=1):
    ax.add_patch(MWedge(S, r, theta - eps, theta + eps,
                        facecolor=color, alpha=alpha, edgecolor='none', zorder=zorder))
    for a in (theta - eps, theta + eps):
        d = np.array([np.cos(np.deg2rad(a)), np.sin(np.deg2rad(a))])
        e = S + r * d
        ax.plot([S[0], e[0]], [S[1], e[1]], color=color, lw=1.2,
                ls=(0, (5, 3)), alpha=0.85, zorder=zorder + 1)


def draw_central_ray(ax, S, theta, r, color, zorder=5):
    d = np.array([np.cos(np.deg2rad(theta)), np.sin(np.deg2rad(theta))])
    e = S + r * d
    ax.annotate('', xy=e, xytext=S,
                arrowprops=dict(arrowstyle='-|>', color=color, lw=1.8,
                                shrinkA=0, shrinkB=0), zorder=zorder)


def scalebar(ax, x0, y0, length, label, color):
    ax.plot([x0, x0 + length], [y0, y0], color=color, lw=2.2, solid_capstyle='butt', zorder=7)
    for x in (x0, x0 + length):
        ax.plot([x, x], [y0 - 14, y0 + 14], color=color, lw=1.6, zorder=7)
    ax.text(x0 + length / 2, y0 + 24, label, ha='center', va='bottom',
            fontsize=10, color=color, zorder=7)


# ============================================================================
# 草图A：图5.1-2 候选 —— 共用参照系
# ============================================================================

def sketch_A():
    """三面板共用同一小视窗 —— 只有这样 2ε 宽的楔形才可见"""
    fig = plt.figure(figsize=(7.2, 3.2), facecolor=PAL['paper'])
    gs = fig.add_gridspec(1, 3, wspace=0.08)

    # 基准算例交会区中心
    C0 = np.array([300.0, 500.0])
    HX, HY = 70.0, 52.0
    XLIM = (C0[0] - HX, C0[0] + HX)
    YLIM = (C0[1] - HY, C0[1] + HY)

    def setup(ax, title, show_y):
        ax.set_facecolor(PAL['paper'])
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
        ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
        ax.set_aspect('equal')
        ax.tick_params(labelsize=10)
        if not show_y:
            ax.set_yticklabels([])
        ax.set_title(title, fontsize=12, weight='bold', pad=8)
        ax.grid(True, alpha=0.18, lw=0.5)

    def clip_box(ax):
        """视窗足够长的射线半径"""
        return 4 * max(XLIM[1] - S1[0], YLIM[1] - S1[1])

    res = solve(TH1, TH2, EPS_BASE)

    # ---- (a) 单站：只有一个楔形穿过视窗 ----
    ax1 = fig.add_subplot(gs[0, 0])
    setup(ax1, r'(a) 单站：一条窄带', True)
    draw_wedge(ax1, S1, TH1, EPS_BASE, PAL['geometry'], alpha=0.30,
               r=clip_box(ax1), zorder=1)
    ax1.annotate('', xy=(C0[0] + 30, C0[1] + 22), xytext=(C0[0] - 40, C0[1] - 28),
                 arrowprops=dict(arrowstyle='-|>', color=PAL['geometry'], lw=2.0))
    # 楔形在交会点处的实际宽度
    d1 = np.hypot(C0[0] - S1[0], C0[1] - S1[1])
    band = 2 * d1 * np.tan(np.deg2rad(EPS_BASE))
    ax1.text(0.5, 0.06, r'带宽 $\approx %.1f$ m，无距离约束' % band,
             transform=ax1.transAxes, ha='center', va='bottom', fontsize=10,
             color=PAL['ink'],
             bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=PAL['slate'],
                       lw=0.8, alpha=0.95))
    ax1.set_ylabel('y (m)', fontsize=11)

    # ---- (b) 双站：两条窄带相交 ----
    ax2 = fig.add_subplot(gs[0, 1])
    setup(ax2, r'(b) 双站：交会成域', False)
    draw_wedge(ax2, S1, TH1, EPS_BASE, PAL['geometry'], alpha=0.28,
               r=clip_box(ax2), zorder=1)
    draw_wedge(ax2, S2, TH2, EPS_BASE, PAL['ochre'], alpha=0.24,
               r=clip_box(ax2), zorder=1)
    ax2.text(0.5, 0.06, '两带相交 $\\Rightarrow$ 有界四边形',
             transform=ax2.transAxes, ha='center', va='bottom', fontsize=10,
             color=PAL['ink'],
             bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=PAL['slate'],
                       lw=0.8, alpha=0.95))

    # ---- (c) 定位域 + D + MEC ----
    ax3 = fig.add_subplot(gs[0, 2])
    setup(ax3, r'(c) 定位域：$D$ 与 $R_{\mathrm{MEC}}$', False)
    draw_wedge(ax3, S1, TH1, EPS_BASE, PAL['geometry'], alpha=0.12,
               r=clip_box(ax3), zorder=1)
    draw_wedge(ax3, S2, TH2, EPS_BASE, PAL['ochre'], alpha=0.10,
               r=clip_box(ax3), zorder=1)
    if res:
        verts, D, (pa, pb), (C, R) = res
        v = np.array(verts); vv = np.vstack([v, v[0]])
        ax3.fill(vv[:, 0], vv[:, 1], color=PAL['field'], alpha=0.85, zorder=3)
        ax3.plot(vv[:, 0], vv[:, 1], color=PAL['geometry'], lw=2.2, zorder=4)
        ax3.add_patch(Circle(C, R, fill=False, ec=PAL['sage'], lw=1.8,
                             ls=(0, (6, 3)), zorder=5))
        ax3.plot([pa[0], pb[0]], [pa[1], pb[1]], color=PAL['ochre'], lw=2.6, zorder=6)
        for p in (pa, pb):
            ax3.plot(p[0], p[1], 'o', color=PAL['ochre'], ms=7,
                     markeredgecolor='white', markeredgewidth=1.2, zorder=7)
        ax3.plot(G[0], G[1], '*', color=PAL['gold'], ms=15,
                 markeredgecolor=PAL['ink'], markeredgewidth=0.8, zorder=8)
        ax3.annotate(r'$D=%.2f$ m' % D, xy=(300, 480), xytext=(318, 462),
                     fontsize=11, color=PAL['ochre'], weight='bold',
                     arrowprops=dict(arrowstyle='->', color=PAL['ochre'], lw=1.2),
                     bbox=dict(boxstyle='round,pad=0.3', fc='white',
                               ec=PAL['ochre'], lw=0.9, alpha=0.95), zorder=9)
        ax3.plot(300, 500, '*', color=PAL['gold'], ms=15,
                 markeredgecolor=PAL['ink'], markeredgewidth=0.8, zorder=8)

    for x0, x1 in [(0.335, 0.365), (0.665, 0.695)]:
        fig.add_artist(FancyArrowPatch((x0, 0.5), (x1, 0.5),
                                       transform=fig.transFigure,
                                       arrowstyle='-|>', mutation_scale=22,
                                       color=PAL['ochre'], lw=2.4))

    fig.subplots_adjust(left=0.06, right=0.99, top=0.88, bottom=0.12)
    p = os.path.join(OUT, '草图A_5.1-2_共用参照系.png')
    fig.savefig(p, facecolor=PAL['paper'], bbox_inches='tight')
    plt.close(fig)
    print('[OK]', p)


# ============================================================================
# 草图B：图5.1-8(b) 候选 —— 3x3 楔形阵列
# ============================================================================

def sketch_B():
    data = json.load(open(os.path.join(HERE, '..', '..', '实验结果',
                                       'q1_scan_results.json'), encoding='utf-8'))
    grid = {(round(r['phi'], 3), round(r['eps'], 3)): r['D'] for r in data['scan_grid']}

    phis = [30, 60, 90]                 # 列：交会角
    epss = [2.0, 1.25, 0.5]             # 行：误差半角

    fig = plt.figure(figsize=(7.2, 7.4), facecolor=PAL['paper'])
    gs = fig.add_gridspec(3, 3, hspace=0.32, wspace=0.22,
                          left=0.10, right=0.99, top=0.90, bottom=0.10)

    # 每个面板的视窗以交会点为中心，但统一尺寸
    HALF = 300.0

    for i, eps in enumerate(epss):
        for j, phi in enumerate(phis):
            ax = fig.add_subplot(gs[i, j])
            ax.set_facecolor(PAL['paper'])
            for sp in ('top', 'right'):
                ax.spines[sp].set_visible(False)
            ax.set_aspect('equal')

            # scan_grid 的 phi 是真交会角：由 h=(L/2)/tan(phi/2) 反推源点高度
            h = (L / 2.0) / np.tan(np.deg2rad(phi) / 2.0)
            src = np.array([L / 2.0, h])
            th1 = float(np.rad2deg(np.arctan2(src[1] - S1[1], src[0] - S1[0])))
            th2 = float(np.rad2deg(np.arctan2(src[1] - S2[1], src[0] - S2[0])))
            if th2 < 0:
                th2 += 360.0
            res = solve(th1, th2, eps)
            D = grid.get((float(phi), float(eps)))

            if res:
                verts = res[0]
                cx, cy = np.mean(np.array(verts), axis=0)
            else:
                verts = None
                cx, cy = 300.0, 300.0

            # 视窗半宽随 D 自适应 —— 草图B 的核心设计点
            half = max(1.55 * (D if D is not None else 50.0), 17.0)
            hx, hy = half, half * 0.72
            x0, x1 = cx - hx, cx + hx
            y0, y1 = cy - hy, cy + hy
            ax.set_xlim(x0, x1)
            ax.set_ylim(y0, y1)

            # 角域半径取到视窗四角之外，弧不进画面
            rr = 1.12 * max(np.hypot(xx - S[0], yy - S[1])
                            for S in (S1, S2)
                            for xx in (x0, x1) for yy in (y0, y1))
            draw_wedge(ax, S1, th1, eps, PAL['geometry'], alpha=0.22, r=rr, zorder=1)
            draw_wedge(ax, S2, th2, eps, PAL['ochre'], alpha=0.18, r=rr, zorder=1)

            if verts is not None:
                v = np.array(verts); vv = np.vstack([v, v[0]])
                ax.fill(vv[:, 0], vv[:, 1], color=PAL['field'], alpha=0.88, zorder=3)
                ax.plot(vv[:, 0], vv[:, 1], color=PAL['geometry'], lw=2.0, zorder=4)

            ax.set_xticks([]); ax.set_yticks([])

            # 核心数值
            if D is not None:
                ax.text(0.5, -0.05, r'$D=%.1f$ m' % D, transform=ax.transAxes,
                        ha='center', va='top', fontsize=12, weight='bold',
                        color=PAL['ochre'])

            # 行/列标签
            if j == 0:
                ax.set_ylabel(r'$\varepsilon=%.2f^\circ$' % eps, fontsize=11,
                              color=PAL['ink'], labelpad=4)
            if i == 0:
                ax.set_title(r'$\varphi=%d^\circ$' % phi, fontsize=12,
                             weight='bold', pad=6)

    p = os.path.join(OUT, '草图B_5.1-8b_楔形阵列.png')
    fig.savefig(p, facecolor=PAL['paper'], bbox_inches='tight')
    plt.close(fig)
    print('[OK]', p)


if __name__ == '__main__':
    sketch_A()
    sketch_B()
