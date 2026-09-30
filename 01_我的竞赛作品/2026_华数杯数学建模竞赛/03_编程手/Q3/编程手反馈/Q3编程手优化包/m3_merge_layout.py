# -*- coding: utf-8 -*-
"""m3_merge_layout.py — Q3 三组 Γ* 布局横向合并（同 Q1/Q2 合并标准）
布局数据：复用 m3_figs_lb.run_lb（q1warm(target=Γ* S) + 贪心可行下降 seed=42 20k，确定性复现定稿）
结构：3 面板单行 + 面板下居中信息卡（圆角+主题色描边）+ 图例 + 底部统一注脚
"""
import os
import sys
import math
import time
import json
import pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.gridspec import GridSpec

OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OUT)
sys.path.insert(0, r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\CLAUDE工作文件\编程手\Q2\编程手反馈\问题2独立实现")
import m4b_layer_b_fixed as M4B
from m2_data import Block
from m2_sa import tree_to_posrot

ACCENT = {'n100': '#2874A6', 'n200': '#1E8449', 'n300': '#D35400'}
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

GAMMA = M4B.GAMMA
Q2_REF = M4B.Q2_REF
CONF = M4B.CONF
Q1M = M4B.Q1M
# 定稿增量口径：同引擎复现（vs 层B Γ=0.15），取自 m4b_results.json
M4B_RES = json.load(open(os.path.join(OUT, '..', '输出', 'm4b_results.json'), encoding='utf-8'))

order = ['n100', 'n200', 'n300']
CACHE = os.path.join(OUT, '_q3_merge_cache.pkl')
DATA = {}
if os.path.exists(CACHE):
    with open(CACHE, 'rb') as f:
        DATA = pickle.load(f)
    print('使用缓存布局', flush=True)
else:
    for n in order:
        data = M4B.load(n)
        blk = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]
        n_iter, n_seed = CONF[n]
        seeds = [42 + i * 111 for i in range(n_seed)]
        S = Q1M[n]
        t0 = time.time()
        wl, tree, wh = M4B.best_of_n(data, blk, S, n_iter, seeds)
        d2 = dict(data); d2['side'] = S
        pos, sizes, W, H = tree_to_posrot(tree, blk, d2)
        dead = (S * S - data['area']) / (S * S)
        n_strip = sum(1 for b in blk if max(b.w, b.h) / min(b.w, b.h) >= 2.5)
        DATA[n] = dict(pos=pos, sizes=sizes, S=S, W=W, H=H, wl=wl, dead=dead,
                       n_strip=n_strip, term_pos=data['term_pos'])
        print(f'[{n}] S*={S} WxH={W:.0f}x{H:.0f} 死区={dead:.4f} HPWL={wl:,.0f} 用时={time.time()-t0:.0f}s', flush=True)
    with open(CACHE, 'wb') as f:
        pickle.dump(DATA, f)
for n in order:
    DATA[n]['delta'] = M4B_RES[n]['delta_pct']  # 定稿口径 +4.5/+6.8/+11.1
fig = plt.figure(figsize=(18.5, 8.0), facecolor='white')
gs = GridSpec(1, 3, width_ratios=[DATA[n]['S'] for n in order], wspace=0.035,
              left=0.015, right=0.995, top=0.93, bottom=0.21)
axs = {}

for ci, n in enumerate(order):
    d = DATA[n]
    ax = fig.add_subplot(gs[0, ci])
    axs[n] = ax
    # 轮廓框
    ax.add_patch(Rectangle((0, 0), d['S'], d['S'], fill=False, edgecolor='#C0392B', lw=2.8))
    # 模块
    for nm, (x, y) in d['pos'].items():
        w, h = d['sizes'][nm]
        ar = max(w, h) / max(min(w, h), 1e-9)
        c = '#E67E22' if ar >= 2.5 else '#4A7DBD'
        ax.add_patch(Rectangle((x, y), w, h, facecolor=c, edgecolor='#333', lw=0.5, alpha=0.85))
    # 终端点
    for tx, ty in d['term_pos'].values():
        ax.plot(tx, ty, 'r.', ms=3.0, zorder=5)
    ax.set_xlim(-8, d['S'] + 8)
    ax.set_ylim(-8, d['S'] + 8)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f'{n}  Γ*={GAMMA[n]:.4f} 轮廓下布局', fontsize=15, color=ACCENT[n],
                 fontweight='bold')

# 面板下居中信息卡（两行）
for n in order:
    d = DATA[n]
    pos_ax = axs[n].get_position()
    xc = (pos_ax.x0 + pos_ax.x1) / 2
    cap = (f'S* {d["S"]:.0f} ｜ 死区 {d["dead"]*100:.2f}% ｜ 长条 {d["n_strip"]}\n'
           f'HPWL {d["wl"]:,.0f}（相对Q2 {d["delta"]:+.1f}%）')
    fig.text(xc, 0.155, cap, ha='center', va='center', fontsize=11.5, color='#2C3E50',
             bbox=dict(boxstyle='round,pad=0.5', fc='white', ec=ACCENT[n], lw=1.4))

# 底部统一注脚
d1, d2_, d3 = DATA['n100'], DATA['n200'], DATA['n300']
foot = (f'注：三组临界死区 Γ* = 0.0933 / 0.0622 / 0.0400（轮廓边长 {d1["S"]:.0f} / {d2_["S"]:.0f} / {d3["S"]:.0f}），'
        f'总 HPWL {d1["wl"]:,.0f} / {d2_["wl"]:,.0f} / {d3["wl"]:,.0f}，'
        f'相对问题二 +{d1["delta"]:.1f}% / +{d2_["delta"]:.1f}% / +{d3["delta"]:.1f}%（死区收紧的线长代价）；'
        f'构造：q1warm 起点 + 贪心可行下降。')
fig.text(0.5, 0.028, foot, ha='center', va='center', fontsize=10.5, color='#5D6D7E')

# 图例
lx = 0.02
for label, fc, ec in [('普通块', '#4A7DBD', '#333'),
                      ('长条块 AR≥2.5', '#E67E22', '#333'),
                      ('轮廓框', 'white', '#C0392B')]:
    fig.add_artist(Rectangle((lx, 0.095), 0.012, 0.014, facecolor=fc, edgecolor=ec,
                             linewidth=1.2, transform=fig.transFigure, clip_on=False))
    fig.text(lx + 0.0145, 0.102, label, fontsize=9, color='#2C3E50', va='center')
    lx += 0.013 + (0.105 if '轮廓' in label else 0.10)
fig.add_artist(Rectangle((lx + 0.005, 0.096), 0.010, 0.010, facecolor='#C0392B',
                         transform=fig.transFigure, clip_on=False))
fig.text(lx + 0.022, 0.102, '终端点', fontsize=9, color='#2C3E50', va='center')

p = os.path.join(OUT, 'q3_fig5_layout_merged.png')
fig.savefig(p, dpi=150, facecolor='white')
print(f'merged → {os.path.basename(p)}')
