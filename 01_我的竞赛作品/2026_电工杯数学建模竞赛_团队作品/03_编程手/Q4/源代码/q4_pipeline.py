"""
Q4 灵敏度分析 — 共享管道函数
===============================
Q1 马尔可夫递推 + Q1.3 需求计算 + Q2 枚举选址 + Q3 枚举定价
所有场景公用此模块

Code location: C:/Users/29845/Desktop/问题4
"""
import numpy as np
import os, sys

# 确保能import Q2的函数
_project_root = r'C:/Users/29845/Desktop/电工杯'
sys.path.insert(0, _project_root)
from q2_biobjective_ga import (s2_continuous, solve_equilibrium, non_dominated_sort, evaluate_config)

# ============================================================
# 数据常量（不随参数变化的）
# ============================================================
COMM_NAMES = list('ABCDEFGHIJ')
SERVICE_NAMES = ['助餐','日间照料','上门护理','康复理疗','助浴','紧急救助']
BASE_PRICE  = np.array([10, 20, 30, 28, 25, 0])
DIRECT_COST = np.array([8, 16, 24, 23, 20, 8])
NON_EMERGENCY = [0, 1, 2, 3, 4]
DEMAND_PP = np.array([
    [14, 20, 22], [8, 14, 18], [0, 6, 12],
    [2, 4, 6], [0, 2, 4], [0.15, 1, 3]
])
INCOME = np.array([3400,3100,3800,2900,3500,2700,3600,3000,3300,3200])
CAP_RATIO = np.array([0.20, 0.25, 0.30])
DIST = np.array([
    [0,600,1200,900,1500,1800,1300,700,1100,500],
    [600,0,800,500,1100,1400,900,400,700,300],
    [1200,800,0,700,600,900,500,900,600,700],
    [900,500,700,0,800,1100,600,300,500,400],
    [1500,1100,600,800,0,500,400,1000,500,800],
    [1800,1400,900,1100,500,0,500,1200,700,1100],
    [1300,900,500,600,400,500,0,800,400,600],
    [700,400,900,300,1000,1200,800,0,600,300],
    [1100,700,600,500,500,700,400,600,0,400],
    [500,300,700,400,800,1100,600,300,400,0],
])
# 原始老人数据
RAW_N0 = np.array([
    [496,152,64],[408,136,64],[632,208,80],[368,120,56],[536,176,72],
    [328,104,40],[592,192,80],[392,128,48],[504,168,64],[456,144,56],
], dtype=float)


# ============================================================
# Q1: 马尔可夫递推
# ============================================================
def run_markov(lam, P_alpha, P_beta, d=0.05, years=5):
    """
    返回 N5: (10, 3) 第5年末各小区三类老人数
    """
    P = np.array([
        [(1-d)*(1-P_alpha)+lam, lam,                  lam     ],
        [(1-d)*P_alpha,          (1-d)*(1-P_beta),    0       ],
        [0,                      (1-d)*P_beta,         (1-d)  ],
    ])
    results = np.zeros((10, 3, years+1), dtype=float)
    for c in range(10):
        N = RAW_N0[c].copy()
        results[c, :, 0] = N
        for t in range(1, years+1):
            N_float = P @ N
            N = np.array([round(N_float[0]), round(N_float[1]), round(N_float[2])])
            results[c, :, t] = N
    return results[:, :, years]  # N5


# ============================================================
# Q1.3: 需求计算 (与Q2 get_data 逻辑一致)
# ============================================================
def compute_demand(N5):
    """返回 daily_demand, monthly_service_demand, elderly_total"""
    n_comm = 10
    monthly_svc = np.zeros((n_comm, 6))
    monthly_total = np.zeros(n_comm)

    for i in range(n_comm):
        caps = INCOME[i] * CAP_RATIO
        for t in range(3):
            n = N5[i, t]
            if n == 0:
                continue
            theo = DEMAND_PP[:, t]
            theo_cost = np.dot(theo, BASE_PRICE)
            if theo_cost <= caps[t]:
                constrained = np.round(n * theo) / n
            else:
                r = caps[t] / theo_cost
                constrained = np.round(theo * r)
                for _ in range(30):
                    if np.dot(constrained, BASE_PRICE) <= caps[t]:
                        break
                    over = (constrained - theo * r) * BASE_PRICE
                    worst = np.argmax(over)
                    if constrained[worst] <= 0:
                        break
                    constrained[worst] -= 1
            monthly_svc[i] += n * constrained
        monthly_total[i] = monthly_svc[i].sum()

    daily_demand = monthly_total / 30
    elderly_total = N5.sum(axis=1)
    return daily_demand, monthly_svc, elderly_total


