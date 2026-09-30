# -*- coding: utf-8 -*-
"""
启发式算法深化 · TSP求解器
============================
六层钻研法 · 第4层：手动实现

包含3种TSP（旅行商问题）求解器：
1. 蚁群算法（ACO）：信息素引导的群体智能
2. 混合算法（Memetic）：遗传算法 + 2-opt局部搜索
3. 模拟退火（SA）：概率接受劣解的局部搜索

TSP是组合优化的经典问题，n>20时精确算法不可行，必须用启发式。
"""

import numpy as np
import random
import time


# ============================================================
# 工具函数
# ============================================================
def calculate_distance_matrix(coords):
    """根据坐标计算距离矩阵"""
    n = len(coords)
    dist = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            dist[i][j] = np.sqrt((coords[i][0]-coords[j][0])**2 +
                                  (coords[i][1]-coords[j][1])**2)
    return dist


def tour_length(tour, dist):
    """计算路径长度"""
    n = len(tour)
    return sum(dist[tour[i]][tour[(i+1) % n]] for i in range(n))


def two_opt_swap(tour, i, j):
    """2-opt交换：反转tour[i..j]段"""
    new_tour = tour[:]
    new_tour[i:j+1] = reversed(tour[i:j+1])
    return new_tour


def local_search_2opt(tour, dist, max_iter=100):
    """
    2-opt局部搜索
    
    核心：不断找两条边交叉的情况，交换后路径变短。
    重复直到没有改进。
    """
    n = len(tour)
    improved = True
    iteration = 0
    
    while improved and iteration < max_iter:
        improved = False
        iteration += 1
        for i in range(n - 1):
            for j in range(i + 1, n):
                # 计算交换前后的边长差
                # 原边：(i-1,i)和(j,j+1)，交换后：(i-1,j)和(i,j+1)
                a, b = tour[i-1], tour[i]
                c, d = tour[j], tour[(j+1) % n]
                
                old_cost = dist[a][b] + dist[c][d]
                new_cost = dist[a][c] + dist[b][d]
                
                if new_cost < old_cost - 1e-10:
                    tour = two_opt_swap(tour, i, j)
                    improved = True
                    break
            if improved:
                break
    
    return tour


