# -*- coding: utf-8 -*-
"""
启发式算法 · 对比实验
======================
六层钻研法 · 第6层：对比创新

5种算法 × 4个测试函数 × 多次运行
- GA, SA, PSO, DE, ACO(连续版)
- Sphere, Rosenbrock, Rastrigin, Griewank
- 10维，500次迭代，5次运行取平均

输出：
1. 结果表格（平均最优值、标准差、最好值、时间）
2. 收敛曲线对比图（4个子图）
"""

import numpy as np
import time
import sys
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 导入统一框架
code_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '02_算法实现手札', '00_手动实现详解')
sys.path.insert(0, os.path.normpath(code_dir))
from importlib import import_module
heur = import_module('10_启发式算法_统一对比框架')


def run_full_experiment(n_dim=10, n_iter=500, n_runs=5):
    """运行完整对比实验"""
    print("=" * 90)
    print("启发式算法对比实验")
    print(f"维度={n_dim}, 迭代次数={n_iter}, 每次运行={n_runs}次")
    print("=" * 90)
    
    all_results = {}
    
    for func_name, (func, base_bounds) in heur.TEST_FUNCTIONS.items():
        print(f"\n{'─' * 90}")
        print(f"测试函数：{func_name}（{n_dim}维）")
        print(f"{'─' * 90}")
        
        bounds = base_bounds * n_dim
        all_results[func_name] = {}
        
        print(f"\n{'算法':<8} {'平均最优值':>14} {'标准差':>12} {'最好值':>14} {'平均时间':>10}")
        print("-" * 65)
        
        for algo_name in ['GA', 'SA', 'PSO', 'DE', 'ACO']:
            algo_func = heur.ALGORITHMS[algo_name]
            best_f_list = []
            time_list = []
            histories = []
            
            for run in range(n_runs):
                result = algo_func(func, bounds, n_iter=n_iter, seed=run * 100 + 42)
                best_f_list.append(result['best_f'])
                time_list.append(result['time'])
                histories.append(result['history'])
            
            avg_f = np.mean(best_f_list)
            std_f = np.std(best_f_list)
            best_f = np.min(best_f_list)
            avg_time = np.mean(time_list)
            avg_history = np.mean(histories, axis=0)
            
            all_results[func_name][algo_name] = {
                'avg_f': avg_f,
                'std_f': std_f,
                'best_f': best_f,
                'avg_time': avg_time,
                'avg_history': avg_history
            }
            
            print(f"{algo_name:<8} {avg_f:>14.6e} {std_f:>12.6e} {best_f:>14.6e} {avg_time:>9.3f}s")
    
    return all_results


def plot_convergence(all_results, n_iter=500):
    """画收敛曲线对比图"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    colors = {'GA': '#FF8FA3', 'SA': '#FFD97A', 'PSO': '#8FC1F0', 
              'DE': '#7BD3B2', 'ACO': '#C9AEE8'}
    
    for idx, func_name in enumerate(['Sphere', 'Rosenbrock', 'Rastrigin', 'Griewank']):
        ax = axes[idx]
        for algo_name in ['GA', 'SA', 'PSO', 'DE', 'ACO']:
            history = all_results[func_name][algo_name]['avg_history']
            ax.plot(range(len(history)), history, label=algo_name, 
                   color=colors[algo_name], linewidth=2)
        
        ax.set_xlabel('迭代次数')
        ax.set_ylabel('最优目标值（对数坐标）')
        ax.set_title(f'{func_name} 函数收敛曲线')
        ax.set_yscale('log')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               '启发式算法_收敛曲线对比.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n收敛曲线已保存：{output_path}")


def print_summary(all_results):
    """打印总结排名"""
    print("\n" + "=" * 90)
    print("总结：各算法在4个测试函数上的平均排名（1=最好）")
    print("=" * 90)
    
    rankings = {algo: [] for algo in ['GA', 'SA', 'PSO', 'DE', 'ACO']}
    
    for func_name in all_results:
        # 按平均最优值排序
        scores = [(algo, all_results[func_name][algo]['avg_f']) 
                  for algo in all_results[func_name]]
        scores.sort(key=lambda x: x[1])
        for rank, (algo, _) in enumerate(scores):
            rankings[algo].append(rank + 1)
    
    print(f"\n{'算法':<8} {'Sphere':>8} {'Rosenbrock':>12} {'Rastrigin':>10} {'Griewank':>10} {'平均排名':>10}")
    print("-" * 65)
    for algo in ['GA', 'SA', 'PSO', 'DE', 'ACO']:
        ranks = rankings[algo]
        avg_rank = np.mean(ranks)
        print(f"{algo:<8} {ranks[0]:>8} {ranks[1]:>12} {ranks[2]:>10} {ranks[3]:>10} {avg_rank:>10.2f}")


if __name__ == '__main__':
    start = time.time()
    
    # 运行实验
    results = run_full_experiment(n_dim=10, n_iter=500, n_runs=5)
    
    # 画收敛曲线
    plot_convergence(results, n_iter=500)
    
    # 打印总结
    print_summary(results)
    
    elapsed = time.time() - start
    print(f"\n总耗时：{elapsed:.1f}秒")
    print("实验完成！")
