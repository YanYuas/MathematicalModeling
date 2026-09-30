"""
差分进化算法 (Differential Evolution, DE) Python 代码模板

适用场景：
- 连续函数全局优化
- 非线性、不可导、多峰函数
- 比遗传算法更适合实数编码问题

核心思想：
- 变异：用两个个体的差加权加到第三个个体上
- 交叉：变异个体与目标个体混合
- 选择：贪心选择，保留优者
"""

import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# 差分进化算法
# ============================================================

class DifferentialEvolution:
    def __init__(self, func, n_dim, bounds,
                 pop_size=50, max_iter=200,
                 F=0.5, CR=0.7, maximize=False):
        """
        参数:
            func: 目标函数
            n_dim: 变量维度
            bounds: 变量边界 [(low, high), ...]
            pop_size: 种群大小
            max_iter: 最大迭代次数
            F: 缩放因子（变异幅度，0.4-0.9）
            CR: 交叉概率（0-1）
            maximize: True求最大值，False求最小值
        """
        self.func = func
        self.n_dim = n_dim
        self.bounds = np.array(bounds)
        self.pop_size = pop_size
        self.max_iter = max_iter
        self.F = F
        self.CR = CR
        self.maximize = maximize

    def init_population(self):
        """初始化种群"""
        return np.random.uniform(
            self.bounds[:, 0], self.bounds[:, 1],
            size=(self.pop_size, self.n_dim)
        )

    def mutate(self, population, idx):
        """变异操作：DE/rand/1策略"""
        # 随机选择三个不同的个体
        candidates = [i for i in range(self.pop_size) if i != idx]
        r1, r2, r3 = np.random.choice(candidates, 3, replace=False)
        # 变异向量
        mutant = population[r1] + self.F * (population[r2] - population[r3])
        # 边界处理
        mutant = np.clip(mutant, self.bounds[:, 0], self.bounds[:, 1])
        return mutant

    def crossover(self, target, mutant):
        """交叉操作：二项式交叉"""
        trial = target.copy()
        # 至少有一个维度来自变异体
        j_rand = np.random.randint(self.n_dim)
        for j in range(self.n_dim):
            if np.random.rand() < self.CR or j == j_rand:
                trial[j] = mutant[j]
        return trial

    def select(self, target, trial):
        """选择操作：贪心选择"""
        target_val = self.func(target)
        trial_val = self.func(trial)

        if self.maximize:
            return trial if trial_val > target_val else target
        else:
            return trial if trial_val < target_val else target

    def run(self):
        """运行差分进化算法"""
        population = self.init_population()
        scores = np.array([self.func(ind) for ind in population])

        if self.maximize:
            best_idx = np.argmax(scores)
        else:
            best_idx = np.argmin(scores)

        best_individual = population[best_idx].copy()
        best_score = scores[best_idx]
        history = [best_score]

        for gen in range(self.max_iter):
            for i in range(self.pop_size):
                # 变异
                mutant = self.mutate(population, i)
                # 交叉
                trial = self.crossover(population[i], mutant)
                # 选择
                population[i] = self.select(population[i], trial)

            # 评估
            scores = np.array([self.func(ind) for ind in population])
            if self.maximize:
                best_idx = np.argmax(scores)
                if scores[best_idx] > best_score:
                    best_score = scores[best_idx]
                    best_individual = population[best_idx].copy()
            else:
                best_idx = np.argmin(scores)
                if scores[best_idx] < best_score:
                    best_score = scores[best_idx]
                    best_individual = population[best_idx].copy()

            history.append(best_score)

            if gen % 20 == 0:
                print(f"第{gen:3d}代: 最优值 = {best_score:.6f}")

        return best_individual, best_score, history


# ============================================================
# 测试：Rastrigin函数（经典多峰测试函数）
# f(x) = 10n + Σ(xi² - 10cos(2πxi))
# 全局最优：x=0, f=0
# ============================================================
if __name__ == "__main__":
    def rastrigin(x):
        return 10 * len(x) + sum([xi**2 - 10 * np.cos(2 * np.pi * xi) for xi in x])

    de = DifferentialEvolution(
        func=rastrigin,
        n_dim=10,
        bounds=[(-5.12, 5.12)] * 10,
        pop_size=50,
        max_iter=300,
        F=0.5,
        CR=0.7,
        maximize=False
    )

    best_x, best_val, history = de.run()

    print("\n" + "=" * 50)
    print("差分进化算法求解Rastrigin函数")
    print("=" * 50)
    print(f"最优解: x = {np.round(best_x, 4)}")
    print(f"最优值: f(x) = {best_val:.6f}")
    print(f"理论最优: f(0) = 0")

    # 绘制收敛曲线
    plt.figure(figsize=(10, 4))
    plt.plot(history)
    plt.xlabel('迭代次数')
    plt.ylabel('最优值')
    plt.title('差分进化算法收敛曲线 (Rastrigin函数, 10维)')
    plt.grid(True)
    plt.savefig('DE_convergence.png', dpi=150, bbox_inches='tight')
    print("收敛曲线已保存为 DE_convergence.png")


# ============================================================
# DE的变体策略
# ============================================================
"""
DE/x/y/z 命名规则：
- x: 变异向量的选择方式
  - rand: 随机选择
  - best: 选择当前最优
  - target-to-best: 目标个体向最优移动
- y: 差向量的数量（1或2）
- z: 交叉方式
  - bin: 二项式交叉
  - exp: 指数交叉

常用策略：
1. DE/rand/1/bin：最经典，鲁棒性好
2. DE/best/1/bin：收敛快，容易局部最优
3. DE/rand/2/bin：种群多样性好，适合多峰
4. DE/best/2/bin：
5. DE/target-to-best/1/bin：自适应步长

参数选择：
- F (缩放因子):
  - 太小：种群多样性丧失，早熟
  - 太大：搜索太随机，收敛慢
  - 建议：0.4-0.9，常用0.5
  - 自适应：F = 0.5 + 0.5*rand()

- CR (交叉概率):
  - 太小：搜索慢
  - 太大：收敛快但可能早熟
  - 建议：0.3-0.9，常用0.7
  - 可分问题用小CR，不可分问题用大CR

- pop_size (种群大小):
  - 简单问题：20-30
  - 复杂问题：50-100
  - 高维问题：100+
"""
