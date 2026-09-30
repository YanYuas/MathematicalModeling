"""
Q2 双目标 Pareto GA — 服务站选址与规模优化 (全新重写)
========================================================
目标: 双目标最大化 (覆盖率, 满意度)
算法: 非支配排序遗传算法 (NSGA-II风格)
关键修复:
  1. 覆盖率 = 实际服务人数/总人数 (非地理覆盖)
  2. S2连续线性插值 (根除阶跃导致的振荡)
  3. Pareto前沿输出 (非单点加权)
借鉴: math1/genetic_algorithm_optimize 的GA骨架
"""
import numpy as np
import time
import os

# ============================================================
# 0. 数据加载
# ============================================================

def get_data():
    """返回所有问题数据的字典，保证不可变"""
    N5 = np.array([
        [521, 150, 114], [436, 130, 106], [669, 199, 150],
        [391, 115,  94], [567, 168, 129], [345, 101,  74],
        [626, 185, 142], [413, 123,  91], [533, 159, 120],
        [480, 141, 105]
    ], dtype=float)

    elderly_total = N5.sum(axis=1)
    total_elderly = elderly_total.sum()

    demand_pp = np.array([
        [14, 20, 22], [8, 14, 18], [0, 6, 12],
        [2, 4, 6], [0, 2, 4], [0.15, 1, 3]
    ])
    cost_per = np.array([8, 16, 24, 23, 20, 8])
    revenue_per = np.array([10, 20, 30, 28, 25, 0])
    income = np.array([3400, 3100, 3800, 2900, 3500, 2700, 3600, 3000, 3300, 3200])
    cap_ratio = np.array([0.20, 0.25, 0.30])

    dist = np.array([
        [0, 600, 1200, 900, 1500, 1800, 1300, 700, 1100, 500],
        [600, 0, 800, 500, 1100, 1400, 900, 400, 700, 300],
        [1200, 800, 0, 700, 600, 900, 500, 900, 600, 700],
        [900, 500, 700, 0, 800, 1100, 600, 300, 500, 400],
        [1500, 1100, 600, 800, 0, 500, 400, 1000, 500, 800],
        [1800, 1400, 900, 1100, 500, 0, 500, 1200, 700, 1100],
        [1300, 900, 500, 600, 400, 500, 0, 800, 400, 600],
        [700, 400, 900, 300, 1000, 1200, 800, 0, 600, 300],
        [1100, 700, 600, 500, 500, 700, 400, 600, 0, 400],
        [500, 300, 700, 400, 800, 1100, 600, 300, 400, 0],
    ])

    n_comm = 10
    comm_names = list('ABCDEFGHIJ')
    scale_names = ['小型', '中型', '大型']
    scale_capacity = np.array([1000, 2000, 3000])
    construct_cost = np.array([18, 32, 45])
    daily_operating = np.array([2000, 3200, 4400])
    MAX_BUDGET = 120
    reachable = dist <= 1000

    # 1.3 消费约束下日需求 (营收价格, 预算安全取整)
    monthly_demand = np.zeros(n_comm)
    monthly_service_demand = np.zeros((n_comm, 6))
    for i in range(n_comm):
        caps = income[i] * cap_ratio
        for t in range(3):
            n = N5[i, t]
            if n == 0:
                continue
            theo = demand_pp[:, t]
            theo_cost = np.dot(theo, revenue_per)
            if theo_cost <= caps[t]:
                constrained = np.round(n * theo) / n
            else:
                r = caps[t] / theo_cost
                constrained = np.round(theo * r)
                for _ in range(30):
                    if np.dot(constrained, revenue_per) <= caps[t]:
                        break
                    over = (constrained - theo * r) * revenue_per
                    worst = np.argmax(over)
                    if constrained[worst] <= 0:
                        break
                    constrained[worst] -= 1
            monthly_service_demand[i] += n * constrained
        monthly_demand[i] = monthly_service_demand[i].sum()
    daily_demand = monthly_demand / 30

    # S1 矩阵
    S1 = np.zeros((n_comm, n_comm))
    for i in range(n_comm):
        for j in range(n_comm):
            d = dist[i, j]
            if d <= 300:       S1[i, j] = 1.00
            elif d <= 500:     S1[i, j] = 0.90
            elif d <= 650:     S1[i, j] = 0.75
            elif d <= 1000:    S1[i, j] = 0.60

    return {
        'N5': N5, 'elderly_total': elderly_total, 'total_elderly': total_elderly,
        'daily_demand': daily_demand, 'monthly_demand': monthly_demand,
        'monthly_service_demand': monthly_service_demand,
        'dist': dist, 'S1': S1, 'reachable': reachable,
        'n_comm': n_comm, 'comm_names': comm_names,
        'scale_names': scale_names, 'scale_capacity': scale_capacity,
        'construct_cost': construct_cost, 'daily_operating': daily_operating,
        'MAX_BUDGET': MAX_BUDGET, 'revenue_per': revenue_per,
        'N5_raw': N5, 'demand_pp': demand_pp, 'cost_per': cost_per,
        'income': income, 'cap_ratio': cap_ratio,
    }


