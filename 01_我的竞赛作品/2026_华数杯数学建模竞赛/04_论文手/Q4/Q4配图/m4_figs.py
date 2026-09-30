# -*- coding: utf-8 -*-
"""m4_figs.py — Q4 配图生成（matplotlib 静态图，10 张，无需外部数据）— 24 修正版
图1 剖分化归 / 图2 缺口互补（右格改：单模块旋转兑现）/ 图3 最优摆放=24 横版（核心）
图5 旋转C4（校对缺口坐标）/ 图6 可行性8vs36 / 图7 包络锚=24 全局最优
新图A 双最优解对比 / 新图B 灵敏度 / 新图C 缺口精确填充 / 新图D SAT误判 vs 单位格
⚠️ 图4"24不可达"已删除（被 24 完美平铺反证）。数字一律 24，禁 30。
输出: 当前目录 q4_figN_*.png
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, FancyArrowPatch

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.dirname(os.path.abspath(__file__))

# design tokens
C_T = '#E67E22'   # T 型
C_L = '#2980B9'   # L 型
C_R1 = '#27AE60'  # 矩形1 b3
C_R2 = '#8E44AD'  # 矩形2 b4
C_OUT = '#C0392B'  # 包络框
C_GAP = '#F5B041'  # 缺口
C_EDGE = '#2C3E50'
C_OK = '#1E8449'
C_BAD = '#C0392B'

# 模块顶点（逆时针，局部）
B1 = [(1,0),(3,0),(3,2),(4,2),(4,4),(0,4),(0,2),(1,2)]   # T
B2 = [(0,0),(2,0),(2,2),(1,2),(1,4),(0,4)]               # L
B3 = [(0,0),(2,0),(2,1),(0,1)]                            # 矩形 2x1
B4 = [(0,0),(1,0),(1,4),(0,4)]                            # 矩形 1x4


def rot(verts, deg):
    if deg == 0:
        return [(float(x), float(y)) for x, y in verts]
    out = []
    for x, y in verts:
        if deg == 90: nx, ny = -y, x
        elif deg == 180: nx, ny = -x, -y
        else: nx, ny = y, -x
        out.append((nx, ny))
    mx = min(p[0] for p in out); my = min(p[1] for p in out)
    return [(x-mx, y-my) for x, y in out]


def shift(verts, off):
    return [(x+off[0], y+off[1]) for x, y in verts]


def draw_poly(ax, verts, fc='#D6EAF8', ec=C_EDGE, lw=1.5, alpha=0.9, label=None, lc='white'):
    pts = [(x, y) for x, y in verts]
    ax.add_patch(Polygon(pts, closed=True, facecolor=fc, edgecolor=ec, linewidth=lw, alpha=alpha))
    if label:
        cx = sum(p[0] for p in pts)/len(pts)
        cy = sum(p[1] for p in pts)/len(pts)
        ax.text(cx, cy, label, ha='center', va='center', fontsize=10, color=lc, fontweight='bold')


def setup_ax(ax, xlim, ylim):
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_aspect('equal')
    ax.axis('off')


# ============ 图1 剖分化归示意 ============
def fig1():
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    ax = axes[0]
    setup_ax(ax, (-0.5, 4.5), (-0.5, 4.5))
    draw_poly(ax, B1, fc=C_T, alpha=0.85)
    ax.set_title('L/T 凹多边形', fontsize=13)
    ax = axes[1]
    setup_ax(ax, (-0.5, 4.5), (-0.5, 4.5))
    ax.add_patch(Rectangle((1,0), 2, 2, fc='#FAD7A0', ec=C_EDGE, lw=1.5, alpha=0.95))
    ax.add_patch(Rectangle((0,2), 4, 2, fc='#F5CBA7', ec=C_EDGE, lw=1.5, alpha=0.95))
    ax.annotate('', xy=(2,0.1), xytext=(2,-0.3),
                arrowprops=dict(arrowstyle='<->', color=C_GAP, lw=1.5))
    ax.text(2.15, -0.55, 'abutment 粘合', fontsize=10, color=C_GAP)
    ax.set_title('guillotine 剖分 + abutment', fontsize=13)
    ax = axes[2]
    setup_ax(ax, (-0.5, 4.5), (-0.5, 4.5))
    ax.add_patch(Rectangle((0,0), 4, 4, fc='#F39C12', ec=C_OUT, lw=2.5, alpha=0.4))
    ax.text(2, 2, '复合块\n(近矩形)', ha='center', va='center', fontsize=11, color=C_EDGE, fontweight='bold')
    ax.annotate('', xy=(4.6,2), xytext=(4.9,2),
                arrowprops=dict(arrowstyle='->', color=C_EDGE, lw=2))
    ax.text(5.05, 2, '进\nB*-Tree', fontsize=10, color=C_EDGE, ha='center', va='center')
    ax.set_title('化归回矩形装箱', fontsize=13)
    fig.suptitle('Q4-图1 剖分-粘合-化归：L/T 凹块 → 复合块 → Q1 矩形装箱', fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'q4_fig1_abutment.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('图1 OK')


# ============ 图2 缺口互补（右格改写：单模块旋转兑现） ============
def fig2():
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    ax = axes[0]
    setup_ax(ax, (-0.5, 4.5), (-0.5, 4.5))
    draw_poly(ax, B1, fc=C_T, alpha=0.85)
    ax.add_patch(Rectangle((0,0), 1, 2, fc=C_GAP, ec='none', alpha=0.5))
    ax.text(0.5, 1, '缺口\n1×2', ha='center', va='center', fontsize=9, color='#7D6608')
    ax.text(2, 4.2, 'b1 缺口面积 4', ha='center', fontsize=10, color=C_EDGE)
    ax = axes[1]
    setup_ax(ax, (-0.5, 4.5), (-0.5, 4.5))
    draw_poly(ax, B2, fc=C_L, alpha=0.85)
    ax.add_patch(Rectangle((1,2), 1, 2, fc=C_GAP, ec='none', alpha=0.5))
    ax.text(1.5, 3, '缺口\n1×2', ha='center', va='center', fontsize=9, color='#7D6608')
    ax.text(1, 4.2, 'b2 缺口面积 2', ha='center', fontsize=10, color=C_EDGE)
    ax = axes[2]
    setup_ax(ax, (-0.5, 4.5), (-0.5, 4.5))
    ax.text(2, 3.2, '缺口总面积 6', fontsize=13, ha='center', fontweight='bold', color=C_OUT)
    ax.text(2, 2.4, '= b3(2) + b4(4)', fontsize=12, ha='center', color=C_EDGE)
    ax.text(2, 1.6, '凹对凹是面积机会', fontsize=12, ha='center', color=C_EDGE)
    ax.text(2, 0.8, 'b3 转90°填缺口 → 24 完美平铺', fontsize=10.5, ha='center', color=C_OK)
    ax.text(2, 0.1, '（全固定0°退化28）', fontsize=9.5, ha='center', color='#7D6608')
    ax.set_title('Q4-图2 缺口互补：凹口是负空间，单模块旋转即兑现', fontsize=13)
    fig.suptitle('Q4-图2 缺口互补示意', fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'q4_fig2_gap.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('图2 OK')


# ============ 图3 最优摆放 = 24 横版（核心，重画） ============
def fig3():
    fig, ax = plt.subplots(figsize=(9.5, 8))
    # 横版解：b1 rot0@(0,0) + b2 rot0@(-1,0) + b3 rot90@(3,0) + b4 rot0@(4,0)
    draw_poly(ax, shift(B1, (0,0)), fc=C_T, alpha=0.85, label='b1 T')
    draw_poly(ax, shift(B2, (-1,0)), fc=C_L, alpha=0.85, label='b2 L')
    draw_poly(ax, shift(rot(B3, 90), (3,0)), fc=C_R1, alpha=0.85, label='b3')
    draw_poly(ax, shift(B4, (4,0)), fc=C_R2, alpha=0.85, label='b4')
    ax.add_patch(Rectangle((-1,0), 6, 4, fill=False, ec=C_OUT, lw=3))
    ax.annotate('', xy=(-1,-0.5), xytext=(5,-0.5), arrowprops=dict(arrowstyle='<->', color=C_OUT, lw=1.5))
    ax.text(2, -0.8, 'W=6', ha='center', fontsize=12, color=C_OUT, fontweight='bold')
    ax.annotate('', xy=(-1.5,0), xytext=(-1.5,4), arrowprops=dict(arrowstyle='<->', color=C_OUT, lw=1.5))
    ax.text(-1.9, 2, 'H=4', va='center', fontsize=12, color=C_OUT, fontweight='bold')
    ax.text(6.4, 3.6, '最小包络 = 24', fontsize=15, fontweight='bold', color=C_OK)
    ax.text(6.4, 2.9, '= 面积下界 = 全局最优', fontsize=11, color=C_EDGE)
    ax.text(6.4, 2.2, '6 × 4，死区 0%', fontsize=13, color=C_EDGE)
    ax.text(6.4, 1.5, '完美平铺', fontsize=12, color=C_OK)
    ax.text(6.4, 0.8, 'b1@(0,0) b2@(-1,0)', fontsize=10, color=C_EDGE)
    ax.text(6.4, 0.1, 'b3 rot90@(3,0) b4@(4,0)', fontsize=10, color=C_EDGE)
    setup_ax(ax, (-2.5, 10.5), (-1.3, 4.6))
    ax.set_title('Q4-图3 最优摆放=24：b3 转90°填缺口，完美平铺（横版 6×4）', fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'q4_fig3_optimal.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('图3 OK')


# ============ 图4 已删除（24 不可达被反证）============
def fig4():
    print('图4 已删除（"24 不可达"被 24 完美平铺反证，勿用）')


# ============ 图5 旋转 C4（校对缺口坐标） ============
def fig5():
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.8))
    # 各朝向 L 的缺口位置（校对后）：rot0 右上 / rot90 左上 / rot180 右下 / rot270 左下
    notches = {
        0: (1, 2, 1, 2),      # x,y,w,h
        90: (0, 1, 2, 1),
        180: (1, 0, 1, 2),
        270: (2, 0, 2, 1),
    }
    for i, deg in enumerate([0, 90, 180, 270]):
        ax = axes[i]
        setup_ax(ax, (-1.5, 3.5), (-1.5, 3.5))
        draw_poly(ax, rot(B2, deg), fc=C_L, alpha=0.85)
        nx, ny, nw, nh = notches[deg]
        ax.add_patch(Rectangle((nx, ny), nw, nh, fc=C_GAP, ec='none', alpha=0.5))
        ax.text(nx+nw/2, ny+nh/2, '缺', ha='center', va='center', fontsize=9, color='#7D6608')
        ax.set_title(f'{deg}°', fontsize=14)
    fig.suptitle('Q4-图5 旋转群 C4：L 型缺口朝向随旋转改变（4 朝向全不同）', fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'q4_fig5_rotC4.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('图5 OK')


# ============ 图6 可行性条件 8 vs 36 ============
def fig6():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    ax = axes[0]
    setup_ax(ax, (-0.5, 4.5), (-0.5, 4.5))
    ax.add_patch(Rectangle((1,0), 2, 2, fc='#FAD7A0', ec=C_EDGE, lw=1.5))
    ax.add_patch(Rectangle((0,2), 4, 2, fc='#F5CBA7', ec=C_EDGE, lw=1.5))
    ax.text(2, 1, 'A', ha='center', va='center', fontsize=12, fontweight='bold', color=C_EDGE)
    ax.text(2, 3, 'B', ha='center', va='center', fontsize=12, fontweight='bold', color=C_EDGE)
    ax.text(0.3, 3.6, 'T 型 3 子块', fontsize=11, color=C_EDGE)
    ax.set_title('T 型剖分 3 子矩形', fontsize=12)
    ax = axes[1]
    ax.axis('off')
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.bar([2.5, 6.5], [36, 8], width=2.2, color=['#BDC3C7', '#E67E22'], edgecolor=C_EDGE)
    ax.text(2.5, 8.6, '3! = 36', ha='center', fontsize=15, fontweight='bold', color='#7F8C8D')
    ax.text(6.5, 4.8, '8', ha='center', fontsize=15, fontweight='bold', color=C_OUT)
    ax.text(6.5, 0.5, '可行排列', ha='center', fontsize=10, color=C_EDGE)
    ax.text(2.5, 0.5, '全部排列', ha='center', fontsize=10, color=C_EDGE)
    ax.text(4.5, 9.2, 'B*-Tree 可行性条件：凹块不能全树搜索', fontsize=12, ha='center', color=C_EDGE)
    fig.suptitle('Q4-图6 可行性条件（Wu/Chang/Chang 2003）：缩解空间是正确性前提', fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'q4_fig6_feasibility.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('图6 OK')


# ============ 图7 包络锚：下界 24 = 可达 = 全局最优（重画） ============
def fig7():
    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.axhline(24, color='#1E8449', ls='--', lw=2)
    ax.text(9.3, 24.4, '面积下界 24（可达，全局最优）', color='#1E8449', fontsize=11, ha='right')
    ax.scatter([6], [24], s=240, color='#C0392B', zorder=5)
    ax.text(6, 25.2, '最小包络 24（死区 0%）', ha='center', fontsize=12, color='#C0392B', fontweight='bold')
    ax.annotate('b3 转90°填缺口 + b2 补左 + b4 补右\n→ 完美平铺 6×4', xy=(6,24), xytext=(2.6,20.5),
                fontsize=10, color=C_EDGE,
                arrowprops=dict(arrowstyle='->', color=C_EDGE, lw=1.2))
    ax.scatter([6], [28], s=120, color='#7F8C8D', zorder=4)
    ax.text(6.15, 28.5, '全固定 0° → 28', ha='left', fontsize=9.5, color='#7F8C8D')
    ax.set_xlim(0, 10); ax.set_ylim(18, 32)
    ax.set_xticks([])
    ax.set_ylabel('最小包络面积')
    ax.grid(alpha=0.3)
    ax.set_title('Q4-图7 验证题面积锚：下界 24 = 可达 = 全局最优（旋转兑现缺口互补）', fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'q4_fig7_area.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('图7 OK')


# ============ 新图A 双最优解对比（横版 vs 竖版） ============
def figA():
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    # 横版 6×4
    ax = axes[0]
    setup_ax(ax, (-1.8, 5.4), (-0.4, 4.4))
    draw_poly(ax, shift(B1, (0,0)), fc=C_T, alpha=0.8, label='b1')
    draw_poly(ax, shift(B2, (-1,0)), fc=C_L, alpha=0.8, label='b2')
    draw_poly(ax, shift(rot(B3,90), (3,0)), fc=C_R1, alpha=0.8, label='b3')
    draw_poly(ax, shift(B4, (4,0)), fc=C_R2, alpha=0.8, label='b4')
    ax.add_patch(Rectangle((-1,0), 6, 4, fill=False, ec=C_OUT, lw=2.5))
    ax.text(2, -0.25, '横版 6×4（b3 单旋转）', ha='center', fontsize=11, fontweight='bold', color=C_EDGE)
    ax.text(4.8, 4.1, '24', ha='center', fontsize=13, fontweight='bold', color=C_OK)
    # 竖版 4×6
    ax = axes[1]
    setup_ax(ax, (-0.4, 4.4), (-0.4, 6.4))
    draw_poly(ax, shift(rot(B1,180), (0,0)), fc=C_T, alpha=0.8, label='b1')
    draw_poly(ax, shift(rot(B2,180), (2,2)), fc=C_L, alpha=0.8, label='b2')
    draw_poly(ax, shift(rot(B3,90), (1,4)), fc=C_R1, alpha=0.8, label='b3')
    draw_poly(ax, shift(B4, (0,2)), fc=C_R2, alpha=0.8, label='b4')
    ax.add_patch(Rectangle((0,0), 4, 6, fill=False, ec=C_OUT, lw=2.5))
    ax.text(2, 6.15, '竖版 4×6（b1/b2 转 180°）', ha='center', fontsize=11, fontweight='bold', color=C_EDGE)
    ax.text(3.9, -0.2, '24', ha='center', fontsize=13, fontweight='bold', color=C_OK)
    fig.suptitle('Q4-新图A 两个 24 最优解：非旋转/镜像等价（多解性）', fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'q4_figA_two_solutions.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('新图A OK')


# ============ 新图B 灵敏度真值 ============
def figB():
    fig, ax = plt.subplots(figsize=(9, 5))
    scen = ['全固定 0°', '仅 b3 旋转', 'b4 固定 0°', 'b1 固定 90°', '全自由']
    vals = [28, 24, 24, 24, 24]
    colors = [C_BAD, C_OK, C_OK, C_OK, C_OK]
    bars = ax.bar(scen, vals, width=0.55, color=colors, edgecolor=C_EDGE, lw=1.2)
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, v+0.4, str(v), ha='center', fontsize=12, fontweight='bold')
    ax.axhline(24, color=C_EDGE, ls='--', lw=1.2, alpha=0.5)
    ax.text(4.4, 24.5, '下界=全局最优 24', ha='right', fontsize=10, color=C_EDGE)
    ax.set_ylim(0, 31)
    ax.set_ylabel('最小包络面积')
    ax.set_title('Q4-新图B 灵敏度：旋转自由度价值集中在 b3（仅转90°即达24；全固定0°退化28）', fontsize=12)
    ax.grid(alpha=0.3, axis='y')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'q4_figB_sensitivity.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('新图B OK')


# ============ 新图C 缺口精确填充（b3 填 b1 缺口，共线贴边） ============
def figC():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    # 左：填缺口前 b1 + 缺口
    ax = axes[0]
    setup_ax(ax, (-0.3, 4.5), (-0.3, 4.5))
    draw_poly(ax, B1, fc=C_T, alpha=0.85)
    ax.add_patch(Rectangle((3,0), 1, 2, fc=C_GAP, ec='none', alpha=0.5))
    ax.text(3.5, 1, '右下缺口\n1×2', ha='center', va='center', fontsize=9, color='#7D6608')
    ax.set_title('b1 右下缺口 1×2（等待填充）', fontsize=11)
    # 右：b3 转90° 恰好填进（共线贴边）
    ax = axes[1]
    setup_ax(ax, (-0.3, 4.5), (-0.3, 4.5))
    draw_poly(ax, B1, fc=C_T, alpha=0.85)
    draw_poly(ax, shift(rot(B3,90), (3,0)), fc=C_R1, alpha=0.95, label='b3', lc='white')
    ax.annotate('共线贴边\n（内部不相交，合法）', xy=(3.0,2.0), xytext=(0.1,3.4),
                fontsize=9.5, color=C_OK, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=C_OK, lw=1.3))
    ax.set_title('b3 转90°恰好填满缺口（缺口互补）', fontsize=11)
    fig.suptitle('Q4-新图C 缺口互补的精确填充：共线贴边必须判不重叠', fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'q4_figC_gap_fill.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('新图C OK')


# ============ 新图D SAT 误判 vs 单位格法 ============
def figD():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    # 左：SAT 共线贴边误判
    ax = axes[0]
    setup_ax(ax, (-0.3, 4.5), (-0.3, 4.5))
    draw_poly(ax, B1, fc=C_T, alpha=0.7)
    draw_poly(ax, shift(rot(B3,90), (3,0)), fc=C_R1, alpha=0.7)
    ax.text(2, 4.15, 'SAT on_seg：边界点判"在内部"\n→ 误判重叠 → 漏掉 24', ha='center',
            fontsize=9.5, color=C_BAD, fontweight='bold')
    ax.set_title('严格 SAT：共线贴边误判重叠（30 的根因）', fontsize=11)
    # 右：单位格法正确
    ax = axes[1]
    setup_ax(ax, (-0.3, 4.5), (-0.3, 4.5))
    draw_poly(ax, B1, fc=C_T, alpha=0.7)
    draw_poly(ax, shift(rot(B3,90), (3,0)), fc=C_R1, alpha=0.7)
    # 画格点中心采样（半整数点）
    for gx in [0.5, 1.5, 2.5, 3.5]:
        for gy in [0.5, 1.5, 2.5, 3.5]:
            ax.plot(gx, gy, 'k.', ms=4)
    ax.plot(3.5, 1.5, 'o', ms=6, color=C_OK, markerfacecolor='none')
    ax.text(2, 4.15, '格点中心 (x+0.5,y+0.5) 采样：贴边处\n无共同中心 → 判不重叠 → 24 可达', ha='center',
            fontsize=9.5, color=C_OK, fontweight='bold')
    ax.set_title('单位格法：格点中心采样，贴边不误判', fontsize=11)
    fig.suptitle('Q4-新图D 重叠判定修正：共线贴边是凹多边形装箱的命门（30→24）', fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'q4_figD_sat_vs_unit.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('新图D OK')


if __name__ == '__main__':
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6(); fig7()
    figA(); figB(); figC(); figD()
    print('全部完成（10 张；图4 占位已删除）')
