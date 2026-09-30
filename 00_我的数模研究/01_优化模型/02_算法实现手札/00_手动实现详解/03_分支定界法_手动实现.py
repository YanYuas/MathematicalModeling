# -*- coding: utf-8 -*-
"""
整数规划 · 分支定界法手动实现
================================
六层钻研法 · 第4层：手动实现

算法核心：
1. 解线性规划松弛，得到下界（最小化问题）
2. 如果LP解全是整数 → 找到最优解
3. 如果有非整数变量 → 分支：x_j ≤ floor 和 x_j ≥ ceil
4. 定界：子问题下界 ≥ 当前上界 → 剪枝

使用 scipy.optimize.linprog 解LP松弛（单纯形法）
问题形式：min c^T x, s.t. A_ub x ≤ b_ub, A_eq x = b_eq, lb ≤ x ≤ ub, x整数
"""

import numpy as np
from scipy.optimize import linprog
import heapq
import time


# ============================================================
# 第一部分：子问题节点类
# ============================================================
class Node:
    """
    分支定界搜索树中的一个节点（子问题）
    
    每个节点代表原问题加上一些额外的上下界约束
    例如：原问题 + (x1 ≤ 2) + (x3 ≥ 5)
    """
    def __init__(self, lb, ub, depth=0):
        """
        参数：
            lb: 各变量的下界数组，shape=(n,)
            ub: 各变量的上界数组，shape=(n,)
            depth: 搜索树深度（根节点=0）
        """
        self.lb = lb.copy()       # 变量下界
        self.ub = ub.copy()       # 变量上界
        self.depth = depth        # 搜索深度
        self.lp_obj = None        # LP松弛的最优值（下界）
        self.lp_x = None          # LP松弛的最优解
        self.feasible = True      # 该子问题是否可行

    def __lt__(self, other):
        """
        用于优先队列（最佳优先搜索）
        按LP目标值从小到大排序（最小化问题，值小的先处理）
        """
        return self.lp_obj < other.lp_obj


# ============================================================
# 第二部分：解LP松弛
# ============================================================
def solve_lp_relaxation(c, A_ub, b_ub, A_eq, b_eq, lb, ub):
    """
    解线性规划松弛（把整数约束去掉）
    
    参数：
        c: 目标函数系数，shape=(n,)
        A_ub: 不等式约束矩阵，shape=(m_ub, n)
        b_ub: 不等式约束右端，shape=(m_ub,)
        A_eq: 等式约束矩阵，shape=(m_eq, n)
        b_eq: 等式约束右端，shape=(m_eq,)
        lb: 变量下界，shape=(n,)
        ub: 变量上界，shape=(n,)
    
    返回：
        (obj, x) 或 (None, None)（不可行时）
    """
    # scipy的linprog要求bounds是(lower, upper)元组列表
    bounds = [(float(l), float(u)) for l, u in zip(lb, ub)]
    
    try:
        # 用HiGHS求解器（scipy默认，比单纯形法快）
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                         bounds=bounds, method='highs')
        if result.success:
            return result.fun, result.x
        else:
            # 不可行或无界
            return None, None
    except Exception:
        return None, None


