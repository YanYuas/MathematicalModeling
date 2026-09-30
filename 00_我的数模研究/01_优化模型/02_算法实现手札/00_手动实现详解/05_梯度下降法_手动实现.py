# -*- coding: utf-8 -*-
"""
非线性规划 · 梯度下降法手动实现
================================
六层钻研法 · 第4层：手动实现

实现内容：
1. 固定步长梯度下降
2. Armijo非精确线搜索梯度下降
3. 动量法（Momentum）
4. Nesterov加速梯度（NAG）

测试函数：
- 二次函数 f(x) = x^T A x（条件数影响收敛速度）
- Rosenbrock函数 f(x,y) = (1-x)² + 100(y-x²)²（经典测试函数，香蕉形山谷）
"""

import numpy as np
import time


# ============================================================
# 第一部分：测试函数
# ============================================================
def quadratic(x, A):
    """二次函数 f(x) = ½ x^T A x"""
    return 0.5 * x @ A @ x

def quadratic_grad(x, A):
    """二次函数梯度 ∇f(x) = A x"""
    return A @ x

def rosenbrock(x):
    """
    Rosenbrock函数（香蕉函数）
    f(x,y) = (1-x)² + 100(y-x²)²
    全局最优在 (1,1)，f=0
    经典测试函数：山谷弯曲，梯度下降容易走之字形
    """
    return (1 - x[0])**2 + 100 * (x[1] - x[0]**2)**2

def rosenbrock_grad(x):
    """Rosenbrock函数梯度"""
    dx = -2 * (1 - x[0]) - 400 * x[0] * (x[1] - x[0]**2)
    dy = 200 * (x[1] - x[0]**2)
    return np.array([dx, dy])


# ============================================================
# 第二部分：Armijo线搜索
# ============================================================
def armijo_line_search(f, grad, x, d, alpha_init=1.0, beta=0.5, c=1e-4):
    """
    Armijo非精确线搜索
    
    找满足 f(x + αd) ≤ f(x) + c·α·∇f(x)^T d 的最大α
    
    参数：
        f: 目标函数
        grad: 当前点梯度
        x: 当前点
        d: 搜索方向
        alpha_init: 初始步长
        beta: 步长缩减因子（每次乘beta）
        c: Armijo常数（通常1e-4到1e-1）
    
    返回：
        alpha: 满足Armijo条件的步长
    """
    alpha = alpha_init
    f_x = f(x)
    grad_dot_d = grad @ d  # ∇f(x)^T d（应该是负数，因为d是下降方向）
    
    # 不断缩小步长，直到满足Armijo条件
    while f(x + alpha * d) > f_x + c * alpha * grad_dot_d:
        alpha *= beta
        if alpha < 1e-10:  # 步长太小，停止
            break
    
    return alpha


# ============================================================
# 第三部分：梯度下降法（固定步长）
# ============================================================
def gradient_descent_fixed(f, grad, x0, lr=0.01, max_iter=10000, tol=1e-6):
    """
    固定步长梯度下降法
    
    参数：
        f: 目标函数
        grad: 梯度函数
        x0: 初始点
        lr: 学习率（固定步长）
        max_iter: 最大迭代次数
        tol: 收敛容差（梯度范数小于tol时停止）
    
    返回：
        dict: {x, f_val, iterations, history, converged}
    """
    x = x0.copy()
    history = [x.copy()]  # 记录迭代轨迹
    
    for k in range(max_iter):
        g = grad(x)  # 计算梯度
        
        # 收敛判断：梯度范数足够小
        if np.linalg.norm(g) < tol:
            return {'x': x, 'f_val': f(x), 'iterations': k, 
                    'history': np.array(history), 'converged': True}
        
        # 更新：x = x - lr * grad
        x = x - lr * g
        history.append(x.copy())
    
    return {'x': x, 'f_val': f(x), 'iterations': max_iter, 
            'history': np.array(history), 'converged': False}


