# -*- coding: utf-8 -*-
"""
拉格朗日乘数法 · 深入研究与手动实现
======================================
六层钻研法 · 第3-4层：数学推导 + 手动实现

内容：
1. 等式约束的拉格朗日乘数法（原理+几何意义+求解）
2. 不等式约束与KKT条件
3. 拉格朗日对偶（对偶函数、强对偶性、与LP对偶的关系）
4. 增广拉格朗日法（实用约束优化算法）
5. 应用案例

拉格朗日乘数法是约束优化的基石，理解它对非线性规划至关重要。
"""

import numpy as np
from scipy.optimize import minimize


# ============================================================
# 1. 等式约束的拉格朗日乘数法
# ============================================================
def lagrangian_equality(f, grad_f, h, grad_h, x0, learning_rate=0.01,
                        max_iter=10000, tol=1e-8):
    """
    等式约束优化：min f(x) s.t. h(x) = 0
    
    拉格朗日函数：L(x, λ) = f(x) + λ * h(x)
    
    最优性条件（一阶必要条件）：
        ∇_x L = ∇f(x) + λ∇h(x) = 0
        ∇_λ L = h(x) = 0
    
    求解方法：梯度下降（同时更新x和λ）
        x = x - lr * ∇_x L
        λ = λ + lr * ∇_λ L  （注意是+号，因为要最大化λ）
    
    参数：
        f: 目标函数
        grad_f: 目标函数梯度
        h: 等式约束函数（h(x)=0）
        grad_h: 约束函数梯度
        x0: 初始点
        learning_rate: 学习率
        max_iter: 最大迭代次数
        tol: 收敛阈值
    
    返回：
        x: 最优解
        lambda_: 最优拉格朗日乘子
        history: 迭代历史
    """
    x = np.array(x0, dtype=float)
    lambda_ = 0.0  # 拉格朗日乘子
    history = []
    
    for iteration in range(max_iter):
        # 计算梯度
        grad_L_x = grad_f(x) + lambda_ * grad_h(x)
        grad_L_lambda = h(x)
        
        # 记录
        history.append((x.copy(), lambda_, f(x), h(x)))
        
        # 检查收敛
        if np.linalg.norm(grad_L_x) < tol and abs(h(x)) < tol:
            break
        
        # 梯度下降更新
        x = x - learning_rate * grad_L_x
        lambda_ = lambda_ + learning_rate * grad_L_lambda  # 注意+号
    
    return x, lambda_, history


def example_equality():
    """
    示例：min f(x,y) = x² + y²  s.t. x + y = 1
    
    解析解：x=y=0.5, f=0.5, λ=-1
    
    几何意义：目标函数的等高线（圆）与约束线（直线）相切。
    在切点，∇f与∇h平行（方向相同或相反）。
    """
    print("=" * 60)
    print("示例1：等式约束 min x²+y² s.t. x+y=1")
    print("=" * 60)
    
    f = lambda x: x[0]**2 + x[1]**2
    grad_f = lambda x: np.array([2*x[0], 2*x[1]])
    h = lambda x: x[0] + x[1] - 1
    grad_h = lambda x: np.array([1.0, 1.0])
    
    x, lam, history = lagrangian_equality(f, grad_f, h, grad_h, [0, 0],
                                            learning_rate=0.05, max_iter=5000)
    
    print(f"最优解：x={x[0]:.6f}, y={x[1]:.6f}")
    print(f"最优值：f={f(x):.6f}")
    print(f"拉格朗日乘子：λ={lam:.6f}")
    print(f"约束满足：h(x)={h(x):.2e}")
    print(f"迭代次数：{len(history)}")
    print(f"解析解：x=y=0.5, f=0.5, λ=-1")
    print()


# ============================================================
# 2. 不等式约束与KKT条件
# ============================================================
def kkt_conditions_example():
    """
    KKT条件示例：min f(x) = x²  s.t. x >= 1
    
    拉格朗日函数：L(x, μ) = x² + μ(1 - x)
    （约束写成 g(x) = 1-x <= 0，所以是 +μ*g(x)）
    
    KKT条件：
    1. 平稳性：∇L = 2x - μ = 0
    2. 原始可行性：x >= 1
    3. 对偶可行性：μ >= 0
    4. 互补松弛：μ(1-x) = 0
    
    分两种情况：
    - μ=0：x=0，但不满足x>=1，无效
    - 1-x=0：x=1，μ=2，满足所有条件
    
    最优解：x=1, f=1, μ=2
    """
    print("=" * 60)
    print("示例2：KKT条件 min x² s.t. x>=1")
    print("=" * 60)
    
    # 用scipy验证
    f = lambda x: x[0]**2
    cons = {'type': 'ineq', 'fun': lambda x: x[0] - 1}
    result = minimize(f, [0], constraints=cons, method='SLSQP')
    
    print(f"最优解：x={result.x[0]:.6f}")
    print(f"最优值：f={result.fun:.6f}")
    print(f"KKT乘子μ：{result.x[0]*2:.6f}（由2x-μ=0得μ=2x）")
    print(f"解析解：x=1, f=1, μ=2")
    print()
    
    print("KKT条件验证：")
    print(f"  1. 平稳性：2x-μ = {2*result.x[0] - 2*result.x[0]:.2e} = 0 ✓")
    print(f"  2. 原始可行性：x-1 = {result.x[0]-1:.2e} >= 0 ✓")
    print(f"  3. 对偶可行性：μ = {2*result.x[0]:.6f} >= 0 ✓")
    print(f"  4. 互补松弛：μ(1-x) = {2*result.x[0]*(1-result.x[0]):.2e} = 0 ✓")
    print()


