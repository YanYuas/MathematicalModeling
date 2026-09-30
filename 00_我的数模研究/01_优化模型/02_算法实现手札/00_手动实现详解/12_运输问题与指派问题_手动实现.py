# -*- coding: utf-8 -*-
"""
运输问题与指派问题 · 手动实现
==============================
六层钻研法 · 第4层：手动实现

1. 运输问题（表上作业法）
   - 初始解：最小元素法 / Vogel近似法
   - 最优性检验：位势法
   - 调整：闭回路法

2. 指派问题（匈牙利算法）
   - 行规约 + 列规约
   - 最少线覆盖所有0
   - 调整矩阵
"""

import numpy as np


# ============================================================
# 一、运输问题
# ============================================================
class TransportationProblem:
    """
    运输问题求解器（表上作业法）
    
    问题：m个产地，n个销地
    产地i产量a_i，销地j销量b_j，单位运费c_ij
    求最小总运费的运输方案
    
    假设：总产量 = 总销量（产销平衡）
    """
    
    def __init__(self, costs, supply, demand):
        """
        参数：
            costs: m×n 运费矩阵
            supply: m个产地的产量
            demand: n个销地的销量
        """
        self.costs = np.array(costs, dtype=float)
        self.supply = np.array(supply, dtype=float)
        self.demand = np.array(demand, dtype=float)
        self.m, self.n = self.costs.shape
        
        # 检查产销平衡
        total_supply = self.supply.sum()
        total_demand = self.demand.sum()
        if abs(total_supply - total_demand) > 1e-6:
            raise ValueError(f"产销不平衡：产量{total_supply}，销量{total_demand}")
    
    def solve_minimum_element(self):
        """
        最小元素法：初始基可行解
        
        核心：每次选运费最小的格子，尽可能多地分配。
        """
        supply = self.supply.copy()
        demand = self.demand.copy()
        allocation = np.zeros((self.m, self.n))
        
        while supply.sum() > 1e-6 and demand.sum() > 1e-6:
            # 找运费最小的可用格子
            min_cost = float('inf')
            min_i, min_j = -1, -1
            for i in range(self.m):
                if supply[i] <= 1e-6:
                    continue
                for j in range(self.n):
                    if demand[j] <= 1e-6:
                        continue
                    if self.costs[i][j] < min_cost:
                        min_cost = self.costs[i][j]
                        min_i, min_j = i, j
            
            if min_i == -1:
                break
            
            # 分配：取产量和销量的较小值
            amount = min(supply[min_i], demand[min_j])
            allocation[min_i][min_j] = amount
            supply[min_i] -= amount
            demand[min_j] -= amount
        
        return allocation
    
    def solve_vogel(self):
        """
        Vogel近似法（VAM）：初始基可行解
        
        核心：每次计算各行各列的最小和次小运费之差（罚数），
        选罚数最大的行/列中运费最小的格子分配。
        
        Vogel法通常比最小元素法更接近最优解。
        """
        supply = self.supply.copy()
        demand = self.demand.copy()
        allocation = np.zeros((self.m, self.n))
        
        while supply.sum() > 1e-6 and demand.sum() > 1e-6:
            # 计算各行罚数（最小和次小之差）
            row_penalty = []
            for i in range(self.m):
                if supply[i] <= 1e-6:
                    row_penalty.append(-1)
                    continue
                available = [self.costs[i][j] for j in range(self.n) if demand[j] > 1e-6]
                if len(available) >= 2:
                    available.sort()
                    row_penalty.append(available[1] - available[0])
                else:
                    row_penalty.append(0)
            
            # 计算各列罚数
            col_penalty = []
            for j in range(self.n):
                if demand[j] <= 1e-6:
                    col_penalty.append(-1)
                    continue
                available = [self.costs[i][j] for i in range(self.m) if supply[i] > 1e-6]
                if len(available) >= 2:
                    available.sort()
                    col_penalty.append(available[1] - available[0])
                else:
                    col_penalty.append(0)
            
            # 选罚数最大的
            max_row_penalty = max(row_penalty) if row_penalty else -1
            max_col_penalty = max(col_penalty) if col_penalty else -1
            
            if max_row_penalty >= max_col_penalty:
                # 在罚数最大的行中选运费最小的列
                i = row_penalty.index(max_row_penalty)
                j = min((j for j in range(self.n) if demand[j] > 1e-6),
                        key=lambda j: self.costs[i][j])
            else:
                # 在罚数最大的列中选运费最小的行
                j = col_penalty.index(max_col_penalty)
                i = min((i for i in range(self.m) if supply[i] > 1e-6),
                        key=lambda i: self.costs[i][j])
            
            amount = min(supply[i], demand[j])
            allocation[i][j] = amount
            supply[i] -= amount
            demand[j] -= amount
        
        return allocation
    
    def compute_potentials(self, allocation):
        """
        位势法：计算位势u_i, v_j和检验数
        
        对基变量（分配>0的格子）：c_ij = u_i + v_j
        检验数：sigma_ij = c_ij - u_i - v_j
        
        如果所有检验数 >= 0，则是最优解。
        """
        # 找基变量位置
        basis = []
        for i in range(self.m):
            for j in range(self.n):
                if allocation[i][j] > 1e-6:
                    basis.append((i, j))
        
        # 解位势方程：u_i + v_j = c_ij
        u = np.full(self.m, np.nan)
        v = np.full(self.n, np.nan)
        u[0] = 0  # 设u_0 = 0
        
        # 迭代求解（类似BFS）
        changed = True
        while changed:
            changed = False
            for i, j in basis:
                if not np.isnan(u[i]) and np.isnan(v[j]):
                    v[j] = self.costs[i][j] - u[i]
                    changed = True
                elif np.isnan(u[i]) and not np.isnan(v[j]):
                    u[i] = self.costs[i][j] - v[j]
                    changed = True
        
        # 计算检验数
        reduced_cost = np.zeros((self.m, self.n))
        for i in range(self.m):
            for j in range(self.n):
                if allocation[i][j] <= 1e-6:  # 非基变量
                    reduced_cost[i][j] = self.costs[i][j] - u[i] - v[j]
        
        return u, v, reduced_cost
    
    def find_loop(self, allocation, start_i, start_j):
        """
        找闭回路：从非基变量(start_i, start_j)出发，
        交替经过非基变量和基变量，回到起点。
        
        闭回路的顶点除了起点都是基变量。
        """
        # BFS找闭回路
        from collections import deque
        
        # 基变量位置集合
        basis_set = set()
        for i in range(self.m):
            for j in range(self.n):
                if allocation[i][j] > 1e-6:
                    basis_set.add((i, j))
        
        # 起点加入（作为非基变量）
        # BFS状态：(i, j, 方向, 路径)
        # 方向：0=水平移动，1=垂直移动
        queue = deque()
        # 从起点出发，可以水平或垂直移动
        for j in range(self.n):
            if j != start_j and (start_i, j) in basis_set:
                queue.append((start_i, j, 1, [(start_i, start_j), (start_i, j)]))
        for i in range(self.m):
            if i != start_i and (i, start_j) in basis_set:
                queue.append((i, start_j, 0, [(start_i, start_j), (i, start_j)]))
        
        while queue:
            i, j, direction, path = queue.popleft()
            
            # 下一步换方向
            if direction == 0:  # 上一步是垂直，下一步水平
                for nj in range(self.n):
                    if nj == j:
                        continue
                    if (i, nj) == (start_i, start_j) and len(path) >= 4:
                        return path + [(start_i, start_j)]
                    if (i, nj) in basis_set and (i, nj) not in path:
                        queue.append((i, nj, 1, path + [(i, nj)]))
            else:  # 上一步是水平，下一步垂直
                for ni in range(self.m):
                    if ni == i:
                        continue
                    if (ni, j) == (start_i, start_j) and len(path) >= 4:
                        return path + [(start_i, start_j)]
                    if (ni, j) in basis_set and (ni, j) not in path:
                        queue.append((ni, j, 0, path + [(ni, j)]))
        
        return None
    
    def optimize(self, initial_method='vogel'):
        """
        完整求解：初始解 → 检验 → 调整 → 最优
        
        返回：最优分配方案和最小总运费
        """
        # 第一步：初始基可行解
        if initial_method == 'vogel':
            allocation = self.solve_vogel()
        else:
            allocation = self.solve_minimum_element()
        
        iteration = 0
        while True:
            iteration += 1
            
            # 第二步：位势法计算检验数
            u, v, reduced_cost = self.compute_potentials(allocation)
            
            # 找最小检验数（最负的）
            min_rc = reduced_cost.min()
            if min_rc >= -1e-6:
                break  # 所有检验数>=0，最优
            
            # 找进基变量（检验数最负的格子）
            min_idx = np.unravel_index(reduced_cost.argmin(), reduced_cost.shape)
            enter_i, enter_j = min_idx
            
            # 第三步：找闭回路并调整
            loop = self.find_loop(allocation, enter_i, enter_j)
            if loop is None:
                break
            
            # 奇数位置（+调整量），偶数位置（-调整量）
            # 起点是+，下一个是-，交替
            minus_positions = loop[1::2]  # 第2,4,6...个顶点
            theta = min(allocation[i][j] for i, j in minus_positions)
            
            # 调整
            for k, (i, j) in enumerate(loop):
                if k % 2 == 0:
                    allocation[i][j] += theta
                else:
                    allocation[i][j] -= theta
        
        # 计算总运费
        total_cost = (allocation * self.costs).sum()
        return allocation, total_cost, iteration


