# -*- coding: utf-8 -*-
"""m2_final_render.py — Q2 定稿复跑 + 布局图重渲染 + 贪心收敛曲线
用途：
  1. 以定稿配置（best-of-N 两轮）重跑贪心可行下降，存 best_*.pkl（图内数字=表7-1）
  2. 渲染 q2_layout_*.png（读 pkl，保证 HPWL 与定稿一致）
  3. 画贪心收敛曲线 q2_conv_*.png（best_wl vs 迭代，替代 SA 收敛）
定稿配置（Q2最终统计表）：n100 5seed×30k；n200 3×25k+3×35k；n300 3×20k+2×30k
"""
import time, random, copy, pickle, os, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.dirname(os.path.abspath(__file__))
from m2_data import load, Block
from m2_init import q1warm_tree
from m2_hpwl import evaluate, terminal_vs_internal
from m2_sa import tree_to_posrot, Q2_PROBS
from m_operators import random_perturbation

# 定稿配置（两轮取最优）
CONF = {
    'n100': dict(seeds=[1, 2, 3, 4, 5], n_iter=30000),
    'n200': dict(seeds=[1, 2, 3, 4, 5, 6], n_iter=35000),  # 25k+35k 合并取 35k
    'n300': dict(seeds=[1, 2, 3, 4, 5], n_iter=30000),      # 20k+30k 合并取 30k
}
BASELINE = {
    'n100': dict(allzero=150761, strip=295222, ref=197000),
    'n200': dict(allzero=251410, strip=552768, ref=346000),
    'n300': dict(allzero=321484, strip=832706, ref=503000),
}


def greedy_solve_trace(data, blk, tree, seed=42, n_iter=30000, trace_every=500):
    """贪心可行下降（同 m2_sa.greedy_solve 逻辑，附加 best_wl trace）。
    可行性硬门 M≤S，接受线长改善扰动。返回 (best_tree, best_wl, accept, trace)。"""
    random.seed(seed)
    S = data['side']
    cur = copy.deepcopy(tree)
    pos, sizes, W0, H0 = tree_to_posrot(cur, blk, data)
    cur_wl, _, _ = evaluate(data, pos, sizes=sizes)
    best_tree, best_wl = copy.deepcopy(cur), cur_wl
    accept = 0
    trace = [(0, cur_wl)]
    for i in range(1, n_iter + 1):
        if i % trace_every == 0:
            trace.append((i, best_wl))
        cand = copy.deepcopy(cur)
        random_perturbation(cand, probs=Q2_PROBS)
        pos, sizes, W, H = tree_to_posrot(cand, blk, data)
        wl, _, _ = evaluate(data, pos, sizes=sizes)
        if max(W, H) > S:
            continue
        if wl < cur_wl:
            cur, cur_wl = cand, wl
            accept += 1
            if wl < best_wl:
                best_wl = wl
                best_tree = copy.deepcopy(cand)
    return best_tree, best_wl, accept, trace


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
    best_trace = None
    for seed in cfg['seeds']:
        t0 = time.time()
        bt, bw, acc, trace = greedy_solve_trace(data, blk, tree, seed=seed, n_iter=cfg['n_iter'])
        W, H, _ = bt.pack()
        print(f'  seed {seed}: wl={bw:,.0f} M={max(W,H):.0f} accept={acc} '
              f'用时={time.time()-t0:.0f}s', flush=True)
        if best is None or bw < best['wl']:
            pos, sizes, W, H = tree_to_posrot(bt, blk, data)
            io_t, in_t = terminal_vs_internal(data, pos, sizes=sizes)
            best = dict(tree=bt, wl=bw, W=W, H=H, io=io_t, internal=in_t, seed=seed)
            best_trace = trace

    # 保存 best 树（供可视化渲染，图内数字=定稿）
    with open(os.path.join(OUT, f'best_{name}.pkl'), 'wb') as f:
        pickle.dump({'tree': best['tree'], 'wl': best['wl'], 'W': best['W'],
                     'H': best['H'], 'seed': best['seed']}, f)

    bl = BASELINE[name]
    W, H = best['W'], best['H']
    gap_ref = (best['wl'] - bl['ref']) / bl['ref'] * 100
    ds = (W * H - data['area']) / (W * H) * 100
    print(f'[最终] {name}: best_wl={best["wl"]:,.0f} (seed {best["seed"]}) '
          f'{W:.0f}×{H:.0f} M={max(W,H):.0f}/{S:.0f} 死区={ds:.2f}%')
    print(f'  I/O网={best["io"]:,.0f} 内部网={best["internal"]:,.0f}')
    print(f'  基线: 全堆{bl["allzero"]:,} | strip{bl["strip"]:,} | 参考{bl["ref"]:,} gap={gap_ref:+.1f}%')

    # 收敛曲线
    draw_conv(name, best_trace, best['wl'])
    return dict(name=name, **best, gap_ref=gap_ref, ds=ds, wl0=wl0)


def draw_conv(name, trace, best_wl):
    its = [t[0] for t in trace]
    wls = [t[1] for t in trace]
    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.plot(its, wls, '-o', color='#2874A6', lw=1.8, markersize=4)
    ax.axhline(best_wl, color='#C0392B', ls='--', lw=1.2)
    ax.text(len(its) * 0.98, best_wl * 1.005, f'best={best_wl:,.0f}',
            ha='right', color='#C0392B', fontsize=10)
    ax.set_xlabel('迭代次数')
    ax.set_ylabel('best HPWL')
    ax.set_title(f'{name} 贪心可行下降收敛曲线 · best={best_wl:,.0f}', fontsize=12)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    p = os.path.join(OUT, f'q2_conv_{name}.png')
    fig.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  [conv_{name}] → {os.path.basename(p)}')


if __name__ == '__main__':
    import sys
    names = sys.argv[1:] if len(sys.argv) > 1 else ['n100', 'n200', 'n300']
    all_res = [run(n) for n in names]
    print('\n\n===== Q2 定稿复跑汇总 =====')
    for r in all_res:
        print(f'{r["name"]}: wl={r["wl"]:,.0f}  {r["W"]:.0f}×{r["H"]:.0f} '
              f'M={max(r["W"],r["H"]):.0f} I/O={r["io"]:,.0f} 内部={r["internal"]:,.0f} '
              f'参考gap={r["gap_ref"]:+.1f}%')
    # 结果 json
    with open(os.path.join(OUT, 'q2_final_render.json'), 'w', encoding='utf-8') as f:
        json.dump({r['name']: {k: v for k, v in r.items() if k != 'tree'}
                   for r in all_res}, f, ensure_ascii=False, indent=2)
    print('结果已存 q2_final_render.json')
