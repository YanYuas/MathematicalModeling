# -*- coding: utf-8 -*-
"""
动态规划进阶 · 手动实现
========================
六层钻研法 · 第4层：手动实现

包含4种进阶DP：
1. 状态压缩DP：TSP旅行商问题
2. 树形DP：最大独立集、树的直径
3. 数位DP：统计1~n中数字特征
4. 概率DP：期望计算

每个算法都有详细中文注释和测试用例。
"""

import numpy as np
from collections import deque


# ============================================================
# 1. 状态压缩DP：TSP旅行商问题
# ============================================================
def tsp_bitmask(dist_matrix):
    """
    状态压缩DP求解TSP（旅行商问题）
    
    问题：从0出发，经过所有节点恰好一次，回到0，求最短路径。
    
    状态定义：
        dp[mask][i] = 经过mask中的节点，当前在i的最短距离
        mask是二进制数，第j位为1表示经过了节点j
    
    状态转移：
        dp[mask | (1<<j)][j] = min(dp[mask | (1<<j)][j],
                                    dp[mask][i] + dist[i][j])
    
    时间复杂度：O(n² * 2^n)
    空间复杂度：O(n * 2^n)
    
    适用：n <= 20（2^20约100万，可以接受）
    """
    n = len(dist_matrix)
    INF = float('inf')
    
    # dp[mask][i]：经过mask中的节点，当前在i的最短距离
    dp = [[INF] * n for _ in range(1 << n)]
    # prev[mask][i]：记录前驱，用于回溯路径
    prev = [[-1] * n for _ in range(1 << n)]
    
    # 初始化：从0出发，只经过0
    dp[1][0] = 0
    
    # 遍历所有状态
    for mask in range(1 << n):
        for i in range(n):
            if dp[mask][i] == INF:
                continue
            # 尝试去没去过的节点j
            for j in range(n):
                if not (mask & (1 << j)):  # j没去过
                    new_mask = mask | (1 << j)
                    new_dist = dp[mask][i] + dist_matrix[i][j]
                    if new_dist < dp[new_mask][j]:
                        dp[new_mask][j] = new_dist
                        prev[new_mask][j] = i
    
    # 所有节点都去过了（mask全1），回到0
    full_mask = (1 << n) - 1
    min_cost = INF
    last_node = -1
    for i in range(1, n):
        cost = dp[full_mask][i] + dist_matrix[i][0]
        if cost < min_cost:
            min_cost = cost
            last_node = i
    
    # 回溯路径
    path = []
    mask = full_mask
    cur = last_node
    while cur != -1:
        path.append(cur)
        p = prev[mask][cur]
        mask ^= (1 << cur)  # 去掉cur
        cur = p
    path.reverse()
    path.append(0)  # 回到起点
    
    return min_cost, path


# ============================================================
# 2. 树形DP
# ============================================================
class Tree:
    """树的邻接表表示"""
    def __init__(self, n):
        self.n = n
        self.children = [[] for _ in range(n)]
        self.parent = [-1] * n
    
    def add_edge(self, u, v):
        """添加无向边（建树时用）"""
        self.children[u].append(v)
        self.children[v].append(u)
    
    def root_tree(self, root=0):
        """从root开始建树，确定父子关系"""
        self.root = root
        self.parent = [-1] * self.n
        self.order = []  # BFS顺序（用于从叶子到根的DP）
        
        queue = deque([root])
        self.parent[root] = root
        while queue:
            u = queue.popleft()
            self.order.append(u)
            for v in self.children[u]:
                if self.parent[v] == -1 and v != self.parent[u]:
                    self.parent[v] = u
                    queue.append(v)
        
        # 重建children为有向的（只含子节点）
        self.children = [[] for _ in range(self.n)]
        for u in range(self.n):
            if u != root:
                self.children[self.parent[u]].append(u)


