# -*- coding: utf-8 -*-
"""m3_figs_static.py — Q3 静态图（无需层B数据）
图1 两层结构流程 / 图2 恒等式临界区域 / 图3 收缩可行性曲线 / 图4 三档锚
图9 构造器对比 / 图10 临界gap / 图11 长条主导 / 图12 完美矩形示意
输出: 当前目录 q3_figN_*.png
"""
import os
import sys
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

# 中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

sys.path.insert(0, r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\CLAUDE工作文件\编程手\Q2\编程手反馈\问题2独立实现")
from m2_data import load, Block
from m2_init import ffd_order_layout, skyline_order, orders

OUT = os.path.dirname(os.path.abspath(__file__))
Q1M = {'n100': 443, 'n200': 432, 'n300': 533}
GAMMA_CONSTR = {'n100': 0.0933, 'n200': 0.0622, 'n300': 0.0400}
DEAD_RATIO = {'n100': 0.0853, 'n200': 0.0586, 'n300': 0.0384}
SQRT_A = {'n100': 423.68, 'n200': 419.16, 'n300': 522.66}
LONGBARS = {'n100': 15, 'n200': 0, 'n300': None}  # n300 待算


def rot_blk(blk, mode='tall'):
    out = []
    for b in blk:
        if mode == 'tall' and max(b.w, b.h) / min(b.w, b.h) >= 2.5:
            out.append(Block(b.idx, b.name, max(b.w, b.h), min(b.w, b.h)))
        else:
            out.append(b)
    return out


def feas_s(S, strategy, blk, data):
    if strategy == 'skyline':
        order = sorted(range(len(blk)), key=lambda i: -blk[i].h)
        layout = skyline_order(blk, order, float(S))
    elif strategy == 'h_desc':
        order = sorted(range(len(blk)), key=lambda i: -blk[i].h)
        layout = ffd_order_layout(blk, order, float(S))
    else:
        order = orders(data, blk)[strategy]
        layout = ffd_order_layout(blk, order, float(S))
    W = max((x + blk[i].w for i, x, y in layout), default=0.0)
    H = max((y + blk[i].h for i, x, y in layout), default=0.0)
    return (W <= S + 1e-9 and H <= S + 1e-9), (W, H)


def sweep(data, blk, start, lo, strategies=('h_desc', 'skyline')):
    """每 S 判可行，返回 [(S, feas_bool)]"""
    res = []
    for S in range(start, lo - 1, -1):
        feas = any(feas_s(S, st, blk, data)[0] for st in strategies)
        res.append((S, feas))
    return res


# ---------- 图1：两层结构流程 ----------
def fig1():
    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.axis('off')
    ax.set_xlim(0, 10); ax.set_ylim(0, 3.2)
    boxes = [
        (0.3, 1.2, 2.2, 1.6, '题设\n最小死区比例?', '#fff7e6'),
        (3.6, 1.2, 2.6, 1.6, '层A 存在性判定\nΓ* = min{Γ: 存在可行布局}\n= 问题一方形对偶', '#e6f4ff'),
        (7.1, 1.2, 2.6, 1.6, '层B 优化更新\nS* 下复用问题二\nmin 总HPWL', '#f0f7e8'),
    ]
    for x, y, w, h, txt, fc in boxes:
        ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor='#333', lw=1.4))
        ax.text(x + w / 2, y + h / 2, txt, ha='center', va='center', fontsize=10)
    for x1, x2 in [(2.5, 3.55), (6.25, 7.05)]:
        ax.add_patch(FancyArrowPatch((x1, 2.0), (x2, 2.0), arrowstyle='-|>',
                                     mutation_scale=18, color='#c0392b', lw=1.6))
    ax.text(5.0, 2.35, '层序不可颠倒', ha='center', fontsize=9, color='#c0392b')
    ax.set_title('Q3-图1 两层结构：存在性判定 → 优化更新', fontsize=12)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'q3_fig1_two_layer.png'), dpi=150); plt.close(fig)


