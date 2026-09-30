# -*- coding: utf-8 -*-
"""m4_layer_b.py — M4 层B：在 Γ* 下跑 greedy_solve 更新 HPWL
先复现 Γ=0.15 Q2 基准，再在 Γ* 下更新。
"""
import os, sys, math, json, time, copy, random
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path: sys.path.insert(0, _here)

from m2_data import load, Block, EXPECT
from m2_hpwl import evaluate, terminal_vs_internal, pack_dims
from m2_init import orders, ffd_order_layout, skyline_order
from m_btree import BTree, Node
from m_operators import random_perturbation
from m_construct import layout_to_btree


Q2_PROBS = (0.2, 0.4, 0.4)


def tree_to_posrot(tree, blk, data):
    W, H, _ = tree.pack()
    layout = tree.get_layout()
    pos, sizes = {}, {}
    for idx, x, y, w, h in layout:
        name = blk[idx].name
        pos[name] = (x, y)
        sizes[name] = (w, h)
    return pos, sizes, W, H


def greedy_solve(data, blk, tree, S, seed=42, n_iter=30000, verbose=False):
    """贪心可行下降。"""
    random.seed(seed)
    cur = copy.deepcopy(tree)
    pos, sizes, W0, H0 = tree_to_posrot(cur, blk, data)
    cur_wl, _, _ = evaluate(data, pos, sizes=sizes)
    best_tree, best_wl = copy.deepcopy(cur), cur_wl
    accept = 0
    t0 = time.time()

    for i in range(n_iter):
        cand = copy.deepcopy(cur)
        random_perturbation(cand, probs=Q2_PROBS)
        pos, sizes, W, H = tree_to_posrot(cand, blk, data)
        if max(W, H) > S + 1e-9:
            continue
        wl, _, _ = evaluate(data, pos, sizes=sizes)
        if wl < cur_wl:
            cur, cur_wl = cand, wl
            accept += 1
            if wl < best_wl:
                best_wl = wl
                best_tree = copy.deepcopy(cand)

    dt = time.time() - t0
    pos, sizes, W, H = tree_to_posrot(best_tree, blk, data)
    wl, per_net, _ = evaluate(data, pos, sizes=sizes)
    io_t, in_t = terminal_vs_internal(data, pos, sizes=sizes)
    return {
        'wl': wl, 'W': W, 'H': H, 'M': max(W, H), 'S': S,
        'accepts': accept, 'time': dt, 'io': io_t, 'internal': in_t,
        'best_tree': best_tree
    }


def run_multi_seed(data, blk, tree, S, seeds=None, n_iter=30000, verbose=True):
    if seeds is None:
        seeds = [42, 123, 456, 789, 2026]
    best = None
    all_wls = []
    for s in seeds:
        r = greedy_solve(data, blk, tree, S, seed=s, n_iter=n_iter, verbose=False)
        all_wls.append(r['wl'])
        if best is None or r['wl'] < best['wl']:
            best = r
    if verbose and len(all_wls) > 1:
        import statistics
        print(f'     best={min(all_wls):,.0f} mean={statistics.mean(all_wls):,.0f} '
              f'std={statistics.stdev(all_wls):,.0f} (N={len(seeds)})')
    elif verbose:
        print(f'     best={all_wls[0]:,.0f}')
    return best, all_wls


def make_initial_tree_ffd(blk, S):
    """用 FFD h_desc 构造初始可行树。
    layout_to_btree 需要 Block 对象，ffd_order_layout 输出 (idx, x, y) 元组。
    """
    order = sorted(range(len(blk)), key=lambda i: -blk[i].h)
    layout = ffd_order_layout(blk, order, float(S))
    return layout_to_btree(blk, layout)


def rot_tall(blk_in):
    """长条旋转：AR>=2.5 长边水平。"""
    out = []
    for b in blk_in:
        if max(b.w, b.h) / min(b.w, b.h) >= 2.5:
            out.append(Block(b.idx, b.name, max(b.w, b.h), min(b.w, b.h)))
        else:
            out.append(b)
    return out


