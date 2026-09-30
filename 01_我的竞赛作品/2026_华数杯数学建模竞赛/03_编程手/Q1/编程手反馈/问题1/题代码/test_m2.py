"""
M2 Milestone Verification: Fast-SA converges to deadspace <= 6% on n100

Acceptance Criteria:
1. n100 with 10 random seeds
2. Mean deadspace <= 6%
3. Std deviation < 2%
4. Results fall in [LB, UB] interval
"""
import time
from data_loader import load_blocks
from btree import BTree
from fast_sa import FastSA
from cost_functions import minmax_cost, deadspace_percent, aspect_ratio
from config import DATA_PATHS, LOWER_BOUNDS, UPPER_BOUNDS

print("=" * 70)
print("M2 MILESTONE VERIFICATION")
print("=" * 70)
print()

# Load n100 dataset
print("Loading n100 dataset...")
blocks = load_blocks(DATA_PATHS['n100'])
total_area = sum(b.area for b in blocks)
print(f"Total blocks: {len(blocks)}")
print(f"Total area: {total_area:.0f}")
print()

# Define cost function (min-max)
def cost_fn(tree):
    W, H, _ = tree.pack()
    return minmax_cost(W, H)

# Run 10 seeds
print("Running Fast-SA with 10 random seeds...")
print("-" * 70)

results = []
for seed in range(10):
    print(f"\nSeed {seed}:", end=" ")

    # Random initial tree
    tree = BTree(blocks)
    tree.build_random_tree(seed=seed)

    # Run SA
    sa = FastSA(blocks, cost_fn)
    start_time = time.time()
    result = sa.run(tree, seed=seed)
    elapsed = time.time() - start_time

    # Compute metrics
    W, H = result['W'], result['H']
    R = aspect_ratio(W, H)
    ds = deadspace_percent(W, H, total_area)
    max_side = max(W, H)

    results.append({
        'seed': seed,
        'W': W,
        'H': H,
        'max_side': max_side,
        'R': R,
        'deadspace': ds,
        'iterations': result['iterations'],
        'time': elapsed
    })

    print(f"W={W:.1f}, H={H:.1f}, max={max_side:.1f}, R={R:.3f}, DS={ds:.2f}%, time={elapsed:.1f}s")

print()
print("=" * 70)
print("RESULTS SUMMARY")
print("=" * 70)
print()

# Compute statistics
deadspaces = [r['deadspace'] for r in results]
Rs = [r['R'] for r in results]
max_sides = [r['max_side'] for r in results]
times = [r['time'] for r in results]

mean_ds = sum(deadspaces) / len(deadspaces)
std_ds = (sum((x - mean_ds)**2 for x in deadspaces) / len(deadspaces)) ** 0.5

mean_R = sum(Rs) / len(Rs)
mean_max = sum(max_sides) / len(max_sides)
mean_time = sum(times) / len(times)

print(f"Deadspace:")
print(f"  Mean: {mean_ds:.2f}%")
print(f"  Std:  {std_ds:.2f}%")
print(f"  Range: [{min(deadspaces):.2f}%, {max(deadspaces):.2f}%]")
print()

print(f"Aspect Ratio:")
print(f"  Mean: {mean_R:.3f}")
print(f"  Range: [{min(Rs):.3f}, {max(Rs):.3f}]")
print()

print(f"Max(W,H):")
print(f"  Mean: {mean_max:.1f}")
print(f"  Range: [{min(max_sides):.1f}, {max(max_sides):.1f}]")
print()

print(f"Runtime:")
print(f"  Mean: {mean_time:.1f}s")
print(f"  Range: [{min(times):.1f}s, {max(times):.1f}s]")
print()

# Check bounds
LB = LOWER_BOUNDS['n100']
UB = UPPER_BOUNDS['n100']
in_bounds = all(LB <= r['max_side'] <= UB for r in results)

print(f"Bounds Check:")
print(f"  Lower bound: {LB}")
print(f"  Upper bound: {UB}")
print(f"  All results in [LB, UB]: {in_bounds}")
print()

# M2 Acceptance Criteria
print("=" * 70)
print("M2 ACCEPTANCE CRITERIA")
print("=" * 70)
print()

criterion_1 = mean_ds <= 6.0
criterion_2 = std_ds < 2.0
criterion_3 = in_bounds

print(f"1. Mean deadspace <= 6%:     {'[PASS]' if criterion_1 else '[FAIL]'} ({mean_ds:.2f}%)")
print(f"2. Std deviation < 2%:       {'[PASS]' if criterion_2 else '[FAIL]'} ({std_ds:.2f}%)")
print(f"3. Results in [LB, UB]:      {'[PASS]' if criterion_3 else '[FAIL]'}")
print()

if criterion_1 and criterion_2 and criterion_3:
    print("=" * 70)
    print("M2 MILESTONE: ACHIEVED [OK]")
    print("=" * 70)
else:
    print("=" * 70)
    print("M2 MILESTONE: NOT ACHIEVED [FAIL]")
    print("=" * 70)
