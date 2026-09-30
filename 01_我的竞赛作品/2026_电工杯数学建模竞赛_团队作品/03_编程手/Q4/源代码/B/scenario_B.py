"""
Q4 场景B — 成本变化
=======================
λ=7%, Pα=0.045, Pβ=0.10, 日固定成本+20%, 预算=120万

Code location: C:/Users/29845/Desktop/问题4
"""
import numpy as np
import os, sys, json
sys.path.insert(0, r'C:/Users/29845/Desktop/电工杯')
sys.path.insert(0, r'C:/Users/29845/Desktop/问题4')
from q2_biobjective_ga import get_data as get_q2_data
from q4_pipeline import build_q2_data, enumerate_q2, optimize_q3_pricing, COMM_NAMES, SERVICE_NAMES

COST_MULT = 1.2; BUDGET = 120

print("=" * 60)
print("Q4 场景B — 成本变化 (日固定成本+20%)")
print(f"成本×{COST_MULT}, 预算={BUDGET}万, 人口=原")
print("=" * 60)

# 复用原N5, 只改成本
orig_data = get_q2_data()
N5 = orig_data['N5_raw']
print(f"\nQ1: 第5年末总老人数 = {N5.sum():.0f} (与基线相同)")

data = build_q2_data(N5, COST_MULT, BUDGET)
q2_result = enumerate_q2(data)
print(f"Q2: {q2_result['n_stations']}站 成本={q2_result['cost']}万 "
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

# Save
out_dir = r'C:/Users/29845/Desktop/问题4\B'
os.makedirs(out_dir, exist_ok=True)
result_data = {
    'scenario': 'B_成本变化',
    'params': {'lam': LAM, 'P_alpha': P_ALPHA, 'P_beta': P_BETA, 'cost_mult': COST_MULT, 'budget': BUDGET},
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
    'q3': {}
}
for s in q2_result['stations']:
    r = q3_results[s]
    result_data['q3'][COMM_NAMES[s]] = {
        'prices': {SERVICE_NAMES[k]: float(r['prices'][k]) for k in range(5)},
        's3_combo': [int(x) for x in r['s3_combo']],
        'profit_rate': float(r['profit_rate']),
        'satisfaction': float(r['satisfaction']),
        'daily_subsidy': float(r['daily_subsidy']),
    }

with open(os.path.join(out_dir, 'scenario_B_result.json'), 'w', encoding='utf-8') as f:
    json.dump(result_data, f, ensure_ascii=False, indent=2)
print(f"\n场景B结果已保存: {out_dir}/scenario_B_result.json")
