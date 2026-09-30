"""
Test different greedy ratios to find optimal balance
Target: gap 50-100% (better than random 300%, worse than FFD 5% for diversity)
"""
from data_loader import load_blocks
from constructive import greedy_random_init
from bounds import compute_lower_bound, compute_gap
from config import DATA_PATHS

dataset = 'n300'  # Focus on problematic n300
blocks = load_blocks(DATA_PATHS[dataset])
lower_bound = compute_lower_bound(blocks)

print("="*60)
print(f"Greedy Ratio Optimization ({dataset})")
print("="*60)
print("\nTarget: gap 50-100% for 5-8x SA speedup\n")

ratios = [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]

for ratio in ratios:
    tree = greedy_random_init(blocks, greedy_ratio=ratio, seed=42)
    W, H, _ = tree.pack()
    gap = compute_gap(max(W, H), lower_bound)

    method_name = {
        0.0: "Pure Random",
        1.0: "Pure FFD",
    }.get(ratio, f"Hybrid {int(ratio*100)}/{int((1-ratio)*100)}")

    status = "TARGET" if 50 <= gap <= 100 else ("TOO GOOD" if gap < 50 else "TOO BAD")
    print(f"  Ratio {ratio:.1f} ({method_name:20s}): gap={gap:6.2f}%  [{status}]")

print("\n" + "="*60)
print("Recommendation: Use ratio that gives gap 50-100%")
print("="*60)
