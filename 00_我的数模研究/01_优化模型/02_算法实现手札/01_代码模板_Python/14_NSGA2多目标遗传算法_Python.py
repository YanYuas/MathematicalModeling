"""
NSGA-II (非支配排序遗传算法 II) Python 代码模板

适用场景：
- 多目标优化问题
- 需要获得Pareto最优前沿
- 目标之间相互冲突，无法同时最优

核心概念：
- Pareto支配：解A支配解B，当且仅当A在所有目标上不差于B，且至少一个目标优于B
- Pareto最优：不被任何其他解支配的解
- Pareto前沿：所有Pareto最优解组成的集合
- 非支配排序：将种群按支配关系分层
- 拥挤度：保持种群多样性
"""

import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# NSGA-II 算法实现
# ============================================================

class NSGA2:
    def __init__(self, objectives, n_dim, bounds,
                 pop_size=100, max_iter=200,
                 crossover_rate=0.9, mutation_rate=0.1):
        """
        参数:
            objectives: 目标函数列表 [f1, f2, ...]，每个函数输入x返回标量
            n_dim: 决策变量维度
            bounds: 变量边界 [(low, high), ...]
            pop_size: 种群大小
            max_iter: 最大迭代次数
            crossover_rate: 交叉概率
            mutation_rate: 变异概率
        """
        self.objectives = objectives
        self.n_obj = len(objectives)
        self.n_dim = n_dim
        self.bounds = np.array(bounds)
        self.pop_size = pop_size
        self.max_iter = max_iter
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate

    def init_population(self):
        """初始化种群"""
        return np.random.uniform(
            self.bounds[:, 0], self.bounds[:, 1],
            size=(self.pop_size, self.n_dim)
        )

    def evaluate(self, population):
        """计算所有目标函数值"""
        return np.array([[f(ind) for f in self.objectives] for ind in population])

    def dominates(self, p, q):
        """判断p是否支配q（最小化问题）"""
        return np.all(p <= q) and np.any(p < q)

    def non_dominated_sort(self, scores):
        """非支配排序，返回每个个体的层级（rank）"""
        n = len(scores)
        domination_count = np.zeros(n)  # 被多少个解支配
        dominated_set = [[] for _ in range(n)]  # 支配哪些解
        ranks = np.zeros(n, dtype=int)

        # 第一层
        front = []
        for p in range(n):
            for q in range(n):
                if p != q:
                    if self.dominates(scores[p], scores[q]):
                        dominated_set[p].append(q)
                    elif self.dominates(scores[q], scores[p]):
                        domination_count[p] += 1
            if domination_count[p] == 0:
                ranks[p] = 0
                front.append(p)

        # 后续层级
        current_front = front
        rank = 0
        while current_front:
            next_front = []
            for p in current_front:
                for q in dominated_set[p]:
                    domination_count[q] -= 1
                    if domination_count[q] == 0:
                        ranks[q] = rank + 1
                        next_front.append(q)
            rank += 1
            current_front = next_front

        return ranks

    def crowding_distance(self, scores, front):
        """计算拥挤度"""
        n = len(front)
        if n <= 2:
            return np.full(n, np.inf)

        distances = np.zeros(n)
        for obj_idx in range(self.n_obj):
            # 按当前目标排序
            sorted_idx = np.argsort(scores[front, obj_idx])
            sorted_front = [front[i] for i in sorted_idx]

            # 边界点拥挤度无穷大
            distances[sorted_idx[0]] = np.inf
            distances[sorted_idx[-1]] = np.inf

            # 计算中间点的拥挤度
            obj_range = scores[sorted_front[-1], obj_idx] - scores[sorted_front[0], obj_idx]
            if obj_range == 0:
                continue
            for i in range(1, n - 1):
                distances[sorted_idx[i]] += (
                    scores[sorted_front[i + 1], obj_idx] -
                    scores[sorted_front[i - 1], obj_idx]
                ) / obj_range

        return distances

    def tournament_select(self, population, ranks, distances):
        """锦标赛选择"""
        idx = np.random.choice(len(population), 2, replace=False)
        # 先比较rank，rank小的好；rank相同比拥挤度，拥挤度大的好
        if ranks[idx[0]] < ranks[idx[1]]:
            return population[idx[0]]
        elif ranks[idx[0]] > ranks[idx[1]]:
            return population[idx[1]]
        else:
            return population[idx[0]] if distances[idx[0]] > distances[idx[1]] else population[idx[1]]

    def crossover(self, parent1, parent2):
        """模拟二进制交叉（SBX）"""
        if np.random.rand() > self.crossover_rate:
            return parent1.copy()

        child = parent1.copy()
        eta = 20  # 分布指数
        for i in range(self.n_dim):
            if np.random.rand() < 0.5:
                if abs(parent1[i] - parent2[i]) > 1e-14:
                    x1, x2 = min(parent1[i], parent2[i]), max(parent1[i], parent2[i])
                    low, high = self.bounds[i]
                    rand = np.random.rand()
                    # 第一个后代
                    beta = 1 + (2 * (x1 - low) / (x2 - x1))
                    alpha = 2 - beta ** (-(eta + 1))
                    if rand <= 1 / alpha:
                        beta_q = (rand * alpha) ** (1 / (eta + 1))
                    else:
                        beta_q = (1 / (2 - rand * alpha)) ** (1 / (eta + 1))
                    child[i] = 0.5 * ((x1 + x2) - beta_q * (x2 - x1))
        return child

    def mutate(self, individual):
        """多项式变异"""
        eta = 20
        for i in range(self.n_dim):
            if np.random.rand() < self.mutation_rate:
                low, high = self.bounds[i]
                delta1 = (individual[i] - low) / (high - low)
                delta2 = (high - individual[i]) / (high - low)
                rand = np.random.rand()
                mut_pow = 1 / (eta + 1)
                if rand < 0.5:
                    xy = 1 - delta1
                    val = 2 * rand + (1 - 2 * rand) * xy ** (eta + 1)
                    delta_q = val ** mut_pow - 1
                else:
                    xy = 1 - delta2
                    val = 2 * (1 - rand) + 2 * (rand - 0.5) * xy ** (eta + 1)
                    delta_q = 1 - val ** mut_pow
                individual[i] += delta_q * (high - low)
                individual[i] = np.clip(individual[i], low, high)
        return individual

    def run(self):
        """运行NSGA-II"""
        # 初始化
        population = self.init_population()
        scores = self.evaluate(population)

        for gen in range(self.max_iter):
            # 非支配排序和拥挤度
            ranks = self.non_dominated_sort(scores)
            distances = np.zeros(len(population))
            for rank in range(max(ranks) + 1):
                front = np.where(ranks == rank)[0]
                distances[front] = self.crowding_distance(scores, front)

            # 选择、交叉、变异产生子代
            offspring = []
            for _ in range(self.pop_size):
                p1 = self.tournament_select(population, ranks, distances)
                p2 = self.tournament_select(population, ranks, distances)
                child = self.crossover(p1, p2)
                child = self.mutate(child)
                offspring.append(child)
            offspring = np.array(offspring)

            # 合并父子代
            combined_pop = np.vstack([population, offspring])
            combined_scores = self.evaluate(combined_pop)

            # 非支配排序选择
            combined_ranks = self.non_dominated_sort(combined_scores)
            combined_distances = np.zeros(len(combined_pop))
            for rank in range(max(combined_ranks) + 1):
                front = np.where(combined_ranks == rank)[0]
                combined_distances[front] = self.crowding_distance(combined_scores, front)

            # 按rank和拥挤度排序，选择前pop_size个
            sorted_indices = np.lexsort((-combined_distances, combined_ranks))
            population = combined_pop[sorted_indices[:self.pop_size]]
            scores = combined_scores[sorted_indices[:self.pop_size]]

            if gen % 20 == 0:
                n_pareto = np.sum(self.non_dominated_sort(scores) == 0)
                print(f"第{gen:3d}代: Pareto前沿解数量 = {n_pareto}")

        # 最终Pareto前沿
        final_ranks = self.non_dominated_sort(scores)
        pareto_idx = np.where(final_ranks == 0)[0]
        return population[pareto_idx], scores[pareto_idx]


