"""
问题一：老人数量预测与理论服务需求 — 最终完整代码
============================================================
问题1.1：基于马尔可夫转移矩阵的逐年递推预测（每步取整）
问题1.2：第5年末各小区理论月服务需求次数

作者：电工杯建模队
日期：2026-05
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# 输出目录：本文件所在目录
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 全局参数
# ============================================================
d       = 0.05    # 年均自然死亡率
U       = 0.07    # 年均新增率（仅进入"自理"）
P_alpha = 0.045   # 自理 → 半失能 转移概率
P_beta  = 0.10    # 半失能 → 失能 转移概率

communities = ['A','B','C','D','E','F','G','H','I','J']
types_cn    = ['自理','半失能','失能']
services    = ['助餐','日间照料','上门护理','康复理疗','助浴','紧急救助']

# ============================================================
# 问题1.1：人口预测
# ============================================================

# 附件1：第0年末（当前）各小区三类老人数
raw = np.array([
    [496, 152,  64],   # A
    [408, 136,  64],   # B
    [632, 208,  80],   # C
    [368, 120,  56],   # D
    [536, 176,  72],   # E
    [328, 104,  40],   # F
    [592, 192,  80],   # G
    [392, 128,  48],   # H
    [504, 168,  64],   # I
    [456, 144,  56],   # J
])

# 状态转移矩阵 P：X(t+1) = P @ X(t)
P = np.array([
    [(1-d)*(1-P_alpha)+U,  U,                   U       ],
    [(1-d)*P_alpha,           (1-d)*(1-P_beta),      0         ],
    [0,                       (1-d)*P_beta,           (1-d)    ],
])

print("=" * 60)
print("问题1.1：基于马尔可夫转移矩阵的老人数量递推预测")
print("=" * 60)
print(f"\n参数：d={d}, U={U}, P_alpha={P_alpha}, P_beta={P_beta}")
print(f"净增长率 = {((1-d+U)-1)*100:+.1f}%/年\n")

print("转移矩阵 P：")
print(np.array2string(P, precision=4, suppress_small=True))
print(f"列和：{P.sum(axis=0)}")

# ---- 5年递推（每步取整）----
years = 5
results = np.zeros((10, 3, years+1), dtype=int)  # [小区, 类型, 年份]

for c in range(10):
    N = raw[c].copy().astype(int)
    results[c, :, 0] = N
    for t in range(1, years+1):
        N_float = P @ N.astype(float)
        N = np.array([round(N_float[0]), round(N_float[1]), round(N_float[2])], dtype=int)
        results[c, :, t] = N

# ---- 逐年输出 ----
for t in range(years+1):
    print(f"\n--- 第{t}年末 ---")
    print(f"{'小区':>5} {'自理':>6} {'半失能':>6} {'失能':>6} {'总数':>6} {'较上年增':>8}")
    for c in range(10):
        row = results[c, :, t]
        delta = row.sum() - (results[c, :, t-1].sum() if t > 0 else raw[c].sum())
        print(f"{communities[c]:>5} {row[0]:>6} {row[1]:>6} {row[2]:>6} {row.sum():>6} {delta:+>8}")

# ---- 全区域汇总 ----
print(f"\n{'='*60}")
print("全区域汇总")
print(f"{'年份':>6} {'自理':>8} {'半失能':>8} {'失能':>8} {'总人数':>8}")
totals_by_year = results.sum(axis=0)  # [3, 6]
for t in range(years+1):
    col = totals_by_year[:, t]
    print(f"第{t}年末 {col[0]:>8.0f} {col[1]:>8.0f} {col[2]:>8.0f} {col.sum():>8.0f}")

# ---- 第5年末快照（问题1.2输入） ----
N5 = results[:, :, 5].astype(int)
print(f"\n第5年末各小区老人数（问题1.2输入）：")
print(f"{'小区':>5} {'自理':>6} {'半失能':>6} {'失能':>6} {'总数':>6}")
for c in range(10):
    print(f"{communities[c]:>5} {N5[c,0]:>6} {N5[c,1]:>6} {N5[c,2]:>6} {N5[c].sum():>6}")
print(f"{'合计':>5} {N5[:,0].sum():>6} {N5[:,1].sum():>6} {N5[:,2].sum():>6} {N5.sum():>6}")

# ============================================================
# 问题1.2：理论月服务需求
# ============================================================

# 附件2：每老人月均服务需求（行=服务，列=[自理,半失能,失能]）
demand_pp = np.array([
    [14,    20,  22],     # 助餐
    [ 8,    14,  18],     # 日间照料
    [ 0,     6,  12],     # 上门护理
    [ 2,     4,   6],     # 康复理疗
    [ 0,     2,   4],     # 助浴
    [ 0.15,  1,   3],     # 紧急救助
])

# 需求张量 D[i,k,j] = N5[i,j] × demand_pp[k,j]    i=小区, k=服务, j=类型
D = N5[:, np.newaxis, :] * demand_pp[np.newaxis, :, :]  # (10, 6, 3)

print(f"\n{'='*60}")
print("问题1.2：第5年末理论月服务需求次数（次/月）")
print("公式：需求 = 第5年末老人数 × 每人月均需求次数")
print(f"{'='*60}")

for i, comm in enumerate(communities):
    n = N5[i]
    print(f"\n--- 小区 {comm} (自理={n[0]}, 半失能={n[1]}, 失能={n[2]}) ---")
    print(f"  {'服务':<8} {'自理贡献':>10} {'半失能贡献':>10} {'失能贡献':>10} {'合计':>10}")
    total_comm = 0
    for k, svc in enumerate(services):
        s, m, d2 = D[i, k, 0], D[i, k, 1], D[i, k, 2]
        t = s + m + d2
        total_comm += t
        print(f"  {svc:<8} {s:>10.1f} {m:>10.1f} {d2:>10.1f} {t:>10.1f}")
    print(f"  {'[合计]':<8} {total_comm:>31.1f}")

# ---- 分服务汇总（全区域） ----
print(f"\n{'='*60}")
print("全区域分服务理论月需求汇总（次/月）")
print(f"{'服务':<8} {'自理贡献':>10} {'半失能贡献':>10} {'失能贡献':>10} {'合计':>10} {'占比':>8}")
svc_totals_3type = D.sum(axis=0)  # (6, 3)
svc_totals = svc_totals_3type.sum(axis=1)  # (6,)
total_all = svc_totals.sum()
for k, svc in enumerate(services):
    s, m, d2 = svc_totals_3type[k]
    t = svc_totals[k]
    print(f"{svc:<8} {s:>10.1f} {m:>10.1f} {d2:>10.1f} {t:>10.0f} {t/total_all*100:>7.1f}%")
print(f"{'合计':<8} {svc_totals_3type[:,0].sum():>10.1f} {svc_totals_3type[:,1].sum():>10.1f} {svc_totals_3type[:,2].sum():>10.1f} {total_all:>10.0f}")

# ---- 小区-服务汇总表 (10×6) ----
print(f"\n{'='*60}")
print("10×6 需求矩阵（加总三类老人，次/月）")
heat_data = D.sum(axis=2)  # (10, 6)
print(f"{'小区':>5}", end="")
for svc in services:
    print(f"{svc:>10}", end="")
print(f"{'合计':>10}")
for i, comm in enumerate(communities):
    print(f"{comm:>5}", end="")
    for k in range(6):
        print(f"{heat_data[i,k]:>10.0f}", end="")
    print(f"{heat_data[i].sum():>10.0f}")
print(f"{'合计':>5}", end="")
for k in range(6):
    print(f"{heat_data[:,k].sum():>10.0f}", end="")
print(f"{heat_data.sum():>10.0f}")
print(f"\n全区域理论月需求总量: {total_all:.0f} 次/月")
print(f"全区域理论年需求总量: {total_all*12:.0f} 次/年")

# ============================================================
# 可视化
# ============================================================

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

colors_type  = ['#4472C4', '#ED7D31', '#A5A5A5']  # 自理蓝, 半失能橙, 失能灰
colors_svc   = ['#4472C4','#ED7D31','#A5A5A5','#FFC000','#5B9BD5','#70AD47']

# ---- 图1：各小区理论月需求总量（堆叠柱状） ----
fig1, ax1 = plt.subplots(figsize=(12, 6))
comm_by_type = D.sum(axis=1)  # (10,3)
x = np.arange(10)
width = 0.55
bottom = np.zeros(10)
for j in range(3):
    ax1.bar(x, comm_by_type[:, j], width, bottom=bottom,
            color=colors_type[j], label=types_cn[j], edgecolor='white', linewidth=0.5)
    bottom += comm_by_type[:, j]
for i, total in enumerate(bottom):
    ax1.text(i, total + 500, f'{total/1000:.1f}k', ha='center', va='bottom',
             fontsize=8, fontweight='bold')
ax1.set_xticks(x); ax1.set_xticklabels(communities, fontsize=11)
ax1.set_ylabel('理论月需求次数（次/月）', fontsize=12)
ax1.set_title('图1：第5年末各小区理论月服务需求总量', fontsize=14, fontweight='bold')
ax1.legend(loc='upper right', fontsize=10)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v/1000:.0f}k'))
ax1.set_ylim(0, bottom.max()*1.15); ax1.grid(axis='y', alpha=0.3)
plt.tight_layout()
fig1.savefig(os.path.join(OUT_DIR, '图1_各小区需求总量.png'), dpi=200, bbox_inches='tight')
print("\n图1 已保存")

# ---- 图2：各服务需求分布（堆叠柱状） ----
fig2, ax2 = plt.subplots(figsize=(12, 6))
svc_by_type = D.sum(axis=0)  # (6,3)
x2 = np.arange(6)
bottom2 = np.zeros(6)
for j in range(3):
    ax2.bar(x2, svc_by_type[:, j], width, bottom=bottom2,
            color=colors_type[j], label=types_cn[j], edgecolor='white', linewidth=0.5)
    bottom2 += svc_by_type[:, j]
for i, total in enumerate(bottom2):
    ax2.text(i, total + 1000, f'{total/1000:.1f}k', ha='center', va='bottom',
             fontsize=8, fontweight='bold')
ax2.set_xticks(x2); ax2.set_xticklabels(services, fontsize=11)
ax2.set_ylabel('理论月需求次数（次/月）', fontsize=12)
ax2.set_title('图2：第5年末全区域各服务理论月需求', fontsize=14, fontweight='bold')
ax2.legend(loc='upper right', fontsize=10)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v/1000:.0f}k'))
ax2.set_ylim(0, bottom2.max()*1.15); ax2.grid(axis='y', alpha=0.3)
plt.tight_layout()
fig2.savefig(os.path.join(OUT_DIR, '图2_各服务需求分布.png'), dpi=200, bbox_inches='tight')
print("图2 已保存")

# ---- 图3：小区×服务热力图 ----
fig3, ax3 = plt.subplots(figsize=(11, 7))
im = ax3.imshow(heat_data, cmap='YlOrRd', aspect='auto', vmin=0)
for i in range(10):
    for k in range(6):
        val = heat_data[i, k]
        color = 'white' if val > heat_data.max()*0.6 else 'black'
        ax3.text(k, i, f'{val:.0f}', ha='center', va='center', fontsize=8,
                 color=color, fontweight='bold')
ax3.set_xticks(range(6)); ax3.set_xticklabels(services, fontsize=11, rotation=30, ha='right')
ax3.set_yticks(range(10)); ax3.set_yticklabels(communities, fontsize=11)
ax3.set_title('图3：小区×服务理论月需求热力图（次/月）', fontsize=14, fontweight='bold')
cbar = plt.colorbar(im, ax=ax3, shrink=0.85, pad=0.02)
cbar.set_label('次/月', fontsize=10)
plt.tight_layout()
fig3.savefig(os.path.join(OUT_DIR, '图3_需求热力图.png'), dpi=200, bbox_inches='tight')
print("图3 已保存")

# ---- 图4：全区域服务需求占比（环形图） ----
fig4, ax4 = plt.subplots(figsize=(10, 7))
pcts = svc_totals / total_all * 100
wedges, texts, autotexts = ax4.pie(
    svc_totals, labels=None, autopct='%1.1f%%', startangle=90,
    pctdistance=0.82,
    colors=plt.cm.Set2(np.linspace(0, 1, 6)),
    wedgeprops={'width': 0.4, 'edgecolor': 'white', 'linewidth': 1.5},
    textprops={'fontsize': 10},
)
legend_labels = [
    f'{svc}\n{svc_totals[k]:.0f}次/月 ({pcts[k]:.1f}%)'
    for k, svc in enumerate(services)
]
ax4.legend(wedges, legend_labels, loc='lower right', fontsize=9,
           bbox_to_anchor=(1.35, 0.5))
ax4.set_title(f'图4：全区域理论月服务需求占比\n（总计 {total_all/1000:.1f} 千次/月）',
              fontsize=14, fontweight='bold')
plt.tight_layout()
fig4.savefig(os.path.join(OUT_DIR, '图4_服务需求占比.png'), dpi=200, bbox_inches='tight')
print("图4 已保存")

# ---- 图5：10个小区人口变化趋势（5×2面板）----
fig5, axes5 = plt.subplots(5, 2, figsize=(12, 16))
fig5.suptitle('各小区三类老人数量变化 (第0–5年末)', fontsize=14, fontweight='bold')
for c in range(10):
    ax = axes5[c//2, c%2]
    data = results[c]  # (3, 6)
    ax.stackplot(range(6), data[0], data[1], data[2],
                 colors=colors_type, labels=types_cn, alpha=0.85)
    for yr in range(6):
        ax.axvline(yr, color='k', linewidth=0.6, linestyle='--', alpha=0.5)
    ax.set_title(f'小区 {communities[c]}', fontsize=11)
    ax.set_xticks(range(6)); ax.set_xlim(0, 5)
    if c >= 8: ax.set_xlabel('年份', fontsize=10)
    if c % 2 == 0: ax.set_ylabel('人数', fontsize=10)
    ax.grid(axis='y', alpha=0.3)
handles, labels = axes5[0,0].get_legend_handles_labels()
fig5.legend(handles, labels, loc='lower center', ncol=3, fontsize=11)
plt.tight_layout(rect=[0, 0.03, 1, 0.97])
fig5.savefig(os.path.join(OUT_DIR, '图5_各小区人口趋势.png'), dpi=200, bbox_inches='tight')
print("图5 已保存")

print(f"\n全部5张图保存至: {OUT_DIR}")

# ============================================================
# 导出 Excel
# ============================================================
output = os.path.join(OUT_DIR, '问题一完整结果.xlsx')
with pd.ExcelWriter(output) as writer:
    # Sheet 1: 逐年人口预测
    rows_pop = []
    for t in range(years+1):
        for c in range(10):
            rows_pop.append({
                '小区': communities[c],
                '年份': f'第{t}年末',
                '自理': int(results[c, 0, t]),
                '半失能': int(results[c, 1, t]),
                '失能': int(results[c, 2, t]),
                '总数': int(results[c, :, t].sum()),
            })
    df_pop = pd.DataFrame(rows_pop)
    df_pop.to_excel(writer, sheet_name='逐年人口预测', index=False)

    # Sheet 2: 理论月需求
    rows_demand = []
    for i, comm in enumerate(communities):
        for k, svc in enumerate(services):
            s, m, d2 = D[i, k, 0], D[i, k, 1], D[i, k, 2]
            rows_demand.append({
                '小区': comm, '服务': svc,
                '自理贡献': round(s, 1), '半失能贡献': round(m, 1),
                '失能贡献': round(d2, 1), '合计': round(s+m+d2, 1),
            })
    df_demand = pd.DataFrame(rows_demand)
    df_demand.to_excel(writer, sheet_name='理论月需求', index=False)

    # Sheet 3: 10×6 需求矩阵
    df_heat = pd.DataFrame(heat_data.round(0).astype(int),
                           index=communities, columns=services)
    df_heat['合计'] = df_heat.sum(axis=1)
    df_heat.to_excel(writer, sheet_name='10x6需求矩阵')

print(f"\nExcel结果已导出至: {output}")
print("包含3个Sheet: 逐年人口预测 / 理论月需求 / 10x6需求矩阵")
print("\n===== 问题一全部完成 =====")