# ============================================================
# 1. S2 满意度：连续线性插值 (修复阶跃振荡)
# ============================================================

def s2_continuous(u):
    """
    S2利用率满意度 — 连续分段线性函数。
    端点对齐旧阶梯 (0.60→1.00, 0.75→0.93, 0.85→0.85, 0.95→0.72, 1.00+→0.50)。
    u=0 时为 1.00。
    """
    if u <= 0.60:
        return 1.00
    elif u <= 0.75:
        return 1.00 - 0.07 * (u - 0.60) / 0.15
    elif u <= 0.85:
        return 0.93 - 0.08 * (u - 0.75) / 0.10
    elif u <= 0.95:
        return 0.85 - 0.13 * (u - 0.85) / 0.10
    else:
        return max(0.50, 0.72 - 0.22 * (u - 0.95) / 0.05)


# ============================================================
# 2. 固定点迭代求解均衡 (连续S2, 无阻尼)
# ============================================================

def solve_equilibrium(config, data, max_iter=250, tol=1e-3):
    """
    求解用户分配均衡。

    算法: 阻尼固定点迭代。若离散分配导致极限环(纯策略Nash均衡不存在),
    则检测周期并用时均利用率(对应混合策略均衡概念)。

    Returns:
        assignments, utils, comm_sats, converged
    """
    n_comm = data['n_comm']
    stations = np.where(config > 0)[0]
    S1 = data['S1']
    reachable = data['reachable']
    daily_demand = data['daily_demand']
    scale_capacity = data['scale_capacity']
    S3 = 1.0

    if len(stations) == 0:
        return (np.full(n_comm, -1, dtype=int), np.zeros(n_comm),
                np.zeros(n_comm), False)

    utils = np.zeros(n_comm)
    damping = 0.12
    UTIL_TOL = 0.008

    util_history = []
    HISTORY_SIZE = 30
    CHECK_INTERVAL = 15

    for iteration in range(max_iter):
        S2_vals = np.array([s2_continuous(utils[s]) for s in range(n_comm)])

        assignments = np.full(n_comm, -1, dtype=int)  # -1=未分配, >=0=站索引
        comm_sats = np.zeros(n_comm)

        for i in range(n_comm):
            best_sat, best_s = 0.0, -1
            for s in stations:
                if reachable[i, s]:
                    sat = 0.2 * S1[i, s] + 0.3 * S2_vals[s] + 0.5 * S3
                    if sat > best_sat + 1e-10:
                        best_sat, best_s = sat, s
            if best_s >= 0:
                assignments[i] = best_s
                comm_sats[i] = best_sat

        new_utils = np.zeros(n_comm)
        for s in stations:
            assigned_demand = daily_demand[assignments == s].sum()
            new_utils[s] = min(1.0, assigned_demand / scale_capacity[config[s] - 1])

        smoothed = damping * new_utils + (1 - damping) * utils
        diff = np.abs(smoothed - utils).max()
        utils = smoothed

        # 记录时均
        util_history.append(utils.copy())
        if len(util_history) > HISTORY_SIZE:
            util_history.pop(0)

        # 周期检测: 每CHECK_INTERVAL步检查时均是否稳定
        if iteration >= HISTORY_SIZE and iteration % CHECK_INTERVAL == 0:
            half = len(util_history) // 2
            avg_first = np.mean(util_history[:half], axis=0)
            avg_second = np.mean(util_history[half:], axis=0)
            drift = np.abs(avg_second - avg_first).max()

            if drift < UTIL_TOL:
                # 时均稳定 → 用后一半的平均作为均衡利用率
                avg_utils = np.mean(util_history[half:], axis=0)

                # 用平均利用率重算最终分配
                S2_final = np.array([s2_continuous(avg_utils[s]) for s in range(n_comm)])
                final_assignments = np.full(n_comm, -1, dtype=int)
                final_sats = np.zeros(n_comm)
                for i in range(n_comm):
                    best_sat, best_s = 0.0, -1
                    for s in stations:
                        if reachable[i, s]:
                            sat = 0.2 * S1[i, s] + 0.3 * S2_final[s] + 0.5 * S3
                            if sat > best_sat + 1e-10:
                                best_sat, best_s = sat, s
                    if best_s >= 0:
                        final_assignments[i] = best_s
                        final_sats[i] = best_sat

                return final_assignments, avg_utils, final_sats, True

        if diff < tol:
            return assignments, utils, comm_sats, True

    # 不收敛但分配可能已稳定 → 用最后状态的时均
    if len(util_history) >= 10:
        avg_utils = np.mean(util_history[-10:], axis=0)
        S2_final = np.array([s2_continuous(avg_utils[s]) for s in range(n_comm)])
        final_assignments = np.zeros(n_comm, dtype=int)
        final_sats = np.zeros(n_comm)
        for i in range(n_comm):
            best_sat, best_s = 0.0, 0
            for s in stations:
                if reachable[i, s]:
                    sat = 0.2 * S1[i, s] + 0.3 * S2_final[s] + 0.5 * S3
                    if sat > best_sat + 1e-10:
                        best_sat, best_s = sat, s
            if best_s > 0:
                final_assignments[i] = best_s
                final_sats[i] = best_sat
        return final_assignments, avg_utils, final_sats, True

    return assignments, utils, comm_sats, False


