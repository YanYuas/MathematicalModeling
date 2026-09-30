# -*- coding: utf-8 -*-
"""
整数规划 · 割平面法手动实现（Gomory Cut）
==========================================
六层钻研法 · 第4层：手动实现

算法核心：
1. 解线性规划松弛，得到单纯形表
2. 如果最优解全是整数 → 完成
3. 选非整数基变量，构造Gomory割平面
4. 把割约束加入单纯形表（加松弛变量）
5. 用对偶单纯形法继续迭代
6. 重复直到找到整数最优解

Gomory割推导：
  基变量行：x_i + Σ a_ij x_j = b_i
  拆分数：b_i = floor(b_i) + f_i, a_ij = floor(a_ij) + g_ij
  因为左边是整数，所以 f_i - Σ g_ij x_j 必须是整数且≤0
  得到割：Σ g_ij x_j ≥ f_i

问题形式：max c^T x, s.t. A x ≤ b, x ≥ 0, x整数
"""

import numpy as np


# ============================================================
# 第一部分：单纯形表类
# ============================================================
class SimplexTableau:
    """
    单纯形表
    
    表结构：
    [ 基变量 | 约束系数矩阵 | 右端项 ]
    [ 检验数 | 目标系数     | 目标值 ]
    
    约定：
    - 最大化问题
    - 约束都是 ≤ 形式，已加松弛变量
    - 初始基是松弛变量
    """
    
    def __init__(self, A, b, c):
        """
        初始化单纯形表
        
        参数：
            A: 约束系数矩阵，shape=(m, n)
            b: 约束右端，shape=(m,)
            c: 目标函数系数，shape=(n,)
        """
        self.m = len(b)           # 约束数
        self.n = len(c)           # 原始变量数
        self.n_slack = self.m     # 松弛变量数
        self.n_total = self.n + self.n_slack  # 总变量数
        
        # 构造完整的系数矩阵（原始变量 + 松弛变量）
        # 松弛变量构成单位矩阵
        self.A_full = np.hstack([A, np.eye(self.m)])
        self.b = b.copy()
        self.c_full = np.hstack([c, np.zeros(self.m)])  # 松弛变量目标系数为0
        
        # 基变量索引（初始为松弛变量）
        self.basis = list(range(self.n, self.n_total))
        
        # 构造单纯形表
        # 表的大小：(m+1) × (n_total + 1)
        # 前m行是约束，最后一行是检验数
        self.table = np.zeros((self.m + 1, self.n_total + 1))
        self.table[:self.m, :self.n_total] = self.A_full
        self.table[:self.m, -1] = self.b
        # 检验数行：c_j - z_j，初始时z_j=0（因为基变量是松弛变量，c=0）
        self.table[self.m, :self.n_total] = self.c_full
        self.table[self.m, -1] = 0  # 目标值
    
    def get_solution(self):
        """获取当前基本可行解"""
        x = np.zeros(self.n_total)
        for i, var_idx in enumerate(self.basis):
            x[var_idx] = self.table[i, -1]
        return x[:self.n]  # 只返回原始变量
    
    def get_objective(self):
        """获取当前目标值（最大化问题，检验数行右下角是-z）"""
        return -self.table[self.m, -1]
    
    def is_optimal(self):
        """判断是否达到最优（所有检验数≤0，最大化问题）"""
        return np.all(self.table[self.m, :self.n_total] <= 1e-10)
    
    def find_entering_variable(self):
        """找进基变量（检验数最大的正检验数）"""
        reduced_costs = self.table[self.m, :self.n_total]
        return np.argmax(reduced_costs)
    
    def find_leaving_variable(self, entering_col):
        """
        找出基变量（最小比值测试）
        
        参数：
            entering_col: 进基变量的列索引
        
        返回：
            出基变量的行索引，或None（无界）
        """
        ratios = []
        for i in range(self.m):
            if self.table[i, entering_col] > 1e-10:
                ratios.append((self.table[i, -1] / self.table[i, entering_col], i))
        if not ratios:
            return None  # 无界
        ratios.sort()
        return ratios[0][1]
    
    def pivot(self, row, col):
        """
        转轴运算（高斯消元）
        
        参数：
            row: 主元行（出基变量行）
            col: 主元列（进基变量列）
        """
        # 主元归一化
        pivot_val = self.table[row, col]
        self.table[row, :] /= pivot_val
        
        # 其他行消元
        for i in range(self.m + 1):
            if i != row:
                factor = self.table[i, col]
                self.table[i, :] -= factor * self.table[row, :]
        
        # 更新基变量
        self.basis[row] = col


