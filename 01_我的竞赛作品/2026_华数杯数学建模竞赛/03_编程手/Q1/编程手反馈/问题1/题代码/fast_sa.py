"""
Fast Simulated Annealing Algorithm for VLSI Floorplanning
Implements 3-phase temperature control with B*-Tree representation

Key Features:
- Adaptive initial temperature from random sampling
- Fast cooling in early phases (2 <= n <= k)
- Best-so-far tracking (not current scan point)
- Cost normalization for numerical stability
- EMA-based avg_delta tracking (C3)
- Two-phase lexicographic optimization (M2)

Author: Algorithm Implementation Team
Date: 2026-08-08
Updated: Per 调整要求 M2/C1/C3
"""
import random
import copy
import time
import math
from typing import List, Tuple, Callable, Dict
from data_loader import Block
from btree import BTree
from operators import random_perturbation
from config import SA_PARAMS


class FastSA:
    """
    Fast Simulated Annealing optimizer for B*-Tree floorplanning

    Temperature Schedule:
        T1 = delta_avg / abs(log(P))
        T_n = T1 * avg_delta_n / (n * c)  for 2 <= n <= k
        T_n = T1 * avg_delta_n / n        for n > k

    Args:
        blocks: List of Block objects to place
        cost_func: Function mapping BTree -> float (cost to minimize)
        P: Initial acceptance probability (default 0.9)
        k: Number of fast cooling levels (default 7)
        c: Fast cooling coefficient (default 100)
    """

    def __init__(
        self,
        blocks: List[Block],
        cost_func: Callable[[BTree], float],
        P: float = None,
        k: int = None,
        c: float = None,
        ema_alpha: float = 0.3  # C3: EMA smoothing factor
    ):
        self.blocks = blocks
        self.cost_func = cost_func

        # Load parameters from config if not provided
        self.P = P if P is not None else SA_PARAMS['P']
        self.k = k if k is not None else SA_PARAMS['k']
        self.c = c if c is not None else SA_PARAMS['c']
        self.ema_alpha = ema_alpha

        self.A_norm = None  # Cost normalization factor
        self._ema_delta = None  # C3: EMA-smoothed delta for temperature formula

    def _normalized_cost(self, tree: BTree) -> float:
        """
        Compute normalized cost to ensure deltas are on order of 1

        Returns:
            cost / A_norm
        """
        raw_cost = self.cost_func(tree)
        if self.A_norm is not None and self.A_norm > 0:
            return raw_cost / self.A_norm
        return raw_cost

    def _compute_norm(self, initial_tree: BTree) -> float:
        """
        Compute cost normalization factor from random sampling

        Purpose: Ensure <delta_cost> is on order of 1 for temperature formula
        Method: Apply 100 random perturbations and compute average cost

        Args:
            initial_tree: Starting tree configuration

        Returns:
            Average cost magnitude (used for normalization)
        """
        costs = []
        tree = copy.deepcopy(initial_tree)

        for _ in range(100):
            random_perturbation(tree)
            cost = self.cost_func(tree)
            costs.append(cost)

        avg_cost = sum(costs) / len(costs)
        # Return average cost as normalization factor
        # This ensures normalized costs are on order of 1
        return avg_cost if avg_cost > 0 else 1.0

    def _init_temperature(self, initial_tree: BTree) -> Tuple[float, float]:
        """
        Compute initial temperature T1 from random move sampling

        Algorithm:
            1. Apply 100 random perturbations
            2. Compute cost differences: delta_i = |cost_new - cost_old|
            3. delta_avg = mean(delta_i)
            4. T1 = delta_avg / abs(log(P))

        Args:
            initial_tree: Starting tree configuration

        Returns:
            (T1, delta_avg) - initial temperature and average cost difference
        """
        deltas = []
        tree = copy.deepcopy(initial_tree)
        old_cost = self.cost_func(tree)  # Use RAW cost, not normalized

        for _ in range(100):
            # Apply random perturbation
            random_perturbation(tree)

            # Compute new cost (raw)
            new_cost = self.cost_func(tree)

            # Record absolute difference
            deltas.append(abs(new_cost - old_cost))

            # Update old cost for next iteration
            old_cost = new_cost

        delta_avg = sum(deltas) / len(deltas) if deltas else 1.0

        # T1 = delta_avg / abs(log(P))
        # Use abs() because log(0.9) = -0.105 (negative)
        T1 = delta_avg / abs(math.log(self.P))

        return T1, delta_avg

    def _run_temperature_level(
        self,
        tree: BTree,
        T: float,
        L: int,
        best_tree: BTree,
        best_cost: float
    ) -> Tuple[BTree, float, List[float], BTree, float]:
        """
        Run L iterations at temperature T

        Returns:
            (updated_tree, avg_delta_this_level, deltas_list, best_tree, best_cost)
        """
        deltas = []
        current_tree = tree
        current_cost = self._normalized_cost(current_tree)

        for _ in range(L):
            candidate_tree = copy.deepcopy(current_tree)
            random_perturbation(candidate_tree)
            candidate_cost = self._normalized_cost(candidate_tree)

            accept = False

            if candidate_cost < current_cost:
                accept = True
                deltas.append(abs(candidate_cost - current_cost))
            else:
                delta = candidate_cost - current_cost
                prob = math.exp(-delta / T)
                if random.random() < prob:
                    accept = True
                    deltas.append(delta)

            if accept:
                current_tree = candidate_tree
                current_cost = candidate_cost

                raw_current_cost = self.cost_func(current_tree)
                if raw_current_cost < best_cost:
                    best_cost = raw_current_cost
                    best_tree = copy.deepcopy(current_tree)

        if deltas:
            avg_delta = sum(deltas) / len(deltas)
        else:
            avg_delta = 0.001

        # C3: EMA-smoothed delta (runs once per level)
        if self._ema_delta is None:
            self._ema_delta = avg_delta
        else:
            self._ema_delta = (
                self.ema_alpha * avg_delta +
                (1.0 - self.ema_alpha) * self._ema_delta
            )

        return current_tree, self._ema_delta, deltas, best_tree, best_cost

    def run(
        self,
        initial_tree: BTree,
        seed: int = 42,
        T_final: float = None,
        max_no_improve: int = None,
        L_factor: int = None,
        verbose: bool = True
    ) -> Dict:
        """
        Main Fast-SA optimization loop

        Args:
            initial_tree: Starting B*-Tree configuration
            seed: Random seed for reproducibility
            T_final: Termination temperature (default from config)
            max_no_improve: Early stopping threshold (default from config)
            L_factor: Iterations per level = L_factor * n (default from config)
            verbose: Print progress messages

        Returns:
            Dictionary with:
                - best_tree: Optimal B*-Tree found
                - best_cost: Cost of best solution
                - W, H, R: Layout dimensions and aspect ratio
                - area: Total layout area
                - deadspace: Deadspace percentage
                - iterations: Number of temperature levels
                - time: Runtime in seconds
                - convergence: Cost history per level
        """
        random.seed(seed)
        start_time = time.time()

        # Load parameters from config if not provided
        T_final = T_final if T_final is not None else SA_PARAMS['T_final']
        max_no_improve = max_no_improve if max_no_improve is not None else SA_PARAMS['max_no_improve']
        L_factor = L_factor if L_factor is not None else SA_PARAMS['L_factor']

        if verbose:
            print("=" * 60)
            print("Fast-SA Optimization Starting")
            print("=" * 60)

        # Step 1: Compute cost normalization (RED LINE #3)
        if verbose:
            print("[Phase 1] Computing cost normalization...")
        self.A_norm = self._compute_norm(initial_tree)
        if verbose:
            print(f"  A_norm = {self.A_norm:.2f}")

        # Step 2: Initialize temperature
        if verbose:
            print("[Phase 2] Initializing temperature...")
        T1, delta_avg = self._init_temperature(initial_tree)
        if verbose:
            print(f"  T1 = {T1:.4f}")
            print(f"  delta_avg = {delta_avg:.4f}")

        # Initialize tracking variables
        T = T1
        current_tree = copy.deepcopy(initial_tree)
        best_tree = copy.deepcopy(initial_tree)
        best_cost = self.cost_func(initial_tree)

        convergence = [best_cost]
        n = 1  # C1: n starts at 1 (T1 from init, then n++ to 2+ for cooling)
        no_improve_count = 0
        avg_delta_n = delta_avg  # Initialize with delta_avg from Phase 2

        if verbose:
            print(f"\n[Phase 3] Main optimization loop (C1: n=1->T1, 2<=n<=k->fast, n>k->normal)")
            print(f"  Initial cost: {best_cost:.2f}")
            print(f"  Termination: T < {T_final} or {max_no_improve} levels no improvement")
            print()

        # Step 3: Main SA loop (C1: level 1 uses T1 as-is)
        while T > T_final and no_improve_count < max_no_improve:
            L = L_factor * len(self.blocks)

            # Run this temperature level (C3: EMA delta computed inside)
            current_tree, avg_delta_n_new, deltas, best_tree, best_cost_new = \
                self._run_temperature_level(current_tree, T, L, best_tree, best_cost)

            if best_cost_new < best_cost:
                improvement = best_cost - best_cost_new
                if verbose:
                    print(f"  Level {n:3d}: T={T:8.4f}, Cost={best_cost_new:8.2f}, "
                          f"Δ_EMA={avg_delta_n_new:.4f}, Improved by {improvement:6.2f}")
                best_cost = best_cost_new
                no_improve_count = 0
            else:
                no_improve_count += 1
                if verbose and no_improve_count % 10 == 0:
                    print(f"  Level {n:3d}: T={T:8.4f}, Cost={best_cost:8.2f}, "
                          f"Δ_EMA={avg_delta_n_new:.4f}, No improve: {no_improve_count}")

            convergence.append(best_cost)

            # Use EMA-smoothed delta for temperature formula (C3)
            avg_delta_n = max(avg_delta_n_new, 0.01)
            n += 1

            # C1: temperature formula — n=1 skipped (uses T1), then:
            #      2 ≤ n ≤ k  → fast cooling
            #      n > k       → normal cooling
            if 2 <= n <= self.k:
                T = T1 * avg_delta_n / (n * self.c)
            else:
                T = T1 * avg_delta_n / n

        # Step 4: Compute final metrics
        W, H, R = best_tree.pack()
        total_area = sum(b.area for b in self.blocks)
        deadspace = ((W * H - total_area) / (W * H)) * 100

        elapsed_time = time.time() - start_time

        if verbose:
            print()
            print("=" * 60)
            print("Optimization Complete")
            print("=" * 60)
            print(f"  Final cost:     {best_cost:.2f}")
            print(f"  Layout:         W={W:.1f}, H={H:.1f}")
            print(f"  Area:           {W * H:.0f}")
            print(f"  Deadspace:      {deadspace:.2f}%")
            print(f"  Aspect ratio:   {R:.3f}")
            print(f"  Iterations:     {n} levels")
            print(f"  Time:           {elapsed_time:.2f}s")
            print("=" * 60)

        return {
            'best_tree': best_tree,
            'best_cost': best_cost,
            'W': W,
            'H': H,
            'R': R,
            'area': W * H,
            'deadspace': deadspace,
            'iterations': n,
            'time': elapsed_time,
            'convergence': convergence
        }