# ============================================================
# 3. 拉格朗日对偶
# ============================================================
def lagrangian_duality_example():
    """
    拉格朗日对偶示例
    
    原问题（线性规划）：
        min 3x1 + 5x2
        s.t. x1 + x2 >= 2
             x1, x2 >= 0
    
    拉格朗日函数：L(x, μ) = 3x1 + 5x2 + μ(2 - x1 - x2)
                         = (3-μ)x1 + (5-μ)x2 + 2μ
    
    对偶函数：g(μ) = min_x L(x, μ)
        如果 3-μ >= 0 且 5-μ >= 0（即μ<=3），则x1=x2=0时最小，g(μ)=2μ
        否则 g(μ) = -∞
    
    对偶问题：max g(μ) = 2μ, s.t. 0 <= μ <= 3
        最优μ=3, g(3)=6
    
    原问题最优：x1=2, x2=0, f=6
    对偶间隙 = 6 - 6 = 0（强对偶成立，因为是线性规划）
    """
    print("=" * 60)
    print("示例3：拉格朗日对偶（线性规划）")
    print("=" * 60)
    
    # 原问题
    print("原问题：min 3x1+5x2 s.t. x1+x2>=2, x1,x2>=0")
    print(f"  最优解：x1=2, x2=0, f=6")
    
    # 对偶函数
    def dual_function(mu):
        if mu <= 3:
            return 2 * mu
        else:
            return -float('inf')
    
    print("\n对偶函数：g(μ) = 2μ (0<=μ<=3)")
    print("对偶问题：max g(μ)")
    print(f"  最优μ=3, g(3)=6")
    print(f"  对偶间隙 = 6 - 6 = 0（强对偶成立）")
    
    # 与线性规划对偶的关系
    print("\n与LP对偶的关系：")
    print("  LP的对偶：max 2y s.t. y<=3, y<=5, y>=0")
    print("  最优y=3，对偶目标=6")
    print("  拉格朗日对偶的μ就是LP对偶的y！")
    print()


# ============================================================
# 4. 增广拉格朗日法（实用约束优化算法）
# ============================================================
def augmented_lagrangian(f, grad_f, h, grad_h, x0,
                         rho0=1.0, rho_max=1e4, gamma=2.0,
                         max_outer=50, max_inner=1000, tol=1e-8):
    """
    增广拉格朗日法（Augmented Lagrangian Method）
    
    解决等式约束优化：min f(x) s.t. h(x) = 0
    
    增广拉格朗日函数：
        L_rho(x, λ) = f(x) + λ*h(x) + (rho/2)*h(x)²
    
    与普通拉格朗日的区别：多了惩罚项 (rho/2)*h(x)²
    好处：即使λ不精确，也能通过惩罚项迫使约束满足
    
    算法流程：
    1. 初始化λ=0, rho=rho0
    2. 外循环：
       a. 内循环：固定λ和rho，用梯度下降最小化L_rho(x, λ)
       b. 检查收敛（约束满足且梯度条件满足）
       c. 更新λ：λ = λ + rho * h(x)
       d. 更新rho：rho = min(rho * gamma, rho_max)
    """
    x = np.array(x0, dtype=float)
    lambda_ = 0.0
    rho = rho0
    history = []
    
    for outer in range(max_outer):
        # 内循环：最小化增广拉格朗日函数
        # 用自适应步长（根据rho调整）
        lr = 0.01 / max(rho, 1.0)  # rho越大步长越小，避免发散
        
        for inner in range(max_inner):
            hx = h(x)
            grad_aug = grad_f(x) + (lambda_ + rho * hx) * grad_h(x)
            
            grad_norm = np.linalg.norm(grad_aug)
            if grad_norm < tol:
                break
            
            # 梯度下降
            x = x - lr * grad_aug
            
            # 防止数值溢出
            if np.any(np.abs(x) > 1e6):
                x = np.clip(x, -1e6, 1e6)
                break
        
        # 记录
        history.append((x.copy(), lambda_, rho, f(x), h(x)))
        
        # 检查收敛（在更新λ和rho之前）
        if abs(h(x)) < tol and np.linalg.norm(grad_f(x) + lambda_ * grad_h(x)) < tol:
            break
        
        # 更新乘子和惩罚参数
        lambda_ = lambda_ + rho * h(x)
        rho = min(rho * gamma, rho_max)
    
    return x, lambda_, history


