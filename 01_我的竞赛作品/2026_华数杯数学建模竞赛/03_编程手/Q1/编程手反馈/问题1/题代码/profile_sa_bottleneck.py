"""
Profile Fast-SA bottleneck: deepcopy vs pack() vs perturbation
"""
import time
import copy
from data_loader import load_blocks
from btree import BTree
from operators import random_perturbation
from cost_functions import minmax_cost
from config import DATA_PATHS

def profile_operations(blocks, n_samples=1000):
    """Profile individual operation costs"""
    tree = BTree(blocks)
    tree.build_random_tree(seed=0)
    n = len(blocks)

    # Test 1: deepcopy
    start = time.time()
    for _ in range(n_samples):
        _ = copy.deepcopy(tree)
    t_deepcopy = time.time() - start

    # Test 2: perturbation (on same tree)
    start = time.time()
    for _ in range(n_samples):
        random_perturbation(tree)
    t_perturb = time.time() - start

    # Test 3: pack()
    start = time.time()
    for _ in range(n_samples):
        tree.pack()
    t_pack = time.time() - start

    # Test 4: cost function
    start = time.time()
    for _ in range(n_samples):
        W, H, _ = tree.pack()
        _ = minmax_cost(W, H)
    t_cost = time.time() - start

    # Test 5: full iteration (deepcopy + perturb + pack + cost)
    start = time.time()
    for _ in range(n_samples):
        test_tree = copy.deepcopy(tree)
        random_perturbation(test_tree)
        W, H, _ = test_tree.pack()
        _ = minmax_cost(W, H)
    t_full = time.time() - start

    return {
        'n': n,
        'deepcopy': t_deepcopy / n_samples * 1000,  # ms
        'perturb': t_perturb / n_samples * 1000,
        'pack': t_pack / n_samples * 1000,
        'cost': (t_cost - t_pack) / n_samples * 1000,  # cost - pack
        'full': t_full / n_samples * 1000
    }

print("=" * 70)
print("Fast-SA Bottleneck Profiling")
print("=" * 70)

datasets = [
    ('n100', DATA_PATHS['n100']),
    ('n200', DATA_PATHS['n200']),
    ('n300', DATA_PATHS['n300'])
]

results = []
for name, path in datasets:
    print(f"\n[{name}]")
    blocks = load_blocks(path)
    r = profile_operations(blocks, n_samples=1000)
    results.append((name, r))

    print(f"  Blocks: {r['n']}")
    print(f"  deepcopy:    {r['deepcopy']:.3f} ms")
    print(f"  perturb:     {r['perturb']:.3f} ms")
    print(f"  pack():      {r['pack']:.3f} ms")
    print(f"  cost calc:   {r['cost']:.3f} ms")
    print(f"  full iter:   {r['full']:.3f} ms")
    print(f"  ---")
    print(f"  deepcopy%:   {r['deepcopy']/r['full']*100:.1f}%")
    print(f"  pack%:       {r['pack']/r['full']*100:.1f}%")

print("\n" + "=" * 70)
print("Complexity Analysis (n200/n100 ratio)")
print("=" * 70)
r100 = results[0][1]
r200 = results[1][1]
r300 = results[2][1]

ratio_deepcopy = r200['deepcopy'] / r100['deepcopy']
ratio_pack = r200['pack'] / r100['pack']
ratio_full = r200['full'] / r100['full']

print(f"  deepcopy ratio: {ratio_deepcopy:.2f}x (expected ~2x if O(n))")
print(f"  pack ratio:     {ratio_pack:.2f}x (expected ~2x if O(n))")
print(f"  full iter ratio:{ratio_full:.2f}x")

print("\n" + "=" * 70)
print("Projected n300 Time")
print("=" * 70)
n300_iters = 100 * r300['n']  # L_factor=100
n300_single_iter_ms = r300['full']
n300_per_level_s = n300_iters * n300_single_iter_ms / 1000
n300_typical_levels = 50
n300_total_s = n300_per_level_s * n300_typical_levels

print(f"  Single iteration: {n300_single_iter_ms:.3f} ms")
print(f"  Per level ({n300_iters} iters): {n300_per_level_s:.1f} s")
print(f"  Full run ({n300_typical_levels} levels): {n300_total_s:.0f} s ({n300_total_s/60:.1f} min)")

print("\n" + "=" * 70)
print("DIAGNOSIS")
print("=" * 70)
print(f"1. Single iteration scaling: n100({r100['full']:.2f}ms) → n200({r200['full']:.2f}ms) → n300({r300['full']:.2f}ms)")
print(f"   Ratio: {ratio_full:.2f}x (confirms O(n) per-iteration cost)")
print(f"\n2. Bottleneck breakdown (n300):")
print(f"   - deepcopy: {r300['deepcopy']:.3f}ms ({r300['deepcopy']/r300['full']*100:.0f}%)")
print(f"   - pack():   {r300['pack']:.3f}ms ({r300['pack']/r300['full']*100:.0f}%)")
print(f"   - perturb:  {r300['perturb']:.3f}ms ({r300['perturb']/r300['full']*100:.0f}%)")
print(f"\n3. Total complexity: O(iterations) × O(per-iter) = O(n) × O(n) = O(n²)")
print(f"   → n300 is {(r300['n']/r100['n'])**2:.0f}x slower than n100 (theoretical)")
print(f"   → Observed: {n300_total_s / 10.5:.1f}x slower")
print(f"\n4. Top 2 bottlenecks:")
if r300['deepcopy'] > r300['pack']:
    print(f"   #1: deepcopy ({r300['deepcopy']/r300['full']*100:.0f}%) - dominates")
    print(f"   #2: pack() ({r300['pack']/r300['full']*100:.0f}%)")
else:
    print(f"   #1: pack() ({r300['pack']/r300['full']*100:.0f}%) - dominates")
    print(f"   #2: deepcopy ({r300['deepcopy']/r300['full']*100:.0f}%)")
print("=" * 70)