# ==================== M2: Two-Phase Optimization ====================

def solve_two_phase(
    blocks: List[Block],
    initial_tree: BTree,
    seed: int = 42,
    eps: float = 0.01,
    mu: float = 1e6,
    sa_run_params: dict = None,
    verbose: bool = True
) -> Dict:
    """
    Two-phase lexicographic optimization (M2).

    Phase 1: Pure area minimization → A_opt
    Phase 2: max(W,H) + area soft penalty → final layout

    Args:
        blocks: Block list
        initial_tree: Starting B*-Tree
        seed: Random seed for reproducibility
        eps: Area tolerance (default 1%)
        mu: Soft penalty coefficient
        sa_run_params: Override SA.run() parameters (T_final, max_no_improve, etc.)
        verbose: Print progress

    Returns:
        Dict with phase1 + phase2 results, gap = (A_final - A_opt)/A_opt
    """
    from cost_functions import phase1_cost, phase2_cost

    A_total = sum(b.area for b in blocks)
    sa_run_params = sa_run_params or {}

    if verbose:
        print("=" * 60)
        print("Two-Phase Optimization (M2)")
        print("=" * 60)

    # === Phase 1: Pure Area ===
    if verbose:
        print("\n" + "-" * 60)
        print("Phase 1: Pure Area Minimization")
        print("-" * 60)

    def cost_p1(tree: BTree) -> float:
        W, H, _ = tree.pack()
        A_chip = W * H
        return phase1_cost(A_chip, A_total)

    sa1 = FastSA(blocks, cost_p1)
    r1 = sa1.run(initial_tree, seed=seed, verbose=verbose, **sa_run_params)
    A_opt = r1['area']
    tree_p1_best = r1['best_tree']

    if verbose:
        print(f"\n  Phase 1 Complete: A_opt = {A_opt:.0f}")

    # === Phase 2: min-max + soft area penalty ===
    if verbose:
        print("\n" + "-" * 60)
        print("Phase 2: min-max + Area Soft Penalty")
        print(f"  Constraints: A <= A_opt * (1 + {eps}) = {A_opt * (1 + eps):.0f}")
        print("-" * 60)

    def cost_p2(tree: BTree) -> float:
        W, H, _ = tree.pack()
        A_chip = W * H
        return phase2_cost(W, H, A_chip, A_opt, eps=eps, mu=mu, norm=A_total)

    sa2 = FastSA(blocks, cost_p2)
    r2 = sa2.run(tree_p1_best, seed=seed, verbose=verbose, **sa_run_params)

    # === Metrics ===
    W2, H2, R2 = r2['best_tree'].pack()
    A_final = W2 * H2
    gap = (A_final - A_opt) / A_opt * 100 if A_opt > 0 else 0.0
    deadspace = (A_final - A_total) / A_final * 100

    if verbose:
        print("\n" + "=" * 60)
        print("Two-Phase Optimization Complete")
        print("=" * 60)
        print(f"  Phase 1 A_opt:    {A_opt:.0f}")
        print(f"  Phase 2 A_final:  {A_final:.0f}")
        print(f"  Gap (A_final-A_opt)/A_opt: {gap:.2f}%")
        print(f"  Layout:           W={W2:.1f}, H={H2:.1f}")
        print(f"  Deadspace:        {deadspace:.2f}%")
        print(f"  Aspect ratio:     {R2:.3f}")
        print("=" * 60)

    return {
        'best_tree': r2['best_tree'],
        'A_opt': A_opt,
        'A_final': A_final,
        'gap_pct': gap,
        'W': W2,
        'H': H2,
        'R': R2,
        'area': A_final,
        'deadspace': deadspace,
        'best_cost': r2['best_cost'],
        'iterations': r1['iterations'] + r2['iterations'],
        'time': r1['time'] + r2['time'],
        'convergence': r2['convergence'],
        'phase1': r1,
        'phase2': r2
    }


