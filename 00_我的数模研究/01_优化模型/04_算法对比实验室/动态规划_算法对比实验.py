# -*- coding: utf-8 -*-
"""
动态规划 · 算法对比实验
========================
六层钻研法 · 第6层：对比创新

对比内容：
1. 纯递归 vs 记忆化搜索 vs 迭代DP（斐波那契）
2. 二维DP vs 一维滚动数组（0-1背包）
3. LIS的O(n²) DP vs O(n log n)贪心二分
4. 不同规模下的性能对比

评价指标：运行时间、空间占用、结果正确性
"""

import numpy as np
import time
import sys
import os

# 导入自己实现的算法
code_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '02_算法实现手札', '00_手动实现详解')
sys.path.insert(0, os.path.normpath(code_dir))
from importlib import import_module
dp_mod = import_module('09_动态规划经典算法_手动实现')


# ============================================================
# 实验1：斐波那契三种方法对比
# ============================================================
def experiment_fib():
    print("=" * 80)
    print("实验1：斐波那契 —— 纯递归 vs 记忆化搜索 vs 迭代DP")
    print("=" * 80)
    
    sizes = [10, 20, 30, 35]
    
    print(f"\n{'n':>6} {'纯递归(ms)':>12} {'记忆化(ms)':>12} {'迭代DP(ms)':>12} {'递归/DP':>10}")
    print("-" * 60)
    
    for n in sizes:
        # 纯递归
        start = time.time()
        r1 = dp_mod.fib_recursive(n)
        t_rec = (time.time() - start) * 1000
        
        # 记忆化
        start = time.time()
        r2 = dp_mod.fib_memo(n)
        t_memo = (time.time() - start) * 1000
        
        # 迭代DP
        start = time.time()
        r3 = dp_mod.fib_dp(n)
        t_dp = (time.time() - start) * 1000
        
        assert r1 == r2 == r3, f"结果不一致！{r1} {r2} {r3}"
        
        ratio = t_rec / t_dp if t_dp > 0 else float('inf')
        print(f"{n:>6} {t_rec:>12.3f} {t_memo:>12.4f} {t_dp:>12.4f} {ratio:>10.0f}x")
    
    print("\n💡 结论：纯递归是O(2^n)指数爆炸，记忆化和迭代DP是O(n)。")
    print("   n=35时，递归比DP慢数万倍！这就是动态规划的威力。")


# ============================================================
# 实验2：背包 —— 二维DP vs 一维滚动数组
# ============================================================
def experiment_knapsack():
    print("\n" + "=" * 80)
    print("实验2：0-1背包 —— 二维DP vs 一维滚动数组")
    print("=" * 80)
    
    # 不同规模：物品数n × 容量W
    configs = [
        (10, 50),
        (50, 200),
        (100, 500),
        (200, 1000),
    ]
    
    print(f"\n{'物品数':>6} {'容量':>6} {'二维(ms)':>10} {'一维(ms)':>10} {'空间比':>10} {'结果一致':>8}")
    print("-" * 60)
    
    np.random.seed(42)
    for n, W in configs:
        weights = np.random.randint(1, 20, n).tolist()
        values = np.random.randint(1, 30, n).tolist()
        
        # 二维DP
        start = time.time()
        r2d, _, _ = dp_mod.knapsack_01_2d(weights, values, W)
        t2d = (time.time() - start) * 1000
        
        # 一维DP
        start = time.time()
        r1d, _ = dp_mod.knapsack_01_1d(weights, values, W)
        t1d = (time.time() - start) * 1000
        
        space_ratio = (n * W) / W  # 二维空间 vs 一维空间
        consistent = "✓" if r2d == r1d else "✗"
        
        print(f"{n:>6} {W:>6} {t2d:>10.3f} {t1d:>10.3f} {space_ratio:>10.0f}x {consistent:>8}")
    
    print("\n💡 结论：一维滚动数组把空间从O(nW)降到O(W)，速度也更快（缓存友好）。")
    print("   关键：一维优化时j必须逆序遍历，否则变成完全背包！")