# ============================================================
# 3. 配置评估 → (覆盖率, 满意度)
# ============================================================

def evaluate_config(config, data):
    """
    评估站点配置。返回 (覆盖率, 满意度, 分配, 利用率, 小区满意度, 实际服务量)。

    覆盖率 = 实际服务老人数 / 总老人数 (非地理覆盖!)
    """
    n_comm = data['n_comm']
    total_cost = sum(data['construct_cost'][c - 1] for c in config if c > 0)

    if total_cost > data['MAX_BUDGET'] or not config.any():
        return 0.0, 0.0, np.zeros(n_comm, dtype=int), np.zeros(n_comm), np.zeros(n_comm), np.zeros(n_comm)

    assignments, utils, comm_sats, _ = solve_equilibrium(config, data)

    stations = np.where(config > 0)[0]
    elderly_total = data['elderly_total']
    total_elderly = data['total_elderly']
    daily_demand = data['daily_demand']
    scale_capacity = data['scale_capacity']

    # 实际服务量 (容量约束, 按比例削减)
    actual_served = np.zeros(n_comm)
    for s in stations:
        idx = np.where(assignments == s)[0]
        if len(idx) == 0:
            continue
        total_assigned = daily_demand[idx].sum()
        capacity = scale_capacity[config[s] - 1]
        if total_assigned > capacity:
            ratio = capacity / total_assigned
            actual_served[idx] = daily_demand[idx] * ratio
        else:
            actual_served[idx] = daily_demand[idx]

    # 覆盖率 = 至少享受一项服务的人数/总人数
    # 站点满员后不可再进人, 容量为硬上限
    # 各站: 实际服务老人 = elderly × min(1, 容量/总需求)
    elderly_served = np.zeros(n_comm)
    for s in stations:
        idx = np.where(assignments == s)[0]
        if len(idx) == 0:
            continue
        total_demand = daily_demand[idx].sum()
        capacity = scale_capacity[config[s] - 1]
        ratio = min(1.0, capacity / total_demand)
        for i in idx:
            elderly_served[i] = ratio * elderly_total[i]
    coverage = elderly_served.sum() / total_elderly

    # 满意度: 按实际服务老人加权 (与覆盖率一致, 只数能进站的人)
    weighted_sat = 0.0
    weighted_total = 0.0
    for i in range(n_comm):
        if assignments[i] >= 0:  # >=0 = 分配到站, -1 = 未分配
            weighted_sat += elderly_served[i] * comm_sats[i]
            weighted_total += elderly_served[i]

    satisfaction = weighted_sat / weighted_total if weighted_total > 0 else 0.0

    return coverage, satisfaction, assignments, utils, comm_sats, actual_served


