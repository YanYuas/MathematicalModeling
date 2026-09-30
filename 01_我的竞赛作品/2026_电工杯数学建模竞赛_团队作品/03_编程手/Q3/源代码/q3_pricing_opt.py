"""
Q3 服务定价与政府补贴优化 — 逐站枚举 + 二分搜索
================================================
目标: max 老人满意度
约束: 0 ≤ 利润率 ≤ 8%
假定: 服务人次无跨站关联 (定价变化不改变小区分配)
算法: 每站枚举4^5=1024种S3组合, 二分搜索精确定价
"""
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from q2_biobjective_ga import get_data, solve_equilibrium, s2_continuous

data = get_data()
comm_names = data['comm_names']
scale_names = data['scale_names']
scale_capacity = data['scale_capacity']
construct_cost = data['construct_cost']
daily_operating = data['daily_operating']
elderly_total = data['elderly_total']

# Q2 最优方案 (枚举全局最优)
BEST_CONFIG = np.zeros(10, dtype=int)
BEST_CONFIG[2] = 2  # C 中型
BEST_CONFIG[3] = 2  # D 中型
BEST_CONFIG[6] = 3  # G 大型

assignments, utils_q2, comm_sats_q2, _ = solve_equilibrium(BEST_CONFIG, data)
STATIONS = np.where(BEST_CONFIG > 0)[0]

SERVICE_NAMES = ['助餐','日间照料','上门护理','康复理疗','助浴','紧急救助']
BASE_PRICE  = np.array([10, 20, 30, 28, 25, 0])
DIRECT_COST = np.array([8, 16, 24, 23, 20, 8])
NON_EMERGENCY = [0, 1, 2, 3, 4]

station_communities = {}
for s in STATIONS:
    station_communities[s] = np.where(assignments == s)[0]

print("=" * 65)
print("Q3 逐站枚举 + 二分搜索 — 服务定价优化")
print(f"Q2最优方案: {len(STATIONS)}站 成本={sum(construct_cost[c-1] for c in BEST_CONFIG if c>0)}万")
for s in STATIONS:
    covered = station_communities[s]
    print(f"  站{comm_names[s]}({scale_names[BEST_CONFIG[s]-1]}): "
          f"覆盖{len(covered)}小区 {''.join(comm_names[c] for c in covered)}, "
          f"Q2利用率={utils_q2[s]:.3f}")
print(f"假定: 定价变化不改变小区分配")


# ============================================================
# 1. 需求计算 — 与 Q2 的 get_data() 完全一致
# ============================================================

def compute_station_demand(prices_6, station_idx):
    """与Q2逻辑完全一致, 仅价格变量不同"""
    covered = station_communities[station_idx]
    N5 = data['N5_raw']
    inc = data['income']
    cap_ratio = data['cap_ratio']
    demand_pp = data['demand_pp']

    monthly_6 = np.zeros(6)

    for ci in covered:
        caps = inc[ci] * cap_ratio
        for t in range(3):
            n = N5[ci, t]
            if n == 0:
                continue
            theo = demand_pp[:, t]
            theo_cost = np.dot(theo, prices_6)

            if theo_cost <= caps[t]:
                # 匹配Q2取整: round(总量)/n→每人→×n = round(总量)
                constrained = np.round(n * theo) / n
            else:
                r = caps[t] / theo_cost
                constrained = np.round(theo * r)
                for _ in range(30):
                    if np.dot(constrained, prices_6) <= caps[t]:
                        break
                    over = (constrained - theo * r) * prices_6
                    worst = np.argmax(over)
                    if constrained[worst] <= 0:
                        break
                    constrained[worst] -= 1
            monthly_6 += n * constrained

    daily_6 = monthly_6 / 30
    return daily_6, monthly_6


# ============================================================
# 2. 利润+满意度计算
# ============================================================