# ============================================================
# 实验3：LIS —— O(n²) DP vs O(n log n) 贪心二分
# ============================================================
def experiment_lis():
    print("\n" + "=" * 80)
    print("实验3：最长递增子序列 —— O(n²) DP vs O(n log n) 贪心二分")
    print("=" * 80)
    
    sizes = [100, 500, 1000, 5000, 10000]
    
    print(f"\n{'n':>8} {'DP O(n²)(ms)':>14} {'二分O(nlogn)(ms)':>18} {'速度比':>10} {'结果一致':>8}")
    print("-" * 70)
    
    np.random.seed(42)
    for n in sizes:
        arr = np.random.permutation(n).tolist()  # 随机排列
        
        # DP方法
        start = time.time()
        len_dp, _ = dp_mod.lis_dp(arr)
        t_dp = (time.time() - start) * 1000
        
        # 贪心二分
        start = time.time()
        len_bin, _ = dp_mod.lis_binary(arr)
        t_bin = (time.time() - start) * 1000
        
        ratio = t_dp / t_bin if t_bin > 0 else float('inf')
        consistent = "✓" if len_dp == len_bin else "✗"
        
        print(f"{n:>8} {t_dp:>14.3f} {t_bin:>18.3f} {ratio:>10.1f}x {consistent:>8}")
    
    print("\n💡 结论：n=10000时，O(n²)需要几秒，O(n log n)只需几毫秒。")
    print("   大数据量时，算法复杂度的差异是决定性的！")


# ============================================================
# 实验4：编辑距离 —— 不同字符串长度
# ============================================================
def experiment_edit_distance():
    print("\n" + "=" * 80)
    print("实验4：编辑距离 —— 不同字符串长度的性能")
    print("=" * 80)
    
    sizes = [50, 100, 200, 500]
    
    print(f"\n{'长度':>6} {'时间(ms)':>10} {'空间(KB)':>10} {'编辑距离':>8}")
    print("-" * 40)
    
    np.random.seed(42)
    chars = 'ACGT'
    for n in sizes:
        s1 = ''.join(np.random.choice(list(chars), n))
        s2 = ''.join(np.random.choice(list(chars), n))
        
        start = time.time()
        dist, _, dp = dp_mod.edit_distance(s1, s2)
        t = (time.time() - start) * 1000
        
        space_kb = (n + 1) * (n + 1) * 8 / 1024  # dp表大小
        
        print(f"{n:>6} {t:>10.3f} {space_kb:>10.1f} {dist:>8}")
    
    print("\n💡 结论：编辑距离是O(mn)时间和空间。")
    print("   长序列比对（如全基因组）需要更高级的算法（如BLAST的种子扩展）。")


# ============================================================
# 实验5：矩阵链乘法 —— 不同矩阵数量
# ============================================================
def experiment_matrix_chain():
    print("\n" + "=" * 80)
    print("实验5：矩阵链乘法 —— O(n³) DP")
    print("=" * 80)
    
    sizes = [5, 10, 20, 50, 100]
    
    print(f"\n{'矩阵数':>6} {'时间(ms)':>10} {'最少乘法次数':>14}")
    print("-" * 35)
    
    np.random.seed(42)
    for n in sizes:
        p = np.random.randint(10, 100, n + 1).tolist()
        
        start = time.time()
        cost, _, _ = dp_mod.matrix_chain_order(p)
        t = (time.time() - start) * 1000
        
        print(f"{n:>6} {t:>10.3f} {cost:>14}")
    
    print("\n💡 结论：矩阵链是O(n³)，n=100时已经需要几百毫秒。")
    print("   但实际中矩阵数量通常不多（<20），所以这个算法完全够用。")


# ============================================================
# 主函数
# ============================================================
if __name__ == '__main__':
    experiment_fib()
    experiment_knapsack()
    experiment_lis()
    experiment_edit_distance()
    experiment_matrix_chain()
    
    print("\n" + "=" * 80)
    print("全部实验完成！")
    print("=" * 80)
    print("""
核心发现：
1. 动态规划把指数级复杂度降到多项式级（斐波那契：2^n → n）
2. 滚动数组优化可以大幅减少空间（背包：nW → W）
3. 算法复杂度决定大数据量下的生死（LIS：n² vs nlogn）
4. DP不是万能的：状态空间太大时（如TSP n>20）需要其他方法
""")
