"""
Q2.3 最优方案报告 (修正版: 含直接服务成本 + 容量修正)
============================================================
算法: NSGA-II双目标Pareto GA + 阻尼固定点迭代均衡
方案: C(中)+D(中)+G(大), 3站109万
利润: 容量修正 + 直接成本(cost_per) + 满意度折扣
输出: 控制台表格 + q2_3_results.xlsx
"""
import numpy as np
import pandas as pd
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from q2_biobjective_ga import get_data, solve_equilibrium, s2_continuous

OUT = os.path.dirname(os.path.abspath(__file__))
data = get_data()
comm = data['comm_names'];  sn = data['scale_names']
ccost = data['construct_cost'];  doper = data['daily_operating']
scap = data['scale_capacity'];   rev = data['revenue_per']
cost_per = np.array([8, 16, 24, 23, 20, 8])
msd = data['monthly_service_demand']
elder = data['elderly_total'];   telder = data['total_elderly']
daily = data['daily_demand']

# Q2全局最优
cfg = np.zeros(10, dtype=int)
cfg[2] = 2; cfg[3] = 2; cfg[6] = 3
stations = np.where(cfg > 0)[0]
total_cost = sum(ccost[c-1] for c in cfg if c > 0)

# 均衡求解
assign, utils, csats, _ = solve_equilibrium(cfg, data)

# 覆盖率
elderly_served = np.zeros(10)
for s in stations:
    idx = np.where(assign == s)[0]
    if len(idx) == 0: continue
    ratio = min(1.0, scap[cfg[s]-1] / daily[idx].sum())
    for i in idx:
        elderly_served[i] = ratio * elder[i]
coverage = elderly_served.sum() / telder

# 满意度
w = elderly_served
satisfaction = np.dot(w, csats) / w.sum() if w.sum() > 0 else 0

print("=" * 70)
print("Q2.3 最优方案详细结果 (修正版)")
print("=" * 70)
print(f"方案: C(中)+D(中)+G(大), 3站{total_cost}万/{data['MAX_BUDGET']}万")
print(f"覆盖率: {coverage*100:.2f}%    满意度: {satisfaction:.4f}")

# -- 表1: 站点概况 --
print(f"\n{'='*70}")
print("表1: 各服务站概况")
print(f"{'='*70}")
print(f"{'站点(规模)':<12} {'覆盖小区':<14} {'覆盖老人':<8} {'日需求/容量':<16} {'利用%':<8} {'S2_j':<8}")
print(f"{'─'*70}")
t1 = []
for s in stations:
    idx = np.where(assign == s)[0]
    names = ','.join(comm[c] for c in idx)
    elders_n = elder[idx].sum()
    dem = daily[idx].sum()
    cap = scap[cfg[s]-1]
    u_pct = utils[s] * 100
    s_2 = s2_continuous(utils[s])
    t1.append({'站点(规模)': f'{comm[s]}({sn[cfg[s]-1]})',
               '覆盖小区': names, '覆盖老人数': elders_n,
               '日需求(人次)': round(dem), '容量(人次/日)': cap,
               '利用率%': round(u_pct, 1), 'S2_j满意度': round(s_2, 4)})
    print(f"{comm[s]}({sn[cfg[s]-1]})    {names:<14} {elders_n:<8.0f} {dem:<5.0f}/{cap:<10.0f} {u_pct:<8.1f} {s_2:<8.4f}")

# -- 表2: 满意度 --
print(f"\n{'='*70}")
print("表2: 各小区满意度分解 (S_{i,j} = 0.2*S1_{i,j} + 0.3*S2_j + 0.5*S3_{i,j})")
print(f"{'='*70}")
print(f"{'小区':<5} {'分配站':<6} {'S1_{i,j}(距离)':<12} {'S2_j(利用)':<14} {'S3_{i,j}(价格)':<12} {'综合S_{i,j}':<10}")
print(f"{'─'*70}")
t2 = []
for i in range(10):
    s = assign[i]
    s1 = data['S1'][i,s]; s_2 = s2_continuous(utils[s])
    t2.append({'小区': comm[i], '分配站': comm[s],
               'S1_{i,j}': round(s1, 2), 'S2_j': round(s_2, 4),
               'S3': 1.0, '综合S_{i,j}': round(csats[i], 4)})
    print(f"{comm[i]:<5} {comm[s]:<6} {s1:<10.2f} {s_2:<12.4f} {'1.00':<10} {csats[i]:.4f}")

