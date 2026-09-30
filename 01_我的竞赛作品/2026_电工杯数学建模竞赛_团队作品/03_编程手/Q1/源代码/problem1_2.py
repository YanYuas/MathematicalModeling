"""
问题1.2：第5年末各小区理论月服务需求次数
理论需求 = 老人数 × 每老人月均需求，无任何约束
"""
import numpy as np
import pandas as pd

# ============================================================
# 1. 从1.1结果读取第5年末老人数据
# ============================================================
df_11 = pd.read_excel(r'c:\Users\29845\Desktop\电工赛1.1\预测结果_取整.xlsx')
df_y5 = df_11[df_11['年份'] == '第5年末'].copy().sort_values('小区')

communities = df_y5['小区'].tolist()
N5 = df_y5[['自理', '半失能', '失能']].values.astype(float)  # (10, 3)

print("第5年末各小区老人数：")
print(df_y5[['小区', '自理', '半失能', '失能', '总数']].to_string(index=False))

# ============================================================
# 2. 附件2数据：每人月均服务需求（次/月）
#    行=服务项目, 列=[自理, 半失能, 失能]
# ============================================================
services = ['助餐', '日间照料', '康复护理', '健康管理', '助浴', '精神慰藉']
demand_pp = np.array([
    [14,    20,  22],     # 助餐
    [ 8,    14,  18],     # 日间照料
    [ 0,     6,  12],     # 康复护理
    [ 2,     4,   6],     # 健康管理
    [ 0,     2,   4],     # 助浴
    [ 0.15,  1,   3],     # 精神慰藉
])

# ============================================================
# 问题1.2：理论月需求
#   demand[i, k, j] = N5[i,j] × demand_pp[k,j]
#   i=小区, k=服务, j=老人类型(0自理/1半失能/2失能)
# ============================================================
demand = N5[:, np.newaxis, :] * demand_pp[np.newaxis, :, :]  # (10, 6, 3)

print(f"\n{'='*60}")
print("问题1.2：各小区理论月服务需求次数（次/月）")
print(f"{'='*60}")

for i, comm in enumerate(communities):
    n = N5[i].astype(int)
    print(f"\n--- 小区 {comm} (自理={n[0]}, 半失能={n[1]}, 失能={n[2]}) ---")
    print(f"  {'服务':<8} {'自理':>8} {'半失能':>8} {'失能':>8} {'合计':>8}")
    for k, svc in enumerate(services):
        s, m, d = demand[i, k, 0], demand[i, k, 1], demand[i, k, 2]
        print(f"  {svc:<8} {s:>8.1f} {m:>8.1f} {d:>8.1f} {s+m+d:>8.1f}")

# 小区 × 服务 汇总表
print(f"\n{'='*60}")
print("1.2 汇总：各小区理论月需求总量（次/月）")
print(f"{'小区':<6} {'自理':>10} {'半失能':>10} {'失能':>10} {'合计':>10}")
for i, comm in enumerate(communities):
    t_s = demand[i, :, 0].sum()
    t_m = demand[i, :, 1].sum()
    t_d = demand[i, :, 2].sum()
    print(f"{comm:<6} {t_s:>10.1f} {t_m:>10.1f} {t_d:>10.1f} {t_s+t_m+t_d:>10.1f}")

# 分服务汇总（全区域）
print(f"\n{'='*60}")
print("全区域分服务理论月需求（次/月）")
print(f"{'服务':<8} {'自理':>10} {'半失能':>10} {'失能':>10} {'合计':>10}")
for k, svc in enumerate(services):
    t_s = demand[:, k, 0].sum()
    t_m = demand[:, k, 1].sum()
    t_d = demand[:, k, 2].sum()
    print(f"{svc:<8} {t_s:>10.1f} {t_m:>10.1f} {t_d:>10.1f} {t_s+t_m+t_d:>10.1f}")

# ============================================================
# 导出 Excel
# ============================================================
output = r'c:\Users\29845\Desktop\电工赛1.1\问题1.2结果.xlsx'
rows = []
for i, comm in enumerate(communities):
    for k, svc in enumerate(services):
        rows.append({
            '小区': comm, '服务': svc,
            '自理(理论)': round(demand[i, k, 0]),
            '半失能(理论)': round(demand[i, k, 1]),
            '失能(理论)': round(demand[i, k, 2]),
            '合计(理论)': round(demand[i, k, 0] + demand[i, k, 1] + demand[i, k, 2]),
        })
pd.DataFrame(rows).to_excel(output, index=False)
print(f"\n结果已导出至: {output}")
