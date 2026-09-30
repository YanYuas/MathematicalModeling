# -*- coding: utf-8 -*-
"""
动态规划 · 经典算法手动实现
============================
六层钻研法 · 第4层：手动实现

包含7个经典DP算法：
1. 0-1背包（二维 + 一维滚动数组优化）
2. 完全背包
3. 最长公共子序列 LCS（含回溯求具体序列）
4. 最长递增子序列 LIS（O(n²) + O(n log n)贪心二分）
5. 编辑距离（含回溯求操作序列）
6. 矩阵链乘法（含回溯求加括号方案）
7. 记忆化搜索 vs 迭代DP（以斐波那契为例对比）

每个算法都有详细中文注释和测试用例。
"""

import numpy as np
import time
from functools import lru_cache


# ============================================================
# 算法1：0-1背包问题
# ============================================================
def knapsack_01_2d(weights, values, capacity):
    """
    0-1背包（二维DP）
    
    状态定义：dp[i][j] = 前i个物品，背包容量j时的最大价值
    状态转移：
        dp[i][j] = max(dp[i-1][j],                    # 不选第i个
                       dp[i-1][j-w[i]] + v[i])         # 选第i个
    
    参数：
        weights: 物品重量列表
        values: 物品价值列表
        capacity: 背包容量
    
    返回：
        (最大价值, dp表, 选中的物品列表)
    """
    n = len(weights)
    # dp[i][j]：前i个物品，容量j的最大价值
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    # 填表：逐个物品考虑
    for i in range(1, n + 1):
        w = weights[i - 1]
        v = values[i - 1]
        for j in range(capacity + 1):
            if j < w:
                # 容量不够，只能不选
                dp[i][j] = dp[i - 1][j]
            else:
                # 选或不选，取较大值
                dp[i][j] = max(dp[i - 1][j], dp[i - 1][j - w] + v)
    
    # 回溯：从dp[n][capacity]往回找选中了哪些物品
    selected = []
    j = capacity
    for i in range(n, 0, -1):
        if dp[i][j] != dp[i - 1][j]:
            # 第i个物品被选中了
            selected.append(i - 1)
            j -= weights[i - 1]
    selected.reverse()
    
    return dp[n][capacity], dp, selected


def knapsack_01_1d(weights, values, capacity):
    """
    0-1背包（一维滚动数组优化）
    
    观察：dp[i]只依赖dp[i-1]，可以用一维数组。
    关键：j必须逆序遍历！否则同一个物品会被选多次。
    
    时间：O(nW)，空间：O(W)
    """
    n = len(weights)
    dp = [0] * (capacity + 1)
    
    for i in range(n):
        w = weights[i]
        v = values[i]
        # 逆序！从capacity到w
        for j in range(capacity, w - 1, -1):
            dp[j] = max(dp[j], dp[j - w] + v)
    
    return dp[capacity], dp


# ============================================================
# 算法2：完全背包问题
# ============================================================
def knapsack_complete(weights, values, capacity):
    """
    完全背包（每个物品可选无限次）
    
    与0-1背包的区别：j正序遍历（允许重复选同一物品）
    
    时间：O(nW)，空间：O(W)
    """
    n = len(weights)
    dp = [0] * (capacity + 1)
    
    for i in range(n):
        w = weights[i]
        v = values[i]
        # 正序！从w到capacity
        for j in range(w, capacity + 1):
            dp[j] = max(dp[j], dp[j - w] + v)
    
    return dp[capacity], dp


# ============================================================
# 算法3：最长公共子序列 LCS
# ============================================================
def lcs(s1, s2):
    """
    最长公共子序列（Longest Common Subsequence）
    
    状态定义：dp[i][j] = s1前i个字符和s2前j个字符的LCS长度
    状态转移：
        如果 s1[i-1] == s2[j-1]: dp[i][j] = dp[i-1][j-1] + 1
        否则: dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    返回：
        (LCS长度, LCS具体字符串, dp表)
    """
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # 填表
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                # 字符相同，LCS长度+1
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                # 字符不同，取较大的那个
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    # 回溯求具体序列
    result = []
    i, j = m, n
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            # 这个字符在LCS中
            result.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            # 往上走
            i -= 1
        else:
            # 往左走
            j -= 1
    result.reverse()
    
    return dp[m][n], ''.join(result), dp


