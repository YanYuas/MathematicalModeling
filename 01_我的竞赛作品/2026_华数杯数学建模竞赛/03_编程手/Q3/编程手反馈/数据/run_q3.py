# -*- coding: utf-8 -*-
"""run_q3.py — Q3 一键跑通：可行性扫描 → 突破尝试 → 层B HPWL → 可视化
用法: python run_q3.py
产出: 问题3/输出/ 下 5 张图 + m4_results.json
"""
import os, sys, math, json, time, copy, random
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path: sys.path.insert(0, _here)

# ── 依赖模块（自包含，全部在本目录） ──
from m2_data import load, Block
from m2_hpwl import evaluate, terminal_vs_internal
from m2_init import ffd_order_layout, skyline_order
from m_btree import BTree
from m_operators import random_perturbation
from m_construct import layout_to_btree

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = os.path.join(_here, '..', '输出')
os.makedirs(OUT_DIR, exist_ok=True)

Q1M = {'n100': 443, 'n200': 432, 'n300': 533}
Q2_REF = {'n100': 220252, 'n200': 430628, 'n300': 672474}
SEEDS = [42, 123, 456]
N_ITER = 10000


# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def rot_tall(blk_in):
    """长条旋转: AR>=2.5 长边水平"""
    out = []
    for b in blk_in:
        if max(b.w, b.h) / min(b.w, b.h) >= 2.5:
            out.append(Block(b.idx, b.name, max(b.w, b.h), min(b.w, b.h)))
        else:
            out.append(b)
    return out


def tree_to_posrot(tree, blk, data):
    W, H, _ = tree.pack()
    layout = tree.get_layout()
    pos, sizes = {}, {}
    for idx, x, y, w, h in layout:
        name = blk[idx].name
        pos[name] = (x, y)
        sizes[name] = (w, h)
    return pos, sizes, W, H


def make_initial_tree(blk, S):
    """FFD h_desc 行堆叠 → B*-Tree"""
    order = sorted(range(len(blk)), key=lambda i: -blk[i].h)
    layout = ffd_order_layout(blk, order, float(S))
    return layout_to_btree(blk, layout)


def greedy_solve(data, blk, tree, S, seed, n_iter=N_ITER):
    """贪心可行下降: cur 只在可行空间 (M≤S) 内移动"""
    random.seed(seed)
    cur = copy.deepcopy(tree)
    pos, sizes, _, _ = tree_to_posrot(cur, blk, data)
    cur_wl = evaluate(data, pos, sizes=sizes)[0]
    best_wl = cur_wl
    for i in range(n_iter):
        cand = copy.deepcopy(cur)
        random_perturbation(cand, probs=(0.2, 0.4, 0.4))
        pos, sizes, W, H = tree_to_posrot(cand, blk, data)
        if max(W, H) > S + 1e-9:
            continue
        wl = evaluate(data, pos, sizes=sizes)[0]
        if wl < cur_wl:
            cur = cand
            cur_wl = wl
            if wl < best_wl:
                best_wl = wl
    pos, sizes, W, H = tree_to_posrot(cur, blk, data)
    return {'wl': best_wl, 'M': max(W, H), 'S': S, 'W': W, 'H': H}


def run_best_of_N(data, blk, S, seeds=SEEDS):
    """多 seed 取最优"""
    blk_tall = rot_tall(blk)
    tree = make_initial_tree(blk_tall, S)
    best = None
    for s in seeds:
        r = greedy_solve(data, blk_tall, tree, S, seed=s)
        if best is None or r['wl'] < best['wl']:
            best = r
    return best


# ═══════════════════════════════════════════════════════════════
# 阶段 1: 可行性扫描
# ═══════════════════════════════════════════════════════════════

