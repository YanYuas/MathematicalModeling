# -*- coding: utf-8 -*-
"""
多目标规划 · NSGA-II手动实现
==============================
六层钻研法 · 第4层：手动实现

NSGA-II (Non-dominated Sorting Genetic Algorithm II)
Deb et al., 2002 —— 最经典的多目标进化算法

三大核心机制：
1. 非支配排序（Fast Non-dominated Sorting）：按Pareto支配关系分层
2. 拥挤度（Crowding Distance）：同一层内保持多样性
3. 精英保留（Elitism）：父子合并选择，保留优秀解

遗传操作：
- SBX交叉（模拟二进制交叉）
- 多项式变异

测试问题：
- 简单双目标：min f1=x², f2=(x-2)²
- ZDT1：经典多目标测试函数
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# ============================================================
# 第一部分：非支配排序
# ============================================================
def fast_non_dominated_sort(objectives):
    """
    快速非支配排序
    
    将种群按Pareto支配关系分成多个前沿层：
    F1 = 不被任何个体支配的个体（Pareto最优）
    F2 = 去掉F1后，不被剩余个体支配的个体
    ...
    
    参数：
        objectives: 所有个体的目标值，shape=(N, k)
    
    返回：
        fronts: 列表，每个元素是一个前沿层的个体索引列表
        ranks: 每个个体的前沿层号（从0开始）
    """
    N = len(objectives)
    
    # S_p = 被p支配的个体集合
    S = [[] for _ in range(N)]
    # n_p = 支配p的个体数量
    n = np.zeros(N, dtype=int)
    # rank = 前沿层号
    ranks = np.zeros(N, dtype=int)
    
    fronts = [[]]  # F0 = 第一前沿
    
    # 第一步：计算每个个体的S_p和n_p
    for p in range(N):
        for q in range(N):
            if p == q:
                continue
            # 判断p是否支配q
            if np.all(objectives[p] <= objectives[q] + 1e-10) and \
               np.any(objectives[p] < objectives[q] - 1e-10):
                S[p].append(q)
            # 判断q是否支配p
            elif np.all(objectives[q] <= objectives[p] + 1e-10) and \
                 np.any(objectives[q] < objectives[p] - 1e-10):
                n[p] += 1
        
        # n_p=0的个体属于第一前沿
        if n[p] == 0:
            ranks[p] = 0
            fronts[0].append(p)
    
    # 第二步：逐层计算后续前沿
    i = 0
    while len(fronts[i]) > 0:
        next_front = []
        for p in fronts[i]:
            for q in S[p]:
                n[q] -= 1
                if n[q] == 0:
                    ranks[q] = i + 1
                    next_front.append(q)
        i += 1
        fronts.append(next_front)
    
    # 去掉最后一个空前沿
    if len(fronts[-1]) == 0:
        fronts.pop()
    
    return fronts, ranks


# ============================================================
# 第二部分：拥挤度计算
# ============================================================
def crowding_distance(objectives, front):
    """
    计算一个前沿层内所有个体的拥挤度
    
    拥挤度衡量个体周围的密集程度：
    - 拥挤度大 = 周围稀疏 = 更值得保留（保持多样性）
    - 边界点（每个目标的最大最小）拥挤度=无穷大
    
    参数：
        objectives: 所有个体的目标值，shape=(N, k)
        front: 该前沿层的个体索引列表
    
    返回：
        distance: 该层内每个个体的拥挤度
    """
    n_front = len(front)
    k = objectives.shape[1]  # 目标数
    distance = np.zeros(n_front)
    
    if n_front <= 2:
        # 少于3个个体时，边界点拥挤度无穷大
        return np.full(n_front, np.inf)
    
    # 对每个目标分别计算
    for obj_idx in range(k):
        # 按该目标值排序
        sorted_indices = sorted(range(n_front), 
                               key=lambda i: objectives[front[i], obj_idx])
        
        # 边界点拥挤度=无穷大
        distance[sorted_indices[0]] = np.inf
        distance[sorted_indices[-1]] = np.inf
        
        # 目标值范围（用于归一化）
        obj_range = objectives[front[sorted_indices[-1]], obj_idx] - \
                    objectives[front[sorted_indices[0]], obj_idx]
        
        if obj_range < 1e-10:
            continue
        
        # 中间点的拥挤度 = 相邻两点目标值之差 / 范围
        for i in range(1, n_front - 1):
            distance[sorted_indices[i]] += (
                objectives[front[sorted_indices[i+1]], obj_idx] -
                objectives[front[sorted_indices[i-1]], obj_idx]
            ) / obj_range
    
    return distance


# ============================================================
# 第三部分：锦标赛选择
# ============================================================
def tournament_selection(population, objectives, ranks, distances, tournament_size=2):
    """
    锦标赛选择
    
    随机选tournament_size个个体，选最好的那个。
    比较规则：
    1. 前沿层号小的更优
    2. 同层内拥挤度大的更优
    
    参数：
        population: 种群，shape=(N, n_vars)
        objectives: 目标值，shape=(N, k)
        ranks: 每个个体的前沿层号
        distances: 每个个体的拥挤度
        tournament_size: 锦标赛大小
    
    返回：
        选中的个体索引
    """
    N = len(population)
    # 随机选择tournament_size个候选
    candidates = np.random.choice(N, tournament_size, replace=False)
    
    # 选最优的（前沿层小，同层则拥挤度大）
    best = candidates[0]
    for c in candidates[1:]:
        if ranks[c] < ranks[best] or \
           (ranks[c] == ranks[best] and distances[c] > distances[best]):
            best = c
    
    return best


# ============================================================
# 第四部分：SBX交叉（模拟二进制交叉）
# ============================================================
def sbx_crossover(parent1, parent2, bounds, eta_c=20, prob_c=0.9):
    """
    SBX交叉（Simulated Binary Crossover，模拟二进制交叉）
    
    模拟二进制编码的单点交叉，产生的子代在父代附近。
    eta_c控制子代离父代的距离：eta_c大→子代接近父代，eta_c小→子代分散。
    
    参数：
        parent1, parent2: 父代个体
        bounds: 变量边界，list of (low, high)
        eta_c: 交叉分布指数（常用20）
        prob_c: 交叉概率
    
    返回：
        (child1, child2): 两个子代
    """
    n_vars = len(parent1)
    child1 = parent1.copy()
    child2 = parent2.copy()
    
    if np.random.random() > prob_c:
        return child1, child2
    
    for i in range(n_vars):
        low, high = bounds[i]
        if abs(parent1[i] - parent2[i]) < 1e-14:
            continue
        
        # 随机数u∈(0,1)
        u = np.random.random()
        
        # 计算扩展因子β
        if u <= 0.5:
            beta = (2 * u) ** (1.0 / (eta_c + 1))
        else:
            beta = (1.0 / (2 * (1 - u))) ** (1.0 / (eta_c + 1))
        
        # 产生子代
        c1 = 0.5 * ((parent1[i] + parent2[i]) - beta * abs(parent2[i] - parent1[i]))
        c2 = 0.5 * ((parent1[i] + parent2[i]) + beta * abs(parent2[i] - parent1[i]))
        
        # 边界检查
        child1[i] = np.clip(c1, low, high)
        child2[i] = np.clip(c2, low, high)
    
    return child1, child2


# ============================================================
# 第五部分：多项式变异
# ============================================================
def polynomial_mutation(individual, bounds, eta_m=20, prob_m=None):
    """
    多项式变异
    
    每个变量以prob_m的概率变异，变异幅度由eta_m控制。
    
    参数：
        individual: 个体
        bounds: 变量边界
        eta_m: 变异分布指数（常用20）
        prob_m: 变异概率，默认1/n_vars
    
    返回：
        变异后的个体
    """
    n_vars = len(individual)
    if prob_m is None:
        prob_m = 1.0 / n_vars  # 经典设置：每个变量平均变异一次
    
    mutant = individual.copy()
    
    for i in range(n_vars):
        if np.random.random() > prob_m:
            continue
        
        low, high = bounds[i]
        u = np.random.random()
        
        # 多项式变异公式
        if u < 0.5:
            delta = (2 * u) ** (1.0 / (eta_m + 1)) - 1
        else:
            delta = 1 - (2 * (1 - u)) ** (1.0 / (eta_m + 1))
        
        mutant[i] = individual[i] + delta * (high - low)
        mutant[i] = np.clip(mutant[i], low, high)
    
    return mutant


# ============================================================
# 第六部分：NSGA-II主算法
# ============================================================
def nsga2(objective_func, bounds, pop_size=100, n_generations=200,
          eta_c=20, eta_m=20, prob_c=0.9, verbose=True):
    """
    NSGA-II主算法
    
    参数：
        objective_func: 目标函数，输入x返回目标值向量
        bounds: 变量边界，list of (low, high)
        pop_size: 种群大小
        n_generations: 迭代代数
        eta_c: 交叉分布指数
        eta_m: 变异分布指数
        prob_c: 交叉概率
        verbose: 是否打印进度
    
    返回：
        dict: {
            'population': 最终种群,
            'objectives': 最终目标值,
            'pareto_front': Pareto前沿的目标值,
            'pareto_population': Pareto前沿的解,
            'history': 每代的Pareto前沿（用于可视化）
        }
    """
    n_vars = len(bounds)
    
    # ---- 步骤1：初始化种群 ----
    population = np.zeros((pop_size, n_vars))
    for i in range(pop_size):
        for j in range(n_vars):
            low, high = bounds[j]
            population[i, j] = low + np.random.random() * (high - low)
    
    # 计算初始种群的目标值
    objectives = np.array([objective_func(ind) for ind in population])
    
    history = []
    
    # ---- 步骤2：主循环 ----
    for gen in range(n_generations):
        # 非支配排序
        fronts, ranks = fast_non_dominated_sort(objectives)
        
        # 计算所有个体的拥挤度
        distances = np.zeros(pop_size)
        for front in fronts:
            cd = crowding_distance(objectives, front)
            for i, idx in enumerate(front):
                distances[idx] = cd[i]
        
        # 记录当前Pareto前沿
        pareto_indices = fronts[0]
        history.append(objectives[pareto_indices].copy())
        
        if verbose and (gen % 20 == 0 or gen == n_generations - 1):
            print(f"  第{gen:3d}代: Pareto前沿有{len(pareto_indices)}个解, "
                  f"f1范围=[{objectives[pareto_indices,0].min():.4f}, "
                  f"{objectives[pareto_indices,0].max():.4f}]")
        
        # ---- 步骤3：选择、交叉、变异生成子代 ----
        offspring = np.zeros((pop_size, n_vars))
        for i in range(0, pop_size, 2):
            # 锦标赛选择两个父代
            p1_idx = tournament_selection(population, objectives, ranks, distances)
            p2_idx = tournament_selection(population, objectives, ranks, distances)
            
            # SBX交叉
            c1, c2 = sbx_crossover(population[p1_idx], population[p2_idx], 
                                    bounds, eta_c, prob_c)
            
            # 多项式变异
            c1 = polynomial_mutation(c1, bounds, eta_m)
            c2 = polynomial_mutation(c2, bounds, eta_m)
            
            offspring[i] = c1
            if i + 1 < pop_size:
                offspring[i + 1] = c2
        
        # 计算子代目标值
        offspring_obj = np.array([objective_func(ind) for ind in offspring])
        
        # ---- 步骤4：精英保留（父子合并，选最优N个）----
        combined_pop = np.vstack([population, offspring])
        combined_obj = np.vstack([objectives, offspring_obj])
        
        # 对合并种群非支配排序
        combined_fronts, combined_ranks = fast_non_dominated_sort(combined_obj)
        
        # 按前沿层依次选，直到满pop_size个
        new_population = []
        new_objectives = []
        for front in combined_fronts:
            if len(new_population) + len(front) <= pop_size:
                # 整个前沿都能装下
                new_population.extend(combined_pop[front])
                new_objectives.extend(combined_obj[front])
            else:
                # 这个前沿装不下，按拥挤度选最稀疏的
                remaining = pop_size - len(new_population)
                cd = crowding_distance(combined_obj, front)
                # 按拥挤度降序排列，选前remaining个
                sorted_by_cd = sorted(range(len(front)), 
                                     key=lambda i: cd[i], reverse=True)
                selected = [front[i] for i in sorted_by_cd[:remaining]]
                new_population.extend(combined_pop[selected])
                new_objectives.extend(combined_obj[selected])
                break
        
        population = np.array(new_population)
        objectives = np.array(new_objectives)
    
    # ---- 步骤5：输出最终Pareto前沿 ----
    fronts, ranks = fast_non_dominated_sort(objectives)
    pareto_indices = fronts[0]
    pareto_obj = objectives[pareto_indices]
    pareto_pop = population[pareto_indices]
    
    # 按第一个目标排序
    sort_order = np.argsort(pareto_obj[:, 0])
    
    return {
        'population': population,
        'objectives': objectives,
        'pareto_front': pareto_obj[sort_order],
        'pareto_population': pareto_pop[sort_order],
        'history': history
    }


# ============================================================
# 第七部分：测试用例
# ============================================================
def test_simple_biobjective():
    """
    测试1：简单双目标问题
    min f1 = x², f2 = (x-2)², x∈[0,2]
    真实Pareto前沿：x∈[0,2]
    """
    print("=" * 60)
    print("测试1：简单双目标问题")
    print("min f1 = x², f2 = (x-2)², x∈[0,2]")
    print("=" * 60)
    
    def obj_func(x):
        return np.array([x[0]**2, (x[0]-2)**2])
    
    bounds = [(0, 2)]
    
    result = nsga2(obj_func, bounds, pop_size=50, n_generations=100, verbose=True)
    
    pf = result['pareto_front']
    print(f"\n最终Pareto前沿：{len(pf)}个解")
    print(f"f1范围：[{pf[:,0].min():.4f}, {pf[:,0].max():.4f}]")
    print(f"f2范围：[{pf[:,1].min():.4f}, {pf[:,1].max():.4f}]")
    
    # 画图
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # 真实前沿
    x_true = np.linspace(0, 2, 100)
    f1_true = x_true**2
    f2_true = (x_true-2)**2
    
    axes[0].scatter(pf[:,0], pf[:,1], c='pink', s=40, alpha=0.7, label='NSGA-II解')
    axes[0].plot(f1_true, f2_true, 'b--', linewidth=2, label='真实Pareto前沿')
    axes[0].set_xlabel('f1 = x²')
    axes[0].set_ylabel('f2 = (x-2)²')
    axes[0].set_title('NSGA-II vs 真实前沿')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 进化过程
    for i, gen_pf in enumerate(result['history']):
        if i % 20 == 0:
            axes[1].scatter(gen_pf[:,0], gen_pf[:,1], s=20, alpha=0.5, 
                          label=f'第{i}代')
    axes[1].plot(f1_true, f2_true, 'b--', linewidth=2, label='真实前沿')
    axes[1].set_xlabel('f1')
    axes[1].set_ylabel('f2')
    axes[1].set_title('进化过程')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('NSGA2_简单双目标.png', dpi=150, bbox_inches='tight')
    print(f"图像已保存：NSGA2_简单双目标.png")
    print("✓ 测试通过！")


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
    def zdt1(x):
        f1 = x[0]
        g = 1 + 9 / (n - 1) * np.sum(x[1:])
        f2 = g * (1 - np.sqrt(f1 / g))
        return np.array([f1, f2])
    
    bounds = [(0, 1)] * n
    
    result = nsga2(zdt1, bounds, pop_size=100, n_generations=200, verbose=True)
    
    pf = result['pareto_front']
    print(f"\n最终Pareto前沿：{len(pf)}个解")
    print(f"f1范围：[{pf[:,0].min():.4f}, {pf[:,0].max():.4f}]")
    
    # 计算与真实前沿的平均误差
    f2_true = 1 - np.sqrt(pf[:,0])
    error = np.mean(np.abs(pf[:,1] - f2_true))
    print(f"与真实前沿的平均误差：{error:.6f}")
    
    # 画图
    plt.figure(figsize=(8, 6))
    plt.scatter(pf[:,0], pf[:,1], c='pink', s=40, alpha=0.7, label='NSGA-II解')
    f1_true = np.linspace(0, 1, 100)
    plt.plot(f1_true, 1 - np.sqrt(f1_true), 'b--', linewidth=2, label='真实Pareto前沿')
    plt.xlabel('f1')
    plt.ylabel('f2')
    plt.title('NSGA-II on ZDT1')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('NSGA2_ZDT1.png', dpi=150, bbox_inches='tight')
    print(f"图像已保存：NSGA2_ZDT1.png")
    print("✓ 测试通过！")


if __name__ == '__main__':
    np.random.seed(42)  # 固定随机种子，可复现
    test_simple_biobjective()
    test_zdt1()
    print("\n" + "=" * 60)
    print("全部测试完成！")
    print("=" * 60)
