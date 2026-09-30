"""
Q2.3 最优方案详细报告
============================================================
算法: NSGA-II 双目标Pareto遗传算法
      + 阻尼固定点迭代均衡求解
      + 连续S2满意度函数
最优方案: C(中型)+D(中型)+G(大型), 3站109万
"""
import numpy as np
from q2_biobjective_ga import get_data, solve_equilibrium, s2_continuous

data = get_data()
comm = data['comm_names']
sn = data['scale_names']
ccost = data['construct_cost']
doper = data['daily_operating']
scap = data['scale_capacity']
rev = data['revenue_per']
msd = data['monthly_service_demand']
elder = data['elderly_total']
telder = data['total_elderly']
daily = data['daily_demand']

# Q2 全局最优
cfg = np.zeros(10, dtype=int)
cfg[2] = 2; cfg[3] = 2; cfg[6] = 3

stations = np.where(cfg > 0)[0]
total_cost = sum(ccost[c-1] for c in cfg if c > 0)

# ---- 均衡求解 ----
assign, utils, csats, _ = solve_equilibrium(cfg, data)

# ---- 覆盖率 ----
elderly_served = np.zeros(10)
for s in stations:
    idx = np.where(assign == s)[0]
    if len(idx) == 0: continue
    ratio = min(1.0, scap[cfg[s]-1] / daily[idx].sum())
    for i in idx:
        elderly_served[i] = ratio * elder[i]
coverage = elderly_served.sum() / telder

# ---- 满意度 ----
ws = sum(elderly_served[i]*csats[i] for i in range(10) if elderly_served[i]>0)
wt = sum(elderly_served[i] for i in range(10) if elderly_served[i]>0)
satisfaction = ws/wt if wt>0 else 0

print("=" * 75)
print("Q2.3  最优方案详细结果")
print("=" * 75)
print(f"\n最优方案: C(中型)+D(中型)+G(大型)")
print(f"站点数: 3    建设成本: {total_cost}万 / {data['MAX_BUDGET']}万")
print(f"服务覆盖率: {coverage*100:.2f}%    加权满意度: {satisfaction:.4f}")

# ---- 各站点详情表 ----
print(f"\n{'─'*75}")
print(f"{'站点':<10} {'覆盖小区':<16} {'覆盖老人':<10} {'日需求/容量':<16} {'利用率':<10} {'S2':<8}")
print(f"{'─'*75}")
for s in stations:
    idx = np.where(assign == s)[0]
    names = ','.join(comm[c] for c in idx)
    elders = elder[idx].sum()
    dem = daily[idx].sum()
    cap = scap[cfg[s]-1]
    u = utils[s]
    ss2 = s2_continuous(u)
    print(f"{comm[s]}({sn[cfg[s]-1]})  {names:<16} {elders:<10.0f} {dem:<5.0f}/{cap:<10.0f} {u*100:<10.1f} {ss2:<8.4f}")

# ---- 满意度分解 ----
print(f"\n{'─'*75}")
print("各小区满意度分解 (Si = 0.2*S1 + 0.3*S2 + 0.5*S3)")
print(f"{'─'*75}")
print(f"{'小区':<6} {'分配站':<8} {'S1(距离)':<10} {'S2(利用)':<12} {'S3(价格)':<10} {'综合S':<10}")
print(f"{'─'*75}")
for i in range(10):
    s = assign[i]
    if s >= 0:
        s1 = data['S1'][i,s]
        s_2 = s2_continuous(utils[s])
        print(f"{comm[i]:<6} {comm[s]:<8} {s1:<10.2f} {s_2:<12.4f} {'1.00':<10} {csats[i]:.4f}")

# ---- 年度利润 ----
print(f"\n{'─'*75}")
print("年度利润计算 (Q2基准定价, 无补贴)")
print(f"{'─'*75}")
print(f"{'站点':<10} {'月收入(元)':<14} {'满意折扣':<10} {'年收入(元)':<15} {'年运营(元)':<15} {'年折旧(元)':<12} {'年利润(元)':<15} {'利润率':<10}")
print(f"{'─'*75}")
tp=tr=to=td=0.0
for s in stations:
    idx = np.where(assign == s)[0]
    mrev = sum(np.dot(msd[c], rev) for c in idx)
    avg_s = csats[idx].mean()
    arev = mrev * avg_s * 12
    aop = doper[cfg[s]-1] * 365
    adepr = ccost[cfg[s]-1]*10000/20
    prf = arev - aop - adepr
    pr = prf/(aop+adepr)*100
    tp+=prf; tr+=arev; to+=aop; td+=adepr
    print(f"{comm[s]}({sn[cfg[s]-1]})  {mrev:<14.0f} {avg_s:<10.4f} {arev:<15.0f} {aop:<15.0f} {adepr:<12.0f} {prf:<15.0f} {pr:<10.1f}%")
print(f"{'─'*75}")
print(f"{'合计':<10} {'':<14} {'':<10} {tr:<15.0f} {to:<15.0f} {td:<12.0f} {tp:<15.0f} {tp/(to+td)*100:<10.1f}%")

# ---- 年度利润公式说明 ----
print(f"\n{'─'*75}")
print("利润计算公式:")
print(f"  月收入 = Σ(各服务月需求量 × 基准定价)")
print(f"  年收入 = 月收入 × 平均满意度 × 12")
print(f"  年运营 = 日运营成本 × 365")
print(f"  年折旧 = 建设成本 × 10000 ÷ 20（按20年直线折旧）")
print(f"  年利润 = 年收入 - 年运营 - 年折旧")
print(f"  利润率 = 年利润 / (年运营 + 年折旧) * 100%")
print(f"{'─'*75}")
print("Q2.3 完成")
