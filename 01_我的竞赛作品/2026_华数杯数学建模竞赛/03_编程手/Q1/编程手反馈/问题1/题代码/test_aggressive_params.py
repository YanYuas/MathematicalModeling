"""
Aggressive Parameters Test - 目标 3-4x 加速
"""
import time
from data_loader import load_blocks
from btree import BTree
from constructive import construct_initial_tree
from fast_sa_optimized import FastSAOptimized
from cost_functions import phase1_cost
from config import DATA_PATHS

print("=" * 70)
print("Aggressive Parameters Test (3-4x speedup target)")
print("=" * 70)

blocks = load_blocks(DATA_PATHS['n100'])
A_total = sum(b.area for b in blocks)

init_tree = construct_initial_tree(blocks, method='ffd')
W_i, H_i, _ = init_tree.pack()
print(f"\n[Initial FFD]: W={W_i:.1f}, H={H_i:.1f}")

def cost_fn(tree):
    W, H, _ = tree.pack()
    return phase1_cost(W * H, A_total)

# 三组参数对比
configs = {
    'Baseline (original)': {
        'T_final': 0.001,
        'max_no_improve': 50,
        'L_factor': 100,
    },
    'Conservative': {
        'T_final': 0.02,
        'max_no_improve': 12,
        'L_factor': 20,
    },
    'Aggressive': {
        'T_final': 0.05,
        'max_no_improve': 10,
        'L_factor': 15,
    },
    'Ultra-fast': {
        'T_final': 0.1,
        'max_no_improve': 8,
        'L_factor': 10,
    }
}

results = {}

for name, params in configs.items():
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"  Params: L={params['L_factor']}, stop={params['max_no_improve']}, Tf={params['T_final']}")
    print(f"{'='*70}")

    t_start = time.time()
    sa = FastSAOptimized(blocks, cost_fn)
    r = sa.run(init_tree, seed=42, verbose=False, **params)
    t_elapsed = time.time() - t_start

    results[name] = {
        'time': t_elapsed,
        'cost': r['best_cost'],
        'deadspace': r['deadspace'],
        'R': r['R'],
        'area': r['area'],
        'cache_hit': r.get('cache_hit_rate', 0) * 100
    }

    print(f"  Time:      {t_elapsed:.2f}s")
    print(f"  Cost:      {r['best_cost']:.4f}")
    print(f"  Deadspace: {r['deadspace']:.2f}%")
    print(f"  R:         {r['R']:.3f}")
    print(f"  Cache hit: {r.get('cache_hit_rate', 0)*100:.1f}%")

# Summary
print("\n" + "=" * 70)
print("Summary Comparison")
print("=" * 70)

baseline_time = results['Baseline (original)']['time']

print(f"\n{'Config':<20} {'Time':>8} {'Speedup':>8} {'Cost':>10} {'DS%':>6} {'R':>6}")
print("-" * 70)

for name, r in results.items():
    speedup = baseline_time / r['time']
    print(f"{name:<20} {r['time']:>7.2f}s {speedup:>7.2f}x {r['cost']:>10.4f} {r['deadspace']:>5.1f}% {r['R']:>6.3f}")

# Quality vs Speed tradeoff
print("\n" + "=" * 70)
print("Quality vs Speed Tradeoff")
print("=" * 70)

baseline_cost = results['Baseline (original)']['cost']

for name, r in results.items():
    if name == 'Baseline (original)':
        continue

    speedup = baseline_time / r['time']
    quality_gap = abs(r['cost'] - baseline_cost) / baseline_cost * 100

    print(f"\n{name}:")
    print(f"  Speedup:      {speedup:.2f}x")
    print(f"  Quality gap:  {quality_gap:.2f}%")

    if speedup >= 3.0 and quality_gap < 5.0:
        print(f"  Status:       [OK] Target achieved!")
    elif speedup >= 2.0:
        print(f"  Status:       [OK] Good balance")
    else:
        print(f"  Status:       [INFO] Limited speedup")

print("\n" + "=" * 70)
print("Recommendation:")

# Find best balance
best = None
best_score = 0

for name, r in results.items():
    if name == 'Baseline (original)':
        continue

    speedup = baseline_time / r['time']
    quality_gap = abs(r['cost'] - baseline_cost) / baseline_cost * 100

    # Score: speedup重要，quality_gap惩罚
    score = speedup - quality_gap * 0.5

    if score > best_score:
        best_score = score
        best = name

if best:
    r = results[best]
    speedup = baseline_time / r['time']
    print(f"  Best config: {best}")
    print(f"  Speedup:     {speedup:.2f}x")
    print(f"  Time:        {r['time']:.2f}s")
    print(f"  Quality:     DS={r['deadspace']:.1f}%, R={r['R']:.3f}")

print("=" * 70)
