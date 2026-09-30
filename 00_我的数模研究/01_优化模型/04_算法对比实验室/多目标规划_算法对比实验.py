# -*- coding: utf-8 -*-
"""
多目标规划 · 算法对比实验
==========================
六层钻研法 · 第6层：对比创新

对比三种多目标优化方法：
1. 加权法（Weighted Sum）：遍历权重，每次解一个单目标
2. ε约束法（ε-Constraint）：遍历ε，每次解一个约束单目标
3. NSGA-II：进化算法，一次运行得到一组解

测试问题：
- 简单双目标（凸前沿，1维）
- ZDT1（凸前沿，30维）
- 非凸测试问题（非凸前沿，检验加权法的缺陷）

评价指标：
- 解的数量
- 覆盖范围（目标值范围）
- 与真实前沿的平均误差
- 运行时间
"""

import numpy as np
import time
import sys
import os

# 导入自己实现的算法
code_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '02_算法实现手札', '00_手动实现详解')
sys.path.insert(0, os.path.normpath(code_dir))
from importlib import import_module

classic = import_module('07_多目标经典方法_手动实现')
nsga2_mod = import_module('08_NSGA2_手动实现')


# ============================================================
# 第一部分：测试问题
# ============================================================
def simple_convex(x):
    """简单凸双目标：min f1=x², f2=(x-2)², x∈[0,2]
    真实前沿：x∈[0,2], f1∈[0,4], f2∈[0,4]（凸）"""
    return np.array([x[0]**2, (x[0]-2)**2])

def nonconvex_problem(x):
    """非凸双目标：min f1=x, f2=1-x² + 0.3*sin(5πx), x∈[0,1]
    真实前沿是非凸的（有凹陷），加权法会漏掉中间部分"""
    f1 = x[0]
    f2 = 1 - x[0]**2 + 0.3 * np.sin(5 * np.pi * x[0])
    return np.array([f1, f2])

def zdt1(x):
    """ZDT1：30维，真实前沿f2=1-sqrt(f1)"""
    n = len(x)
    f1 = x[0]
    g = 1 + 9 / (n - 1) * np.sum(x[1:])
    f2 = g * (1 - np.sqrt(f1 / g))
    return np.array([f1, f2])


# ============================================================
# 第二部分：评价指标
# ============================================================
def mean_distance_to_front(pareto_obj, true_front_func):
    """
    计算得到的Pareto前沿到真实前沿的平均距离
    
    对每个解，找真实前沿上最近的点的距离。
    """
    distances = []
    for f in pareto_obj:
        # 在真实前沿上采样找最近点
        min_dist = np.inf
        for t in np.linspace(0, 1, 500):
            f_true = true_front_func(t)
            dist = np.sqrt(np.sum((f - f_true)**2))
            if dist < min_dist:
                min_dist = dist
        distances.append(min_dist)
    return np.mean(distances)


def coverage(pareto_obj):
    """计算Pareto前沿在每个目标上的覆盖范围"""
    return {
        'f1_range': (pareto_obj[:,0].min(), pareto_obj[:,0].max()),
        'f2_range': (pareto_obj[:,1].min(), pareto_obj[:,1].max()),
        'f1_span': pareto_obj[:,0].max() - pareto_obj[:,0].min(),
        'f2_span': pareto_obj[:,1].max() - pareto_obj[:,1].min()
    }