def tree_max_independent_set(tree, weights=None):
    """
    树形DP：树的最大独立集
    
    问题：在树中选一些节点，任意两个不相邻，求最大权重和。
    
    状态定义：
        dp[u][0] = 不选u时，以u为根的子树的最大权重
        dp[u][1] = 选u时，以u为根的子树的最大权重
    
    状态转移：
        dp[u][0] = Σ max(dp[v][0], dp[v][1])  （不选u，子节点可选可不选）
        dp[u][1] = w[u] + Σ dp[v][0]           （选u，子节点都不能选）
    
    从叶子到根计算（后序遍历）。
    """
    n = tree.n
    if weights is None:
        weights = [1] * n
    
    dp0 = [0] * n  # 不选u
    dp1 = [0] * n  # 选u
    
    # 从叶子到根（BFS的逆序）
    for u in reversed(tree.order):
        dp1[u] = weights[u]  # 选u，先加自己的权重
        for v in tree.children[u]:
            dp0[u] += max(dp0[v], dp1[v])  # 不选u，子节点取大的
            dp1[u] += dp0[v]                # 选u，子节点不能选
    
    return max(dp0[tree.root], dp1[tree.root])


def tree_diameter(tree):
    """
    树形DP：树的直径（最长路径）
    
    方法：两次DFS，或树形DP。
    这里用树形DP：对每个节点，求经过该节点的最长路径。
    
    状态定义：
        depth[u] = 以u为根的子树中，从u出发的最长向下路径长度
    
    对节点u，经过u的最长路径 = 最长的两个子树depth之和 + 2
    直径 = 所有节点的max(最长路径)
    """
    n = tree.n
    depth = [0] * n
    diameter = 0
    
    # 从叶子到根
    for u in reversed(tree.order):
        max1, max2 = 0, 0  # 最长和次长的子树depth
        for v in tree.children[u]:
            d = depth[v] + 1
            if d > max1:
                max2 = max1
                max1 = d
            elif d > max2:
                max2 = d
        
        depth[u] = max1
        diameter = max(diameter, max1 + max2)  # 经过u的最长路径
    
    return diameter


