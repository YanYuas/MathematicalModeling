"""
Q2.3 各服务站年度利润柱状图
============================================================
最优方案: C(中)+D(中)+G(大), 3站109万
修正利润: 容量修正 + 直接成本 + 满意度折扣
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from q2_biobjective_ga import get_data, solve_equilibrium, s2_continuous

out_dir = os.path.dirname(os.path.abspath(__file__))
data = get_data()
ccost = data['construct_cost']; doper = data['daily_operating']
scap = data['scale_capacity']; rev = data['revenue_per']
cost_per = np.array([8, 16, 24, 23, 20, 8])
msd = data['monthly_service_demand']
daily = data['daily_demand']
comm = data['comm_names']; sn = data['scale_names']

cfg = np.zeros(10, dtype=int)
cfg[2] = 2; cfg[3] = 2; cfg[6] = 3
stations = np.where(cfg > 0)[0]
assign, utils, csats, _ = solve_equilibrium(cfg, data)

labels = []; profits = []; revenues = []; costs = []; fixeds = []
for s in stations:
    idx = np.where(assign == s)[0]
    cap = scap[cfg[s]-1]
    ratio = min(1.0, cap / daily[idx].sum())
    avg_s = csats[idx].mean()

    mrev = sum(np.dot(msd[c], rev) for c in idx) * ratio
    mdc  = sum(np.dot(msd[c], cost_per) for c in idx) * ratio
    mgross = mrev - mdc
    agross = mgross * avg_s * 12
    aop = doper[cfg[s]-1] * 365
    adepr = ccost[cfg[s]-1]*10000/20
    afixed = aop + adepr
    prf = agross - afixed

    labels.append(f'{comm[s]}\n({sn[cfg[s]-1]})')
    profits.append(prf)
    revenues.append(agross)
    costs.append(afixed)

# 图
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(7, 5))
x = np.arange(len(labels))
w = 0.5
bars = ax.bar(x, np.array(profits)/1e4, w, color=['#4472C4', '#ED7D31', '#70AD47'],
              edgecolor='white', linewidth=1.2)

for i, (bar, prf, rev, cst) in enumerate(zip(bars, profits, revenues, fixeds)):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
            f'{prf/1e4:.1f}万元 (利润率{prf/cst*100:.0f}%)',
            ha='center', va='bottom', fontsize=11, fontweight='bold', color='#333')

ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=13)
ax.set_ylabel('年利润 (万元)', fontsize=13)
ax.set_ylim(0, max(profits)/1e4*1.18)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f'))
ax.grid(axis='y', alpha=0.3)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
plt.tight_layout()

png = os.path.join(out_dir, 'q2_3_annual_profit.png')
fig.savefig(png, dpi=200, bbox_inches='tight')
plt.close(fig)
print(f'已保存: {png}')
