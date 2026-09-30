# -*- coding: utf-8 -*-
"""m2_final.py — Q2 独立实现 最终实验：贪心可行下降 best-of-N（主路径）
从 q1warm（可行起点）贪心下降线长，多 seed 取最优可行。
输出三组最终结果 + 基线对比 + 按网型分解。
"""
import time
import random
import copy
import pickle
import os
from m2_data import load, Block
from m2_init import q1warm_tree
from m2_hpwl import evaluate, terminal_vs_internal
from m2_sa import greedy_solve, tree_to_posrot

OUT = os.path.dirname(os.path.abspath(__file__))

# 每集：seed 数 × 迭代数
CONF = {
    'n100': dict(seeds=[1, 2, 3, 4, 5], n_iter=30000),
    'n200': dict(seeds=[1, 2, 3], n_iter=25000),
    'n300': dict(seeds=[1, 2, 3], n_iter=20000),
}
# 基线（建模手实测，编程手 hpwl.py）
BASELINE = {
    'n100': dict(allzero=150761, strip=295222, ref=197000),
    'n200': dict(allzero=251410, strip=552768, ref=346000),
    'n300': dict(allzero=321484, strip=832706, ref=503000),
}


def run(name):
    data = load(name)
    blk = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]
    S = data['side']
    tree, _ = q1warm_tree(data, blk)
    pos, sizes, W0, H0 = tree_to_posrot(tree, blk, data)
    wl0, _, _ = evaluate(data, pos, sizes=sizes)
    print(f'\n=== {name} S={S:.2f} 起点wl={wl0:,.0f} M0={max(W0,H0):.0f} ===', flush=True)

    cfg = CONF[name]
    best = None
    for seed in cfg['seeds']:
        t0 = time.time()
        bt, bw, acc = greedy_solve(data, blk, tree, seed=seed, n_iter=cfg['n_iter'])
        W, H, _ = bt.pack()
        print(f'  seed {seed}: wl={bw:,.0f} M={max(W,H):.0f} accept={acc} '
              f'用时={time.time()-t0:.0f}s', flush=True)
        if best is None or bw < best['wl']:
            pos, sizes, W, H = tree_to_posrot(bt, blk, data)
            io_t, in_t = terminal_vs_internal(data, pos, sizes=sizes)
            best = dict(tree=bt, wl=bw, W=W, H=H, io=io_t, internal=in_t, seed=seed)

    # 保存 best 树（供可视化/复现）
    with open(os.path.join(OUT, f'best_{name}.pkl'), 'wb') as f:
        pickle.dump({'tree': best['tree'], 'wl': best['wl'], 'W': best['W'],
                     'H': best['H'], 'seed': best['seed']}, f)

    bl = BASELINE[name]
    W, H = best['W'], best['H']
    gap_all = (best['wl'] - bl['allzero']) / bl['allzero'] * 100
    gap_strip = (bl['strip'] - best['wl']) / bl['strip'] * 100
    gap_ref = (best['wl'] - bl['ref']) / bl['ref'] * 100
    A = W * H
    ds = (A - data['area']) / A * 100
    print(f'\n[最终] {name}: best_wl={best["wl"]:,.0f} (seed {best["seed"]}) '
          f'{W:.0f}×{H:.0f} M={max(W,H):.0f}/{S:.0f} 死区={ds:.2f}%')
    print(f'  I/O网={best["io"]:,.0f} 内部网={best["internal"]:,.0f}')
    print(f'  基线: 全堆{bl["allzero"]:,} gap={gap_all:+.1f}% | '
          f'strip{bl["strip"]:,} gap={gap_strip:+.1f}% | '
          f'参考{bl["ref"]:,} gap={gap_ref:+.1f}%')
    return dict(name=name, **best, gap_all=gap_all, gap_strip=gap_strip,
                gap_ref=gap_ref, ds=ds)


if __name__ == '__main__':
    import sys
    names = sys.argv[1:] if len(sys.argv) > 1 else ['n100', 'n200', 'n300']
    all_res = [run(n) for n in names]
    print('\n\n===== Q2 最终结果汇总 =====')
    for r in all_res:
        print(f'{r["name"]}: wl={r["wl"]:,.0f}  {r["W"]:.0f}×{r["H"]:.0f} '
              f'M={max(r["W"],r["H"]):.0f} I/O={r["io"]:,.0f} 内部={r["internal"]:,.0f} '
              f'参考gap={r["gap_ref"]:+.1f}%')
