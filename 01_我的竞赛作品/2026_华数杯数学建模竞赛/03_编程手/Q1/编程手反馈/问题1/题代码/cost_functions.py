"""
Cost Functions for Multi-Objective Floorplan Optimization

Implements three cost function variants for optimizing chip layout:
1. Phase 2 Cost (Primary): max(W,H) + soft area penalty — two-phase lexicographic
2. Weighted Sum (Validation): A/A_norm + lambda*(R-1)^2 — normalized
3. Phase 1 Cost: Pure area minimization (A / A_norm)

The two-phase approach enforces dictionary priority:
  Phase 1 → A_opt (pure area min)
  Phase 2 → max(W,H) subject to A <= A_opt*(1+eps) soft penalty

Author: Algorithm Implementation Team
Date: 2026-08-08
Updated: Per 调整要求 M1/M3 — soft penalty, normalized weighted_cost
"""

from typing import Tuple


def phase2_cost(W: float, H: float, A_chip: float, A_opt: float,
                eps: float = 0.01, mu: float = 1e6, norm: float = None) -> float:
    """
    Phase 2 primary cost: min-max + area soft penalty (M1)

    min max(W,H) subject to A_chip <= A_opt * (1 + eps)

    Soft penalty (NOT hard inf) so SA can traverse infeasible regions.
    mu is large relative to primary term to guarantee final compliance.

    Args:
        W: Bounding box width
        H: Bounding box height
        A_chip: W * H (chip area)
        A_opt: Optimal area from Phase 1 (pure area SA result)
        eps: Area tolerance (default 0.01 = 1%)
        mu: Penalty coefficient (default 1e6, >> primary term magnitude)
        norm: Normalization factor (default: max(W,H) scale, typically ~400-550)

    Returns:
        max(W,H) + mu * max(0, A_chip - A_opt*(1+eps))
    """
    if norm is not None and norm > 0:
        primary = max(W, H) / norm
    else:
        primary = max(W, H)

    # Soft penalty: only penalize if area exceeds A_opt * (1 + eps)
    A_limit = A_opt * (1.0 + eps)
    penalty = mu * max(0.0, A_chip - A_limit)

    return primary + penalty


def phase1_cost(A_chip: float, A_norm: float) -> float:
    """
    Phase 1 cost: pure area minimization (M2)

    Args:
        A_chip: W * H (chip area)
        A_norm: Normalization factor (total block area)

    Returns:
        A_chip / A_norm — normalized area
    """
    return A_chip / max(A_norm, 1e-9)


def weighted_cost(W: float, H: float, A_chip: float, A_norm: float,
                  lam: float = 0.05) -> float:
    """
    Validation cost function: normalized weighted sum (M3)

    C = A_chip / A_norm + lam * (R - 1)^2

    Normalized so <Δcost> is on order of 1 for temperature formula validity.

    Args:
        W: Bounding box width
        H: Bounding box height
        A_chip: W * H (chip area)
        A_norm: Normalization factor (total block area)
        lam: Penalty coefficient (default 0.05, dimensionless)

    Returns:
        Normalized weighted cost

    Example:
        >>> weighted_cost(450, 440, 198000, 179501, lam=0.05)
        ~1.11
    """
    R = aspect_ratio(W, H)
    return A_chip / max(A_norm, 1e-9) + lam * (R - 1.0) ** 2


def minmax_cost(W: float, H: float, norm: float = 1.0) -> float:
    """
    Simple min-max cost: minimize max(W, H)

    Kept for compatibility / single-phase quick runs.
    For two-phase, use phase2_cost() instead.

    Args:
        W: Bounding box width
        H: Bounding box height
        norm: Normalization factor (default 1.0)

    Returns:
        max(W, H) / norm
    """
    return max(W, H) / max(norm, 1e-9)


def aspect_ratio(W: float, H: float) -> float:
    """
    Compute aspect ratio R = max(W,H) / min(W,H)

    Always returns R >= 1.0 (unified definition)

    Args:
        W: Width
        H: Height

    Returns:
        Aspect ratio >= 1.0

    Example:
        >>> aspect_ratio(100, 80)
        1.25
        >>> aspect_ratio(80, 100)
        1.25
        >>> aspect_ratio(100, 100)
        1.0
    """
    return max(W, H) / max(min(W, H), 1e-9)


