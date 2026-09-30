"""
m_fastsa.py — 独立实现 阶段E：Fast-SA 修正版
建模手 F16 初始温度 + F20 归一化，修复编程手 R1-R4。

温度调度修正（独立发现）：
  建模手 F17/F18 的 c=100 快冷在归一化 delta≈0.05 尺度下瞬间冻结温度
  （n=2 后 T≈1.2e-4，接受率→0，SA 退化为贪心+早停，只跑 1-2 级）。
  编程手 phase1 只跑 2 级、A_opt=初始面积，正是此失效。
  独立实现改用 F16 定 T1 + 平滑几何冷却 T_n = T1·α^n，
  保留"高温撒网→渐冷→低温细搜"的 SA 本质，不依赖 delta 尺度假设。

修正点：
  R1: cost_func 已分项归一化(O(1)) → T1 采样直接对归一化 delta，无惩罚爆炸
  R3: 温度采样与运行同一量级（全归一化），温度平滑下降不冻结
  R4: max_no_improve=20 + T_final=0.01 + max_levels=40，不激进早停
  best-so-far: 记归一化 cost 最小值对应的树
"""
import copy
import math
import random
import time
from typing import Callable, Dict, Optional
from m_btree import BTree
from m_operators import random_perturbation


class FastSA:
    def __init__(self, blocks, cost_func: Callable[[BTree], float], P: float = 0.9,
                 k: int = 7, c: float = 100.0, ema_alpha: float = 0.3):
        self.blocks = blocks
        self.cost_func = cost_func
        self.P = P
        self.k = k
        self.c = c
        self.ema_alpha = ema_alpha
        self._ema = None
        self.trace = []  # (level, T, best_cost)

    def _sample_t1(self, tree: BTree) -> float:
        """对归一化 cost 采样 delta → T1。与运行同量级（R3 修复）。"""
        deltas = []
        cur = copy.deepcopy(tree)
        old = self.cost_func(cur)
        for _ in range(100):
            random_perturbation(cur)
            new = self.cost_func(cur)
            deltas.append(abs(new - old))
            old = new
        avg = sum(deltas) / max(len(deltas), 1)
        return avg / abs(math.log(self.P)), avg

    def _level(self, tree: BTree, T: float, L: int, best_tree, best_cost):
        deltas = []
        cur = copy.deepcopy(tree)
        cur_cost = self.cost_func(cur)
        for _ in range(L):
            cand = copy.deepcopy(cur)
            random_perturbation(cand)
            c_cost = self.cost_func(cand)
            d = c_cost - cur_cost
            if d < 0 or random.random() < math.exp(-d / max(T, 1e-12)):
                cur, cur_cost = cand, c_cost
                deltas.append(abs(d))
                if cur_cost < best_cost:
                    best_cost = cur_cost
                    best_tree = copy.deepcopy(cur)
        avg_d = sum(deltas) / len(deltas) if deltas else 0.001
        if self._ema is None:
            self._ema = avg_d
        else:
            self._ema = self.ema_alpha * avg_d + (1 - self.ema_alpha) * self._ema
        return cur, self._ema, best_tree, best_cost

    def run(self, initial_tree: BTree, seed: int = 42, L_factor: int = 10,
            T_final: float = None, max_no_improve: int = 20, max_levels: int = 40,
            verbose: bool = True) -> Dict:
        random.seed(seed)
        t0 = time.time()
        T1, _ = self._sample_t1(initial_tree)
        # 几何冷却：T_final 相对 T1（T1×0.02），保证温度平滑降不冻结
        if T_final is None:
            T_final = T1 * 0.02
        alpha = (T_final / T1) ** (1.0 / max_levels) if T1 > 0 else 0.9
        self._ema = None
        T = T1
        best_tree = copy.deepcopy(initial_tree)
        best_cost = self.cost_func(initial_tree)
        cur = copy.deepcopy(initial_tree)
        n = 1
        no_improve = 0
        self.trace = [(0, T, best_cost)]

        if verbose:
            print(f"  T1={T1:.4f} T_final={T_final:.4f} α={alpha:.3f} | 初始cost={best_cost:.4f}")

        while T > T_final and no_improve < max_no_improve and n <= max_levels:
            L = L_factor * len(self.blocks)
            cur, avg_d, best_tree, best_cost = self._level(cur, T, L, best_tree, best_cost)
            self.trace.append((n, T, best_cost))

            old_cost = self.trace[-2][2] if len(self.trace) > 1 else float('inf')
            if best_cost < old_cost:
                no_improve = 0
            else:
                no_improve += 1

            T = T * alpha
            n += 1
            if verbose and n % 5 == 0:
                print(f"    级{n:2d}: T={T:.4f} best={best_cost:.4f}")

        W, H, R = best_tree.pack()
        dt = time.time() - t0
        if verbose:
            print(f"  完成: {n-1}级 T={T:.4f} cost={best_cost:.4f} W={W:.0f} H={H:.0f} R={R:.3f} 用时={dt:.1f}s")
        return {'best_tree': best_tree, 'cost': best_cost, 'W': W, 'H': H, 'R': R,
                'levels': n - 1, 'time': dt, 'trace': self.trace}