# ============================================================
# 1. 蚁群算法（ACO）求解TSP
# ============================================================
class AntColonyTSP:
    """
    蚁群算法求解TSP
    
    核心思想：
    - 每只蚂蚁从随机城市出发，根据"信息素浓度"和"距离"选择下一个城市
    - 信息素越多的边越可能被选（正反馈）
    - 距离越近的城市越可能被选（启发式）
    - 所有蚂蚁走完后，更新信息素（路径越短的蚂蚁留下越多信息素）
    - 信息素会挥发，避免陷入局部最优
    
    参数：
        n_ants: 蚂蚁数量
        n_iter: 迭代次数
        alpha: 信息素重要度（越大越依赖信息素）
        beta: 启发式重要度（越大越依赖距离）
        rho: 信息素挥发率（0~1）
        Q: 信息素强度常数
    """
    
    def __init__(self, dist, n_ants=20, n_iter=100,
                 alpha=1.0, beta=5.0, rho=0.5, Q=100):
        self.dist = dist
        self.n = len(dist)
        self.n_ants = n_ants
        self.n_iter = n_iter
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.Q = Q
        
        # 初始化信息素矩阵
        # 初始信息素 = Q / (n * 平均距离)
        avg_dist = dist.sum() / (self.n * (self.n - 1))
        self.pheromone = np.ones((self.n, self.n)) * (Q / (self.n * avg_dist))
        
        # 启发式信息 = 1/距离
        self.heuristic = np.zeros((self.n, self.n))
        for i in range(self.n):
            for j in range(self.n):
                if i != j:
                    self.heuristic[i][j] = 1.0 / dist[i][j]
    
    def _select_next_city(self, current, unvisited):
        """
        轮盘赌选择下一个城市
        
        选择概率 = (信息素^alpha) * (启发式^beta) / 总和
        """
        probabilities = []
        for city in unvisited:
            tau = self.pheromone[current][city] ** self.alpha
            eta = self.heuristic[current][city] ** self.beta
            probabilities.append(tau * eta)
        
        total = sum(probabilities)
        probabilities = [p / total for p in probabilities]
        
        # 轮盘赌
        r = random.random()
        cumulative = 0
        for i, city in enumerate(unvisited):
            cumulative += probabilities[i]
            if r <= cumulative:
                return city
        
        return unvisited[-1]
    
    def _construct_solution(self):
        """一只蚂蚁构建完整路径"""
        start = random.randint(0, self.n - 1)
        tour = [start]
        unvisited = list(range(self.n))
        unvisited.remove(start)
        
        current = start
        while unvisited:
            next_city = self._select_next_city(current, unvisited)
            tour.append(next_city)
            unvisited.remove(next_city)
            current = next_city
        
        return tour
    
    def _update_pheromone(self, all_tours, all_lengths):
        """
        更新信息素
        
        1. 挥发：pheromone *= (1 - rho)
        2. 沉积：每只蚂蚁在自己的路径上留下信息素
           信息素量 = Q / 路径长度（路径越短留越多）
        """
        # 挥发
        self.pheromone *= (1 - self.rho)
        
        # 沉积
        for tour, length in zip(all_tours, all_lengths):
            deposit = self.Q / length
            for i in range(self.n):
                a, b = tour[i], tour[(i+1) % self.n]
                self.pheromone[a][b] += deposit
                self.pheromone[b][a] += deposit  # 无向图
    
    def solve(self, verbose=False):
        """运行蚁群算法"""
        best_tour = None
        best_length = float('inf')
        history = []
        
        for iteration in range(self.n_iter):
            # 所有蚂蚁构建路径
            all_tours = []
            all_lengths = []
            
            for _ in range(self.n_ants):
                tour = self._construct_solution()
                length = tour_length(tour, self.dist)
                all_tours.append(tour)
                all_lengths.append(length)
                
                if length < best_length:
                    best_length = length
                    best_tour = tour[:]
            
            # 更新信息素
            self._update_pheromone(all_tours, all_lengths)
            
            history.append(best_length)
            
            if verbose and (iteration + 1) % 20 == 0:
                print(f"  迭代 {iteration+1}/{self.n_iter}: 最优={best_length:.2f}")
        
        return best_tour, best_length, history