def compute_station_profit(prices_6, station_idx):
    s = station_idx
    covered = station_communities[s]
    daily_6_raw, _ = compute_station_demand(prices_6, station_idx)

    # 容量截断
    cap = scale_capacity[BEST_CONFIG[s] - 1]
    daily_total_raw = daily_6_raw.sum()
    if daily_total_raw > cap:
        daily_6 = daily_6_raw * (cap / daily_total_raw)
    else:
        daily_6 = daily_6_raw.copy()

    effective_total = daily_6.sum()
    utilization = effective_total / cap
    s2 = s2_continuous(utilization)

    # S3
    s3_vals = np.ones(6)
    for k in range(6):
        bp = BASE_PRICE[k]
        if bp == 0:
            s3_vals[k] = 1.0
        elif prices_6[k] <= bp:
            s3_vals[k] = 1.00
        elif prices_6[k] <= bp * 1.10:
            s3_vals[k] = 0.90
        elif prices_6[k] <= bp * 1.20:
            s3_vals[k] = 0.75
        else:
            s3_vals[k] = 0.60

    # S1
    S1_vals = data['S1'][covered, s]

    # 各小区满意度
    comm_sats_local = np.zeros(len(covered))
    for i_cover, ci in enumerate(covered):
        total_d = daily_6.sum()
        avg_s3 = np.dot(daily_6, s3_vals) / total_d if total_d > 0 else 1.0
        comm_sats_local[i_cover] = 0.2 * S1_vals[i_cover] + 0.3 * s2 + 0.5 * avg_s3

    elderly_cov = data['elderly_total'][covered]
    satisfaction = (comm_sats_local * elderly_cov).sum() / elderly_cov.sum() if elderly_cov.sum() > 0 else 0

    # 利润
    daily_revenue = np.dot(daily_6, prices_6)
    daily_direct_cost = np.dot(daily_6, DIRECT_COST)

    subsidy_caps = {1: 1000, 2: 1800, 3: 2600}
    daily_subsidy_raw = daily_6[NON_EMERGENCY].sum() * 2.0
    daily_subsidy = min(daily_subsidy_raw, subsidy_caps[BEST_CONFIG[s]])

    annual_revenue = daily_revenue * 365
    annual_subsidy = daily_subsidy * 365
    annual_direct_cost = daily_direct_cost * 365
    annual_fixed_oper = daily_operating[BEST_CONFIG[s] - 1] * 365
    annual_depr = construct_cost[BEST_CONFIG[s] - 1] * 10000 / 20

    gross_profit = annual_revenue - annual_direct_cost
    total_oper_cost = annual_fixed_oper + annual_depr
    profit_rate = (gross_profit + annual_subsidy - total_oper_cost) / total_oper_cost

    return profit_rate, satisfaction, s3_vals, daily_subsidy, effective_total, utilization, daily_6


# ============================================================
# 3. S3档位枚举 + 价格区间
# ============================================================

S3_COMBOS = []
for code in range(4 ** 5):
    combo = np.zeros(5, dtype=int)
    tmp = code
    for k in range(5):
        combo[k] = tmp % 4
        tmp //= 4
    S3_COMBOS.append(combo)


def s3_to_range(s3_level, base_price):
    if s3_level == 0:
        return (base_price * 0.5, base_price)
    elif s3_level == 1:
        return (base_price, base_price * 1.10)
    elif s3_level == 2:
        return (base_price * 1.10, base_price * 1.20)
    else:
        return (base_price * 1.20, base_price * 2.0)


# ============================================================
# 4. 逐站枚举优化
# ============================================================

