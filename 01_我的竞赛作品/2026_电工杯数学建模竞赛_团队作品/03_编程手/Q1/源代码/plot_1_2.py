"""
问题1.2 可视化：4张图
图1: 各小区理论月需求总量（堆叠柱状图）
图2: 各服务需求分布（堆叠柱状图）
图3: 小区×服务热力图
图4: 全区域服务需求占比（饼图）
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ============================================================
# 数据准备
# ============================================================
communities = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
services = ['助餐', '日间照料', '上门护理', '康复理疗', '助浴', '紧急救助']
types = ['自理', '半失能', '失能']

# 第5年末老人数
N5 = np.array([
    [521, 150, 114],  # A
    [436, 130, 106],  # B
    [669, 199, 150],  # C
    [391, 115,  94],  # D
    [567, 168, 129],  # E
    [345, 101,  74],  # F
    [626, 185, 142],  # G
    [413, 123,  91],  # H
    [533, 159, 120],  # I
    [480, 141, 105],  # J
])

# 每老人月均需求 [服务, 老人类型]
demand_pp = np.array([
    [14,    20,  22],    # 助餐
    [ 8,    14,  18],    # 日间照料
    [ 0,     6,  12],    # 康复护理
    [ 2,     4,   6],    # 健康管理
    [ 0,     2,   4],    # 助浴
    [ 0.15,  1,   3],    # 精神慰藉
])

# 需求矩阵 (10小区, 6服务, 3类型)
demand = N5[:, np.newaxis, :] * demand_pp[np.newaxis, :, :]

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

colors = ['#4472C4', '#ED7D31', '#A5A5A5']  # 自理蓝, 半失能橙, 失能灰
colors_services = ['#4472C4', '#ED7D31', '#A5A5A5', '#FFC000', '#5B9BD5', '#70AD47']

# ============================================================
# 图1：各小区理论月需求总量（堆叠柱状图）
# ============================================================
fig1, ax1 = plt.subplots(figsize=(12, 6))

# 按类型汇总：(10, 3)
comm_by_type = demand.sum(axis=1)  # (10, 3)

x = np.arange(len(communities))
width = 0.55

bottom = np.zeros(len(communities))
for j in range(3):
    bars = ax1.bar(x, comm_by_type[:, j], width, bottom=bottom,
                   color=colors[j], label=types[j], edgecolor='white', linewidth=0.5)
    bottom += comm_by_type[:, j]

# 在柱顶标注总数
for i, total in enumerate(bottom):
    ax1.text(i, total + 500, f'{total/1000:.1f}k', ha='center', va='bottom', fontsize=8, fontweight='bold')

ax1.set_xlabel('小区', fontsize=12)
ax1.set_ylabel('理论月需求次数（次/月）', fontsize=12)
ax1.set_title('图1：第5年末各小区理论月服务需求总量', fontsize=14, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(communities, fontsize=11)
ax1.legend(loc='upper right', fontsize=10)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v/1000:.0f}k'))
ax1.set_ylim(0, bottom.max() * 1.15)
ax1.grid(axis='y', alpha=0.3)

plt.tight_layout()
fig1.savefig(r'c:\Users\29845\Desktop\电工赛题2\图1_各小区需求总量.png', dpi=200, bbox_inches='tight')
print("图1 已保存")

# ============================================================
# 图2：各服务需求分布（堆叠柱状图）
# ============================================================
fig2, ax2 = plt.subplots(figsize=(12, 6))

# 按服务汇总：(6, 3)
svc_by_type = demand.sum(axis=0)  # (6, 3)

x2 = np.arange(len(services))
bottom2 = np.zeros(len(services))
for j in range(3):
    ax2.bar(x2, svc_by_type[:, j], width, bottom=bottom2,
            color=colors[j], label=types[j], edgecolor='white', linewidth=0.5)
    bottom2 += svc_by_type[:, j]

for i, total in enumerate(bottom2):
    ax2.text(i, total + 1000, f'{total/1000:.1f}k', ha='center', va='bottom', fontsize=8, fontweight='bold')

ax2.set_xlabel('服务项目', fontsize=12)
ax2.set_ylabel('理论月需求次数（次/月）', fontsize=12)
ax2.set_title('图2：第5年末全区域各服务理论月需求', fontsize=14, fontweight='bold')
ax2.set_xticks(x2)
ax2.set_xticklabels(services, fontsize=11)
ax2.legend(loc='upper right', fontsize=10)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v/1000:.0f}k'))
ax2.set_ylim(0, bottom2.max() * 1.15)
ax2.grid(axis='y', alpha=0.3)

plt.tight_layout()
fig2.savefig(r'c:\Users\29845\Desktop\电工赛题2\图2_各服务需求分布.png', dpi=200, bbox_inches='tight')
print("图2 已保存")

# ============================================================
# 图3：小区×服务热力图
# ============================================================
fig3, ax3 = plt.subplots(figsize=(11, 7))

# 按小区+服务汇总（不分类型）：(10, 6)
heat_data = demand.sum(axis=2)  # (10, 6)

im = ax3.imshow(heat_data, cmap='YlOrRd', aspect='auto', vmin=0)

# 在每个格子标注数值
for i in range(len(communities)):
    for k in range(len(services)):
        val = heat_data[i, k]
        color = 'white' if val > heat_data.max() * 0.6 else 'black'
        ax3.text(k, i, f'{val:.0f}', ha='center', va='center', fontsize=8, color=color, fontweight='bold')

ax3.set_xticks(range(len(services)))
ax3.set_xticklabels(services, fontsize=11, rotation=30, ha='right')
ax3.set_yticks(range(len(communities)))
ax3.set_yticklabels(communities, fontsize=11)
ax3.set_title('图3：小区 × 服务理论月需求热力图（单位：次/月）', fontsize=14, fontweight='bold')

cbar = plt.colorbar(im, ax=ax3, shrink=0.85, pad=0.02)
cbar.set_label('次/月', fontsize=10)

plt.tight_layout()
fig3.savefig(r'c:\Users\29845\Desktop\电工赛题2\图3_需求热力图.png', dpi=200, bbox_inches='tight')
print("图3 已保存")

# ============================================================
# 图4：全区域服务需求占比（环形图 + 详细标注）
# ============================================================
fig4, ax4 = plt.subplots(figsize=(10, 7))

svc_totals = demand.sum(axis=(0, 2))  # (6,) 各服务总量
total_all = svc_totals.sum()
pcts = svc_totals / total_all * 100

wedges, texts, autotexts = ax4.pie(
    svc_totals,
    labels=None,
    autopct='%1.1f%%',
    startangle=90,
    pctdistance=0.82,
    colors=plt.cm.Set2(np.linspace(0, 1, 6)),
    wedgeprops={'width': 0.4, 'edgecolor': 'white', 'linewidth': 1.5},
    textprops={'fontsize': 10},
)

# 外侧大标签
legend_labels = [
    f'{svc}\n{svc_totals[i]/1000:.1f}k ({pcts[i]:.1f}%)'
    for i, svc in enumerate(services)
]
ax4.legend(wedges, legend_labels, loc='lower right', fontsize=9,
           bbox_to_anchor=(1.35, 0.5))

ax4.set_title('图4：全区域理论月服务需求占比\n（总计 {:.0f} 千次/月）'.format(total_all/1000),
              fontsize=14, fontweight='bold')

plt.tight_layout()
fig4.savefig(r'c:\Users\29845\Desktop\电工赛题2\图4_服务需求占比.png', dpi=200, bbox_inches='tight')
print("图4 已保存")

print("\n4张图全部保存到: 电工赛题2 文件夹")