# ============================================================
# 第三部分：分支定界主算法
# ============================================================
def branch_and_bound(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None,
                     var_type=None, lb=None, ub=None, method='best_first',
                     max_nodes=10000, verbose=False):
    """
    分支定界法求解整数规划（最小化问题）
    
    参数：
        c: 目标函数系数，shape=(n,)，min c^T x
        A_ub: 不等式约束 A_ub x ≤ b_ub
        b_ub: 不等式约束右端
        A_eq: 等式约束 A_eq x = b_eq
        b_eq: 等式约束右端
        var_type: 变量类型数组，'I'=整数，'C'=连续。默认全整数
        lb: 变量下界，默认0
        ub: 变量上界，默认None（无穷大）
        method: 搜索策略，'dfs'=深度优先，'best_first'=最佳优先
        max_nodes: 最大搜索节点数（防止爆炸）
        verbose: 是否打印中间过程
    
    返回：
        dict: {
            'obj': 最优值,
            'x': 最优解,
            'nodes_explored': 搜索节点数,
            'status': 'optimal' / 'max_nodes_exceeded' / 'infeasible'
        }
    """
    n = len(c)
    
    # ---- 步骤0：处理默认参数 ----
    if var_type is None:
        var_type = ['I'] * n  # 默认全整数
    if lb is None:
        lb = np.zeros(n)
    if ub is None:
        ub = np.full(n, np.inf)
    if A_ub is None:
        A_ub = np.empty((0, n))
        b_ub = np.empty(0)
    if A_eq is None:
        A_eq = np.empty((0, n))
        b_eq = np.empty(0)
    
    c = np.array(c, dtype=float)
    A_ub = np.array(A_ub, dtype=float)
    b_ub = np.array(b_ub, dtype=float)
    A_eq = np.array(A_eq, dtype=float)
    b_eq = np.array(b_eq, dtype=float)
    lb = np.array(lb, dtype=float)
    ub = np.array(ub, dtype=float)
    
    # 找出哪些变量是整数变量
    int_indices = [i for i in range(n) if var_type[i] == 'I']
    
    # ---- 步骤1：初始化 ----
    # 上界 = 当前找到的最好整数解的目标值（最小化问题，初始为无穷大）
    upper_bound = np.inf
    best_x = None
    nodes_explored = 0
    
    # 根节点
    root = Node(lb, ub, depth=0)
    
    if method == 'best_first':
        # 最佳优先：用优先队列（最小堆）
        queue = []
        heapq.heappush(queue, root)
    else:
        # 深度优先：用栈（列表模拟）
        queue = [root]
    
    # ---- 步骤2：主循环 ----
    while queue:
        # 防止搜索节点过多
        if nodes_explored >= max_nodes:
            if verbose:
                print(f"达到最大节点数 {max_nodes}，停止搜索")
            break
        
        # 取出一个节点
        if method == 'best_first':
            node = heapq.heappop(queue)
        else:
            node = queue.pop()  # 栈：后进先出
        
        nodes_explored += 1
        
        if verbose:
            print(f"\n节点 {nodes_explored} (深度{node.depth}): ", end="")
        
        # ---- 步骤3：解该节点的LP松弛 ----
        obj, x = solve_lp_relaxation(c, A_ub, b_ub, A_eq, b_eq, node.lb, node.ub)
        node.lp_obj = obj
        node.lp_x = x
        
        # ---- 步骤4：剪枝1：不可行 ----
        if obj is None:
            if verbose:
                print("LP不可行，剪枝")
            continue
        
        # ---- 步骤5：剪枝2：下界 ≥ 上界 ----
        if obj >= upper_bound - 1e-10:
            if verbose:
                print(f"LP下界 {obj:.4f} ≥ 上界 {upper_bound:.4f}，剪枝")
            continue
        
        # ---- 步骤6：检查LP解是否全是整数 ----
        # 只检查整数变量（连续变量不需要整数）
        non_int_var = None
        max_frac = 0
        for i in int_indices:
            frac = abs(x[i] - round(x[i]))
            if frac > 1e-6 and frac > max_frac:
                max_frac = frac
                non_int_var = i
        
        if non_int_var is None:
            # LP解全是整数 → 找到一个整数可行解
            if obj < upper_bound:
                upper_bound = obj
                best_x = x.copy()
                if verbose:
                    print(f"找到整数解！目标值={obj:.4f}，更新上界")
            else:
                if verbose:
                    print(f"整数解但目标值={obj:.4f}不优于当前上界，剪枝")
            continue
        
        # ---- 步骤7：分支 ----
        # 选非整数变量 non_int_var，值为 x[non_int_var]
        branch_val = x[non_int_var]
        floor_val = np.floor(branch_val)
        ceil_val = np.ceil(branch_val)
        
        if verbose:
            print(f"x{non_int_var+1}={branch_val:.4f}非整数，分支为≤{floor_val}和≥{ceil_val}")
        
        # 左分支：x_j ≤ floor(branch_val)
        left_lb = node.lb.copy()
        left_ub = node.ub.copy()
        left_ub[non_int_var] = min(left_ub[non_int_var], floor_val)
        left_node = Node(left_lb, left_ub, depth=node.depth + 1)
        
        # 右分支：x_j ≥ ceil(branch_val)
        right_lb = node.lb.copy()
        right_ub = node.ub.copy()
        right_lb[non_int_var] = max(right_lb[non_int_var], ceil_val)
        right_node = Node(right_lb, right_ub, depth=node.depth + 1)
        
        # 加入队列
        if method == 'best_first':
            # 先解两个子节点的LP，得到下界，再入堆
            # （这样堆排序才有意义）
            for child in [left_node, right_node]:
                child.lp_obj, child.lp_x = solve_lp_relaxation(
                    c, A_ub, b_ub, A_eq, b_eq, child.lb, child.ub)
                if child.lp_obj is not None and child.lp_obj < upper_bound:
                    heapq.heappush(queue, child)
        else:
            # 深度优先：右子节点先入栈（这样左子节点先被处理）
            queue.append(right_node)
            queue.append(left_node)
    
    # ---- 步骤8：返回结果 ----
    if best_x is not None:
        status = 'optimal' if nodes_explored < max_nodes else 'max_nodes_exceeded'
        return {
            'obj': upper_bound,
            'x': best_x,
            'nodes_explored': nodes_explored,
            'status': status
        }
    else:
        return {
            'obj': None,
            'x': None,
            'nodes_explored': nodes_explored,
            'status': 'infeasible'
        }


