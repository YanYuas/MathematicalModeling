"""
Q2 方案C：分层先后优化 GA
============================
两步修复：
  1. 覆盖率 = 实际服务老人数 / 总老人数（非地理覆盖）
  2. S2 = 连续分段线性插值（非阶跃，根除振荡）

算法：
  第一层：最大化覆盖率 C
  第二层：max 0.6*C + 0.4*S，约束 C >= C_max - 0.01
"""
import numpy as np
import time
import os

# ============================================================
# 0. 数据加载
# ============================================================

N5 = np.array([
    [521, 150, 114], [436, 130, 106], [669, 199, 150],
    [391, 115,  94], [567, 168, 129], [345, 101,  74],
    [626, 185, 142], [413, 123,  91], [533, 159, 120],
    [480, 141, 105]
], dtype=float)

elderly_total = N5.sum(axis=1)
total_elderly = elderly_total.sum()
n_comm = 10
comm_names = list('ABCDEFGHIJ')

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

scale_names = ['小型', '中型', '大型']
scale_capacity = np.array([1000, 2000, 3000])
construct_cost = np.array([18, 32, 45])
daily_operating  = np.array([2000, 3200, 4400])
MAX_BUDGET = 120
reachable = dist <= 1000

# 日需求（消费约束）
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

S3 = 1.0


# ============================================================
# 1. 连续 S2（修复阶跃振荡）
# ============================================================

def s2_continuous(u):
    """连续分段线性 S2，端点对齐旧阶跃值"""
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
# 2. 均衡求解（连续 S2，阻尼固定点 + 时均周期检测）
# ============================================================

def solve_equilibrium(config, max_iter=200, tol=1e-3):
    """返回 (assignments, utils, comm_sats, converged)"""
    stations = np.where(config > 0)[0]
    if len(stations) == 0:
        return np.full(n_comm, -1, dtype=int), np.zeros(n_comm), np.zeros(n_comm), False

    utils = np.zeros(n_comm)
    damping = 0.05
    util_history = []
    HISTORY_SIZE = 60
    CHECK_INTERVAL = 30

    for iteration in range(max_iter):
        S2_vals = np.array([s2_continuous(utils[s]) for s in range(n_comm)])

        assignments = np.full(n_comm, -1, dtype=int)
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

        util_history.append(utils.copy())
        if len(util_history) > HISTORY_SIZE:
            util_history.pop(0)

        if iteration >= HISTORY_SIZE and iteration % CHECK_INTERVAL == 0:
            half = len(util_history) // 2
            avg_first = np.mean(util_history[:half], axis=0)
            avg_second = np.mean(util_history[half:], axis=0)
            drift = np.abs(avg_second - avg_first).max()
            if drift < 0.005:
                avg_utils = np.mean(util_history[half:], axis=0)
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

    if len(util_history) >= 10:
        avg_utils = np.mean(util_history[-10:], axis=0)
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

    return assignments, utils, comm_sats, False


# ============================================================
# 3. 配置评估 → (覆盖率, 满意度)
# ============================================================

def evaluate_config(config):
    """
    返回 (覆盖率, 满意度, 分配, 利用率, 小区满意度, 实际服务量)

    覆盖率 = 实际分配到站并被服务的人数 / 总老人数
    """
    total_cost = sum(construct_cost[c - 1] for c in config if c > 0)

    if total_cost > MAX_BUDGET or not config.any():
        return 0.0, 0.0, np.zeros(n_comm, dtype=int), np.zeros(n_comm), np.zeros(n_comm), np.zeros(n_comm)

    assignments, utils, comm_sats, _ = solve_equilibrium(config)
    stations = np.where(config > 0)[0]

    # 容量削减（仅用于利润计算等，不影响覆盖率和满意度定义）
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

    # 覆盖率 = 实际接受服务人数 / 总老人数（容量约束下实际能服务到的比例）
    elderly_served = np.zeros(n_comm)
    for i in range(n_comm):
        if daily_demand[i] > 0:
            ratio = actual_served[i] / daily_demand[i]
            elderly_served[i] = ratio * elderly_total[i]
    coverage = elderly_served.sum() / total_elderly

    # 加权满意度（仅对实际被服务的小区，按实际服务老人数加权）
    weighted_sat = 0.0
    weighted_total = 0.0
    for i in range(n_comm):
        if elderly_served[i] > 0:
            weighted_sat += elderly_served[i] * comm_sats[i]
            weighted_total += elderly_served[i]
    satisfaction = weighted_sat / weighted_total if weighted_total > 0 else 0.0

    return coverage, satisfaction, assignments, utils, comm_sats, actual_served