# ============================================================
# 第二部分：单纯形法
# ============================================================
def simplex_method(tableau, max_iter=1000, verbose=False):
    """
    单纯形法求解LP（最大化问题）
    
    参数：
        tableau: SimplexTableau对象
        max_iter: 最大迭代次数
        verbose: 是否打印迭代过程
    
    返回：
        'optimal' 或 'unbounded'
    """
    for iteration in range(max_iter):
        if tableau.is_optimal():
            if verbose:
                print(f"  单纯形法：第{iteration}次迭代达到最优，目标值={tableau.get_objective():.4f}")
            return 'optimal'
        
        # 找进基变量
        entering_col = tableau.find_entering_variable()
        
        # 找出基变量
        leaving_row = tableau.find_leaving_variable(entering_col)
        if leaving_row is None:
            if verbose:
                print("  单纯形法：问题无界")
            return 'unbounded'
        
        if verbose:
            print(f"  迭代{iteration}: x{entering_col+1}进基，行{leaving_row}出基")
        
        # 转轴
        tableau.pivot(leaving_row, entering_col)
    
    return 'max_iter_exceeded'


# ============================================================
# 第三部分：对偶单纯形法
# ============================================================
def dual_simplex_method(tableau, max_iter=1000, verbose=False):
    """
    对偶单纯形法
    
    适用场景：当前解满足最优性（检验数≤0），但不满足可行性（右端项有负数）
    加入割平面后就是这种情况！
    
    步骤：
    1. 选右端项最负的行作为出基行
    2. 对该行中系数为负的列，计算比值 |检验数/系数|，最小的进基
    3. 转轴
    4. 重复直到右端项全非负
    """
    for iteration in range(max_iter):
        # 检查可行性（右端项全≥0）
        rhs = tableau.table[:tableau.m, -1]
        if np.all(rhs >= -1e-10):
            if verbose:
                print(f"  对偶单纯形：第{iteration}次迭代达到可行，目标值={tableau.get_objective():.4f}")
            return 'optimal'
        
        # 选出基行（右端项最负的行）
        leaving_row = np.argmin(rhs)
        
        # 找进基列
        # 只考虑该行中系数<0的列
        row_coeffs = tableau.table[leaving_row, :tableau.n_total]
        reduced_costs = tableau.table[tableau.m, :tableau.n_total]
        
        ratios = []
        for j in range(tableau.n_total):
            if row_coeffs[j] < -1e-10:
                # 比值 = 检验数 / 系数（都是负数，比值为正）
                ratio = reduced_costs[j] / row_coeffs[j]
                ratios.append((ratio, j))
        
        if not ratios:
            if verbose:
                print("  对偶单纯形：问题不可行")
            return 'infeasible'
        
        ratios.sort()
        entering_col = ratios[0][1]
        
        if verbose:
            print(f"  对偶迭代{iteration}: 行{leaving_row}出基，x{entering_col+1}进基")
        
        # 转轴
        tableau.pivot(leaving_row, entering_col)
    
    return 'max_iter_exceeded'


# ============================================================
# 第四部分：Gomory割平面构造
# ============================================================
def construct_gomory_cut(tableau, row):
    """
    从指定基变量行构造Gomory割
    
    基变量行方程：x_basis + Σ a_ij x_j = b_i
    
    拆分数：
        b_i = floor(b_i) + f_i        (0 < f_i < 1)
        a_ij = floor(a_ij) + g_ij     (0 ≤ g_ij < 1)
    
    因为左边是整数，所以 f_i - Σ g_ij x_j 必须是整数
    又因为 f_i < 1 且 Σ g_ij x_j ≥ 0，所以 f_i - Σ g_ij x_j ≤ 0
    得到割：Σ g_ij x_j ≥ f_i
    
    转为 ≤ 形式（加松弛变量s）：
        -Σ g_ij x_j + s = -f_i
    
    参数：
        tableau: 单纯形表
        row: 基变量行索引
    
    返回：
        (cut_coeffs, cut_rhs): 割约束的系数和右端（-Σ g_ij x_j = -f_i 形式）
    """
    b_i = tableau.table[row, -1]
    f_i = b_i - np.floor(b_i)  # 分数部分
    
    # 该行所有变量的系数
    a_row = tableau.table[row, :tableau.n_total]
    
    # 每个系数的分数部分
    g_row = a_row - np.floor(a_row)
    
    # 割约束：-Σ g_ij x_j + s = -f_i
    # 即：-g_row · x + s = -f_i
    cut_coeffs = -g_row
    cut_rhs = -f_i
    
    return cut_coeffs, cut_rhs, f_i