# ============================================================
# 第四部分：梯度下降法（Armijo线搜索）
# ============================================================
def gradient_descent_armijo(f, grad, x0, max_iter=10000, tol=1e-6):
    """
    带Armijo线搜索的梯度下降法
    
    每一步自动选择合适的步长，比固定步长更稳定。
    """
    x = x0.copy()
    history = [x.copy()]
    
    for k in range(max_iter):
        g = grad(x)
        
        if np.linalg.norm(g) < tol:
            return {'x': x, 'f_val': f(x), 'iterations': k,
                    'history': np.array(history), 'converged': True}
        
        # 搜索方向：负梯度
        d = -g
        
        # Armijo线搜索找步长
        alpha = armijo_line_search(f, g, x, d)
        
        # 更新
        x = x + alpha * d
        history.append(x.copy())
    
    return {'x': x, 'f_val': f(x), 'iterations': max_iter,
            'history': np.array(history), 'converged': False}


# ============================================================
# 第五部分：动量法（Momentum）
# ============================================================
def momentum_method(f, grad, x0, lr=0.01, momentum=0.9, max_iter=10000, tol=1e-6):
    """
    动量法（Momentum）
    
    核心思想：累积历史梯度，像小球从山坡滚下，在峡谷中减少震荡。
    
    更新公式：
        v_{k+1} = momentum * v_k + lr * ∇f(x_k)
        x_{k+1} = x_k - v_{k+1}
    
    参数：
        momentum: 动量系数（通常0.9）
    """
    x = x0.copy()
    v = np.zeros_like(x)  # 速度（累积梯度）
    history = [x.copy()]
    
    for k in range(max_iter):
        g = grad(x)
        
        if np.linalg.norm(g) < tol:
            return {'x': x, 'f_val': f(x), 'iterations': k,
                    'history': np.array(history), 'converged': True}
        
        # 更新速度
        v = momentum * v + lr * g
        # 更新位置
        x = x - v
        history.append(x.copy())
    
    return {'x': x, 'f_val': f(x), 'iterations': max_iter,
            'history': np.array(history), 'converged': False}


# ============================================================
# 第六部分：Nesterov加速梯度（NAG）
# ============================================================
def nesterov_accelerated(f, grad, x0, lr=0.01, momentum=0.9, max_iter=10000, tol=1e-6):
    """
    Nesterov加速梯度（NAG）
    
    改进动量法：先看一眼"未来位置"的梯度，再决定怎么加速。
    
    更新公式：
        v_{k+1} = momentum * v_k + lr * ∇f(x_k - momentum * v_k)
        x_{k+1} = x_k - v_{k+1}
    
    比动量法收敛更快，理论上有O(1/k²)的收敛速率。
    """
    x = x0.copy()
    v = np.zeros_like(x)
    history = [x.copy()]
    
    for k in range(max_iter):
        # 先计算"未来位置"的梯度
        lookahead_x = x - momentum * v
        g = grad(lookahead_x)
        
        if np.linalg.norm(g) < tol:
            return {'x': x, 'f_val': f(x), 'iterations': k,
                    'history': np.array(history), 'converged': True}
        
        # 更新速度和位置
        v = momentum * v + lr * g
        x = x - v
        history.append(x.copy())
    
    return {'x': x, 'f_val': f(x), 'iterations': max_iter,
            'history': np.array(history), 'converged': False}


# ============================================================
# 第七部分：测试用例
# ============================================================
def test_quadratic():
    """
    测试1：二次函数（不同条件数）
    
    f(x) = ½ x^T A x，最优解x*=0，f*=0
    
    条件数 = λ_max(A) / λ_min(A)
    条件数越大，梯度下降越慢（之字形）
    """
    print("=" * 60)
    print("测试1：二次函数（条件数对收敛的影响）")
    print("=" * 60)
    
    # 构造不同条件数的矩阵
    for cond in [1, 10, 100, 1000]:
        # 对角矩阵，特征值1和cond
        A = np.array([[1, 0], [0, cond]])
        
        f = lambda x: quadratic(x, A)
        g = lambda x: quadratic_grad(x, A)
        
        x0 = np.array([1.0, 1.0])
        
        # 固定步长梯度下降（步长=2/(λmax+λmin)是最优固定步长）
        lr = 2.0 / (1 + cond)
        result = gradient_descent_fixed(f, g, x0, lr=lr, max_iter=50000, tol=1e-6)
        
        print(f"\n条件数={cond:5d}, 最优步长={lr:.6f}")
        print(f"  固定步长GD：迭代{result['iterations']:6d}次, "
              f"f={result['f_val']:.2e}, 收敛={result['converged']}")
        
        # Armijo线搜索
        result2 = gradient_descent_armijo(f, g, x0, max_iter=50000, tol=1e-6)
        print(f"  Armijo GD：  迭代{result2['iterations']:6d}次, "
              f"f={result2['f_val']:.2e}, 收敛={result2['converged']}")
    
    print("\n💡 结论：条件数越大，梯度下降越慢。条件数=1000时需要上万次迭代！")


