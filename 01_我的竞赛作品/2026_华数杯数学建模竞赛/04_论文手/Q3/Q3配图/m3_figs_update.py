# -*- coding: utf-8 -*-
"""m3_figs_update.py — 用修正层B 最终数据重画 图6 权衡曲线 / 图7 更新对比
数据源: 编程手/Q3/编程手反馈/输出/m4b_results.json
"""
import os, json, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

HERE = os.path.dirname(os.path.abspath(__file__))
JSON = os.path.join(HERE, '..', '..', '..', '编程手', 'Q3', '编程手反馈', '输出', 'm4b_results.json')
Q2_WL = {'n100': 220252, 'n200': 430628, 'n300': 672474}
GAMMA = {'n100': 0.0933, 'n200': 0.0622, 'n300': 0.0400}
names = ['n100', 'n200', 'n300']
cols = ['#2196F3', '#4CAF50', '#FF9800']
marks = ['o', 's', '^']

with open(JSON, encoding='utf-8') as f:
    res = json.load(f)


# ---- 图6 权衡曲线 ----
fig, ax = plt.subplots(figsize=(7.5, 5))
for name, c, m in zip(names, cols, marks):
    r = res[name]
    gs = [GAMMA[name]] + sorted(r['trade'].keys())
    wls = [r['wl_star']] + [r['trade'][str(g)] for g in sorted(r['trade'].keys())]
    gs_all = gs + [0.15]
    wl_all = wls + [r['wl_015']]
    ax.plot(gs_all, wl_all, '-', color=c, lw=1.8, alpha=0.6)
    ax.scatter(gs_all, wl_all, c=c, marker=m, s=55, zorder=5)
    ax.annotate(f'{r["wl_star"]:,.0f}', xy=(GAMMA[name], r['wl_star']),
                xytext=(GAMMA[name] + 0.012, r['wl_star'] * 1.01), fontsize=9, color=c)
    ax.annotate(f'{r["wl_015"]:,.0f}', xy=(0.15, r['wl_015']),
                xytext=(0.138, r['wl_015'] * 1.005), fontsize=9, color=c)
    # 中间点小标
    for g, wl in zip(gs[1:], wls[1:]):
        ax.plot(g, wl, '.', color=c, ms=6)
ax.set_xlabel('死区比例 Γ（题设口径）')
ax.set_ylabel('总 HPWL')
ax.set_title('Q3-图6 死区-线长权衡曲线：死区越紧线长越差（修正层B 最终数据）', fontsize=11)
ax.legend(names, fontsize=10)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(HERE, 'q3_fig6_tradeoff.png'), dpi=150)
plt.close(fig)
print('图6 更新 OK')


# ---- 图7 更新对比 ----
x = np.arange(3); w = 0.35
fig, ax = plt.subplots(figsize=(7, 4.4))
q2 = [Q2_WL[n] for n in names]
upd = [res[n]['wl_star'] for n in names]
deltas = [res[n]['delta_pct'] for n in names]
ax.bar(x - w / 2, q2, w, color='#7f8c8d', label='问题二（Γ=0.15 定稿）')
ax.bar(x + w / 2, upd, w, color='#c0392b', label='Q3 更新（Γ*）')
for i, n in enumerate(names):
    ax.text(i + w / 2, upd[i] * 1.02, f'{upd[i]:,.0f}\n({deltas[i]:+.1f}%)', ha='center', fontsize=9, color='#c0392b')
ax.set_xticks(x); ax.set_xticklabels(names)
ax.set_ylabel('总 HPWL')
ax.set_title('Q3-图7 更新对比：Γ* 轮廓下线长劣于 Γ=0.15（修正层B 最终数据）', fontsize=11)
ax.legend(fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(HERE, 'q3_fig7_compare.png'), dpi=150)
plt.close(fig)
print('图7 更新 OK')
print('全部更新完成')