# ============================================================
# 测试：ZDT1多目标测试问题
# 最小化 f1 = x1
# 最小化 f2 = g(x) * (1 - sqrt(x1/g(x)))
# 其中 g(x) = 1 + 9/(n-1) * Σxi (i=2..n)
# ============================================================
if __name__ == "__main__":
    n_dim = 30

    def f1(x):
        return x[0]

    def g(x):
        return 1 + 9 / (n_dim - 1) * sum(x[1:])

    def f2(x):
        return g(x) * (1 - np.sqrt(x[0] / g(x)))

    nsga = NSGA2(
        objectives=[f1, f2],
        n_dim=n_dim,
        bounds=[(0, 1)] * n_dim,
        pop_size=100,
        max_iter=200,
        crossover_rate=0.9,
        mutation_rate=1 / n_dim
    )

    pareto_x, pareto_f = nsga.run()

    print("\n" + "=" * 50)
    print("NSGA-II求解ZDT1问题")
    print("=" * 50)
    print(f"Pareto前沿解数量: {len(pareto_f)}")
    print(f"f1范围: [{pareto_f[:, 0].min():.4f}, {pareto_f[:, 0].max():.4f}]")
    print(f"f2范围: [{pareto_f[:, 1].min():.4f}, {pareto_f[:, 1].max():.4f}]")

    # 绘制Pareto前沿
    plt.figure(figsize=(8, 6))
    plt.scatter(pareto_f[:, 0], pareto_f[:, 1], c='blue', s=20, alpha=0.7, label='NSGA-II')
    plt.xlabel('f1 (最小化)')
    plt.ylabel('f2 (最小化)')
    plt.title('ZDT1问题的Pareto前沿')
    plt.legend()
    plt.grid(True)
    plt.savefig('NSGA2_Pareto_front.png', dpi=150, bbox_inches='tight')
    print("Pareto前沿图已保存为 NSGA2_Pareto_front.png")


# ============================================================
# 多目标优化方法对比
# ============================================================
"""
多目标优化方法：

1. 先验方法（需要决策者偏好）
   - 加权求和法：最简单，但只能得到凸前沿上的点
   - 目标规划：设定目标值，最小化偏离
   - 分层序列法：按优先级依次优化

2. 后验方法（生成Pareto前沿，再选择）
   - NSGA-II：最常用，非支配排序+拥挤度
   - MOEA/D：分解方法，收敛快
   - SPEA2：强度Pareto进化算法
   - MOPSO：多目标粒子群

3. 方法选择
   - 目标少（2-3个）：NSGA-II
   - 目标多（4+）：MOEA/D
   - 需要快速收敛：MOPSO
   - 需要理论保证：加权法（凸问题）
"""