# ============================================================
# 4. 快速非支配排序 (Fast Non-Dominated Sort)
# ============================================================

def non_dominated_sort(C_vals, S_vals):
    """
    快速非支配排序。返回 list of list: fronts[0] = Pareto前沿(F1)。

    Parameters:
        C_vals: (N,) 覆盖率数组
        S_vals: (N,) 满意度数组

    Returns:
        fronts: list of list of indices
    """
    n = len(C_vals)
    dominated_by = [set() for _ in range(n)]
    dominates_count = [0] * n
    fronts = [[]]

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            # i 支配 j?
            if (C_vals[i] >= C_vals[j] and S_vals[i] >= S_vals[j] and
                    (C_vals[i] > C_vals[j] or S_vals[i] > S_vals[j])):
                dominated_by[i].add(j)
            elif (C_vals[j] >= C_vals[i] and S_vals[j] >= S_vals[i] and
                  (C_vals[j] > C_vals[i] or S_vals[j] > S_vals[i])):
                dominates_count[i] += 1

        if dominates_count[i] == 0:
            fronts[0].append(i)

    front_idx = 0
    while front_idx < len(fronts):
        next_front = []
        for i in fronts[front_idx]:
            for j in dominated_by[i]:
                dominates_count[j] -= 1
                if dominates_count[j] == 0:
                    next_front.append(j)
        if next_front:
            fronts.append(next_front)
        else:
            break
        front_idx += 1

    return fronts


# ============================================================
# 5. 拥挤距离 (Crowding Distance)
# ============================================================

def crowding_distance(front_indices, C_vals, S_vals):
    """
    计算拥挤距离。边界点距离=inf。

    Returns:
        dict: {index: distance}
    """
    n = len(front_indices)
    distances = {i: 0.0 for i in front_indices}

    if n <= 2:
        for i in front_indices:
            distances[i] = float('inf')
        return distances

    # 按覆盖率排序
    sorted_c = sorted(front_indices, key=lambda i: C_vals[i])
    distances[sorted_c[0]] = float('inf')
    distances[sorted_c[-1]] = float('inf')
    c_range = C_vals[sorted_c[-1]] - C_vals[sorted_c[0]]
    if c_range > 1e-12:
        for k in range(1, n - 1):
            d = (C_vals[sorted_c[k + 1]] - C_vals[sorted_c[k - 1]]) / c_range
            distances[sorted_c[k]] += d

    # 按满意度排序
    sorted_s = sorted(front_indices, key=lambda i: S_vals[i])
    distances[sorted_s[0]] = float('inf')
    distances[sorted_s[-1]] = float('inf')
    s_range = S_vals[sorted_s[-1]] - S_vals[sorted_s[0]]
    if s_range > 1e-12:
        for k in range(1, n - 1):
            d = (S_vals[sorted_s[k + 1]] - S_vals[sorted_s[k - 1]]) / s_range
            distances[sorted_s[k]] += d

    return distances


# ============================================================
# 6. GA 算子 (借鉴 math1 的结构)
# ============================================================