def test_rosenbrock():
    """
    测试2：Rosenbrock函数（香蕉函数）
    
    这是梯度下降的"噩梦"：山谷弯曲，梯度方向几乎垂直于最优方向，
    导致梯度下降走之字形，收敛极慢。
    """
    print("\n" + "=" * 60)
    print("测试2：Rosenbrock函数（香蕉函数）")
    print("=" * 60)
    print("f(x,y) = (1-x)² + 100(y-x²)²，最优解(1,1)，f*=0")
    
    x0 = np.array([-1.0, 1.0])  # 起点
    
    methods = [
        ('固定步长GD (lr=0.001)', lambda: gradient_descent_fixed(
            rosenbrock, rosenbrock_grad, x0, lr=0.001, max_iter=50000)),
        ('固定步长GD (lr=0.002)', lambda: gradient_descent_fixed(
            rosenbrock, rosenbrock_grad, x0, lr=0.002, max_iter=50000)),
        ('Armijo GD', lambda: gradient_descent_armijo(
            rosenbrock, rosenbrock_grad, x0, max_iter=50000)),
        ('动量法 (m=0.9)', lambda: momentum_method(
            rosenbrock, rosenbrock_grad, x0, lr=0.001, momentum=0.9, max_iter=50000)),
        ('NAG (m=0.9)', lambda: nesterov_accelerated(
            rosenbrock, rosenbrock_grad, x0, lr=0.001, momentum=0.9, max_iter=50000)),
    ]
    
    for name, method in methods:
        start = time.time()
        result = method()
        elapsed = time.time() - start
        print(f"\n{name}:")
        print(f"  迭代{result['iterations']:6d}次, "
              f"f={result['f_val']:.2e}, "
              f"x=({result['x'][0]:.6f}, {result['x'][1]:.6f}), "
              f"收敛={result['converged']}, 时间={elapsed:.3f}s")
    
    print("\n💡 结论：Rosenbrock函数对梯度下降非常不友好。")
    print("  动量法和NAG比普通GD快很多，但仍需上千次迭代。")
    print("  这种函数需要牛顿法或共轭梯度法才能快速收敛。")


def test_momentum_effect():
    """
    测试3：动量系数的影响
    """
    print("\n" + "=" * 60)
    print("测试3：动量系数对收敛的影响")
    print("=" * 60)
    
    # 条件数=100的二次函数
    A = np.array([[1, 0], [0, 100]])
    f = lambda x: quadratic(x, A)
    g = lambda x: quadratic_grad(x, A)
    x0 = np.array([1.0, 1.0])
    
    for m in [0, 0.5, 0.9, 0.95, 0.99]:
        result = momentum_method(f, g, x0, lr=0.005, momentum=m, max_iter=50000)
        print(f"  动量={m:.2f}: 迭代{result['iterations']:6d}次, "
              f"f={result['f_val']:.2e}, 收敛={result['converged']}")
    
    print("\n💡 结论：动量越大，收敛越快，但太大会震荡。0.9是常用的好选择。")


if __name__ == '__main__':
    test_quadratic()
    test_rosenbrock()
    test_momentum_effect()
    print("\n" + "=" * 60)
    print("全部测试完成！")
    print("=" * 60)
