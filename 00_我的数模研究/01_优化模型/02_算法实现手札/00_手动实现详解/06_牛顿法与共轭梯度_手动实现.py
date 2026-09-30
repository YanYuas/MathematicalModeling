# -*- coding: utf-8 -*-
"""
非线性规划 · 牛顿法与共轭梯度法手动实现
========================================
六层钻研法 · 第4层：手动实现

实现内容：
1. 纯牛顿法（步长=1，局部二次收敛）
2. 带线搜索的牛顿法（全局收敛）
3. 修正牛顿法（Hessian不正定时加正则项）
4. BFGS拟牛顿法（不计算Hessian，用近似矩阵）
5. 非线性共轭梯度法（FR和PR公式）

测试函数：
- 二次函数（牛顿法1次收敛）
- Rosenbrock函数（牛顿法几十次收敛，对比梯度下降的上万次）
"""

import numpy as np
import time


# ============================================================
# 第一部分：测试函数
# ============================================================
def rosenbrock(x):
    """Rosenbrock函数 f(x,y) = (1-x)² + 100(y-x²)²，最优(1,1), f=0"""
    return (1 - x[0])**2 + 100 * (x[1] - x[0]**2)**2

def rosenbrock_grad(x):
    """Rosenbrock梯度"""
    dx = -2 * (1 - x[0]) - 400 * x[0] * (x[1] - x[0]**2)
    dy = 200 * (x[1] - x[0]**2)
    return np.array([dx, dy])

def rosenbrock_hessian(x):
    """Rosenbrock的Hessian矩阵"""
    dxx = 2 - 400 * (x[1] - 3*x[0]**2)
    dxy = -400 * x[0]
    dyy = 200
    return np.array([[dxx, dxy], [dxy, dyy]])

def quadratic(x, A):
    """二次函数 f(x) = ½ x^T A x"""
    return 0.5 * x @ A @ x

def quadratic_grad(x, A):
    """二次函数梯度"""
    return A @ x

def quadratic_hessian(x, A):
    """二次函数Hessian（常数矩阵A）"""
    return A


# ============================================================
# 第二部分：Armijo线搜索（复用梯度下降中的）
# ============================================================
def armijo_line_search(f, grad, x, d, alpha_init=1.0, beta=0.5, c=1e-4):
    """Armijo非精确线搜索，找满足充分下降的最大步长"""
    alpha = alpha_init
    f_x = f(x)
    grad_dot_d = grad @ d
    while f(x + alpha * d) > f_x + c * alpha * grad_dot_d:
        alpha *= beta
        if alpha < 1e-10:
            break
    return alpha


# ============================================================
# 第三部分：纯牛顿法
# ============================================================
def newton_method(f, grad, hessian, x0, max_iter=1000, tol=1e-6):
    """
    纯牛顿法（步长=1）
    
    迭代公式：x_{k+1} = x_k - H_k^{-1} g_k
    其中H_k=∇²f(x_k), g_k=∇f(x_k)
    
    优点：在最优点附近二次收敛
    缺点：可能不收敛（全局收敛性不保证），Hessian可能不正定
    """
    x = x0.copy()
    history = [x.copy()]
    
    for k in range(max_iter):
        g = grad(x)
        
        if np.linalg.norm(g) < tol:
            return {'x': x, 'f_val': f(x), 'iterations': k,
                    'history': np.array(history), 'converged': True}
        
        H = hessian(x)
        
        # 解线性方程组 H d = -g（比求逆更稳定）
        try:
            d = np.linalg.solve(H, -g)
        except np.linalg.LinAlgError:
            # Hessian奇异，用梯度方向
            d = -g
        
        # 纯牛顿法：步长=1
        x = x + d
        history.append(x.copy())
    
    return {'x': x, 'f_val': f(x), 'iterations': max_iter,
            'history': np.array(history), 'converged': False}


# ============================================================
# 第四部分：带线搜索的牛顿法（全局收敛）
# ============================================================
def newton_method_linesearch(f, grad, hessian, x0, max_iter=1000, tol=1e-6):
    """
    带Armijo线搜索的牛顿法
    
    方向：d = -H^{-1} g（牛顿方向）
    步长：Armijo线搜索自动选择
    
    这样既有牛顿法的快速收敛，又有全局收敛性。
    """
    x = x0.copy()
    history = [x.copy()]
    
    for k in range(max_iter):
        g = grad(x)
        
        if np.linalg.norm(g) < tol:
            return {'x': x, 'f_val': f(x), 'iterations': k,
                    'history': np.array(history), 'converged': True}
        
        H = hessian(x)
        
        # 解牛顿方向
        try:
            d = np.linalg.solve(H, -g)
            # 检查是否是下降方向（d^T g < 0）
            if d @ g > 0:
                d = -g  # 不是下降方向，用梯度方向
        except np.linalg.LinAlgError:
            d = -g
        
        # Armijo线搜索
        alpha = armijo_line_search(f, g, x, d)
        
        x = x + alpha * d
        history.append(x.copy())
    
    return {'x': x, 'f_val': f(x), 'iterations': max_iter,
            'history': np.array(history), 'converged': False}