# ============================================================
# Q2: 枚举选址
# ============================================================
def build_q2_data(N5, cost_mult, budget):
    """构造Q2所需的data字典"""
    daily_demand, monthly_svc, elderly_total = compute_demand(N5)
    total_elderly = elderly_total.sum()
    n_comm = 10
    reachable = DIST <= 1000

    S1 = np.zeros((n_comm, n_comm))
    for i in range(n_comm):
        for j in range(n_comm):
            d = DIST[i, j]
            if d <= 300:       S1[i, j] = 1.00
            elif d <= 500:     S1[i, j] = 0.90
            elif d <= 650:     S1[i, j] = 0.75
            elif d <= 1000:    S1[i, j] = 0.60

    scale_capacity = np.array([1000, 2000, 3000])
    construct_cost = np.array([18, 32, 45])
    daily_operating = np.array([2000, 3200, 4400]) * cost_mult

    return {
        'N5': N5, 'elderly_total': elderly_total, 'total_elderly': total_elderly,
        'daily_demand': daily_demand, 'monthly_service_demand': monthly_svc,
        'dist': DIST, 'S1': S1, 'reachable': reachable,
        'n_comm': n_comm, 'comm_names': COMM_NAMES,
        'scale_names': ['小型','中型','大型'],
        'scale_capacity': scale_capacity,
        'construct_cost': construct_cost,
        'daily_operating': daily_operating,
        'MAX_BUDGET': budget,
        'N5_raw': N5, 'demand_pp': DEMAND_PP,
        'cost_per': np.array([8,16,24,23,20,8]),
        'revenue_per': BASE_PRICE,
        'income': INCOME, 'cap_ratio': CAP_RATIO,
    }


