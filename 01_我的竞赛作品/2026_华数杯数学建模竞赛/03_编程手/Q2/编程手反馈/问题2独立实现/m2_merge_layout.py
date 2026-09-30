# -*- coding: utf-8 -*-
"""m2_merge_layout.py — Q2 三组布局横向合并（同 Q1 合并标准）
布局数据：best_*.pkl（n100/n200 有）；n300 无 pkl → 现场贪心 seed=2 n_iter=20000（与现图同源）
结构：3 面板单行 + 面板下居中信息卡（圆角白卡+主题色描边）+ 图例 + 底部统一注脚
"""
import os
import time
import pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.gridspec import GridSpec

from m2_data import load, Block
from m2_init import q1warm_tree
from m2_sa import tree_to_posrot, greedy_solve
from m2_hpwl import evaluate, terminal_vs_internal

OUT = os.path.dirname(os.path.abspath(__file__))

T = {
    'fill_normal': '#D6EAF8', 'edge_normal': '#2874A6',
    'fill_strip': '#FDEBD0', 'edge_strip': '#D35400',
    'outline': '#C0392B', 'terminal': '#C0392B', 'term_edge': '#922B21',
    'f_ann': 9,
}
ACCENT = {'n100': '#2874A6', 'n200': '#1E8449', 'n300': '#D35400'}
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


def get_tree(data, blk, name):
    """优先读 best pkl；n300 无 best pkl 则现场贪心并缓存（与 m2_visualize 同回退逻辑）。"""
    pkl = os.path.join(OUT, f'best_{name}.pkl')
    if os.path.exists(pkl):
        with open(pkl, 'rb') as f:
            return pickle.load(f)['tree'], 'pkl'
    cache = os.path.join(OUT, f'_greedy_{name}.pkl')
    if os.path.exists(cache):
        with open(cache, 'rb') as f:
            return pickle.load(f), 'greedy(cache)'
    tree0, _ = q1warm_tree(data, blk)
    t0 = time.time()
    tree, wl, _ = greedy_solve(data, blk, tree0, seed=2, n_iter=20000)
    print(f'  [{name}] 现场贪心 seed=2 20k 用时 {time.time()-t0:.0f}s wl={wl:,.0f}')
    with open(cache, 'wb') as f:
        pickle.dump(tree, f)
    return tree, 'greedy'


DATA = {}
for n in ['n100', 'n200', 'n300']:
    data = load(n)
    blk = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]
    tree, src = get_tree(data, blk, n)
    pos, sizes, W, H = tree_to_posrot(tree, blk, data)
    wl, _, _ = evaluate(data, pos, sizes=sizes)
    io_t, in_t = terminal_vs_internal(data, pos, sizes=sizes)
    S = data['side']
    ds = (W * H - data['area']) / (W * H) * 100
    strip_idx = {b.idx for b in blk if max(b.w, b.h) / min(b.w, b.h) >= 2.5}
    DATA[n] = dict(tree=tree, blk=blk, pos=pos, sizes=sizes, W=W, H=H, S=S,
                   wl=wl, io=io_t, internal=in_t, ds=ds, strip_idx=strip_idx,
                   src=src, n_strip=len(strip_idx), area=data['area'],
                   term_pos=data['term_pos'])

order = ['n100', 'n200', 'n300']

fig = plt.figure(figsize=(18.5, 8.0), facecolor='white')
gs = GridSpec(1, 3, width_ratios=[DATA[n]['S'] for n in order], wspace=0.035,
              left=0.015, right=0.995, top=0.93, bottom=0.21)
axs = {}

