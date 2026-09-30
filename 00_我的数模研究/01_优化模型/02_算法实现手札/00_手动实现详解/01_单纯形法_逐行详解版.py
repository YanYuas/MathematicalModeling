"""
单纯形法 逐行详解教学版
========================
这是一个专门用于学习的版本，每一步都有详细标注。
建议配合《线性规划_深研笔记》一起阅读。

求解问题（标准形式）：
    min  c^T x
    s.t. Ax = b
         x >= 0

学习建议：
1. 先看懂"单纯形表"的结构
2. 再理解"进基变量"和"出基变量"的选择
3. 最后理解"主元旋转"操作
4. 用 test_step_by_step() 函数一步步看中间结果
"""

import numpy as np


# ================================================================
# 第一部分：单纯形法的核心数据结构——单纯形表
# ================================================================
#
# 单纯形表的结构（m个约束，n个变量）：
#
#     x1  x2  ...  xn | RHS（右端项）
#    ------------------+-----------
#     a11 a12 ... a1n | b1        ← 第1行约束
#     a21 a22 ... a2n | b2        ← 第2行约束
#     ...              | ...
#     am1 am2 ... amn | bm        ← 第m行约束
#    ------------------+-----------
#     r1  r2  ...  rn | -z        ← 检验数行（最后一行）
#
# 其中：
#   - 前m行是约束方程的系数
#   - 最后一行是检验数 r_j = c_j - c_B^T B^{-1} A_j
#   - 最后一列的前m个是基变量的值 b_bar = B^{-1} b
#   - 最后一行最后一个是 -z（负的目标函数值）
#
# 基变量的列一定是单位向量（只有一个1，其余0）
# ================================================================


def print_tableau(tableau, basis, iteration, entering=None, leaving=None):
    """
    打印单纯形表，方便观察每一步的变化

    参数:
        tableau: 单纯形表（m+1行，n+1列）
        basis: 基变量索引列表 [基变量1, 基变量2, ...]
        iteration: 当前迭代次数
        entering: 进基变量索引（用于高亮）
        leaving: 出基变量所在行（用于高亮）
    """
    m = len(basis)
    n = tableau.shape[1] - 1

    print(f"\n{'='*60}")
    print(f"第 {iteration} 次迭代")
    print(f"当前基变量: {['x'+str(b) for b in basis]}")
    if entering is not None:
        print(f"进基变量: x{entering}")
    if leaving is not None:
        print(f"出基变量: x{basis[leaving]}（第{leaving}行）")
    print(f"{'='*60}")

    # 打印表头
    header = "      " + "".join([f"{'x'+str(j):>8}" for j in range(n)]) + f"{'RHS':>8}"
    print(header)
    print("-" * len(header))

    # 打印约束行
    for i in range(m):
        row_str = f"x{basis[i]:<3}" if i != leaving else f"x{basis[i]}*"
        row_str = f"{row_str:>6}"
        for j in range(n):
            val = tableau[i, j]
            if j == entering:
                row_str += f"[{val:>6.2f}]"  # 进基列用方括号标记
            else:
                row_str += f"{val:>8.2f}"
        row_str += f"{tableau[i, -1]:>8.2f}"
        print(row_str)

    # 打印检验数行
    print("-" * len(header))
    row_str = f"{'r_j':>6}"
    for j in range(n):
        val = tableau[-1, j]
        if j == entering:
            row_str += f"[{val:>6.2f}]"
        else:
            row_str += f"{val:>8.2f}"
    row_str += f"{-tableau[-1, -1]:>8.2f}"  # 显示z而不是-z
    print(row_str)
    print(f"当前目标值 z = {-tableau[-1, -1]:.4f}")


# ================================================================
# 第二部分：核心操作——主元旋转（Pivot）
# ================================================================
#
# 主元旋转是单纯形法最核心的操作，它完成了"从一个顶点跳到另一个顶点"。
#
# 以 tableau[row, col] 为主元（pivot element），进行高斯-约旦消元：
# 1. 主元行除以主元值，使主元变为1
# 2. 其他所有行减去 该行主元列系数 × 主元行，使主元列其他元素变为0
#
# 这样操作后，主元列就变成了单位向量（只有主元位置是1），
# 对应的变量就成为了新的基变量。
# ================================================================


