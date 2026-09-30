# -*- coding: utf-8 -*-
"""m2_sa.py — Q2 独立实现 阶段P3/P4：成本函数 + Fast-SA（几何冷却）
成本 Φ = W/W_norm + λ·max(0,(M−S)/S)，M²=A·R 恒等式隐含。
- best 只记可行解（M≤S）
- 两阶段 λ：Phase1 高 λ 拉回轮廓，Phase2 低 λ 自适应优化线长
- 几何冷却（Q1 教训：Fast-SA c=100 在归一化下冻结）
"""
import copy
import math
import random
import time
from m_btree import BTree
from m_operators import random_perturbation
from m2_data import Block, load
from m2_hpwl import evaluate, terminal_vs_internal, pack_dims

Q2_PROBS = (0.2, 0.4, 0.4)  # 旋转 0.2（双效算子，Q2 特殊）


class Q2Cost:
    """成本函数：线长主目标 + 轮廓软惩罚。"""

    def __init__(self, data, blk, w_norm, lam_fn):
        self.data = data
        self.blk = blk
        self.w_norm = w_norm
        self.S = data['side']
        self.lam_fn = lam_fn
        self.n_eval = 0
        self.feas_cnt = 0

    def __call__(self, tree):
        W, H, _ = tree.pack()
        pos, sizes, W2, H2 = tree_to_posrot(tree, self.blk, self.data)
        wl, _, _ = evaluate(self.data, pos, sizes=sizes)
        M = max(W2, H2)
        feas = M <= self.S + 1e-9
        penalty = max(0.0, (M - self.S) / self.S)
        lam = self.lam_fn()
        cost = wl / self.w_norm + lam * penalty
        self.n_eval += 1
        if feas:
            self.feas_cnt += 1
        return cost, feas, wl, M

    def feasible_rate(self):
        return self.feas_cnt / max(self.n_eval, 1)


def tree_to_posrot(tree, blk, data):
    """tree 布局 → (pos, sizes, W, H)。sizes[name] = 当前方向 (w,h)。
    不推断 rot（B*-Tree 的 block 尺寸即当前方向，预旋转会误判）。
    必须先 pack() 填充 node.x/y，否则 get_layout 全 0（假值）。返回 W,H 免二次 pack。"""
    W, H, _ = tree.pack()
    layout = tree.get_layout()
    pos, sizes = {}, {}
    for idx, x, y, w, h in layout:
        name = blk[idx].name
        pos[name] = (x, y)
        sizes[name] = (w, h)
    return pos, sizes, W, H


def greedy_solve(data, blk, tree, seed=42, n_iter=30000, climbing=False,
                 T_climb=0.0, verbose=False):
    """贪心可行下降：cur 只在可行空间（M≤S），接受线长改善扰动。
    climbing=True 时接受少量 wl 升（爬山跳出局部，T_climb 相对 wl 量级）。
    贪心证明 > SA 温度（Q2 独立发现：可行内下降路径丰富，温度是负资产）。"""
    random.seed(seed)
    S = data['side']
    cur = copy.deepcopy(tree)
    pos, sizes, W0, H0 = tree_to_posrot(cur, blk, data)
    cur_wl, _, _ = evaluate(data, pos, sizes=sizes)
    best_tree, best_wl = copy.deepcopy(cur), cur_wl
    accept = 0
    for i in range(n_iter):
        cand = copy.deepcopy(cur)
        random_perturbation(cand, probs=Q2_PROBS)
        pos, sizes, W, H = tree_to_posrot(cand, blk, data)
        wl, _, _ = evaluate(data, pos, sizes=sizes)
        if max(W, H) > S:
            continue
        if wl < cur_wl:
            cur, cur_wl = cand, wl
            accept += 1
            if wl < best_wl:
                best_wl = wl
                best_tree = copy.deepcopy(cand)
        elif climbing and T_climb > 0 and random.random() < math.exp(-(wl - cur_wl) / T_climb):
            cur, cur_wl = cand, wl
    return best_tree, best_wl, accept