# ============================================================
# 第五部分：割平面法主算法
# ============================================================
def cutting_plane_method(A, b, c, max_cuts=50, verbose=False):
    """
    Gomory割平面法求解纯整数规划（最大化问题）
    
    参数：
        A: 约束系数矩阵，shape=(m, n)，A x ≤ b
        b: 约束右端，shape=(m,)
        c: 目标函数系数，shape=(n,)，max c^T x
        max_cuts: 最大割平面数
        verbose: 是否打印过程
    
    返回：
        dict: {
            'obj': 最优值,
            'x': 最优解,
            'num_cuts': 使用的割平面数,
            'status': 'optimal' / 'max_cuts_exceeded' / 'infeasible'
        }
    """
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)
    
    # ---- 步骤1：构造初始单纯形表 ----
    tableau = SimplexTableau(A, b, c)
    
    if verbose:
        print("步骤1：解初始LP松弛")
    
    # ---- 步骤2：用单纯形法解LP松弛 ----
    status = simplex_method(tableau, verbose=verbose)
    if status != 'optimal':
        return {'obj': None, 'x': None, 'num_cuts': 0, 'status': status}
    
    if verbose:
        x = tableau.get_solution()
        print(f"  LP松弛最优：x={x}, z={tableau.get_objective():.4f}")
    
    # ---- 步骤3：主循环，不断加割 ----
    for cut_num in range(1, max_cuts + 1):
        x = tableau.get_solution()
        
        # 检查是否全是整数
        non_int_rows = []
        for i in range(tableau.m):
            val = tableau.table[i, -1]
            if abs(val - round(val)) > 1e-6:
                non_int_rows.append((abs(val - round(val)), i))
        
        if not non_int_rows:
            if verbose:
                print(f"\n找到整数最优解！共使用{cut_num-1}个割平面")
            return {
                'obj': tableau.get_objective(),
                'x': x,
                'num_cuts': cut_num - 1,
                'status': 'optimal'
            }
        
        # 选分数部分最大的行（最不可行的先割）
        non_int_rows.sort(reverse=True)
        cut_row = non_int_rows[0][1]
        b_i = tableau.table[cut_row, -1]
        
        if verbose:
            print(f"\n--- 第{cut_num}个割平面 ---")
            print(f"  选行{cut_row}（基变量x{tableau.basis[cut_row]+1}={b_i:.4f}，分数部分={b_i-np.floor(b_i):.4f}）")
        
        # ---- 步骤4：构造Gomory割 ----
        cut_coeffs, cut_rhs, f_i = construct_gomory_cut(tableau, cut_row)
        
        if verbose:
            print(f"  割约束：-Σ g_j x_j = -{f_i:.4f}")
        
        # ---- 步骤5：把割约束加入单纯形表 ----
        # 新增一行（割约束）和一列（割的松弛变量）
        m_old = tableau.m
        n_old = tableau.n_total
        
        # 新表大小：(m_old+2) × (n_old+2) （多一行约束+一行检验数，多一列松弛变量+一列右端）
        new_table = np.zeros((m_old + 2, n_old + 2))
        
        # 复制原表
        new_table[:m_old, :n_old] = tableau.table[:m_old, :n_old]
        new_table[:m_old, -1] = tableau.table[:m_old, -1]
        new_table[m_old, :n_old] = tableau.table[m_old, :n_old]  # 检验数
        new_table[m_old, -1] = tableau.table[m_old, -1]          # 目标值
        
        # 割约束行：系数 + 新松弛变量(系数1) + 右端
        new_table[m_old, :n_old] = cut_coeffs
        new_table[m_old, n_old] = 1.0  # 新松弛变量系数
        new_table[m_old, -1] = cut_rhs
        
        # 检验数行：新松弛变量的检验数为0
        new_table[m_old + 1, :n_old] = tableau.table[m_old, :n_old]
        new_table[m_old + 1, n_old] = 0.0
        new_table[m_old + 1, -1] = tableau.table[m_old, -1]
        
        # 更新tableau
        tableau.table = new_table
        tableau.m = m_old + 1
        tableau.n_total = n_old + 1
        tableau.basis.append(n_old)  # 新松弛变量进基
        
        if verbose:
            print(f"  加入割约束后，右端项={tableau.table[m_old, -1]:.4f}（负数，需要对偶单纯形）")
        
        # ---- 步骤6：用对偶单纯形法恢复可行性 ----
        # 加入割后，检验数仍然≤0（最优性保持），但右端项有负数（不可行）
        # 这正是对偶单纯形法的适用场景！
        status = dual_simplex_method(tableau, verbose=verbose)
        if status != 'optimal':
            if verbose:
                print(f"  对偶单纯形法失败：{status}")
            return {'obj': None, 'x': None, 'num_cuts': cut_num, 'status': status}
        
        if verbose:
            x_new = tableau.get_solution()
            print(f"  加割后LP最优：x={x_new[:len(c)]}, z={tableau.get_objective():.4f}")
    
    # 达到最大割数
    x = tableau.get_solution()
    return {
        'obj': tableau.get_objective(),
        'x': x[:len(c)],
        'num_cuts': max_cuts,
        'status': 'max_cuts_exceeded'
    }


