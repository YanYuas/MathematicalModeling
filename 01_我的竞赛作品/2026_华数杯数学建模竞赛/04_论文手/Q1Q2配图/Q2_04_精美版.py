# -*- coding: utf-8 -*-
"""Q2_04 精美版 v3 — HPWL = 两个正交投影之和（素雅配色 + 干净排版）
色板与 Q2_01 统一：赭红包围盒 + 深蓝/墨绿跨度 + 柔和浅填充。
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.dirname(os.path.abspath(__file__))

C_PIN = '#2F3542'
C_BOX_E = '#EF6A5A'
C_BOX_F = '#FCE8E5'
C_X = '#5C9BD6'
C_Y = '#6BBF59'
C_PROJ = '#CBD5E1'
C_SUB = '#7A8794'
C_TXT = '#2F3542'

pts = [(2, 1), (5, 3), (4, 6), (7, 2)]
x_min, x_max = 2, 7
y_min, y_max = 1, 6
sx, sy = x_max - x_min, y_max - y_min

fig, ax = plt.subplots(figsize=(9.2, 6.8))
ax.set_xlim(-3.4, 10.0)
ax.set_ylim(-1.9, 9.3)
ax.set_aspect('equal')
ax.axis('off')

# 包围盒（柔和浅红）
ax.add_patch(FancyBboxPatch((x_min, y_min), sx, sy,
                            boxstyle='round,pad=0.02,rounding_size=0.12',
                            fc=C_BOX_F, ec=C_BOX_E, lw=1.8, alpha=0.9))

# 投影虚线（极淡）
for a, b, kind in [(x_min, y_min, 'v'), (x_max, y_max, 'v'), (y_min, x_min, 'h'), (y_max, x_max, 'h')]:
    if kind == 'v':
        ax.plot([a, a], [0, b], color=C_PROJ, lw=0.9, ls=(0, (3, 3)), alpha=0.9)
    else:
        ax.plot([0, b], [a, a], color=C_PROJ, lw=0.9, ls=(0, (3, 3)), alpha=0.9)

# 引脚点 + 标号
for i, (px, py) in enumerate(pts, 1):
    ax.scatter([px], [py], s=130, c=C_PIN, edgecolor='white', lw=1.4, zorder=6)
    ax.text(px + 0.20, py - 0.36, f'p{i}', fontsize=10, color=C_PIN, fontweight='bold', zorder=7)

# x 跨度
ax.annotate('', xy=(x_min, -0.55), xytext=(x_max, -0.55),
            arrowprops=dict(arrowstyle='<->', color=C_X, lw=1.8))
ax.text((x_min + x_max)/2, -1.0, f'span_x = {x_max}−{x_min} = {sx}', ha='center',
        fontsize=12, color=C_X, fontweight='bold')
# y 跨度
ax.annotate('', xy=(-0.55, y_min), xytext=(-0.55, y_max),
            arrowprops=dict(arrowstyle='<->', color=C_Y, lw=1.8))
ax.text(-1.4, (y_min + y_max)/2, f'span_y = {y_max}−{y_min} = {sy}', va='center',
        fontsize=12, color=C_Y, fontweight='bold')
ax.text(9.1, -0.55, 'x', fontsize=12, color=C_SUB)
ax.text(-0.55, 9.0, 'y', fontsize=12, color=C_SUB)

# 公式卡
fb = FancyBboxPatch((5.0, 6.3), 4.6, 2.55, boxstyle='round,pad=0.28',
                    fc='white', ec='#D5DBE2', lw=1.3)
ax.add_patch(fb)
ax.text(7.3, 8.25, 'HPWL = span_x + span_y', ha='center', fontsize=12.5,
        color=C_TXT, fontweight='bold')
ax.text(7.3, 7.55, f'= {sx} + {sy} = {sx + sy}', ha='center', fontsize=13,
        color=C_BOX_E, fontweight='bold')
ax.text(7.3, 6.85, '包围盒半周长', ha='center', fontsize=9.5, color=C_SUB)

ax.text(3.3, -1.5, '几何本质：HPWL 是 x、y 两个正交投影长度之和；2-pin 网时退化为两点 L1 距离（见 Q2-图5）',
        ha='center', fontsize=10, color=C_SUB)

ax.set_title('Q2-图4  HPWL = 两个正交投影之和（包围盒半周长）', fontsize=14, fontweight='bold', pad=10)
fig.tight_layout()
p = os.path.join(OUT, 'Q2_04_HPWL投影.png')
fig.savefig(p, dpi=200, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved', os.path.basename(p), '(v3 素雅)')
