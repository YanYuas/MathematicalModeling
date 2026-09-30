# -*- coding: utf-8 -*-
"""
博弈论基础 · 原理与手动实现
==============================
六层钻研法 · 第3-4层：数学推导 + 手动实现

内容：
1. 博弈论基本概念（参与者/策略/收益/纳什均衡）
2. 零和博弈与最小最大定理
3. 纯策略纳什均衡求解
4. 混合策略纳什均衡（2×2博弈解析解）
5. 零和博弈的线性规划求解
6. 经典案例：囚徒困境、性别战、鹰鸽博弈

博弈论是优化的延伸：多个决策者相互影响，每个人的最优取决于他人的选择。
"""

import numpy as np
from itertools import product


# ============================================================
# 1. 博弈论基本概念
# ============================================================
"""
博弈的三要素：
1. 参与者（Players）：做决策的人
2. 策略（Strategies）：每个参与者可以选择的行动
3. 收益（Payoffs）：每个策略组合下各参与者的收益

纳什均衡（Nash Equilibrium）：
  在一个策略组合中，每个参与者的策略都是对其他参与者策略的最优反应。
  换句话说，没有人能通过单方面改变策略来提高自己的收益。

数学表达：
  策略组合 (s1*, s2*, ..., sn*) 是纳什均衡，当且仅当
  对每个参与者i，ui(si*, s-i*) >= ui(si, s-i*) 对所有si成立。
"""


# ============================================================
# 2. 纯策略纳什均衡求解
# ============================================================
def find_pure_nash_equilibrium(payoff_matrix):
    """
    找纯策略纳什均衡
    
    参数：
        payoff_matrix: 二维数组，payoff_matrix[i][j] = (row_player_payoff, col_player_payoff)
    
    返回：
        纳什均衡列表，每个元素是 (row_strategy, col_strategy, row_payoff, col_payoff)
    """
    n_rows = len(payoff_matrix)
    n_cols = len(payoff_matrix[0])
    
    nash_equilibria = []
    
    for i in range(n_rows):
        for j in range(n_cols):
            # 检查行玩家是否最优（给定列玩家选j）
            row_payoff = payoff_matrix[i][j][0]
            row_best = all(payoff_matrix[k][j][0] <= row_payoff + 1e-10 
                          for k in range(n_rows))
            
            # 检查列玩家是否最优（给定行玩家选i）
            col_payoff = payoff_matrix[i][j][1]
            col_best = all(payoff_matrix[i][k][1] <= col_payoff + 1e-10 
                          for k in range(n_cols))
            
            if row_best and col_best:
                nash_equilibria.append((i, j, row_payoff, col_payoff))
    
    return nash_equilibria


def prisoners_dilemma():
    """
    囚徒困境（Prisoner's Dilemma）
    
    两个嫌疑人被分开审讯：
    - 都沉默：各判1年
    - 都坦白：各判3年
    - 一个坦白一个沉默：坦白的释放，沉默的判5年
    
    收益矩阵（行玩家收益，列玩家收益）：
                    沉默      坦白
    沉默        (-1, -1)   (-5, 0)
    坦白         (0, -5)   (-3, -3)
    
    纳什均衡：(坦白, 坦白)，收益(-3, -3)
    但(沉默, 沉默)收益(-1, -1)对双方都更好——这就是"困境"！
    """
    print("=" * 60)
    print("案例1：囚徒困境")
    print("=" * 60)
    
    # 收益：用负数表示判刑年数（越大越好）
    payoff = [
        [(-1, -1), (-5, 0)],   # 行：沉默
        [(0, -5), (-3, -3)],   # 行：坦白
    ]
    
    ne = find_pure_nash_equilibrium(payoff)
    print(f"纯策略纳什均衡：{len(ne)}个")
    for i, j, rp, cp in ne:
        row_strat = "沉默" if i == 0 else "坦白"
        col_strat = "沉默" if j == 0 else "坦白"
        print(f"  ({row_strat}, {col_strat}): 行收益={rp}, 列收益={cp}")
    
    print("\n分析：")
    print("  无论对方选什么，坦白总是更好（占优策略）")
    print("  所以双方都坦白，各判3年")
    print("  但如果都沉默，各判1年——个体理性导致集体非理性！")
    print()


