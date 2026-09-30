"""
TDD 测试文件：问题二 双目标 Pareto GA 重写
===========================================
先写测试 → 看失败 → 再写实现 → 看通过
"""
import numpy as np

# ============================================================
# TEST 1: S2 连续函数 — 阶跃改为线性插值
# ============================================================

def test_s2_continuous():
    """S2(u) 在各区间应连续，端点应与阶跃值对齐"""
    from q2_biobjective_ga import s2_continuous

    # 端点值对齐旧阶梯
    assert abs(s2_continuous(0.30) - 1.00) < 1e-10, f"u=0.3 fail: {s2_continuous(0.30)}"
    assert abs(s2_continuous(0.60) - 1.00) < 1e-10, f"u=0.6 fail: {s2_continuous(0.60)}"
    assert abs(s2_continuous(0.75) - 0.93) < 1e-10, f"u=0.75 fail: {s2_continuous(0.75)}"
    assert abs(s2_continuous(0.85) - 0.85) < 1e-10, f"u=0.85 fail: {s2_continuous(0.85)}"
    assert abs(s2_continuous(0.95) - 0.72) < 1e-10, f"u=0.95 fail: {s2_continuous(0.95)}"
    assert abs(s2_continuous(1.00) - 0.50) < 1e-10, f"u=1.0 fail: {s2_continuous(1.00)}"

    # 中间点线性插值
    mid = s2_continuous(0.675)  # (0.60+0.75)/2
    expected = 0.965  # (1.00+0.93)/2
    assert abs(mid - expected) < 1e-10, f"u=0.675 mid fail: {mid}"

    # 单调递减
    vals = [s2_continuous(u) for u in np.linspace(0, 1.2, 100)]
    for i in range(len(vals)-1):
        assert vals[i] >= vals[i+1], f"非单调: u={i/100}, {vals[i]} < {vals[i+1]}"

    # 无 NaN
    for u in np.linspace(0, 2, 50):
        assert not np.isnan(s2_continuous(u))

    print("✓ test_s2_continuous 通过")


# ============================================================
# TEST 2: 固定点迭代收敛 — 连续S2 无阻尼
# ============================================================

def test_solve_equilibrium():
    """固定点迭代应在规定步数内收敛到唯一均衡，无空站"""
    from q2_biobjective_ga import solve_equilibrium, get_data, s2_continuous

    data = get_data()
    config = np.zeros(10, dtype=int)
    # 配置: C(小), D(小), F(大), I(小), J(小) — 旧代码在此配置下振荡
    config[2] = 1  # C
    config[3] = 1  # D
    config[5] = 3  # F
    config[8] = 1  # I
    config[9] = 1  # J

    assignments, utils, comm_sats, converged = solve_equilibrium(config, data, tol=1e-3)

    # 必须收敛 (离散分配下tol=1e-3为实用收敛)
    assert converged, f"固定点迭代未收敛！"

    # 所有站点必须有非零分配（无空站！）
    stations = np.where(config > 0)[0]
    for s in stations:
        assigned = np.sum(assignments == s)
        assert assigned > 0, f"站点 {s} 为空站！赋值={assigned}"

    # 利用率在 [0,1] 内
    for s in stations:
        assert 0 <= utils[s] <= 1.01, f"站点 {s} 利用率异常: {utils[s]}"

    print("✓ test_solve_equilibrium 通过 (所有站点非空, 收敛)")


# ============================================================
# TEST 3: 非支配排序
# ============================================================

def test_non_dominated_sort():
    """快速非支配排序正确分层"""
    from q2_biobjective_ga import non_dominated_sort

    C = np.array([1.0, 0.9, 0.8, 0.95, 0.85])
    S = np.array([0.9, 0.95, 1.0, 0.85, 0.92])

    fronts = non_dominated_sort(C, S)

    # F1 层：未被支配的个体 (C=1.0,S=0.9), (C=0.9,S=0.95), (C=0.8,S=1.0)
    # (C=1.0,S=0.9) 不被任何支配
    # (C=0.9,S=0.95) vs (C=1.0,S=0.9): 互不支配 (前者C更高，后者S更高)
    # 这些都在第一层
    assert len(fronts) >= 1, "至少有一个前沿层"

    # (C=0.95,S=0.85) 被 (C=1.0,S=0.9) 支配 (C和S都更高)
    # 不应在 F1
    in_f1 = set(fronts[0])
    assert 3 not in in_f1, f"个体3(C=0.95,S=0.85)不应在F1, F1={in_f1}"
    assert 0 in in_f1, f"个体0(C=1.0,S=0.9)应在F1, F1={in_f1}"
    assert 1 in in_f1, f"个体1(C=0.9,S=0.95)应在F1, F1={in_f1}"

    print("✓ test_non_dominated_sort 通过")


