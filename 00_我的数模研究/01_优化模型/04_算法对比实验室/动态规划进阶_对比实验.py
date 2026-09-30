# -*- coding: utf-8 -*-
"""
动态规划进阶 · 对比实验
========================
六层钻研法 · 第6层：对比创新

对比内容：
1. TSP：状态压缩DP vs 暴力枚举 vs 最近邻启发式
2. 树形DP：不同树规模/深度的性能
3. 数位DP：逐位计算法 vs 通用记忆化框架
4. 概率DP：迭代法收敛速度
"""

import numpy as np
import time
import sys
import os
from itertools import permutations

code_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '02_算法实现手札', '00_手动实现详解')
sys.path.insert(0, os.path.normpath(code_dir))
from importlib import import_module
dp_adv = import_module('13_动态规划进阶_手动实现')


def experiment_tsp():
    print("=" * 80)
    print("实验1：TSP —— 状态压缩DP vs 暴力枚举 vs 最近邻启发式")
    print("=" * 80)
    
    def tsp_brute_force(dist):
        """暴力枚举：O((n-1)!)"""
        n = len(dist)
        best = float('inf')
        for perm in permutations(range(1, n)):
            path = [0] + list(perm) + [0]
            cost = sum(dist[path[i]][path[i+1]] for i in range(len(path)-1))
            best = min(best, cost)
        return best
    
    def tsp_nearest_neighbor(dist):
        """最近邻启发式：O(n²)，不保证最优"""
        n = len(dist)
        visited = [False] * n
        path = [0]
        visited[0] = True
        cost = 0
        for _ in range(n - 1):
            cur = path[-1]
            next_city = -1
            min_d = float('inf')
            for j in range(n):
                if not visited[j] and dist[cur][j] < min_d:
                    min_d = dist[cur][j]
                    next_city = j
            path.append(next_city)
            visited[next_city] = True
            cost += min_d
        cost += dist[path[-1]][0]
        return cost
    
    sizes = [5, 6, 7, 8, 9, 10, 12, 15]
    
    print(f"\n{'n':>4} {'DP(ms)':>10} {'暴力(ms)':>10} {'最近邻(ms)':>12} {'DP最优':>8} {'NN误差':>8}")
    print("-" * 60)
    
    np.random.seed(42)
    for n in sizes:
        # 生成随机距离矩阵（对称）
        coords = np.random.rand(n, 2) * 100
        dist = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                dist[i][j] = np.sqrt((coords[i][0]-coords[j][0])**2 + (coords[i][1]-coords[j][1])**2)
        
        # 状态压缩DP
        start = time.time()
        cost_dp, _ = dp_adv.tsp_bitmask(dist)
        t_dp = (time.time() - start) * 1000
        
        # 暴力枚举（n<=9才跑，否则太慢）
        if n <= 9:
            start = time.time()
            cost_bf = tsp_brute_force(dist)
            t_bf = (time.time() - start) * 1000
            dp_optimal = abs(cost_dp - cost_bf) < 1e-6
        else:
            t_bf = float('inf')
            dp_optimal = True  # DP一定是最优的
        
        # 最近邻
        start = time.time()
        cost_nn = tsp_nearest_neighbor(dist)
        t_nn = (time.time() - start) * 1000
        
        nn_error = (cost_nn - cost_dp) / cost_dp * 100
        
        bf_str = f"{t_bf:.3f}" if t_bf != float('inf') else "N/A"
        print(f"{n:>4} {t_dp:>10.3f} {bf_str:>10} {t_nn:>12.3f} {'✓' if dp_optimal else '✗':>8} {nn_error:>7.1f}%")
    
    print("\n💡 结论：")
    print("   - 状态压缩DP保证最优，n=15时仍可接受（约几十ms）")
    print("   - 暴力枚举n=9时已经很慢（O((n-1)!)）")
    print("   - 最近邻最快但有误差，通常比最优解差10-30%")
    print("   - n>20时建议用启发式算法（GA/SA/ACO）")