# ---------- 图2：恒等式临界区域 ----------
def fig2():
    fig, ax = plt.subplots(figsize=(7, 5))
    R = [i / 100 for i in range(100, 181)]  # 1.00 ~ 1.80
    for g, col, lab in [(0.15, '#2f6fd0', r'$\Gamma=0.15$'),
                        (GAMMA_CONSTR['n100'], '#c0392b', r'$\Gamma=\Gamma^*=0.0933$')]:
        ax.plot(R, [1 + g] * len(R), color=col, lw=2, label=lab)
    # 可行区阴影（Γ* 边界下方）
    ax.fill_between(R, 0, [1 + GAMMA_CONSTR['n100']] * len(R), color='#2f6fd0', alpha=0.08)
    # 最优长宽比点
    ax.axvline(1.093, color='#c0392b', ls='--', lw=1.2)
    ax.plot(1.093, 1.093, 'o', color='#c0392b', ms=7)
    ax.annotate(r'$R^*=1+\Gamma^*$', xy=(1.093, 1.093), xytext=(1.28, 1.16),
                arrowprops=dict(arrowstyle='->', color='#c0392b'), fontsize=10)
    ax.text(1.06, 0.35, '可行区\n$R \\leq 1+\\Gamma$', fontsize=10, color='#2f6fd0')
    ax.text(1.32, 1.38, '不可行区', fontsize=10, color='#c0392b')
    ax.set_xlabel(r'长宽比 $R = \max(W,H)/\min(W,H)$', fontsize=11)
    ax.set_ylabel(r'轮廓边界 $1+\Gamma$', fontsize=11)
    ax.set_ylim(0.9, 1.6)
    ax.legend(loc='upper left', fontsize=10)
    ax.set_title('Q3-图2 恒等式临界刻画：死区=长宽比盈余（n100）', fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'q3_fig2_critical.png'), dpi=150); plt.close(fig)


# ---------- 图3：收缩可行性曲线 ----------
def fig3():
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
    for ax, name in zip(axes, ['n100', 'n200', 'n300']):
        data = load(name)
        blk = rot_blk([Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())])
        res = sweep(data, blk, Q1M[name], int(math.ceil(SQRT_A[name])))
        Ss = [s for s, _ in res]
        feas = [f for _, f in res]
        gam = [s * s / data['area'] - 1 for s in Ss]
        ax.step(gam, feas, where='post', color='#2f6fd0', lw=2)
        ax.fill_between(gam, 0, feas, step='post', alpha=0.15, color='#2f6fd0')
        gstar = GAMMA_CONSTR[name]
        ax.axvline(gstar, color='#c0392b', ls='--', lw=1.4)
        ax.annotate(f'Γ*={gstar:.4f}', xy=(gstar, 0.5), xytext=(gstar + 0.012, 0.6),
                    arrowprops=dict(arrowstyle='->', color='#c0392b'), fontsize=9, color='#c0392b')
        ax.set_xlabel('Γ（题设口径）')
        ax.set_ylabel('可行（1/0）')
        ax.set_yticks([0, 1]); ax.set_yticklabels(['不可行', '可行'])
        ax.set_title(name, fontsize=11)
        ax.grid(alpha=0.3)
    fig.suptitle('Q3-图3 收缩可行性曲线：可行域对 Γ 单调，临界即答案', fontsize=12)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'q3_fig3_sweep.png'), dpi=150); plt.close(fig)


# ---------- 图4：三档锚 ----------
def fig4():
    names = ['n100', 'n200', 'n300']
    x = range(3)
    constr = [GAMMA_CONSTR[n] for n in names]
    ref = [0.0589, None, None]
    fig, ax = plt.subplots(figsize=(7, 4.4))
    b1 = ax.bar(x, constr, 0.5, color='#2f6fd0', label='构造可达 Γ*')
    for i, v in enumerate(constr):
        ax.text(i, v + 0.002, f'{v:.4f}', ha='center', fontsize=10)
    ax.hlines(0, -0.5, 2.5, color='#7f8c8d', lw=1.5)
    ax.text(2.55, 0, '面积下界 Γ≥0', fontsize=9, color='#7f8c8d', va='center')
    for i, v in enumerate(ref):
        if v:
            ax.plot(i + 0.25, v, 'rv', ms=10, label='参考趋势' if i == 0 else '')
            ax.annotate(f'参考\n{v:.4f}', xy=(i + 0.25, v), xytext=(i + 0.38, v - 0.012),
                        fontsize=8.5, color='#c0392b')
    ax.set_xticks(list(x)); ax.set_xticklabels(names)
    ax.set_ylabel('Γ*（题设口径）')
    ax.set_title('Q3-图4 三档锚：构造可达 / 面积下界 / 参考趋势', fontsize=11)
    ax.legend(loc='upper right', fontsize=9)
    ax.set_ylim(-0.005, 0.11)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'q3_fig4_three_tier.png'), dpi=150); plt.close(fig)