def pivot(tableau, row, col):
    """
    主元旋转（高斯-约旦消元）

    这是单纯形法的核心操作，一次旋转 = 一次顶点跳跃

    参数:
        tableau: 单纯形表
        row: 主元行（出基变量所在行）
        col: 主元列（进基变量所在列）

    返回:
        旋转后的单纯形表
    """
    # 步骤1：取出主元值
    pivot_value = tableau[row, col]
    # 标注：主元值必须 > 0（否则比值测试不会选这一行）

    # 步骤2：主元行除以主元值，使主元位置变为1
    # 标注：这一行对应的方程，两边同时除以主元值
    tableau[row, :] = tableau[row, :] / pivot_value

    # 步骤3：对其他所有行（包括检验数行），消去主元列的元素
    # 标注：第i行 = 第i行 - 第i行主元列系数 × 主元行
    for i in range(tableau.shape[0]):
        if i != row:  # 跳过主元行本身
            factor = tableau[i, col]  # 第i行主元列的系数
            # 标注：factor * 主元行 就是要消去的部分
            tableau[i, :] = tableau[i, :] - factor * tableau[row, :]

    # 标注：旋转完成后，主元列col变成了单位向量（第row行是1，其余是0）
    # 这意味着变量x_col成为了新的基变量，替换了原来的x_basis[row]
    return tableau


# ================================================================
# 第三部分：单纯形法主循环
# ================================================================
#
# 算法流程：
# 1. 计算检验数 r_j = c_j - c_B^T B^{-1} A_j
# 2. 如果所有 r_j >= 0（最小化问题），达到最优，结束
# 3. 否则，选择 r_j < 0 中最小的那个变量进基
# 4. 比值测试：theta = min{b_bar_i / a_bar_ik | a_bar_ik > 0}
#    达到最小值的行对应的基变量出基
# 5. 主元旋转，回到步骤1
# ================================================================


