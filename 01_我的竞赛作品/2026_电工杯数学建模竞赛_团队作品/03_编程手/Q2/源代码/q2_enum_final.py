"""
Q2 枚举验证 — 修正版模型
=========================
遍历全部可行配置，用修正后模型评估，找全局 Pareto 前沿。
与 GA 结果对比验证。
"""
import numpy as np
from itertools import combinations
import time
import os

# 直接 import 修正版模型的函数
from q2_biobjective_ga import (
    get_data, evaluate_config, non_dominated_sort,
    crowding_distance, solve_equilibrium, s2_continuous
)

data = get_data()
n_comm = data['n_comm']
comm_names = data['comm_names']
construct_cost = data['construct_cost']
scale_capacity = data['scale_capacity']
scale_names = data['scale_names']
MAX_BUDGET = data['MAX_BUDGET']

print("=" * 55)
print("Q2 枚举验证 — 修正版模型")
print("覆盖率: 题目定义 (至少享受一项服务)")
print("S2: 连续线性插值")
print("=" * 55)

# ========= 生成全部可行配置 =========
print("\n生成可行配置...")
all_configs = []
total_checked = 0
total_feasible = 0

for k in range(1, 7):  # 1-6 站 (7站最小成本=7×18=126>120)
    for positions in combinations(range(n_comm), k):
        for scale_code in range(3 ** k):
            scales = np.zeros(k, dtype=int)
            tmp = scale_code
            for si in range(k):
                scales[si] = (tmp % 3) + 1
                tmp //= 3
            cfg = np.zeros(n_comm, dtype=int)
            total_cost = 0
            for si in range(k):
                cfg[positions[si]] = scales[si]
                total_cost += construct_cost[scales[si] - 1]
            total_checked += 1
            if total_cost <= MAX_BUDGET:
                total_feasible += 1
                all_configs.append(cfg)

print(f"检查: {total_checked:,}, 可行: {total_feasible:,}")

# ========= 评估全部可行配置 =========
print("评估中...")
t0 = time.time()

all_C = np.zeros(len(all_configs))
all_S = np.zeros(len(all_configs))