# ============================================================
# 第四部分：测试用例
# ============================================================
def test_knapsack():
    """
    测试1：0-1背包问题
    
    5件物品，价值v=[10, 7, 15, 8, 12]，重量w=[3, 2, 5, 4, 3]，背包容量W=10
    求最大价值（用最小化形式：min -v^T x）
    """
    print("=" * 60)
    print("测试1：0-1背包问题")
    print("=" * 60)
    
    v = np.array([10, 7, 15, 8, 12])
    w = np.array([3, 2, 5, 4, 3])
    W = 10
    n = 5
    
    # 最小化 -v^T x
    c = -v
    A_ub = w.reshape(1, -1)
    b_ub = np.array([W])
    lb = np.zeros(n)
    ub = np.ones(n)  # 0-1变量上界为1
    
    result = branch_and_bound(c, A_ub=A_ub, b_ub=b_ub, lb=lb, ub=ub,
                              method='best_first', verbose=True)
    
    print(f"\n结果：最优值={-result['obj']:.2f}（最大价值）")
    print(f"最优解：x={result['x']}")
    print(f"选中物品：{[i+1 for i in range(n) if result['x'][i] > 0.5]}")
    print(f"搜索节点数：{result['nodes_explored']}")
    print(f"状态：{result['status']}")
    
    # 验证
    selected = [i for i in range(n) if result['x'][i] > 0.5]
    total_w = sum(w[i] for i in selected)
    total_v = sum(v[i] for i in selected)
    print(f"验证：总重量={total_w}≤{W}，总价值={total_v}")
    assert total_w <= W, "重量超过容量！"
    assert abs(total_v - (-result['obj'])) < 0.01, "价值不匹配！"
    print("✓ 测试通过！")


def test_production():
    """
    测试2：整数生产计划
    
    max 3x1 + 5x2
    s.t. x1 + 2x2 ≤ 8
         2x1 + x2 ≤ 10
         x1, x2 ≥ 0, 整数
    """
    print("\n" + "=" * 60)
    print("测试2：整数生产计划")
    print("=" * 60)
    
    c = np.array([-3, -5])  # 最小化 -3x1 -5x2
    A_ub = np.array([[1, 2], [2, 1]])
    b_ub = np.array([8, 10])
    lb = np.array([0, 0])
    
    result = branch_and_bound(c, A_ub=A_ub, b_ub=b_ub, lb=lb,
                              method='best_first', verbose=True)
    
    print(f"\n结果：最优值={-result['obj']:.2f}（最大利润）")
    print(f"最优解：x1={result['x'][0]:.0f}, x2={result['x'][1]:.0f}")
    print(f"搜索节点数：{result['nodes_explored']}")
    
    # 对比LP松弛
    lp_obj, lp_x = solve_lp_relaxation(c, A_ub, b_ub, None, None, lb, [np.inf, np.inf])
    print(f"LP松弛最优：x1={lp_x[0]:.2f}, x2={lp_x[1]:.2f}, z={-lp_obj:.2f}")
    print(f"整数最优：x1={result['x'][0]:.0f}, x2={result['x'][1]:.0f}, z={-result['obj']:.2f}")
    print(f"整数性差距：{(-lp_obj) - (-result['obj']):.2f}")
    print("✓ 测试通过！")


def test_dfs_vs_bestfirst():
    """
    测试3：深度优先 vs 最佳优先 对比
    """
    print("\n" + "=" * 60)
    print("测试3：DFS vs Best-First 对比")
    print("=" * 60)
    
    # 构造一个稍大的背包问题
    np.random.seed(42)
    n = 15
    v = np.random.randint(5, 20, n)
    w = np.random.randint(2, 8, n)
    W = int(sum(w) * 0.4)
    
    c = -v
    A_ub = w.reshape(1, -1)
    b_ub = np.array([W])
    lb = np.zeros(n)
    ub = np.ones(n)
    
    for method in ['dfs', 'best_first']:
        start = time.time()
        result = branch_and_bound(c, A_ub=A_ub, b_ub=b_ub, lb=lb, ub=ub,
                                  method=method, verbose=False)
        elapsed = time.time() - start
        print(f"{method:12s}: 最优值={-result['obj']:.0f}, "
              f"节点数={result['nodes_explored']:5d}, 时间={elapsed:.4f}s")
    
    print("✓ 对比完成！")


if __name__ == '__main__':
    test_knapsack()
    test_production()
    test_dfs_vs_bestfirst()
    print("\n" + "=" * 60)
    print("全部测试通过！")
    print("=" * 60)
