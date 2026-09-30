# -*- coding: utf-8 -*-
"""Q2_06 精美版 v3 — 轮廓可行性判据 A·R ≤ S²（素雅配色 + 干净排版）
色板与 Q2_01/04 统一：深蓝曲线 + 柔和浅蓝可行区 + 墨绿/赭红示例点。
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.dirname(os.path.abspath(__file__))

C_CURVE = '#5C9BD6'
C_FEAS = '#DCEBFA'
C_OK = '#6BBF59'
C_BAD = '#EF6A5A'
C_TXT = '#2F3542'
C_SUB = '#7A8794'
C_GRID = '#EDF1F5'

fig, ax = plt.subplots(figsize=(8.8, 6.5))
x = np.linspace(0.05, 3.0, 500)

ax.plot(x, 1/x, color=C_CURVE, lw=2.4, label='可行边界 A·R = S²（即 M = S）')
ax.fill_between(x, 0, 1/x, color=C_FEAS, alpha=0.9, label='可行区域  A·R ≤ S²')

ax.axvline(1.0, color=C_SUB, ls=(0, (4, 3)), lw=1.3)
ax.text(1.05, 1.85, 'A = S²（仅面积达标不充分）', fontsize=9.5, color=C_SUB)

# 示例点
ax.scatter([1.0], [0.65], s=120, c=C_OK, edgecolor='white', lw=1.4, zorder=6)
ax.text(1.09, 0.84, '可行：A·R = 0.65 < 1', fontsize=9.5, color=C_OK)
ax.scatter([1.6], [1.0], s=120, c=C_BAD, edgecolor='white', lw=1.4, zorder=6)
ax.text(1.69, 1.19, '不可行：A·R = 1.6 > 1', fontsize=9.5, color=C_BAD)
# 瘦长反例
ax.scatter([0.5], [2.5], s=120, c=C_BAD, edgecolor='white', lw=1.4, zorder=6, marker='^')
ax.annotate('瘦长反例：A = 0.5·S² 达标，\n但 R = 2.5 → A·R = 1.25 > 1 不可行',
            xy=(0.5, 2.5), xytext=(1.35, 2.62),
            fontsize=9.5, color=C_BAD, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=C_BAD, lw=1.3))

# 判据卡
ax.text(0.16, 0.30, 'M ≤ S 当且仅当 A·R ≤ S²', fontsize=12.5, color=C_TXT,
        fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.45', fc='white', ec='#D5DBE2', lw=1.3))

ax.set_xlim(0, 3.0)
ax.set_ylim(0, 2.95)
ax.set_xlabel('A / S² （打包面积 / 轮廓面积）', fontsize=11)
ax.set_ylabel('R（长宽比 = max/min）', fontsize=11)
ax.legend(loc='upper right', fontsize=9.5, framealpha=0.9)
ax.grid(True, color=C_GRID, lw=0.7, alpha=0.8)
ax.set_title('Q2-图6  轮廓可行性判据 A·R ≤ S²（不能仅以面积判可行）', fontsize=13, fontweight='bold')
fig.tight_layout()
p = os.path.join(OUT, 'Q2_06_可行性区域.png')
fig.savefig(p, dpi=200, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved', os.path.basename(p), '(v3 素雅)')
