"""
Test random initialization gap across multiple seeds
Determine if n300+random really has 300% average gap
"""
from data_loader import load_blocks
from constructive import construct_initial_tree
from bounds import compute_lower_bound, compute_gap
from config import DATA_PATHS
import statistics

dataset = 'n300'
blocks = load_blocks(DATA_PATHS[dataset])
lower_bound = compute_lower_bound(blocks)

print("="*60)
print(f"Random Initialization Gap Distribution ({dataset})")
print("="*60)

gaps = []
for seed in range(20):  # Test 20 seeds
    tree = construct_initial_tree(blocks, method='random', seed=seed)
    W, H, _ = tree.pack()
    gap = compute_gap(max(W, H), lower_bound)
    gaps.append(gap)
    print(f"  Seed {seed:2d}: gap={gap:6.2f}%")

print("\n" + "="*60)
print(f"Statistics:")
print(f"  Mean:   {statistics.mean(gaps):6.2f}%")
print(f"  Median: {statistics.median(gaps):6.2f}%")
print(f"  StdDev: {statistics.stdev(gaps):6.2f}%")
print(f"  Min:    {min(gaps):6.2f}%")
print(f"  Max:    {max(gaps):6.2f}%")
print("="*60)

if statistics.mean(gaps) < 100:
    print("\n[结论] Random初始化平均gap<100%，n300+random不需要特殊优化")
    print("       原timeout问题可能是其他原因（deepcopy瓶颈）")
else:
    print(f"\n[结论] Random初始化平均gap={statistics.mean(gaps):.1f}%，确需优化")