# ============================================================
# 4. GA 算子
# ============================================================

def gen_random_config():
    while True:
        cfg = np.random.randint(0, 4, n_comm)
        cost = sum(construct_cost[c - 1] for c in cfg if c > 0)
        if cost <= MAX_BUDGET and cfg.any():
            return cfg


def repair(cfg):
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


def tournament_select(pop, fitness, k=5):
    idx = np.random.choice(len(pop), k, replace=False)
    best = idx[fitness[idx].argmax()]
    return pop[best].copy()


# ============================================================
# 5. 单次分层 GA 运行
# ============================================================

def run_single_ga(seed):
    """方案C：先 max C，再 max 0.6*C + 0.4*S"""
    np.random.seed(seed)

    POP_SIZE = 100
    N_GEN = 60
    ELITE = 10
    CROSSOVER_RATE = 0.8
    MUTATION_RATE = 0.15

    # ---------- 第一层：最大化覆盖率 ----------
    pop = np.array([gen_random_config() for _ in range(POP_SIZE)])
    fitness_cov = np.zeros(POP_SIZE)
    for i in range(POP_SIZE):
        cr, _, _, _, _, _ = evaluate_config(pop[i])
        fitness_cov[i] = cr

    best_cov = fitness_cov.max()
    best_cfg_layer1 = pop[fitness_cov.argmax()].copy()

    for gen in range(1, N_GEN):
        order = fitness_cov.argsort()[::-1]
        new_pop = np.zeros_like(pop)
        new_pop[:ELITE] = pop[order[:ELITE]]
        for i in range(ELITE, POP_SIZE):
            p1 = tournament_select(pop, fitness_cov)
            p2 = tournament_select(pop, fitness_cov)
            if np.random.rand() < CROSSOVER_RATE:
                cp = np.random.randint(1, n_comm)
                child = np.concatenate([p1[:cp], p2[cp:]])
            else:
                child = p1.copy()
            if np.random.rand() < MUTATION_RATE:
                child[np.random.randint(n_comm)] = np.random.randint(0, 4)
            new_pop[i] = repair(child)
        pop = new_pop
        for i in range(POP_SIZE):
            cr, _, _, _, _, _ = evaluate_config(pop[i])
            fitness_cov[i] = cr
        cur = fitness_cov.max()
        if cur > best_cov:
            best_cov = cur
            best_cfg_layer1 = pop[fitness_cov.argmax()].copy()

    max_coverage = best_cov
    TOL = 0.01

    # ---------- 第二层：加权综合，约束 C >= C_max - TOL ----------
    # 用第一层最优解热启动，加速收敛
    pop2 = np.array([gen_random_config() for _ in range(POP_SIZE)])
    pop2[0] = best_cfg_layer1.copy()  # 种子：第一层最优解
    fitness2 = np.zeros(POP_SIZE)
    for i in range(POP_SIZE):
        cr, sat, _, _, _, _ = evaluate_config(pop2[i])
        fit = 0.6 * cr + 0.4 * sat
        if cr >= max_coverage - TOL:
            fitness2[i] = fit
        else:
            fitness2[i] = fit - 0.5 * (max_coverage - cr)

    best_f2 = fitness2.max()
    best_cfg2 = pop2[fitness2.argmax()].copy()

    for gen in range(1, N_GEN):
        order = fitness2.argsort()[::-1]
        new_pop = np.zeros_like(pop2)
        new_pop[:ELITE] = pop2[order[:ELITE]]
        for i in range(ELITE, POP_SIZE):
            p1 = tournament_select(pop2, fitness2)
            p2 = tournament_select(pop2, fitness2)
            if np.random.rand() < CROSSOVER_RATE:
                cp = np.random.randint(1, n_comm)
                child = np.concatenate([p1[:cp], p2[cp:]])
            else:
                child = p1.copy()
            if np.random.rand() < MUTATION_RATE:
                child[np.random.randint(n_comm)] = np.random.randint(0, 4)
            new_pop[i] = repair(child)
        pop2 = new_pop
        for i in range(POP_SIZE):
            cr, sat, _, _, _, _ = evaluate_config(pop2[i])
            fit = 0.6 * cr + 0.4 * sat
            if cr >= max_coverage - TOL:
                fitness2[i] = fit
            else:
                fitness2[i] = fit - 0.5 * (max_coverage - cr)
        cur = fitness2.max()
        if cur > best_f2:
            best_f2 = cur
            best_cfg2 = pop2[fitness2.argmax()].copy()

    cov_final, sat_final, asgn, utils, csats, actual = evaluate_config(best_cfg2)
    return best_cfg2, cov_final, sat_final, asgn, utils, csats, actual, max_coverage


