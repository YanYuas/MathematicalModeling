# -*- coding: utf-8 -*-
"""m2_experiment.py — Q2 独立实现 阶段P5：n100 全链路试运行
目标：验证 SA 能否 (a) 拉回轮廓 (b) 优化线长。
起点对比：random / pref_y（terminal-aware）/ 各排序。
"""
import sys
import time
from m2_data import Block, load
from m2_hpwl import evaluate, terminal_vs_internal
from m2_init import orders, construct, q1warm_tree
from m2_sa import Q2Cost, TwoPhaseLambda, FastSA2, compute_w_norm


def run_dataset(name, init_keys, seed=42, max_levels=40, L_factor=10,
                lam_p1=5.0, verbose=False):
    data = load(name)
    blk = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]
    print(f'\n=== {name} S={data["side"]:.2f} ===')
    results = []
    for k in init_keys:
        od = orders(data, blk)
        if k == 'random':
            from m_construct import construct_initial_tree
            tree = construct_initial_tree(blk, method='random', seed=seed)
        elif k == 'q1warm':
            tree, _ = q1warm_tree(data, blk)
        else:
            tree, _ = construct(data, od[k], blk)
        W0, H0, _ = tree.pack()
        pos, sizes, _, _ = tree_to_posrot(tree, blk, data)
        wl0, _, _ = evaluate(data, pos, sizes=sizes)
        print(f'[起点 {k}] wl={wl0:,.0f} M={max(W0,H0):.0f}/{data["side"]:.0f} '
              f'可行={"是" if max(W0,H0)<=data["side"] else "否"}')

        t0 = time.time()
        wn = compute_w_norm(data, blk, tree, n_samples=300, seed=seed)
        lam = TwoPhaseLambda(max_levels, lam_p1=lam_p1)
        cost = Q2Cost(data, blk, wn, lam)
        sa = FastSA2(cost)
        r = sa.run(tree, seed=seed, L_factor=L_factor, max_levels=max_levels,
                   verbose=verbose)
        r['init'] = k
        r['wl0'] = wl0
        r['W_norm'] = wn
        results.append(r)
        bm = f'{r["best_M"]:.0f}' if r['best_M'] is not None else 'None'
        imp = f'{(r["wl0"]-r["best_wl"])/r["wl0"]*100:.1f}%' if r['feasible'] else '-'
        print(f'  → {k}: best_wl={r["best_wl"]:,.0f} M={bm}/{data["side"]:.0f} '
              f'可行={r["feasible"]} 耗时={r["time"]:.1f}s 改善={imp}')
    return results


if __name__ == '__main__':
    # 快速测速：n100 10级
    name = sys.argv[1] if len(sys.argv) > 1 else 'n100'
    levels = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    from m2_sa import tree_to_posrot
    run_dataset(name, ['q1warm'], max_levels=levels, lam_p1=15.0, verbose=False)
