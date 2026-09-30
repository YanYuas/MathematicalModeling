"""
对偶单纯形法 手动实现
======================

对偶单纯形法 vs 原始单纯形法：
- 原始单纯形法：保持原可行（b>=0），逐步追求对偶可行（检验数>=0）
- 对偶单纯形法：保持对偶可行（检验数>=0），逐步追求原可行（b>=0）

什么时候用对偶单纯形法？
1. 初始解对偶可行但原不可行（如增加约束后）
2. 灵敏度分析：改变右端项b，或增加新约束
3. 某些问题天然对偶可行（如目标函数系数全为正的最小化问题）

核心思想：
- 从一个"对偶可行"的基解出发（检验数都>=0，但b可能有负数）
- 每次选一个b<0的基变量出基
- 用比值测试选进基变量，保持对偶可行性
- 直到所有b>=0，此时原可行+对偶可行=最优
"""

import numpy as np


def dual_simplex(A, b, c, initial_basis=None, max_iter=1000, verbose=True):
    """
    对偶单纯形法求解

    前提：初始基解是对偶可行的（所有检验数 >= 0），但可能原不可行（b可能有负）

    参数:
        A: 约束系数矩阵 (m x n)
        b: 右端项 (m,)，可以有负数
        c: 目标函数系数 (n,)
        initial_basis: 初始基变量索引
        max_iter: 最大迭代次数
        verbose: 是否打印详情

    返回:
        x, z, status
    """
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)
    m, n = A.shape

    if initial_basis is None:
        initial_basis = list(range(n - m, n))

    basis = initial_basis.copy()

    # 构造单纯形表
    tableau = np.zeros((m + 1, n + 1))
    tableau[:m, :n] = A
    tableau[:m, -1] = b

    # 计算检验数（假设初始对偶可行）
    c_B = c[basis]
    tableau[-1, :n] = c - c_B @ A
    tableau[-1, -1] = -c_B @ b

    if verbose:
        print("=" * 60)
        print("对偶单纯形法开始")
        print(f"初始基: {['x'+str(b) for b in basis]}")
        print(f"初始检验数: {np.round(tableau[-1, :n], 4)}")
        print(f"初始右端项: {np.round(tableau[:m, -1], 4)}")
        print("=" * 60)

    for iteration in range(1, max_iter + 1):

        # --------------------------------------------------------
        # 步骤1：检查原可行性
        # --------------------------------------------------------
        # 标注：对偶单纯形法保持对偶可行（检验数>=0），追求原可行（b>=0）
        # 如果所有b >= 0，达到最优
        rhs = tableau[:m, -1]
        negative_rows = [i for i in range(m) if rhs[i] < -1e-10]

        if len(negative_rows) == 0:
            if verbose:
                print(f"\n所有右端项 >= 0，原可行+对偶可行 = 最优！")
            break

        # --------------------------------------------------------
        # 步骤2：选择出基变量
        # --------------------------------------------------------
        # 标注：选b最负的那一行对应的基变量出基
        # （也可以用Bland规则选下标最小的）
        leaving_row = negative_rows[0]
        for i in negative_rows:
            if rhs[i] < rhs[leaving_row]:
                leaving_row = i

        leaving_var = basis[leaving_row]

        if verbose:
            print(f"\n第{iteration}次迭代:")
            print(f"  出基变量: x{leaving_var}（第{leaving_row}行，b={rhs[leaving_row]:.4f}）")

        # --------------------------------------------------------
        # 步骤3：比值测试，选择进基变量
        # --------------------------------------------------------
        # 标注：对偶单纯形法的比值测试和原始单纯形法相反！
        # 原始单纯形法：theta = min{b_i / a_ik | a_ik > 0}（看正的系数）
        # 对偶单纯形法：theta = min{|r_j / a_lj| | a_lj < 0}（看负的系数）
        #
        # 为什么？因为要保持检验数>=0（对偶可行）。
        # 出基行是第l行，进基变量是x_j，主元是a_lj。
        # 旋转后，新检验数 r'_k = r_k - (r_j / a_lj) * a_lk
        # 要保持 r'_k >= 0，需要选择合适的j。
        # 对于a_lj < 0的列（因为出基行b<0，必须选负系数才能让b变正），
        # 比值 |r_j / a_lj| 最小的列能保证所有检验数仍>=0。

        pivot_row = tableau[leaving_row, :n]
        reduced_costs = tableau[-1, :n]

        valid_cols = []
        ratios = []
        for j in range(n):
            if pivot_row[j] < -1e-10:  # 只看负系数
                ratio = abs(reduced_costs[j] / pivot_row[j])
                valid_cols.append(j)
                ratios.append(ratio)
                if verbose:
                    print(f"  x{j}: |r_j/a_lj| = |{reduced_costs[j]:.4f}/{pivot_row[j]:.4f}| = {ratio:.4f}")

        if len(valid_cols) == 0:
            # 出基行所有系数 >= 0，但b<0，说明问题不可行
            if verbose:
                print(f"  出基行所有系数 >= 0，但b<0，原问题不可行！")
            return None, None, 'infeasible'

        # 选比值最小的列进基
        min_ratio_idx = np.argmin(ratios)
        entering = valid_cols[min_ratio_idx]

        if verbose:
            print(f"  进基变量: x{entering}（比值={ratios[min_ratio_idx]:.4f}）")

        # --------------------------------------------------------
        # 步骤4：主元旋转（和原始单纯形法一样）
        # --------------------------------------------------------
        pivot_value = tableau[leaving_row, entering]
        tableau[leaving_row, :] /= pivot_value
        for i in range(tableau.shape[0]):
            if i != leaving_row:
                factor = tableau[i, entering]
                tableau[i, :] -= factor * tableau[leaving_row, :]

        basis[leaving_row] = entering

        if verbose:
            print(f"  旋转后右端项: {np.round(tableau[:m, -1], 4)}")
            print(f"  旋转后检验数: {np.round(tableau[-1, :n], 4)}")

    else:
        print(f"警告：超过最大迭代次数 {max_iter}")

    # 提取解
    x = np.zeros(n)
    for i in range(m):
        x[basis[i]] = tableau[i, -1]
    z = -tableau[-1, -1]

    if verbose:
        print(f"\n最优解: x = {np.round(x, 4)}")
        print(f"最优值: z = {z:.4f}")

    return x, z, 'optimal'