# ============================================================
# TEST 4: 拥挤距离
# ============================================================

def test_crowding_distance():
    """边界个体应获得无限距离"""
    from q2_biobjective_ga import crowding_distance

    C = np.array([1.0, 0.95, 0.9, 0.85, 0.8])
    S = np.array([0.8, 0.85, 0.9, 0.95, 1.0])
    front = [0, 1, 2, 3, 4]

    dist = crowding_distance(front, C, S)

    # 边界个体 (C最大或S最大) 距离应为 inf
    assert dist[0] == float('inf'), f"边界0应为inf: {dist[0]}"
    assert dist[4] == float('inf'), f"边界4应为inf: {dist[4]}"
    # 中间个体距离应为有限正数
    assert 0 < dist[2] < float('inf'), f"中间2应为有限: {dist[2]}"

    print("✓ test_crowding_distance 通过")


# ============================================================
# TEST 5: 覆盖率正确定义
# ============================================================

def test_coverage_definition():
    """覆盖率 = 站点容量能装下的人数/总人数 (满员不可再进)"""
    from q2_biobjective_ga import evaluate_config, get_data

    data = get_data()
    config = np.zeros(10, dtype=int)
    config[2] = 1  # C站(小,1000人次/日), 5个小区分配来, 需求远超容量

    cov, sat, _, _, _, _ = evaluate_config(config, data)

    # 单站容量仅1000, 5个小区日需求~5000, 比率~0.2
    assert cov > 0.05, f"覆盖应>0: {cov:.4f}"
    assert cov < 0.5, f"单站覆盖应<50%: {cov:.4f}"

    print(f"✓ test_coverage_definition 通过 (cov={cov:.4f})")


# ============================================================
# TEST 6: 预算约束
# ============================================================

def test_station_A_index_zero():
    """站A(index=0)被分配时不应被误判为未分配"""
    from q2_biobjective_ga import evaluate_config, get_data

    data = get_data()
    config = np.zeros(10, dtype=int)
    config[0] = 1  # 只在A建站(小型) - A是index 0!

    cov, sat, assignments, _, _, _ = evaluate_config(config, data)

    # A站1000m内: A(0), B(600), J(500) → 3个小区应分配到站A(index=0)
    # 如果index-0 bug存在, 这些小区会被误判为未分配, cov=0
    assert cov > 0.0, f"A站分配后覆盖应为正: {cov:.4f}"
    assert assignments[0] == 0, f"A小区应分配到站0, 实际={assignments[0]}"
    print(f"✓ test_station_A_index_zero 通过 (cov={cov:.4f}, A→站{assignments[0]})")


def test_budget_constraint():
    """超预算配置应返回零覆盖率"""
    from q2_biobjective_ga import evaluate_config, get_data

    data = get_data()
    config = np.full(10, 3, dtype=int)  # 全大型站: 10×45=450万 >> 120万

    cov, sat, _, _, _, _ = evaluate_config(config, data)

    assert cov == 0.0, f"超预算应返回0, 实际={cov}"
    assert sat == 0.0, f"超预算满意应为0, 实际={sat}"

    print("✓ test_budget_constraint 通过")


# ============================================================
# 运行所有测试
# ============================================================

if __name__ == '__main__':
    print("=" * 55)
    print("TDD 测试：问题二 双目标 Pareto GA")
    print("=" * 55)
    print()

    try:
        test_s2_continuous()
    except ImportError as e:
        print(f"⚠ 跳过 (实现文件还未创建): {e}")

    try:
        test_solve_equilibrium()
    except ImportError as e:
        print(f"⚠ 跳过 (实现文件还未创建): {e}")

    try:
        test_non_dominated_sort()
    except ImportError as e:
        print(f"⚠ 跳过 (实现文件还未创建): {e}")

    try:
        test_crowding_distance()
    except ImportError as e:
        print(f"⚠ 跳过 (实现文件还未创建): {e}")

    try:
        test_coverage_definition()
    except ImportError as e:
        print(f"⚠ 跳过 (实现文件还未创建): {e}")

    try:
        test_station_A_index_zero()
    except ImportError as e:
        print(f"⚠ 跳过 (实现文件还未创建): {e}")

    try:
        test_budget_constraint()
    except ImportError as e:
        print(f"⚠ 跳过 (实现文件还未创建): {e}")

    print()
    print("=" * 55)
    print("TDD RED 阶段完成 — 所有测试应因 ImportError/AssertionError 失败")
    print("下一步：实现 q2_biobjective_ga.py 让测试通过")
    print("=" * 55)