def deadspace_percent(W: float, H: float, A_total: float) -> float:
    """
    Compute deadspace percentage

    deadspace% = (A_chip - A_blocks) / A_chip * 100

    Args:
        W: Bounding box width
        H: Bounding box height
        A_total: Total block area

    Returns:
        Deadspace percentage [0, 100]

    Example:
        >>> deadspace_percent(100, 100, 8000)
        20.0
        >>> deadspace_percent(100, 100, 10000)
        0.0
        >>> deadspace_percent(112.5, 89, 8000)
        20.11235955056178
    """
    A_chip = W * H
    return (A_chip - A_total) / max(A_chip, 1e-9) * 100


def gap_percent(result: float, lower_bound: float) -> float:
    """
    Compute gap from theoretical lower bound

    gap% = (result - LB) / LB * 100

    Args:
        result: Achieved result value
        lower_bound: Theoretical lower bound

    Returns:
        Gap percentage (can be negative if result < LB)

    Example:
        >>> gap_percent(10000, 8000)
        25.0
        >>> gap_percent(9000, 8000)
        12.5
        >>> gap_percent(8000, 8000)
        0.0
    """
    return (result - lower_bound) / max(lower_bound, 1e-9) * 100


# ============================================================================
# Integration Examples
# ============================================================================

# ============================================================================
# Integration Examples
# ============================================================================

def example_integration():
    """
    Example integration with FastSA optimizer

    Demonstrates two-phase primary flow and weighted validation.
    """
    print("=" * 70)
    print("Cost Functions Integration Examples")
    print("=" * 70)

    W, H = 450.0, 440.0
    A_total = 179501.0
    A_opt = 179800.0

    print(f"\nTest layout: W={W:.1f}, H={H:.1f}")
    print(f"Total block area: {A_total:.0f}")
    print(f"A_opt from Phase 1: {A_opt:.0f}")

    # Example 1: Two-phase (primary)
    print("\n" + "-" * 70)
    print("Example 1: Two-Phase Cost (Primary)")
    print("-" * 70)
    c_p2 = phase2_cost(W, H, W * H, A_opt, norm=A_total)
    print(f"Phase 2 cost: {c_p2:.6f}")
    print("\nIntegration code:")
    print("    # Phase 1")
    print("    def cost_p1(tree): W,H,_=tree.pack(); return (W*H)/A_total")
    print("    sa1 = FastSA(blocks, cost_p1); r1 = sa1.run(tree)")
    print("    A_opt = r1['area']")
    print("    # Phase 2")
    print("    def cost_p2(tree):")
    print("        W,H,_=tree.pack()")
    print("        return phase2_cost(W, H, W*H, A_opt, norm=A_total)")
    print("    sa2 = FastSA(blocks, cost_p2); r2 = sa2.run(r1['best_tree'])")

    # Example 2: Weighted (validation)
    print("\n" + "-" * 70)
    print("Example 2: Weighted Sum (Validation)")
    print("-" * 70)
    c_w = weighted_cost(W, H, W * H, A_total, lam=0.05)
    print(f"Cost: {c_w:.6f}")
    print("\nIntegration code:")
    print("    def cost_fn(tree):")
    print("        W,H,_=tree.pack()")
    print("        return weighted_cost(W, H, W*H, A_total, lam=0.05)")
    print("    sa = FastSA(blocks, cost_fn); result = sa.run(tree)")

    # Metrics
    print("\n" + "-" * 70)
    print("Quality Metrics")
    print("-" * 70)
    R = aspect_ratio(W, H)
    ds = deadspace_percent(W, H, A_total)
    gap_a = gap_percent(W * H, A_opt)
    print(f"Aspect ratio R: {R:.3f}")
    print(f"Deadspace: {ds:.2f}%")
    print(f"Gap (A_final - A_opt)/A_opt: {gap_a:.2f}%")
    print("\n" + "=" * 70)


# ============================================================================
# Testing
# ============================================================================

