# -*- coding: utf-8 -*-
"""m3_figs_lb.py — Q3 层B 图（真实 greedy_solve 数据）
图5 三组 Γ* 布局图 / 图6 死区-线长权衡曲线 / 图7 更新对比 / 图8 连续可行链
数据: 层B 轻量跑测（单 seed=42，n_iter=20000），正式值待编程手 M4 复现。
输出: 当前目录 q3_fig5/6/7/8_*.png + 数据 q3_lb_data.json
"""
import os
import sys
import json
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

sys.path.insert(0, r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\CLAUDE工作文件\编程手\Q2\编程手反馈\问题2独立实现")
from m2_data import load, Block
from m2_init import q1warm_tree
from m2_sa import greedy_solve, tree_to_posrot

OUT = os.path.dirname(os.path.abspath(__file__))
GAMMA = {'n100': 0.0933, 'n200': 0.0622, 'n300': 0.0400}
Q2_WL = {'n100': 220252, 'n200': 430628, 'n300': 672474}
N_ITER = 20000
SEED = 42


def load_data(name):
    d = load(name)
    blk = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(d['blocks'].items())]
    return d, blk


def run_lb(d, blk, S, n_iter=N_ITER, seed=SEED):
    """层B：q1warm 起点(target=S) + 贪心可行下降（改 data['side']=S 为可行性门）"""
    d2 = dict(d); d2['side'] = S
    tree, _ = q1warm_tree(d, blk, target=S)
    btree, wl, _ = greedy_solve(d2, blk, tree, seed=seed, n_iter=n_iter)
    pos, sizes, W, H = tree_to_posrot(btree, blk, d2)
    return pos, sizes, W, H, wl, d2


def fig5_layout(name, pos, sizes, S, wl, dead, fname):
    """Γ* 布局图：轮廓框 + 终端 + 模块 + 信息卡"""
    fig, ax = plt.subplots(figsize=(6.6, 6.6))
    ax.add_patch(Rectangle((0, 0), S, S, fill=False, edgecolor='#c0392b', lw=2.6))
    # 长条（AR≥2.5）暖橙，其余冷蓝
    for nm, (x, y) in pos.items():
        w, h = sizes[nm]
        ar = max(w, h) / max(min(w, h), 1e-9)
        c = '#e67e22' if ar >= 2.5 else '#4a7dbd'
        ax.add_patch(Rectangle((x, y), w, h, facecolor=c, edgecolor='#333', lw=0.5, alpha=0.85))
    # 终端红点
    d = load(name)
    for t, (x, y) in d['term_pos'].items():
        ax.plot(x, y, 'r.', ms=3.2, zorder=5)
    ax.set_xlim(-8, S + 8); ax.set_ylim(-8, S + 8)
    ax.set_aspect('equal'); ax.axis('off')
    ax.text(S / 2, -20, f'{name}  S*={S:.0f}  死区占比={dead:.1%}  HPWL={wl:,.0f}',
            ha='center', fontsize=11)
    ax.set_title(f'Q3-图5 {name}  Γ*={GAMMA[name]:.4f} 轮廓下布局', fontsize=12)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, fname), dpi=150); plt.close(fig)


def fig6_tradeoff(data_all, names):
    """权衡曲线：Γ 采样点 层B HPWL"""
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    trade = {}
    for name in names:
        d, blk = data_all[name]
        gammas = sorted(set([GAMMA[name], 0.05, 0.08, 0.11, 0.15]))
        gammas = [g for g in gammas if g >= GAMMA[name] - 1e-9]
        gs, wls = [], []
        for g in gammas:
            S = math.sqrt(d['area'] * (1 + g))
            _, _, _, _, wl, _ = run_lb(d, blk, S, n_iter=12000)
            gs.append(g); wls.append(wl)
            print(f'  [{name}] Γ={g:.4f} S={S:.1f} HPWL={wl:,.0f}')
        trade[name] = {'gs': gs, 'wls': wls}
        ax.plot(gs, wls, 'o-', lw=2, label=name)
        ax.annotate(f'Γ*={GAMMA[name]:.3f}\n{wls[0]:,.0f}', xy=(gs[0], wls[0]),
                    xytext=(gs[0] + 0.012, wls[0] * 0.97), fontsize=8.5)
    ax.set_xlabel('死区比例 Γ（题设口径）')
    ax.set_ylabel('总 HPWL')
    ax.set_title('Q3-图6 死区-线长权衡曲线：死区越紧线长越差', fontsize=12)
    ax.legend(fontsize=10); ax.grid(alpha=0.3)
    ax.invert_xaxis()  # Γ 大→小 从左到右展示压缩过程
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'q3_fig6_tradeoff.png'), dpi=150); plt.close(fig)
    return trade


