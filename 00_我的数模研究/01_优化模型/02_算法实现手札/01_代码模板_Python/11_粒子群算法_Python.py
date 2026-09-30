"""
粒子群优化算法 (Particle Swarm Optimization, PSO) Python 代码模板

适用场景：
- 连续函数全局优化
- 神经网络训练、参数优化
- 多峰函数优化

核心思想：
- 每个粒子有位置和速度
- 粒子跟踪个体最优(pbest)和全局最优(gbest)
- 速度更新：v = w*v + c1*r1*(pbest-x) + c2*r2*(gbest-x)
- 位置更新：x = x + v
"""

import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# 粒子群算法：连续函数优化
# ============================================================

class ParticleSwarmOptimization:
    def __init__(self, func, n_dim, bounds,
                 pop_size=30, max_iter=200,
                 w=0.8, c1=1.5, c2=1.5,
                 maximize=True):
        """
        参数:
            func: 目标函数
            n_dim: 变量维度
            bounds: 变量边界 [(low, high), ...]
            pop_size: 粒子数量
            max_iter: 最大迭代次数
            w: 惯性权重（0.4-0.9，大则全局搜索强，小则局部搜索强）
            c1: 个体学习因子（通常1.5-2）
            c2: 社会学习因子（通常1.5-2）
            maximize: True求最大值，False求最小值
        """
        self.func = func
        self.n_dim = n_dim
        self.bounds = np.array(bounds)
        self.pop_size = pop_size
        self.max_iter = max_iter
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.maximize = maximize

        # 速度范围（通常为位置范围的10%-20%）
        self.v_max = (self.bounds[:, 1] - self.bounds[:, 0]) * 0.2

    def init_particles(self):
        """初始化粒子群"""
        # 位置
        positions = np.random.uniform(
            self.bounds[:, 0], self.bounds[:, 1],
            size=(self.pop_size, self.n_dim)
        )
        # 速度
        velocities = np.random.uniform(
            -self.v_max, self.v_max,
            size=(self.pop_size, self.n_dim)
        )
        return positions, velocities

    def evaluate(self, positions):
        """计算适应度"""
        scores = np.array([self.func(p) for p in positions])
        return scores

    def run(self):
        """运行粒子群算法"""
        positions, velocities = self.init_particles()
        scores = self.evaluate(positions)

        # 个体最优
        pbest_pos = positions.copy()
        pbest_score = scores.copy()

        # 全局最优
        if self.maximize:
            gbest_idx = np.argmax(scores)
        else:
            gbest_idx = np.argmin(scores)
        gbest_pos = positions[gbest_idx].copy()
        gbest_score = scores[gbest_idx]

        history = [gbest_score]

        for iter in range(self.max_iter):
            # 更新速度
            r1 = np.random.rand(self.pop_size, self.n_dim)
            r2 = np.random.rand(self.pop_size, self.n_dim)

            velocities = (self.w * velocities +
                          self.c1 * r1 * (pbest_pos - positions) +
                          self.c2 * r2 * (gbest_pos - positions))

            # 限制速度
            velocities = np.clip(velocities, -self.v_max, self.v_max)

            # 更新位置
            positions = positions + velocities

            # 边界处理
            positions = np.clip(positions, self.bounds[:, 0], self.bounds[:, 1])

            # 评估新位置
            scores = self.evaluate(positions)

            # 更新个体最优
            if self.maximize:
                update_mask = scores > pbest_score
            else:
                update_mask = scores < pbest_score
            pbest_pos[update_mask] = positions[update_mask]
            pbest_score[update_mask] = scores[update_mask]

            # 更新全局最优
            if self.maximize:
                current_best_idx = np.argmax(scores)
                if scores[current_best_idx] > gbest_score:
                    gbest_pos = positions[current_best_idx].copy()
                    gbest_score = scores[current_best_idx]
            else:
                current_best_idx = np.argmin(scores)
                if scores[current_best_idx] < gbest_score:
                    gbest_pos = positions[current_best_idx].copy()
                    gbest_score = scores[current_best_idx]

            history.append(gbest_score)

            if iter % 20 == 0:
                print(f"迭代{iter:3d}: 最优值 = {gbest_score:.6f}")

        return gbest_pos, gbest_score, history


# ============================================================
# 测试：求 f(x,y) = (1-x)^2 + 100*(y-x^2)^2 的最小值（Rosenbrock函数）
# ============================================================
if __name__ == "__main__":
    def rosenbrock(x):
        return (1 - x[0])**2 + 100 * (x[1] - x[0]**2)**2

    pso = ParticleSwarmOptimization(
        func=rosenbrock,
        n_dim=2,
        bounds=[(-5, 5), (-5, 5)],
        pop_size=30,
        max_iter=200,
        w=0.7,
        c1=1.5,
        c2=1.5,
        maximize=False
    )

    best_x, best_val, history = pso.run()

    print("\n" + "=" * 50)
    print("粒子群算法求解结果")
    print("=" * 50)
    print(f"最优解: x = {best_x[0]:.6f}, y = {best_x[1]:.6f}")
    print(f"最优值: f(x,y) = {best_val:.6f}")
    print(f"理论最优: (1, 1), f=0")

    # 绘制收敛曲线
    plt.figure(figsize=(10, 4))
    plt.plot(history)
    plt.xlabel('迭代次数')
    plt.ylabel('最优值')
    plt.title('粒子群算法收敛曲线')
    plt.grid(True)
    plt.savefig('PSO_convergence.png', dpi=150, bbox_inches='tight')
    print("收敛曲线已保存为 PSO_convergence.png")


# ============================================================
# 参数调节指南
# ============================================================
"""
惯性权重 w:
- 较大（0.9）：全局搜索能力强，适合多峰函数
- 较小（0.4）：局部搜索能力强，适合精细调整
- 常用策略：线性递减权重，从0.9降到0.4
  w = w_max - (w_max - w_min) * iter / max_iter

学习因子 c1, c2:
- c1 = c2 = 2：经典设置
- c1 > c2：更多关注个体经验
- c2 > c1：更多关注群体经验
- 常用：c1 = c2 = 1.5 或 2

粒子数量 pop_size:
- 简单问题：20-30
- 复杂问题：50-100
- 太多：计算慢，太少：容易陷入局部最优

速度限制 v_max:
- 通常为变量范围的10%-20%
- 太大：粒子飞过最优解
- 太小：搜索不充分
"""