# ============================================================
# 第三部分：主实验
# ============================================================
def run_experiment():
    print("=" * 90)
    print("多目标规划算法对比实验")
    print("=" * 90)
    
    np.random.seed(42)
    
    # ---- 测试1：简单凸双目标 ----
    print("\n" + "─" * 90)
    print("测试1：简单凸双目标（min f1=x², f2=(x-2)², x∈[0,2]）")
    print("真实前沿：凸曲线，f1∈[0,4], f2∈[0,4]")
    print("─" * 90)
    
    x0 = np.array([1.0])
    bounds = [(0, 2)]
    
    # 加权法
    start = time.time()
    x_ws, f_ws = classic.weighted_sum_method(simple_convex, x0, bounds, n_weights=20)
    time_ws = time.time() - start
    pareto_ws, _ = classic.extract_pareto_front(f_ws)
    
    # ε约束法
    start = time.time()
    x_eps, f_eps = classic.epsilon_constraint_method(simple_convex, x0, bounds, n_eps=20)
    time_eps = time.time() - start
    pareto_eps, _ = classic.extract_pareto_front(f_eps)
    
    # NSGA-II
    start = time.time()
    result = nsga2_mod.nsga2(simple_convex, bounds, pop_size=50, n_generations=100, verbose=False)
    time_nsga = time.time() - start
    pareto_nsga = result['pareto_front']
    
    print(f"\n{'方法':<12} {'解数':>6} {'f1范围':>16} {'f2范围':>16} {'时间':>8}")
    print("-" * 60)
    print(f"{'加权法':<12} {len(pareto_ws):>6} "
          f"[{pareto_ws[:,0].min():.3f},{pareto_ws[:,0].max():.3f}]  "
          f"[{pareto_ws[:,1].min():.3f},{pareto_ws[:,1].max():.3f}]  "
          f"{time_ws:>7.3f}s")
    print(f"{'ε约束法':<12} {len(pareto_eps):>6} "
          f"[{pareto_eps[:,0].min():.3f},{pareto_eps[:,0].max():.3f}]  "
          f"[{pareto_eps[:,1].min():.3f},{pareto_eps[:,1].max():.3f}]  "
          f"{time_eps:>7.3f}s")
    print(f"{'NSGA-II':<12} {len(pareto_nsga):>6} "
          f"[{pareto_nsga[:,0].min():.3f},{pareto_nsga[:,0].max():.3f}]  "
          f"[{pareto_nsga[:,1].min():.3f},{pareto_nsga[:,1].max():.3f}]  "
          f"{time_nsga:>7.3f}s")
    
    # ---- 测试2：非凸问题 ----
    print("\n" + "─" * 90)
    print("测试2：非凸双目标（加权法的噩梦）")
    print("min f1=x, f2=1-x²+0.3sin(5πx), x∈[0,1]")
    print("真实前沿非凸，加权法会漏掉中间凹陷部分")
    print("─" * 90)
    
    x0 = np.array([0.5])
    bounds = [(0, 1)]
    
    # 真实前沿函数
    def true_front_nonconvex(t):
        return np.array([t, 1 - t**2 + 0.3 * np.sin(5 * np.pi * t)])
    
    # 加权法
    start = time.time()
    x_ws, f_ws = classic.weighted_sum_method(nonconvex_problem, x0, bounds, n_weights=30)
    time_ws = time.time() - start
    pareto_ws, _ = classic.extract_pareto_front(f_ws)
    err_ws = mean_distance_to_front(pareto_ws, true_front_nonconvex)
    
    # ε约束法
    start = time.time()
    x_eps, f_eps = classic.epsilon_constraint_method(nonconvex_problem, x0, bounds, n_eps=30)
    time_eps = time.time() - start
    pareto_eps, _ = classic.extract_pareto_front(f_eps)
    err_eps = mean_distance_to_front(pareto_eps, true_front_nonconvex)
    
    # NSGA-II
    start = time.time()
    result = nsga2_mod.nsga2(nonconvex_problem, bounds, pop_size=80, n_generations=150, verbose=False)
    time_nsga = time.time() - start
    pareto_nsga = result['pareto_front']
    err_nsga = mean_distance_to_front(pareto_nsga, true_front_nonconvex)
    
    print(f"\n{'方法':<12} {'解数':>6} {'f1范围':>16} {'平均误差':>10} {'时间':>8}")
    print("-" * 60)
    print(f"{'加权法':<12} {len(pareto_ws):>6} "
          f"[{pareto_ws[:,0].min():.3f},{pareto_ws[:,0].max():.3f}]  "
          f"{err_ws:>10.6f} {time_ws:>7.3f}s")
    print(f"{'ε约束法':<12} {len(pareto_eps):>6} "
          f"[{pareto_eps[:,0].min():.3f},{pareto_eps[:,0].max():.3f}]  "
          f"{err_eps:>10.6f} {time_eps:>7.3f}s")
    print(f"{'NSGA-II':<12} {len(pareto_nsga):>6} "
          f"[{pareto_nsga[:,0].min():.3f},{pareto_nsga[:,0].max():.3f}]  "
          f"{err_nsga:>10.6f} {time_nsga:>7.3f}s")
    
    print(f"\n💡 注意：加权法的f1范围可能不连续（漏掉非凸部分），ε约束法和NSGA-II能覆盖整个前沿")
    
    # ---- 测试3：ZDT1（30维）----
    print("\n" + "─" * 90)
    print("测试3：ZDT1（30维高维问题）")
    print("真实前沿：f2 = 1 - sqrt(f1), f1∈[0,1]")
    print("─" * 90)
    
    n = 30
    x0 = np.ones(n) * 0.5
    bounds = [(0, 1)] * n
    
    def true_front_zdt1(t):
        return np.array([t, 1 - np.sqrt(t)])
    
    # 加权法
    start = time.time()
    x_ws, f_ws = classic.weighted_sum_method(zdt1, x0, bounds, n_weights=15)
    time_ws = time.time() - start
    pareto_ws, _ = classic.extract_pareto_front(f_ws)
    err_ws = mean_distance_to_front(pareto_ws, true_front_zdt1)
    
    # NSGA-II
    start = time.time()
    result = nsga2_mod.nsga2(zdt1, bounds, pop_size=100, n_generations=200, verbose=False)
    time_nsga = time.time() - start
    pareto_nsga = result['pareto_front']
    err_nsga = mean_distance_to_front(pareto_nsga, true_front_zdt1)
    
    print(f"\n{'方法':<12} {'解数':>6} {'f1范围':>16} {'平均误差':>10} {'时间':>8}")
    print("-" * 60)
    print(f"{'加权法':<12} {len(pareto_ws):>6} "
          f"[{pareto_ws[:,0].min():.4f},{pareto_ws[:,0].max():.4f}]  "
          f"{err_ws:>10.6f} {time_ws:>7.3f}s")
    print(f"{'NSGA-II':<12} {len(pareto_nsga):>6} "
          f"[{pareto_nsga[:,0].min():.4f},{pareto_nsga[:,0].max():.4f}]  "
          f"{err_nsga:>10.6f} {time_nsga:>7.3f}s")
    
    print(f"\n💡 高维问题中，加权法需要多次求解单目标（每次都是30维优化），NSGA-II一次运行得到更多解")


