"""
整数规划 Python 代码模板
使用 pulp 库求解（需要安装：pip install pulp）

适用场景：
- 0-1规划（指派问题、选址问题、背包问题）
- 整数规划（生产数量、人员安排）
- 混合整数规划
"""

import pulp

# ============================================================
# 例题1：指派问题
# 4个人做4项工作，每人做一项，每项工作一人做
# 求最小总时间
# ============================================================

# 效率矩阵（人i做工作j的时间）
cost_matrix = [
    [3, 8, 9, 4],
    [5, 2, 7, 6],
    [9, 5, 4, 8],
    [7, 6, 3, 5]
]

n = len(cost_matrix)

# 创建问题（求最小值）
prob = pulp.LpProblem("指派问题", pulp.LpMinimize)

# 决策变量：x[i][j] = 1 表示人i做工作j
x = [[pulp.LpVariable(f"x_{i}_{j}", cat='Binary') for j in range(n)] for i in range(n)]

# 目标函数：最小化总时间
prob += pulp.lpSum(cost_matrix[i][j] * x[i][j] for i in range(n) for j in range(n))

# 约束1：每人做一项工作
for i in range(n):
    prob += pulp.lpSum(x[i][j] for j in range(n)) == 1

# 约束2：每项工作一人做
for j in range(n):
    prob += pulp.lpSum(x[i][j] for i in range(n)) == 1

# 求解
prob.solve(pulp.PULP_CBC_CMD(msg=0))

print("=" * 50)
print("指派问题求解结果")
print("=" * 50)
print(f"状态: {pulp.LpStatus[prob.status]}")
print(f"最小总时间: {pulp.value(prob.objective)}")
print("指派方案:")
for i in range(n):
    for j in range(n):
        if pulp.value(x[i][j]) > 0.5:
            print(f"  人{i+1} → 工作{j+1} (时间{cost_matrix[i][j]})")

# ============================================================
# 例题2：0-1背包问题
# 有5个物品，重量和价值如下，背包容量10
# 求最大价值
# ============================================================

print("\n" + "=" * 50)
print("0-1背包问题")
print("=" * 50)

weights = [2, 3, 4, 5, 6]
values = [3, 4, 5, 6, 7]
capacity = 10
n_items = len(weights)

prob2 = pulp.LpProblem("背包问题", pulp.LpMaximize)

# 决策变量
y = [pulp.LpVariable(f"y_{i}", cat='Binary') for i in range(n_items)]

# 目标函数
prob2 += pulp.lpSum(values[i] * y[i] for i in range(n_items))

# 约束：总重量不超过容量
prob2 += pulp.lpSum(weights[i] * y[i] for i in range(n_items)) <= capacity

prob2.solve(pulp.PULP_CBC_CMD(msg=0))

print(f"最大价值: {pulp.value(prob2.objective)}")
print("选中物品:")
total_weight = 0
for i in range(n_items):
    if pulp.value(y[i]) > 0.5:
        print(f"  物品{i+1}: 重量{weights[i]}, 价值{values[i]}")
        total_weight += weights[i]
print(f"总重量: {total_weight}/{capacity}")

# ============================================================
# 通用函数封装
# ============================================================

def solve_assignment(cost_matrix, maximize=False):
    """
    通用指派问题求解器

    参数:
        cost_matrix: 二维列表，成本/效率矩阵
        maximize: True求最大值，False求最小值

    返回:
        assignment: 列表，assignment[i] = j 表示人i做工作j
        total_cost: 总成本/收益
    """
    n = len(cost_matrix)
    sense = pulp.LpMaximize if maximize else pulp.LpMinimize
    prob = pulp.LpProblem("Assignment", sense)

    x = [[pulp.LpVariable(f"x_{i}_{j}", cat='Binary') for j in range(n)] for i in range(n)]

    if maximize:
        prob += pulp.lpSum(cost_matrix[i][j] * x[i][j] for i in range(n) for j in range(n))
    else:
        prob += pulp.lpSum(cost_matrix[i][j] * x[i][j] for i in range(n) for j in range(n))

    for i in range(n):
        prob += pulp.lpSum(x[i][j] for j in range(n)) == 1
    for j in range(n):
        prob += pulp.lpSum(x[i][j] for i in range(n)) == 1

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    assignment = [-1] * n
    for i in range(n):
        for j in range(n):
            if pulp.value(x[i][j]) > 0.5:
                assignment[i] = j
                break

    return assignment, pulp.value(prob.objective)