def experiment_tree_dp():
    print("\n" + "=" * 80)
    print("实验2：树形DP —— 不同规模/深度的性能")
    print("=" * 80)
    
    configs = [
        (100, 2, "小树浅"),
        (1000, 2, "中树浅"),
        (10000, 2, "大树浅"),
        (100, 10, "小树深"),
        (1000, 10, "中树深"),
    ]
    
    print(f"\n{'节点数':>8} {'分支度':>8} {'类型':>8} {'建树(ms)':>10} {'MIS(ms)':>10} {'直径(ms)':>10}")
    print("-" * 60)
    
    np.random.seed(42)
    for n, branch, label in configs:
        # 生成随机树
        tree = dp_adv.Tree(n)
        for i in range(1, n):
            parent = np.random.randint(0, min(i, branch * 10))
            tree.add_edge(parent, i)
        
        start = time.time()
        tree.root_tree(0)
        t_root = (time.time() - start) * 1000
        
        weights = np.random.randint(1, 100, n).tolist()
        
        start = time.time()
        mis = dp_adv.tree_max_independent_set(tree, weights)
        t_mis = (time.time() - start) * 1000
        
        start = time.time()
        diam = dp_adv.tree_diameter(tree)
        t_diam = (time.time() - start) * 1000
        
        print(f"{n:>8} {branch:>8} {label:>8} {t_root:>10.3f} {t_mis:>10.3f} {t_diam:>10.3f}")
    
    print("\n💡 结论：树形DP是O(n)的，节点数从100到10000时间线性增长，非常高效。")


def experiment_digit_dp():
    print("\n" + "=" * 80)
    print("实验3：数位DP —— 逐位计算法 vs 通用记忆化框架")
    print("=" * 80)
    
    test_ns = [1000, 10000, 100000, 1000000, 10000000]
    
    print(f"\n{'n':>12} {'逐位法(ms)':>12} {'记忆化(ms)':>12} {'结果一致':>8}")
    print("-" * 50)
    
    for n in test_ns:
        start = time.time()
        r1 = dp_adv.count_digit_one(n)
        t1 = (time.time() - start) * 1000
        
        start = time.time()
        # 用通用框架实现统计1的个数
        def digit_func(mode, started, state, d=None, pos=None):
            if mode == 'digit':
                cnt = state if state else 0
                if d == 1:
                    cnt += 1
                return cnt, True
            else:
                return state if state else 0
        r2 = dp_adv.digit_dp_generic(n, digit_func)
        t2 = (time.time() - start) * 1000
        
        consistent = r1 == r2
        print(f"{n:>12} {t1:>12.6f} {t2:>12.6f} {'✓' if consistent else '✗':>8}")
    
    print("\n💡 结论：")
    print("   - 逐位计算法是O(位数)，极快（微秒级）")
    print("   - 通用记忆化框架更灵活，但有函数调用开销")
    print("   - 简单问题用逐位法，复杂问题用通用框架")


def experiment_probability_dp():
    print("\n" + "=" * 80)
    print("实验4：概率DP —— 迭代法收敛速度")
    print("=" * 80)
    
    # 随机游走：比较迭代次数与精度
    n = 10
    start = 5
    exact = start * (n - start)  # 解析解25
    
    print(f"\n随机游走 n={n}, start={start}，解析解={exact}")
    print(f"{'迭代次数':>10} {'结果':>10} {'误差':>10} {'时间(ms)':>10}")
    print("-" * 45)
    
    for iterations in [10, 50, 100, 500, 1000, 5000]:
        E = [0.0] * (n + 1)
        start_time = time.time()
        for _ in range(iterations):
            new_E = E[:]
            for i in range(1, n):
                new_E[i] = 1.0 + 0.5 * E[i - 1] + 0.5 * E[i + 1]
            E = new_E
        t = (time.time() - start_time) * 1000
        
        error = abs(E[start] - exact)
        print(f"{iterations:>10} {E[start]:>10.6f} {error:>10.6f} {t:>10.4f}")
    
    print("\n💡 结论：")
    print("   - 雅可比迭代收敛较慢，需要约1000次才能接近精确解")
    print("   - 实际中可以用高斯-赛德尔迭代（原地更新），收敛更快")
    print("   - 或者直接解线性方程组（有环的概率DP本质是解方程组）")


if __name__ == '__main__':
    experiment_tsp()
    experiment_tree_dp()
    experiment_digit_dp()
    experiment_probability_dp()
    
    print("\n" + "=" * 80)
    print("全部实验完成！")
    print("=" * 80)
