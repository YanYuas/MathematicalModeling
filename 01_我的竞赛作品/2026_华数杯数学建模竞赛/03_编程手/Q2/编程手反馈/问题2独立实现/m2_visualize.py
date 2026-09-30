# -*- coding: utf-8 -*-
"""m2_visualize.py — Q2 可视化：轮廓框 + 终端点 + 模块 + 信息卡（四要素）
design token 制度（同 Q1 PRD）。读 best_*.pkl 渲染。
"""
import os
import pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.gridspec import GridSpec
from m2_data import load, Block
from m2_sa import tree_to_posrot
from m2_hpwl import evaluate, terminal_vs_internal

OUT = os.path.dirname(os.path.abspath(__file__))
BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"

T = {
    'fill_normal': '#D6EAF8', 'edge_normal': '#2874A6',
    'fill_strip': '#FDEBD0', 'edge_strip': '#D35400',
    'outline': '#C0392B', 'terminal': '#C0392B', 'term_edge': '#922B21',
    'annot': '#2C3E50', 'grid': '#E8E8E8',
    'f_title': 16, 'f_axis': 12, 'f_tick': 10, 'f_ann': 9, 'f_card': 11,
    'l_outline': 3.0,
}
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


def render(name, seed=2, n_iter=20000):
    data = load(name)
    blk = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]
    pkl = os.path.join(OUT, f'best_{name}.pkl')
    if os.path.exists(pkl):
        with open(pkl, 'rb') as f:
            pk = pickle.load(f)
        tree = pk['tree']
    else:
        from m2_init import q1warm_tree
        from m2_sa import greedy_solve
        tree0, _ = q1warm_tree(data, blk)
        tree, _, _ = greedy_solve(data, blk, tree0, seed=seed, n_iter=n_iter)
        print(f'  [可视化] {name} 现场贪心 seed={seed} n_iter={n_iter}', flush=True)
    pos, sizes, W, H = tree_to_posrot(tree, blk, data)
    wl, _, _ = evaluate(data, pos, sizes=sizes)
    io_t, in_t = terminal_vs_internal(data, pos, sizes=sizes)
    S = data['side']
    ds = (W * H - data['area']) / (W * H) * 100

    # 长条块
    strip_idx = {b.idx for b in blk if max(b.w, b.h) / min(b.w, b.h) >= 2.5}
    fs = {200: 5, 100: 6, 300: 5}.get(len(blk), 5)

    fig = plt.figure(figsize=(11.5, 9.5))
    gs = GridSpec(1, 2, width_ratios=[5.5, 1.6], wspace=0.08)
    ax = fig.add_subplot(gs[0, 0])
    ax_info = fig.add_subplot(gs[0, 1])
    ax_info.axis('off')

    # 模块
    for idx, x, y, w, h in tree.get_layout():
        is_strip = idx in strip_idx
        face = T['fill_strip'] if is_strip else T['fill_normal']
        edge = T['edge_strip'] if is_strip else T['edge_normal']
        ax.add_patch(Rectangle((x, y), w, h, facecolor=face, edgecolor=edge,
                               linewidth=1.2 if is_strip else 0.8, alpha=0.92))
        if w >= 30 and h >= 25:
            ax.text(x + w / 2, y + h / 2, str(idx), ha='center', va='center',
                    fontsize=fs, color='#1A5276')
        else:
            ax.text(x + w / 2, y + h / 2, str(idx), ha='center', va='center',
                    fontsize=fs - 1, rotation=90, color='#1A5276')
    # 终端点（置顶，Z 序最高）
    for tname, (tx, ty) in data['term_pos'].items():
        ax.scatter([tx], [ty], marker='s', s=14, color=T['terminal'],
                   edgecolor=T['term_edge'], linewidth=0.4, zorder=6)
    # 轮廓框
    ax.add_patch(Rectangle((0, 0), S, S, fill=False, edgecolor=T['outline'],
                           linewidth=T['l_outline'], zorder=5))
    ax.set_xlim(-S * 0.08, S * 1.04)
    ax.set_ylim(-S * 0.08, S * 1.04)
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color('#BDC3C7')
    ax.set_title(f'{name} Q2 布局 · 总HPWL最小', fontsize=T['f_title'],
                 color=T['annot'], fontweight='bold')

    lines = [
        ('数据集', name),
        ('轮廓', f'{S:.1f} × {S:.1f}'),
        ('占用', f'{W:.0f} × {H:.0f}'),
        ('总HPWL', f'{wl:,.0f}'),
        ('I/O网', f'{io_t:,.0f}'),
        ('内部网', f'{in_t:,.0f}'),
        ('死区', f'{ds:.2f}%'),
        ('长条块', f'{len(strip_idx)}'),
    ]
    ax_info.text(0.02, 0.98, 'Q2 结果', transform=ax_info.transAxes, ha='left',
                 va='top', fontsize=T['f_card'] + 1, color=T['annot'], fontweight='bold')
    y = 0.90
    for k, v in lines:
        ax_info.text(0.02, y, f'{k}：{v}', transform=ax_info.transAxes, ha='left',
                     va='top', fontsize=T['f_card'], color=T['annot'])
        y -= 0.115
    ax_info.text(0.02, 0.22, '图例', transform=ax_info.transAxes, ha='left',
                 va='top', fontsize=T['f_card'] + 1, color=T['annot'], fontweight='bold')
    ax_info.add_patch(Rectangle((0.03, 0.16), 0.25, 0.02, facecolor=T['fill_normal'],
                                edgecolor=T['edge_normal'], transform=ax_info.transAxes))
    ax_info.text(0.33, 0.16, '普通块', transform=ax_info.transAxes, fontsize=T['f_ann'],
                 color=T['annot'], va='center')
    ax_info.add_patch(Rectangle((0.03, 0.125), 0.25, 0.02, facecolor=T['fill_strip'],
                                edgecolor=T['edge_strip'], transform=ax_info.transAxes))
    ax_info.text(0.33, 0.125, '长条块 AR≥2.5', transform=ax_info.transAxes,
                 fontsize=T['f_ann'], color=T['annot'], va='center')
    ax_info.scatter([0.15], [0.075], marker='s', s=30, color=T['terminal'],
                    edgecolor=T['term_edge'], transform=ax_info.transAxes, zorder=6)
    ax_info.text(0.33, 0.075, '终端点', transform=ax_info.transAxes, fontsize=T['f_ann'],
                 color=T['annot'], va='center')

    p = os.path.join(OUT, f'q2_layout_{name}.png')
    fig.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  [q2_layout_{name}] HPWL={wl:,.0f} {W:.0f}x{H:.0f} → {os.path.basename(p)}')


if __name__ == '__main__':
    import sys
    names = sys.argv[1:] if len(sys.argv) > 1 else ['n100', 'n200', 'n300']
    print('=== Q2 可视化（四要素）===')
    for n in names:
        render(n)
    print('完成')
