"""Run Q2 TOPSIS to get optimal config for Q3."""
import sys, os
os.chdir(r'c:\Users\29845\Desktop\电工杯')
sys.path.insert(0, r'c:\Users\29845\Desktop\电工杯')

from q2_biobjective_ga import get_data, evaluate_config, non_dominated_sort, _topsis_select, solve_equilibrium, s2_continuous
import numpy as np

data = get_data()
comm_names = data['comm_names']
scale_names = data['scale_names']
construct_cost = data['construct_cost']

# Read Pareto results and apply TOPSIS
import csv
pareto_C = []
pareto_S = []
pareto_details = []

with open('q2_pareto_results.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        pareto_C.append(float(row['覆盖率']))
        pareto_S.append(float(row['满意度']))
        pareto_details.append(row['站点详情'])

pareto_C = np.array(pareto_C)
pareto_S = np.array(pareto_S)

# TOPSIS
topsis_idx = _topsis_select(pareto_C, pareto_S)
print(f"TOPSIS推荐: P{topsis_idx+1}")
print(f"覆盖率: {pareto_C[topsis_idx]:.4f}")
print(f"满意度: {pareto_S[topsis_idx]:.4f}")
print(f"配置: {pareto_details[topsis_idx]}")

# Parse the config
detail = pareto_details[topsis_idx]
# e.g. "D(中型)-E(中型)-G(小型)-J(中型)"
scale_map = {'小型': 1, '中型': 2, '大型': 3}
cfg = np.zeros(10, dtype=int)
for part in detail.split('-'):
    name = part[0]  # e.g. 'D'
    scale_str = part[2:-1]  # e.g. '中型'
    idx = ord(name) - ord('A')
    cfg[idx] = scale_map[scale_str]

print(f"\n解析配置: {cfg}")
stations = np.where(cfg > 0)[0]
cost = sum(construct_cost[c-1] for c in cfg if c > 0)
print(f"站点数: {len(stations)}, 成本: {cost}万")

# Detailed evaluation
cov, sat, assignments, utils, comm_sats, actual = evaluate_config(cfg, data)
print(f"\n=== Q2最优方案详细信息 ===")
print(f"覆盖率: {cov:.4f} ({cov*100:.1f}%)")
print(f"满意度: {sat:.4f}")

for s in stations:
    covered = np.where(assignments == s)[0]
    dem = data['daily_demand'][covered].sum()
    cap = data['scale_capacity'][cfg[s]-1]
    print(f"  站{comm_names[s]}({scale_names[cfg[s]-1]}): "
          f"容量{cap:.0f}, 日需求{dem:.0f}, util={utils[s]:.3f}, "
          f"覆盖: {' '.join(comm_names[c] for c in covered)}")

print(f"\n各小区分配:")
for i in range(10):
    s = assignments[i]
    print(f"  {comm_names[i]} → 站{comm_names[s] if s>=0 else '无'} "
          f"S1={data['S1'][i,s] if s>=0 else 0:.2f} S2={s2_continuous(utils[s]) if s>=0 else 0:.2f} 满意度={comm_sats[i]:.4f}")

# Print daily demand per community
print(f"\n各小区日需求:")
for i in range(10):
    print(f"  {comm_names[i]}: {data['daily_demand'][i]:.1f} 次/日, 老人{data['elderly_total'][i]:.0f}人")

print(f"\n=== 此配置将作为Q3的输入 ===")
print(f"站点配置: {' '.join(f'{comm_names[s]}({scale_names[cfg[s]-1]})' for s in stations)}")
