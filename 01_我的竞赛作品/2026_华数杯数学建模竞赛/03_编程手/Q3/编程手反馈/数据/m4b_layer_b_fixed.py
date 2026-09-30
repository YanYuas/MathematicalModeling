# -*- coding: utf-8 -*-
"""m4b_layer_b_fixed.py — 层B 修正版（建模手代理编程手）
修正点（对照编程手 run_q3.py 层B）：
  1. 起点换 q1warm_tree(target=S)（Q2 定稿同款），非 FFD h_desc
  2. 迭代对齐 Q2 定稿配置：n100 30k×5 / n200 25k×3 / n300 20k×3 seed
  3. 可行性门 = data['side'] 改 S（greedy_solve 复用 Q2 独立实现版）
输出: m4b_results.json（Γ=0.15 复现验证 + S* 更新 + 权衡采样）
"""
import os, sys, math, json, time
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path: sys.path.insert(0, _here)

import m2_data
m2_data.BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"
from m2_data import load, Block
from m2_init import q1warm_tree
from m2_sa import greedy_solve, tree_to_posrot
from m2_hpwl import evaluate

OUT = os.path.join(_here, '..', '输出')
os.makedirs(OUT, exist_ok=True)

# Q2 定稿配置（m2_final.py 验证过）
CONF = {'n100': (30000, 5), 'n200': (25000, 3), 'n300': (20000, 3)}
Q1M = {'n100': 443, 'n200': 432, 'n300': 533}
GAMMA = {'n100': 0.0933, 'n200': 0.0622, 'n300': 0.0400}
Q2_REF = {'n100': 220252, 'n200': 430628, 'n300': 672474}


def best_of_n(data, blk, S, n_iter, seeds, verbose=False):
    """q1warm 起点 + greedy_solve 多 seed best"""
    d2 = dict(data); d2['side'] = S
    tree, _ = q1warm_tree(data, blk, target=S)
    best_wl, best_tree, best_wh = 1e18, None, None
    for seed in seeds:
        bt, wl, _ = greedy_solve(d2, blk, tree, seed=seed, n_iter=n_iter)
        pos, sizes, W, H = tree_to_posrot(bt, blk, d2)
        if wl < best_wl:
            best_wl, best_tree = wl, bt
            best_wh = (W, H)
    return best_wl, best_tree, best_wh


def main():
    t0 = time.time()
    res = {}
    print('=' * 62)
    print('层B 修正版：q1warm 起点 + Q2 定稿迭代配置')
    print('=' * 62)
    for name in ['n100', 'n200', 'n300']:
        n_iter, n_seed = CONF[name]
        seeds = [42 + i * 111 for i in range(n_seed)]
        data = load(name)
        blk = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]

        # 1) Γ=0.15 复现验证
        S15 = math.sqrt(data['area'] * 1.15)
        wl15, _, wh15 = best_of_n(data, blk, S15, n_iter, seeds)
        ref = Q2_REF[name]
        gap = (wl15 - ref) / ref * 100
        flag = 'OK' if abs(gap) < 3 else 'MISMATCH'
        print(f'[{name}] Γ=0.15: HPWL={wl15:,.0f} (Q2定稿 {ref:,} gap {gap:+.1f}%) [{flag}]')

        # 2) S* 更新
        Sstar = Q1M[name]
        wlstar, _, whstar = best_of_n(data, blk, Sstar, n_iter, seeds)
        delta = (wlstar - wl15) / wl15 * 100
        print(f'        S*={Sstar}: HPWL={wlstar:,.0f} (WxH={whstar[0]:.0f}x{whstar[1]:.0f}) Δ={delta:+.1f}%')

        # 3) 权衡采样（轻量 1 seed 15k，中间点）
        trade = {}
        mids = [0.10, 0.125] if name == 'n100' else [0.09, 0.12] if name == 'n200' else [0.07, 0.10, 0.125]
        for g in mids:
            S = math.sqrt(data['area'] * (1 + g))
            wl, _, _ = best_of_n(data, blk, S, 15000, [7])
            trade[round(g, 4)] = wl
            print(f'        权衡 Γ={g}: HPWL={wl:,.0f}')

        res[name] = {
            'wl_015': wl15, 'wl_star': wlstar, 'delta_pct': delta,
            'S15': S15, 'Sstar': Sstar, 'wh_star': [whstar[0], whstar[1]],
            'gap_vs_Q2_pct': gap, 'trade': trade,
        }

    with open(os.path.join(OUT, 'm4b_results.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

    print('=' * 62)
    print(f'  总耗时 {time.time()-t0:.0f}s')
    print('=' * 62)


if __name__ == '__main__':
    main()