# ============================================================
# 算法4：最长递增子序列 LIS
# ============================================================
def lis_dp(arr):
    """
    最长递增子序列（DP方法，O(n²)）
    
    状态定义：dp[i] = 以arr[i]结尾的LIS长度
    状态转移：dp[i] = max(dp[j] + 1) for j < i and arr[j] < arr[i]
    """
    n = len(arr)
    if n == 0:
        return 0, []
    
    dp = [1] * n  # 每个元素自身长度为1
    prev = [-1] * n  # 记录前驱，用于回溯
    
    for i in range(1, n):
        for j in range(i):
            if arr[j] < arr[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                prev[i] = j
    
    # 找最大值的位置
    max_len = max(dp)
    max_idx = dp.index(max_len)
    
    # 回溯
    result = []
    while max_idx != -1:
        result.append(arr[max_idx])
        max_idx = prev[max_idx]
    result.reverse()
    
    return max_len, result


def lis_binary(arr):
    """
    最长递增子序列（贪心+二分，O(n log n)）
    
    维护tails数组：tails[i] = 长度为i+1的递增子序列的最小末尾元素。
    对每个元素，用二分查找它应该插入的位置。
    
    注意：tails不是真正的LIS，只是长度正确。需要额外记录前驱才能回溯。
    """
    import bisect
    
    n = len(arr)
    if n == 0:
        return 0, []
    
    tails = []  # tails[i] = 长度i+1的LIS的最小末尾
    tails_idx = []  # 对应元素在原数组中的索引
    prev = [-1] * n  # 前驱索引
    
    for i, x in enumerate(arr):
        # 二分查找第一个>=x的位置
        pos = bisect.bisect_left(tails, x)
        
        if pos == len(tails):
            # x比所有末尾都大，追加
            tails.append(x)
            tails_idx.append(i)
        else:
            # 替换
            tails[pos] = x
            tails_idx[pos] = i
        
        # 记录前驱
        if pos > 0:
            prev[i] = tails_idx[pos - 1]
    
    # 回溯
    result = []
    idx = tails_idx[-1]
    while idx != -1:
        result.append(arr[idx])
        idx = prev[idx]
    result.reverse()
    
    return len(tails), result


# ============================================================
# 算法5：编辑距离
# ============================================================
def edit_distance(s1, s2):
    """
    编辑距离（Levenshtein Distance）
    
    把s1变成s2最少需要多少次操作（插入、删除、替换）。
    
    状态定义：dp[i][j] = s1前i个字符变成s2前j个字符的最少操作数
    状态转移：
        如果 s1[i-1] == s2[j-1]: dp[i][j] = dp[i-1][j-1]
        否则: dp[i][j] = 1 + min(dp[i-1][j],    # 删除
                                  dp[i][j-1],    # 插入
                                  dp[i-1][j-1])  # 替换
    
    返回：
        (编辑距离, 操作序列, dp表)
    """
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # 初始条件
    for i in range(m + 1):
        dp[i][0] = i  # s1前i个全删
    for j in range(n + 1):
        dp[0][j] = j  # 全插入s2前j个
    
    # 填表
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],      # 删除s1[i-1]
                    dp[i][j - 1],      # 插入s2[j-1]
                    dp[i - 1][j - 1]   # 替换
                )
    
    # 回溯求操作序列
    operations = []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and s1[i - 1] == s2[j - 1]:
            operations.append(f"保留 '{s1[i-1]}'")
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            operations.append(f"删除 '{s1[i-1]}'")
            i -= 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            operations.append(f"插入 '{s2[j-1]}'")
            j -= 1
        else:
            operations.append(f"替换 '{s1[i-1]}' → '{s2[j-1]}'")
            i -= 1
            j -= 1
    operations.reverse()
    
    return dp[m][n], operations, dp


# ============================================================
# 算法6：矩阵链乘法
# ============================================================
def matrix_chain_order(p):
    """
    矩阵链乘法最优括号化
    
    参数：
        p: 矩阵维度列表，p[i-1]×p[i]是第i个矩阵的维度
           例：p=[10,100,5,50] 表示 A1(10×100), A2(100×5), A3(5×50)
    
    状态定义：dp[i][j] = 矩阵i到j相乘的最少标量乘法次数
    状态转移：
        dp[i][j] = min(dp[i][k] + dp[k+1][j] + p[i-1]*p[k]*p[j])
                   for k in [i, j-1]
    
    计算顺序：按区间长度从小到大
    
    返回：
        (最少乘法次数, 分割点表, 括号化方案字符串)
    """
    n = len(p) - 1  # 矩阵个数
    # dp[i][j]：矩阵i到j的最少乘法次数（i,j从1开始）
    dp = [[0] * (n + 1) for _ in range(n + 1)]
    # split[i][j]：最优分割点k
    split = [[0] * (n + 1) for _ in range(n + 1)]
    
    # 按区间长度从小到大计算
    for length in range(2, n + 1):  # length是链长，从2到n
        for i in range(1, n - length + 2):
            j = i + length - 1
            dp[i][j] = float('inf')
            # 枚举分割点k
            for k in range(i, j):
                cost = dp[i][k] + dp[k + 1][j] + p[i - 1] * p[k] * p[j]
                if cost < dp[i][j]:
                    dp[i][j] = cost
                    split[i][j] = k
    
    # 回溯构造括号化方案
    def build_parens(i, j):
        if i == j:
            return f"A{i}"
        k = split[i][j]
        return f"({build_parens(i, k)} × {build_parens(k + 1, j)})"
    
    solution = build_parens(1, n)
    
    return dp[1][n], split, solution


# ============================================================
# 算法7：记忆化搜索 vs 迭代DP
# ============================================================
def fib_recursive(n):
    """纯递归（不推荐，O(2^n)）"""
    if n <= 1:
        return n
    return fib_recursive(n - 1) + fib_recursive(n - 2)