# ============================================================
# 3. 数位DP
# ============================================================
def count_digit_one(n):
    """
    数位DP：统计1~n中数字1出现的总次数
    
    例如 n=12：1,10,11,12 中1出现了5次（1,1,1,1,1）
    
    方法：按位计算每一位上1出现的次数。
    对第k位（从右数，0开始）：
        high = n // (10^(k+1))   高位
        cur = (n // 10^k) % 10   当前位
        low = n % 10^k           低位
        
        如果 cur == 0：该位1出现次数 = high * 10^k
        如果 cur == 1：该位1出现次数 = high * 10^k + low + 1
        如果 cur > 1：该位1出现次数 = (high + 1) * 10^k
    """
    if n <= 0:
        return 0
    
    count = 0
    factor = 1  # 10^k
    
    while factor <= n:
        high = n // (factor * 10)
        cur = (n // factor) % 10
        low = n % factor
        
        if cur == 0:
            count += high * factor
        elif cur == 1:
            count += high * factor + low + 1
        else:
            count += (high + 1) * factor
        
        factor *= 10
    
    return count


def digit_dp_generic(n, digit_func):
    """
    通用数位DP框架（记忆化搜索）
    
    参数：
        n: 上界
        digit_func: 自定义函数，返回(满足条件的数量, 额外统计)
    
    这个框架可以处理各种数位统计问题，如：
    - 统计含数字1的数的个数
    - 统计各位和为k的数的个数
    - 统计不含4和9的数的个数
    
    状态：(pos, tight, started, ...其他状态)
    """
    digits = list(map(int, str(n)))
    n_digits = len(digits)
    
    from functools import lru_cache
    
    @lru_cache(maxsize=None)
    def dp(pos, tight, started, state):
        """
        pos: 当前处理到第几位
        tight: 是否受上界约束（前面的位都等于n的对应位）
        started: 是否已经开始（前面是否有非零位，处理前导零）
        state: 自定义状态（如当前数字和、是否含某数字等）
        """
        if pos == n_digits:
            # 处理完所有位，返回结果
            return digit_func('end', started, state)
        
        limit = digits[pos] if tight else 9
        total = 0
        
        for d in range(limit + 1):
            new_tight = tight and (d == limit)
            new_started = started or (d > 0)
            
            # 自定义状态转移
            new_state, valid = digit_func('digit', new_started, state, d, pos)
            if not valid:
                continue
            
            total += dp(pos + 1, new_tight, new_started, new_state)
        
        return total
    
    return dp(0, True, False, None)


def count_numbers_without_49(n):
    """
    数位DP示例：统计1~n中不含数字4和9的数的个数
    
    用通用框架实现。
    """
    def digit_func(mode, started, state, d=None, pos=None):
        if mode == 'digit':
            if d == 4 or d == 9:
                return state, False  # 含4或9，无效
            return state, True
        else:  # end
            return 1 if started else 0  # started=False表示0，不算
    
    return digit_dp_generic(n, digit_func)


# ============================================================
# 4. 概率DP（期望DP）
# ============================================================
def dice_expected_rolls(target):
    """
    概率DP：掷骰子，求累计点数达到target的期望次数
    
    状态：E[i] = 累计点数为i时，还需要的期望次数
    转移：E[i] = 1 + (E[i+1] + E[i+2] + ... + E[i+6]) / 6
    边界：E[i] = 0 for i >= target
    
    从后往前算。
    """
    if target <= 0:
        return 0
    
    E = [0.0] * (target + 6)  # 多开几位，避免越界
    
    for i in range(target - 1, -1, -1):
        E[i] = 1.0 + sum(E[i + j] for j in range(1, 7)) / 6.0
    
    return E[0]


def random_walk_expected_steps(n, start):
    """
    概率DP：一维随机游走期望步数
    
    问题：在0~n的线段上，从start出发，每步以50%概率左移、50%右移。
    到达0或n停止。求到达边界的期望步数。
    
    状态：E[i] = 在位置i时，到达终点的期望步数
    转移：E[i] = 1 + 0.5*E[i-1] + 0.5*E[i+1]
    边界：E[0] = E[n] = 0
    
    这是一个线性方程组，可以用递推求解。
    解析解：E[i] = i * (n - i)
    """
    if start == 0 or start == n:
        return 0
    
    # 用高斯消元解线性方程组，或者直接用解析解
    # 这里用迭代法（更通用）
    E = [0.0] * (n + 1)
    
    # 迭代求解（雅可比迭代）
    for _ in range(10000):
        new_E = E[:]
        for i in range(1, n):
            new_E[i] = 1.0 + 0.5 * E[i - 1] + 0.5 * E[i + 1]
        E = new_E
    
    return E[start]


def expected_collect_all_coupons(n):
    """
    概率DP：收集优惠券问题（赠券收集问题）
    
    问题：有n种优惠券，每次随机获得一种。求收集齐n种的期望次数。
    
    状态：E[i] = 已经收集了i种时，还需要的期望次数
    转移：E[i] = 1 + (i/n)*E[i] + ((n-i)/n)*E[i+1]
         （以i/n概率获得已有的，(n-i)/n概率获得新的）
    化简：E[i] = n/(n-i) + E[i+1]
    边界：E[n] = 0
    
    解析解：E[0] = n * (1 + 1/2 + 1/3 + ... + 1/n) = n * H_n
    """
    E = [0.0] * (n + 1)
    
    for i in range(n - 1, -1, -1):
        # E[i] = n/(n-i) + E[i+1]
        E[i] = n / (n - i) + E[i + 1]
    
    return E[0]


# ============================================================
# 测试用例
# ============================================================
def test_tsp():
    print("=" * 60)
    print("测试1：状态压缩DP - TSP旅行商问题")
    print("=" * 60)
    
    # 4个城市的距离矩阵
    dist = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0],
    ]
    
    cost, path = tsp_bitmask(dist)
    print(f"最短路径长度：{cost}")
    print(f"路径：{'→'.join(map(str, path))}")
    
    # 验证：0→1→3→2→0 = 10+25+30+15 = 80
    assert cost == 80, f"期望80，实际{cost}"
    print("✓ 测试通过！\n")


