"""
验证优化版本在两阶段M2流程中的表现
"""
from data_loader import load_blocks
from btree import BTree
from constructive import construct_initial_tree
from fast_sa_optimized import FastSAOptimized
from cost_functions import phase1_cost, phase2_cost
from config import DATA_PATHS
import time

print("=" * 70)
print("M2 Two-Phase with Ultra-fast Parameters")
print("=" * 70)

blocks = load_blocks(DATA_PATHS['n100'])
A_total = sum(b.area for b in blocks)

init_tree = construct_initial_tree(blocks, method='ffd')
W_i, H_i, _ = init_tree.pack()
print(f"\n[FFD Initial]: W={W_i:.1f}, H={H_i:.1f}")

# Ultra-fast parameters (from config.py after update)
ultra_params = {
    'T_final': 0.1,
    'max_no_improve': 8,
    'L_factor': 10,
}

print("\n" + "=" * 70)
print("Phase 1: Pure Area Minimization")
print("=" * 70)

def cost_p1(tree):
    W, H, _ = tree.pack()
    return phase1_cost(W * H, A_total)

t1_start = time.time()
sa1 = FastSAOptimized(blocks, cost_p1)
r1 = sa1.run(init_tree, seed=42, verbose=True, **ultra_params)
t1_elapsed = time.time() - t1_start

A_opt = r1['area']
print(f"\nPhase 1 Complete: A_opt = {A_opt:.0f}, Time = {t1_elapsed:.2f}s")

print("\n" + "=" * 70)
print("Phase 2: min-max + Area Soft Penalty")
print(f"  Constraint: A <= {A_opt * 1.01:.0f}")
print("=" * 70)

def cost_p2(tree):
    W, H, _ = tree.pack()
    A_chip = W * H
    return phase2_cost(W, H, A_chip, A_opt, eps=0.01, mu=1e6, norm=A_total)

t2_start = time.time()
sa2 = FastSAOptimized(blocks, cost_p2)
r2 = sa2.run(r1['best_tree'], seed=42, verbose=True, **ultra_params)
t2_elapsed = time.time() - t2_start

W2, H2, R2 = r2['best_tree'].pack()
A_final = W2 * H2
gap = (A_final - A_opt) / A_opt * 100

print("\n" + "=" * 70)
print("Two-Phase Optimization Complete")
print("=" * 70)
print(f"\nPhase 1:")
print(f"  A_opt:      {A_opt:.0f}")
print(f"  Time:       {t1_elapsed:.2f}s")

print(f"\nPhase 2:")
print(f"  A_final:    {A_final:.0f}")
print(f"  W × H:      {W2:.1f} × {H2:.1f}")
print(f"  Gap:        {gap:.2f}%")
print(f"  Deadspace:  {r2['deadspace']:.2f}%")
print(f"  R:          {R2:.3f}")
print(f"  Time:       {t2_elapsed:.2f}s")

print(f"\nTotal Time:   {t1_elapsed + t2_elapsed:.2f}s")

print("\n" + "=" * 70)
print("Verification")
print("=" * 70)

checks = [
    ("Gap < 5%", gap < 5.0),
    ("Deadspace < 10%", r2['deadspace'] < 10.0),
    ("R < 1.15", R2 < 1.15),
    ("Total time < 60s", (t1_elapsed + t2_elapsed) < 60.0),
]

all_ok = True
for label, ok in checks:
    print(f"  {'[OK]' if ok else '[FAIL]'} {label}")
    all_ok = all_ok and ok

print("\n" + "=" * 70)
if all_ok:
    print("M2 Ultra-fast Verification - PASSED")
    print("Ready for full experiment matrix (110 runs)")
else:
    print("M2 Ultra-fast Verification - Some criteria not met")

print("=" * 70)