def optimize_station(s, verbose=True):
    best = {'s3_combo': None, 'prices': None, 'profit_rate': None,
            'satisfaction': 0, 'utilization': 0, 'daily_subsidy': 0,
            'effective_total': 0, 's3_vals': None}

    feasible_count = 0

    for combo in S3_COMBOS:
        lo_prices, hi_prices = np.zeros(6), np.zeros(6)
        for k in range(5):
            lo_prices[k], hi_prices[k] = s3_to_range(combo[k], BASE_PRICE[k])
        lo_prices[5] = hi_prices[5] = 0

        pr_lo, sat_lo, *_ = compute_station_profit(lo_prices, s)
        pr_hi, sat_hi, *_ = compute_station_profit(hi_prices, s)

        if pr_lo > 0.08 or pr_hi < 0:
            continue  # 不可行

        feasible_count += 1

        # 二分搜索: 在可行利润率 [0, 8%] 内找最高利润率 (=8%)
        # 理由: S3同档内满意不变, 取利润最高(同满意但更可持续)
        lo, hi = 0.0, 1.0
        best_price_local = None
        best_pr_local = None

        for _ in range(45):
            mid = (lo + hi) / 2
            mid_prices = lo_prices + mid * (hi_prices - lo_prices)
            mid_prices[5] = 0
            pr_mid, sat_mid, _, _, _, _, _ = compute_station_profit(mid_prices, s)

            if pr_mid > 0.08:
                hi = mid  # 利润率超上限, 降价
            elif pr_mid < 0:
                lo = mid  # 亏损, 涨价
            else:
                # 可行 [0, 8%], 降价追最低利润率 (价格↓=满意↑)
                best_price_local = mid_prices.copy()
                best_pr_local = pr_mid
                hi = mid  # 降价→利润率↓→满意↑

        if best_price_local is not None:
            pr_final, sat_final, s3_final, sub_final, eff_final, util_final, _ = \
                compute_station_profit(best_price_local, s)
            if sat_final > best['satisfaction']:
                best.update({
                    's3_combo': combo, 'prices': best_price_local.copy(),
                    'profit_rate': pr_final, 'satisfaction': sat_final,
                    'utilization': util_final, 'daily_subsidy': sub_final,
                    'effective_total': eff_final, 's3_vals': s3_final,
                })

    if verbose and best['prices'] is not None:
        print(f"\n站{comm_names[s]}({scale_names[BEST_CONFIG[s]-1]}): "
              f"枚举{len(S3_COMBOS)}种, 可行{feasible_count}种")
        print(f"  最优S3档位: {best['s3_combo']}")
        price_str = ' '.join(f'{SERVICE_NAMES[k]}={best["prices"][k]:.2f}' for k in range(5))
        print(f"  最优定价: {price_str}")
        print(f"  利润率={best['profit_rate']*100:.2f}%, "
              f"满意度={best['satisfaction']:.4f}, "
              f"利用率={best['utilization']:.3f}")

    return best


# ============================================================
# 5. 主程序
# ============================================================