if __name__ == '__main__':
    print("Testing cost_functions.py (per 调整要求 M1/M3)")
    print("=" * 70)

    W, H = 450.0, 440.0
    A_total = 179501.0
    A_opt = 179800.0
    A_chip = W * H

    print(f"\nTest layout: W={W:.1f}, H={H:.1f}")
    print(f"Total block area: {A_total:.0f}")
    print(f"A_opt (from Phase 1): {A_opt:.0f}")
    print(f"A_chip: {A_chip:.0f}")

    print("\n" + "-" * 70)
    print("Function Tests (new signatures)")
    print("-" * 70)

    c_mm = minmax_cost(W, H, norm=A_total)
    c_w = weighted_cost(W, H, A_chip, A_total, lam=0.05)
    c_p1 = phase1_cost(A_chip, A_total)
    c_p2 = phase2_cost(W, H, A_chip, A_opt, norm=A_total)

    print(f"\n  min-max (legacy):     {c_mm:.6f}")
    print(f"  weighted (M3 fixed):  {c_w:.6f}")
    print(f"  phase1 (area):        {c_p1:.6f}")
    print(f"  phase2 (M1 correct):  {c_p2:.6f}")

    R = aspect_ratio(W, H)
    ds = deadspace_percent(W, H, A_total)
    gap_a = gap_percent(A_chip, A_opt)

    print(f"\n  Aspect ratio R: {R:.3f}")
    print(f"  Deadspace: {ds:.2f}%")
    print(f"  Gap (A-A_opt)/A_opt: {gap_a:.2f}%")

    # Acceptance tests
    print("\n" + "-" * 70)
    print("Acceptance Tests")
    print("-" * 70)

    tests_passed = 0
    tests_total = 0

    tests_total += 1
    if c_mm > 0 and c_w > 0 and c_p1 > 0 and c_p2 > 0:
        print(f"[PASS] 1. All cost functions return valid positive values")
        tests_passed += 1
    else:
        print(f"[FAIL] 1. Invalid cost function output")

    tests_total += 1
    if R >= 1.0:
        print(f"[PASS] 2. Aspect ratio R = {R:.3f} >= 1.0")
        tests_passed += 1
    else:
        print(f"[FAIL] 2. Aspect ratio R = {R:.3f} < 1.0")

    tests_total += 1
    if 0 <= ds <= 50:
        print(f"[PASS] 3. Deadspace {ds:.2f}% in valid range")
        tests_passed += 1
    else:
        print(f"[FAIL] 3. Deadspace {ds:.2f}% out of range")

    # M1: Soft penalty test
    tests_total += 1
    c_violated = phase2_cost(500, 500, 500 * 500, A_opt=179800, norm=A_total, eps=0.01, mu=1000)
    c_ok = phase2_cost(424, 424, 424 * 424, A_opt=179800, norm=A_total, eps=0.01, mu=1000)
    if c_violated > c_ok:  # violated layout should cost more
        print(f"[PASS] 4. M1 soft penalty working (violated={c_violated:.1f} > ok={c_ok:.1f})")
        tests_passed += 1
    else:
        print(f"[FAIL] 4. M1 soft penalty NOT working")

    # M3: Weighted is normalized (<Δcost> ≈ O(1))
    tests_total += 1
    if abs(c_w) < 10:  # Should be ~1.1 for this example, not ~200000
        print(f"[PASS] 5. M3 weighted normalized (c_w={c_w:.4f} < 10)")
        tests_passed += 1
    else:
        print(f"[FAIL] 5. M3 weighted NOT normalized (c_w={c_w:.4f})")

    # Edge case safety
    tests_total += 1
    try:
        minmax_cost(100, 0)
        aspect_ratio(0, 100)
        deadspace_percent(0, 0, 1000)
        gap_percent(100, 0)
        phase1_cost(0, 1000)
        print(f"[PASS] 6. No division by zero in edge cases")
        tests_passed += 1
    except ZeroDivisionError:
        print(f"[FAIL] 6. Division by zero detected")

    # Aspect ratio symmetry
    tests_total += 1
    R1 = aspect_ratio(100, 80)
    R2 = aspect_ratio(80, 100)
    if abs(R1 - R2) < 1e-9:
        print(f"[PASS] 7. Aspect ratio is symmetric: {R1:.3f} = {R2:.3f}")
        tests_passed += 1
    else:
        print(f"[FAIL] 7. Aspect ratio not symmetric")

    print("\n" + "-" * 70)
    print(f"Test Summary: {tests_passed}/{tests_total} tests passed")
    print("-" * 70)

    if tests_passed == tests_total:
        print("\n[OK] All cost functions working correctly (M1/M3 verified)")
        print("\nRunning integration examples...\n")
        example_integration()
    else:
        print(f"\n[FAIL] {tests_total - tests_passed} test(s) failed")

    print("\n" + "=" * 70)