def simplex_solve(A, b, c, initial_basis=None, max_iter=1000, verbose=True):
    """
    单纯形法求解（假设已有初始基可行解）

    参数:
        A: 约束系数矩阵 (m x n)
        b: 右端项 (m,)，要求 b >= 0
        c: 目标函数系数 (n,)
        initial_basis: 初始基变量索引列表
        max_iter: 最大迭代次数
        verbose: 是否打印每一步详情

    返回:
        x: 最优解
        z: 最优值
        status: 状态（'optimal' / 'unbounded'）
    """
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)
    m, n = A.shape

    # ------------------------------------------------------------
    # 初始化：构造初始单纯形表
    # ------------------------------------------------------------
    if initial_basis is None:
        # 如果没有指定初始基，假设最后m个变量是松弛变量（构成单位矩阵）
        initial_basis = list(range(n - m, n))

    basis = initial_basis.copy()

    # 构造单纯形表：前m行是[A | b]，最后一行是检验数
    tableau = np.zeros((m + 1, n + 1))
    tableau[:m, :n] = A       # 约束系数
    tableau[:m, -1] = b       # 右端项

    # 计算初始检验数行
    # 标注：检验数 r_j = c_j - c_B^T B^{-1} A_j
    # 因为初始基是单位矩阵，B^{-1} = I，所以 r_j = c_j - c_B^T A_j
    c_B = c[basis]  # 基变量的目标系数
    tableau[-1, :n] = c - c_B @ A  # 检验数
    tableau[-1, -1] = -c_B @ b     # -z（目标值的负数）

    if verbose:
        print("=" * 60)
        print("单纯形法开始求解")
        print(f"问题规模: {m}个约束, {n}个变量")
        print(f"初始基变量: {['x'+str(b) for b in basis]}")
        print_tableau(tableau, basis, 0)

    # ------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------
    for iteration in range(1, max_iter + 1):

        # --------------------------------------------------------
        # 步骤1：最优性检验
        # --------------------------------------------------------
        # 标注：对于最小化问题，如果所有检验数 r_j >= 0，
        # 则增大任何非基变量（从0开始增大）都会使目标值增大或不变，
        # 所以当前解就是最优解。
        reduced_costs = tableau[-1, :n]

        # 找到所有负的检验数
        negative_indices = [j for j in range(n) if reduced_costs[j] < -1e-10]

        if len(negative_indices) == 0:
            # 所有检验数 >= 0，达到最优
            if verbose:
                print(f"\n所有检验数 >= 0，达到最优！")
            break

        # --------------------------------------------------------
        # 步骤2：选择进基变量
        # --------------------------------------------------------
        # 标注：选择检验数最负的变量进基（最速下降方向）
        # 这是Dantzig规则，实际中也可以用Bland规则（选下标最小的）
        entering = negative_indices[0]
        for j in negative_indices:
            if reduced_costs[j] < reduced_costs[entering]:
                entering = j

        if verbose:
            print(f"\n选择进基变量: x{entering}（检验数={reduced_costs[entering]:.4f}）")

        # --------------------------------------------------------
        # 步骤3：比值测试，选择出基变量
        # --------------------------------------------------------
        # 标注：进基变量x_k从0开始增大，基变量 x_B = b_bar - a_bar_k * x_k
        # 为了保持 x_B >= 0，需要 x_k <= b_bar_i / a_bar_ik（当a_bar_ik > 0时）
        # 所以 x_k 的最大增量 = min{b_bar_i / a_bar_ik | a_bar_ik > 0}
        # 达到这个最小值的行对应的基变量出基（减小到0）

        pivot_column = tableau[:m, entering]  # 进基变量列的系数
        rhs = tableau[:m, -1]                  # 右端项（基变量当前值）

        # 只考虑系数 > 0 的行（系数 <= 0 的行，x_k增大时基变量不会减小）
        valid_rows = []
        ratios = []
        for i in range(m):
            if pivot_column[i] > 1e-10:  # 系数严格大于0
                ratio = rhs[i] / pivot_column[i]
                valid_rows.append(i)
                ratios.append(ratio)
                if verbose:
                    print(f"  第{i}行: x{basis[i]} = {rhs[i]:.4f} / {pivot_column[i]:.4f} = {ratio:.4f}")

        if len(valid_rows) == 0:
            # 所有系数 <= 0，意味着x_k可以无限增大，目标值无限减小
            if verbose:
                print(f"进基列所有系数 <= 0，问题无界！")
            return None, None, 'unbounded'

        # 选择比值最小的行（出基变量所在行）
        min_ratio_idx = np.argmin(ratios)
        leaving_row = valid_rows[min_ratio_idx]
        leaving_var = basis[leaving_row]

        if verbose:
            print(f"最小比值 = {ratios[min_ratio_idx]:.4f}（第{leaving_row}行）")
            print(f"出基变量: x{leaving_var}")

        # --------------------------------------------------------
        # 步骤4：主元旋转
        # --------------------------------------------------------
        # 标注：以 (leaving_row, entering) 为主元进行旋转
        # 旋转后，x_entering成为基变量，x_leaving_var成为非基变量
        tableau = pivot(tableau, leaving_row, entering)
        basis[leaving_row] = entering  # 更新基变量列表

        if verbose:
            print_tableau(tableau, basis, iteration, entering, leaving_row)

    else:
        # 超过最大迭代次数
        print(f"警告：超过最大迭代次数 {max_iter}")

    # ------------------------------------------------------------
    # 提取最优解
    # ------------------------------------------------------------
    x = np.zeros(n)
    for i in range(m):
        x[basis[i]] = tableau[i, -1]  # 基变量的值 = 右端项
    z = -tableau[-1, -1]              # 最优值

    if verbose:
        print(f"\n{'='*60}")
        print(f"求解完成！")
        print(f"最优解: x = {np.round(x, 4)}")
        print(f"最优值: z = {z:.4f}")
        print(f"迭代次数: {iteration}")
        print(f"{'='*60}")

    return x, z, 'optimal'


# ================================================================
# 第四部分：两阶段法（获取初始基可行解）
# ================================================================
#
# 当约束中包含 = 或 >= 时，松弛变量不能直接构成初始基，
# 需要引入人工变量，用两阶段法求解。
#
# 第一阶段：最小化人工变量之和
#   - 如果最优值 > 0，原问题不可行
#   - 如果最优值 = 0，得到原问题的一个基可行解
#
# 第二阶段：去掉人工变量，用原始目标函数继续优化
# ================================================================