# -- 表3: 利润 (修正版) --
print(f"\n{'='*70}")
print("表3: 年度利润 (容量修正 + 直接成本 + 满意度折扣)")
print(f"{'='*70}")
print(f"{'站点':<10} {'月收入':<12} {'月成本':<12} {'月毛利':<12} {'年毛利':<13} {'年固定':<12} {'年利润':<13} {'利润率%':<8}")
print(f"{'─'*70}")
t3 = []; tp=0.0; tfo=0.0
for s in stations:
    idx = np.where(assign == s)[0]
    cap = scap[cfg[s]-1]
    full_daily = daily[idx].sum()
    ratio = min(1.0, cap / full_daily)
    avg_s = csats[idx].mean()

    mrev = sum(np.dot(msd[c], rev) for c in idx) * ratio
    mdc  = sum(np.dot(msd[c], cost_per) for c in idx) * ratio
    mgross = mrev - mdc
    agross = mgross * avg_s * 12
    aop = doper[cfg[s]-1] * 365
    adepr = ccost[cfg[s]-1]*10000/20
    afixed = aop + adepr
    prf = agross - afixed
    pr_pct = prf/afixed*100
    tp+=prf; tfo+=afixed

    t3.append({'站点(规模)': f'{comm[s]}({sn[cfg[s]-1]})',
               '月收入(容量修正)': round(mrev), '月直接成本': round(mdc),
               '月毛利': round(mgross), '年毛利': round(agross),
               '年固定': round(afixed), '年利润': round(prf), '利润率%': round(pr_pct,1)})
    print(f"{comm[s]}({sn[cfg[s]-1]})  {mrev:<12.0f} {mdc:<12.0f} {mgross:<12.0f} {agross:<13.0f} {afixed:<12.0f} {prf:<13.0f} {pr_pct:<8.1f}")

t3.append({'站点(规模)': '合计', '月收入(容量修正)': '', '月直接成本': '',
           '月毛利': '', '年毛利': '', '年固定': round(tfo),
           '年利润': round(tp), '利润率%': round(tp/tfo*100,1)})
print(f"{'─'*70}")
print(f"{'合计':<10} {'':<12} {'':<12} {'':<12} {'':<13} {tfo:<12.0f} {tp:<13.0f} {tp/tfo*100:<8.1f}")

# 利润公式
print(f"\n利润公式(修正版):")
print(f"  月收入 = sum(各服务月需求*基准定价) * 容量修正比")
print(f"  月直接成本 = sum(各服务月需求*服务直接成本) * 容量修正比")
print(f"  月毛利 = 月收入 - 月直接成本")
print(f"  年毛利 = 月毛利 * 满意度折扣 * 12")
print(f"  年固定 = 日运营*365 + 建设成本*10000/20")
print(f"  年利润 = 年毛利 - 年固定")
print(f"  利润率 = 年利润 / 年固定 * 100%")
print(f"\n  基准定价: {rev.tolist()}")
print(f"  直接成本: {cost_per.tolist()}")

# ==== 导出Excel ====
xlsx = os.path.join(OUT, 'q2_3_results.xlsx')
with pd.ExcelWriter(xlsx) as writer:
    pd.DataFrame(t1).to_excel(writer, sheet_name='站点概况', index=False)
    pd.DataFrame(t2).to_excel(writer, sheet_name='满意度分解', index=False)
    pd.DataFrame(t3).to_excel(writer, sheet_name='年度利润', index=False)
print(f"\nExcel已导出: {xlsx}")
print("Q2.3 完成")
