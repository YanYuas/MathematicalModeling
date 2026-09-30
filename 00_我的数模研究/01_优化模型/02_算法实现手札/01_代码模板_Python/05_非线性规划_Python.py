"""
非线性规划 Python 代码模板
使用 scipy.optimize.minimize 求解

适用场景：
- 目标函数或约束条件是非线性的
- 二次规划、几何规划等
"""

import numpy as np
from scipy.optimize import minimize

# ============================================================
# 例题：非线性规划
# min  f(x) = x1^2 + x2^2 - 4*x1 - 6*x2 + 10
# s.t. x1 + x2 <= 6
#      x1 >= 0, x2 >= 0
# ============================================================

# 目标函数
def objective(x):
    x1, x2 = x
    return x1**2 + x2**2 - 4*x1 - 6*x2 + 10

# 梯度（可选，提高求解速度）
def gradient(x):
    x1, x2 = x
    return np.array([2*x1 - 4, 2*x2 - 6])

# 约束条件
# 不等式约束：x1 + x2 - 6 <= 0
constraints = [
    {'type': 'ineq', 'fun': lambda x: 6 - x[0] - x[1]}  # >= 0 的形式
]

# 变量边界
bounds = [(0, None), (0, None)]

# 初始值
x0 = [1, 1]

# 求解（SLSQP方法适合带约束的非线性规划）
result = minimize(objective, x0, method='SLSQP', jac=gradient,
                  constraints=constraints, bounds=bounds)

print("=" * 50)
print("非线性规划求解结果")
print("=" * 50)
print(f"最优解: x1 = {result.x[0]:.4f}, x2 = {result.x[1]:.4f}")
print(f"最优值: {result.fun:.4f}")
print(f"求解状态: {result.message}")
print(f"迭代次数: {result.nit}")

# ============================================================
# 例题2：带非线性约束的优化
# min  f(x) = -x1*x2*x3
# s.t. x1 + 2*x2 + 2*x3 <= 72
#      x1, x2, x3 >= 0
# ============================================================

print("\n" + "=" * 50)
print("带非线性约束的优化")
print("=" * 50)

def objective2(x):
    return -x[0] * x[1] * x[2]

def constraint2(x):
    return 72 - x[0] - 2*x[1] - 2*x[2]

constraints2 = [{'type': 'ineq', 'fun': constraint2}]
bounds2 = [(0, None), (0, None), (0, None)]
x0_2 = [10, 10, 10]

result2 = minimize(objective2, x0_2, method='SLSQP',
                   constraints=constraints2, bounds=bounds2)

print(f"最优解: x1 = {result2.x[0]:.4f}, x2 = {result2.x[1]:.4f}, x3 = {result2.x[2]:.4f}")
print(f"最大体积: {-result2.fun:.4f}")

# ============================================================
# 通用函数封装
# ============================================================

def solve_nlp(obj_func, x0, constraints=None, bounds=None, method='SLSQP', jac=None):
    """
    通用非线性规划求解器

    参数:
        obj_func: 目标函数
        x0: 初始值
        constraints: 约束条件列表
        bounds: 变量边界
        method: 求解方法（SLSQP, L-BFGS-B, BFGS, Nelder-Mead等）
        jac: 梯度函数（可选）

    返回:
        result: scipy 求解结果对象
    """
    result = minimize(obj_func, x0, method=method, jac=jac,
                      constraints=constraints, bounds=bounds)
    return result


# 方法选择指南：
# - 带约束的非线性规划：SLSQP
# - 无约束或仅边界约束：L-BFGS-B（需要梯度）或 Nelder-Mead（无需梯度）
# - 全局优化：basinhopping, differential_evolution, shgo