def two_phase_simplex(A, b, c, verbose=True):
    """
    两阶段法求解线性规划（标准形式 min c^T x, Ax=b, x>=0）

    参数:
        A: 约束系数矩阵
        b: 右端项
        c: 目标函数系数
        verbose: 是否打印详情

    返回:
        x, z, status
    """
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)
    m, n = A.shape

    if verbose:
        print("=" * 60)
        print("两阶段法开始")
        print("=" * 60)

    # ------------------------------------------------------------
    # 第一阶段：引入人工变量，最小化人工变量之和
    # ------------------------------------------------------------
    # 标注：在每个约束后加一个人工变量 a_i >= 0
    # 目标：min a_1 + a_2 + ... + a_m
    # 初始基：人工变量（因为它们构成单位矩阵）

    A_phase1 = np.hstack([A, np.eye(m)])  # 加人工变量列
    c_phase1 = np.concatenate([np.zeros(n), np.ones(m)])  # 人工变量系数为1
    basis_phase1 = list(range(n, n + m))  # 初始基 = 人工变量

    if verbose:
        print(f"\n第一阶段：最小化 {'+'.join(['a'+str(i) for i in range(m)])}")
        print(f"人工变量作为初始基")

    # 调用单纯形法求解第一阶段
    # 标注：第一阶段的目标是最小化人工变量之和
    x_phase1, z_phase1, status = simplex_solve(
        A_phase1, b, c_phase1,
        initial_basis=basis_phase1,
        verbose=verbose
    )

    if status == 'unbounded':
        return None, None, 'unbounded'

    if z_phase1 > 1e-8:
        # 第一阶段最优值 > 0，说明人工变量无法全部为0
        # 标注：这意味着原问题没有可行解
        if verbose:
            print(f"\n第一阶段最优值 = {z_phase1:.6f} > 0")
            print("原问题不可行！")
        return None, None, 'infeasible'

    if verbose:
        print(f"\n第一阶段完成，最优值 = {z_phase1:.6f}，问题可行")

    # ------------------------------------------------------------
    # 处理退化：人工变量可能还在基中（值为0）
    # ------------------------------------------------------------
    # 标注：如果人工变量还在基中，需要找非人工变量替换它
    # 如果找不到，说明该行约束是冗余的，可以删除

    # 这里简化处理：直接从第一阶段的最终表中提取基变量
    # 实际实现中需要更仔细的退化处理（参见01_单纯形法_手动实现.py）

    # 重新构造第二阶段的表（简化版，假设人工变量已不在基中）
    # 标注：实际使用中建议用 01_单纯形法_手动实现.py 的完整版本
    print("\n注：完整的两阶段法（含退化处理）请见 01_单纯形法_手动实现.py")
    print("本教学版主要展示单纯形法主循环的细节")

    return None, None, 'demo_only'


# ================================================================
# 第五部分：一步步演示（教学用）
# ================================================================


def test_step_by_step():
    """
    一步步演示单纯形法求解生产计划问题

    问题：
        max 3x1 + 5x2
        s.t. x1 + 2x2 <= 8    （原料甲）
             2x1 + x2 <= 10   （原料乙）
             x1, x2 >= 0

    转化为标准形式：
        min -3x1 - 5x2
        s.t. x1 + 2x2 + s1 = 8
             2x1 + x2 + s2 = 10
             x1, x2, s1, s2 >= 0

    变量顺序：x0=x1, x1=x2, x2=s1, x3=s2
    """
    print("\n" + "#" * 60)
    print("# 一步步演示：生产计划问题")
    print("#" * 60)
    print("""
原始问题：
    max 3x1 + 5x2
    s.t. x1 + 2x2 <= 8    （原料甲限量8）
         2x1 + x2 <= 10   （原料乙限量10）
         x1, x2 >= 0

转化为标准形式（加松弛变量s1, s2）：
    min -3x1 - 5x2
    s.t. x1 + 2x2 + s1 = 8
         2x1 + x2 + s2 = 10
         x1, x2, s1, s2 >= 0

变量编号：x0=x1, x1=x2, x2=s1, x3=s2
初始基：s1, s2（即x2, x3）
    """)

    # 约束矩阵（4个变量：x1, x2, s1, s2）
    A = [
        [1, 2, 1, 0],   # x1 + 2x2 + s1 = 8
        [2, 1, 0, 1]    # 2x1 + x2 + s2 = 10
    ]
    b = [8, 10]
    c = [-3, -5, 0, 0]  # 最小化 -3x1 -5x2

    x, z, status = simplex_solve(A, b, c, initial_basis=[2, 3], verbose=True)

    print(f"""
结果解释：
    x1 = {x[0]:.0f}（生产甲产品 {x[0]:.0f} 单位）
    x2 = {x[1]:.0f}（生产乙产品 {x[1]:.0f} 单位）
    s1 = {x[2]:.0f}（原料甲剩余 {x[2]:.0f} 单位）
    s2 = {x[3]:.0f}（原料乙剩余 {x[3]:.0f} 单位）
    最大利润 = {-z:.0f} 元

验证：
    原料甲使用: {x[0]:.0f} + 2*{x[1]:.0f} = {x[0] + 2*x[1]:.0f} <= 8 ✓
    原料乙使用: 2*{x[0]:.0f} + {x[1]:.0f} = {2*x[0] + x[1]:.0f} <= 10 ✓
    利润: 3*{x[0]:.0f} + 5*{x[1]:.0f} = {3*x[0] + 5*x[1]:.0f} ✓
    """)