for ci, n in enumerate(order):
    d = DATA[n]
    ax = fig.add_subplot(gs[0, ci])
    axs[n] = ax
    fs = {200: 5, 100: 6, 300: 5}[len(d['blk'])]
    # 模块
    for idx, x, y, w, h in d['tree'].get_layout():
        is_strip = idx in d['strip_idx']
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
    # 终端点（置顶）
    for tx, ty in d['term_pos'].values():
        ax.scatter([tx], [ty], marker='s', s=12, color=T['terminal'],
                   edgecolor=T['term_edge'], linewidth=0.4, zorder=6)
    # 轮廓框
    ax.add_patch(Rectangle((0, 0), d['S'], d['S'], fill=False, edgecolor=T['outline'],
                           linewidth=2.8, zorder=5))
    ax.set_xlim(-d['S'] * 0.08, d['S'] * 1.04)
    ax.set_ylim(-d['S'] * 0.08, d['S'] * 1.04)
    ax.set_aspect('equal')
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color('#BDC3C7')
    ax.set_title(f'{n} · 总HPWL {d["wl"]:,.0f}', fontsize=15, color=ACCENT[n],
                 fontweight='bold')

# 面板下居中信息卡（两行，避免超面板宽互相重叠）
for n in order:
    d = DATA[n]
    pos_ax = axs[n].get_position()
    xc = (pos_ax.x0 + pos_ax.x1) / 2
    cap = (f'占用 {d["W"]:.0f}×{d["H"]:.0f} ｜ 死区 {d["ds"]:.2f}% ｜ 长条 {d["n_strip"]}\n'
           f'I/O网 {d["io"]:,.0f} ｜ 内部网 {d["internal"]:,.0f}')
    fig.text(xc, 0.158, cap, ha='center', va='center', fontsize=11.5, color='#2C3E50',
             bbox=dict(boxstyle='round,pad=0.5', fc='white', ec=ACCENT[n], lw=1.4))

# 底部统一注脚
d100, d200, d300 = DATA['n100'], DATA['n200'], DATA['n300']
foot = (f'注：三组总HPWL {d100["wl"]:,.0f} / {d200["wl"]:,.0f} / {d300["wl"]:,.0f}，占用 '
        f'{d100["W"]:.0f}×{d100["H"]:.0f} / {d200["W"]:.0f}×{d200["H"]:.0f} / {d300["W"]:.0f}×{d300["H"]:.0f}，'
        f'轮廓边长 {d100["S"]:.1f} / {d200["S"]:.1f} / {d300["S"]:.1f}；可行性由 Q1 方形解 warm start 保证，'
        f'搜索为贪心可行下降 + best-of-N。')
fig.text(0.5, 0.028, foot, ha='center', va='center', fontsize=10.5, color='#5D6D7E')

# 图例（左下角）
lx = 0.02
for label, fc, ec in [('普通块', T['fill_normal'], T['edge_normal']),
                      ('长条块 AR≥2.5', T['fill_strip'], T['edge_strip']),
                      ('外框=轮廓', 'white', T['outline'])]:
    fig.add_artist(Rectangle((lx, 0.095), 0.012, 0.014, facecolor=fc, edgecolor=ec,
                             linewidth=1.2, transform=fig.transFigure, clip_on=False))
    fig.text(lx + 0.0145, 0.102, label, fontsize=9, color='#2C3E50', va='center')
    lx += 0.013 + (0.105 if '外框' in label else 0.10)
fig.add_artist(Rectangle((lx + 0.005, 0.097), 0.010, 0.010, facecolor=T['terminal'],
                         edgecolor=T['term_edge'], transform=fig.transFigure, clip_on=False))
fig.text(lx + 0.022, 0.102, '终端点', fontsize=9, color='#2C3E50', va='center')

p = os.path.join(OUT, 'q2_layout_merged.png')
fig.savefig(p, dpi=150, facecolor='white')
print(f'merged → {os.path.basename(p)}')
for n in order:
    d = DATA[n]
    print(f'  {n}: wl={d["wl"]:,.0f} {d["W"]:.0f}×{d["H"]:.0f} 死区={d["ds"]:.2f}% '
          f'I/O={d["io"]:,.0f} 内部={d["internal"]:,.0f} 源={d["src"]}')