def enumerate_q2(data):
    """枚举全部可行配置, 找TOPSIS最优"""
    from itertools import combinations
    n_comm = data['n_comm']
    construct_cost = data['construct_cost']
    MAX_BUDGET = data['MAX_BUDGET']
    scale_capacity = data['scale_capacity']

    all_configs = []; all_C = []; all_S = []
    max_k = min(6, MAX_BUDGET // 18)
    for k in range(1, max_k + 1):
        for positions in combinations(range(n_comm), k):
            for scale_code in range(3 ** k):
                scales = np.zeros(k, dtype=int)
                tmp = scale_code
                for si in range(k):
                    scales[si] = (tmp % 3) + 1; tmp //= 3
                cfg = np.zeros(n_comm, dtype=int)
                total_cost = 0
                for si in range(k):
                    cfg[positions[si]] = scales[si]
                    total_cost += construct_cost[scales[si] - 1]
                if total_cost <= MAX_BUDGET:
                    all_configs.append(cfg)

    print(f"    枚举: {len(all_configs)} 可行配置")
    for ci, cfg in enumerate(all_configs):
        C, S, _, _, _, _ = evaluate_config(cfg, data)
        all_C.append(C); all_S.append(S)

    all_C = np.array(all_C); all_S = np.array(all_S)
    fronts = non_dominated_sort(all_C, all_S)
    pareto_idx = fronts[0]

    # TOPSIS选最优 (先去重, 与原Q2逻辑一致)
    pareto_C = all_C[pareto_idx]; pareto_S = all_S[pareto_idx]
    pareto_cfgs = [all_configs[i] for i in pareto_idx]

    unique = {}
    for i in range(len(pareto_C)):
        key = (round(pareto_C[i], 6), round(pareto_S[i], 6))
        if key not in unique:
            unique[key] = pareto_cfgs[i]
    dedup_C = np.array([k[0] for k in unique])
    dedup_S = np.array([k[1] for k in unique])
    dedup_cfgs = list(unique.values())
    order = np.argsort(dedup_C)
    dedup_C = dedup_C[order]; dedup_S = dedup_S[order]
    dedup_cfgs = [dedup_cfgs[i] for i in order]

    topsis_idx = _topsis_select(dedup_C, dedup_S)
    best_cfg = dedup_cfgs[topsis_idx]

    stations = np.where(best_cfg > 0)[0]
    cost = sum(construct_cost[c - 1] for c in best_cfg if c > 0)
    cov_final, sat_final, asgn_final, utils_final, csats_final, _ = evaluate_config(best_cfg, data)

    result = {
        'config': best_cfg, 'stations': stations, 'n_stations': len(stations),
        'cost': cost, 'coverage': cov_final, 'satisfaction': sat_final,
        'assignments': asgn_final, 'utils': utils_final, 'comm_sats': csats_final,
        'pareto_C': pareto_C, 'pareto_S': pareto_S,
    }
    return result


def _topsis_select(C, S):
    n = len(C)
    if n <= 1: return 0
    data_mat = np.column_stack([C, S])
    norm = np.sqrt((data_mat ** 2).sum(axis=0)); norm[norm == 0] = 1
    Z = data_mat / norm
    W = Z * np.array([0.5, 0.5])
    ideal_pos = W.max(axis=0); ideal_neg = W.min(axis=0)
    d_pos = np.sqrt(((W - ideal_pos) ** 2).sum(axis=1))
    d_neg = np.sqrt(((W - ideal_neg) ** 2).sum(axis=1))
    scores = d_neg / (d_pos + d_neg + 1e-12)
    return scores.argmax()


# ============================================================
# Q3: 枚举定价
# ============================================================
def s3_to_range(s3_level, base_price):
    if s3_level == 0:     return (base_price * 0.5, base_price)
    elif s3_level == 1:   return (base_price, base_price * 1.10)
    elif s3_level == 2:   return (base_price * 1.10, base_price * 1.20)
    else:                 return (base_price * 1.20, base_price * 2.0)


def compute_station_demand_q3(prices_6, station_communities, data):
    """与Q2需求逻辑一致, 用给定价格"""
    N5 = data['N5_raw']
    monthly_6 = np.zeros(6)
    for ci in station_communities:
        caps = INCOME[ci] * CAP_RATIO
        for t in range(3):
            n = N5[ci, t]
            if n == 0: continue
            theo = DEMAND_PP[:, t]
            theo_cost = np.dot(theo, prices_6)
            if theo_cost <= caps[t]:
                constrained = np.round(n * theo) / n
            else:
                r = caps[t] / theo_cost
                constrained = np.round(theo * r)
                for _ in range(30):
                    if np.dot(constrained, prices_6) <= caps[t]: break
                    over = (constrained - theo * r) * prices_6
                    worst = np.argmax(over)
                    if constrained[worst] <= 0: break
                    constrained[worst] -= 1
            monthly_6 += n * constrained
    daily_6 = monthly_6 / 30
    return daily_6, monthly_6


def compute_station_profit_q3(prices_6, station_communities, data, config, s_idx):
    """计算某站给定定价的利润率和满意度"""
    daily_6_raw, _ = compute_station_demand_q3(prices_6, station_communities, data)
    cap = data['scale_capacity'][config[s_idx] - 1]
    daily_total_raw = daily_6_raw.sum()
    if daily_total_raw > cap:
        daily_6 = daily_6_raw * (cap / daily_total_raw)
    else:
        daily_6 = daily_6_raw.copy()

    effective_total = daily_6.sum()
    utilization = effective_total / cap
    s2 = s2_continuous(utilization)

    s3_vals = np.ones(6)
    for k in range(6):
        bp = BASE_PRICE[k]
        if bp == 0: s3_vals[k] = 1.0
        elif prices_6[k] <= bp: s3_vals[k] = 1.00
        elif prices_6[k] <= bp * 1.10: s3_vals[k] = 0.90
        elif prices_6[k] <= bp * 1.20: s3_vals[k] = 0.75
        else: s3_vals[k] = 0.60

    S1_vals = data['S1'][list(station_communities), s_idx]
    elderly_cov = data['elderly_total'][list(station_communities)]
    comm_sats_local = np.zeros(len(station_communities))
    for i_cover in range(len(station_communities)):
        avg_s3 = np.dot(daily_6, s3_vals) / daily_6.sum() if daily_6.sum() > 0 else 1.0
        comm_sats_local[i_cover] = 0.2 * S1_vals[i_cover] + 0.3 * s2 + 0.5 * avg_s3
    satisfaction = (comm_sats_local * elderly_cov).sum() / elderly_cov.sum() if elderly_cov.sum() > 0 else 0

    daily_revenue = np.dot(daily_6, prices_6)
    daily_direct_cost = np.dot(daily_6, DIRECT_COST)
    subsidy_caps = {1: 1000, 2: 1800, 3: 2600}
    daily_subsidy_raw = daily_6[NON_EMERGENCY].sum() * 2.0
    daily_subsidy = min(daily_subsidy_raw, subsidy_caps[config[s_idx]])

    annual_revenue = daily_revenue * 365
    annual_subsidy = daily_subsidy * 365
    annual_direct = daily_direct_cost * 365
    annual_oper = data['daily_operating'][config[s_idx] - 1] * 365
    annual_depr = data['construct_cost'][config[s_idx] - 1] * 10000 / 20
    gross = annual_revenue - annual_direct
    total_cost = annual_oper + annual_depr
    profit_rate = (gross + annual_subsidy - total_cost) / total_cost
    return profit_rate, satisfaction, s3_vals, daily_subsidy, effective_total, utilization, daily_6


def generate_s3_combos():
    combos = []
    for code in range(4 ** 5):
        combo = np.zeros(5, dtype=int)
        tmp = code
        for k in range(5): combo[k] = tmp % 4; tmp //= 4
        combos.append(combo)
    return combos


S3_COMBOS_ALL = generate_s3_combos()


def optimize_q3_pricing(q2_result, data):
    """逐站枚举定价: 全平价最优"""
    config = q2_result['config']
    stations = q2_result['stations']
    assignments = q2_result['assignments']

    station_communities = {}
    for s in stations:
        station_communities[s] = np.where(assignments == s)[0]

    results = {}
    for s in stations:
        best = {'satisfaction': 0}
        for combo in S3_COMBOS_ALL:
            lo_prices = np.zeros(6); hi_prices = np.zeros(6)
            for k in range(5):
                lo_prices[k], hi_prices[k] = s3_to_range(combo[k], BASE_PRICE[k])
            lo_prices[5] = hi_prices[5] = 0

            pr_lo, _, _, _, _, _, _ = compute_station_profit_q3(lo_prices, station_communities[s], data, config, s)
            pr_hi, _, _, _, _, _, _ = compute_station_profit_q3(hi_prices, station_communities[s], data, config, s)
            if pr_lo > 0.08 or pr_hi < 0: continue

            lo, hi = 0.0, 1.0
            best_p_local = None
            for _ in range(40):
                mid = (lo + hi) / 2
                mp = lo_prices + mid * (hi_prices - lo_prices); mp[5] = 0
                pr_m, _, _, _, _, _, _ = compute_station_profit_q3(mp, station_communities[s], data, config, s)
                if pr_m > 0.08: hi = mid
                elif pr_m < 0: lo = mid
                else: best_p_local = mp.copy(); hi = mid  # 追最低价

            if best_p_local is not None:
                pr_f, sat_f, s3_f, sub_f, eff_f, util_f, d6 = \
                    compute_station_profit_q3(best_p_local, station_communities[s], data, config, s)
                if sat_f > best['satisfaction']:
                    best.update({'s3_combo': combo, 'prices': best_p_local.copy(),
                                 'profit_rate': pr_f, 'satisfaction': sat_f,
                                 's3_vals': s3_f, 'daily_subsidy': sub_f,
                                 'effective_total': eff_f, 'utilization': util_f})
        results[s] = best

    return results, station_communities
