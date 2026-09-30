# -*- coding: utf-8 -*-
"""Q1/Q2 全部配图本地生成（matplotlib 静态 PNG，不依赖网站）。
用法: python 生成全部图.py  → 输出到本目录 *.png
17 幅：Q1 9 幅 + Q2 8 幅（数据图 7 幅待实验后另出）。
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow, Polygon
from matplotlib.lines import Line2D

# ---- 中文字体 ----
for f in ['Microsoft YaHei', 'SimHei', 'SimSun']:
    try:
        matplotlib.rcParams['font.sans-serif'] = [f]
        break
    except Exception:
        pass
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['font.size'] = 10

OUT = os.path.dirname(os.path.abspath(__file__))
def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('saved', name)

def box(ax, x0, y0, x1, y1, fc, ec, lw=2, alpha=1.0, hatch=None):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=fc, edgecolor=ec, lw=lw, alpha=alpha, hatch=hatch))

def rect_center(x0, y0, x1, y1):
    return ((x0 + x1) / 2, (y0 + y1) / 2)

# ================= Q1 =================

def q1_fig1():
    fig, ax = plt.subplots(figsize=(8, 3.6))
    # 方案A：3×3 + 3×1 + 2×2 (面积9+3+4=16)，外框 6×3=18, R=2
    box(ax, 0, 0, 3, 3, '#BFDBFE', '#2563EB'); box(ax, 3, 0, 6, 1, '#BFDBFE', '#2563EB'); box(ax, 3, 1, 5, 3, '#BFDBFE', '#2563EB')
    # 方案B：3×3 + 2×3（放右），外框 5×... 用两个3x3? 简化为 4×4 面积16 R=1
    box(ax, 9, 0, 13, 4, '#BBF7D0', '#16A34A'); box(ax, 13, 0, 15, 4, '#BBF7D0', '#16A34A')
    ax.annotate('方案A：面积18，长宽比 R=2（高6宽3）', xy=(0, 3.6), fontsize=10, color='#1E3A8A')
    ax.annotate('方案B：面积16，长宽比 R=1（方）', xy=(9, 4.4), fontsize=10, color='#14532D')
    ax.set_xlim(-0.5, 16); ax.set_ylim(-0.5, 5.2); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('Q1-图1  同面积下不同长宽比（副目标：趋近1）')
    save(fig, 'Q1_01_同面积不同长宽比.png')

def q1_fig2():
    fig, ax = plt.subplots(figsize=(8, 3.6))
    # 压实前：有缝隙
    box(ax, 0, 0, 4, 2, '#BFDBFE', '#2563EB'); box(ax, 5, 0, 7, 3, '#BFDBFE', '#2563EB'); box(ax, 0, 3, 3, 4, '#BFDBFE', '#2563EB')
    ax.add_patch(FancyArrow(7.5, 1.5, 2.5, 0, width=0.06, color='#DC2626'))
    ax.annotate('压实\n(admissible)', xy=(8.2, 2.0), fontsize=9, color='#DC2626', ha='center')
    box(ax, 11, 0, 15, 2, '#BBF7D0', '#16A34A'); box(ax, 15, 2, 17, 5, '#BBF7D0', '#16A34A'); box(ax, 17, 0, 20, 1, '#BBF7D0', '#16A34A')
    ax.set_xlim(-0.5, 21); ax.set_ylim(-0.5, 5.8); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('Q1-图2  admissible 无损压缩：压实不增大外接框')
    save(fig, 'Q1_02_admissible压缩.png')

def q1_fig3():
    fig, ax = plt.subplots(figsize=(8, 3.8))
    box(ax, 0, 0, 3, 2, '#BFDBFE', '#2563EB'); ax.annotate('A(根)', (0.1, 0.1), fontsize=9)
    box(ax, 3, 0, 6, 2, '#BBF7D0', '#16A34A'); ax.annotate('B(A左)', (3.1, 0.1), fontsize=9)
    box(ax, 0, 2, 3, 4, '#E9D5FF', '#9333EA'); ax.annotate('C(A右)', (0.1, 2.1), fontsize=9)
    box(ax, 3, 2, 6, 4, '#FEF3C7', '#F59E0B'); ax.annotate('D(C右)', (3.1, 2.1), fontsize=9)
    ax.add_patch(FancyArrow(6.8, 1.8, 2.2, 0, width=0.06, color='#DC2626'))
    ax.annotate('一一对应', (7.8, 2.3), fontsize=9, color='#DC2626', ha='center')
    # 树：A 根，左 B，右 C，C 右 D
    tx = [10, 8.5, 11.5, 10, 13]; ty = [0.6, 2.2, 2.2, 3.8, 3.8]
    ax.plot([10, 8.5], [0.6, 2.2], color='#374151'); ax.plot([10, 11.5], [0.6, 2.2], color='#374151')
    ax.plot([11.5, 10], [2.2, 3.8], color='#374151'); ax.plot([11.5, 13], [2.2, 3.8], color='#374151', linestyle='--')
    for (x, y, lab, c) in zip(tx, ty, ['A', 'B', 'C', 'D'], ['#2563EB', '#16A34A', '#9333EA', '#F59E0B']):
        ax.scatter([x], [y], s=450, c=c, zorder=5); ax.annotate(lab, (x, y), color='white', ha='center', va='center', fontsize=11, fontweight='bold', zorder=6)
    ax.annotate('左=右邻块\n右=正上方块', (7.5, 4.4), fontsize=9, color='#374151', ha='center')
    ax.set_xlim(-0.5, 14); ax.set_ylim(-0.8, 5); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('Q1-图3  B*-Tree 与布局 一一对应')
    save(fig, 'Q1_03_BSTree对应.png')

def q1_fig4():
    fig = plt.figure(figsize=(7.5, 5.5))
    ax = fig.add_subplot(111, projection='3d')
    Ar = np.linspace(1, 1.5, 40); R = np.linspace(1, 3, 40)
    A, RR = np.meshgrid(Ar, R); Z = np.sqrt(A * RR)
    ax.plot_surface(A, RR, Z, cmap='Blues', alpha=0.85, edgecolor='none')
    ax.scatter([1], [1], [1], s=120, c='red', zorder=5)
    ax.set_xlabel('A/A_total'); ax.set_ylabel('R'); ax.set_zlabel('M=√(A·R)')
    ax.set_title('Q1-图4  min-max 目标曲面：最低点 = 面积近优 + 方形')
    ax.view_init(elev=22, azim=-60)
    save(fig, 'Q1_04_恒等式曲面.png')

def q1_fig5():
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    box(ax, 0, 0, 4, 4, '#BFDBFE', '#2563EB')
    box(ax, 6, 0, 10, 3.9, '#FECACA', '#DC2626')
    ax.annotate('X: W=100,H=100\nA=10000 M=100 R=1', (0, 4.5), fontsize=10)
    ax.annotate('Y: W=101,H=99\nA=9999 M=101 R≈1.02', (6, 4.5), fontsize=10)
    ax.annotate('题设取 Y（面积小）；无约束 min-max 取 X（长边小）→ 冲突！', (0.5, 5.8), fontsize=10, color='#B91C1C')
    ax.set_xlim(-0.5, 11); ax.set_ylim(-0.5, 6.5); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('Q1-图5  min-max 与词典序冲突反例（需加面积约束）')
    save(fig, 'Q1_05_minmax反例.png')

def q1_fig6():
    fig, ax = plt.subplots(figsize=(6.5, 4))
    r = np.linspace(1, 3, 200)
    ax.plot(r, np.sqrt(1.2 * r), color='#2563EB', lw=2, label='M=√(A_ratio·R)，固定 A_ratio=1.2')
    ax.scatter([1, 3], [np.sqrt(1.2), np.sqrt(3.6)], color='#DC2626', zorder=5)
    ax.annotate('R=1 时 M 最小', (1, np.sqrt(1.2)), textcoords='offset points', xytext=(10, 10))
    ax.set_xlabel('长宽比 R'); ax.set_ylabel('M = max(W,H)')
    ax.legend(); ax.grid(alpha=0.3)
    ax.set_title('Q1-图6  固定面积下 M 单调于 R（副目标激活）')
    save(fig, 'Q1_06_M随R单调.png')

def q1_fig7():
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    box(ax, 0, 0, 1, 5, '#FECACA', '#DC2626'); ax.annotate('高瘦 1×5\n(R=5)', (0.05, 0.5), fontsize=9)
    box(ax, 2, 0, 5, 2, '#FECACA', '#DC2626'); ax.annotate('矮宽 3×2\n(R=1.5)', (2.1, 0.5), fontsize=9)
    ax.add_patch(FancyArrow(5.8, 1.0, 2.0, 0, width=0.06, color='#16A34A'))
    ax.annotate('配对', (6.6, 1.6), fontsize=9, color='#16A34A')
    box(ax, 8, 0, 12, 5, '#BBF7D0', '#16A34A'); box(ax, 8, 0, 11, 2, '#BBF7D0', '#16A34A')
    ax.annotate('复合块 4×5\n(R=1.25)：总宽≈总高', (8.1, 0.5), fontsize=9, color='#14532D')
    ax.set_xlim(-0.5, 13); ax.set_ylim(-0.5, 6); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('Q1-图7  长条纵横比互补配对预处理（R:5→1.25）')
    save(fig, 'Q1_07_长条配对.png')

def q1_fig8():
    fig, ax = plt.subplots(figsize=(7, 4))
    # 行1 高3
    box(ax, 0, 0, 2, 3, '#BFDBFE', '#2563EB'); box(ax, 2, 0, 4, 3, '#BFDBFE', '#2563EB'); box(ax, 4, 0, 5.5, 3, '#BFDBFE', '#2563EB')
    ax.annotate('行1 (高3)', (0, 3.2), fontsize=9)
    box(ax, 0, 3, 2.5, 5, '#BBF7D0', '#16A34A'); box(ax, 2.5, 3, 5, 5, '#BBF7D0', '#16A34A')
    ax.annotate('行2 (高2)', (0, 5.2), fontsize=9)
    box(ax, 0, 5, 3, 6, '#E9D5FF', '#9333EA')
    ax.annotate('行3 (高1)', (0, 6.2), fontsize=9)
    ax.annotate('FFD：按高降序逐行堆叠，行高=行内最大高，总高=行高和', (0.2, 7.2), fontsize=10, color='#374151')
    ax.set_xlim(-0.5, 6.5); ax.set_ylim(-0.5, 7.8); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('Q1-图8  FFD 行堆叠构造初解')
    save(fig, 'Q1_08_FFD行堆叠.png')

def q1_fig9():
    fig, ax = plt.subplots(figsize=(8, 3.6))
    rows = [('n100', 0, [424, 443], '#2563EB'), ('n200', 0.08, [420, 440], '#16A34A'), ('n300', 0.16, [523, 538], '#9333EA')]
    xmin, xmax = 400, 560
    for lab, y, (lo, hi), c in rows:
        ax.plot([lo, hi], [y, y], color=c, lw=5, solid_capstyle='butt')
        ax.scatter([lo, hi], [y, y], color=c, zorder=5)
        ax.annotate(f'{lab}: [{lo},{hi}]', (lo, y + 0.02), fontsize=10, color=c)
    ax.axvspan(xmin, xmax, color='#F3F4F6', zorder=-1)
    ax.set_xlim(xmin, xmax); ax.set_ylim(-0.05, 0.26)
    ax.set_yticks([]); ax.grid(axis='x', alpha=0.3)
    ax.set_xlabel('方形边长')
    ax.set_title('Q1-图9  三组可行区间 [LB,UB]：结果落区间内=可信')
    save(fig, 'Q1_09_可行区间.png')

# ================= Q2 =================

def q2_fig1():
    fig, ax = plt.subplots(figsize=(9, 4.4))
    # 方案A：线长优但超轮廓
    box(ax, 0, 0, 8, 8, 'none', '#111827', lw=2)
    ax.scatter([0, 8, 8, 0], [4, 0, 8, 0], s=60, c='#DC2626', zorder=5)
    box(ax, 5, 5, 11, 10, '#FECACA', '#DC2626')
    ax.plot([8, 10], [10, 13], color='#DC2626', linestyle='--')
    ax.annotate('方案A：线长优，但块被拉向终端 → 超轮廓（非法）', (0, 8.4), fontsize=10, color='#B91C1C')
    # 方案B：可行但线长差
    box(ax, 14, 0, 22, 8, 'none', '#111827', lw=2)
    box(ax, 15, 1, 18, 4, '#BBF7D0', '#16A34A'); box(ax, 18, 4, 21, 7, '#BBF7D0', '#16A34A')
    ax.scatter([14, 22], [4, 0], s=60, c='#F59E0B', zorder=5)
    ax.plot([16.5, 14], [2.5, 4], color='#F59E0B', linestyle='--')
    ax.annotate('方案B：压回轮廓内（可行），但线网跨度大 → 线长差', (14, 8.4), fontsize=10, color='#14532D')
    ax.annotate('两者对冲 = 本问题核心张力', (4, -1.8), fontsize=11, color='#111827')
    ax.set_xlim(-1, 24); ax.set_ylim(-2.6, 12); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('Q2-图1  核心张力：线长优化 vs 轮廓约束对冲')
    save(fig, 'Q2_01_核心张力.png')

def q2_fig2():
    fig, ax = plt.subplots(figsize=(6.5, 6.2))
    S = 454
    ax.add_patch(Rectangle((0, 0), S, S, facecolor='none', edgecolor='#111827', lw=2))
    for i, n in [(0, 85), (1, 84), (2, 82), (3, 83)]:
        pass
    bx = np.linspace(0, 444, 10); by = np.linspace(0, 444, 9)
    ax.scatter(bx, np.zeros_like(bx), s=30, c='#2563EB', zorder=5)
    ax.scatter(bx, np.full_like(bx, 444), s=30, c='#2563EB', zorder=5)
    ax.scatter(np.zeros_like(by), by, s=30, c='#2563EB', zorder=5)
    ax.scatter(np.full_like(by, 444), by, s=30, c='#2563EB', zorder=5)
    ax.annotate('底边 85 个', (100, -12), fontsize=10, color='#2563EB')
    ax.annotate('顶边 84 个', (100, 456), fontsize=10, color='#2563EB')
    ax.annotate('左边 82 个', (-8, 200), fontsize=10, color='#2563EB', rotation=90)
    ax.annotate('右边 83 个', (450, 200), fontsize=10, color='#2563EB', rotation=90)
    ax.set_xlim(-35, 480); ax.set_ylim(-35, 480); ax.set_aspect('equal'); ax.set_xlabel('x'); ax.set_ylabel('y')
    ax.set_title('Q2-图2  终端四边均匀分布（n100 实测 85/84/82/83）')
    save(fig, 'Q2_02_终端分布.png')

def q2_fig3():
    fig, ax = plt.subplots(figsize=(6.5, 6))
    box(ax, 0, 0, 10, 10, 'none', '#111827', lw=2)
    ax.scatter([0], [5], s=90, c='#DC2626', zorder=6); ax.annotate('终端 t（边界锚点）', (0.3, 5.3), fontsize=9, color='#DC2626')
    box(ax, 3, 4, 5, 6, '#BFDBFE', '#2563EB'); box(ax, 6, 6, 8, 8, '#BFDBFE', '#2563EB'); box(ax, 5, 2, 7, 4, '#BFDBFE', '#2563EB')
    ax.plot([0, 3], [5, 5], color='#DC2626'); ax.plot([0, 7], [5, 7], color='#DC2626'); ax.plot([0, 6], [5, 3], color='#DC2626')
    ax.annotate('I/O 网：1 终端 + k 模块\n包围盒必含终端点', (0.5, 10.5), fontsize=10, color='#374151')
    ax.annotate('每条终端恰出现于一个线网 → 终端锚定', (0.5, 11.8), fontsize=10, color='#374151')
    ax.set_xlim(-0.5, 11); ax.set_ylim(-0.5, 12.8); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('Q2-图3  I/O 超网结构（1 终端 + k 模块）')
    save(fig, 'Q2_03_IO超网.png')

def q2_fig4():
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    pts = np.array([[2, 1], [5, 3], [4, 6], [7, 2]])
    ax.scatter(pts[:, 0], pts[:, 1], s=70, c='#111827', zorder=5)
    ax.add_patch(Rectangle((2, 1), 5, 5, facecolor='#FECACA', edgecolor='#DC2626', lw=2, alpha=0.5))
    ax.annotate('span_x = 7−2 = 5', (2.2, 0.1), fontsize=10, color='#2563EB')
    ax.annotate('span_y = 6−1 = 5', (-1.4, 2.0), fontsize=10, color='#16A34A', rotation=90)
    ax.annotate('', (2, -0.4), xytext=(7, -0.4), arrowprops=dict(arrowstyle='<->', color='#2563EB'))
    ax.annotate('', (-0.4, 1), xytext=(-0.4, 6), arrowprops=dict(arrowstyle='<->', color='#16A34A'))
    ax.annotate('HPWL = span_x + span_y = 10（包围盒半周长）', (1.5, 7.3), fontsize=10, color='#B91C1C')
    ax.set_xlim(-2.5, 8); ax.set_ylim(-1, 8.2); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('Q2-图4  HPWL = 两个正交投影之和')
    save(fig, 'Q2_04_HPWL投影.png')

def q2_fig5():
    fig, ax = plt.subplots(figsize=(6, 5.5))
    t = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(t), np.sin(t), color='#DC2626', linestyle='--', lw=1.5, label='L2 圆（欧氏）')
    th = np.linspace(0, 2 * np.pi, 400)
    r = 1.0 / (np.abs(np.cos(th)) + np.abs(np.sin(th)))
    ax.plot(r * np.cos(th), r * np.sin(th), color='#2563EB', lw=2, label='L1 菱形：|Δx|+|Δy|=1')
    ax.scatter([1, 0], [0, 1], s=50, c='#111827', zorder=5)
    ax.legend(loc='upper right'); ax.grid(alpha=0.3); ax.set_aspect('equal')
    ax.set_title('Q2-图5  2-pin 网 HPWL = L1 距离（菱形等值线）')
    save(fig, 'Q2_05_L1菱形.png')

def q2_fig6():
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    a = np.linspace(0.01, 3, 400)
    ax.plot(a, 1 / a, color='#2563EB', lw=2, label='可行边界 A·R = S²（双曲线）')
    ax.fill_between(a, 0, 1 / a, color='#DBEAFE', alpha=0.5)
    ax.scatter([1.02, 1.1, 1.2, 1.3], [0.9, 1.35, 1.05, 0.8], s=50, c='#16A34A', zorder=5, label='可行点 (A·R≤S²)')
    ax.scatter([1.1, 1.3, 1.05], [1.9, 1.7, 1.6], s=50, c='#DC2626', zorder=5, label='不可行点（越界）')
    ax.annotate('可行性区域\nA·R ≤ S²', (0.3, 0.5), fontsize=11, color='#1E3A8A')
    ax.set_xlim(0, 3); ax.set_ylim(0, 2.5); ax.set_xlabel('A/S²'); ax.set_ylabel('R')
    ax.legend(loc='upper right'); ax.grid(alpha=0.3)
    ax.set_title('Q2-图6  轮廓可行性判据 A·R ≤ S²')
    save(fig, 'Q2_06_可行性区域.png')

def q2_fig7():
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    t = np.linspace(0, 0.3, 200)
    ax.plot(t, 2 * t + t ** 2, color='#2563EB', lw=2, label='平滑软惩罚 (A·R−S²)/S² = 2t+t²')
    ax.plot(t, t, color='#DC2626', lw=2, linestyle='--', label='直接线性惩罚 t = M/S−1')
    ax.annotate('t=0 平滑激活：\n越界一点代价小', (0.05, 0.16), fontsize=9, color='#1E3A8A')
    ax.set_xlabel('越界量 t = M/S − 1'); ax.set_ylabel('惩罚代价')
    ax.legend(loc='upper left'); ax.grid(alpha=0.3)
    ax.set_title('Q2-图7  平滑软惩罚 vs 直接线性惩罚')
    save(fig, 'Q2_07_软惩罚对比.png')

def q2_fig8():
    fig, ax = plt.subplots(figsize=(6.5, 4))
    r = np.linspace(0, 1, 200)
    ax.plot(r, 1.1 - r, color='#2563EB', lw=2, label='λ(r) = λ_0·(1.1−r)')
    ax.scatter([0.2, 0.5, 0.8], [0.9, 0.6, 0.3], color='#16A34A', zorder=5)
    ax.annotate('可行率高 → λ↓ → 聚焦线长', (0.5, 0.75), fontsize=9, color='#14532D')
    ax.annotate('可行率低 → λ↑ → 压回轮廓', (0.05, 1.0), fontsize=9, color='#B91C1C')
    ax.set_xlabel('近期可行率 r = n_feasible/n'); ax.set_ylabel('惩罚权重 λ')
    ax.legend(); ax.grid(alpha=0.3)
    ax.set_title('Q2-图8  λ 自适应：随可行率开关式调节')
    save(fig, 'Q2_08_λ自适应.png')

if __name__ == '__main__':
    q1_fig1(); q1_fig2(); q1_fig3(); q1_fig4(); q1_fig5()
    q1_fig6(); q1_fig7(); q1_fig8(); q1_fig9()
    q2_fig1(); q2_fig2(); q2_fig3(); q2_fig4(); q2_fig5()
    q2_fig6(); q2_fig7(); q2_fig8()
    print('全部完成')