def fig7_compare(lb_wl):
    names = ['n100', 'n200', 'n300']
    x = np.arange(3); w = 0.35
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.bar(x - w / 2, [Q2_WL[n] for n in names], w, color='#7f8c8d', label='问题二（Γ=0.15）')
    ax.bar(x + w / 2, [lb_wl[n] for n in names], w, color='#c0392b', label='Q3 更新（Γ*）')
    for i, n in enumerate(names):
        ax.text(i + w / 2, lb_wl[n] * 1.02, f'{lb_wl[n]:,.0f}', ha='center', fontsize=9, color='#c0392b')
    ax.set_xticks(x); ax.set_xticklabels(names)
    ax.set_ylabel('总 HPWL')
    ax.set_title('Q3-图7 更新对比：Γ* 轮廓下线长劣于 Γ=0.15（层B 轻量跑测）', fontsize=11)
    ax.legend(fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'q3_fig7_compare.png'), dpi=150); plt.close(fig)


def fig8_chain(data_all, names):
    """连续可行链：S 序列 q1warm 构造布局帧（快，无贪心）"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    for ax, name in zip(axes, names):
        d, blk = data_all[name]
        Sstar = math.sqrt(d['area'] * (1 + GAMMA[name]))
        S150 = math.sqrt(d['area'] * 1.15)
        Smid = (Sstar + S150) / 2
        for Si, (S, col, tag) in enumerate([(S150, '#2f6fd0', f'Γ=0.15  S={S150:.0f}'),
                                             (Smid, '#8e44ad', f'中间  S={Smid:.0f}'),
                                             (Sstar, '#c0392b', f'Γ*  S={Sstar:.0f}')]):
            tree, layout = q1warm_tree(d, blk, target=S)
            pos, sizes, W, H = tree_to_posrot(tree, blk, d)
            # 画在对应子轴，缩放位置
            ox, oy = Si * 0, Si * 0
            for nm, (x, y) in pos.items():
                w, h = sizes[nm]
                c = '#e67e22' if max(w, h) / min(w, h) >= 2.5 else '#4a7dbd'
                ax.add_patch(Rectangle((x + ox, y + oy), w, h, facecolor=c,
                                       edgecolor='#333', lw=0.4, alpha=0.7))
            ax.add_patch(Rectangle((ox, oy), S, S, fill=False, edgecolor=col, lw=2.2))
            ax.text(S / 2, S + 5, tag, ha='center', fontsize=9.5, color=col)
        ax.set_aspect('equal'); ax.axis('off')
        ax.set_title(name, fontsize=11)
    fig.suptitle('Q3-图8 连续可行链：从 Γ=0.15 可行解沿 Γ 下降，每步有可行起点', fontsize=12)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'q3_fig8_chain.png'), dpi=150); plt.close(fig)


def main():
    names = ['n100', 'n200', 'n300']
    data_all = {n: load_data(n) for n in names}
    lb_wl = {}
    # 图5 布局 + 图7 数据
    for name in names:
        d, blk = data_all[name]
        Sstar = math.sqrt(d['area'] * (1 + GAMMA[name]))
        pos, sizes, W, H, wl, _ = run_lb(d, blk, Sstar)
        dead = (Sstar * Sstar - d['area']) / (Sstar * Sstar)
        lb_wl[name] = wl
        print(f'[{name}] S*={Sstar:.2f} W={W:.0f} H={H:.0f} 死区={dead:.4f} HPWL={wl:,.0f}')
        fig5_layout(name, pos, sizes, Sstar, wl, dead, f'q3_fig5_layout_{name}.png')
    # 图6 权衡
    print('权衡曲线采样...')
    trade = fig6_tradeoff(data_all, names)
    # 图7 对比
    fig7_compare(lb_wl)
    # 图8 连续可行链
    fig8_chain(data_all, names)
    # 存数据
    with open(os.path.join(OUT, 'q3_lb_data.json'), 'w', encoding='utf-8') as f:
        json.dump({'lb_wl': lb_wl, 'trade': trade, 'gamma': GAMMA, 'q2_wl': Q2_WL},
                  f, ensure_ascii=False, indent=1)
    print('全部完成 →', OUT)


if __name__ == '__main__':
    main()