def main():
    results = {}
    total_revenue = 0
    total_subsidy = 0
    total_oper_cost = 0
    total_profit = 0

    for s in [2, 3, 6]:  # C, D, G
        res = optimize_station(s)
        results[s] = res

        p = res['prices']
        daily_6, daily_total = compute_station_profit(p, s)[6], compute_station_profit(p, s)[4]
        annual_rev = np.dot(daily_6, p) * 365
        annual_direct = np.dot(daily_6, DIRECT_COST) * 365
        annual_oper = daily_operating[BEST_CONFIG[s] - 1] * 365
        annual_depr = construct_cost[BEST_CONFIG[s] - 1] * 10000 / 20

        total_revenue += annual_rev
        total_subsidy += res['daily_subsidy'] * 365
        total_oper_cost += annual_oper + annual_depr
        total_profit += annual_rev - annual_direct + res['daily_subsidy'] * 365 - annual_oper - annual_depr

    overall_pr = total_profit / total_oper_cost if total_oper_cost > 0 else 0

    print(f"\n{'='*65}")
    print(f"Q3 优化结果汇总")
    print(f"{'='*65}")

    for s in [2, 3, 6]:
        r = results[s]
        cov = station_communities[s]
        print(f"\n站{comm_names[s]}({scale_names[BEST_CONFIG[s]-1]}) — "
              f"覆盖: {''.join(comm_names[c] for c in cov)}")
        print(f"  定价: ", end="")
        for k in range(5):
            lbl = ['平价','微涨≤10%','上涨10-20%','高价>20%'][r['s3_combo'][k]]
            print(f"{SERVICE_NAMES[k]}={r['prices'][k]:.2f}({lbl})", end="  ")
        print(f"\n  紧急救助: 免费")
        print(f"  利润率: {r['profit_rate']*100:.2f}%")
        print(f"  满意度: {r['satisfaction']:.4f}")
        print(f"  利用率: {r['utilization']:.3f}")
        print(f"  日均补贴: {r['daily_subsidy']:.0f}元")
        print(f"  日有效服务: {r['effective_total']:.0f}人次")

    print(f"\n--- 汇总 ---")
    print(f"  总利润率: {overall_pr*100:.2f}%")
    print(f"  年总收入: {total_revenue:,.0f}元")
    print(f"  年补贴: {total_subsidy:,.0f}元")
    print(f"  年运营总成本: {total_oper_cost:,.0f}元")
    print(f"  年总利润: {total_profit:,.0f}元")

    # 全区域满意度
    all_sats, all_weights = [], []
    for s in [2, 3, 6]:
        cov = station_communities[s]
        _, _, s3_v, _, eff, util, d6 = compute_station_profit(results[s]['prices'], s)
        s2 = s2_continuous(util) if util > 0 else 1.0
        for ci in cov:
            s1 = data['S1'][ci, s]
            avg_s3 = np.dot(d6, s3_v) / d6.sum() if d6.sum() > 0 else 1.0
            all_sats.append(0.2 * s1 + 0.3 * s2 + 0.5 * avg_s3)
            all_weights.append(elderly_total[ci])

    overall_sat = np.average(all_sats, weights=all_weights)
    print(f"  全区域加权满意度: {overall_sat:.4f}")

    # ============================================================
    # Q3.2 详细输出: 每站年度利润+利润率, 小区满意度, 价格满意度
    # ============================================================
    print(f"\n{'='*65}")
    print(f"Q3.2 详细结果")
    print(f"{'='*65}")

    for s in [2, 3, 6]:
        r = results[s]
        cov = station_communities[s]
        _, _, s3_v, sub, eff, util_v, d6 = compute_station_profit(r['prices'], s)

        annual_oper = daily_operating[BEST_CONFIG[s] - 1] * 365
        annual_depr = construct_cost[BEST_CONFIG[s] - 1] * 10000 / 20
        annual_rev = np.dot(d6, r['prices']) * 365
        annual_direct = np.dot(d6, DIRECT_COST) * 365
        gross_profit = annual_rev - annual_direct
        annual_subsidy = sub * 365
        total_cost = annual_oper + annual_depr
        net_profit = gross_profit + annual_subsidy - total_cost
        pr = net_profit / total_cost

        print(f"\n站{comm_names[s]}({scale_names[BEST_CONFIG[s]-1]}):")
        print(f"  年服务收入: {annual_rev:,.0f}元")
        print(f"  年直接支出: {annual_direct:,.0f}元")
        print(f"  年毛利润: {gross_profit:,.0f}元")
        print(f"  年政府补贴: {annual_subsidy:,.0f}元")
        print(f"  年固定运营成本: {annual_oper:,.0f}元")
        print(f"  年折旧: {annual_depr:,.0f}元")
        print(f"  年净利润: {net_profit:,.0f}元")
        print(f"  利润率: {pr*100:.2f}%")

        s2_v = s2_continuous(util_v) if util_v > 0 else 1.0
        print(f"\n  各小区满意度得分:")
        for ci in cov:
            s1 = data['S1'][ci, s]
            avg_s3 = np.dot(d6, s3_v) / d6.sum() if d6.sum() > 0 else 1.0
            sat = 0.2 * s1 + 0.3 * s2_v + 0.5 * avg_s3
            price_sat = avg_s3  # 价格满意度 = 加权S3
            print(f"    {comm_names[ci]}: S_{{{comm_names[ci]},{comm_names[s]}}}={sat:.4f} "
                  f"(S1_{{{comm_names[ci]},{comm_names[s]}}}={s1:.2f}, S2_{{{comm_names[s]}}}={s2_v:.4f}, "
                  f"S3(价格)={price_sat:.4f})")

    # ============================================================
    # Q3.3 不同类型老人可及性分析
    # ============================================================
    print(f"\n{'='*65}")
    print(f"Q3.3 定价与补贴对不同类型老人可及性的影响")
    print(f"{'='*65}")

    # 计算全区域不同类型老人的可及性指标
    N5_raw = data['N5_raw']
    type_names = ['自理', '半失能', '失能']
    cap_ratio_v = data['cap_ratio']

    for t in range(3):
        total_t = N5_raw[:, t].sum()
        print(f"\n[{type_names[t]}] 全区域共{total_t:.0f}人")

        # 平均月消费上限
        avg_cap = np.dot(N5_raw[:, t], data['income'] * cap_ratio_v[t]) / total_t
        print(f"  平均月消费上限: {avg_cap:.0f}元")

        # 新定价下的月消费 vs 上限
        affordable_all = 0
        unaffordable_all = 0
        for s in [2, 3, 6]:
            prices_s = results[s]['prices']
            cov = station_communities[s]
            for ci in cov:
                n_t = N5_raw[ci, t]
                if n_t == 0:
                    continue
                theo = data['demand_pp'][:, t]
                theo_cost = np.dot(theo, prices_s)
                if theo_cost <= data['income'][ci] * cap_ratio_v[t]:
                    affordable_all += n_t
                else:
                    r = data['income'][ci] * cap_ratio_v[t] / theo_cost
                    unaffordable_all += n_t * (1 - r)  # 无法满足的比例

        pct_affordable = affordable_all / total_t * 100
        print(f"  完全可负担人数: {affordable_all:.0f} ({pct_affordable:.1f}%)")

        # 实际需求满足率
        total_theo_demand = 0
        total_actual_demand = 0
        for s in [2, 3, 6]:
            prices_s = results[s]['prices']
            cov = station_communities[s]
            for ci in cov:
                n_t = N5_raw[ci, t]
                if n_t == 0:
                    continue
                theo = data['demand_pp'][:, t]
                theo_sum = theo.sum()
                theo_cost = np.dot(theo, prices_s)
                total_theo_demand += n_t * theo_sum
                if theo_cost <= data['income'][ci] * cap_ratio_v[t]:
                    total_actual_demand += n_t * theo_sum
                else:
                    r = data['income'][ci] * cap_ratio_v[t] / theo_cost
                    constrained = np.round(theo * r)
                    for _ in range(30):
                        if np.dot(constrained, prices_s) <= data['income'][ci] * cap_ratio_v[t]:
                            break
                        over = (constrained - theo * r) * prices_s
                        worst = np.argmax(over)
                        if constrained[worst] <= 0:
                            break
                        constrained[worst] -= 1
                    total_actual_demand += n_t * constrained.sum()

        fulfill_rate = total_actual_demand / total_theo_demand * 100 if total_theo_demand > 0 else 0
        print(f"  需求满足率: {fulfill_rate:.1f}% ({total_actual_demand:.0f}/{total_theo_demand:.0f} 次/月)")

        # 政府补贴覆盖
        subsidy_per_person = 2.0 * total_actual_demand / 30 / total_t  # 元/人/日
        print(f"  人均补贴: {subsidy_per_person:.2f}元/日")

    print(f"\n===== Q3 全部完成 =====")

    # CSV
    out_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(out_dir, 'q3_results.csv')
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write('站点,规模,服务,P_k(基准价),最优定价,S3档位,利润率,S(满意度),U_j(利用率),日均补贴\n')
        for s in [2, 3, 6]:
            r = results[s]
            for k in range(5):
                lbl = ['平价','微涨≤10%','上涨10-20%','高价>20%'][r['s3_combo'][k]]
                f.write(f'{comm_names[s]},{scale_names[BEST_CONFIG[s]-1]},'
                       f'{SERVICE_NAMES[k]},{BASE_PRICE[k]},{r["prices"][k]:.2f},'
                       f'{lbl},{r["profit_rate"]*100:.2f}%,{r["satisfaction"]:.4f},'
                       f'{r["utilization"]:.3f},{r["daily_subsidy"]:.0f}\n')
            f.write(f'{comm_names[s]},{scale_names[BEST_CONFIG[s]-1]},'
                   f'紧急救助,0,0,公益免费,,,,,\n')
        f.write(f'\n汇总,,全区域加权满意度,{overall_sat:.4f},,,,,\n')
        f.write(f'汇总,,总利润率,{overall_pr*100:.2f}%,,,,,\n')
    print(f"\n结果已保存: {csv_path}")

    return results


if __name__ == '__main__':
    results = main()