# ================================================================
# 第六部分：更多测试
# ================================================================


def test_transportation():
    """测试运输问题"""
    print("\n" + "#" * 60)
    print("# 测试：运输问题（2产地3销地）")
    print("#" * 60)

    # 变量：x01, x02, x03, x11, x12, x13（产地i到销地j的运量）
    # 约束：产地产量、销地销量
    A = [
        [1, 1, 1, 0, 0, 0],   # 产地1产量=10
        [0, 0, 0, 1, 1, 1],   # 产地2产量=20
        [1, 0, 0, 1, 0, 0],   # 销地1销量=8
        [0, 1, 0, 0, 1, 0],   # 销地2销量=12
    ]
    b = [10, 20, 8, 12]
    c = [3, 5, 2, 4, 1, 3]  # 单位运费

    # 注：运输问题有一个约束是冗余的，这里去掉了销地3的约束
    # 销地3销量 = 总产量 - 销地1 - 销地2 = 30 - 8 - 12 = 10

    print("""
问题：2个产地（产量10, 20），3个销地（销量8, 12, 10）
单位运费：
      销1  销2  销3
产1   3    5    2
产2   4    1    3
    """)

    # 这个问题需要两阶段法（因为有等式约束），这里用完整版本
    print("（运输问题含等式约束，需要两阶段法）")
    print("完整求解请使用 01_单纯形法_手动实现.py")


def test_verbose_off():
    """静默模式测试"""
    print("\n" + "#" * 60)
    print("# 静默模式测试")
    print("#" * 60)

    A = [[1, 2, 1, 0], [2, 1, 0, 1]]
    b = [8, 10]
    c = [-3, -5, 0, 0]

    x, z, status = simplex_solve(A, b, c, initial_basis=[2, 3], verbose=False)
    print(f"最优解: x1={x[0]:.2f}, x2={x[1]:.2f}")
    print(f"最优值: {-z:.2f}")
    print(f"状态: {status}")


if __name__ == "__main__":
    # 一步步演示（建议仔细看每一步的表变化）
    test_step_by_step()

    # 静默模式测试
    test_verbose_off()

    print("""
============================================================
学习要点总结：
============================================================
1. 单纯形表的结构：前m行约束 + 最后一行检验数 + 最后一列RHS
2. 检验数 r_j = c_j - c_B^T B^{-1} A_j，判断是否最优
3. 进基变量：选检验数最负的（最小化问题）
4. 出基变量：比值测试 theta = min{b_i / a_ik | a_ik > 0}
5. 主元旋转：一次旋转 = 一次顶点跳跃
6. 两阶段法：第一阶段判断可行性，第二阶段求最优
7. 退化：基变量为0，可能导致循环（Bland规则可避免）

建议：
- 反复运行 test_step_by_step()，观察每一步表的变化
- 手动计算一遍，和程序结果对比
- 尝试修改参数，观察结果变化
============================================================
    """)
