"""
动态规划 Python 代码模板

适用场景：
- 最优子结构 + 重叠子问题
- 背包问题、最短路径、资源分配、生产计划
"""

# ============================================================
# 例题1：0-1背包问题（动态规划解法）
# ============================================================
print("=" * 50)
print("0-1背包问题（动态规划）")
print("=" * 50)

def knapsack_01(weights, values, capacity):
    """
    0-1背包问题

    参数:
        weights: 物品重量列表
        values: 物品价值列表
        capacity: 背包容量

    返回:
        max_value: 最大价值
        selected: 选中物品的索引列表
    """
    n = len(weights)
    # dp[i][w] 表示前i个物品，容量w时的最大价值
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    # 填充dp表
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i-1][w],
                               dp[i-1][w - weights[i-1]] + values[i-1])
            else:
                dp[i][w] = dp[i-1][w]

    # 回溯找选中的物品
    selected = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            selected.append(i - 1)
            w -= weights[i-1]
    selected.reverse()

    return dp[n][capacity], selected

# 测试
weights = [2, 3, 4, 5, 6]
values = [3, 4, 5, 6, 7]
capacity = 10

max_val, selected = knapsack_01(weights, values, capacity)
print(f"最大价值: {max_val}")
print(f"选中物品: {selected}")
print(f"选中物品详情:")
for i in selected:
    print(f"  物品{i+1}: 重量{weights[i]}, 价值{values[i]}")

# ============================================================
# 例题2：完全背包问题（物品可重复选）
# ============================================================
print("\n" + "=" * 50)
print("完全背包问题")
print("=" * 50)

def knapsack_complete(weights, values, capacity):
    n = len(weights)
    dp = [0] * (capacity + 1)

    for w in range(capacity + 1):
        for i in range(n):
            if weights[i] <= w:
                dp[w] = max(dp[w], dp[w - weights[i]] + values[i])

    return dp[capacity]

max_val_complete = knapsack_complete(weights, values, capacity)
print(f"最大价值（可重复选）: {max_val_complete}")

# ============================================================
# 例题3：最短路径问题（多阶段决策）
# ============================================================
print("\n" + "=" * 50)
print("最短路径问题（多阶段决策）")
print("=" * 50)

# 图的邻接矩阵，INF表示不可达
INF = float('inf')
graph = [
    [0, 2, 5, INF, INF, INF],   # 节点0
    [INF, 0, 1, 4, INF, INF],   # 节点1
    [INF, INF, 0, 2, 3, INF],   # 节点2
    [INF, INF, INF, 0, 1, 5],   # 节点3
    [INF, INF, INF, INF, 0, 2], # 节点4
    [INF, INF, INF, INF, INF, 0] # 节点5
]

def shortest_path_dp(graph, start, end):
    """动态规划求最短路径（DAG图）"""
    n = len(graph)
    # dp[i] 表示从start到i的最短距离
    dp = [INF] * n
    dp[start] = 0
    parent = [-1] * n

    # 按拓扑序更新（这里假设节点编号就是拓扑序）
    for u in range(n):
        if dp[u] == INF:
            continue
        for v in range(n):
            if graph[u][v] != INF and dp[u] + graph[u][v] < dp[v]:
                dp[v] = dp[u] + graph[u][v]
                parent[v] = u

    # 回溯路径
    path = []
    node = end
    while node != -1:
        path.append(node)
        node = parent[node]
    path.reverse()

    return dp[end], path

dist, path = shortest_path_dp(graph, 0, 5)
print(f"最短距离: {dist}")
print(f"路径: {' → '.join(map(str, path))}")

# ============================================================
# 例题4：资源分配问题
# ============================================================
print("\n" + "=" * 50)
print("资源分配问题")
print("=" * 50)

# 将5个资源分配给3个项目，各项目获得不同资源数的收益如下
# profit[i][j] 表示项目i分配j个资源的收益
profit = [
    [0, 3, 5, 7, 9, 10],   # 项目1
    [0, 2, 4, 6, 8, 9],    # 项目2
    [0, 4, 6, 8, 9, 11]    # 项目3
]
total_resources = 5

def resource_allocation(profit, total):
    n_projects = len(profit)
    # dp[i][j] 表示前i个项目分配j个资源的最大收益
    dp = [[0] * (total + 1) for _ in range(n_projects + 1)]
    alloc = [[0] * (total + 1) for _ in range(n_projects + 1)]

    for i in range(1, n_projects + 1):
        for j in range(total + 1):
            for k in range(j + 1):
                if dp[i-1][j-k] + profit[i-1][k] > dp[i][j]:
                    dp[i][j] = dp[i-1][j-k] + profit[i-1][k]
                    alloc[i][j] = k

    # 回溯分配方案
    allocation = [0] * n_projects
    j = total
    for i in range(n_projects, 0, -1):
        allocation[i-1] = alloc[i][j]
        j -= alloc[i][j]

    return dp[n_projects][total], allocation

max_profit, allocation = resource_allocation(profit, total_resources)
print(f"最大总收益: {max_profit}")
print(f"分配方案: 项目1={allocation[0]}, 项目2={allocation[1]}, 项目3={allocation[2]}")
