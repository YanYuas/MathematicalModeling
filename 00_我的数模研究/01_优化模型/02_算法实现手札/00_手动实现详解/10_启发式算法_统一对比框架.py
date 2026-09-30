# -*- coding: utf-8 -*-
"""
启发式算法 · 统一对比框架
==========================
六层钻研法 · 第4层：手动实现

包含5种经典启发式算法的统一实现：
1. 遗传算法 GA
2. 模拟退火 SA
3. 粒子群 PSO
4. 差分进化 DE
5. 蚁群 ACO（连续版本，用于连续优化对比）

以及4个标准测试函数：
- Sphere（单峰凸函数）
- Rosenbrock（香蕉函数，弯曲峡谷）
- Rastrigin（多峰，大量局部最优）
- Griewank（多峰+变量关联）

所有算法使用相同的接口：
    result = algorithm(objective_func, bounds, n_iter, ...)
返回：{'best_x', 'best_f', 'history', 'time'}
"""

import numpy as np
import time


# ============================================================
# 测试函数
# ============================================================
def sphere(x):
    """Sphere函数：f = Σx_i²，全局最优f(0)=0"""
    return np.sum(x**2)

def rosenbrock(x):
    """Rosenbrock函数：香蕉函数，全局最优f(1,1,...)=0"""
    return np.sum(100 * (x[1:] - x[:-1]**2)**2 + (1 - x[:-1])**2)

def rastrigin(x):
    """Rastrigin函数：多峰，全局最优f(0)=0"""
    return np.sum(x**2 - 10 * np.cos(2 * np.pi * x) + 10)

def griewank(x):
    """Griewank函数：多峰+变量关联，全局最优f(0)=0"""
    return 1.0/4000 * np.sum(x**2) - np.prod(np.cos(x / np.sqrt(np.arange(1, len(x)+1)))) + 1


# ============================================================
# 算法1：遗传算法 GA
# ============================================================
def genetic_algorithm(obj_func, bounds, n_iter=500, pop_size=50,
                      crossover_rate=0.8, mutation_rate=0.1, seed=None):
    """
    遗传算法（实数编码）
    
    流程：初始化 → 选择 → 交叉 → 变异 → 评估 → 重复
    """
    if seed is not None:
        np.random.seed(seed)
    
    n_vars = len(bounds)
    low = np.array([b[0] for b in bounds])
    high = np.array([b[1] for b in bounds])
    
    # 初始化种群
    population = low + np.random.random((pop_size, n_vars)) * (high - low)
    fitness = np.array([obj_func(ind) for ind in population])
    
    history = []
    start = time.time()
    
    for gen in range(n_iter):
        # 记录最优
        best_idx = np.argmin(fitness)
        history.append(fitness[best_idx])
        
        # 选择：锦标赛选择（随机选3个，取最好的）
        new_pop = np.zeros_like(population)
        for i in range(pop_size):
            candidates = np.random.choice(pop_size, 3, replace=False)
            winner = candidates[np.argmin(fitness[candidates])]
            new_pop[i] = population[winner].copy()
        
        # 交叉：算术交叉
        for i in range(0, pop_size, 2):
            if np.random.random() < crossover_rate and i + 1 < pop_size:
                alpha = np.random.random(n_vars)
                child1 = alpha * new_pop[i] + (1 - alpha) * new_pop[i+1]
                child2 = (1 - alpha) * new_pop[i] + alpha * new_pop[i+1]
                new_pop[i] = np.clip(child1, low, high)
                new_pop[i+1] = np.clip(child2, low, high)
        
        # 变异：高斯变异
        for i in range(pop_size):
            if np.random.random() < mutation_rate:
                mutant = new_pop[i] + np.random.normal(0, 0.1 * (high - low), n_vars)
                new_pop[i] = np.clip(mutant, low, high)
        
        # 精英保留：把上一代最好的直接保留
        new_pop[0] = population[best_idx].copy()
        
        # 评估新一代
        population = new_pop
        fitness = np.array([obj_func(ind) for ind in population])
    
    best_idx = np.argmin(fitness)
    elapsed = time.time() - start
    
    return {
        'best_x': population[best_idx],
        'best_f': fitness[best_idx],
        'history': history,
        'time': elapsed
    }


# ============================================================
# 算法2：模拟退火 SA
# ============================================================
def simulated_annealing(obj_func, bounds, n_iter=500,
                        T0=100.0, T_min=1e-4, alpha=0.95, seed=None):
    """
    模拟退火
    
    流程：初始化 → 随机扰动 → Metropolis接受 → 降温 → 重复
    """
    if seed is not None:
        np.random.seed(seed)
    
    n_vars = len(bounds)
    low = np.array([b[0] for b in bounds])
    high = np.array([b[1] for b in bounds])
    
    # 初始解
    x = low + np.random.random(n_vars) * (high - low)
    f = obj_func(x)
    best_x = x.copy()
    best_f = f
    
    T = T0
    history = []
    start = time.time()
    
    for i in range(n_iter):
        history.append(best_f)
        
        # 随机扰动（在当前解附近）
        step = np.random.normal(0, 0.1 * (high - low), n_vars)
        x_new = np.clip(x + step, low, high)
        f_new = obj_func(x_new)
        
        # Metropolis接受准则
        delta = f_new - f
        if delta < 0 or np.random.random() < np.exp(-delta / max(T, 1e-10)):
            x = x_new
            f = f_new
            if f < best_f:
                best_x = x.copy()
                best_f = f
        
        # 降温
        T = T * alpha
        if T < T_min:
            T = T_min
    
    elapsed = time.time() - start
    
    return {
        'best_x': best_x,
        'best_f': best_f,
        'history': history,
        'time': elapsed
    }