# ============================================================
# 第五部分：修正牛顿法（Hessian不正定时加正则项）
# ============================================================
def modified_newton(f, grad, hessian, x0, max_iter=1000, tol=1e-6):
    """
    修正牛顿法
    
    当Hessian不正定时，加正则项使其正定：
    H_modified = H + λI，其中λ足够大使H_modified正定
    
    这样牛顿方向始终是下降方向。
    """
    x = x0.copy()
    history = [x.copy()]
    
    for k in range(max_iter):
        g = grad(x)
        
        if np.linalg.norm(g) < tol:
            return {'x': x, 'f_val': f(x), 'iterations': k,
                    'history': np.array(history), 'converged': True}
        
        H = hessian(x)
        
        # 检查Hessian是否正定（尝试Cholesky分解）
        lambda_reg = 0.0
        while True:
            try:
                H_mod = H + lambda_reg * np.eye(len(x))
                np.linalg.cholesky(H_mod)  # 正定才能分解
                d = np.linalg.solve(H_mod, -g)
                break
            except np.linalg.LinAlgError:
                lambda_reg = max(lambda_reg * 10, 1e-6)
                if lambda_reg > 1e10:
                    d = -g
                    break
        
        alpha = armijo_line_search(f, g, x, d)
        x = x + alpha * d
        history.append(x.copy())
    
    return {'x': x, 'f_val': f(x), 'iterations': max_iter,
            'history': np.array(history), 'converged': False}


# ============================================================
# 第六部分：BFGS拟牛顿法
# ============================================================
def bfgs_method(f, grad, x0, max_iter=1000, tol=1e-6):
    """
    BFGS拟牛顿法
    
    不计算Hessian，而是用近似矩阵B_k逼近∇²f(x_k)。
    
    更新公式（秩2更新）：
        s_k = x_{k+1} - x_k
        y_k = g_{k+1} - g_k
        B_{k+1} = B_k - (B_k s_k s_k^T B_k)/(s_k^T B_k s_k) + (y_k y_k^T)/(y_k^T s_k)
    
    初始B_0通常取单位矩阵（第一步就是梯度下降）。
    """
    n = len(x0)
    x = x0.copy()
    B = np.eye(n)  # 初始Hessian近似=单位矩阵
    history = [x.copy()]
    
    g = grad(x)
    
    for k in range(max_iter):
        if np.linalg.norm(g) < tol:
            return {'x': x, 'f_val': f(x), 'iterations': k,
                    'history': np.array(history), 'converged': True}
        
        # 解BFGS方向：B d = -g
        try:
            d = np.linalg.solve(B, -g)
        except np.linalg.LinAlgError:
            d = -g
        
        # 线搜索
        alpha = armijo_line_search(f, g, x, d)
        
        # 更新
        x_new = x + alpha * d
        g_new = grad(x_new)
        
        s = x_new - x
        y = g_new - g
        
        # BFGS更新（确保分母不为0）
        sy = s @ y
        if abs(sy) > 1e-10:
            Bs = B @ s
            B = B - np.outer(Bs, Bs) / (s @ Bs) + np.outer(y, y) / sy
        
        x = x_new
        g = g_new
        history.append(x.copy())
    
    return {'x': x, 'f_val': f(x), 'iterations': max_iter,
            'history': np.array(history), 'converged': False}


# ============================================================
# 第七部分：非线性共轭梯度法
# ============================================================
def nonlinear_cg(f, grad, x0, formula='PR', max_iter=10000, tol=1e-6):
    """
    非线性共轭梯度法
    
    搜索方向：
        d_0 = -g_0
        d_k = -g_k + β_k d_{k-1}
    
    β的计算公式：
        FR: β_k = ||g_k||² / ||g_{k-1}||²
        PR: β_k = g_k^T (g_k - g_{k-1}) / ||g_{k-1}||²
    
    每步用Armijo线搜索找步长。
    """
    x = x0.copy()
    g = grad(x)
    d = -g  # 初始方向=负梯度
    history = [x.copy()]
    
    for k in range(max_iter):
        if np.linalg.norm(g) < tol:
            return {'x': x, 'f_val': f(x), 'iterations': k,
                    'history': np.array(history), 'converged': True}
        
        # 线搜索
        alpha = armijo_line_search(f, g, x, d)
        
        # 更新
        x_new = x + alpha * d
        g_new = grad(x_new)
        
        # 计算β
        if formula == 'FR':
            beta = (g_new @ g_new) / (g @ g + 1e-20)
        elif formula == 'PR':
            beta = (g_new @ (g_new - g)) / (g @ g + 1e-20)
            beta = max(beta, 0)  # PR的重启技巧
        else:
            beta = 0
        
        # 新方向
        d = -g_new + beta * d
        
        # 定期重启（每n次迭代重启为梯度方向）
        if k % len(x) == 0:
            d = -g_new
        
        x = x_new
        g = g_new
        history.append(x.copy())
    
    return {'x': x, 'f_val': f(x), 'iterations': max_iter,
            'history': np.array(history), 'converged': False}