# ============================================================
# 第四部分：结论
# ============================================================
def print_conclusion():
    print("\n" + "=" * 90)
    print("实验结论")
    print("=" * 90)
    print("""
1. 加权法：
   - 优点：简单，每次只需解一个单目标问题
   - 缺点：只能得到Pareto前沿的凸部分，非凸前沿会漏掉中间解
   - 适用：凸问题，需要精确解，且权重有明确物理意义

2. ε约束法：
   - 优点：可以得到整个Pareto前沿（包括非凸部分）
   - 缺点：需要为约束目标选择合适的ε范围，计算量较大
   - 适用：非凸问题，需要精确的Pareto前沿

3. NSGA-II：
   - 优点：一次运行得到一组解，天然适合非凸和高维问题，不需要梯度
   - 缺点：是近似算法，不保证精确收敛，需要调参（种群大小、迭代次数）
   - 适用：复杂、高维、非凸问题，需要近似Pareto前沿

4. 选择建议：
   - 问题简单（低维、凸）：加权法或ε约束法（精确）
   - 问题复杂（高维、非凸、非线性）：NSGA-II（近似但高效）
   - 比赛中：通常用NSGA-II，因为建模问题往往复杂且非凸
   - 有明确偏好：理想点法或目标规划（直接得到一个偏好解）
""")


if __name__ == '__main__':
    run_experiment()
    print_conclusion()
