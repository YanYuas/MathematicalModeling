"""
遗传算法 (Genetic Algorithm, GA) Python 代码模板

适用场景：
- 复杂非线性、多峰、不可导的优化问题
- 组合优化问题（TSP、调度、指派）
- 全局优化

核心步骤：
1. 初始化种群
2. 适应度评估
3. 选择（轮盘赌/锦标赛）
4. 交叉
5. 变异
6. 重复直到收敛
"""

import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# 遗传算法：连续函数优化
# 求 f(x) = x * sin(10*pi*x) + 2 在 [-1, 2] 上的最大值
# ============================================================

class GeneticAlgorithm:
    def __init__(self, func, n_dim, bounds, pop_size=50, max_iter=200,
                 crossover_rate=0.8, mutation_rate=0.01, maximize=True):
        """
        参数:
            func: 目标函数
            n_dim: 变量维度
            bounds: 变量边界 [(low, high), ...]
            pop_size: 种群大小
            max_iter: 最大迭代次数
            crossover_rate: 交叉概率
            mutation_rate: 变异概率
            maximize: True求最大值，False求最小值
        """
        self.func = func
        self.n_dim = n_dim
        self.bounds = np.array(bounds)
        self.pop_size = pop_size
        self.max_iter = max_iter
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.maximize = maximize

        # 编码长度（每个变量用20位二进制表示）
        self.gene_length = 20
        self.total_length = n_dim * self.gene_length

    def encode(self, x):
        """实数 -> 二进制编码"""
        chromosome = []
        for i in range(self.n_dim):
            low, high = self.bounds[i]
            # 映射到 [0, 2^gene_length - 1]
            int_val = int((x[i] - low) / (high - low) * (2**self.gene_length - 1))
            chromosome.extend([int(b) for b in format(int_val, f'0{self.gene_length}b')])
        return np.array(chromosome)

    def decode(self, chromosome):
        """二进制 -> 实数"""
        x = np.zeros(self.n_dim)
        for i in range(self.n_dim):
            gene = chromosome[i*self.gene_length:(i+1)*self.gene_length]
            int_val = int(''.join(map(str, gene)), 2)
            low, high = self.bounds[i]
            x[i] = low + int_val / (2**self.gene_length - 1) * (high - low)
        return x

    def init_population(self):
        """初始化种群"""
        pop = []
        for _ in range(self.pop_size):
            x = np.random.uniform(self.bounds[:, 0], self.bounds[:, 1])
            pop.append(self.encode(x))
        return np.array(pop)

    def fitness(self, population):
        """计算适应度"""
        scores = []
        for ind in population:
            x = self.decode(ind)
            val = self.func(x)
            if self.maximize:
                scores.append(val)
            else:
                scores.append(-val)  # 求最小值时取负
        return np.array(scores)

    def select(self, population, scores):
        """轮盘赌选择"""
        # 确保适应度为正
        scores = scores - scores.min() + 1e-6
        probs = scores / scores.sum()
        indices = np.random.choice(len(population), size=self.pop_size, p=probs)
        return population[indices]

    def crossover(self, population):
        """单点交叉"""
        new_pop = []
        for i in range(0, self.pop_size, 2):
            parent1 = population[i].copy()
            parent2 = population[min(i+1, self.pop_size-1)].copy()
            if np.random.rand() < self.crossover_rate:
                point = np.random.randint(1, self.total_length)
                child1 = np.concatenate([parent1[:point], parent2[point:]])
                child2 = np.concatenate([parent2[:point], parent1[point:]])
                new_pop.extend([child1, child2])
            else:
                new_pop.extend([parent1, parent2])
        return np.array(new_pop[:self.pop_size])

    def mutate(self, population):
        """位翻转变异"""
        for i in range(self.pop_size):
            for j in range(self.total_length):
                if np.random.rand() < self.mutation_rate:
                    population[i, j] = 1 - population[i, j]
        return population

    def run(self):
        """运行遗传算法"""
        population = self.init_population()
        best_history = []
        best_individual = None
        best_score = -np.inf

        for gen in range(self.max_iter):
            scores = self.fitness(population)
            population = self.select(population, scores)
            population = self.crossover(population)
            population = self.mutate(population)

            # 记录最优
            current_best_idx = np.argmax(scores)
            if scores[current_best_idx] > best_score:
                best_score = scores[current_best_idx]
                best_individual = population[current_best_idx].copy()
            best_history.append(best_score if self.maximize else -best_score)

            if gen % 20 == 0:
                print(f"第{gen:3d}代: 最优值 = {best_history[-1]:.6f}")

        best_x = self.decode(best_individual)
        best_val = self.func(best_x)
        return best_x, best_val, best_history


# ============================================================
# 测试：求 f(x) = x * sin(10*pi*x) + 2 的最大值
# ============================================================
if __name__ == "__main__":
    def test_func(x):
        return x[0] * np.sin(10 * np.pi * x[0]) + 2

    ga = GeneticAlgorithm(
        func=test_func,
        n_dim=1,
        bounds=[(-1, 2)],
        pop_size=50,
        max_iter=200,
        crossover_rate=0.8,
        mutation_rate=0.01,
        maximize=True
    )

    best_x, best_val, history = ga.run()

    print("\n" + "=" * 50)
    print("遗传算法求解结果")
    print("=" * 50)
    print(f"最优解: x = {best_x[0]:.6f}")
    print(f"最优值: f(x) = {best_val:.6f}")

    # 绘制收敛曲线
    plt.figure(figsize=(10, 4))
    plt.plot(history)
    plt.xlabel('迭代次数')
    plt.ylabel('最优值')
    plt.title('遗传算法收敛曲线')
    plt.grid(True)
    plt.savefig('GA_convergence.png', dpi=150, bbox_inches='tight')
    print("收敛曲线已保存为 GA_convergence.png")


# ============================================================
# 快速使用版（简化版，直接用scikit-opt库）
# ============================================================
"""
# 安装：pip install scikit-opt
from sko.GA import GA

def demo_func(x):
    x1, x2 = x
    return x1 ** 2 + (x2 - 0.05) ** 2

ga = GA(func=demo_func, n_dim=2, size_pop=50, max_iter=200,
        lb=[-1, -1], ub=[1, 1], precision=1e-7)
best_x, best_y = ga.run()
print('best_x:', best_x, 'best_y:', best_y)
"""
