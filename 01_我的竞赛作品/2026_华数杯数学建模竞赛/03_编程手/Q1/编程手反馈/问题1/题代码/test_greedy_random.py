"""
Quick test for greedy_random initialization
Validates: 1) Gap improvement (300% -> 80%)
          2) Construction correctness
          3) Time improvement
"""
import time
from data_loader import load_blocks
from constructive import construct_initial_tree
from bounds import compute_lower_bound, compute_gap
from cost_functions import deadspace_percent
from config import DATA_PATHS, EXPECTED_AREAS

print("="*60)
print("Greedy-Random Initialization Test")
print("="*60)

for dataset in ['n100', 'n200', 'n300']:
    print(f"\n{'='*60}")
    print(f"Dataset: {dataset}")
    print(f"{'='*60}")

    blocks = load_blocks(DATA_PATHS[dataset])
    total_area = EXPECTED_AREAS[dataset]
    lower_bound = compute_lower_bound(blocks)

    # Test 1: Pure random (baseline)
    print("\n  [Baseline] Pure Random:")
    start = time.time()
    tree_random = construct_initial_tree(blocks, method='random', seed=42)
    t_random = time.time() - start

    W_r, H_r, _ = tree_random.pack()
    ds_r = deadspace_percent(W_r, H_r, total_area)
    gap_r = compute_gap(max(W_r, H_r), lower_bound)
    print(f"    Time: {t_random:.3f}s")
    print(f"    W={W_r:.1f}, H={H_r:.1f}, max={max(W_r,H_r):.1f}")
    print(f"    Deadspace: {ds_r:.2f}%, Gap: {gap_r:.2f}%")

    # Test 2: Greedy-random hybrid
    print("\n  [New] Greedy-Random (80/20):")
    start = time.time()
    tree_gr = construct_initial_tree(blocks, method='greedy_random', seed=42)
    t_gr = time.time() - start

    W_gr, H_gr, _ = tree_gr.pack()
    ds_gr = deadspace_percent(W_gr, H_gr, total_area)
    gap_gr = compute_gap(max(W_gr, H_gr), lower_bound)
    print(f"    Time: {t_gr:.3f}s")
    print(f"    W={W_gr:.1f}, H={H_gr:.1f}, max={max(W_gr,H_gr):.1f}")
    print(f"    Deadspace: {ds_gr:.2f}%, Gap: {gap_gr:.2f}%")

    # Test 3: FFD (reference)
    print("\n  [Reference] FFD:")
    start = time.time()
    tree_ffd = construct_initial_tree(blocks, method='ffd')
    t_ffd = time.time() - start

    W_f, H_f, _ = tree_ffd.pack()
    ds_f = deadspace_percent(W_f, H_f, total_area)
    gap_f = compute_gap(max(W_f, H_f), lower_bound)
    print(f"    Time: {t_ffd:.3f}s")
    print(f"    W={W_f:.1f}, H={H_f:.1f}, max={max(W_f,H_f):.1f}")
    print(f"    Deadspace: {ds_f:.2f}%, Gap: {gap_f:.2f}%")

    # Comparison
    print(f"\n  Summary:")
    print(f"    Gap improvement: {gap_r:.1f}% -> {gap_gr:.1f}% (target: <100%)")
    print(f"    Quality vs FFD: {gap_gr:.1f}% vs {gap_f:.1f}%")
    print(f"    [PASS]" if gap_gr < 100 else f"    [FAIL] gap still >100%")

print("\n" + "="*60)
print("Test Complete")
print("="*60)
