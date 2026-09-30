# -*- coding: utf-8 -*-
"""
启发式算法深化 · TSP对比实验
==============================
六层钻研法 · 第6层：对比创新

对比：
1. 最近邻（基线）
2. 2-opt局部搜索
3. 蚁群算法（ACO）
4. 混合算法（Memetic = GA + 2-opt）
5. 模拟退火（SA）

不同规模：n=20, 30, 50
多次运行取平均，比较解的质量和运行时间。
"""

import numpy as np
import random
import time
import sys
import os

code_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '02_算法实现手札', '00_手动实现详解')
sys.path.insert(0, os.path.normpath(code_dir))
from importlib import import_module
tsp_solvers = import_module('14_启发式算法深化_TSP求解器')


def nearest_neighbor(dist):
    """最近邻启发式（基线）"""
    n = len(dist)
    visited = [False] * n
    tour = [0]
    visited[0] = True
    for _ in range(n - 1):
        cur = tour[-1]
        next_city = min((j for j in range(n) if not visited[j]),
                        key=lambda j: dist[cur][j])
        tour.append(next_city)
        visited[next_city] = True
    return tour, tsp_solvers.tour_length(tour, dist)


def run_experiment():
    print("=" * 90)
    print("TSP求解器对比实验")
    print("=" * 90)
    
    sizes = [20, 30, 50]
    n_runs = 5  # 每种算法运行5次取平均
    
    for n in sizes:
        print(f"\n{'='*80}")
        print(f"问题规模：n={n}")
        print(f"{'='*80}")
        
        # 生成固定的测试问题
        np.random.seed(123)
        coords = np.random.rand(n, 2) * 100
        dist = tsp_solvers.calculate_distance_matrix(coords)
        
        results = {}
        
        # 1. 最近邻（确定性，只跑一次）
        random.seed(42)
        start = time.time()
        _, nn_len = nearest_neighbor(dist)
        nn_time = (time.time() - start) * 1000
        results['最近邻'] = (nn_len, nn_len, nn_len, nn_time)
        
        # 2. 2-opt（从最近邻出发）
        random.seed(42)
        start = time.time()
        tour_nn, _ = nearest_neighbor(dist)
        tour_2opt = tsp_solvers.local_search_2opt(tour_nn, dist)
        opt2_len = tsp_solvers.tour_length(tour_2opt, dist)
        opt2_time = (time.time() - start) * 1000
        results['2-opt'] = (opt2_len, opt2_len, opt2_len, opt2_time)
        
        # 3. 蚁群算法
        aco_lengths = []
        aco_times = []
        for run in range(n_runs):
            random.seed(run)
            np.random.seed(run)
            start = time.time()
            aco = tsp_solvers.AntColonyTSP(dist, n_ants=20, n_iter=50)
            _, length, _ = aco.solve()
            aco_lengths.append(length)
            aco_times.append((time.time() - start) * 1000)
        results['蚁群ACO'] = (min(aco_lengths), np.mean(aco_lengths), max(aco_lengths), np.mean(aco_times))
        
        # 4. 混合算法
        ma_lengths = []
        ma_times = []
        for run in range(n_runs):
            random.seed(run)
            np.random.seed(run)
            start = time.time()
            ma = tsp_solvers.MemeticTSP(dist, pop_size=30, n_iter=30)
            _, length, _ = ma.solve()
            ma_lengths.append(length)
            ma_times.append((time.time() - start) * 1000)
        results['混合Memetic'] = (min(ma_lengths), np.mean(ma_lengths), max(ma_lengths), np.mean(ma_times))
        
        # 5. 模拟退火
        sa_lengths = []
        sa_times = []
        for run in range(n_runs):
            random.seed(run)
            np.random.seed(run)
            start = time.time()
            sa = tsp_solvers.SimulatedAnnealingTSP(dist, T0=1000, T_min=1e-3, alpha=0.99, L=50)
            _, length, _ = sa.solve()
            sa_lengths.append(length)
            sa_times.append((time.time() - start) * 1000)
        results['模拟退火SA'] = (min(sa_lengths), np.mean(sa_lengths), max(sa_lengths), np.mean(sa_times))
        
        # 输出结果
        print(f"\n{'算法':<15} {'最好':>10} {'平均':>10} {'最差':>10} {'平均时间(ms)':>12} {'相对NN':>10}")
        print("-" * 70)
        
        nn_best = results['最近邻'][0]
        for name, (best, mean, worst, avg_time) in results.items():
            improvement = (nn_best - best) / nn_best * 100
            print(f"{name:<15} {best:>10.2f} {mean:>10.2f} {worst:>10.2f} {avg_time:>12.1f} {improvement:>9.1f}%")
    
    print("\n" + "=" * 90)
    print("实验结论：")
    print("  1. 2-opt局部搜索简单高效，从最近邻出发通常能改进20-30%")
    print("  2. 蚁群算法信息素正反馈机制适合TSP，但参数敏感")
    print("  3. 混合算法（GA+2-opt）通常质量最好，因为每个个体都做了局部优化")
    print("  4. 模拟退火实现简单，质量稳定但收敛较慢")
    print("  5. 问题规模越大，高级算法相对最近邻的优势越明显")
    print("=" * 90)


if __name__ == '__main__':
    run_experiment()
