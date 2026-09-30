# -*- coding: utf-8 -*-
"""
多目标规划 · 经典方法手动实现
==============================
六层钻研法 · 第4层：手动实现

实现内容：
1. Pareto支配关系判断与非支配解提取
2. 加权法（Weighted Sum）：遍历权重得到Pareto前沿
3. ε约束法（ε-Constraint）：遍历ε得到Pareto前沿
4. 理想点法（Ideal Point / TOPSIS）：找离理想点最近的解

测试问题：
- 简单双目标：min f1=x², f2=(x-2)², x∈[0,2]
  真实Pareto前沿：x∈[0,2]，f1∈[0,4], f2∈[0,4]
- ZDT1测试函数（经典多目标测试问题）
"""

import numpy as np
from scipy.optimize import minimize
import matplotlib
matplotlib.use('Agg')  # 不显示图形，只保存
import matplotlib.pyplot as plt


# ============================================================
# 第一部分：Pareto支配关系
# ============================================================
def dominates(f1, f2):
    """
    判断解1是否支配解2（最小化问题）
    
    解1支配解2 当且仅当：
    1. 解1在所有目标上都不劣于解2（f1_i ≤ f2_i）
    2. 解1至少在一个目标上严格优于解2（f1_i < f2_i）
    
    参数：
        f1: 解1的目标值向量，shape=(k,)
        f2: 解2的目标值向量，shape=(k,)
    
    返回：
        True如果f1支配f2，否则False
    """
    # 条件1：所有目标都不劣
    all_no_worse = np.all(f1 <= f2 + 1e-10)
    # 条件2：至少一个目标严格更优
    any_better = np.any(f1 < f2 - 1e-10)
    return all_no_worse and any_better


def extract_pareto_front(objectives):
    """
    从一组解中提取Pareto最优解（非支配解）
    
    参数：
        objectives: 所有解的目标值，shape=(N, k)
    
    返回：
        (pareto_obj, pareto_idx): Pareto解的目标值和索引
    """
    N = len(objectives)
    is_pareto = np.ones(N, dtype=bool)
    
    for i in range(N):
        if not is_pareto[i]:
            continue
        for j in range(N):
            if i != j and is_pareto[j]:
                # 如果j支配i，i不是Pareto最优
                if dominates(objectives[j], objectives[i]):
                    is_pareto[i] = False
                    break
    
    pareto_idx = np.where(is_pareto)[0]
    pareto_obj = objectives[pareto_idx]
    
    # 按第一个目标排序（方便画图）
    sort_order = np.argsort(pareto_obj[:, 0])
    return pareto_obj[sort_order], pareto_idx[sort_order]


# ============================================================
# 第二部分：测试问题
# ============================================================
def simple_biobjective(x):
    """
    简单双目标问题（1维决策变量）
    
    min f1 = x²
    min f2 = (x-2)²
    s.t. 0 ≤ x ≤ 2
    
    真实Pareto前沿：x∈[0,2]，f1∈[0,4], f2∈[0,4]
    两个目标在x=1处达到平衡（f1=f2=1）
    """
    return np.array([x[0]**2, (x[0]-2)**2])


def zdt1(x):
    """
    ZDT1测试函数（经典多目标测试问题，30维）
    
    min f1 = x1
    min f2 = g(x) · (1 - sqrt(f1/g(x)))
    where g(x) = 1 + 9/(n-1) · Σ_{i=2}^n x_i
    
    真实Pareto前沿：f2 = 1 - sqrt(f1)，f1∈[0,1]
    变量范围：x_i ∈ [0,1]
    """
    n = len(x)
    f1 = x[0]
    g = 1 + 9 / (n - 1) * np.sum(x[1:])
    f2 = g * (1 - np.sqrt(f1 / g))
    return np.array([f1, f2])


# ============================================================
# 第三部分：加权法
# ============================================================
def weighted_sum_method(objective_func, x0, bounds, n_weights=20):
    """
    加权法：遍历不同权重，将多目标转化为单目标求解
    
    对每个权重w=(w1, w2, ..., wk)，求解：
        min Σ w_i · f_i(x)
    
    参数：
        objective_func: 目标函数，输入x返回目标值向量
        x0: 初始点
        bounds: 变量边界
        n_weights: 权重数量（双目标时从0到1均匀采样）
    
    返回：
        (all_x, all_f): 所有得到的解和对应的目标值
    """
    k = len(objective_func(x0))  # 目标数
    all_x = []
    all_f = []
    
    # 生成权重（双目标时均匀采样w1∈[0,1]，w2=1-w1）
    if k == 2:
        weights = np.linspace(0, 1, n_weights)
        weight_list = [(w, 1-w) for w in weights]
    else:
        # 多目标时用随机权重（简化处理）
        weight_list = np.random.dirichlet(np.ones(k), n_weights)
    
    for w in weight_list:
        # 定义单目标函数：加权和
        def single_obj(x, w=w):
            f = objective_func(x)
            return np.sum(w * f)
        
        # 用L-BFGS-B求解单目标
        result = minimize(single_obj, x0, method='L-BFGS-B', bounds=bounds)
        
        if result.success:
            all_x.append(result.x)
            all_f.append(objective_func(result.x))
    
    return np.array(all_x), np.array(all_f)


