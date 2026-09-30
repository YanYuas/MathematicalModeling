"""
Fast-SA Optimized Version - 消除深拷贝瓶颈

核心优化：
1. 原地修改 + 撤销机制（替代 deepcopy）
2. 缓存 pack 结果（避免重复计算）
3. 减少温度级数（quality vs speed）

预期提升：5-10x 加速
"""
import random
import copy
import time
import math
from typing import List, Tuple, Callable, Dict
from data_loader import Block
from btree import BTree
from operators import op1_rotate, op2_delete_insert, op3_swap
from config import SA_PARAMS


class FastSAOptimized:
    """
    Optimized Fast Simulated Annealing

    Key optimizations:
    - In-place perturbation with undo mechanism
    - Cached pack results
    - Reduced memory allocation
    """

    def __init__(
        self,
        blocks: List[Block],
        cost_func: Callable[[BTree], float],
        P: float = None,
        k: int = None,
        c: float = None,
        ema_alpha: float = 0.3
    ):
        self.blocks = blocks
        self.cost_func = cost_func
        self.P = P if P is not None else SA_PARAMS['P']
        self.k = k if k is not None else SA_PARAMS['k']
        self.c = c if c is not None else SA_PARAMS['c']
        self.ema_alpha = ema_alpha
        self.A_norm = None
        self._ema_delta = None

        # Performance cache
        self._pack_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def _get_tree_hash(self, tree: BTree) -> int:
        """快速树哈希（用于缓存）"""
        # 简化版：只hash节点block ID序列
        try:
            node_ids = tuple(n.block.name for n in tree.nodes.values())
            return hash(node_ids)
        except:
            return id(tree)  # fallback

    def _normalized_cost(self, tree: BTree) -> float:
        """Normalized cost with caching"""
        tree_hash = self._get_tree_hash(tree)

        if tree_hash in self._pack_cache:
            self._cache_hits += 1
            return self._pack_cache[tree_hash]

        self._cache_misses += 1
        cost = self.cost_func(tree)

        if self.A_norm is None:
            self.A_norm = max(cost, 1e-9)

        norm_cost = cost / self.A_norm
        self._pack_cache[tree_hash] = norm_cost
        return norm_cost

    def _clear_cache(self):
        """清空缓存（温度级切换时）"""
        self._pack_cache.clear()

    def _perturbation_with_undo(self, tree: BTree) -> Tuple[callable, dict]:
        """
        Apply perturbation and return undo function

        Returns:
            (undo_func, undo_data)
        """
        r = random.random()

        if r < 0.1:  # Op1: rotate
            node = random.choice(list(tree.nodes.values()))
            old_w, old_h = node.block.w, node.block.h
            node.block.rotate()

            def undo():
                node.block.w, node.block.h = old_w, old_h

            return undo, {'op': 'rotate', 'node': node}

        elif r < 0.6:  # Op2: delete-insert (most disruptive)
            # For now, still use deepcopy for this complex op
            # TODO: implement proper undo for tree restructure
            return None, {'op': 'delete_insert'}

        else:  # Op3: swap
            if len(tree.nodes) < 2:
                return lambda: None, {'op': 'swap_skip'}

            nodes = list(tree.nodes.values())
            n1, n2 = random.sample(nodes, 2)
            b1, b2 = n1.block, n2.block
            n1.block, n2.block = b2, b1

            def undo():
                n1.block, n2.block = b1, b2

            return undo, {'op': 'swap', 'nodes': (n1, n2)}

    def _run_temperature_level_optimized(
        self,
        tree: BTree,
        T: float,
        L: int,
        best_tree: BTree,
        best_cost: float
    ) -> Tuple[BTree, float, List[float], BTree, float]:
        """
        Optimized temperature level - 原地修改 + 撤销
        """
        deltas = []
        current_cost = self._normalized_cost(tree)

        for _ in range(L):
            # Apply perturbation in-place
            undo_func, undo_data = self._perturbation_with_undo(tree)

            if undo_func is None:
                # Fallback to deepcopy for complex ops
                candidate_tree = copy.deepcopy(tree)
                from operators import op2_delete_insert
                op2_delete_insert(candidate_tree)
                candidate_cost = self._normalized_cost(candidate_tree)

                accept = False
                if candidate_cost < current_cost:
                    accept = True
                    deltas.append(abs(candidate_cost - current_cost))
                else:
                    delta = candidate_cost - current_cost
                    if random.random() < math.exp(-delta / T):
                        accept = True
                        deltas.append(delta)

                if accept:
                    tree = candidate_tree
                    current_cost = candidate_cost

                    raw_cost = self.cost_func(tree)
                    if raw_cost < best_cost:
                        best_cost = raw_cost
                        best_tree = copy.deepcopy(tree)

                continue

            # Evaluate perturbed tree (in-place)
            candidate_cost = self._normalized_cost(tree)

            accept = False
            if candidate_cost < current_cost:
                accept = True
                deltas.append(abs(candidate_cost - current_cost))
            else:
                delta = candidate_cost - current_cost
                if random.random() < math.exp(-delta / T):
                    accept = True
                    deltas.append(delta)

            if accept:
                # Keep the change
                current_cost = candidate_cost

                # Update best
                raw_cost = self.cost_func(tree)
                if raw_cost < best_cost:
                    best_cost = raw_cost
                    best_tree = copy.deepcopy(tree)
            else:
                # Reject: undo the change
                undo_func()

        # EMA smoothing
        if deltas:
            avg_delta = sum(deltas) / len(deltas)
        else:
            avg_delta = 0.001

        if self._ema_delta is None:
            self._ema_delta = avg_delta
        else:
            self._ema_delta = (
                self.ema_alpha * avg_delta +
                (1.0 - self.ema_alpha) * self._ema_delta
            )

        return tree, self._ema_delta, deltas, best_tree, best_cost

    def run(
        self,
        initial_tree: BTree,
        seed: int = 42,
        verbose: bool = False,
        T_final: float = None,
        max_no_improve: int = None,
        L_factor: int = None
    ) -> Dict:
        """Run optimized Fast-SA"""
        random.seed(seed)

        T_final = T_final if T_final is not None else SA_PARAMS['T_final']
        max_no_improve = max_no_improve if max_no_improve is not None else SA_PARAMS['max_no_improve']
        L_factor = L_factor if L_factor is not None else SA_PARAMS['L_factor']

        start_time = time.time()

        if verbose:
            print("=" * 60)
            print("Fast-SA Optimization (Optimized Version)")
            print("=" * 60)

        # Phase 1: Compute normalization
        self.A_norm = self.cost_func(initial_tree)

        # Phase 2: Initialize temperature
        T1, delta_avg = self._initialize_temperature(initial_tree, L_factor, verbose)

        # Phase 3: Main SA loop
        T = T1
        current_tree = copy.deepcopy(initial_tree)
        best_tree = copy.deepcopy(initial_tree)
        best_cost = self.cost_func(initial_tree)

        convergence = [best_cost]
        n = 1
        no_improve_count = 0
        avg_delta_n = delta_avg

        if verbose:
            print(f"\n[Phase 3] Main optimization (optimized - no deepcopy per iteration)")
            print(f"  Initial cost: {best_cost:.2f}")
            print(f"  Cache: enabled")
            print()

        while T > T_final and no_improve_count < max_no_improve:
            L = L_factor * len(self.blocks)

            # Clear cache每10级
            if n % 10 == 0:
                self._clear_cache()

            current_tree, avg_delta_n_new, deltas, best_tree, best_cost_new = \
                self._run_temperature_level_optimized(current_tree, T, L, best_tree, best_cost)

            if best_cost_new < best_cost:
                improvement = best_cost - best_cost_new
                if verbose:
                    print(f"  Level {n:3d}: T={T:8.4f}, Cost={best_cost_new:8.2f}, "
                          f"Improved by {improvement:6.2f} [cache: {self._cache_hits}/{self._cache_hits+self._cache_misses}]")
                best_cost = best_cost_new
                no_improve_count = 0
            else:
                no_improve_count += 1

            convergence.append(best_cost)
            avg_delta_n = max(avg_delta_n_new, 0.01)
            n += 1

            if 2 <= n <= self.k:
                T = T1 * avg_delta_n / (n * self.c)
            else:
                T = T1 * avg_delta_n / n

        # Metrics
        W, H, R = best_tree.pack()
        total_area = sum(b.area for b in self.blocks)
        deadspace = ((W * H - total_area) / (W * H)) * 100
        elapsed_time = time.time() - start_time

        if verbose:
            print(f"\n  Cache hit rate: {self._cache_hits/(self._cache_hits+self._cache_misses)*100:.1f}%")
            print(f"  Final: W={W:.1f}, H={H:.1f}, DS={deadspace:.2f}%, R={R:.3f}")
            print(f"  Time: {elapsed_time:.2f}s")
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
            'convergence': convergence,
            'cache_hit_rate': self._cache_hits/(self._cache_hits+self._cache_misses) if self._cache_misses > 0 else 0
        }

    def _initialize_temperature(self, tree: BTree, L_factor: int, verbose: bool) -> Tuple[float, float]:
        """Initialize T1 from random sampling"""
        if verbose:
            print("[Phase 2] Initializing temperature...")

        L_init = L_factor * len(self.blocks)
        deltas = []
        test_tree = copy.deepcopy(tree)

        for _ in range(L_init):
            undo_func, _ = self._perturbation_with_undo(test_tree)
            if undo_func:
                cost_after = self._normalized_cost(test_tree)
                undo_func()
                cost_before = self._normalized_cost(test_tree)
                deltas.append(abs(cost_after - cost_before))

        if deltas:
            delta_avg = sum(deltas) / len(deltas)
        else:
            delta_avg = 0.1

        T1 = delta_avg / abs(math.log(self.P))

        if verbose:
            print(f"  T1 = {T1:.4f}")
            print(f"  delta_avg = {delta_avg:.4f}")

        return T1, delta_avg