def run_feasibility_scan():
    print('=' * 60)
    print('阶段 1: 可行性扫描')
    print('=' * 60)
    results = {}
    for name in ['n100', 'n200', 'n300']:
        data = load(name)
        blk0 = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]
        strategies = ['h_desc', 'area_desc', 'skyline', 'skyline_area']

        best_S, best_strat = None, None
        lo = int(math.ceil(math.sqrt(data['area'])))
        for mode in ['tall']:
            blk = rot_tall(blk0) if mode == 'tall' else blk0
            for S in range(Q1M[name], lo - 1, -1):
                hit = None
                for strat in strategies:
                    if strat.startswith('skyline'):
                        order = sorted(range(len(blk)), key=lambda i: (
                            -blk[i].area if 'area' in strat else -blk[i].h))
                        layout = skyline_order(blk, order, float(S))
                    elif strat == 'h_desc':
                        order = sorted(range(len(blk)), key=lambda i: -blk[i].h)
                        layout = ffd_order_layout(blk, order, float(S))
                    else:
                        continue
                    W = max((x + blk[i].w for i, x, y in layout), default=0.0)
                    H = max((y + blk[i].h for i, x, y in layout), default=0.0)
                    if W <= S + 1e-9 and H <= S + 1e-9:
                        hit = (strat, W, H)
                        break
                if hit:
                    best_S = S
                    best_strat = hit[0]
                else:
                    break  # 不可行，停止向下
            if best_S:
                break

        gamma_star = (best_S ** 2 - data['area']) / data['area']
        dead_ratio = (best_S ** 2 - data['area']) / best_S ** 2
        print(f'  {name}: min feasible S={best_S} (strat={best_strat}) '
              f'Gamma*={gamma_star:.4f} Dead={dead_ratio:.2%}')
        results[name] = {'S_star': best_S, 'gamma_star': gamma_star, 'dead_ratio': dead_ratio}
    print()
    return results


# ═══════════════════════════════════════════════════════════════
# 阶段 2: 层B HPWL 优化
# ═══════════════════════════════════════════════════════════════

def run_layer_b():
    print('=' * 60)
    print('阶段 2: 层B HPWL 优化')
    print('=' * 60)
    all_r = {}
    for name in ['n100', 'n200', 'n300']:
        data = load(name)
        blk = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]

        for label, S in [('0.15', math.sqrt(data['area'] * 1.15)), ('star', Q1M[name])]:
            best = run_best_of_N(data, blk, S)
            key = f'{name}_{label}'
            all_r[key] = best
            wl_str = f'{best["wl"]:,.0f}'
            m_str = f'{best["M"]:.0f}'
            print(f'  {key}: HPWL={wl_str}  M={m_str}/{S:.0f}')
    print()

    # 保存
    with open(os.path.join(_here, 'm4_results.json'), 'w') as f:
        out = {k: {'wl': v['wl'], 'M': v['M'], 'S': v['S']} for k, v in all_r.items()}
        json.dump(out, f, indent=2)
    return all_r


# ═══════════════════════════════════════════════════════════════
# 阶段 3: 可视化
# ═══════════════════════════════════════════════════════════════