# ============================================================
# 二、指派问题（匈牙利算法）
# ============================================================
def hungarian_assignment(cost_matrix):
    """
    匈牙利算法：求解最小费用指派问题
    
    问题：n个人n项任务，每人做一项，每项一人做，费用c_ij
    求最小总费用的指派方案。
    
    算法步骤：
    1. 行规约：每行减该行最小值
    2. 列规约：每列减该列最小值
    3. 用最少的线覆盖所有0元素
    4. 如果线数=n，找到最优解；否则调整矩阵，回到3
    """
    n = len(cost_matrix)
    cost = np.array(cost_matrix, dtype=float)
    
    # 第一步：行规约
    for i in range(n):
        cost[i] -= cost[i].min()
    
    # 第二步：列规约
    for j in range(n):
        cost[:, j] -= cost[:, j].min()
    
    # 主循环
    while True:
        # 第三步：用最少线覆盖所有0
        # 用匈牙利匹配的方式找最大匹配
        # 匹配数 = 最少覆盖线数（Konig定理）
        
        # 构建二分图：左边=行，右边=列，0元素=边
        graph_left = []
        for i in range(n):
            neighbors = [j for j in range(n) if abs(cost[i][j]) < 1e-6]
            graph_left.append(neighbors)
        
        # 匈牙利算法求最大匹配
        matching = [-1] * n  # matching[j] = 匹配到列j的行
        
        def try_match(u, visited):
            for v in graph_left[u]:
                if not visited[v]:
                    visited[v] = True
                    if matching[v] == -1 or try_match(matching[v], visited):
                        matching[v] = u
                        return True
            return False
        
        max_matching = 0
        for u in range(n):
            visited = [False] * n
            if try_match(u, visited):
                max_matching += 1
        
        # 如果最大匹配数=n，找到完美匹配（最优解）
        if max_matching == n:
            # 从matching还原指派方案
            assignment = [-1] * n
            for j in range(n):
                assignment[matching[j]] = j
            total_cost = sum(cost_matrix[i][assignment[i]] for i in range(n))
            return assignment, total_cost
        
        # 第四步：调整矩阵
        # 找未覆盖的最小元素
        # 标记：从所有未匹配的行出发，交替走未匹配边（0）和匹配边
        
        # 标记行和列
        marked_rows = set()
        marked_cols = set()
        
        # 未匹配的行
        unmatched_rows = set(range(n)) - set(matching[j] for j in range(n) if matching[j] != -1)
        marked_rows.update(unmatched_rows)
        
        changed = True
        while changed:
            changed = False
            # 从标记行出发，找0元素所在的未标记列
            for i in list(marked_rows):
                for j in range(n):
                    if abs(cost[i][j]) < 1e-6 and j not in marked_cols:
                        marked_cols.add(j)
                        changed = True
            # 从标记列出发，找匹配的行
            for j in list(marked_cols):
                if matching[j] != -1 and matching[j] not in marked_rows:
                    marked_rows.add(matching[j])
                    changed = True
        
        # 未覆盖的行 = 标记行，未覆盖的列 = 未标记列
        # 覆盖的行 = 未标记行，覆盖的列 = 标记列
        
        # 找未覆盖元素的最小值
        min_uncovered = float('inf')
        for i in range(n):
            if i in marked_rows:  # 未覆盖的行
                for j in range(n):
                    if j not in marked_cols:  # 未覆盖的列
                        if cost[i][j] < min_uncovered:
                            min_uncovered = cost[i][j]
        
        # 调整：未覆盖元素减最小值，交叉覆盖元素加最小值
        for i in range(n):
            for j in range(n):
                if i in marked_rows and j not in marked_cols:
                    cost[i][j] -= min_uncovered
                elif i not in marked_rows and j in marked_cols:
                    cost[i][j] += min_uncovered