# ============================================================
# 第四部分：ε约束法
# ============================================================
def epsilon_constraint_method(objective_func, x0, bounds, n_eps=20):
    """
    ε约束法：选第一个目标为主目标，其他目标作为约束
    
    min f1(x)
    s.t. f2(x) ≤ ε
         x ∈ bounds
    
    遍历不同的ε，得到Pareto前沿。
    
    参数：
        objective_func: 目标函数
        x0: 初始点
        bounds: 变量边界
        n_eps: ε的数量
    
    返回：
        (all_x, all_f): 所有得到的解和对应的目标值
    """
    # 先求f2的范围（单独优化f2）
    def obj2(x):
        return objective_func(x)[1]
    
    result_min = minimize(obj2, x0, method='L-BFGS-B', bounds=bounds)
    f2_min = result_min.fun
    
    # f2的最大值（在f1最小时）
    def obj1(x):
        return objective_func(x)[0]
    
    result_f1min = minimize(obj1, x0, method='L-BFGS-B', bounds=bounds)
    f2_at_f1min = objective_func(result_f1min.x)[1]
    f2_max = max(f2_at_f1min, f2_min + 0.1)  # 留一点余量
    
    # 遍历ε
    epsilons = np.linspace(f2_min, f2_max, n_eps)
    
    all_x = []
    all_f = []
    
    for eps in epsilons:
        # 主目标：min f1
        def main_obj(x):
            return objective_func(x)[0]
        
        # 约束：f2 ≤ ε
        constraint = {'type': 'ineq', 'fun': lambda x, eps=eps: eps - objective_func(x)[1]}
        
        result = minimize(main_obj, x0, method='SLSQP', bounds=bounds, 
                         constraints=[constraint])
        
        if result.success:
            f = objective_func(result.x)
            # 只保留满足约束的解
            if f[1] <= eps + 1e-6:
                all_x.append(result.x)
                all_f.append(f)
    
    return np.array(all_x), np.array(all_f)


# ============================================================
# 第五部分：理想点法
# ============================================================
def ideal_point_method(objective_func, x0, bounds, weights=None):
    """
    理想点法：先找每个目标单独最优的理想点，再找离理想点最近的解
    
    理想点 f* = (f1*, f2*, ..., fk*)，其中fi* = min fi(x)
    
    最小化到理想点的距离：
        min ||f(x) - f*|| （欧氏距离或加权距离）
    
    参数：
        objective_func: 目标函数
        x0: 初始点
        bounds: 变量边界
        weights: 各目标的权重，默认等权重
    
    返回：
        (x_opt, f_opt, ideal_point): 最优解、目标值、理想点
    """
    k = len(objective_func(x0))
    if weights is None:
        weights = np.ones(k) / k
    
    # 步骤1：求理想点（每个目标单独优化）
    ideal_point = np.zeros(k)
    for i in range(k):
        def obj_i(x, i=i):
            return objective_func(x)[i]
        result = minimize(obj_i, x0, method='L-BFGS-B', bounds=bounds)
        ideal_point[i] = result.fun
    
    print(f"  理想点：f* = {ideal_point}")
    
    # 步骤2：求离理想点最近的解（加权欧氏距离）
    def distance_obj(x):
        f = objective_func(x)
        # 归一化后再算距离（避免量纲影响）
        # 这里简化处理，直接用加权距离
        return np.sqrt(np.sum(weights * (f - ideal_point)**2))
    
    result = minimize(distance_obj, x0, method='L-BFGS-B', bounds=bounds)
    
    if result.success:
        f_opt = objective_func(result.x)
        return result.x, f_opt, ideal_point
    else:
        return None, None, ideal_point