def test_tree_dp():
    print("=" * 60)
    print("测试2：树形DP - 最大独立集 + 直径")
    print("=" * 60)
    
    # 建一棵树：0-1, 0-2, 1-3, 1-4
    tree = Tree(5)
    tree.add_edge(0, 1)
    tree.add_edge(0, 2)
    tree.add_edge(1, 3)
    tree.add_edge(1, 4)
    tree.root_tree(0)
    
    # 最大独立集（权重都为1）
    mis = tree_max_independent_set(tree)
    print(f"最大独立集大小：{mis}")
    # 可选{2,3,4}或{0,3,4}，大小3
    assert mis == 3
    
    # 带权重
    weights = [10, 20, 30, 40, 50]
    mis_w = tree_max_independent_set(tree, weights)
    print(f"带权最大独立集：{mis_w}")
    # 选{2,3,4}：30+40+50=120，或{0,3,4}：10+40+50=100
    # 最优是{2,3,4}=120
    assert mis_w == 120
    
    # 树的直径
    diameter = tree_diameter(tree)
    print(f"树的直径：{diameter}")
    # 最长路径：2-0-1-3 或 2-0-1-4，长度3
    assert diameter == 3
    
    print("✓ 测试通过！\n")


def test_digit_dp():
    print("=" * 60)
    print("测试3：数位DP")
    print("=" * 60)
    
    # 统计1~12中1出现的次数
    count = count_digit_one(12)
    print(f"1~12中1出现的次数：{count}")
    # 1,10,11,12 → 1出现5次
    assert count == 5
    
    count2 = count_digit_one(100)
    print(f"1~100中1出现的次数：{count2}")
    # 个位10次+十位10次+百位1次=21次
    assert count2 == 21
    
    # 不含4和9的数
    no49 = count_numbers_without_49(20)
    print(f"1~20中不含4和9的数的个数：{no49}")
    # 去掉4,9,14,19 → 16个
    assert no49 == 16
    
    print("✓ 测试通过！\n")


def test_probability_dp():
    print("=" * 60)
    print("测试4：概率DP（期望DP）")
    print("=" * 60)
    
    # 掷骰子达到6的期望次数
    e_dice = dice_expected_rolls(6)
    print(f"掷骰子累计达到6的期望次数：{e_dice:.4f}")
    assert e_dice > 2 and e_dice < 4
    
    # 随机游走：n=10, start=5
    e_walk = random_walk_expected_steps(10, 5)
    print(f"随机游走n=10,start=5的期望步数：{e_walk:.4f}")
    # 解析解：i*(n-i) = 5*5 = 25
    assert abs(e_walk - 25) < 1.0
    
    # 赠券收集：n=5
    e_coupon = expected_collect_all_coupons(5)
    print(f"收集5种优惠券的期望次数：{e_coupon:.4f}")
    # 解析解：5*(1+1/2+1/3+1/4+1/5) = 5*2.2833 = 11.4167
    expected = 5 * (1 + 1/2 + 1/3 + 1/4 + 1/5)
    assert abs(e_coupon - expected) < 1e-6
    
    print("✓ 测试通过！\n")


if __name__ == '__main__':
    test_tsp()
    test_tree_dp()
    test_digit_dp()
    test_probability_dp()
    print("=" * 60)
    print("全部测试通过！")
    print("=" * 60)