# ============================================================
# 测试用例
# ============================================================
def test_transportation():
    print("=" * 60)
    print("测试1：运输问题")
    print("=" * 60)
    
    # 3个产地，4个销地
    costs = [
        [3, 11, 3, 10],
        [1, 9, 2, 8],
        [7, 4, 10, 5],
    ]
    supply = [7, 4, 9]
    demand = [3, 6, 5, 6]
    
    tp = TransportationProblem(costs, supply, demand)
    
    # 最小元素法
    alloc1 = tp.solve_minimum_element()
    cost1 = (alloc1 * tp.costs).sum()
    print(f"最小元素法初始解：总运费={cost1}")
    
    # Vogel法
    alloc2 = tp.solve_vogel()
    cost2 = (alloc2 * tp.costs).sum()
    print(f"Vogel法初始解：总运费={cost2}")
    
    # 完整求解（Vogel初始+位势检验+闭回路调整）
    alloc_opt, cost_opt, iterations = tp.optimize('vogel')
    print(f"最优解：总运费={cost_opt}，迭代次数={iterations}")
    print("最优分配方案：")
    for i in range(3):
        for j in range(4):
            if alloc_opt[i][j] > 1e-6:
                print(f"  产地{i} → 销地{j}：{alloc_opt[i][j]}")
    
    assert abs(cost_opt - 85) < 1e-6, f"期望85，实际{cost_opt}"
    print("✓ 测试通过！\n")