def gen_random_config(data):
    """生成预算可行的随机个体"""
    MAX_BUDGET = data['MAX_BUDGET']
    construct_cost = data['construct_cost']
    n_comm = data['n_comm']

    while True:
        cfg = np.random.randint(0, 4, n_comm)
        cost = sum(construct_cost[c - 1] for c in cfg if c > 0)
        if cost <= MAX_BUDGET and cfg.any():
            return cfg


def repair(cfg, data):
    """修复不可行个体 (降级/移除直到满足预算)"""
    MAX_BUDGET = data['MAX_BUDGET']
    construct_cost = data['construct_cost']
    n_comm = data['n_comm']

    total_cost = sum(construct_cost[c - 1] for c in cfg if c > 0)
    stations = np.where(cfg > 0)[0].tolist()

    while total_cost > MAX_BUDGET and stations:
        idx = np.random.choice(stations)
        if cfg[idx] > 1:
            total_cost -= construct_cost[cfg[idx] - 1] - construct_cost[cfg[idx] - 2]
            cfg[idx] -= 1
        else:
            total_cost -= construct_cost[0]
            cfg[idx] = 0
            stations = np.where(cfg > 0)[0].tolist()

    if not cfg.any():
        cfg[np.random.randint(n_comm)] = 1
    return cfg


def tournament_select(pop_indices, C_vals, S_vals, front_rank, crowding, k=5):
    """
    Pareto 锦标赛选择:
    - 不同层: 层号小的胜
    - 同层: 拥挤距离大的胜
    """
    candidates = np.random.choice(pop_indices, k, replace=False)
    best = candidates[0]

    for c in candidates[1:]:
        if front_rank[c] < front_rank[best]:
            best = c
        elif front_rank[c] == front_rank[best]:
            if crowding.get(c, 0.0) > crowding.get(best, 0.0):
                best = c
    return best


# ============================================================
# 7. 主程序
# ============================================================

