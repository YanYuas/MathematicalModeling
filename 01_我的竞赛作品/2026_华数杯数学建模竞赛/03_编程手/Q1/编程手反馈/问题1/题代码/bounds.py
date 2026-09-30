"""
Bounds Computation Module for Floorplanning Optimization

Computes theoretical lower bounds and constructive upper bounds
to validate optimization results and measure solution quality.

Author: Senior Developer
Date: 2026-08-08
"""

import math
from typing import List, Tuple
from data_loader import Block
from constructive import construct_initial_tree


def compute_lower_bound(blocks: List[Block]) -> int:
    """
    Compute theoretical lower bound (square packing assumption).

    Formula: LB = ceil(sqrt(total_area))
    Represents the minimum side length if blocks could be perfectly packed.

    Args:
        blocks: List of Block objects

    Returns:
        Theoretical lower bound (integer)
    """
    total_area = sum(b.area for b in blocks)
    return math.ceil(math.sqrt(total_area))


def compute_upper_bound(blocks: List[Block], method: str = 'ffd') -> int:
    """
    Compute constructive upper bound using heuristic initial solution.

    Uses FFD row packing to get a feasible layout, then returns max(W,H).

    Args:
        blocks: List of Block objects
        method: Construction method ('ffd' or 'skyline')

    Returns:
        Upper bound as max(W, H) from initial solution
    """
    tree = construct_initial_tree(blocks, method=method)
    W, H, _ = tree.pack()
    return math.ceil(max(W, H))


def compute_bounds(blocks: List[Block]) -> Tuple[int, int]:
    """
    Compute both theoretical lower bound and constructive upper bound.

    Args:
        blocks: List of Block objects

    Returns:
        (lower_bound, upper_bound) tuple
    """
    lb = compute_lower_bound(blocks)
    ub = compute_upper_bound(blocks)
    return lb, ub


def compute_gap(result: float, lower_bound: float) -> float:
    """
    Compute gap percentage from lower bound.

    Formula: gap = (result - lower_bound) / lower_bound * 100%

    Args:
        result: Achieved result value
        lower_bound: Theoretical lower bound

    Returns:
        Gap percentage
    """
    return (result - lower_bound) / max(lower_bound, 1e-9) * 100.0


# ==================== Testing ====================
if __name__ == '__main__':
    from config import DATA_PATHS
    from data_loader import load_blocks

    print("=" * 60)
    print("Bounds Computation Module Test")
    print("=" * 60)

    for name in ['n100', 'n200', 'n300']:
        print(f"\n{name}:")
        blocks = load_blocks(DATA_PATHS[name])

        lb, ub = compute_bounds(blocks)
        gap = compute_gap(ub, lb)

        print(f"  Lower Bound (LB): {lb}")
        print(f"  Upper Bound (UB): {ub}")
        print(f"  Gap: {gap:.2f}%")
        print(f"  [OK] Bounds computed successfully")
