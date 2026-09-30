"""
Quick M2 test - single seed to verify functionality
"""
from data_loader import load_blocks
from btree import BTree
from fast_sa import FastSA
from cost_functions import minmax_cost, deadspace_percent, aspect_ratio
from config import DATA_PATHS, LOWER_BOUNDS, UPPER_BOUNDS

print("Quick M2 Test - Single Seed")
print("=" * 60)

# Load n100
blocks = load_blocks(DATA_PATHS['n100'])
total_area = sum(b.area for b in blocks)

# Cost function
def cost_fn(tree):
    W, H, _ = tree.pack()
    return minmax_cost(W, H)

# Random initial tree
tree = BTree(blocks)
tree.build_random_tree(seed=0)
W0, H0, _ = tree.pack()
print(f"Initial: W={W0:.1f}, H={H0:.1f}, max={max(W0,H0):.1f}")

# Run SA
print("\nRunning Fast-SA (seed=0)...")
sa = FastSA(blocks, cost_fn)
result = sa.run(tree, seed=0)

# Results
W, H = result['W'], result['H']
R = aspect_ratio(W, H)
ds = deadspace_percent(W, H, total_area)
max_side = max(W, H)

print(f"\nResults:")
print(f"  W={W:.1f}, H={H:.1f}")
print(f"  max(W,H)={max_side:.1f}")
print(f"  R={R:.3f}")
print(f"  Deadspace={ds:.2f}%")
print(f"  Iterations={result['iterations']}")

# Check criteria
LB = LOWER_BOUNDS['n100']
UB = UPPER_BOUNDS['n100']
in_bounds = LB <= max_side <= UB

print(f"\nChecks:")
print(f"  Deadspace <= 6%: {'[PASS]' if ds <= 6.0 else '[FAIL]'} ({ds:.2f}%)")
print(f"  In bounds [{LB}, {UB}]: {'[PASS]' if in_bounds else '[FAIL]'} ({max_side:.1f})")