# ============================================================
# 第八部分：测试用例
# ============================================================
def test_quadratic():
    """
    测试1：二次函数（牛顿法应该1次收敛）
    """
    print("=" * 60)
    print("测试1：二次函数（牛顿法1次收敛）")
    print("=" * 60)
    
    # 条件数=100的二次函数
    A = np.array([[1, 0], [0, 100]])
    f = lambda x: quadratic(x, A)
    g = lambda x: quadratic_grad(x, A)
    h = lambda x: quadratic_hessian(x, A)
    
    x0 = np.array([1.0, 1.0])
    
    # 纯牛顿法
    result = newton_method(f, g, h, x0)
    print(f"纯牛顿法：迭代{result['iterations']}次, f={result['f_val']:.2e}, "
          f"x={result['x']}, 收敛={result['converged']}")
    
    # BFGS
    result = bfgs_method(f, g, x0)
    print(f"BFGS：    迭代{result['iterations']}次, f={result['f_val']:.2e}, "
          f"x={result['x']}, 收敛={result['converged']}")
    
    # 共轭梯度（FR）
    result = nonlinear_cg(f, g, x0, formula='FR')
    print(f"CG-FR：   迭代{result['iterations']}次, f={result['f_val']:.2e}, "
          f"x={result['x']}, 收敛={result['converged']}")
    
    print("\n💡 二次函数是牛顿法的甜点：Hessian是常数，1次就到最优点！")


def test_rosenbrock():
    """
    测试2：Rosenbrock函数（对比各算法收敛速度）
    """
    print("\n" + "=" * 60)
    print("测试2：Rosenbrock函数（各算法对比）")
    print("=" * 60)
    print("f(x,y) = (1-x)² + 100(y-x²)²，最优(1,1), f=0")
    
    x0 = np.array([-1.2, 1.0])  # 经典起点
    
    methods = [
        ('纯牛顿法', lambda: newton_method(rosenbrock, rosenbrock_grad, rosenbrock_hessian, x0)),
        ('牛顿+线搜索', lambda: newton_method_linesearch(rosenbrock, rosenbrock_grad, rosenbrock_hessian, x0)),
        ('修正牛顿法', lambda: modified_newton(rosenbrock, rosenbrock_grad, rosenbrock_hessian, x0)),
        ('BFGS拟牛顿', lambda: bfgs_method(rosenbrock, rosenbrock_grad, x0)),
        ('CG-FR', lambda: nonlinear_cg(rosenbrock, rosenbrock_grad, x0, formula='FR')),
        ('CG-PR', lambda: nonlinear_cg(rosenbrock, rosenbrock_grad, x0, formula='PR')),
    ]
    
    for name, method in methods:
        start = time.time()
        result = method()
        elapsed = time.time() - start
        print(f"\n{name:12s}: 迭代{result['iterations']:5d}次, "
              f"f={result['f_val']:.2e}, "
              f"x=({result['x'][0]:.8f}, {result['x'][1]:.8f}), "
              f"收敛={result['converged']}, 时间={elapsed:.4f}s")
    
    print("\n💡 对比梯度下降的32035次迭代，牛顿法和BFGS只需几十次！")
    print("  这就是二阶信息的威力。")


def test_newton_divergence():
    """
    测试3：纯牛顿法可能不收敛
    """
    print("\n" + "=" * 60)
    print("测试3：纯牛顿法的不收敛案例")
    print("=" * 60)
    
    # 一维函数 f(x) = arctan(x)，从x=2出发
    # 牛顿法可能震荡或发散
    def f1d(x):
        return np.arctan(x[0])**2
    
    def g1d(x):
        return np.array([2 * np.arctan(x[0]) / (1 + x[0]**2)])
    
    def h1d(x):
        val = 2 / (1 + x[0]**2)
        return np.array([[val - 4 * x[0] * np.arctan(x[0]) / (1 + x[0]**2)**2]])
    
    x0 = np.array([2.0])
    
    result = newton_method(f1d, g1d, h1d, x0, max_iter=20)
    print(f"纯牛顿法（arctan²，起点x=2）：")
    print(f"  迭代{result['iterations']}次, f={result['f_val']:.6f}, x={result['x'][0]:.6f}")
    print(f"  收敛={result['converged']}")
    
    if not result['converged']:
        print("  → 纯牛顿法可能发散或震荡，这就是为什么需要线搜索！")
    
    result2 = newton_method_linesearch(f1d, g1d, h1d, x0, max_iter=100)
    print(f"\n带线搜索的牛顿法：")
    print(f"  迭代{result2['iterations']}次, f={result2['f_val']:.6f}, x={result2['x'][0]:.6f}")
    print(f"  收敛={result2['converged']}")


if __name__ == '__main__':
    test_quadratic()
    test_rosenbrock()
    test_newton_divergence()
    print("\n" + "=" * 60)
    print("全部测试完成！")
    print("=" * 60)
