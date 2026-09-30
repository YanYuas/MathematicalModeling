"""
Performance Comparison: Original vs Optimized Fast-SA
"""
import time
from data_loader import load_blocks
from btree import BTree
from constructive import construct_initial_tree
from fast_sa import FastSA
from fast_sa_optimized import FastSAOptimized
from cost_functions import phase1_cost
from config import DATA_PATHS

print("=" * 70)
print("Performance Comparison: Original vs Optimized Fast-SA")
print("=" * 70)

# Load n100
blocks = load_blocks(DATA_PATHS['n100'])
A_total = sum(b.area for b in blocks)

# Build FFD initial
print("\n[Building Initial Tree (FFD)]")
init_tree = construct_initial_tree(blocks, method='ffd')
W_i, H_i, _ = init_tree.pack()
print(f"  FFD: W={W_i:.1f}, H={H_i:.1f}")

# Cost function
def cost_fn(tree):
    W, H, _ = tree.pack()
    return phase1_cost(W * H, A_total)

# Quick parameters
quick_params = {
    'T_final': 0.01,
    'max_no_improve': 15,
    'L_factor': 30,  # 进一步减少
}

print("\n" + "=" * 70)
print("Test 1: Original Fast-SA")
print("=" * 70)
t1_start = time.time()
sa1 = FastSA(blocks, cost_fn)
r1 = sa1.run(init_tree, seed=42, verbose=True, **quick_params)
t1_elapsed = time.time() - t1_start

print("\n" + "=" * 70)
print("Test 2: Optimized Fast-SA")
print("=" * 70)
t2_start = time.time()
sa2 = FastSAOptimized(blocks, cost_fn)
r2 = sa2.run(init_tree, seed=42, verbose=True, **quick_params)
t2_elapsed = time.time() - t2_start

print("\n" + "=" * 70)
print("Performance Comparison")
print("=" * 70)
print(f"\nOriginal:")
print(f"  Time:      {t1_elapsed:.2f}s")
print(f"  Cost:      {r1['best_cost']:.2f}")
print(f"  Deadspace: {r1['deadspace']:.2f}%")
print(f"  R:         {r1['R']:.3f}")

print(f"\nOptimized:")
print(f"  Time:      {t2_elapsed:.2f}s")
print(f"  Cost:      {r2['best_cost']:.2f}")
print(f"  Deadspace: {r2['deadspace']:.2f}%")
print(f"  R:         {r2['R']:.3f}")
print(f"  Cache hit: {r2.get('cache_hit_rate', 0)*100:.1f}%")

speedup = t1_elapsed / t2_elapsed if t2_elapsed > 0 else 0
quality_gap = abs(r1['best_cost'] - r2['best_cost']) / r1['best_cost'] * 100

print(f"\n{'='*70}")
print(f"Speedup:      {speedup:.2f}x")
print(f"Quality gap:  {quality_gap:.2f}%")

if speedup > 2.0 and quality_gap < 5.0:
    print(f"\n[OK] Optimization SUCCESS: {speedup:.1f}x faster, quality preserved")
elif speedup > 1.5:
    print(f"\n[OK] Moderate improvement: {speedup:.1f}x faster")
else:
    print(f"\n[WARN] Limited improvement: {speedup:.1f}x")

print("=" * 70)