# ============================================================
# 2. 混合算法（Memetic Algorithm）求解TSP
# ============================================================
class MemeticTSP:
    """
    混合算法（Memetic Algorithm）求解TSP
    
    核心思想：遗传算法（全局搜索）+ 2-opt局部搜索（局部优化）
    
    "Memetic"来自"meme"（模因），类比基因进化但加入了文化进化（局部学习）。
    
    流程：
    1. 初始化种群（随机路径）
    2. 对每个个体做2-opt局部搜索
    3. 选择（锦标赛选择）
    4. 交叉（顺序交叉OX）
    5. 变异（交换变异）
    6. 对新个体做2-opt局部搜索
    7. 重复2-6
    """
    
    def __init__(self, dist, pop_size=50, n_iter=100,
                 crossover_rate=0.8, mutation_rate=0.2):
        self.dist = dist
        self.n = len(dist)
        self.pop_size = pop_size
        self.n_iter = n_iter
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
    
    def _random_tour(self):
        """生成随机路径"""
        tour = list(range(self.n))
        random.shuffle(tour)
        return tour
    
    def _tournament_select(self, population, fitness, k=3):
        """锦标赛选择：随机选k个，取最好的"""
        candidates = random.sample(range(len(population)), k)
        best = min(candidates, key=lambda i: fitness[i])
        return population[best][:]
    
    def _order_crossover(self, parent1, parent2):
        """
        顺序交叉（OX）
        
        1. 从parent1选一段
        2. 把这段放到孩子相同位置
        3. 剩下的位置按parent2的顺序填充（去掉已有的）
        """
        n = self.n
        start, end = sorted(random.sample(range(n), 2))
        
        child = [-1] * n
        child[start:end+1] = parent1[start:end+1]
        
        # 从parent2中按顺序填充剩余位置
        parent2_cities = [c for c in parent2 if c not in child]
        idx = 0
        for i in range(n):
            if child[i] == -1:
                child[i] = parent2_cities[idx]
                idx += 1
        
        return child
    
    def _swap_mutation(self, tour):
        """交换变异：随机交换两个位置"""
        i, j = random.sample(range(self.n), 2)
        tour[i], tour[j] = tour[j], tour[i]
        return tour
    
    def solve(self, verbose=False):
        """运行混合算法"""
        # 初始化种群
        population = [self._random_tour() for _ in range(self.pop_size)]
        
        # 对每个个体做局部搜索
        for i in range(self.pop_size):
            population[i] = local_search_2opt(population[i], self.dist)
        
        fitness = [tour_length(t, self.dist) for t in population]
        best_idx = min(range(self.pop_size), key=lambda i: fitness[i])
        best_tour = population[best_idx][:]
        best_length = fitness[best_idx]
        history = [best_length]
        
        for iteration in range(self.n_iter):
            new_population = []
            
            for _ in range(self.pop_size):
                # 选择
                parent1 = self._tournament_select(population, fitness)
                parent2 = self._tournament_select(population, fitness)
                
                # 交叉
                if random.random() < self.crossover_rate:
                    child = self._order_crossover(parent1, parent2)
                else:
                    child = parent1[:]
                
                # 变异
                if random.random() < self.mutation_rate:
                    child = self._swap_mutation(child)
                
                # 局部搜索（关键！Memetic的核心）
                child = local_search_2opt(child, self.dist)
                
                new_population.append(child)
            
            # 更新种群
            population = new_population
            fitness = [tour_length(t, self.dist) for t in population]
            
            # 更新最优
            current_best_idx = min(range(self.pop_size), key=lambda i: fitness[i])
            if fitness[current_best_idx] < best_length:
                best_length = fitness[current_best_idx]
                best_tour = population[current_best_idx][:]
            
            history.append(best_length)
            
            if verbose and (iteration + 1) % 20 == 0:
                print(f"  迭代 {iteration+1}/{self.n_iter}: 最优={best_length:.2f}")
        
        return best_tour, best_length, history


# ============================================================
# 3. 模拟退火（SA）求解TSP
# ============================================================
class SimulatedAnnealingTSP:
    """
    模拟退火求解TSP
    
    核心思想：
    - 从一个初始解出发，不断做小的扰动（交换两个城市）
    - 如果新解更好，接受
    - 如果新解更差，以概率 exp(-ΔE/T) 接受（避免陷入局部最优）
    - 温度T逐渐降低，接受劣解的概率越来越小
    - 最终收敛到近似最优解
    
    参数：
        T0: 初始温度
        T_min: 最低温度
        alpha: 降温系数（0~1，越接近1降温越慢）
        L: 每个温度下的迭代次数
    """
    
    def __init__(self, dist, T0=1000.0, T_min=1e-3, alpha=0.995, L=100):
        self.dist = dist
        self.n = len(dist)
        self.T0 = T0
        self.T_min = T_min
        self.alpha = alpha
        self.L = L
    
    def _neighbor(self, tour):
        """生成邻居解：随机交换两个位置"""
        new_tour = tour[:]
        i, j = random.sample(range(self.n), 2)
        new_tour[i], new_tour[j] = new_tour[j], new_tour[i]
        return new_tour
    
    def solve(self, init_tour=None, verbose=False):
        """运行模拟退火"""
        # 初始解
        if init_tour is None:
            current = list(range(self.n))
            random.shuffle(current)
        else:
            current = init_tour[:]
        
        current_length = tour_length(current, self.dist)
        best_tour = current[:]
        best_length = current_length
        
        T = self.T0
        history = [best_length]
        
        while T > self.T_min:
            for _ in range(self.L):
                # 生成邻居
                neighbor = self._neighbor(current)
                neighbor_length = tour_length(neighbor, self.dist)
                
                # 计算能量差
                delta = neighbor_length - current_length
                
                # 接受准则
                if delta < 0 or random.random() < np.exp(-delta / T):
                    current = neighbor
                    current_length = neighbor_length
                    
                    if current_length < best_length:
                        best_length = current_length
                        best_tour = current[:]
            
            history.append(best_length)
            T *= self.alpha  # 降温
        
        return best_tour, best_length, history


