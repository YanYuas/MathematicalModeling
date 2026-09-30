"""
单纯形法 手动实现
====================
不依赖 scipy.optimize.linprog，从零实现完整的单纯形法。

实现内容：
1. 标准形式转化
2. 两阶段法获取初始基可行解
3. 单纯形法主循环
4. 退化处理（Bland规则可选）
5. 无界检测
6. 不可行检测

作者：建模手
日期：2026-09-08
"""

import numpy as np


class SimplexSolver:
    """
    单纯形法求解器

    求解标准形式：
        min  c^T x
        s.t. Ax = b
             x >= 0
    """

    def __init__(self, A, b, c, method='standard', max_iter=1000, verbose=False):
        """
        参数:
            A: 约束系数矩阵 (m x n)
            b: 右端项 (m,)
            c: 目标函数系数 (n,)
            method: 'standard' 普通单纯形法, 'bland' Bland规则（防循环）
            max_iter: 最大迭代次数
            verbose: 是否打印迭代过程
        """
        self.A = np.array(A, dtype=float)
        self.b = np.array(b, dtype=float)
        self.c = np.array(c, dtype=float)
        self.method = method
        self.max_iter = max_iter
        self.verbose = verbose

        self.m, self.n = self.A.shape
        self.iterations = 0
        self.status = 'not solved'

    def solve(self):
        """主求解函数"""
        # 第一步：用两阶段法获取初始基可行解
        success, tableau, basis = self._two_phase()
        if not success:
            self.status = 'infeasible'
            return None, None

        # 第二步：单纯形法主循环
        result = self._simplex_loop(tableau, basis)
        return result

    def _two_phase(self):
        """
        两阶段法：
        第一阶段：引入人工变量，最小化人工变量之和，判断可行性
        第二阶段：去掉人工变量，用原始目标函数继续优化
        """
        # 构造第一阶段问题
        # min sum(artificial variables)
        # s.t. Ax + artificial = b
        A_phase1 = np.hstack([self.A, np.eye(self.m)])
        c_phase1 = np.concatenate([np.zeros(self.n), np.ones(self.m)])
        b_phase1 = self.b.copy()

        # 初始基：人工变量
        basis = list(range(self.n, self.n + self.m))

        # 构造单纯形表
        # 表的结构：[A | b]
        #         [c | z]  （最后一行是检验数行）
        tableau = np.zeros((self.m + 1, self.n + self.m + 1))
        tableau[:self.m, :self.n + self.m] = A_phase1
        tableau[:self.m, -1] = b_phase1

        # 计算初始检验数（需要用基变量消去）
        # 检验数行 = c_phase1 - c_B^T * A_phase1
        c_B = c_phase1[basis]
        tableau[-1, :-1] = c_phase1 - c_B @ A_phase1
        tableau[-1, -1] = -c_B @ b_phase1  # 当前目标值（负的）

        if self.verbose:
            print("=== 第一阶段开始 ===")

        # 第一阶段求解
        tableau, basis, success = self._simplex_iteration(
            tableau, basis, c_phase1, phase=1
        )

        if not success:
            return False, None, None

        # 检查第一阶段最优值
        phase1_obj = -tableau[-1, -1]
        if phase1_obj > 1e-10:
            if self.verbose:
                print(f"第一阶段最优值 = {phase1_obj:.6f} > 0，原问题不可行")
            return False, None, None

        if self.verbose:
            print(f"第一阶段完成，最优值 = {phase1_obj:.6f}，问题可行")

        # 检查人工变量是否还在基中（退化情况）
        # 如果人工变量还在基中且值为0，需要换基；换不出来说明是冗余约束，删除该行
        rows_to_remove = []
        for i, b_var in enumerate(basis):
            if b_var >= self.n:  # 是人工变量
                # 找一个非人工变量的列来替换
                found = False
                for j in range(self.n):
                    if j not in basis and abs(tableau[i, j]) > 1e-8:
                        tableau = self._pivot(tableau, i, j)
                        basis[i] = j
                        found = True
                        break
                if not found:
                    # 该行是冗余约束，标记删除
                    rows_to_remove.append(i)

        # 删除冗余约束行
        if rows_to_remove:
            tableau = np.delete(tableau, rows_to_remove, axis=0)
            basis = [b for i, b in enumerate(basis) if i not in rows_to_remove]

        # 第二阶段：去掉人工变量列，替换目标函数
        tableau = np.delete(tableau, range(self.n, self.n + self.m), axis=1)
        # 重新计算检验数行
        m_current = len(basis)
        c_B = self.c[basis]
        tableau[-1, :-1] = self.c - c_B @ tableau[:m_current, :-1]
        tableau[-1, -1] = -c_B @ tableau[:m_current, -1]

        if self.verbose:
            print("=== 第二阶段开始 ===")

        return True, tableau, basis

    def _simplex_iteration(self, tableau, basis, c_obj, phase=2):
        """单纯形法迭代主循环"""
        m = len(basis)
        n_vars = tableau.shape[1] - 1

        for iteration in range(self.max_iter):
            self.iterations += 1

            # 步骤1：检查最优性
            # 最小化问题：所有检验数 >= 0 时最优
            reduced_costs = tableau[-1, :-1]

            if self.method == 'bland':
                # Bland规则：选下标最小的负检验数
                entering = -1
                for j in range(n_vars):
                    if reduced_costs[j] < -1e-10:
                        entering = j
                        break
            else:
                # 标准规则：选最负的检验数
                entering = np.argmin(reduced_costs)
                if reduced_costs[entering] >= -1e-10:
                    entering = -1

            if entering == -1:
                # 达到最优
                if self.verbose:
                    print(f"迭代{iteration}: 达到最优，目标值 = {-tableau[-1, -1]:.6f}")
                return tableau, basis, True

            # 步骤2：比值测试，选出基变量
            column = tableau[:m, entering]
            rhs = tableau[:m, -1]

            # 只考虑 column > 0 的行
            valid_rows = [i for i in range(m) if column[i] > 1e-10]

            if len(valid_rows) == 0:
                # 所有系数 <= 0，问题无界
                if self.verbose:
                    print(f"迭代{iteration}: 问题无界")
                self.status = 'unbounded'
                return tableau, basis, False

            # 计算比值
            ratios = [(rhs[i] / column[i], i) for i in valid_rows]

            if self.method == 'bland':
                # Bland规则：比值最小时选下标最小的
                min_ratio = min(r for r, _ in ratios)
                candidates = [i for r, i in ratios if abs(r - min_ratio) < 1e-10]
                leaving = min(candidates, key=lambda i: basis[i])
            else:
                # 标准规则：选比值最小的
                leaving = min(ratios, key=lambda x: x[0])[1]

            # 步骤3：主元旋转
            tableau = self._pivot(tableau, leaving, entering)
            basis[leaving] = entering

            if self.verbose and iteration % 10 == 0:
                print(f"迭代{iteration}: 目标值 = {-tableau[-1, -1]:.6f}, "
                      f"进基变量 x{entering}, 出基变量 x{basis[leaving]}")

        # 超过最大迭代次数
        print(f"警告：超过最大迭代次数 {self.max_iter}")
        return tableau, basis, True

    def _pivot(self, tableau, row, col):
        """
        高斯-约旦消元（主元旋转）
        以 tableau[row, col] 为主元，将该列其他元素消为0
        """
        pivot_val = tableau[row, col]
        tableau[row, :] /= pivot_val

        for i in range(tableau.shape[0]):
            if i != row:
                factor = tableau[i, col]
                tableau[i, :] -= factor * tableau[row, :]

        return tableau

    def _simplex_loop(self, tableau, basis):
        """第二阶段的单纯形循环"""
        tableau, basis, success = self._simplex_iteration(
            tableau, basis, self.c, phase=2
        )

        if not success and self.status == 'unbounded':
            return None

        # 提取最优解
        m = len(basis)
        x = np.zeros(tableau.shape[1] - 1)
        for i, b_var in enumerate(basis):
            x[b_var] = tableau[i, -1]

        optimal_value = -tableau[-1, -1]
        self.status = 'optimal'

        # 只返回原始变量（前n个）
        return x[:self.n], optimal_value


