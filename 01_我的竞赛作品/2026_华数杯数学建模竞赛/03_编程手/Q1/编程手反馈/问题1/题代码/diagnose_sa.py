"""
Diagnostic test: Add progress logging to understand SA performance
"""
from data_loader import load_blocks
from btree import BTree
from fast_sa import FastSA
from cost_functions import minmax_cost
from config import DATA_PATHS
import time

print("SA Performance Diagnostic")
print("=" * 60)

# Load n100
blocks = load_blocks(DATA_PATHS['n100'])

# Cost function
def cost_fn(tree):
    W, H, _ = tree.pack()
    return minmax_cost(W, H)

# Create initial tree
tree = BTree(blocks)
tree.build_random_tree(seed=0)
W0, H0, _ = tree.pack()
print(f"Initial: W={W0:.1f}, H={H0:.1f}, cost={cost_fn(tree):.1f}")
print()

# Modify SA to add logging
print("Starting Fast-SA with progress logging...")
print("(If this hangs >30s at one step, we know the bottleneck)")
print()

sa = FastSA(blocks, cost_fn)

# Patch run method to add logging
original_run = sa.run

def logged_run(tree, seed=42):
    import random
    import copy
    from operators import random_perturbation

    random.seed(seed)

    # Normalization
    print("[1/5] Computing normalization... ", end="", flush=True)
    start = time.time()
    sa.A_norm = sa._compute_norm(tree)
    print(f"done ({time.time()-start:.1f}s)")

    # Init temperature
    print("[2/5] Initializing temperature... ", end="", flush=True)
    start = time.time()
    T1, delta_avg = sa._init_temperature(tree)
    print(f"done ({time.time()-start:.1f}s), T1={T1:.2f}")

    # Main loop - only run 5 levels for diagnostic
    print("[3/5] Running SA main loop (5 levels only for diagnostic)...")
    current_tree = copy.deepcopy(tree)
    best_tree = copy.deepcopy(tree)
    best_cost = cost_fn(tree)

    T = T1
    for n in range(1, 6):
        print(f"  Level {n}: T={T:.4f}... ", end="", flush=True)
        start = time.time()

        # Run temperature level
        current_tree, avg_delta_n, _ = sa._run_temperature_level(
            current_tree, T, L=100*len(blocks)
        )

        elapsed = time.time() - start
        print(f"done ({elapsed:.1f}s, {100*len(blocks)} iterations)")

        # Update best
        current_cost = cost_fn(current_tree)
        if current_cost < best_cost:
            best_cost = current_cost
            best_tree = copy.deepcopy(current_tree)

        # Update temperature
        if 2 <= n <= sa.k:
            T = T1 * avg_delta_n / (n * sa.c)
        else:
            T = T1 * avg_delta_n / n

    # Final results
    W, H, _ = best_tree.pack()
    print()
    print(f"[4/5] After 5 levels: W={W:.1f}, H={H:.1f}, cost={best_cost:.1f}")
    print(f"[5/5] Improvement: {cost_fn(tree):.1f} -> {best_cost:.1f} ({(1-best_cost/cost_fn(tree))*100:.1f}%)")

    return {
        'best_tree': best_tree,
        'best_cost': best_cost,
        'W': W, 'H': H,
        'iterations': 5
    }

sa.run = logged_run

# Run diagnostic
result = sa.run(tree, seed=0)

print()
print("=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
