"""
Q4 基线 — 复用Q2原始get_data(), 保证精确复现
===================================================

Code location: C:/Users/29845/Desktop/问题4
"""
import numpy as np
import os, sys, json
sys.path.insert(0, r'C:/Users/29845/Desktop/电工杯')
sys.path.insert(0, r'C:/Users/29845/Desktop/问题4')
from q2_biobjective_ga import get_data
from q4_pipeline import enumerate_q2, optimize_q3_pricing, COMM_NAMES, SERVICE_NAMES

data = get_data()
N5 = data['N5_raw']

print("=" * 60)
print("Q4 基线 (直接复用Q2原始get_data)")
print(f"N5总老人={N5.sum():.0f}, 预算={data['MAX_BUDGET']}万, 成本×1.0")
print("=" * 60)

q2_result = enumerate_q2(data)
print(f"\nQ2: {q2_result['n_stations']}站 成本={q2_result['cost']}万 "
      f"C={q2_result['coverage']:.4f} S={q2_result['satisfaction']:.4f}")

for s in q2_result['stations']:
    cov = np.where(q2_result['assignments'] == s)[0]
    print(f"  站{COMM_NAMES[s]}({data['scale_names'][q2_result['config'][s]-1]}): "
          f"{','.join(COMM_NAMES[c] for c in cov)}, util={q2_result['utils'][s]:.3f}")

q3_results, sc = optimize_q3_pricing(q2_result, data)
print(f"\nQ3 最优定价:")
for s in q2_result['stations']:
    r = q3_results[s]
    pstr = ' '.join(f'{SERVICE_NAMES[k]}={r["prices"][k]:.2f}' for k in range(5))
    print(f"  站{COMM_NAMES[s]}: {pstr}, S3={r['s3_combo']}, "
          f"pr={r['profit_rate']*100:.2f}%, sat={r['satisfaction']:.4f}")

out_dir = r'C:/Users/29845/Desktop/问题4'
result_data = {
    'scenario': '基线',
    'params': {'lam': 0.07, 'P_alpha': 0.045, 'P_beta': 0.10, 'cost_mult': 1.0, 'budget': 120},
    'N5_total': float(N5.sum()),
    'q2': {
        'n_stations': int(q2_result['n_stations']),
        'cost': int(q2_result['cost']),
        'coverage': float(q2_result['coverage']),
        'satisfaction': float(q2_result['satisfaction']),
        'stations': [{'name': COMM_NAMES[s], 'scale': data['scale_names'][q2_result['config'][s]-1],
                       'covers': ','.join(COMM_NAMES[c] for c in np.where(q2_result['assignments']==s)[0]),
                       'utilization': float(q2_result['utils'][s])} for s in q2_result['stations']],
    },
    'q3': {COMM_NAMES[s]: {
        'prices': {SERVICE_NAMES[k]: float(q3_results[s]['prices'][k]) for k in range(5)},
        's3_combo': [int(x) for x in q3_results[s]['s3_combo']],
        'profit_rate': float(q3_results[s]['profit_rate']),
        'satisfaction': float(q3_results[s]['satisfaction']),
        'daily_subsidy': float(q3_results[s]['daily_subsidy']),
    } for s in q2_result['stations']}
}

with open(os.path.join(out_dir, 'baseline_result.json'), 'w', encoding='utf-8') as f:
    json.dump(result_data, f, ensure_ascii=False, indent=2)
print(f"\n基线结果已保存: {out_dir}/baseline_result.json")