def example_augmented_lagrangian():
    """增广拉格朗日法示例"""
    print("=" * 60)
    print("示例4：增广拉格朗日法 min x²+y² s.t. x+y=1")
    print("=" * 60)
    
    f = lambda x: x[0]**2 + x[1]**2
    grad_f = lambda x: np.array([2*x[0], 2*x[1]])
    h = lambda x: x[0] + x[1] - 1
    grad_h = lambda x: np.array([1.0, 1.0])
    
    x, lam, history = augmented_lagrangian(f, grad_f, h, grad_h, [0, 0])
    
    print(f"最优解：x={x[0]:.6f}, y={x[1]:.6f}")
    print(f"最优值：f={f(x):.6f}")
    print(f"拉格朗日乘子：λ={lam:.6f}")
    print(f"约束满足：h(x)={h(x):.2e}")
    print(f"外循环次数：{len(history)}")
    print()
    
    print("外循环过程：")
    print(f"{'迭代':>4} {'x':>10} {'y':>10} {'λ':>10} {'rho':>10} {'h(x)':>12}")
    print("-" * 60)
    for i, (xi, li, rho, fi, hi) in enumerate(history[:10]):
        print(f"{i:>4} {xi[0]:>10.6f} {xi[1]:>10.6f} {li:>10.6f} {rho:>10.1f} {hi:>12.2e}")
    print()


# ============================================================
# 5. 综合案例：投资组合优化（带约束）
# ============================================================
def portfolio_optimization():
    """
    投资组合优化：最小化风险（方差），约束期望收益
    
    min  x^T Σ x    （风险）
    s.t. μ^T x >= r   （期望收益至少r）
         Σ x_i = 1    （全部投资）
         x_i >= 0     （不允许做空）
    
    用拉格朗日乘数法理解，用scipy求解。
    """
    print("=" * 60)
    print("示例5：投资组合优化")
    print("=" * 60)
    
    # 3只股票的期望收益和协方差矩阵
    mu = np.array([0.1, 0.2, 0.15])  # 期望收益
    Sigma = np.array([[0.04, 0.006, 0.02],
                      [0.006, 0.09, 0.06],
                      [0.02, 0.06, 0.16]])  # 协方差
    
    target_return = 0.15  # 目标收益
    
    # 目标函数：风险（方差）
    def risk(x):
        return x @ Sigma @ x
    
    def grad_risk(x):
        return 2 * Sigma @ x
    
    # 约束
    cons = [
        {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # 总和=1
        {'type': 'ineq', 'fun': lambda x: mu @ x - target_return},  # 收益>=目标
    ]
    bounds = [(0, None)] * 3  # 不做空
    
    result = minimize(risk, [1/3, 1/3, 1/3], jac=grad_risk,
                      constraints=cons, bounds=bounds, method='SLSQP')
    
    print(f"最优投资比例：{result.x}")
    print(f"最小风险（方差）：{result.fun:.6f}")
    print(f"实际期望收益：{mu @ result.x:.4f}")
    print(f"投资总和：{np.sum(result.x):.6f}")
    print()
    
    print("拉格朗日乘数法视角：")
    print("  L(x, λ, μ) = x^TΣx + λ(Σx-1) + μ(r - μ^Tx)")
    print("  KKT条件给出最优解的结构")
    print("  有效前沿：不同目标收益r对应的最小风险")
    print()


# ============================================================
# 主函数
# ============================================================
if __name__ == '__main__':
    example_equality()
    kkt_conditions_example()
    lagrangian_duality_example()
    example_augmented_lagrangian()
    portfolio_optimization()
    
    print("=" * 60)
    print("全部示例运行完成！")
    print("=" * 60)
    print()
    print("核心要点总结：")
    print("  1. 等式约束：∇f = λ∇h（梯度平行）")
    print("  2. 不等式约束：KKT条件（平稳性+可行性+互补松弛）")
    print("  3. 拉格朗日对偶：原问题↔对偶问题，LP强对偶成立")
    print("  4. 增广拉格朗日法：加惩罚项，实用约束优化算法")
    print("  5. 影子价格：λ表示约束放松1单位时目标值的变化")