# ==================== Testing and Validation ====================
if __name__ == '__main__':
    from data_loader import load_blocks
    from cost_functions import phase1_cost, phase2_cost
    from config import DATA_PATHS, LOWER_BOUNDS, UPPER_BOUNDS

    print("=" * 60)
    print("Fast-SA + Two-Phase Optimization Test (M2)")
    print("=" * 60)

    blocks = load_blocks(DATA_PATHS['n100'])
    A_total = sum(b.area for b in blocks)

    # Build initial tree (FFD constructive)
    from constructive import construct_initial_tree
    print("\n[Building Initial Tree (FFD)]")
    init_tree = construct_initial_tree(blocks, method='ffd')
    W_i, H_i, _ = init_tree.pack()
    print(f"  FFD initial: W={W_i:.1f}, H={H_i:.1f}, max(W,H)={max(W_i,H_i):.1f}")

    # Run two-phase optimization (M2)
    result = solve_two_phase(
        blocks, init_tree, seed=42,
        eps=0.01, mu=1e6, verbose=True
    )

    # === Verification (per 调整要求 验收标准) ===
    print("\n[Verification - Adjusted M2 Milestone]")

    checks = []
    n = len(blocks)

    # 1. Bounds check
    in_bounds = LOWER_BOUNDS['n100'] <= result['best_cost'] <= UPPER_BOUNDS['n100']
    checks.append(('Cost in [LB,UB]', in_bounds))

    # 2. Gap check: (A_final - A_opt)/A_opt < 5%
    gap_ok = result['gap_pct'] < 5.0
    checks.append((f"Gap={result['gap_pct']:.2f}% < 5%", gap_ok))

    # 3. Deadspace 2-5%
    ds_ok = 2.0 <= result['deadspace'] <= 5.0
    checks.append((f"Deadspace {result['deadspace']:.2f}% (target 2-5%)", ds_ok))

    # 4. Aspect ratio
    r_ok = result['R'] <= 1.15
    checks.append((f"Aspect ratio R={result['R']:.3f} <= 1.15", r_ok))

    for label, passed in checks:
        print(f"  {'[OK]' if passed else '[FAIL]'} {label}")

    all_ok = all(p for _, p in checks)

    print("\n" + "=" * 60)
    if all_ok:
        print("M2 Milestone (Adjusted) - Complete [OK]")
        print("Per 验收标准: LB<=result<=UB, gap<5%, 死区2-5%, R<=1.15")
    else:
        print("M2 Milestone - Some criteria not met")
        print("Review failed checks above")
    print("=" * 60)

    # Robustness test (10 seeds)
    print("\n[Robustness Test: 10 Seeds]")
    print("=" * 60)
    gaps, areas, rs = [], [], []
    for s in range(10):
        tree_s = construct_initial_tree(blocks, method='ffd')
        r_s = solve_two_phase(blocks, tree_s, seed=s, verbose=False)
        gaps.append(r_s['gap_pct'])
        areas.append(r_s['A_final'])
        rs.append(r_s['R'])
        print(f"  Seed {s}: A={r_s['A_final']:.0f}, R={r_s['R']:.3f}, Gap={r_s['gap_pct']:.2f}%")

    avg_gap = sum(gaps) / len(gaps)
    std_gap = (sum((g - avg_gap)**2 for g in gaps) / len(gaps)) ** 0.5
    avg_area = sum(areas) / len(areas)
    print(f"\n  Average A_final: {avg_area:.0f}")
    print(f"  Average Gap:     {avg_gap:.2f}%")
    print(f"  Std Gap:          {std_gap:.2f}%")
    print(f"  Stability check:  {'[OK]' if std_gap < 3.0 else '[INFO] Variability exists'}")
    print("=" * 60)