def fib_memo(n, memo=None):
    """记忆化搜索（自顶向下，O(n)）"""
    if memo is None:
        memo = {}
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo)
    return memo[n]


def fib_dp(n):
    """迭代DP（自底向上，O(n)时间，O(1)空间）"""
    if n <= 1:
        return n
    a, b = 0, 1  # a=fib(i-2), b=fib(i-1)
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


# ============================================================
# 测试用例
# ============================================================
def test_knapsack():
    print("=" * 60)
    print("测试1：0-1背包")
    print("=" * 60)
    weights = [2, 3, 4, 5]
    values = [3, 4, 5, 6]
    capacity = 8
    
    max_val, dp, selected = knapsack_01_2d(weights, values, capacity)
    print(f"二维DP：最大价值={max_val}, 选中物品={selected}")
    
    max_val_1d, dp_1d = knapsack_01_1d(weights, values, capacity)
    print(f"一维DP：最大价值={max_val_1d}")
    
    assert max_val == max_val_1d == 10, "背包测试失败！"
    print("✓ 测试通过！\n")


def test_complete_knapsack():
    print("=" * 60)
    print("测试2：完全背包")
    print("=" * 60)
    weights = [2, 3, 4]
    values = [3, 4, 5]
    capacity = 10
    
    max_val, dp = knapsack_complete(weights, values, capacity)
    print(f"完全背包：最大价值={max_val}")
    # 验证：选5个物品1（重量2，价值3）= 15
    assert max_val == 15, "完全背包测试失败！"
    print("✓ 测试通过！\n")


def test_lcs():
    print("=" * 60)
    print("测试3：最长公共子序列 LCS")
    print("=" * 60)
    s1 = "ABCBDAB"
    s2 = "BDCAB"
    
    length, lcs_str, dp = lcs(s1, s2)
    print(f"s1 = {s1}")
    print(f"s2 = {s2}")
    print(f"LCS长度 = {length}")
    print(f"LCS = {lcs_str}")
    
    assert length == 4, "LCS测试失败！"
    print("✓ 测试通过！\n")


def test_lis():
    print("=" * 60)
    print("测试4：最长递增子序列 LIS")
    print("=" * 60)
    arr = [10, 9, 2, 5, 3, 7, 101, 18]
    
    len_dp, seq_dp = lis_dp(arr)
    print(f"DP方法(O(n²))：长度={len_dp}, 序列={seq_dp}")
    
    len_bin, seq_bin = lis_binary(arr)
    print(f"贪心二分(O(nlogn))：长度={len_bin}, 序列={seq_bin}")
    
    assert len_dp == len_bin == 4, "LIS测试失败！"
    print("✓ 测试通过！\n")


def test_edit_distance():
    print("=" * 60)
    print("测试5：编辑距离")
    print("=" * 60)
    s1 = "kitten"
    s2 = "sitting"
    
    dist, ops, dp = edit_distance(s1, s2)
    print(f"'{s1}' → '{s2}'")
    print(f"编辑距离 = {dist}")
    print("操作序列：")
    for op in ops:
        print(f"  {op}")
    
    assert dist == 3, "编辑距离测试失败！"
    print("✓ 测试通过！\n")


def test_matrix_chain():
    print("=" * 60)
    print("测试6：矩阵链乘法")
    print("=" * 60)
    # A1(10×100), A2(100×5), A3(5×50)
    p = [10, 100, 5, 50]
    
    min_cost, split, solution = matrix_chain_order(p)
    print(f"矩阵维度：{p}")
    print(f"最少乘法次数 = {min_cost}")
    print(f"最优括号化：{solution}")
    
    assert min_cost == 7500, "矩阵链测试失败！"
    print("✓ 测试通过！\n")


def test_fib_comparison():
    print("=" * 60)
    print("测试7：斐波那契三种方法对比")
    print("=" * 60)
    n = 30
    
    start = time.time()
    result_rec = fib_recursive(n)
    time_rec = time.time() - start
    
    start = time.time()
    result_memo = fib_memo(n)
    time_memo = time.time() - start
    
    start = time.time()
    result_dp = fib_dp(n)
    time_dp = time.time() - start
    
    print(f"fib({n}) = {result_dp}")
    print(f"纯递归：    {time_rec*1000:8.2f} ms")
    print(f"记忆化搜索：{time_memo*1000:8.4f} ms")
    print(f"迭代DP：    {time_dp*1000:8.4f} ms")
    print(f"递归 vs DP 速度比：{time_rec/time_dp:.0f} 倍")
    
    assert result_rec == result_memo == result_dp, "斐波那契测试失败！"
    print("✓ 测试通过！\n")


if __name__ == '__main__':
    test_knapsack()
    test_complete_knapsack()
    test_lcs()
    test_lis()
    test_edit_distance()
    test_matrix_chain()
    test_fib_comparison()
    print("=" * 60)
    print("全部测试通过！")
    print("=" * 60)