def battle_of_sexes():
    """
    性别战（Battle of the Sexes）
    
    一对情侣决定去哪：
    - 男方喜欢足球，女方喜欢芭蕾
    - 但两人更想在一起（分开的话都不开心）
    
    收益矩阵：
                    足球      芭蕾
    足球         (2, 1)    (0, 0)
    芭蕾         (0, 0)    (1, 2)
    
    纳什均衡：(足球, 足球)和(芭蕾, 芭蕾)——两个纯策略均衡！
    还有一个混合策略均衡。
    """
    print("=" * 60)
    print("案例2：性别战（协调博弈）")
    print("=" * 60)
    
    payoff = [
        [(2, 1), (0, 0)],   # 行：足球
        [(0, 0), (1, 2)],   # 行：芭蕾
    ]
    
    ne = find_pure_nash_equilibrium(payoff)
    print(f"纯策略纳什均衡：{len(ne)}个")
    for i, j, rp, cp in ne:
        row_strat = "足球" if i == 0 else "芭蕾"
        col_strat = "足球" if j == 0 else "芭蕾"
        print(f"  ({row_strat}, {col_strat}): 行收益={rp}, 列收益={cp}")
    
    print("\n分析：")
    print("  有两个纯策略均衡，双方都想在一起，但偏好不同")
    print("  混合策略均衡：男方以2/3概率选足球，女方以2/3概率选芭蕾")
    print("  混合策略下，双方期望收益都是2/3（比纯策略差）")
    print()


# ============================================================
# 3. 混合策略纳什均衡（2×2博弈）
# ============================================================
def solve_mixed_strategy_2x2(payoff_matrix):
    """
    求解2×2博弈的混合策略纳什均衡
    
    行玩家以概率p选策略0，1-p选策略1
    列玩家以概率q选策略0，1-q选策略1
    
    混合策略均衡的条件：
    - 行玩家的两个策略期望收益相等（否则会偏向某一个）
    - 列玩家的两个策略期望收益相等
    
    返回：(p, q, row_expected_payoff, col_expected_payoff)
    """
    # 收益矩阵
    a = payoff_matrix[0][0][0]  # 行选0，列选0，行收益
    b = payoff_matrix[0][1][0]  # 行选0，列选1，行收益
    c = payoff_matrix[1][0][0]  # 行选1，列选0，行收益
    d = payoff_matrix[1][1][0]  # 行选1，列选1，行收益
    
    e = payoff_matrix[0][0][1]  # 行选0，列选0，列收益
    f = payoff_matrix[0][1][1]  # 行选0，列选1，列收益
    g = payoff_matrix[1][0][1]  # 行选1，列选0，列收益
    h = payoff_matrix[1][1][1]  # 行选1，列选1，列收益
    
    # 列玩家混合策略q：使行玩家两个策略收益相等
    # q*a + (1-q)*b = q*c + (1-q)*d
    # q*(a-b-c+d) = d - b
    denom_row = a - b - c + d
    if abs(denom_row) < 1e-10:
        q = None
    else:
        q = (d - b) / denom_row
    
    # 行玩家混合策略p：使列玩家两个策略收益相等
    # p*e + (1-p)*g = p*f + (1-p)*h
    # p*(e-f-g+h) = h - g
    denom_col = e - f - g + h
    if abs(denom_col) < 1e-10:
        p = None
    else:
        p = (h - g) / denom_col
    
    # 计算期望收益
    if p is not None and q is not None and 0 <= p <= 1 and 0 <= q <= 1:
        row_payoff = p * q * a + p * (1-q) * b + (1-p) * q * c + (1-p) * (1-q) * d
        col_payoff = p * q * e + p * (1-q) * f + (1-p) * q * g + (1-p) * (1-q) * h
        return p, q, row_payoff, col_payoff
    else:
        return None, None, None, None


