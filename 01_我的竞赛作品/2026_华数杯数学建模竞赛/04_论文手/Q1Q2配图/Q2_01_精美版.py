# -*- coding: utf-8 -*-
"""Q2_01 精美版 v3 — 核心张力：线长 vs 轮廓对冲（素雅配色 + 干净排版重做）
统一低调色板：深蓝/墨绿/赭红 + 柔和浅填充；去霓虹、去斜纹，线条更细。
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrow, Circle

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.dirname(os.path.abspath(__file__))

# 活泼中饱和色板
C_OUTLINE = '#566573'     # 轮廓框
C_MOD    = '#DCEBFA'      # 模块浅蓝
C_MOD_E  = '#5C9BD6'      # 模块边
C_OVER   = '#EF6A5A'      # 超轮廓珊瑚红
C_OVER_L = '#FCE8E5'      # 超轮廓浅红
C_TERM   = '#EF6A5A'      # 终端
C_NET    = '#A5B4C6'      # 线网
C_TXT    = '#2F3542'
C_SUB    = '#7A8794'
C_BLUE   = '#5C9BD6'
C_GREEN  = '#6BBF59'


def mod(ax, x0, y0, w, h, label=None, edge=C_MOD_E, fill=C_MOD):
    box = FancyBboxPatch((x0, y0), w, h, boxstyle='round,pad=0.03,rounding_size=0.10',
                         fc=fill, ec=edge, lw=1.4, mutation_aspect=0.6)
    ax.add_patch(box)
    if label:
        ax.text(x0+w/2, y0+h/2, label, ha='center', va='center', fontsize=11,
                color='#2B2B2B', fontweight='bold', zorder=5)


def terminal(ax, x, y):
    ax.add_patch(plt.Rectangle((x-0.12, y-0.12), 0.24, 0.24, fc=C_TERM, ec='white', lw=0.8, zorder=6))


def net(ax, x1, y1, x2, y2, label=None):
    ax.plot([x1, x2], [y1, y2], color=C_NET, lw=1.1, ls=(0, (4, 3)), alpha=0.8, zorder=2)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx+0.18, my+0.18, label, fontsize=8.5, color=C_SUB, ha='left')


fig, ax = plt.subplots(figsize=(15.5, 6.5))
ax.set_xlim(-1.7, 24.5)
ax.set_ylim(-1.8, 10.2)
ax.set_aspect('equal')
ax.axis('off')

# ============ 左：① 线长导向 ============
ax.add_patch(FancyBboxPatch((0.9, 0.9), 8.0, 8.0, boxstyle='round,pad=0.02,rounding_size=0.12',
                            fc='none', ec=C_OUTLINE, lw=2.0))
for tx, ty in [(4.9, 8.9), (8.9, 4.5), (2.4, 0.9), (0.9, 6.0)]:
    terminal(ax, tx, ty)
# M1 溢出右边界
mod(ax, 6.7, 5.5, 3.2, 2.4, label='M1', edge=C_OVER)
ax.add_patch(FancyBboxPatch((8.9, 5.5), 1.0, 2.4, boxstyle='round,pad=0.02,rounding_size=0.06',
                            fc=C_OVER_L, ec='none', alpha=0.85, mutation_aspect=0.6))
mod(ax, 3.6, 5.9, 2.9, 2.6, label='M2')
mod(ax, 1.2, 1.2, 2.3, 2.1, label='M3')
net(ax, 8.9, 4.5, 8.3, 5.5)
net(ax, 4.9, 8.9, 5.05, 7.2)
net(ax, 2.4, 0.9, 2.35, 1.2)
ax.annotate('超轮廓（非法）', xy=(9.6, 6.7), xytext=(11.0, 8.6),
            fontsize=10, color=C_OVER, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=C_OVER, lw=1.4))
ax.text(4.9, 9.55, '① 线长导向：块被拉向终端 → 溢出轮廓', ha='center',
        fontsize=11.5, color=C_TXT, fontweight='bold')

# ============ 中央：对冲 ============
ax.add_patch(FancyArrow(10.4, 6.4, 1.5, 0, width=0.07, color=C_BLUE, zorder=4))
ax.text(11.15, 6.85, '线长偏好 · 块分散', ha='center', fontsize=9.5, color=C_BLUE)
ax.add_patch(FancyArrow(11.9, 4.4, -1.5, 0, width=0.07, color=C_GREEN, zorder=4))
ax.text(11.15, 3.9, '轮廓偏好 · 块聚拢', ha='center', fontsize=9.5, color=C_GREEN)
c = Circle((11.15, 5.4), 0.30, fc='white', ec=C_OUTLINE, lw=1.4, zorder=4)
ax.add_patch(c)
ax.text(11.15, 5.4, '张力', ha='center', va='center', fontsize=9, color=C_TXT, zorder=5)

# ============ 右：② 轮廓导向 ============
ax.add_patch(FancyBboxPatch((12.5, 0.9), 8.0, 8.0, boxstyle='round,pad=0.02,rounding_size=0.12',
                            fc='none', ec=C_OUTLINE, lw=2.0))
for tx, ty in [(16.5, 8.9), (20.5, 4.9), (12.5, 2.7)]:
    terminal(ax, tx, ty)
mod(ax, 12.9, 1.2, 2.4, 2.4, label='M1')
mod(ax, 15.3, 1.2, 3.0, 3.3, label='M2')
mod(ax, 12.9, 3.6, 3.6, 3.5, label='M3')
net(ax, 20.5, 4.9, 16.8, 2.85, label='长线网')
net(ax, 16.5, 8.9, 14.7, 5.35, label='长线网')
net(ax, 12.5, 2.7, 14.1, 2.4)
ax.annotate('跨度大 → HPWL 高', xy=(18.7, 3.8), xytext=(18.6, 8.5),
            fontsize=10, color=C_GREEN, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=C_GREEN, lw=1.4))
ax.text(16.5, 9.55, '② 轮廓导向：块被迫聚拢 → 线网跨度大', ha='center',
        fontsize=11.5, color=C_TXT, fontweight='bold')

# ============ 底部 ============
ax.text(11.4, -1.25, '两者对冲 = 本问题核心张力：可行性必须由起点保证（q1warm 方形解），搜索以硬门约束在可行域内贪心下降（§5）',
        ha='center', fontsize=10.5, color=C_SUB)

ax.set_title('Q2-图1  核心张力：线长优化 vs 轮廓约束对冲', fontsize=14, fontweight='bold', pad=12)
fig.tight_layout()
p = os.path.join(OUT, 'Q2_01_核心张力.png')
fig.savefig(p, dpi=200, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved', os.path.basename(p), '(v3 素雅)')
