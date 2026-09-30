"""
线性规划 Python 代码模板
使用 scipy.optimize.linprog 求解

标准形式：
    min  c^T x
    s.t. A_ub @ x <= b_ub
         A_eq @ x == b_eq
         lb <= x <= ub

注意：scipy 的 linprog 只能求最小值，求最大值时目标函数系数取负
"""

import numpy as np
from scipy.optimize import linprog

# ============================================================
# 例题：生产计划问题
# 某工厂生产甲、乙两种产品，每单位利润分别为3元和5元
# 生产甲需1个单位原料A，2个单位原料B
# 生产乙需2个单位原料A，1个单位原料B
# 原料A限量8单位，原料B限量10单位
# 求最大利润
# ============================================================

# 目标函数：max 3*x1 + 5*x2  →  min -3*x1 -5*x2
c = [-3, -5]

# 不等式约束：A_ub @ x <= b_ub
# 原料A：x1 + 2*x2 <= 8
# 原料B：2*x1 + x2 <= 10
A_ub = [
    [1, 2],
    [2, 1]
]
b_ub = [8, 10]

# 等式约束（本例无）
A_eq = None
b_eq = None

# 变量边界：x1 >= 0, x2 >= 0
bounds = [(0, None), (0, None)]

# 求解
result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                 bounds=bounds, method='highs')

print("=" * 50)
print("线性规划求解结果")
print("=" * 50)
print(f"最优解: x1 = {result.x[0]:.4f}, x2 = {result.x[1]:.4f}")
print(f"最大利润: {-result.fun:.4f} 元")
print(f"求解状态: {result.message}")

# ============================================================
# 通用函数封装
# ============================================================

def solve_lp(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None, bounds=None, maximize=False):
    """
    通用线性规划求解器

    参数:
        c: 目标函数系数列表
        A_ub: 不等式约束系数矩阵 (<=)
        b_ub: 不等式约束右端项
        A_eq: 等式约束系数矩阵 (==)
        b_eq: 等式约束右端项
        bounds: 变量边界列表，如 [(0, None), (0, 10)]
        maximize: True求最大值，False求最小值

    返回:
        result: scipy 求解结果对象
    """
    if maximize:
        c = [-x for x in c]

    result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                     bounds=bounds, method='highs')

    if result.success:
        if maximize:
            result.fun = -result.fun
        return result
    else:
        print(f"求解失败: {result.message}")
        return None


# 使用示例
if __name__ == "__main__":
    # 示例1：基本用法（上面的生产计划问题）
    print("\n" + "=" * 50)
    print("示例：运输问题")
    print("=" * 50)

    # 运输问题：3个产地，4个销地
    # 产量
    supply = [10, 20, 30]
    # 销量
    demand = [15, 15, 15, 15]
    # 单位运费
    cost = [
        [8, 7, 5, 6],
        [4, 3, 6, 5],
        [7, 5, 4, 3]
    ]

    # 构建目标函数（12个变量：x11,x12,x13,x14,x21,...）
    c_transport = []
    for row in cost:
        c_transport.extend(row)

    # 产量约束：每个产地运出量 = 产量
    A_eq_trans = []
    b_eq_trans = []
    for i in range(3):
        row = [0] * 12
        for j in range(4):
            row[i * 4 + j] = 1
        A_eq_trans.append(row)
        b_eq_trans.append(supply[i])

    # 销量约束：每个销地收到量 = 销量
    for j in range(4):
        row = [0] * 12
        for i in range(3):
            row[i * 4 + j] = 1
        A_eq_trans.append(row)
        b_eq_trans.append(demand[j])

    bounds_trans = [(0, None)] * 12

    res = solve_lp(c_transport, A_eq=A_eq_trans, b_eq=b_eq_trans,
                   bounds=bounds_trans, maximize=False)

    if res:
        print(f"最小总运费: {res.fun:.2f}")
        print("运输方案:")
        for i in range(3):
            for j in range(4):
                val = res.x[i * 4 + j]
                if val > 1e-6:
                    print(f"  产地{i+1} → 销地{j+1}: {val:.2f}")