def compute_w_norm(data, blk, initial_tree, n_samples=500, seed=42):
    """SA 前试扰动 n 次的平均 HPWL = 归一化因子。"""
    random.seed(seed)
    wls = []
    cur = copy.deepcopy(initial_tree)
    for _ in range(n_samples):
        random_perturbation(cur, probs=Q2_PROBS)
        pos, sizes, _, _ = tree_to_posrot(cur, blk, data)
        wl, _, _ = evaluate(data, pos, sizes=sizes)
        wls.append(wl)
    return sum(wls) / len(wls)


class TwoPhaseLambda:
    """两阶段 λ：Phase1 固定高 λ 拉回轮廓；Phase2 自适应（可行率驱动）。"""

    def __init__(self, n_phases, phase1_ratio=0.3, lam_p1=5.0,
                 lam_p2_init=0.5, window=300, th_high=0.8, th_low=0.35,
                 lam_min=0.05, lam_max=8.0):
        self.phase1_end = int(n_phases * phase1_ratio)
        self.lam_p1 = lam_p1
        self.lam = lam_p2_init
        self.window = []
        self.win = window
        self.th_hi, self.th_lo = th_high, th_low
        self.lo, self.hi = lam_min, lam_max
        self.iter = 0
        self.in_phase1 = True
        self.history = []

    def __call__(self):
        if self.in_phase1:
            return self.lam_p1
        return self.lam

    def record(self, is_feasible):
        self.iter += 1
        if self.iter >= self.phase1_end and self.in_phase1:
            self.in_phase1 = False
            self.window = []
            print(f'    [λ] 进入 Phase2，λ={self.lam:.3f}')
        if not self.in_phase1:
            self.window.append(1 if is_feasible else 0)
            if len(self.window) > self.win:
                self.window.pop(0)
            if len(self.window) == self.win:
                fr = sum(self.window) / self.win
                if fr > self.th_hi:
                    self.lam = max(self.lo, self.lam / 1.5)
                elif fr < self.th_lo:
                    self.lam = min(self.hi, self.lam * 1.5)
                self.history.append((self.iter, fr, self.lam))