# ============================================================
# 测试用例
# ============================================================
def test_aco():
    print("=" * 60)
    print("测试1：蚁群算法求解TSP")
    print("=" * 60)
    
    np.random.seed(42)
    random.seed(42)
    
    # 生成20个随机城市
    coords = np.random.rand(20, 2) * 100
    dist = calculate_distance_matrix(coords)
    
    aco = AntColonyTSP(dist, n_ants=20, n_iter=50, alpha=1.0, beta=5.0)
    tour, length, history = aco.solve(verbose=True)
    
    print(f"蚁群算法最优路径长度：{length:.2f}")
    print(f"路径：{tour}")
    assert len(tour) == 20
    assert len(set(tour)) == 20
    print("✓ 测试通过！\n")


def test_memetic():
    print("=" * 60)
    print("测试2：混合算法（Memetic）求解TSP")
    print("=" * 60)
    
    np.random.seed(42)
    random.seed(42)
    
    coords = np.random.rand(20, 2) * 100
    dist = calculate_distance_matrix(coords)
    
    ma = MemeticTSP(dist, pop_size=30, n_iter=30)
    tour, length, history = ma.solve(verbose=True)
    
    print(f"混合算法最优路径长度：{length:.2f}")
    assert len(tour) == 20
    assert len(set(tour)) == 20
    print("✓ 测试通过！\n")


def test_sa():
    print("=" * 60)
    print("测试3：模拟退火求解TSP")
    print("=" * 60)
    
    np.random.seed(42)
    random.seed(42)
    
    coords = np.random.rand(20, 2) * 100
    dist = calculate_distance_matrix(coords)
    
    sa = SimulatedAnnealingTSP(dist, T0=1000, T_min=1e-3, alpha=0.99, L=50)
    tour, length, history = sa.solve(verbose=True)
    
    print(f"模拟退火最优路径长度：{length:.2f}")
    assert len(tour) == 20
    assert len(set(tour)) == 20
    print("✓ 测试通过！\n")


def test_2opt():
    print("=" * 60)
    print("测试4：2-opt局部搜索")
    print("=" * 60)
    
    np.random.seed(42)
    coords = np.random.rand(10, 2) * 100
    dist = calculate_distance_matrix(coords)
    
    # 随机路径
    tour = list(range(10))
    random.shuffle(tour)
    init_length = tour_length(tour, dist)
    
    # 2-opt优化
    improved = local_search_2opt(tour, dist)
    opt_length = tour_length(improved, dist)
    
    print(f"初始路径长度：{init_length:.2f}")
    print(f"2-opt后长度：{opt_length:.2f}")
    print(f"改进：{(init_length - opt_length)/init_length*100:.1f}%")
    assert opt_length <= init_length + 1e-10
    print("✓ 测试通过！\n")


if __name__ == '__main__':
    test_2opt()
    test_aco()
    test_memetic()
    test_sa()
    print("=" * 60)
    print("全部测试通过！")
    print("=" * 60)
