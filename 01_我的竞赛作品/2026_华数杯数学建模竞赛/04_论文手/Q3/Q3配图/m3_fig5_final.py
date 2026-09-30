# -*- coding: utf-8 -*-
"""m3_fig5_final.py — Q3 图5 单图重渲染（定稿值 233,578/472,286/761,907）
读 m3_merge_layout 的缓存布局（m4b 定稿配置多 seed best），覆盖旧 m3_figs_lb 单图。
输出: 当前目录 q3_fig5_layout_n100/n200/n300.png（信息卡数字=定稿）
"""
import os
import sys
import pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

OUT = os.path.dirname(os.path.abspath(__file__))
CACHE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\CLAUDE工作文件\编程手\Q3\编程手反馈\Q3编程手优化包\_q3_merge_cache.pkl"

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

GAMMA = {'n100': 0.0933, 'n200': 0.0622, 'n300': 0.0400}
DELTA = {'n100': +4.5, 'n200': +6.8, 'n300': +11.1}  # 定稿口径（vs 层B 复现值）

with open(CACHE, 'rb') as f:
    DATA = pickle.load(f)

for n in ['n100', 'n200', 'n300']:
    d = DATA[n]
    fig, ax = plt.subplots(figsize=(6.6, 6.6))
    ax.add_patch(Rectangle((0, 0), d['S'], d['S'], fill=False, edgecolor='#C0392B', lw=2.6))
    for nm, (x, y) in d['pos'].items():
        w, h = d['sizes'][nm]
        ar = max(w, h) / max(min(w, h), 1e-9)
        c = '#E67E22' if ar >= 2.5 else '#4A7DBD'
        ax.add_patch(Rectangle((x, y), w, h, facecolor=c, edgecolor='#333', lw=0.5, alpha=0.85))
    for tx, ty in d['term_pos'].values():
        ax.plot(tx, ty, 'r.', ms=3.2, zorder=5)
    ax.set_xlim(-8, d['S'] + 8)
    ax.set_ylim(-8, d['S'] + 8)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.text(d['S']/2, -20, f'{n}  S*={d["S"]:.0f}  死区占比={d["dead"]*100:.1f}%  HPWL={d["wl"]:,.0f}（+{DELTA[n]:.1f}%）',
            ha='center', fontsize=11)
    ax.set_title(f'Q3-图5 {n}  Γ*={GAMMA[n]:.4f} 轮廓下布局', fontsize=12)
    fig.tight_layout()
    p = os.path.join(OUT, f'q3_fig5_layout_{n}.png')
    fig.savefig(p, dpi=150, facecolor='white')
    plt.close(fig)
    print(f'[{n}] HPWL={d["wl"]:,.0f} 定稿 → {os.path.basename(p)}')
print('图5 单图全部更新为定稿值')