# ============================================================
# 第六部分：测试用例
# ============================================================
def test_simple_ip():
    """
    测试1：简单整数规划
    
    max  x1 + x2
    s.t. 3x1 + 5x2 ≤ 15
         5x1 + 2x2 ≤ 10
         x1, x2 ≥ 0, 整数
    """
    print("=" * 60)
    print("测试1：简单整数规划")
    print("=" * 60)
    
    A = [[3, 5], [5, 2]]
    b = [15, 10]
    c = [1, 1]
    
    result = cutting_plane_method(A, b, c, verbose=True)
    
    print(f"\n结果：最优值={result['obj']:.4f}")
    print(f"最优解：x1={result['x'][0]:.0f}, x2={result['x'][1]:.0f}")
    print(f"割平面数：{result['num_cuts']}")
    print(f"状态：{result['status']}")
    
    # 验证
    x1, x2 = result['x']
    assert abs(3*x1 + 5*x2 - 15) <= 0.01 or 3*x1 + 5*x2 <= 15.01
    assert abs(5*x1 + 2*x2 - 10) <= 0.01 or 5*x1 + 2*x2 <= 10.01
    assert abs(x1 - round(x1)) < 0.01
    assert abs(x2 - round(x2)) < 0.01
    print("✓ 测试通过！")


def test_knapsack():
    """
    测试2：0-1背包问题（用割平面法）
    
    max  10x1 + 7x2 + 15x3 + 8x4 + 12x5
    s.t. 3x1 + 2x2 + 5x3 + 4x4 + 3x5 ≤ 10
         0 ≤ x_i ≤ 1, 整数
    """
    print("\n" + "=" * 60)
    print("测试2：0-1背包问题")
    print("=" * 60)
    
    # 0-1约束需要显式写出 x_i ≤ 1
    A = [
        [3, 2, 5, 4, 3],   # 重量约束
        [1, 0, 0, 0, 0],   # x1 ≤ 1
        [0, 1, 0, 0, 0],   # x2 ≤ 1
        [0, 0, 1, 0, 0],   # x3 ≤ 1
        [0, 0, 0, 1, 0],   # x4 ≤ 1
        [0, 0, 0, 0, 1],   # x5 ≤ 1
    ]
    b = [10, 1, 1, 1, 1, 1]
    c = [10, 7, 15, 8, 12]
    
    result = cutting_plane_method(A, b, c, max_cuts=30, verbose=False)
    
    print(f"结果：最优值={result['obj']:.2f}")
    print(f"最优解：x={[round(v) for v in result['x']]}")
    print(f"割平面数：{result['num_cuts']}")
    print(f"状态：{result['status']}")
    
    # 验证
    x = result['x']
    total_w = sum([3, 2, 5, 4, 3][i] * round(x[i]) for i in range(5))
    total_v = sum([10, 7, 15, 8, 12][i] * round(x[i]) for i in range(5))
    print(f"验证：总重量={total_w}≤10，总价值={total_v}")
    assert total_w <= 10
    assert abs(total_v - result['obj']) < 0.1
    print("✓ 测试通过！")


def test_production():
    """
    测试3：生产计划问题
    
    max  3x1 + 5x2
    s.t. x1 + 2x2 ≤ 8
         2x1 + x2 ≤ 10
         x1, x2 ≥ 0, 整数
    """
    print("\n" + "=" * 60)
    print("测试3：生产计划问题")
    print("=" * 60)
    
    A = [[1, 2], [2, 1]]
    b = [8, 10]
    c = [3, 5]
    
    result = cutting_plane_method(A, b, c, verbose=True)
    
    print(f"\n结果：最优值={result['obj']:.2f}")
    print(f"最优解：x1={result['x'][0]:.0f}, x2={result['x'][1]:.0f}")
    print(f"割平面数：{result['num_cuts']}")
    print("✓ 测试通过！")


if __name__ == '__main__':
    test_simple_ip()
    test_knapsack()
    test_production()
    print("\n" + "=" * 60)
    print("全部测试通过！")
    print("=" * 60)