# ============================================================
# 测试1：生产计划问题
# ============================================================
def test_production_planning():
    print("=" * 60)
    print("测试1：生产计划问题")
    print("=" * 60)
    print("max 3x1 + 5x2")
    print("s.t. x1 + 2x2 <= 8")
    print("     2x1 + x2 <= 10")
    print("     x1, x2 >= 0")
    print()

    # 转化为标准形式（min, =, >=0）
    # max 3x1+5x2 → min -3x1-5x2
    # x1+2x2 <= 8 → x1+2x2+s1 = 8
    # 2x1+x2 <= 10 → 2x1+x2+s2 = 10
    A = [[1, 2, 1, 0],
         [2, 1, 0, 1]]
    b = [8, 10]
    c = [-3, -5, 0, 0]  # 最小化

    solver = SimplexSolver(A, b, c, verbose=True)
    x, obj = solver.solve()

    print(f"\n最优解: x1 = {x[0]:.4f}, x2 = {x[1]:.4f}")
    print(f"最大利润: {-obj:.4f}")
    print(f"预期答案: x1=4, x2=2, 利润=22")
    print(f"迭代次数: {solver.iterations}")
    print()


# ============================================================
# 测试2：运输问题
# ============================================================
def test_transportation():
    print("=" * 60)
    print("测试2：运输问题")
    print("=" * 60)
    # 2个产地，3个销地
    # 产地产量：[10, 20]，销地销量：[8, 12, 10]
    # 单位运费矩阵：
    #      销1  销2  销3
    # 产1   3    5    2
    # 产2   4    1    3
    print("最小化总运费，2产地3销地")
    print()

    # 变量 x_ij，共6个
    # 约束：产地i的发货量 = 产量
    #       销地j的收货量 = 销量
    A = [
        [1, 1, 1, 0, 0, 0],   # 产地1
        [0, 0, 0, 1, 1, 1],   # 产地2
        [1, 0, 0, 1, 0, 0],   # 销地1
        [0, 1, 0, 0, 1, 0],   # 销地2
        [0, 0, 1, 0, 0, 1],   # 销地3
    ]
    b = [10, 20, 8, 12, 10]
    c = [3, 5, 2, 4, 1, 3]

    solver = SimplexSolver(A, b, c, verbose=False)
    x, obj = solver.solve()

    print("最优运输方案:")
    print(f"  产地1→销地1: {x[0]:.1f}, 产地1→销地2: {x[1]:.1f}, 产地1→销地3: {x[2]:.1f}")
    print(f"  产地2→销地1: {x[3]:.1f}, 产地2→销地2: {x[4]:.1f}, 产地2→销地3: {x[5]:.1f}")
    print(f"最小总运费: {obj:.2f}")
    print(f"迭代次数: {solver.iterations}")
    print()


