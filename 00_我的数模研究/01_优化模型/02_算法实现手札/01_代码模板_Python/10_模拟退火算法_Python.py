"""
模拟退火算法 (Simulated Annealing, SA) Python 代码模板

适用场景：
- 全局优化，避免局部最优
- 组合优化问题（TSP、调度）
- 接受劣解的概率随温度降低而减小

核心思想：
- 以一定概率接受比当前解差的解（Metropolis准则）
- 温度高时接受概率大（广搜），温度低时接受概率小（精搜）
"""

import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# 模拟退火算法：连续函数优化
# ============================================================

class SimulatedAnnealing:
    def __init__(self, func, n_dim, bounds,
                 initial_temp=1000, cooling_rate=0.95,
                 min_temp=1e-5, max_iter=1000,
                 step_size=0.1, maximize=True):
        """
        参数:
            func: 目标函数
            n_dim: 变量维度
            bounds: 变量边界
            initial_temp: 初始温度
            cooling_rate: 降温系数（0-1之间，越接近1降温越慢）
            min_temp: 最低温度
            max_iter: 最大迭代次数
            step_size: 邻域搜索步长
            maximize: True求最大值，False求最小值
        """
        self.func = func
        self.n_dim = n_dim
        self.bounds = np.array(bounds)
        self.T = initial_temp
        self.cooling_rate = cooling_rate
        self.min_temp = min_temp
        self.max_iter = max_iter
        self.step_size = step_size
        self.maximize = maximize

    def get_random_solution(self):
        """随机生成初始解"""
        return np.random.uniform(self.bounds[:, 0], self.bounds[:, 1])

    def get_neighbor(self, x):
        """在当前解附近生成新解"""
        new_x = x + np.random.normal(0, self.step_size, self.n_dim)
        # 边界处理
        new_x = np.clip(new_x, self.bounds[:, 0], self.bounds[:, 1])
        return new_x

    def acceptance_probability(self, delta_E, T):
        """Metropolis准则：接受新解的概率"""
        if self.maximize:
            # 最大化：delta_E = E_new - E_old，正的更好
            if delta_E > 0:
                return 1.0  # 新解更好，一定接受
            else:
                return np.exp(delta_E / T)  # 新解更差，以概率接受
        else:
            # 最小化：delta_E = E_new - E_old，负的更好
            if delta_E < 0:
                return 1.0
            else:
                return np.exp(-delta_E / T)

    def run(self):
        """运行模拟退火算法"""
        # 初始化
        current = self.get_random_solution()
        current_val = self.func(current)
        best = current.copy()
        best_val = current_val

        history = [best_val]
        temp_history = [self.T]

        iteration = 0
        while self.T > self.min_temp and iteration < self.max_iter:
            # 生成新解
            new_solution = self.get_neighbor(current)
            new_val = self.func(new_solution)

            # 计算接受概率
            delta_E = new_val - current_val
            prob = self.acceptance_probability(delta_E, self.T)

            # 接受或拒绝
            if np.random.rand() < prob:
                current = new_solution
                current_val = new_val

            # 更新最优解
            if self.maximize:
                if current_val > best_val:
                    best = current.copy()
                    best_val = current_val
            else:
                if current_val < best_val:
                    best = current.copy()
                    best_val = current_val

            # 降温
            self.T *= self.cooling_rate

            history.append(best_val)
            temp_history.append(self.T)
            iteration += 1

            if iteration % 100 == 0:
                print(f"迭代{iteration:4d}: 温度={self.T:.4f}, 最优值={best_val:.6f}")

        return best, best_val, history, temp_history


# ============================================================
# 测试：求 f(x) = x * sin(10*pi*x) + 2 的最大值
# ============================================================
if __name__ == "__main__":
    def test_func(x):
        return x[0] * np.sin(10 * np.pi * x[0]) + 2

    sa = SimulatedAnnealing(
        func=test_func,
        n_dim=1,
        bounds=[(-1, 2)],
        initial_temp=100,
        cooling_rate=0.99,
        min_temp=1e-4,
        max_iter=500,
        step_size=0.1,
        maximize=True
    )

    best_x, best_val, history, temp_history = sa.run()

    print("\n" + "=" * 50)
    print("模拟退火算法求解结果")
    print("=" * 50)
    print(f"最优解: x = {best_x[0]:.6f}")
    print(f"最优值: f(x) = {best_val:.6f}")

    # 绘制收敛曲线
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(history)
    ax1.set_xlabel('迭代次数')
    ax1.set_ylabel('最优值')
    ax1.set_title('收敛曲线')
    ax1.grid(True)

    ax2.plot(temp_history)
    ax2.set_xlabel('迭代次数')
    ax2.set_ylabel('温度')
    ax2.set_title('温度下降曲线')
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig('SA_convergence.png', dpi=150, bbox_inches='tight')
    print("收敛曲线已保存为 SA_convergence.png")


# ============================================================
# 参数调节指南
# ============================================================
"""
初始温度 initial_temp:
- 太小：容易陷入局部最优
- 太大：收敛慢，浪费计算
- 建议：100-1000，根据问题调整

降温系数 cooling_rate:
- 接近1（如0.99）：降温慢，搜索充分，但迭代多
- 接近0（如0.8）：降温快，可能错过最优
- 建议：0.95-0.99

步长 step_size:
- 太大：在最优解附近震荡
- 太小：搜索慢，容易局部最优
- 建议：变量范围的1%-10%

终止条件：
- 温度降到 min_temp
- 或达到 max_iter
"""