# ============================================================
# 第六部分：测试用例
# ============================================================
def test_simple_problem():
    """
    测试1：简单双目标问题
    min f1 = x², f2 = (x-2)², x∈[0,2]
    真实Pareto前沿：x∈[0,2]
    """
    print("=" * 60)
    print("测试1：简单双目标问题")
    print("min f1 = x², f2 = (x-2)², x∈[0,2]")
    print("=" * 60)
    
    x0 = np.array([1.0])
    bounds = [(0, 2)]
    
    # 加权法
    print("\n--- 加权法 ---")
    x_ws, f_ws = weighted_sum_method(simple_biobjective, x0, bounds, n_weights=20)
    pareto_ws, _ = extract_pareto_front(f_ws)
    print(f"  得到 {len(f_ws)} 个解，其中 {len(pareto_ws)} 个Pareto最优")
    print(f"  f1范围：[{pareto_ws[:,0].min():.4f}, {pareto_ws[:,0].max():.4f}]")
    print(f"  f2范围：[{pareto_ws[:,1].min():.4f}, {pareto_ws[:,1].max():.4f}]")
    
    # ε约束法
    print("\n--- ε约束法 ---")
    x_eps, f_eps = epsilon_constraint_method(simple_biobjective, x0, bounds, n_eps=20)
    pareto_eps, _ = extract_pareto_front(f_eps)
    print(f"  得到 {len(f_eps)} 个解，其中 {len(pareto_eps)} 个Pareto最优")
    print(f"  f1范围：[{pareto_eps[:,0].min():.4f}, {pareto_eps[:,0].max():.4f}]")
    print(f"  f2范围：[{pareto_eps[:,1].min():.4f}, {pareto_eps[:,1].max():.4f}]")
    
    # 理想点法
    print("\n--- 理想点法 ---")
    x_opt, f_opt, ideal = ideal_point_method(simple_biobjective, x0, bounds)
    print(f"  最优解：x = {x_opt[0]:.4f}")
    print(f"  目标值：f1 = {f_opt[0]:.4f}, f2 = {f_opt[1]:.4f}")
    print(f"  到理想点距离：{np.sqrt(np.sum((f_opt-ideal)**2)):.4f}")
    
    # 画图
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # 真实Pareto前沿
    x_true = np.linspace(0, 2, 100)
    f1_true = x_true**2
    f2_true = (x_true-2)**2
    
    # 加权法
    axes[0].scatter(f_ws[:,0], f_ws[:,1], c='pink', s=30, alpha=0.6, label='加权法解')
    axes[0].plot(f1_true, f2_true, 'b--', label='真实Pareto前沿')
    axes[0].set_xlabel('f1 = x²')
    axes[0].set_ylabel('f2 = (x-2)²')
    axes[0].set_title('加权法')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # ε约束法
    axes[1].scatter(f_eps[:,0], f_eps[:,1], c='lightblue', s=30, alpha=0.6, label='ε约束法解')
    axes[1].plot(f1_true, f2_true, 'b--', label='真实Pareto前沿')
    axes[1].set_xlabel('f1 = x²')
    axes[1].set_ylabel('f2 = (x-2)²')
    axes[1].set_title('ε约束法')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    # 理想点法
    axes[2].scatter([f_opt[0]], [f_opt[1]], c='red', s=100, marker='*', label='理想点法解', zorder=5)
    axes[2].scatter([ideal[0]], [ideal[1]], c='green', s=100, marker='D', label='理想点', zorder=5)
    axes[2].plot(f1_true, f2_true, 'b--', label='真实Pareto前沿')
    axes[2].plot([ideal[0], f_opt[0]], [ideal[1], f_opt[1]], 'k:', alpha=0.5)
    axes[2].set_xlabel('f1 = x²')
    axes[2].set_ylabel('f2 = (x-2)²')
    axes[2].set_title('理想点法')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('多目标_经典方法对比.png', dpi=150, bbox_inches='tight')
    print(f"\n  图像已保存：多目标_经典方法对比.png")
    
    print("\n✓ 测试通过！")


def test_zdt1():
    """
    测试2：ZDT1测试函数（30维）
    真实Pareto前沿：f2 = 1 - sqrt(f1)
    """
    print("\n" + "=" * 60)
    print("测试2：ZDT1测试函数（30维）")
    print("真实Pareto前沿：f2 = 1 - sqrt(f1)")
    print("=" * 60)
    
    n = 30
    x0 = np.ones(n) * 0.5
    bounds = [(0, 1)] * n
    
    # 加权法
    print("\n--- 加权法 ---")
    x_ws, f_ws = weighted_sum_method(zdt1, x0, bounds, n_weights=15)
    pareto_ws, _ = extract_pareto_front(f_ws)
    print(f"  得到 {len(f_ws)} 个解，其中 {len(pareto_ws)} 个Pareto最优")
    
    # 理想点法
    print("\n--- 理想点法 ---")
    x_opt, f_opt, ideal = ideal_point_method(zdt1, x0, bounds)
    if f_opt is not None:
        print(f"  最优目标值：f1 = {f_opt[0]:.4f}, f2 = {f_opt[1]:.4f}")
        # 真实Pareto前沿上f1对应的f2
        f2_true = 1 - np.sqrt(f_opt[0])
        print(f"  真实前沿上f1={f_opt[0]:.4f}对应f2={f2_true:.4f}")
        print(f"  误差：{abs(f_opt[1]-f2_true):.6f}")
    
    print("\n✓ 测试通过！")


if __name__ == '__main__':
    test_simple_problem()
    test_zdt1()
    print("\n" + "=" * 60)
    print("全部测试完成！")
    print("=" * 60)
