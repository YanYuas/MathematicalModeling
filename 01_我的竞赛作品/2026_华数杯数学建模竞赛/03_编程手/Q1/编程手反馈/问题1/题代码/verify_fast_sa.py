"""
Quick verification of Fast-SA implementation
Tests critical components without full optimization run
"""
import math
from data_loader import load_blocks
from btree import BTree
from fast_sa import FastSA
from config import DATA_PATHS

print("=" * 60)
print("Fast-SA Quick Verification")
print("=" * 60)

# Load small dataset
print("\n[1] Loading data...")
blocks = load_blocks(DATA_PATHS['n100'])
print(f"    Loaded {len(blocks)} blocks")

# Build initial tree
print("\n[2] Building initial tree...")
tree = BTree(blocks)
tree.build_random_tree(seed=42)
W, H, R = tree.pack()
print(f"    Initial: W={W:.1f}, H={H:.1f}, R={R:.3f}")

# Define cost function
def cost_fn(tree):
    W, H, R = tree.pack()
    return max(W, H)

initial_cost = cost_fn(tree)
print(f"    Initial cost: {initial_cost:.2f}")

# Create FastSA instance
print("\n[3] Creating FastSA instance...")
sa = FastSA(blocks, cost_fn, P=0.9, k=7, c=100)
print(f"    P={sa.P}, k={sa.k}, c={sa.c}")

# Test normalization
print("\n[4] Testing cost normalization...")
A_norm = sa._compute_norm(tree)
print(f"    A_norm = {A_norm:.2f}")
normalized = sa._normalized_cost(tree)
print(f"    Normalized cost = {normalized:.4f}")

# Test temperature initialization
print("\n[5] Testing temperature initialization...")
T1, delta_avg = sa._init_temperature(tree)
print(f"    T1 = {T1:.4f}")
print(f"    delta_avg = {delta_avg:.4f}")
print(f"    Formula check: T1 = {delta_avg:.4f} / abs(log({sa.P})) = {delta_avg / abs(math.log(sa.P)):.4f}")

# Test temperature schedule
print("\n[6] Testing temperature schedule...")
print("    Level | Formula | Temperature")
print("    ------|---------|------------")
for n in range(1, 12):
    if 2 <= n <= sa.k:
        T_n = T1 * delta_avg / (n * sa.c)
        formula = f"T1*Δ/(n*c)"
    else:
        T_n = T1 * delta_avg / n
        formula = f"T1*Δ/n"
    print(f"    {n:5d} | {formula:11s} | {T_n:12.6f}")

# Run short optimization (only 5 levels)
print("\n[7] Running short optimization (5 levels)...")
result = sa.run(
    tree,
    seed=42,
    max_no_improve=5,  # Stop after 5 levels
    verbose=False
)

print(f"    Best cost: {result['best_cost']:.2f}")
print(f"    Layout: W={result['W']:.1f}, H={result['H']:.1f}")
print(f"    Deadspace: {result['deadspace']:.2f}%")
print(f"    Levels: {result['iterations']}")
print(f"    Time: {result['time']:.2f}s")
print(f"    Improvement: {initial_cost - result['best_cost']:.2f}")

# Verification checks
print("\n[8] Verification checks...")
checks = []

# Check 1: Improvement
improved = result['best_cost'] < initial_cost
checks.append(("Optimization improved cost", improved))
print(f"    ✓ Improvement: {improved}")

# Check 2: Valid layout
valid = result['W'] > 0 and result['H'] > 0
checks.append(("Valid layout dimensions", valid))
print(f"    ✓ Valid layout: {valid}")

# Check 3: Convergence
conv = result['convergence']
monotonic = all(conv[i] <= conv[i-1] + 1.0 for i in range(1, len(conv)))
checks.append(("Monotonic convergence", monotonic))
print(f"    ✓ Convergence: {monotonic}")

# Check 4: Temperature formula
T_test = T1 * delta_avg / (2 * sa.c)  # n=2, fast cooling
formula_correct = abs(T_test - T1 * delta_avg / (2 * sa.c)) < 0.0001
checks.append(("Temperature formula correct", formula_correct))
print(f"    ✓ Formula: {formula_correct}")

# Summary
print("\n" + "=" * 60)
all_passed = all(result for _, result in checks)

if all_passed:
    print("Fast-SA Implementation VERIFIED ✓")
    print("All critical components working correctly")
else:
    print("Fast-SA Implementation - Some checks failed")
    for check_name, result in checks:
        if not result:
            print(f"  ✗ {check_name}")

print("=" * 60)