def hawk_dove_game():
    """
    鹰鸽博弈（Hawk-Dove Game）
    
    两只动物争夺资源V：
    - 鹰策略：战斗，赢了得V，输了受伤-C
    - 鸽策略：展示，赢了得V，输了0（不受伤）
    
    收益矩阵（假设V=2, C=4）：
                    鹰        鸽
    鹰         (-1, -1)   (2, 0)
    鸽          (0, 2)    (1, 1)
    
    混合策略均衡：以V/C的概率选鹰
    """
    print("=" * 60)
    print("案例3：鹰鸽博弈（演化博弈）")
    print("=" * 60)
    
    V, C = 2, 4
    payoff = [
        [((V-C)/2, (V-C)/2), (V, 0)],   # 鹰
        [(0, V), (V/2, V/2)],             # 鸽
    ]
    
    print(f"参数：资源V={V}, 战斗成本C={C}")
    print(f"收益矩阵：")
    print(f"          鹰        鸽")
    print(f"  鹰   {payoff[0][0]}   {payoff[0][1]}")
    print(f"  鸽   {payoff[1][0]}   {payoff[1][1]}")
    
    # 纯策略均衡
    ne = find_pure_nash_equilibrium(payoff)
    print(f"\n纯策略纳什均衡：{len(ne)}个")
    for i, j, rp, cp in ne:
        row_strat = "鹰" if i == 0 else "鸽"
        col_strat = "鹰" if j == 0 else "鸽"
        print(f"  ({row_strat}, {col_strat})")
    
    # 混合策略均衡
    p, q, rp, cp = solve_mixed_strategy_2x2(payoff)
    if p is not None:
        print(f"\n混合策略纳什均衡：")
        print(f"  行玩家：以{p:.2f}概率选鹰，{1-p:.2f}概率选鸽")
        print(f"  列玩家：以{q:.2f}概率选鹰，{1-q:.2f}概率选鸽")
        print(f"  期望收益：行={rp:.2f}, 列={cp:.2f}")
        print(f"  理论值：鹰的概率=V/C={V/C:.2f}")
    
    print("\n分析：")
    print("  当C>V时，混合策略是演化稳定策略（ESS）")
    print("  鹰的比例=V/C，资源越珍贵或战斗成本越低，鹰越多")
    print()


# ============================================================
# 4. 零和博弈与最小最大定理
# ============================================================
def solve_zero_sum_game(payoff_matrix):
    """
    求解零和博弈（行玩家收益矩阵，列玩家收益=-行收益）
    
    最小最大定理（von Neumann）：
        max_p min_q p^T A q = min_q max_p p^T A q
        即：行玩家的最大最小收益 = 列玩家的最小最大损失
    
    用线性规划求解：
    行玩家：max v, s.t. Σ p_i * a_ij >= v (对所有j), Σp_i=1, p_i>=0
    列玩家：min v, s.t. Σ q_j * a_ij <= v (对所有i), Σq_j=1, q_j>=0
    """
    print("=" * 60)
    print("零和博弈求解（最小最大定理）")
    print("=" * 60)
    
    A = np.array(payoff_matrix, dtype=float)
    n_rows, n_cols = A.shape
    
    # 行玩家的最大最小策略（纯策略）
    row_guaranteed = A.min(axis=1).max()  # 最大最小
    row_strategy = A.min(axis=1).argmax()
    
    # 列玩家的最小最大策略（纯策略）
    col_guaranteed = A.max(axis=0).min()  # 最小最大
    col_strategy = A.max(axis=0).argmin()
    
    print(f"收益矩阵（行玩家）：")
    print(A)
    print(f"\n纯策略分析：")
    print(f"  行玩家最大最小：{row_guaranteed}（选策略{row_strategy}）")
    print(f"  列玩家最小最大：{col_guaranteed}（选策略{col_strategy}）")
    
    if abs(row_guaranteed - col_guaranteed) < 1e-10:
        print(f"  ✓ 纯策略鞍点存在，博弈值={row_guaranteed}")
    else:
        print(f"  ✗ 纯策略鞍点不存在，需要混合策略")
        print(f"  行玩家保证：{row_guaranteed}，列玩家限制：{col_guaranteed}")
        print(f"  混合策略博弈值在[{row_guaranteed}, {col_guaranteed}]之间")
    
    print()
    return row_guaranteed, col_guaranteed


