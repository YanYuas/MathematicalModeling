"""
Simple diagnostic: Time each SA component
"""
from data_loader import load_blocks
from btree import BTree
from cost_functions import minmax_cost
from config import DATA_PATHS
import time

print("SA Component Timing Test")
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
print(f"Initial tree created: {len(blocks)} blocks")
print()

# Test 1: Single pack() time
print("Test 1: Single pack() operation")
start = time.time()
for i in range(100):
    W, H, R = tree.pack()
elapsed = time.time() - start
print(f"  100 packs: {elapsed:.2f}s ({elapsed*10:.1f}ms per pack)")
print()

# Test 2: Single perturbation + pack
print("Test 2: Perturbation + pack")
from operators import random_perturbation
import copy

start = time.time()
for i in range(100):
    test_tree = copy.deepcopy(tree)
    random_perturbation(test_tree)
    W, H, R = test_tree.pack()
elapsed = time.time() - start
print(f"  100 iterations: {elapsed:.2f}s ({elapsed*10:.1f}ms per iter)")
print()

# Test 3: Estimate one temperature level (10000 iterations)
print("Test 3: Estimated time for one temperature level (10000 iters)")
iterations_per_level = 100 * len(blocks)  # 10000 for n100
estimated_time = (elapsed / 100) * iterations_per_level
print(f"  Expected: {estimated_time:.1f}s per level")
print()

# Test 4: Estimate full SA run
print("Test 4: Estimated full SA run time")
typical_levels = 50  # Typical SA runs ~50 temperature levels
total_estimated = estimated_time * typical_levels
print(f"  {typical_levels} levels × {estimated_time:.1f}s = {total_estimated:.0f}s ({total_estimated/60:.1f} minutes)")
print()

print("=" * 60)
print("DIAGNOSIS:")
if total_estimated > 300:
    print("  [SLOW] SA will take >5 minutes per seed")
    print("  Recommendation: Reduce iterations per level or use constructive init")
elif total_estimated > 120:
    print("  [MODERATE] SA will take 2-5 minutes per seed")
    print("  Recommendation: Consider using constructive initial solution")
else:
    print("  [OK] SA should complete in reasonable time")
print("=" * 60)