# ============================================================
# 6. 主程序
# ============================================================

def main():
    print("=" * 60)
    print("Q2 方案C：分层先后优化 GA")
    print("修复：连续S2 + 实际服务覆盖率")
    print("目标：第一层 max C，第二层 max 0.6*C + 0.4*S")
    print("=" * 60)

    N_RUNS = 3
    t0 = time.time()

    best_overall_cfg = None
    best_overall_fit = -np.inf
    results = []

    for run in range(N_RUNS):
        cfg, cov, sat, asgn, utils, csats, actual, max_c = run_single_ga(run * 137 + 42)
        fit = 0.6 * cov + 0.4 * sat
        stations = np.where(cfg > 0)[0]
        station_str = '-'.join(comm_names[s] for s in stations)
        cost = sum(construct_cost[c - 1] for c in cfg if c > 0)
        print(f"  Run {run+1}: {len(stations)}站 {cost}万, "
              f"C={cov:.4f}, S={sat:.4f}, F={fit:.4f}, "
              f"maxC={max_c:.4f}, 站点={station_str}")
        results.append((cfg, cov, sat, fit, cost, max_c))
        if fit > best_overall_fit:
            best_overall_fit = fit
            best_overall_cfg = cfg.copy()

    elapsed = time.time() - t0

    # ========== 最优方案详细分析 ==========
    cfg = best_overall_cfg
    cov, sat, assignments, utils, comm_sats, actual = evaluate_config(cfg)
    stations = np.where(cfg > 0)[0]
    total_cost = sum(construct_cost[c - 1] for c in cfg if c > 0)

    print(f"\n{'='*60}")
    print(f"方案C 最优结果 ({elapsed:.1f}s)")
    print(f"{'='*60}")
    print(f"站点数: {len(stations)}")
    print(f"建设成本: {total_cost} 万 / {MAX_BUDGET} 万")
    print(f"覆盖率: {cov:.4f} ({cov*100:.1f}%) — 实际服务/总人数")
    print(f"满意度: {sat:.4f}")
    print(f"适应度: {0.6*cov + 0.4*sat:.4f}")

    print(f"\n站点详情:")
    for s in stations:
        covered = np.where(assignments == s)[0]
        if len(covered) == 0:
            print(f"  站点 {comm_names[s]} ({scale_names[cfg[s]-1]}) — 空站!")
            continue
        dem = daily_demand[covered].sum()
        cap = scale_capacity[cfg[s] - 1]
        print(f"  站点 {comm_names[s]} ({scale_names[cfg[s]-1]}): "
              f"成本{construct_cost[cfg[s]-1]}万, "
              f"日服务{dem:.0f}/{cap}, "
              f"利用率{utils[s]:.4f}, "
              f"覆盖: {' '.join(comm_names[c] for c in covered)}")

    print(f"\n各小区满意度分解:")
    for i in range(n_comm):
        s = assignments[i]
        if s > 0:
            s1 = S1[i, s]
            s2 = s2_continuous(utils[s])
            print(f"  {comm_names[i]}: S={comm_sats[i]:.4f} → 站{comm_names[s]} "
                  f"(S1={s1:.2f} S2={s2:.4f} S3=1.00)")

    # 利润
    print(f"\n年度利润:")
    total_profit = 0
    for s in stations:
        covered = np.where(assignments == s)[0]
        if len(covered) == 0:
            print(f"  站点 {comm_names[s]}: 空站, 无利润")
            continue
        monthly_rev = sum(np.dot(monthly_service_demand[c], revenue_per) for c in covered)
        avg_s = comm_sats[covered].mean()
        annual_rev = monthly_rev * avg_s * 12
        annual_oper = daily_operating[cfg[s] - 1] * 365
        annual_depr = construct_cost[cfg[s] - 1] * 10000 / 20
        profit = annual_rev - annual_oper - annual_depr
        total_profit += profit
        print(f"  站点 {comm_names[s]}: {profit:,.0f} 元/年")
    print(f"  总利润: {total_profit:,.0f} 元/年")

    return cfg, cov, sat, assignments, utils, comm_sats


if __name__ == '__main__':
    cfg, cov, sat, assignments, utils, comm_sats = main()
