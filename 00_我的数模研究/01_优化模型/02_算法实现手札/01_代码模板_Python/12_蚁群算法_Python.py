"""
蚁群算法 (Ant Colony Optimization, ACO) Python 代码模板

适用场景：
- 旅行商问题(TSP)
- 车辆路径问题(VRP)
- 网络路由、调度问题
- 其他组合优化问题

核心思想：
- 蚂蚁在路径上留下信息素
- 信息素浓度高的路径被选择概率大
- 信息素随时间挥发，避免陷入局部最优
- 正反馈机制：好路径上信息素越来越多
"""

import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# 蚁群算法求解TSP问题
# ============================================================

class AntColonyTSP:
    def __init__(self, distances, n_ants=20, max_iter=100,
                 alpha=1.0, beta=5.0, rho=0.5, Q=100):
        """
        参数:
            distances: 距离矩阵 (n x n)
            n_ants: 蚂蚁数量
            max_iter: 最大迭代次数
            alpha: 信息素重要程度因子（越大越依赖信息素）
            beta: 启发函数重要程度因子（越大越依赖距离）
            rho: 信息素挥发系数（0-1，越大挥发越快）
            Q: 信息素释放总量
        """
        self.distances = distances
        self.n = len(distances)
        self.n_ants = n_ants
        self.max_iter = max_iter
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.Q = Q

        # 初始化信息素矩阵（初始为1）
        self.pheromone = np.ones((self.n, self.n))
        # 启发函数（距离的倒数）
        self.visibility = 1 / (distances + np.eye(self.n) * 1e-10)

    def construct_solution(self):
        """一只蚂蚁构造完整路径"""
        path = [np.random.randint(self.n)]  # 随机起点
        visited = set(path)

        while len(path) < self.n:
            current = path[-1]
            # 计算转移概率
            probs = []
            for j in range(self.n):
                if j not in visited:
                    tau = self.pheromone[current][j] ** self.alpha
                    eta = self.visibility[current][j] ** self.beta
                    probs.append(tau * eta)
                else:
                    probs.append(0)

            probs = np.array(probs)
            probs = probs / probs.sum()  # 归一化

            # 轮盘赌选择下一个城市
            next_city = np.random.choice(self.n, p=probs)
            path.append(next_city)
            visited.add(next_city)

        return path

    def path_length(self, path):
        """计算路径总长度"""
        length = 0
        for i in range(len(path)):
            length += self.distances[path[i]][path[(i + 1) % self.n]]
        return length

    def update_pheromone(self, paths, lengths):
        """更新信息素"""
        # 信息素挥发
        self.pheromone *= (1 - self.rho)

        # 蚂蚁释放信息素
        for path, length in zip(paths, lengths):
            for i in range(len(path)):
                self.pheromone[path[i]][path[(i + 1) % self.n]] += self.Q / length

    def run(self):
        """运行蚁群算法"""
        best_path = None
        best_length = float('inf')
        history = []

        for iter in range(self.max_iter):
            # 所有蚂蚁构造路径
            paths = [self.construct_solution() for _ in range(self.n_ants)]
            lengths = [self.path_length(p) for p in paths]

            # 更新最优解
            min_idx = np.argmin(lengths)
            if lengths[min_idx] < best_length:
                best_length = lengths[min_idx]
                best_path = paths[min_idx].copy()

            # 更新信息素
            self.update_pheromone(paths, lengths)

            history.append(best_length)

            if iter % 10 == 0:
                print(f"迭代{iter:3d}: 最短路径 = {best_length:.2f}")

        return best_path, best_length, history


# ============================================================
# 测试：随机生成城市坐标
# ============================================================
if __name__ == "__main__":
    np.random.seed(42)
    n_cities = 20
    cities = np.random.rand(n_cities, 2) * 100  # 随机城市坐标

    # 计算距离矩阵
    distances = np.zeros((n_cities, n_cities))
    for i in range(n_cities):
        for j in range(n_cities):
            distances[i][j] = np.sqrt(np.sum((cities[i] - cities[j]) ** 2))

    # 运行蚁群算法
    aco = AntColonyTSP(
        distances=distances,
        n_ants=30,
        max_iter=100,
        alpha=1.0,
        beta=5.0,
        rho=0.5,
        Q=100
    )

    best_path, best_length, history = aco.run()

    print("\n" + "=" * 50)
    print("蚁群算法求解TSP结果")
    print("=" * 50)
    print(f"最短路径长度: {best_length:.2f}")
    print(f"最优路径: {best_path}")

    # 绘制结果
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # 最优路径
    ax1.scatter(cities[:, 0], cities[:, 1], c='red', s=50, zorder=5)
    for i in range(n_cities):
        ax1.annotate(str(i), (cities[i, 0], cities[i, 1]),
                     fontsize=8, ha='center', va='bottom')
    for i in range(n_cities):
        start = best_path[i]
        end = best_path[(i + 1) % n_cities]
        ax1.plot([cities[start, 0], cities[end, 0]],
                 [cities[start, 1], cities[end, 1]], 'b-', alpha=0.7)
    ax1.set_title(f'最优路径 (长度={best_length:.2f})')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.grid(True)

    # 收敛曲线
    ax2.plot(history)
    ax2.set_xlabel('迭代次数')
    ax2.set_ylabel('最短路径长度')
    ax2.set_title('收敛曲线')
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig('ACO_TSP_result.png', dpi=150, bbox_inches='tight')
    print("结果图已保存为 ACO_TSP_result.png")


# ============================================================
# 参数调节指南
# ============================================================
"""
alpha (信息素重要程度):
- 太小：蚂蚁主要靠贪心选择，容易局部最优
- 太大：过早收敛，多样性不足
- 建议：0.5-2.0，常用1.0

beta (启发函数重要程度):
- 太小：搜索太随机，收敛慢
- 太大：贪心太强，容易局部最优
- 建议：2-10，常用5.0

rho (信息素挥发系数):
- 太小：信息素积累太多，容易早熟
- 太大：信息素挥发太快，搜索随机性太强
- 建议：0.1-0.8，常用0.5

n_ants (蚂蚁数量):
- 太少：搜索不充分
- 太多：计算慢
- 建议：城市数的1-2倍

Q (信息素释放量):
- 影响信息素更新幅度，通常不影响最终结果
- 建议：10-1000
"""