def make_figures(fs_results, m4_results):
    print('=' * 60)
    print('阶段 3: 可视化')
    print('=' * 60)

    # (a) 三组 Gamma* 布局图
    for name in ['n100', 'n200', 'n300']:
        data = load(name)
        blk0 = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]
        blk = rot_tall(blk0)
        S_star = Q1M[name]
        order = sorted(range(len(blk)), key=lambda i: -blk[i].h)
        layout = ffd_order_layout(blk, order, float(S_star))

        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_xlim(-5, S_star + 5)
        ax.set_ylim(-5, S_star + 5)
        ax.set_aspect('equal')
        ax.add_patch(patches.Rectangle((0, 0), S_star, S_star, fill=False,
                                        edgecolor='black', linewidth=2))

        colors = plt.cm.tab20(np.linspace(0, 1, len(blk)))
        for j, (idx, x, y) in enumerate(layout):
            b = blk[idx]
            ax.add_patch(patches.Rectangle((x, y), b.w, b.h, fill=True,
                facecolor=colors[j % 20], edgecolor='black', linewidth=0.3, alpha=0.7))
            if b.area > 200:
                ax.text(x + b.w / 2, y + b.h / 2, b.name, ha='center',
                        va='center', fontsize=5)

        t_xs = [p[0] for p in data['term_pos'].values()]
        t_ys = [p[1] for p in data['term_pos'].values()]
        ax.scatter(t_xs, t_ys, c='red', s=8, marker='s', zorder=10, alpha=0.8)

        gs = fs_results[name]['gamma_star']
        dr = fs_results[name]['dead_ratio']
        hpwl_text = ''
        if f'{name}_star' in m4_results:
            hpwl_val = m4_results[f'{name}_star']['wl']
            hpwl_text = f', HPWL={hpwl_val:,.0f}'
        ax.set_title(f'{name}: S*={S_star}, Gamma*={gs:.4f}, Dead={dr:.2%}{hpwl_text}', fontsize=14)
        ax.set_xlabel('X'); ax.set_ylabel('Y')

        fp = os.path.join(OUT_DIR, f'{name}_gamma_star_layout.png')
        plt.savefig(fp, dpi=200, bbox_inches='tight')
        plt.close()
        print(f'  {fp}')

    # (b) 可行性收缩曲线
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for ax_idx, name in enumerate(['n100', 'n200', 'n300']):
        ax = axes[ax_idx]
        data = load(name)
        blk = rot_tall([Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())])
        lo = int(math.ceil(math.sqrt(data['area'])))
        hi = Q1M[name]
        feasible_s, infeasible_s = [], []
        for S in range(lo, hi + 1):
            order = sorted(range(len(blk)), key=lambda i: -blk[i].h)
            layout = ffd_order_layout(blk, order, float(S))
            W = max((x + blk[i].w for i, x, y in layout), default=0.0)
            H = max((y + blk[i].h for i, x, y in layout), default=0.0)
            (feasible_s if W <= S + 1e-9 and H <= S + 1e-9 else infeasible_s).append(S)
        g_feas = [(s**2 / data['area'] - 1) for s in feasible_s]
        g_infeas = [(s**2 / data['area'] - 1) for s in infeasible_s]
        ax.scatter(g_feas, [1]*len(g_feas), c='green', s=30, marker='o', label='Feasible')
        ax.scatter(g_infeas, [0]*len(g_infeas), c='red', s=30, marker='x', label='Infeasible')
        ax.axvline(x=fs_results[name]['gamma_star'], color='blue', linestyle='--', label=f"Gamma*={fs_results[name]['gamma_star']:.4f}")
        ax.set_title(name); ax.set_xlabel('Gamma'); ax.set_ylim(-0.2, 1.5)
        ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
    fig.suptitle('Feasibility vs Gamma', fontsize=14)
    plt.tight_layout()
    fp = os.path.join(OUT_DIR, 'feasibility_curve.png')
    plt.savefig(fp, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  {fp}')

    # (c) 权衡曲线
    fig, ax = plt.subplots(figsize=(8, 6))
    for name, c, m in zip(['n100', 'n200', 'n300'], ['#2196F3', '#4CAF50', '#FF9800'], ['o', 's', '^']):
        wl15 = m4_results[f'{name}_0.15']['wl']
        wls = m4_results[f'{name}_star']['wl']
        gs = fs_results[name]['gamma_star']
        ax.plot([gs, 0.15], [wls, wl15], '-', color=c, linewidth=2, alpha=0.5)
        ax.scatter([gs], [wls], c=c, marker=m, s=120, zorder=5,
                    label=f'{name} (Gamma*={gs:.4f})')
        ax.scatter([0.15], [wl15], c=c, marker=m, s=80, zorder=5,
                    edgecolors=c, linewidths=1.5, facecolors='none')
        ax.annotate(f'{wls:,.0f}', (gs, wls), textcoords="offset points",
                     xytext=(10, -10), fontsize=9, color=c)
        ax.annotate(f'{wl15:,.0f}', (0.15, wl15), textcoords="offset points",
                     xytext=(10, 5), fontsize=9, color=c)
    ax.set_xlabel('Gamma (Dead Space Ratio)', fontsize=12)
    ax.set_ylabel('HPWL', fontsize=12)
    ax.set_title('HPWL vs Dead Space Ratio Trade-off', fontsize=14)
    ax.legend(fontsize=10); ax.grid(True, alpha=0.3)
    fp = os.path.join(OUT_DIR, 'tradeoff_curve.png')
    plt.savefig(fp, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  {fp}')

    print()


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    t0 = time.time()

    # 阶段 1
    fs = run_feasibility_scan()

    # 阶段 2
    m4 = run_layer_b()

    # 阶段 3
    make_figures(fs, m4)

    # 汇总
    print('=' * 65)
    print('  Q3 最终结果')
    print('=' * 65)
    print(f'  {"组":<6s} {"Gamma*":>8s} {"死区%":>8s} {"HPWL(.15)":>12s} {"HPWL(G*)":>12s} {"Δ%":>8s} {"M*/S*"}')
    print(f'  {"-"*65}')
    for name in ['n100', 'n200', 'n300']:
        gs = fs[name]['gamma_star']
        dr = fs[name]['dead_ratio']
        wl15 = m4[f'{name}_0.15']['wl']
        wls = m4[f'{name}_star']['wl']
        delta = (wls - wl15) / wl15 * 100
        Ms = m4[f'{name}_star']['M']
        Ss = m4[f'{name}_star']['S']
        wl15_s = f'{wl15:,.0f}'
        wls_s = f'{wls:,.0f}'
        delta_s = f'{delta:+.1f}'
        print(f'  {name:<6s} {gs:8.4f} {dr*100:6.2f}%  {wl15_s:>12s}  {wls_s:>12s}  {delta_s:>7s}%  {Ms:.0f}/{Ss:.0f}')
    print(f'  {"-"*65}')
    print(f'  总耗时: {time.time()-t0:.1f}s')
    print(f'  输出: {OUT_DIR}')
    print('=' * 65)