def matching_pennies():
    """
    猜硬币博弈（Matching Pennies）
    
    两个玩家同时出硬币正面或反面：
    - 相同：行玩家赢（+1），列玩家输（-1）
    - 不同：行玩家输（-1），列玩家赢（+1）
    
    收益矩阵（行玩家）：
                    正面      反面
    正面           1        -1
    反面          -1         1
    
    没有纯策略均衡，混合策略均衡：各以1/2概率选正面/反面
    """
    print("=" * 60)
    print("案例4：猜硬币博弈（零和博弈）")
    print("=" * 60)
    
    payoff = [[1, -1], [-1, 1]]
    solve_zero_sum_game(payoff)
    
    print("混合策略均衡：")
    print("  双方都以1/2概率选正面，1/2概率选反面")
    print("  博弈值=0（公平游戏）")
    print()


# ============================================================
# 5. 零和博弈的线性规划求解（混合策略）
# ============================================================
def solve_zero_sum_mixed(A):
    """
    用线性规划求解零和博弈的混合策略
    
    行玩家问题：
        max v
        s.t. Σ_i p_i * a_ij >= v  (对所有j)
             Σ_i p_i = 1
             p_i >= 0
    
    转化为标准LP（用scipy.optimize.linprog）：
    变量：x = [p_0, p_1, ..., p_{n-1}, v]
    目标：max v → min -v
    约束：Σ p_i * a_ij - v >= 0 → -Σ p_i * a_ij + v <= 0
          Σ p_i = 1
          p_i >= 0, v自由
    """
    from scipy.optimize import linprog
    
    A = np.array(A, dtype=float)
    n_rows, n_cols = A.shape
    
    # 变量：p[0..n_rows-1], v
    # 目标：min -v
    c = np.zeros(n_rows + 1)
    c[-1] = -1
    
    # 不等式约束：Σ p_i * a_ij - v >= 0 → -Σ p_i * a_ij + v <= 0
    A_ub = np.zeros((n_cols, n_rows + 1))
    for j in range(n_cols):
        for i in range(n_rows):
            A_ub[j][i] = -A[i][j]
        A_ub[j][-1] = 1
    b_ub = np.zeros(n_cols)
    
    # 等式约束：Σ p_i = 1
    A_eq = np.zeros((1, n_rows + 1))
    A_eq[0][:n_rows] = 1
    b_eq = [1]
    
    # 边界：p_i >= 0, v自由
    bounds = [(0, None)] * n_rows + [(None, None)]
    
    result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                     bounds=bounds, method='highs')
    
    if result.success:
        p = result.x[:n_rows]
        v = result.x[-1]
        return p, v
    else:
        return None, None


def test_zero_sum_lp():
    """测试零和博弈混合策略求解"""
    print("=" * 60)
    print("案例5：零和博弈混合策略（LP求解）")
    print("=" * 60)
    
    # 石头剪刀布
    A = [
        [0, -1, 1],   # 石头
        [1, 0, -1],   # 剪刀
        [-1, 1, 0],   # 布
    ]
    
    p, v = solve_zero_sum_mixed(A)
    if p is not None:
        print("石头剪刀布博弈：")
        print(f"  行玩家最优混合策略：石头={p[0]:.3f}, 剪刀={p[1]:.3f}, 布={p[2]:.3f}")
        print(f"  博弈值：{v:.3f}")
        print(f"  理论值：各1/3，博弈值=0")
    print()


# ============================================================
# 主函数
# ============================================================
if __name__ == '__main__':
    prisoners_dilemma()
    battle_of_sexes()
    hawk_dove_game()
    matching_pennies()
    test_zero_sum_lp()
    
    print("=" * 60)
    print("博弈论基础要点总结：")
    print("=" * 60)
    print("1. 纳什均衡：每个人的策略都是对他人的最优反应")
    print("2. 纯策略均衡：用最优反应法逐个检查")
    print("3. 混合策略均衡：让对方各策略期望收益相等")
    print("4. 零和博弈：最小最大定理，可用线性规划求解")
    print("5. 囚徒困境：个体理性导致集体非理性")
    print("6. 协调博弈：多个均衡，需要沟通/惯例")
    print("7. 鹰鸽博弈：混合策略是演化稳定策略（ESS）")