# ================================================================
# 应用场景演示：灵敏度分析——增加约束
# ================================================================
#
# 场景：已经用原始单纯形法求出了最优解，现在增加一个新约束。
# 新约束可能使当前最优解变得不可行。
# 这时不需要从头求解，只需要：
# 1. 把新约束加入表中（加松弛变量）
# 2. 此时检验数仍然>=0（对偶可行），但b可能变负（原不可行）
# 3. 用对偶单纯形法继续求解
#
# 这比重新用两阶段法快得多！
# ================================================================


def demo_sensitivity_analysis():
    """
    演示：先求原问题最优，再增加约束，用对偶单纯形法继续

    原问题：
        min -3x1 - 5x2
        s.t. x1 + 2x2 <= 8
             2x1 + x2 <= 10
             x1, x2 >= 0

    最优解：x1=4, x2=2, z=-22

    增加约束：x1 + x2 <= 5（新约束）
    此时原最优解 x1+x2=6 > 5，不可行了
    用对偶单纯形法快速求解
    """
    print("\n" + "#" * 60)
    print("# 演示：灵敏度分析——增加约束后用对偶单纯形法")
    print("#" * 60)

    # 原问题的最优表（从原始单纯形法得到）
    # 变量：x0=x1, x1=x2, x2=s1, x3=s2
    # 最优基：x0, x1（即x1, x2）
    # 最优表：
    #       x0    x1    x2     x3    RHS
    # x1   1.00  0.00 -0.33   0.67   4.00
    # x2   0.00  1.00  0.67  -0.33   2.00
    # r    0.00  0.00  2.33   0.33  22.00

    print("""
原问题最优解：x1=4, x2=2, 最大利润=22

现在增加新约束：x1 + x2 <= 5
原最优解 x1+x2 = 6 > 5，不再可行！

传统方法：重新用两阶段法求解（麻烦）
对偶单纯形法：在最优表基础上加约束，继续迭代（快速）
    """)

    # 构造增加约束后的表
    # 新约束：x1 + x2 + s3 = 5，加松弛变量s3（x4）
    # 变量变为：x0=x1, x1=x2, x2=s1, x3=s2, x4=s3
    # 基变为：x0, x1, x4（新约束的松弛变量）

    # 原最优表（增加一列0给新松弛变量）
    A_opt = np.array([
        [1.00, 0.00, -1/3,  2/3, 0],   # x1行
        [0.00, 1.00,  2/3, -1/3, 0],   # x2行
    ])
    b_opt = np.array([4.0, 2.0])

    # 新约束行：x1 + x2 + s3 = 5
    # 但需要用基变量表示（消去x1, x2）
    # x1 = 4 + (1/3)s1 - (2/3)s2
    # x2 = 2 - (2/3)s1 + (1/3)s2
    # 代入：x1 + x2 + s3 = 6 - (1/3)s1 - (1/3)s2 + s3 = 5
    # 即：-(1/3)s1 - (1/3)s2 + s3 = -1
    new_row = np.array([0, 0, -1/3, -1/3, 1])
    new_rhs = -1.0

    # 完整的表
    A = np.vstack([A_opt, new_row])
    b = np.append(b_opt, new_rhs)
    c = np.array([-3, -5, 0, 0, 0])  # 目标函数

    print("增加约束后的初始表（对偶可行，原不可行）：")
    print(f"  基变量: x1, x2, s3")
    print(f"  右端项: {b}（s3=-1 < 0，原不可行）")
    print(f"  检验数: [0, 0, 2.33, 0.33, 0]（全部>=0，对偶可行）")
    print()

    # 用对偶单纯形法求解
    x, z, status = dual_simplex(A, b, c, initial_basis=[0, 1, 4], verbose=True)

    print(f"""
结果：
    x1 = {x[0]:.2f}, x2 = {x[1]:.2f}
    s1 = {x[2]:.2f}, s2 = {x[3]:.2f}, s3 = {x[4]:.2f}
    最大利润 = {-z:.2f}

验证新约束：x1 + x2 = {x[0]+x[1]:.2f} <= 5 ✓
    """)