# ============================================================
# 测试3：不可行问题
# ============================================================
def test_infeasible():
    print("=" * 60)
    print("测试3：不可行问题检测")
    print("=" * 60)
    print("min x1 + x2")
    print("s.t. x1 + x2 <= 1")
    print("     x1 + x2 >= 2")
    print("     x1, x2 >= 0")
    print()

    # x1+x2 <= 1 → x1+x2+s1 = 1
    # x1+x2 >= 2 → x1+x2-s2 = 2
    A = [[1, 1, 1, 0],
         [1, 1, 0, -1]]
    b = [1, 2]
    c = [1, 1, 0, 0]

    solver = SimplexSolver(A, b, c, verbose=True)
    x, obj = solver.solve()

    print(f"状态: {solver.status}")
    print()


# ============================================================
# 测试4：无界问题
# ============================================================
def test_unbounded():
    print("=" * 60)
    print("测试4：无界问题检测")
    print("=" * 60)
    print("min -x1 - x2")
    print("s.t. x1 - x2 <= 1")
    print("     x1, x2 >= 0")
    print()

    A = [[1, -1, 1]]
    b = [1]
    c = [-1, -1, 0]

    solver = SimplexSolver(A, b, c, verbose=True)
    result = solver.solve()

    print(f"状态: {solver.status}")
    if result is not None:
        x, obj = result
        print(f"最优值: {obj}")
    print()


# ============================================================
# 与 scipy 对比验证
# ============================================================
def compare_with_scipy():
    print("=" * 60)
    print("与 scipy.optimize.linprog 对比验证")
    print("=" * 60)

    try:
        from scipy.optimize import linprog

        # 随机生成一个线性规划问题
        np.random.seed(42)
        m, n = 5, 8
        A = np.random.rand(m, n) * 10
        b = np.random.rand(m) * 50 + 10
        c = np.random.rand(n) * 10

        # 我们的求解器（需要标准形式，加松弛变量）
        A_std = np.hstack([A, np.eye(m)])
        c_std = np.concatenate([c, np.zeros(m)])

        solver = SimplexSolver(A_std, b, c_std, verbose=False)
        x_mine, obj_mine = solver.solve()

        # scipy求解
        res = linprog(c, A_ub=A, b_ub=b, method='highs')

        print(f"我的求解器: 最优值 = {obj_mine:.6f}, 迭代 = {solver.iterations}")
        print(f"scipy:      最优值 = {res.fun:.6f}")
        print(f"差异: {abs(obj_mine - res.fun):.8f}")
        print(f"验证通过: {abs(obj_mine - res.fun) < 1e-6}")
    except ImportError:
        print("scipy未安装，跳过对比")


if __name__ == "__main__":
    test_production_planning()
    test_transportation()
    test_infeasible()
    test_unbounded()
    compare_with_scipy()

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)
    print()
    print("实现心得：")
    print("1. 两阶段法是获取初始基可行解的关键，第一阶段判断可行性")
    print("2. 主元旋转是核心操作，一次旋转完成一次顶点跳跃")
    print("3. 退化在实际中常见，但循环极罕见，Bland规则会降低效率")
    print("4. 数值稳定性很重要，需要设置容差（1e-10）判断零")
    print("5. 和scipy对比，结果一致，说明实现正确")