def solve_two_phase(blocks, initial_tree, seed: int = 42, eps: float = 0.01, mu: float = 10.0,
                    Phi_norm: Optional[float] = None, verbose: bool = True) -> Dict:
    """两阶段：Phase1 纯面积 → A_opt；Phase2 min-max+软惩罚。建模手 M2。"""
    from m_cost import phase1_cost, phase2_cost
    A_total = sum(b.area for b in blocks)

    if verbose:
        print("[Phase1] 纯面积最小化")
    def c1(tree):
        W, H, _ = tree.pack()
        return phase1_cost(W * H, A_total)
    r1 = FastSA(blocks, c1).run(initial_tree, seed=seed, verbose=verbose)
    A_opt = r1['best_tree'].pack()[0] * r1['best_tree'].pack()[1]
    if Phi_norm is None:
        Phi_norm = max(A_opt ** 0.5, 1.0)  # 初始解 max 边长近似

    if verbose:
        print(f"  A_opt={A_opt:.0f} (死区={(A_opt-A_total)/A_opt*100:.2f}%)")
        print("[Phase2] min-max + 面积软惩罚")

    def c2(tree):
        W, H, _ = tree.pack()
        return phase2_cost(W, H, A_opt, A_total, Phi_norm, eps=eps, mu=mu)
    r2 = FastSA(blocks, c2).run(r1['best_tree'], seed=seed + 1, verbose=verbose)

    W, H, R = r2['best_tree'].pack()
    A_final = W * H
    return {'best_tree': r2['best_tree'], 'A_opt': A_opt, 'A_final': A_final,
            'W': W, 'H': H, 'R': R, 'area': A_final,
            'gap_pct': (A_final - A_opt) / A_opt * 100,
            'deadspace': (A_final - A_total) / A_final * 100,
            'levels': r1['levels'] + r2['levels'],
            'time': r1['time'] + r2['time'],
            'phase1': r1, 'phase2': r2}


if __name__ == '__main__':
    import os
    from m_data import load_blocks
    from m_construct import construct_initial_tree
    BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"
    blk = load_blocks(os.path.join(BASE, 'n100.blocks'))
    A_total = sum(b.area for b in blk)

    print("=== 阶段E: Fast-SA 修正版（n100）===")
    init = construct_initial_tree(blk, method='ffd')
    W0, H0, _ = init.pack()
    print(f"[初始 FFD] W={W0:.0f} H={H0:.0f} max={max(W0,H0):.0f} 死区={(W0*H0-A_total)/(W0*H0)*100:.2f}%")

    res = solve_two_phase(blk, init, seed=42, verbose=True)
    print(f"\n[两阶段结果] A_opt={res['A_opt']:.0f} A_final={res['A_final']:.0f} "
          f"W={res['W']:.0f} H={res['H']:.0f} R={res['R']:.3f} gap={res['gap_pct']:.2f}% "
          f"死区={res['deadspace']:.2f}% 总级数={res['levels']} 用时={res['time']:.1f}s")