def main():
    print("=" * 60)
    print("Q2 双目标 Pareto GA — 服务站选址优化 (重写版)")
    print("算法: 非支配排序遗传算法 (NSGA-II风格)")
    print("目标: max 覆盖率, max 满意度 (独立双目标)")
    print("修复: S2连续函数 + 实际服务覆盖率")
    print("=" * 60)

    data = get_data()
    n_comm = data['n_comm']
    comm_names = data['comm_names']
    construct_cost = data['construct_cost']
    scale_capacity = data['scale_capacity']
    scale_names = data['scale_names']
    elderly_total = data['elderly_total']
    daily_demand = data['daily_demand']
    daily_operating = data['daily_operating']
    revenue_per = data['revenue_per']
    monthly_service_demand = data['monthly_service_demand']

    # GA 参数
    POP_SIZE = 80
    N_GEN = 60
    ELITE = 8
    N_RUNS = 3
    TOURNAMENT_K = 5
    CROSSOVER_RATE = 0.8
    MUTATION_RATE = 0.15

    print(f"\n种群={POP_SIZE}, 代数={N_GEN}, 精英={ELITE}, 独立运行={N_RUNS}")
    print(f"Pareto选择: 锦标赛k={TOURNAMENT_K}, 交叉={CROSSOVER_RATE}, 变异={MUTATION_RATE}")

    # ========= 多起点独立运行 =========
    all_C = []
    all_S = []
    all_configs = []
    all_info = []

    t0 = time.time()

    for run in range(N_RUNS):
        seed = run * 137 + 42
        np.random.seed(seed)

        # --- 种群初始化 ---
        pop = np.array([gen_random_config(data) for _ in range(POP_SIZE)])
        C_vals = np.zeros(POP_SIZE)
        S_vals = np.zeros(POP_SIZE)

        for i in range(POP_SIZE):
            C_vals[i], S_vals[i], _, _, _, _ = evaluate_config(pop[i], data)

        for gen in range(N_GEN):
            # 非支配排序
            fronts = non_dominated_sort(C_vals, S_vals)

            # 层号映射
            front_rank = np.full(POP_SIZE, 999)
            for rank, front in enumerate(fronts):
                for idx in front:
                    front_rank[idx] = rank

            # 拥挤距离 (逐层计算)
            crowding = {}
            for front in fronts:
                if len(front) > 0:
                    cd = crowding_distance(front, C_vals, S_vals)
                    crowding.update(cd)

            # 精英选择: 按 (层号, -拥挤距离) 排序取前 ELITE
            pop_order = sorted(
                range(POP_SIZE),
                key=lambda i: (front_rank[i], -crowding.get(i, 0.0))
            )
            elite_indices = pop_order[:ELITE]

            # 生成新一代
            new_pop = np.zeros_like(pop)
            new_pop[:ELITE] = pop[elite_indices]

            # 锦标赛选择 + 交叉 + 变异
            for i in range(ELITE, POP_SIZE):
                p1_idx = tournament_select(
                    list(range(POP_SIZE)), C_vals, S_vals, front_rank, crowding, TOURNAMENT_K)
                p2_idx = tournament_select(
                    list(range(POP_SIZE)), C_vals, S_vals, front_rank, crowding, TOURNAMENT_K)

                p1 = pop[p1_idx]
                p2 = pop[p2_idx]

                # 交叉
                if np.random.rand() < CROSSOVER_RATE:
                    cp = np.random.randint(1, n_comm)
                    child = np.concatenate([p1[:cp], p2[cp:]])
                else:
                    child = p1.copy()

                # 变异
                if np.random.rand() < MUTATION_RATE:
                    child[np.random.randint(n_comm)] = np.random.randint(0, 4)

                new_pop[i] = repair(child, data)

            pop = new_pop

            # 重新评估
            for i in range(POP_SIZE):
                C_vals[i], S_vals[i], _, _, _, _ = evaluate_config(pop[i], data)

        # --- 收集本运行的 Pareto 前沿 ---
        fronts = non_dominated_sort(C_vals, S_vals)
        for idx in fronts[0]:  # F1 = Pareto 前沿
            all_C.append(C_vals[idx])
            all_S.append(S_vals[idx])
            all_configs.append(pop[idx].copy())

        f1_size = len(fronts[0])
        best_c_idx = max(fronts[0], key=lambda i: C_vals[i]) if fronts[0] else 0
        best_s_idx = max(fronts[0], key=lambda i: S_vals[i]) if fronts[0] else 0
        print(f"  Run {run+1}: F1={f1_size}个非支配解, "
              f"最高C={C_vals[best_c_idx]:.4f}, 最高S={S_vals[best_s_idx]:.4f}")

        # 打印一个代表性解
        if fronts[0]:
            rep_idx = sorted(fronts[0], key=lambda i: -(C_vals[i] + S_vals[i]))[0]
            cfg = pop[rep_idx]
            stations = np.where(cfg > 0)[0]
            cost = sum(construct_cost[c - 1] for c in cfg if c > 0)
            s_names = '-'.join(f'{comm_names[s]}({scale_names[cfg[s]-1]})' for s in stations)
            print(f"        代表解: {len(stations)}站 {cost}万 C={C_vals[rep_idx]:.4f} "
                  f"S={S_vals[rep_idx]:.4f} [{s_names}]")

    elapsed = time.time() - t0

    # ========= 合并所有运行的 Pareto 前沿 (去重) =========
    all_C = np.array(all_C)
    all_S = np.array(all_S)
    # 用 (C,S) 对去重
    unique_pairs = {}
    for i in range(len(all_C)):
        key = (round(all_C[i], 6), round(all_S[i], 6))
        if key not in unique_pairs:
            unique_pairs[key] = all_configs[i]

    dedup_C = np.array([k[0] for k in unique_pairs])
    dedup_S = np.array([k[1] for k in unique_pairs])
    dedup_configs = list(unique_pairs.values())

    fronts_final = non_dominated_sort(dedup_C, dedup_S)
    pareto_indices = fronts_final[0]

    pareto_C = dedup_C[pareto_indices]
    pareto_S = dedup_S[pareto_indices]
    pareto_configs = [dedup_configs[i] for i in pareto_indices]

    # 按覆盖率排序
    order = np.argsort(pareto_C)
    pareto_C = pareto_C[order]
    pareto_S = pareto_S[order]
    pareto_configs = [pareto_configs[i] for i in order]

    # ========= 输出 Pareto 前沿 =========
    print(f"\n{'='*60}")
    print(f"双目标优化完成 ({elapsed:.1f}s)")
    print(f"合并后 Pareto 前沿: {len(pareto_indices)} 个非支配解")
    print(f"{'='*60}")
    print(f"\n{'方案':<6} {'站点数':<6} {'成本(万)':<8} {'覆盖率':<8} {'满意度':<8} {'站点详情'}")
    print("-" * 80)

    for pi in range(len(pareto_C)):
        cfg = pareto_configs[pi]
        stations = np.where(cfg > 0)[0]
        n_stations = len(stations)
        cost = sum(construct_cost[c - 1] for c in cfg if c > 0)
        s_detail = ' '.join(f'{comm_names[s]}({scale_names[cfg[s]-1]})' for s in stations)
        print(f"P{pi+1:<5} {n_stations:<6} {cost:<8} {pareto_C[pi]:.4f}   {pareto_S[pi]:.4f}   {s_detail}")

    # ========= 各类最优 =========
    print(f"\n--- 极端点 ---")
    # 最高覆盖率
    best_c_idx = pareto_C.argmax()
    cfg_c = pareto_configs[best_c_idx]
    print(f"最高覆盖率: C={pareto_C[best_c_idx]:.4f}, S={pareto_S[best_c_idx]:.4f}")

    # 最高满意度
    best_s_idx = pareto_S.argmax()
    cfg_s = pareto_configs[best_s_idx]
    print(f"最高满意度: C={pareto_C[best_s_idx]:.4f}, S={pareto_S[best_s_idx]:.4f}")

    # TOPSIS 折中解
    topsis_idx = _topsis_select(pareto_C, pareto_S)
    cfg_topsis = pareto_configs[topsis_idx]
    stations_t = np.where(cfg_topsis > 0)[0]
    print(f"\n--- TOPSIS 推荐折中方案 ---")
    print(f"覆盖率: {pareto_C[topsis_idx]:.4f}")
    print(f"满意度: {pareto_S[topsis_idx]:.4f}")
    cost_t = sum(construct_cost[c - 1] for c in cfg_topsis if c > 0)
    print(f"站点: {len(stations_t)}个, 成本: {cost_t}万")

    # 详细输出推荐方案
    assignments, utils, comm_sats, _ = solve_equilibrium(cfg_topsis, data)
    print(f"\n站点详情:")
    for s in stations_t:
        covered = np.where(assignments == s)[0]
        if len(covered) == 0:
            print(f"  站点 {comm_names[s]} ({scale_names[cfg_topsis[s]-1]}) — ⚠ 空站!")
            continue
        dem = daily_demand[covered].sum()
        cap = scale_capacity[cfg_topsis[s] - 1]
        print(f"  站点 {comm_names[s]} ({scale_names[cfg_topsis[s]-1]}): "
              f"日服务{dem:.0f}/{cap}, util={utils[s]:.3f}, "
              f"覆盖: {' '.join(comm_names[c] for c in covered)}")

    print(f"\n各小区满意度:")
    for i in range(n_comm):
        s = assignments[i]
        if s > 0:
            print(f"  {comm_names[i]}: S_{{{comm_names[i]},{comm_names[s]}}}={comm_sats[i]:.4f} → 站{comm_names[s]} "
                  f"(S1_{{{comm_names[i]},{comm_names[s]}}}={data['S1'][i,s]:.2f} S2_{{{comm_names[s]}}}={s2_continuous(utils[s]):.2f} S3=1.00)")

    # 利润
    print(f"\n年度利润:")
    total_profit = 0
    for s in stations_t:
        covered = np.where(assignments == s)[0]
        if len(covered) == 0:
            continue
        monthly_rev = sum(np.dot(data['monthly_service_demand'][c], revenue_per) for c in covered)
        avg_s = comm_sats[covered].mean()
        annual_rev = monthly_rev * avg_s * 12
        annual_oper = daily_operating[cfg_topsis[s] - 1] * 365
        annual_depr = construct_cost[cfg_topsis[s] - 1] * 10000 / 20
        profit = annual_rev - annual_oper - annual_depr
        total_profit += profit
        print(f"  站点 {comm_names[s]}: {profit:,.0f} 元/年")
    print(f"  总利润: {total_profit:,.0f} 元/年")

    # ========= 保存数据 =========
    save_results(pareto_C, pareto_S, pareto_configs, data)

    return pareto_C, pareto_S, pareto_configs