# ---------- 图9：构造器对比 ----------
def fig9():
    data = load('n100')
    blk = rot_blk([Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())])
    Ss = list(range(455, 420, -1))
    hd, sk = [], []
    for S in Ss:
        _, wh_h = feas_s(S, 'h_desc', blk, data)
        _, wh_s = feas_s(S, 'skyline', blk, data)
        hd.append(wh_h[1]); sk.append(wh_s[1])
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.plot(Ss, hd, 'o-', color='#2f6fd0', lw=2, label='h_desc 行堆叠')
    ax.plot(Ss, sk, 's--', color='#e67e22', lw=2, label='skyline（h 降序）')
    ax.plot(Ss, Ss, '-', color='#7f8c8d', lw=1, label='H=S（可行线）')
    ax.axvline(443, color='#c0392b', ls=':', lw=1.4)
    ax.annotate('Γ*（443）', xy=(443, 500), fontsize=9, color='#c0392b')
    ax.set_xlabel('轮廓边长 S'); ax.set_ylabel('打包高度 H')
    ax.set_title('Q3-图9 判可行构造器对比（n100）：双构造器无绝对赢家', fontsize=11)
    ax.legend(fontsize=9); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'q3_fig9_constructors.png'), dpi=150); plt.close(fig)


# ---------- 图10：临界 gap ----------
def fig10():
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
    strategies = ['h_desc', 'skyline', 'area_desc', 'pref_yx']
    for ax, name in zip(axes, ['n100', 'n200', 'n300']):
        data = load(name)
        blk = rot_blk([Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())])
        S = Q1M[name] - 1
        gaps = []
        for st in strategies:
            _, wh = feas_s(S, st, blk, data)
            gaps.append(max(wh) - S)
        ax.bar(range(len(strategies)), gaps, 0.55, color='#c0392b', alpha=0.8)
        ax.set_xticks(range(len(strategies))); ax.set_xticklabels(strategies, rotation=20, fontsize=8)
        ax.set_ylabel(f'超出 S={S} 的量'); ax.set_title(name, fontsize=11)
        ax.grid(axis='y', alpha=0.3)
    fig.suptitle('Q3-图10 临界 gap（S=Q1M−1）：n100/n200 仅超 1，n300 超 8-13', fontsize=12)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'q3_fig10_gap.png'), dpi=150); plt.close(fig)


# ---------- 图11：长条主导 ----------
def fig11():
    data = {}
    nb = {}
    for name in ['n100', 'n200', 'n300']:
        d = load(name)
        data[name] = d
        blk = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(d['blocks'].items())]
        nb[name] = sum(1 for b in blk if max(b.w, b.h) / min(b.w, b.h) >= 2.5)
    fig, ax = plt.subplots(figsize=(6.5, 4.4))
    names = ['n100', 'n200', 'n300']
    ax.scatter([nb[n] for n in names], [DEAD_RATIO[n] for n in names],
               s=160, color='#2f6fd0', zorder=3)
    for n in names:
        ax.annotate(n, xy=(nb[n], DEAD_RATIO[n]), xytext=(nb[n] + 1.2, DEAD_RATIO[n]),
                    fontsize=11)
    ax.set_xlabel('长条模块数（AR≥2.5）')
    ax.set_ylabel('死区占比')
    ax.set_title('Q3-图11 长条主导死区：长条越多死区越难压', fontsize=11)
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'q3_fig11_longbar.png'), dpi=150); plt.close(fig)


# ---------- 图12：完美矩形极限 ----------
def fig12():
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    # 完美平铺：4 块拼正方形
    sq = [(0, 0, 4, 4), (4, 0, 3, 3), (0, 4, 3, 3), (3, 3, 4, 4)]  # 实际不成方，示意
    # 用面积一致的方块拼 7x7
    tiles = [(0, 0, 4, 4), (4, 0, 3, 3), (0, 4, 3, 3), (4, 4, 3, 3), (3, 3, 1, 1)]
    colors = ['#2f6fd0', '#e67e22', '#27ae60', '#8e44ad', '#f5f5f5']
    for (x, y, w, h), c in zip(tiles, colors):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=c, edgecolor='#333', lw=1.5))
        ax.text(x + w / 2, y + h / 2, f'{w}x{h}', ha='center', va='center', fontsize=9, color='white' if c != '#f5f5f5' else '#333')
    ax.set_xlim(-0.6, 7.6); ax.set_ylim(-0.6, 7.6)
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('Q3-图12 死区→0 = 完美平铺（NP-complete）', fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'q3_fig12_tessellation.png'), dpi=150); plt.close(fig)


if __name__ == '__main__':
    print('生成 Q3 静态图...')
    fig1(); print('  fig1 ok')
    fig2(); print('  fig2 ok')
    fig3(); print('  fig3 ok')
    fig4(); print('  fig4 ok')
    fig9(); print('  fig9 ok')
    fig10(); print('  fig10 ok')
    fig11(); print('  fig11 ok')
    fig12(); print('  fig12 ok')
    print('全部完成 →', OUT)