def main():
    print('=== M4 层B：Γ=0.15 基准复现 + Γ* 下 HPWL 更新 ===')

    Q1M = {'n100': 443, 'n200': 432, 'n300': 533}
    Q2_REF = {'n100': 220252, 'n200': 430628, 'n300': 672474}
    N_ITER = 30000
    SEEDS = [42, 123, 456, 789, 2026]

    all_results = {}

    for name in ['n100', 'n200', 'n300']:
        print(f'\n{"="*60}')
        print(f'  [{name}]')
        print(f'{"="*60}')

        data = load(name)
        blk0 = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]
        ref_wl = Q2_REF[name]

        # --- step 1: gamma=0.15 baseline ---
        S015 = math.sqrt(data['area'] * 1.15)
        print(f'  [Step 1] Γ=0.15 (S={S015:.2f}):')

        blk015 = rot_tall(blk0)
        tree015 = make_initial_tree_ffd(blk015, S015)
        pos, sizes, W, H = tree_to_posrot(tree015, blk015, data)
        print(f'    初始树: W={W:.0f} H={H:.0f} M={max(W,H):.0f}')

        best015, all015 = run_multi_seed(data, blk015, tree015, S015, seeds=SEEDS, n_iter=N_ITER)
        feat15 = '可行' if best015['M'] <= S015 + 1e-9 else '超轮廓'
        print(f'    预期 Q2: {ref_wl:,.0f}  实测: {best015["wl"]:,.0f}  '
              f'Δ={(best015["wl"]-ref_wl)/ref_wl*100:+.1f}%  M={best015["M"]:.0f}/{S015:.0f} [{feat15}]')

        # --- step 2: gamma = gamma* ---
        S_star = Q1M[name]
        gamma_star = (S_star**2 - data['area']) / data['area']
        dead_ratio = (S_star**2 - data['area']) / S_star**2
        print(f'\n  [Step 2] Γ*={gamma_star:.4f} (S*={S_star}, 死区={dead_ratio:.2%}):')

        blk_star = rot_tall(blk0)
        tree_star = make_initial_tree_ffd(blk_star, S_star)
        pos, sizes, W, H = tree_to_posrot(tree_star, blk_star, data)
        print(f'    初始树: W={W:.0f} H={H:.0f} M={max(W,H):.0f}')

        best_star, all_star = run_multi_seed(data, blk_star, tree_star, S_star, seeds=SEEDS, n_iter=N_ITER)
        feat_star = '可行' if best_star['M'] <= S_star + 1e-9 else '超轮廓'
        print(f'    Γ* HPWL: {best_star["wl"]:,.0f}  M={best_star["M"]:.0f}/{S_star}  '
              f'I/O={best_star["io"]:,.0f} 内部={best_star["internal"]:,.0f} [{feat_star}]')

        delta_pct = (best_star["wl"] - best015["wl"]) / best015["wl"] * 100
        print(f'    HPWL 增量 vs Γ=0.15: {delta_pct:+.1f}%')

        all_results[name] = {
            'gamma_star': gamma_star,
            'dead_ratio': dead_ratio,
            'S_star': S_star,
            'S_015': S015,
            'hpwl_015': best015['wl'],
            'hpwl_star': best_star['wl'],
            'M_015': best015['M'],
            'M_star': best_star['M'],
            'io_star': best_star['io'],
            'internal_star': best_star['internal'],
            'ref_q2': ref_wl,
        }

    # 汇总
    print(f'\n\n{"="*60}')
    print(f'  M4 层B 汇总表')
    print(f'{"="*60}')
    print(f'  {"组":<6s} {"Γ*":>8s} {"死区%":>8s} {"HPWL(γ*)":>12s} {"HPWL(.15)":>12s} {"Δ%":>8s}')
    print(f'  {"-"*60}')
    for name in ['n100', 'n200', 'n300']:
        r = all_results[name]
        delta = (r['hpwl_star'] - r['hpwl_015']) / r['hpwl_015'] * 100
        print(f'  {name:<6s} {r["gamma_star"]:8.4f} {r["dead_ratio"]*100:6.2f}%  '
              f'{r["hpwl_star"]:>12,.0f}  {r["hpwl_015"]:>12,.0f}  {delta:+7.1f}%')

    # 保存
    serializable = {}
    for name, r in all_results.items():
        serializable[name] = {}
        for k, v in r.items():
            if isinstance(v, (float, int)):
                serializable[name][k] = float(v)
            else:
                pass  # skip tree objects
    with open(os.path.join(_here, 'm4_results.json'), 'w') as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)
    print(f'\n结果已保存: m4_results.json')
    print('=== M4 完成 ===')


if __name__ == '__main__':
    main()
