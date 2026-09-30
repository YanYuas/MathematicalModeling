"""
问题1.3：消费约束下第5年末各小区实际月服务需求
==============================================
规则：每类老人月消费上限 = 月收入 × 比例(自理20%/半失能25%/失能30%)
      理论费用(用营收价格)超上限 → 所有服务等比削减 → 取整
"""
import numpy as np
import pandas as pd
import os

# ====== 1. 第5年末老人数 (1.1马尔可夫预测结果) ======
N5 = np.array([
    [521, 150, 114], [436, 130, 106], [669, 199, 150],
    [391, 115,  94], [567, 168, 129], [345, 101,  74],
    [626, 185, 142], [413, 123,  91], [533, 159, 120],
    [480, 141, 105]
], dtype=float)
communities = list('ABCDEFGHIJ')

# ====== 2. 各小区人均月收入 (附件1) ======
income = dict(zip('ABCDEFGHIJ',
    [3400, 3100, 3800, 2900, 3500, 2700, 3600, 3000, 3300, 3200]))

# ====== 3. 参数 ======
services = ['助餐','日间照料','上门护理','康复理疗','助浴','紧急救助']
types_cn = ['自理','半失能','失能']

# 附件2: 每老人月均服务需求 (服务×类型)
demand_pp = np.array([
    [14,   20,  22],   # 助餐
    [ 8,   14,  18],   # 日间照料
    [ 0,    6,  12],   # 上门护理
    [ 2,    4,   6],   # 康复理疗
    [ 0,    2,   4],   # 助浴
    [0.15,  1,   3],   # 紧急救助
])

# 附件2: 单次服务营收(元/次), 紧急救助免费=0
revenue = np.array([10, 20, 30, 28, 25, 0])

# 消费比例: 自理20%, 半失能25%, 失能30%
cap_ratio = np.array([0.20, 0.25, 0.30])

# ====== 4. 逐小区逐类型计算 ======
print("=" * 70)
print("问题1.3：消费约束下第5年末实际月服务需求（次/月）")
print("=" * 70)

monthly_svc = np.zeros((10, 6))   # 小区×服务 实际总需求
daily_demand = np.zeros(10)        # 各小区日均总需求
rows = []                           # Excel导出

for i, comm in enumerate(communities):
    inc = income[comm]
    caps = inc * cap_ratio  # 三类老人月消费上限

    print(f"\n小区{comm} (月收入={inc})")

    for t in range(3):
        n = int(N5[i, t])
        if n == 0:
            continue

        theo = demand_pp[:, t]                     # 每人理论需求
        theo_cost = np.dot(theo, revenue)           # 每人理论费用

        if theo_cost <= caps[t]:
            # 不超预算: 对总量取整 (0.15×521→78, 不吞掉)
            constrained = np.round(n * theo) / n
            r = 1.0
            flag = "充足"
        else:
            r = caps[t] / theo_cost
            constrained = np.round(theo * r)  # 每人取整

            # 预算硬约束: 按金额误差调整
            for _ in range(30):
                per_cost = np.dot(constrained, revenue)
                if per_cost <= caps[t]:
                    break
                # 找上浮金额最大的服务: (取整值-原值)×单价
                over_amount = (constrained - theo * r) * revenue
                worst = np.argmax(over_amount)
                if constrained[worst] <= 0:
                    break
                constrained[worst] -= 1

            flag = f"削减 r={r:.4f}"

        monthly_svc[i] += n * constrained

        print(f"  {types_cn[t]}({n}人): 单人费用{theo_cost:.0f} vs 上限{caps[t]:.0f} → {flag}")
        for k in range(6):
            per_theo = theo[k]
            per_act = constrained[k]
            rows.append([comm, services[k], types_cn[t],
                         round(n * per_theo), round(n * per_act),
                         round(r, 4) if r < 1 else 1.0])

    daily_demand[i] = monthly_svc[i].sum() / 30

print(f"\n{'='*70}")
print("各小区日均总需求 (次/日)")
print(f"{'='*70}")
for i, comm in enumerate(communities):
    print(f"  {comm}: {daily_demand[i]:.1f}")

print(f"\n{'='*70}")
print("10×6 实际月需求矩阵 (次/月)")
print(f"{'='*70}")
header = f"  {'小区':<6}" + ''.join(f"{s:>8}" for s in services) + f"  {'合计':>8}"
print(header)
for i, comm in enumerate(communities):
    row = f"  {comm:<6}"
    for k in range(6):
        row += f"{monthly_svc[i,k]:>8.0f}"
    row += f"{monthly_svc[i].sum():>8.0f}"
    print(row)
total_row = f"  {'合计':<6}"
for k in range(6):
    total_row += f"{monthly_svc[:,k].sum():>8.0f}"
total_row += f"{monthly_svc.sum():>8.0f}"
print(total_row)
print(f"\n全区域月总需求: {monthly_svc.sum():.0f} 次/月")
print(f"全区域日总需求: {daily_demand.sum():.1f} 次/日")

# ====== 5. 导出到桌面 ======
df_out = pd.DataFrame(rows, columns=['小区','服务','老人类型','理论次数','实际次数','削减比例'])
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '问题1.3结果_new.xlsx')
with pd.ExcelWriter(out_path) as writer:
    df_out.to_excel(writer, sheet_name='明细', index=False)
    # 10x6矩阵
    mat = pd.DataFrame(monthly_svc.round(0).astype(int),
                       index=communities, columns=services)
    mat['合计'] = mat.sum(axis=1)
    mat.to_excel(writer, sheet_name='10x6矩阵')
    # 日需求
    daily_df = pd.DataFrame({'小区': communities, '日需求(次/日)': daily_demand.round(1)})
    daily_df.to_excel(writer, sheet_name='日需求', index=False)
print(f"\n结果已导出: {out_path}")