# ============================================================
# 算法3：粒子群 PSO
# ============================================================
def particle_swarm(obj_func, bounds, n_iter=500, pop_size=50,
                   w=0.7, c1=2.0, c2=2.0, seed=None):
    """
    粒子群优化
    
    速度更新：v = w*v + c1*r1*(pbest-x) + c2*r2*(gbest-x)
    位置更新：x = x + v
    """
    if seed is not None:
        np.random.seed(seed)
    
    n_vars = len(bounds)
    low = np.array([b[0] for b in bounds])
    high = np.array([b[1] for b in bounds])
    
    # 初始化位置和速度
    positions = low + np.random.random((pop_size, n_vars)) * (high - low)
    v_max = 0.2 * (high - low)  # 速度上限
    velocities = (np.random.random((pop_size, n_vars)) - 0.5) * 2 * v_max
    
    # 初始评估
    fitness = np.array([obj_func(p) for p in positions])
    pbest = positions.copy()
    pbest_f = fitness.copy()
    gbest_idx = np.argmin(fitness)
    gbest = positions[gbest_idx].copy()
    gbest_f = fitness[gbest_idx]
    
    history = []
    start = time.time()
    
    for gen in range(n_iter):
        history.append(gbest_f)
        
        # 更新速度
        r1 = np.random.random((pop_size, n_vars))
        r2 = np.random.random((pop_size, n_vars))
        velocities = (w * velocities + 
                      c1 * r1 * (pbest - positions) + 
                      c2 * r2 * (gbest - positions))
        velocities = np.clip(velocities, -v_max, v_max)
        
        # 更新位置
        positions = np.clip(positions + velocities, low, high)
        
        # 评估
        fitness = np.array([obj_func(p) for p in positions])
        
        # 更新pbest
        better = fitness < pbest_f
        pbest[better] = positions[better].copy()
        pbest_f[better] = fitness[better]
        
        # 更新gbest
        gbest_idx = np.argmin(pbest_f)
        if pbest_f[gbest_idx] < gbest_f:
            gbest = pbest[gbest_idx].copy()
            gbest_f = pbest_f[gbest_idx]
    
    elapsed = time.time() - start
    
    return {
        'best_x': gbest,
        'best_f': gbest_f,
        'history': history,
        'time': elapsed
    }


# ============================================================
# 算法4：差分进化 DE
# ============================================================
def differential_evolution(obj_func, bounds, n_iter=500, pop_size=50,
                           F=0.8, CR=0.9, seed=None):
    """
    差分进化
    
    变异：v = a + F*(b - c)
    交叉：u_j = v_j if rand<CR else x_j
    选择：u比x好就替换
    """
    if seed is not None:
        np.random.seed(seed)
    
    n_vars = len(bounds)
    low = np.array([b[0] for b in bounds])
    high = np.array([b[1] for b in bounds])
    
    # 初始化种群
    population = low + np.random.random((pop_size, n_vars)) * (high - low)
    fitness = np.array([obj_func(ind) for ind in population])
    
    history = []
    start = time.time()
    
    for gen in range(n_iter):
        best_idx = np.argmin(fitness)
        history.append(fitness[best_idx])
        
        for i in range(pop_size):
            # 随机选三个不同的个体a,b,c
            candidates = [j for j in range(pop_size) if j != i]
            a, b, c = np.random.choice(candidates, 3, replace=False)
            
            # 变异
            mutant = population[a] + F * (population[b] - population[c])
            mutant = np.clip(mutant, low, high)
            
            # 交叉
            trial = population[i].copy()
            j_rand = np.random.randint(n_vars)  # 保证至少一个维度被替换
            for j in range(n_vars):
                if np.random.random() < CR or j == j_rand:
                    trial[j] = mutant[j]
            
            # 选择
            f_trial = obj_func(trial)
            if f_trial <= fitness[i]:
                population[i] = trial
                fitness[i] = f_trial
    
    best_idx = np.argmin(fitness)
    elapsed = time.time() - start
    
    return {
        'best_x': population[best_idx],
        'best_f': fitness[best_idx],
        'history': history,
        'time': elapsed
    }