# ================================================================
# 应用场景演示：改变右端项
# ================================================================


def demo_rhs_change():
    """
    演示：改变右端项b，用对偶单纯形法

    原问题最优基不变，但b变化后可能出现负数
    此时检验数仍>=0（对偶可行），用对偶单纯形法
    """
    print("\n" + "#" * 60)
    print("# 演示：改变右端项后用对偶单纯形法")
    print("#" * 60)

    print("""
原问题：原料甲限量8，原料乙限量10
最优解：x1=4, x2=2

现在原料甲限量变为5（减少了3）
影子价格告诉我们利润会减少，但基可能不变
如果b变负，用对偶单纯形法
    """)

    # 最优表（基：x1, x2）
    # x1 = 4 + (1/3)s1 - (2/3)s2
    # x2 = 2 - (2/3)s1 + (1/3)s2
    # 原料甲 = 8 - s1，变为5意味着 s1 = 3
    # 新的 b_bar = B^{-1} b_new
    # B^{-1} = [[-1/3, 2/3], [2/3, -1/3]]
    # b_new = [5, 10]
    # b_bar = B^{-1} b_new = [(-5+20)/3, (10-10)/3] = [5, 0]
    # 这个例子b没变负，所以不需要对偶单纯形法

    # 换一个b变化更大的例子：原料甲变为2
    # b_bar = B^{-1} [2, 10] = [(-2+20)/3, (4-10)/3] = [6, -2]
    # x2 = -2 < 0，原不可行了！

    print("更极端：原料甲限量变为2")
    print("此时 x2 = -2 < 0，原不可行，但检验数仍>=0")
    print()

    A = np.array([
        [1.00, 0.00, -1/3,  2/3],
        [0.00, 1.00,  2/3, -1/3],
    ])
    b = np.array([6.0, -2.0])  # x1=6, x2=-2
    c = np.array([-3, -5, 0, 0])

    x, z, status = dual_simplex(A, b, c, initial_basis=[0, 1], verbose=True)

    print(f"""
结果：
    x1 = {x[0]:.2f}, x2 = {x[1]:.2f}
    最大利润 = {-z:.2f}
    """)


if __name__ == "__main__":
    demo_sensitivity_analysis()
    demo_rhs_change()

    print("""
============================================================
对偶单纯形法学习要点：
============================================================
1. 保持对偶可行（检验数>=0），追求原可行（b>=0）
2. 出基选择：b最负的行
3. 进基选择：min{|r_j / a_lj| | a_lj < 0}（注意是负系数！）
4. 主元旋转：和原始单纯形法完全一样
5. 最大优势：灵敏度分析（加约束、改b）时不需要从头求解
6. 前提：初始解必须对偶可行（检验数全>=0）

和原始单纯形法的对比：
                    原始单纯形法        对偶单纯形法
初始条件            原可行             对偶可行
追求目标            对偶可行           原可行
出基选择            比值测试(正系数)   b最负
进基选择            检验数最负         比值测试(负系数)
适用场景            一般问题           灵敏度分析
============================================================
    """)