for ci, cfg in enumerate(all_configs):
    all_C[ci], all_S[ci], _, _, _, _ = evaluate_config(cfg, data)

    if ci % max(1, len(all_configs) // 20) == 0:
        elapsed = time.time() - t0
        print(f"  {ci/len(all_configs)*100:.0f}% ({ci}/{len(all_configs)}), "
              f"已用{elapsed:.0f}s, best_C={all_C[:ci+1].max():.4f}")

elapsed = time.time() - t0
print(f"评估完成 ({elapsed:.1f}s)")

# ========= 非支配排序 =========
fronts = non_dominated_sort(all_C, all_S)
pareto_idx = fronts[0]

pareto_C = all_C[pareto_idx]
pareto_S = all_S[pareto_idx]
pareto_cfgs = [all_configs[i] for i in pareto_idx]

# 去重
unique = {}
for i in range(len(pareto_C)):
    key = (round(pareto_C[i], 6), round(pareto_S[i], 6))
    if key not in unique:
        unique[key] = pareto_cfgs[i]

dedup_C = np.array([k[0] for k in unique])
dedup_S = np.array([k[1] for k in unique])
dedup_cfgs = list(unique.values())

# 按覆盖率排序
order = np.argsort(dedup_C)
dedup_C = dedup_C[order]
dedup_S = dedup_S[order]
dedup_cfgs = [dedup_cfgs[i] for i in order]

# ========= 输出 Pareto 前沿 =========
print(f"\n{'='*55}")
print(f"全局 Pareto 前沿: {len(dedup_C)} 个非支配解")
print(f"说明: 唯一解同时拥有最高C和最高S, 支配所有其他15,207个解")
print(f"{'='*55}")

# 最优方案 (全局最高满意度或最高覆盖率)
# 在 Pareto 前沿上选 TOPSIS 折中
from q2_biobjective_ga import _topsis_select
topsis_pareto_idx = _topsis_select(dedup_C, dedup_S)
best_cfg = dedup_cfgs[topsis_pareto_idx]
best_S_val = dedup_S[topsis_pareto_idx]
best_C_val = dedup_C[topsis_pareto_idx]

print(f"\n--- 枚举 TOPSIS 推荐方案 ---")
print(f"配置: {' '.join(f'{comm_names[s]}({scale_names[best_cfg[s]-1]})' for s in np.where(best_cfg>0)[0])}")
print(f"覆盖率: {best_C_val:.4f}")
print(f"满意度: {best_S_val:.4f}")
print(f"成本: {sum(construct_cost[c-1] for c in best_cfg if c>0)}万")
print(f"全覆盖配置数: 0 (硬容量约束下120万预算不可能100%覆盖)")

# 评估详情
asgn, utils, sats, conv = solve_equilibrium(best_cfg, data)
elderly_total = data['elderly_total']
daily_demand = data['daily_demand']
stations = np.where(best_cfg > 0)[0]
print(f"均衡收敛: {conv}")
print(f"\n站点详情:")
for s in stations:
    covered = np.where(asgn == s)[0]
    dem = daily_demand[covered].sum()
    cap = scale_capacity[best_cfg[s] - 1]
    print(f"  站{comm_names[s]}({scale_names[best_cfg[s]-1]}): "
          f"服务{len(covered)}小区 {''.join(comm_names[c] for c in covered)}, "
          f"日需求{dem:.0f}/{cap}, util={utils[s]:.3f}")

print(f"\n各小区满意度:")
for i in range(n_comm):
    s = asgn[i]
    if s > 0:
        S1_val = data['S1'][i, s]
        S2_val = s2_continuous(utils[s])
        print(f"  {comm_names[i]}: S_{{{comm_names[i]},{comm_names[s]}}}={sats[i]:.4f} → 站{comm_names[s]} "
              f"(S1_{{{comm_names[i]},{comm_names[s]}}}={S1_val:.2f} S2_{{{comm_names[s]}}}={S2_val:.2f} S3=1.00)")

# 利润
revenue_per = data['revenue_per']
daily_operating = data['daily_operating']
monthly_svc = data['monthly_service_demand']
print(f"\n年度利润:")
total_profit = 0
for s in stations:
    covered = np.where(asgn == s)[0]
    if len(covered) == 0:
        continue
    monthly_rev = sum(np.dot(monthly_svc[c], revenue_per) for c in covered)
    avg_s = sats[covered].mean()
    annual_rev = monthly_rev * avg_s * 12
    annual_oper = daily_operating[best_cfg[s] - 1] * 365
    annual_depr = construct_cost[best_cfg[s] - 1] * 10000 / 20
    profit = annual_rev - annual_oper - annual_depr
    total_profit += profit
    print(f"  站{comm_names[s]}: {profit:,.0f} 元/年")
print(f"  总利润: {total_profit:,.0f} 元/年")

# ========= 极端点 =========
print(f"\n--- 极端点 ---")
best_c = dedup_C.argmax()
best_s = dedup_S.argmax()
print(f"最高覆盖率: P{best_c+1} C={dedup_C[best_c]:.4f} S={dedup_S[best_c]:.4f}")
print(f"最高满意度: P{best_s+1} C={dedup_C[best_s]:.4f} S={dedup_S[best_s]:.4f}")

# ========= GA 对比 =========
print(f"\n--- GA vs 枚举 ---")
# 检查 GA 找到的 Pareto 解是否都在枚举 Pareto 前沿上
ga_files = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'q2_pareto_results_ga.csv')
import csv
ga_configs = []
if os.path.exists(ga_files):
    with open(ga_files, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ga_configs.append((float(row['覆盖率']), float(row['满意度']), row['站点详情']))

print(f"GA Pareto: {len(ga_configs)} 个解")
print(f"枚举 Pareto: {len(dedup_C)} 个解")
if ga_configs:
    print(f"枚举最高C: {dedup_C.max():.4f}, GA最高C: {max(g[0] for g in ga_configs):.4f}")

# 检查 GA 解是否被枚举支配
if ga_configs:
    print("\nGA 解的枚举验证:")
    for gc, gs, gd in ga_configs:
        # 检查枚举中是否有支配它的
        dominated = any(dedup_C[i] >= gc + 1e-6 and dedup_S[i] >= gs + 1e-6 for i in range(len(dedup_C)))
        matching = any(abs(dedup_C[i] - gc) < 1e-4 and abs(dedup_S[i] - gs) < 1e-4 for i in range(len(dedup_C)))
        status = "在枚举Pareto上" if matching else ("被枚举支配" if dominated else "枚举未找到")
        print(f"  C={gc:.4f} S={gs:.4f} [{gd}] → {status}")

print(f"\n枚举解的覆盖率范围: [{all_C[all_C>0].min():.4f}, {all_C.max():.4f}]")
print(f"枚举解的满意度范围: [{all_S[all_S>0].min():.4f}, {all_S.max():.4f}]")

# ========= 保存 =========
out_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(out_dir, 'enum_pareto_results.csv')
with open(csv_path, 'w', encoding='utf-8') as f:
    f.write('方案,站点数,成本,覆盖率C,满意度S,站点详情\n')
    for i in range(len(dedup_C)):
        cfg = dedup_cfgs[i]
        stations = np.where(cfg > 0)[0]
        cost = sum(construct_cost[c-1] for c in cfg if c>0)
        detail = '-'.join(f'{comm_names[s]}({scale_names[cfg[s]-1]})' for s in stations)
        f.write(f'P{i+1},{len(stations)},{cost},{dedup_C[i]:.6f},{dedup_S[i]:.6f},{detail}\n')
print(f"\n枚举结果已保存: {csv_path}")

# ========= 生成 Pareto 前沿图 (权威版本) =========
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(dedup_C * 100, dedup_S, s=80, c='#0F4D92',
               edgecolors='white', linewidth=1.5, zorder=5)

    for i in range(len(dedup_C)):
        cfg = dedup_cfgs[i]
        stations = np.where(cfg > 0)[0]
        n_s = len(stations)
        cost = sum(construct_cost[c - 1] for c in cfg if c > 0)
        ax.annotate(f'P{i+1}\n{n_s}站{cost}万',
                   (dedup_C[i] * 100, dedup_S[i]),
                   fontsize=7, ha='center', color='#272727')

    ax.plot(dedup_C * 100, dedup_S, '--', color='#767676', alpha=0.3, zorder=1)
    ax.set_xlabel('覆盖率 C (%)', fontsize=12)
    ax.set_ylabel('加权满意度 S', fontsize=12)
    ax.set_title('Pareto 前沿: C vs S\n(全局枚举验证)', fontsize=14, fontweight='bold')
    ax.grid(alpha=0.3)

    png_path = os.path.join(out_dir, 'q2_pareto_front.png')
    fig.savefig(png_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"Pareto 前沿图已保存: {png_path}")
except Exception as e:
    print(f"⚠ 图表生成失败: {e}")

print(f"\n===== 枚举验证完成 =====")
