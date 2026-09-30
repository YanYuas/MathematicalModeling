"""
多目标规划 Python 代码模板
方法：
1. 加权求和法（最简单）
2. 理想点法（TOPSIS思想）
3. 分层序列法
4. Pareto前沿（NSGA-II）
"""

import numpy as np
from scipy.optimize import minimize

# ============================================================
# 例题：多目标规划
# 目标1：min f1 = x1^2 + x2^2  （距离原点最近）
# 目标2：max f2 = x1 + 2*x2    （收益最大）
# 约束：x1 + x2 <= 5, x1 >= 0, x2 >= 0
# ============================================================

def f1(x):
    return x[0]**2 + x[1]**2

def f2(x):
    return -(x[0] + 2*x[1])  # 取负转为最小化

constraints = [{'type': 'ineq', 'fun': lambda x: 5 - x[0] - x[1]}]
bounds = [(0, None), (0, None)]

# ============================================================
# 方法1：加权求和法
# ============================================================
print("=" * 50)
print("方法1：加权求和法")
print("=" * 50)

weights_list = [(0.2, 0.8), (0.5, 0.5), (0.8, 0.2)]

for w1, w2 in weights_list:
    def combined_obj(x, w1=w1, w2=w2):
        return w1 * f1(x) + w2 * f2(x)

    result = minimize(combined_obj, [1, 1], method='SLSQP',
                      constraints=constraints, bounds=bounds)
    print(f"权重({w1},{w2}): x=({result.x[0]:.3f},{result.x[1]:.3f}), "
          f"f1={f1(result.x):.3f}, f2={-f2(result.x):.3f}")

# ============================================================
# 方法2：理想点法
# ============================================================
print("\n" + "=" * 50)
print("方法2：理想点法")
print("=" * 50)

# 求每个目标的最优值（理想点）
res1 = minimize(f1, [1, 1], method='SLSQP', constraints=constraints, bounds=bounds)
res2 = minimize(f2, [1, 1], method='SLSQP', constraints=constraints, bounds=bounds)

f1_ideal = res1.fun      # f1的最小值
f2_ideal = res2.fun      # f2的最小值（已经是负的）

print(f"理想点: f1*={f1_ideal:.4f}, f2*={f2_ideal:.4f}")

# 最小化到理想点的距离
def distance_to_ideal(x):
    return np.sqrt((f1(x) - f1_ideal)**2 + (f2(x) - f2_ideal)**2)

result_ideal = minimize(distance_to_ideal, [1, 1], method='SLSQP',
                        constraints=constraints, bounds=bounds)

print(f"最优解: x=({result_ideal.x[0]:.3f},{result_ideal.x[1]:.3f})")
print(f"目标值: f1={f1(result_ideal.x):.3f}, f2={-f2(result_ideal.x):.3f}")

# ============================================================
# 方法3：Pareto前沿（用加权法生成多个点）
# ============================================================
print("\n" + "=" * 50)
print("方法3：Pareto前沿")
print("=" * 50)

pareto_points = []
for w in np.linspace(0, 1, 20):
    def obj(x, w=w):
        return w * f1(x) + (1-w) * f2(x)
    res = minimize(obj, [1, 1], method='SLSQP', constraints=constraints, bounds=bounds)
    if res.success:
        pareto_points.append((f1(res.x), -f2(res.x)))

print("Pareto前沿点 (f1, f2):")
for p in pareto_points[::4]:  # 每隔4个打印一个
    print(f"  ({p[0]:.3f}, {p[1]:.3f})")

# ============================================================
# 方法选择指南
# ============================================================
"""
多目标规划方法选择：
1. 加权求和法：最简单，需要确定权重，适合决策者有明确偏好
2. 理想点法：不需要权重，结果折中，适合无明确偏好
3. 分层序列法：按重要性排序依次优化，适合目标有明确优先级
4. NSGA-II：生成Pareto前沿，适合需要展示所有折中方案
5. 目标规划：设定目标值，最小化偏离，适合有期望目标值
"""
