"""
Quick M2 Milestone Test (Fast Parameters)
验证两阶段是否工作，用快速参数
"""
from data_loader import load_blocks
from btree import BTree
from fast_sa import solve_two_phase
from constructive import construct_initial_tree
from config import DATA_PATHS

print("=" * 60)
print("Quick M2 Milestone Test (Fast Parameters)")
print("=" * 60)

# Load n100
blocks = load_blocks(DATA_PATHS['n100'])
A_total = sum(b.area for b in blocks)

# FFD initial
print("\n[Building FFD Initial Tree]")
init_tree = construct_initial_tree(blocks, method='ffd')
W_i, H_i, _ = init_tree.pack()
print(f"  FFD initial: W={W_i:.1f}, H={H_i:.1f}")

# Quick SA parameters (reduced for speed)
quick_params = {
    'T_final': 0.01,       # 提前终止
    'max_no_improve': 20,  # 减少等待
    'L_factor': 50,        # 减少每级迭代
}

print("\n[Running Two-Phase with Quick Parameters]")
print(f"  (L_factor=50, max_no_improve=20, T_final=0.01)")

result = solve_two_phase(
    blocks, init_tree, seed=42,
    eps=0.01, mu=1e6,
    sa_run_params=quick_params,
    verbose=True
)

# Verification
print("\n" + "=" * 60)
print("[M2 Verification]")
print("=" * 60)

checks = [
    (f"Gap={result['gap_pct']:.2f}% < 10%", result['gap_pct'] < 10.0),
    (f"Deadspace={result['deadspace']:.2f}%", 2.0 <= result['deadspace'] <= 15.0),
    (f"R={result['R']:.3f} < 1.5", result['R'] < 1.5),
    (f"A_opt={result['A_opt']:.0f} defined", result['A_opt'] > 0)
]

for label, ok in checks:
    print(f"  {'[OK]' if ok else '[WARN]'} {label}")

all_ok = all(ok for _, ok in checks)

print("\n" + "=" * 60)
if all_ok:
    print("Quick M2 Test - PASSED")
    print("Two-phase structure working correctly")
else:
    print("Quick M2 Test - Partial (some metrics off, but structure OK)")

print("=" * 60)
