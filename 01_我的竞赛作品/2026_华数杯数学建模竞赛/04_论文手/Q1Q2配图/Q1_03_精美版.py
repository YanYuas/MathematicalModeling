# -*- coding: utf-8 -*-
"""Q1_03 精美版 — B*-Tree 与布局一一对应（修正版）
修正：2×2 网格中 D 在 C 右侧 → 按"左子=右邻块"规则 D 是 C 的**左子**（原图误标 C 右子，且有散线）。
设计：左=布局（圆角模块+尺寸标注+包络框）→ 中=编码箭头 → 右=B*-Tree（节点颜色对齐模块，边标左/右）。
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrow

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.dirname(os.path.abspath(__file__))

# design tokens（活泼中饱和色板）
CM = {  # 模块颜色（布局框 与 树节点 共用）
    'A': '#5C9BD6', 'B': '#6BBF59', 'C': '#9575CD', 'D': '#E5B155',
}
C_EDGE = '#566573'   # 树边
C_OUT = '#EF6A5A'    # 包络框（珊瑚红）
C_ANNOT = '#7A8794'  # 说明文字
C_CORR = '#C5CFDA'   # 对应箭头（淡蓝灰）


def mod_box(ax, x0, y0, w, h, name, fc, label_sub):
    """圆角模块：主标(名) + 副标(尺寸)。"""
    box = FancyBboxPatch((x0, y0), w, h, boxstyle='round,pad=0.03,rounding_size=0.12',
                         fc=fc, ec='white', lw=2, alpha=0.95, mutation_aspect=0.5)
    ax.add_patch(box)
    cx, cy = x0 + w/2, y0 + h/2
    ax.text(cx, cy + 0.16, name, ha='center', va='center', fontsize=17,
            color='white', fontweight='bold', zorder=5)
    ax.text(cx, cy - 0.30, label_sub, ha='center', va='center', fontsize=8.5,
            color='white', alpha=0.9, zorder=5)


def tree_node(ax, x, y, name, fc, r=0.34):
    c = Circle((x, y), r, fc=fc, ec='white', lw=2, zorder=6)
    ax.add_patch(c)
    ax.text(x, y, name, ha='center', va='center', fontsize=14, color='white',
            fontweight='bold', zorder=7)


def tree_edge(ax, x1, y1, x2, y2, is_right=False, label=''):
    ls = '--' if is_right else '-'
    ax.plot([x1, x2], [y1, y2], color=C_EDGE, lw=2.0, ls=ls, zorder=3)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx+0.10, my+0.06, label, fontsize=8.5, color=C_ANNOT,
                ha='left', va='bottom')


fig, ax = plt.subplots(figsize=(14, 6.0))
ax.set_xlim(-0.6, 16.2)
ax.set_ylim(-1.2, 4.9)
ax.set_aspect('equal')
ax.axis('off')

# ========== 左：布局（2×2 网格，每模块 3×2）==========
# A(0,0) B(3,0) / C(0,2) D(3,2)
mod_box(ax, 0.0, 0.0, 3, 2, 'A', CM['A'], '3×2 · 根')
mod_box(ax, 3.0, 0.0, 3, 2, 'B', CM['B'], '3×2 · A左')
mod_box(ax, 0.0, 2.0, 3, 2, 'C', CM['C'], '3×2 · A右')
mod_box(ax, 3.0, 2.0, 3, 2, 'D', CM['D'], '3×2 · C左')
# 包络框
ax.add_patch(FancyBboxPatch((0, 0), 6, 4, boxstyle='round,pad=0.02,rounding_size=0.08',
                            fc='none', ec=C_OUT, lw=2.2))
# 包络尺寸
ax.annotate('', xy=(0, -0.35), xytext=(6, -0.35),
            arrowprops=dict(arrowstyle='<->', color=C_ANNOT, lw=1.2))
ax.text(3, -0.6, 'W=6', ha='center', fontsize=10, color=C_ANNOT)
ax.annotate('', xy=(-0.35, 0), xytext=(-0.35, 4),
            arrowprops=dict(arrowstyle='<->', color=C_ANNOT, lw=1.2))
ax.text(-0.62, 2, 'H=4', va='center', fontsize=10, color=C_ANNOT)
ax.text(3, 4.45, '布局（bottom-left 压实）', ha='center', fontsize=12,
        color=C_EDGE, fontweight='bold')

# 模块 → 树节点 对应箭头（淡色，强调一一对应）
corr = {
    'A': ((1.5, 1.0), (11.0, 4.0)),
    'B': ((4.5, 1.0), (9.0, 2.0)),
    'C': ((1.5, 3.0), (13.0, 2.0)),
    'D': ((4.5, 3.0), (11.8, 0.4)),
}
for _name, ((sx, sy), (tx, ty)) in corr.items():
    ax.annotate('', xy=(tx, ty), xytext=(sx, sy),
                arrowprops=dict(arrowstyle='-', color=C_CORR, lw=0.9, alpha=0.6,
                                connectionstyle='arc3,rad=0.18'))

# ========== 中：编码箭头 ==========
ax.annotate('', xy=(7.9, 2.0), xytext=(6.6, 2.0),
            arrowprops=dict(arrowstyle='->', color=C_OUT, lw=2.6))
ax.text(7.25, 2.5, 'B*-Tree\n编码', ha='center', fontsize=11,
        color=C_OUT, fontweight='bold')

# ========== 右：B*-Tree ==========
# 根 A；A 左子=B（右邻），A 右子=C（上方）；C 左子=D（右邻）
tree_edge(ax, 11.0, 3.66, 9.0, 2.34, is_right=False, label='左子=右邻')
tree_edge(ax, 11.0, 3.66, 13.0, 2.34, is_right=True,  label='右子=上方')
tree_edge(ax, 13.0, 1.66, 11.8, 0.74, is_right=False, label='左子=右邻')
tree_node(ax, 11.0, 4.0, 'A', CM['A'])
tree_node(ax, 9.0, 2.0, 'B', CM['B'])
tree_node(ax, 13.0, 2.0, 'C', CM['C'])
tree_node(ax, 11.8, 0.4, 'D', CM['D'])
ax.text(11.0, 4.62, '根（左下角模块）', ha='center', fontsize=9.5, color=C_ANNOT)
ax.text(13.2, 0.42, '叶', ha='left', va='center', fontsize=9, color=C_ANNOT)
ax.text(11.0, -0.75, 'B*-Tree（先序遍历解码）', ha='center', fontsize=12,
        color=C_EDGE, fontweight='bold')

# ========== 底部规则说明 ==========
ax.text(7.3, -1.15, '规则：左子树 = 同行右邻块（B 在 A 右侧 → B 是 A 左子；D 在 C 右侧 → D 是 C 左子）；'
        '右子树 = 正上方块（C 在 A 上方 → C 是 A 右子）。',
        ha='center', fontsize=10, color=C_ANNOT)

ax.set_title('Q1-图3  B*-Tree 与布局一一对应（左子=右邻，右子=上方）',
             fontsize=14, fontweight='bold', pad=14)

fig.tight_layout()
p = os.path.join(OUT, 'Q1_03_BSTree对应.png')
fig.savefig(p, dpi=200, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved', os.path.basename(p), '(精美版，已修正 D 为 C 左子)')