def test_assignment():
    print("=" * 60)
    print("测试2：指派问题（匈牙利算法）")
    print("=" * 60)
    
    # 4个人4项任务
    costs = [
        [4, 1, 3, 2],
        [2, 0, 5, 3],
        [3, 2, 2, 4],
        [5, 4, 1, 5],
    ]
    
    assignment, total_cost = hungarian_assignment(costs)
    print(f"最小总费用：{total_cost}")
    print("指派方案：")
    for i in range(4):
        print(f"  人{i} → 任务{assignment[i]}（费用{costs[i][assignment[i]]}）")
    
    assert total_cost == 6, f"期望6，实际{total_cost}"
    print("✓ 测试通过！\n")


def test_assignment_large():
    print("=" * 60)
    print("测试3：大规模指派问题（10×10随机）")
    print("=" * 60)
    
    np.random.seed(42)
    n = 10
    costs = np.random.randint(1, 100, (n, n)).tolist()
    
    assignment, total_cost = hungarian_assignment(costs)
    print(f"最小总费用：{total_cost}")
    print(f"指派方案：{assignment}")
    
    # 验证：每人一项，每项一人
    assert sorted(assignment) == list(range(n))
    print("✓ 测试通过！\n")


if __name__ == '__main__':
    test_transportation()
    test_assignment()
    test_assignment_large()
    print("=" * 60)
    print("全部测试通过！")
    print("=" * 60)