class FastSA2:
    """几何冷却 Fast-SA。best 只记可行解。返回完整 trace。"""

    def __init__(self, cost, P=0.9, ema_alpha=0.3):
        self.cost = cost
        self.P = P
        self.ema_alpha = ema_alpha
        self._ema = None

    def _sample_t1(self, tree):
        """T1 采样基于线长 delta（剥离惩罚）——惩罚主导会让 T1 过大 → 随机游走退化。
        与运行 cost 分离：温度反映线长优化尺度，超轮廓惩罚在运行中自动拒绝。"""
        deltas = []
        cur = copy.deepcopy(tree)
        _, _, old_wl, _ = self.cost(cur)
        for _ in range(100):
            random_perturbation(cur, probs=Q2_PROBS)
            _, _, new_wl, _ = self.cost(cur)
            deltas.append(abs(new_wl - old_wl) / self.cost.w_norm)
            old_wl = new_wl
        avg = sum(deltas) / max(len(deltas), 1)
        return avg / abs(math.log(self.P)), avg

    def run(self, initial_tree, seed=42, L_factor=10, max_levels=40,
            max_no_improve=20, verbose=True):
        random.seed(seed)
        t0 = time.time()
        T1, avg_d = self._sample_t1(initial_tree)
        T_final = T1 * 0.02
        alpha = (T_final / T1) ** (1.0 / max_levels) if T1 > 0 else 0.9
        self._ema = None
        T = T1

        # best 只记可行
        c0, f0, wl0, M0 = self.cost(initial_tree)
        if f0:
            best_tree, best_cost, best_wl, best_M = copy.deepcopy(initial_tree), c0, wl0, M0
        else:
            best_tree, best_cost, best_wl, best_M = None, float('inf'), float('inf'), float('inf')

        cur = copy.deepcopy(initial_tree)
        cur_cost = c0
        n, no_improve = 1, 0
        trace = [(0, T, best_wl if best_tree else float('inf'), best_M)]

        if verbose:
            print(f'  T1={T1:.4f} α={alpha:.3f} | 初始cost={c0:.4f} 可行={f0} W={M0:.0f}/S={self.cost.S:.0f}')

        while T > T_final and no_improve < max_no_improve and n <= max_levels:
            L = L_factor * len(self.cost.blk)
            deltas = []
            for _ in range(L):
                cand = copy.deepcopy(cur)
                random_perturbation(cand, probs=Q2_PROBS)
                c_cost, c_feas, c_wl, c_M = self.cost(cand)
                self.cost.lam_fn.record(c_feas)  # λ 管理器推进阶段/窗口
                # 可行性硬门：cur 只在可行空间移动，温度控制可行内探索（爬山）
                d = c_cost - cur_cost
                if c_feas and (d < 0 or random.random() < math.exp(-d / max(T, 1e-12))):
                    cur, cur_cost = cand, c_cost
                    deltas.append(abs(d))
                    if c_cost < best_cost:
                        best_cost, best_wl, best_M = c_cost, c_wl, c_M
                        best_tree = copy.deepcopy(cand)
            avg_d = sum(deltas) / len(deltas) if deltas else 0.001
            self._ema = self.ema_alpha * avg_d + (1 - self.ema_alpha) * (self._ema or avg_d)
            trace.append((n, T, best_wl if best_tree else float('inf'), best_M))
            if best_wl < trace[-2][2]:
                no_improve = 0
            else:
                no_improve += 1
            T *= alpha
            n += 1
            if verbose and n % 5 == 0:
                fr = self.cost.feasible_rate()
                print(f'    级{n:2d}: T={T:.5f} best_wl={best_wl:,.0f} best_M={best_M:.0f} 可行率={fr:.1%}')

        dt = time.time() - t0
        if best_tree:
            W, H, R = best_tree.pack()
            pos, sizes, _, _ = tree_to_posrot(best_tree, self.cost.blk, self.cost.data)
            io_t, in_t = terminal_vs_internal(self.cost.data, pos, sizes=sizes)
            print(f'  完成: {n-1}级 best_wl={best_wl:,.0f} M={best_M:.0f}/{self.cost.S:.0f} '
                  f'I/O={io_t:,.0f} 内部={in_t:,.0f} 用时={dt:.1f}s')
            return {'best_tree': best_tree, 'best_wl': best_wl, 'best_M': best_M,
                    'W': W, 'H': H, 'R': R, 'levels': n - 1, 'time': dt,
                    'trace': trace, 'io': io_t, 'internal': in_t, 'feasible': True}
        print(f'  失败: {n-1}级 无可行解 用时={dt:.1f}s')
        return {'best_tree': None, 'best_wl': float('inf'), 'best_M': None,
                'W': 0, 'H': 0, 'R': 0, 'levels': n - 1, 'time': dt,
                'trace': trace, 'io': 0, 'internal': 0, 'feasible': False}


if __name__ == '__main__':
    print('=== 阶段P3/P4: 成本 + SA 模块就绪 ===')
    # 冒烟测试
    from m2_init import orders, construct
    d = load('n100')
    blk = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(d['blocks'].items())]
    tree, _ = construct(d, orders(d, blk)['pref_y'], blk)
    wn = compute_w_norm(d, blk, tree, n_samples=50)
    lam = TwoPhaseLambda(40, lam_p1=5.0)
    cost = Q2Cost(d, blk, wn, lam)
    print(f'W_norm={wn:,.0f}')
    c, f, wl, M = cost(tree)
    print(f'初始: cost={c:.4f} 可行={f} wl={wl:,.0f} M={M:.0f}/{d["side"]:.0f}')
    print('阶段P3/P4: OK')
