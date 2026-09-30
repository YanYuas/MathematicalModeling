# -*- coding: utf-8 -*-
"""m_merge_layout.py — Q1 三组布图横向合并 + 统一注脚
重渲染（与 m_visualize 同源确定性 FFD 构造，数字已复现对齐定稿）：
  3 面板横向：各保留布图 + W/H 尺寸线（证据）
  去掉每图右侧大信息卡（合并后冗余）→ 面板下各一条紧凑指标条
  底部统一注脚：图例 + 三组关键指标单行（替代原 3 个分散脚注）
"""
import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.gridspec import GridSpec

from m_data import load_blocks, Block
from m_construct import construct_initial_tree

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"
OUT = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\CLAUDE工作文件\编程手\Q1\编程手反馈\问题1独立实现"

T = {
    'fill_normal': '#D6EAF8', 'edge_normal': '#2874A6',
    'fill_strip': '#FDEBD0', 'edge_strip': '#D35400',
    'outline': '#C0392B',
    'f_title': 15, 'f_ann': 9, 'f_cap': 10, 'f_foot': 9.5,
}
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

CONF = {'n100': (True, 443), 'n200': (False, 432), 'n300': (True, 533)}


def rotate_strips(blocks, threshold=2.5):
    return [Block(b.idx, b.name, max(b.w, b.h), min(b.w, b.h)) if b.aspect_ratio() >= threshold
            else Block(b.idx, b.name, b.w, b.h) for b in blocks]


def dimension_arrow(ax, x1, y1, x2, y2, color='#2C3E50'):
    """尺寸线（两端箭头），数字标注由调用处单独外移放置，避免与轮廓边界重合。"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='<->', color=color, lw=1.0))


# 预计算三组数据
DATA = {}
for n, (use_rot, target) in CONF.items():
    blk = load_blocks(os.path.join(BASE, f'{n}.blocks'))
    A = sum(b.area for b in blk)
    strip_idx = {b.idx for b in blk if b.aspect_ratio() >= 2.5}
    n_strip = len(strip_idx)
    blocks = rotate_strips(blk) if use_rot else blk
    tree = construct_initial_tree(blocks, method='ffd', target_width=float(target))
    W, H, R = tree.pack()
    ds = (W * H - A) / (W * H) * 100
    method = '仅长条旋转' if target in (443, 533) else '基础行堆叠'
    DATA[n] = dict(blocks=blocks, layout=tree.get_layout(), strip_idx=strip_idx,
                   W=W, H=H, A=A, ds=ds, R=R, target=target, method=method, n_strip=n_strip)

order = ['n100', 'n200', 'n300']

# 画布：3 面板单行 + 面板下信息卡 + 图例/统一注脚
ACCENT = {'n100': '#2874A6', 'n200': '#1E8449', 'n300': '#D35400'}
fig = plt.figure(figsize=(18.5, 8.0), facecolor='white')
gs = GridSpec(1, 3, width_ratios=[443, 432, 533], wspace=0.035,
              left=0.015, right=0.995, top=0.93, bottom=0.21)
axs = {}

for ci, n in enumerate(order):
    d = DATA[n]
    ax = fig.add_subplot(gs[0, ci])
    axs[n] = ax
    fs = {200: 5, 100: 7, 300: 5}[len(d['blocks'])]
    for idx, x, y, w, h in d['layout']:
        is_strip = idx in d['strip_idx']
        face = T['fill_strip'] if is_strip else T['fill_normal']
        edge = T['edge_strip'] if is_strip else T['edge_normal']
        lw = 1.2 if is_strip else 0.8
        ax.add_patch(Rectangle((x, y), w, h, facecolor=face, edgecolor=edge,
                               linewidth=lw, alpha=0.92))
        cx, cy = x + w / 2, y + h / 2
        if w >= 30 and h >= 25:
            ax.text(cx, cy, str(idx), ha='center', va='center', fontsize=fs, color='#1A5276')
        else:
            ax.text(cx, cy, str(idx), ha='center', va='center', fontsize=fs - 1,
                    rotation=90, color='#1A5276')
    ax.add_patch(Rectangle((0, 0), d['W'], d['H'], fill=False, edgecolor=T['outline'],
                           linewidth=2.8))
    dimension_arrow(ax, 0, -d['W'] * 0.028, d['W'], -d['W'] * 0.028)
    dimension_arrow(ax, -d['H'] * 0.028, 0, -d['H'] * 0.028, d['H'])
    ax.text(d['W'] / 2, -d['W'] * 0.085, f'W={d["W"]:.0f}', ha='center', va='top',
            fontsize=T['f_ann'], color='#2C3E50')
    ax.text(-d['H'] * 0.085, d['H'] / 2, f'H={d["H"]:.0f}', ha='center', va='center',
            fontsize=T['f_ann'], color='#2C3E50')
    ax.set_xlim(-d['W'] * 0.15, d['W'] * 1.02)
    ax.set_ylim(-d['H'] * 0.15, d['H'] * 1.02)
    ax.set_aspect('equal')
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color('#BDC3C7')
    ax.set_title(f'{n} 布图结果（{d["W"]:.0f}×{d["H"]:.0f}）', fontsize=T['f_title'],
                 color=ACCENT[n], fontweight='bold')

# 面板下信息卡：居中于各自面板（圆角白卡 + 面板主题色描边），替代原右侧信息卡
CAP_FS = 11.5
for n in order:
    d = DATA[n]
    pos = axs[n].get_position()
    xc = (pos.x0 + pos.x1) / 2
    cap = f'死区 {d["ds"]:.2f}% ｜ R={d["R"]:.3f} ｜ 面积 {d["W"]*d["H"]:,.0f} ｜ 长条 {d["n_strip"]} ｜ {d["method"]}'
    fig.text(xc, 0.155, cap, ha='center', va='center', fontsize=CAP_FS, color='#2C3E50',
             bbox=dict(boxstyle='round,pad=0.45', fc='white', ec=ACCENT[n], lw=1.4))

# 底部统一注脚（优化点：原每图底部/右侧分散信息 → 全图一条）
fig.text(0.5, 0.028, '注：三组最小包络 443×442 / 432×432 / 533×532，死区 8.33% / 5.86% / 3.66%，总面积 '
         '179,501 / 175,696 / 273,170；n100、n300 为长条旋转构造，n200 为基础行堆叠（FFD 确定性构造，数字同 Q1 定稿）。',
         ha='center', va='center', fontsize=10.5, color='#5D6D7E')

# 图例色块（fig 坐标，左下角）
lx = 0.02
for label, fc, ec in [('普通块', T['fill_normal'], T['edge_normal']),
                      ('长条块 AR≥2.5', T['fill_strip'], T['edge_strip']),
                      ('外框=轮廓', 'white', T['outline'])]:
    fig.add_artist(Rectangle((lx, 0.095), 0.012, 0.014, facecolor=fc, edgecolor=ec,
                             linewidth=1.2, transform=fig.transFigure, clip_on=False))
    fig.text(lx + 0.0145, 0.102, label, fontsize=9, color='#2C3E50', va='center')
    lx += 0.013 + (0.105 if '外框' in label else 0.10)

p = os.path.join(OUT, 'layout_merged.png')
fig.savefig(p, dpi=150, facecolor='white')
print(f'merged → {os.path.basename(p)}')
