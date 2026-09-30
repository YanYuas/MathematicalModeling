# -*- coding: utf-8 -*-
"""m5_deliver.py — M5 交付：三组布图 + 收缩曲线 + 权衡曲线 + 结果表
依赖 m4_results.json (层B输出) + m3_scan 可行性扫描结果
"""
import os, sys, math, json
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path: sys.path.insert(0, _here)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.ticker as ticker
import numpy as np

from m2_data import load, Block
from m2_init import ffd_order_layout
from m_construct import layout_to_btree
from m2_hpwl import evaluate, terminal_vs_internal

# 中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = os.path.join(_here, '..', '输出')
os.makedirs(OUT_DIR, exist_ok=True)

Q1M = {'n100': 443, 'n200': 432, 'n300': 533}
Q2_REF = {'n100': 220252, 'n200': 430628, 'n300': 672474}


def rot_tall(blk_in):
    out = []
    for b in blk_in:
        if max(b.w, b.h) / min(b.w, b.h) >= 2.5:
            out.append(Block(b.idx, b.name, max(b.w, b.h), min(b.w, b.h)))
        else:
            out.append(b)
    return out


def load_m4_results():
    """加载 M4 结果，并重新映射 key 从 'n100_0.15' 到 'n100': {hpwl_015, hpwl_star, ...}"""
    rpath = os.path.join(_here, 'm4_results.json')
    if not os.path.exists(rpath):
        return None
    with open(rpath, 'r') as f:
        raw = json.load(f)
    # raw keys: n100_0.15, n100_star, n200_0.15, n200_star, n300_0.15, n300_star
    mapped = {}
    for key, val in raw.items():
        name, label = key.rsplit('_', 1)
        if name not in mapped:
            mapped[name] = {}
        if label == '0.15':
            mapped[name]['hpwl_015'] = val['wl']
            mapped[name]['M_015'] = val['M']
            mapped[name]['S_015'] = val['S']
        else:
            mapped[name]['hpwl_star'] = val['wl']
            mapped[name]['M_star'] = val['M']
            mapped[name]['S_star'] = val['S']
    # fill gamma_star
    for name in mapped:
        mapped[name]['gamma_star'] = (mapped[name]['S_star']**2 - load(name)['area']) / load(name)['area']
    return mapped


# ── 1. 三组 Γ* 布局图 ──
def plot_layout(name, S_star, gamma_star, dead_ratio, out_path=None):
    """绘制 Γ* 下的最终布局：轮廓 + 模块 + 终端"""
    data = load(name)
    blk0 = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]
    blk = rot_tall(blk0)

    # FFD h_desc 构造布局（Q3 构造解）
    order = sorted(range(len(blk)), key=lambda i: -blk[i].h)
    layout = ffd_order_layout(blk, order, float(S_star))

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(-5, S_star + 5)
    ax.set_ylim(-5, S_star + 5)
    ax.set_aspect('equal')

    # 轮廓
    ax.add_patch(patches.Rectangle((0, 0), S_star, S_star, fill=False,
                                    edgecolor='black', linewidth=2, linestyle='-'))

    # 模块
    colors = plt.cm.tab20(np.linspace(0, 1, len(blk)))
    for j, (idx, x, y) in enumerate(layout):
        b = blk[idx]
        rect = patches.Rectangle((x, y), b.w, b.h, fill=True, facecolor=colors[j % 20],
                                  edgecolor='black', linewidth=0.3, alpha=0.7)
        ax.add_patch(rect)
        # 小模块标号
        if b.w * b.h > 200:
            ax.text(x + b.w/2, y + b.h/2, b.name, ha='center', va='center',
                    fontsize=5, clip_on=True)

    # 终端
    t_xs = [p[0] for p in data['term_pos'].values()]
    t_ys = [p[1] for p in data['term_pos'].values()]
    ax.scatter(t_xs, t_ys, c='red', s=8, marker='s', zorder=10, alpha=0.8,
               label=f'Terminals ({len(t_xs)})')

    ax.set_title(f'{name}: S*={S_star}, Gamma*={gamma_star:.4f}, Dead={dead_ratio:.2%}',
                 fontsize=14)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.legend(loc='upper right', fontsize=9)

    if out_path is None:
        out_path = os.path.join(OUT_DIR, f'{name}_gamma_star_layout.png')
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  layout: {out_path}')
    return out_path