# ============================================================
# 8. TOPSIS 辅助
# ============================================================

def _topsis_select(C_vals, S_vals):
    """用TOPSIS从Pareto前沿选折中解 (等权重)"""
    n = len(C_vals)
    if n <= 1:
        return 0

    # 归一化
    data_mat = np.column_stack([C_vals, S_vals])
    norm = np.sqrt((data_mat ** 2).sum(axis=0))
    norm[norm == 0] = 1
    Z = data_mat / norm

    # 加权 (等权)
    weights = np.array([0.5, 0.5])
    W = Z * weights

    # 理想解
    ideal_pos = W.max(axis=0)
    ideal_neg = W.min(axis=0)

    # 距离
    d_pos = np.sqrt(((W - ideal_pos) ** 2).sum(axis=1))
    d_neg = np.sqrt(((W - ideal_neg) ** 2).sum(axis=1))

    # 贴近度
    scores = d_neg / (d_pos + d_neg + 1e-12)

    return scores.argmax()


# ============================================================
# 9. 结果保存
# ============================================================

def save_results(pareto_C, pareto_S, pareto_configs, data):
    """保存 Pareto 前沿图表和数据"""
    comm_names = data['comm_names']
    scale_names = data['scale_names']
    construct_cost = data['construct_cost']

    out_dir = os.path.dirname(os.path.abspath(__file__))

    # CSV
    csv_path = os.path.join(out_dir, 'q2_pareto_results_ga.csv')
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write('方案,站点数,成本(万),覆盖率C,满意度S,站点详情\n')
        for i in range(len(pareto_C)):
            cfg = pareto_configs[i]
            stations = np.where(cfg > 0)[0]
            cost = sum(construct_cost[c - 1] for c in cfg if c > 0)
            detail = '-'.join(f'{comm_names[s]}({scale_names[cfg[s]-1]})' for s in stations)
            f.write(f'P{i+1},{len(stations)},{cost},{pareto_C[i]:.6f},{pareto_S[i]:.6f},{detail}\n')
    print(f"\nPareto 数据已保存: {csv_path}")

    # 图
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        fig, ax = plt.subplots(figsize=(10, 7))

        ax.scatter(pareto_C * 100, pareto_S, s=80, c='#0F4D92',
                   edgecolors='white', linewidth=1.5, zorder=5)

        for i in range(len(pareto_C)):
            cfg = pareto_configs[i]
            stations = np.where(cfg > 0)[0]
            n_s = len(stations)
            cost = sum(construct_cost[c - 1] for c in cfg if c > 0)
            ax.annotate(f'P{i+1}\n{n_s}站{cost}万',
                       (pareto_C[i] * 100, pareto_S[i]),
                       fontsize=7, ha='center',
                       color='#272727')

        ax.plot(pareto_C * 100, pareto_S, '--', color='#767676', alpha=0.3, zorder=1)

        ax.set_xlabel('覆盖率 C (%)', fontsize=12)
        ax.set_ylabel('加权满意度 S', fontsize=12)
        ax.set_title('Pareto 前沿: C vs S\n(NSGA-II 双目标Pareto GA)', fontsize=14, fontweight='bold')
        ax.grid(alpha=0.3)

        png_path = os.path.join(out_dir, 'q2_pareto_front_ga.png')
        fig.savefig(png_path, dpi=200, bbox_inches='tight')
        plt.close(fig)
        print(f"Pareto 前沿图已保存: {png_path}")
    except Exception as e:
        print(f"⚠ 图表生成失败: {e}")


# ============================================================
# 入口
# ============================================================

if __name__ == '__main__':
    pareto_C, pareto_S, pareto_configs = main()