# ============================================================
# 算法5：蚁群算法（连续版本）
# ============================================================
def ant_colony_continuous(obj_func, bounds, n_iter=500, pop_size=50,
                          q=0.5, zeta=1.0, seed=None):
    """
    连续空间蚁群算法（ACO_R）
    
    用高斯分布代替离散的信息素：
    - 每只蚂蚁根据"解的存档"中的高斯分布采样
    - 存档中保留最好的k个解
    - 每次迭代后更新存档
    """
    if seed is not None:
        np.random.seed(seed)
    
    n_vars = len(bounds)
    low = np.array([b[0] for b in bounds])
    high = np.array([b[1] for b in bounds])
    
    # 初始化：随机生成pop_size个解
    solutions = low + np.random.random((pop_size, n_vars)) * (high - low)
    fitness = np.array([obj_func(s) for s in solutions])
    
    # 存档：保留最好的k个解
    k = max(5, pop_size // 5)
    archive_idx = np.argsort(fitness)[:k]
    archive = solutions[archive_idx].copy()
    archive_f = fitness[archive_idx].copy()
    
    history = []
    start = time.time()
    
    for gen in range(n_iter):
        history.append(archive_f[0])
        
        # 计算每个存档解的权重（越好权重越大）
        ranks = np.arange(k) + 1
        weights = np.exp(-ranks**2 / (2 * q**2 * k**2))
        weights /= weights.sum()
        
        # 每只蚂蚁根据存档的高斯分布采样
        new_solutions = np.zeros_like(solutions)
        for i in range(pop_size):
            # 轮盘赌选一个存档解作为均值
            chosen = np.random.choice(k, p=weights)
            mean = archive[chosen]
            
            # 标准差：与存档中其他解的平均距离
            sigma = zeta * np.mean(np.abs(archive - mean), axis=0)
            sigma = np.maximum(sigma, 1e-6)  # 防止为0
            
            # 高斯采样
            new_solutions[i] = np.clip(
                mean + np.random.normal(0, sigma, n_vars), low, high)
        
        # 评估新解
        new_fitness = np.array([obj_func(s) for s in new_solutions])
        
        # 合并并更新存档
        all_solutions = np.vstack([archive, new_solutions])
        all_fitness = np.concatenate([archive_f, new_fitness])
        best_k = np.argsort(all_fitness)[:k]
        archive = all_solutions[best_k].copy()
        archive_f = all_fitness[best_k].copy()
    
    elapsed = time.time() - start
    
    return {
        'best_x': archive[0],
        'best_f': archive_f[0],
        'history': history,
        'time': elapsed
    }


# ============================================================
# 统一运行接口
# ============================================================
ALGORITHMS = {
    'GA': genetic_algorithm,
    'SA': simulated_annealing,
    'PSO': particle_swarm,
    'DE': differential_evolution,
    'ACO': ant_colony_continuous,
}

TEST_FUNCTIONS = {
    'Sphere': (sphere, [(-5.12, 5.12)]),
    'Rosenbrock': (rosenbrock, [(-2.048, 2.048)]),
    'Rastrigin': (rastrigin, [(-5.12, 5.12)]),
    'Griewank': (griewank, [(-600, 600)]),
}


def run_comparison(n_dim=10, n_iter=300, n_runs=5, verbose=True):
    """
    运行所有算法在所有测试函数上的对比实验
    
    参数：
        n_dim: 问题维度
        n_iter: 迭代次数
        n_runs: 每个算法运行次数（取平均）
    
    返回：
        results: 字典，results[func_name][algo_name] = 平均结果
    """
    results = {}
    
    for func_name, (func, base_bounds) in TEST_FUNCTIONS.items():
        if verbose:
            print(f"\n{'='*60}")
            print(f"测试函数：{func_name}（{n_dim}维）")
            print(f"{'='*60}")
        
        bounds = base_bounds * n_dim
        results[func_name] = {}
        
        for algo_name, algo_func in ALGORITHMS.items():
            best_f_list = []
            time_list = []
            histories = []
            
            for run in range(n_runs):
                result = algo_func(func, bounds, n_iter=n_iter, seed=run*100+42)
                best_f_list.append(result['best_f'])
                time_list.append(result['time'])
                histories.append(result['history'])
            
            avg_f = np.mean(best_f_list)
            std_f = np.std(best_f_list)
            best_f = np.min(best_f_list)
            avg_time = np.mean(time_list)
            avg_history = np.mean(histories, axis=0)
            
            results[func_name][algo_name] = {
                'avg_f': avg_f,
                'std_f': std_f,
                'best_f': best_f,
                'avg_time': avg_time,
                'avg_history': avg_history
            }
            
            if verbose:
                print(f"  {algo_name:6s}: 平均={avg_f:.6e} ± {std_f:.6e}, "
                      f"最好={best_f:.6e}, 时间={avg_time:.3f}s")
    
    return results


# ============================================================
# 测试用例
# ============================================================
if __name__ == '__main__':
    print("启发式算法统一对比框架 - 快速测试")
    print("=" * 60)
    
    # 简单测试：Sphere函数，10维，100次迭代
    bounds = [(-5.12, 5.12)] * 10
    
    for name, algo in ALGORITHMS.items():
        result = algo(sphere, bounds, n_iter=100, seed=42)
        print(f"{name:6s}: best_f = {result['best_f']:.6f}, time = {result['time']:.3f}s")
    
    print("\n✓ 所有算法测试通过！")