# ── 2. 可行性收缩曲线 ──
def plot_feasibility_curve(out_path=None):
    """Γ vs 可行/不可行，标 Γ* 临界点。从 m3_scan 数据重建。"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for ax_idx, name in enumerate(['n100', 'n200', 'n300']):
        ax = axes[ax_idx]
        data = load(name)
        blk0 = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]
        blk = rot_tall(blk0)

        lo = int(math.ceil(math.sqrt(data['area'])))
        hi = Q1M[name]

        feasible_s = []
        infeasible_s = []
        for S in range(lo, hi + 1):
            order = sorted(range(len(blk)), key=lambda i: -blk[i].h)
            layout = ffd_order_layout(blk, order, float(S))
            W = max((x + blk[i].w for i, x, y in layout), default=0.0)
            H = max((y + blk[i].h for i, x, y in layout), default=0.0)
            if W <= S + 1e-9 and H <= S + 1e-9:
                feasible_s.append(S)
            else:
                infeasible_s.append(S)

        gamma_feas = [(s**2/data['area'] - 1) for s in feasible_s]
        gamma_infeas = [(s**2/data['area'] - 1) for s in infeasible_s]

        ax.scatter(gamma_feas, [1]*len(gamma_feas), c='green', s=30, marker='o', label='Feasible')
        ax.scatter(gamma_infeas, [0]*len(gamma_infeas), c='red', s=30, marker='x', label='Infeasible')

        gamma_star = (Q1M[name]**2 - data['area']) / data['area']
        ax.axvline(x=gamma_star, color='blue', linestyle='--', linewidth=1.5,
                    label=f'Gamma*={gamma_star:.4f}')

        ax.set_xlabel('Gamma')
        ax.set_ylabel('Feasible (1=Yes, 0=No)')
        ax.set_title(f'{name}')
        ax.set_ylim(-0.2, 1.5)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    fig.suptitle('Feasibility vs Gamma (Gamma* = minimum feasible dead space ratio)', fontsize=14)
    plt.tight_layout()

    if out_path is None:
        out_path = os.path.join(OUT_DIR, 'feasibility_curve.png')
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  feasibility: {out_path}')
    return out_path


# ── 3. 权衡曲线 (需要 M4 结果) ──
def plot_tradeoff_curve(m4, out_path=None):
    """HPWL vs Gamma 权衡：标出 Γ* 和 Γ=0.15 两点"""
    if m4 is None:
        print('  tradeoff: SKIP (no M4 results)')
        return None

    fig, ax = plt.subplots(figsize=(8, 6))
    names = ['n100', 'n200', 'n300']
    colors = ['#2196F3', '#4CAF50', '#FF9800']
    markers = ['o', 's', '^']

    for name, c, m in zip(names, colors, markers):
        r = m4[name]
        g_star = r['gamma_star']
        g_015 = 0.15
        wl_star = r['hpwl_star']
        wl_015 = r['hpwl_015']

        ax.plot([g_star, g_015], [wl_star, wl_015], '-', color=c, linewidth=2, alpha=0.5)
        ax.scatter([g_star], [wl_star], c=c, marker=m, s=120, zorder=5,
                    label=f'{name} (Gamma*={g_star:.4f})')
        ax.scatter([g_015], [wl_015], c=c, marker=m, s=80, zorder=5,
                    facecolors='none', linewidths=1.5)
        ax.annotate(f'{wl_star:,.0f}', (g_star, wl_star), textcoords="offset points",
                     xytext=(10, -10), fontsize=9, color=c)
        ax.annotate(f'{wl_015:,.0f}', (g_015, wl_015), textcoords="offset points",
                     xytext=(10, 5), fontsize=9, color=c)

    ax.set_xlabel('Gamma (Dead Space Ratio)', fontsize=12)
    ax.set_ylabel('HPWL', fontsize=12)
    ax.set_title('HPWL vs Dead Space Ratio Trade-off', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))

    if out_path is None:
        out_path = os.path.join(OUT_DIR, 'tradeoff_curve.png')
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  tradeoff: {out_path}')
    return out_path


# ── 4. 结果表 ──
def print_result_table(m4=None):
    """打印 Q3 完整结果表。"""
    print('\n' + '='*70)
    print('  Q3 Final Results')
    print('='*70)
    print(f'  {"Dataset":<8s} {"Gamma*":>8s} {"Dead%":>8s} {"S*":>6s}')
    print(f'  {"-"*40}')

    for name in ['n100', 'n200', 'n300']:
        gamma_star = (Q1M[name]**2 - load(name)['area']) / load(name)['area']
        dead_ratio = (Q1M[name]**2 - load(name)['area']) / Q1M[name]**2
        print(f'  {name:<8s} {gamma_star:8.4f} {dead_ratio*100:6.2f}%  {Q1M[name]:>6d}')

    if m4:
        print(f'\n  {"Dataset":<8s} {"HPWL(G=0.15)":>14s} {"HPWL(Gamma*)":>14s} {"Delta%":>8s} {"M_in_S*"}')
        print(f'  {"-"*60}')
        for name in ['n100', 'n200', 'n300']:
            r = m4[name]
            delta = (r['hpwl_star'] - r['hpwl_015']) / r['hpwl_015'] * 100
            print(f'  {name:<8s} {r["hpwl_015"]:>14,.0f} {r["hpwl_star"]:>14,.0f} '
                  f'{delta:+7.1f}%  {r["M_star"]:.0f}/{r["S_star"]:.0f}')
    print('='*70)


# ── main ──
def main():
    m4 = load_m4_results()

    print('=== M5 交付：可视化 + 结果表 ===')

    # 1. 三组布局图
    print('\n[1/4] 三组 Gamma* 布局图:')
    for name in ['n100', 'n200', 'n300']:
        S_star = Q1M[name]
        gamma_star = (S_star**2 - load(name)['area']) / load(name)['area']
        dead_ratio = (S_star**2 - load(name)['area']) / S_star**2
        plot_layout(name, S_star, gamma_star, dead_ratio)

    # 2. 可行性收缩曲线
    print('\n[2/4] 可行性收缩曲线:')
    plot_feasibility_curve()

    # 3. 权衡曲线
    print('\n[3/4] 权衡曲线:')
    plot_tradeoff_curve(m4)

    # 4. 结果表
    print('\n[4/4] 结果表:')
    print_result_table(m4)

    print('\n=== M5 完成 ===')
    print(f'输出目录: {OUT_DIR}')


if __name__ == '__main__':
    main()
