"""
m_visualize.py — Q1 六张图（按配图PRD重绘）
design token 制度：色板/字体/线宽/间距 集中定义，全图引用。
layout: 普通块冷蓝 + 长条块暖橙高亮 + 红外框 + 尺寸线 + 信息卡
scan:   基础/旋转双曲线 + 可行/不可行区域 + 最优点★标注
"""
import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.gridspec import GridSpec

from m_data import load_blocks, Block
from m_construct import construct_initial_tree, ffd_max_side

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"
OUT = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\CLAUDE工作文件\编程手\Q1\编程手反馈\问题1独立实现"

# ==================== design tokens ====================
T = {
    # 色板
    'fill_normal': '#D6EAF8', 'edge_normal': '#2874A6',
    'fill_strip': '#FDEBD0', 'edge_strip': '#D35400',
    'outline': '#C0392B', 'grid': '#E8E8E8',
    'curve_base': '#2874A6', 'curve_rot': '#E67E22', 'ref': '#7F8C8D',
    'feasible': '#E8F8F5', 'infeasible': '#FDEDEC', 'annot': '#2C3E50',
    # 字体
    'f_title': 16, 'f_axis': 12, 'f_tick': 10, 'f_ann': 9, 'f_card': 11,
    # 线宽
    'l_main': 2.5, 'l_sub': 1.8, 'l_outline': 3.0, 'l_grid': 0.6,
}
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 每集：构造法（True=长条旋转）+ 最终 target
CONF = {'n100': (True, 443), 'n200': (False, 432), 'n300': (True, 533)}


def rotate_strips(blocks, threshold=2.5):
    return [Block(b.idx, b.name, max(b.w, b.h), min(b.w, b.h)) if b.aspect_ratio() >= threshold
            else Block(b.idx, b.name, b.w, b.h) for b in blocks]


def dimension_arrow(ax, x1, y1, x2, y2, label, color='#2C3E50'):
    """尺寸线：两端箭头 + 标注。"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='<->', color=color, lw=1.2))
    ax.text((x1 + x2) / 2, (y1 + y2) / 2, label, fontsize=T['f_ann'],
            color=color, ha='center', va='bottom')


def plot_floorplan(blocks, orig_blocks, target, n, outdir):
    tree = construct_initial_tree(blocks, method='ffd', target_width=float(target))
    W, H, R = tree.pack()
    layout = tree.get_layout()
    A_total = sum(b.area for b in blocks)
    ds = (W * H - A_total) / (W * H) * 100
    strip_idx = {b.idx for b in orig_blocks if b.aspect_ratio() >= 2.5}
    n_strip = len(strip_idx)
    fs = {200: 5, 100: 7, 300: 5}.get(len(blocks), 5)

    # 左绘图区 + 右信息区（GridSpec，信息卡不遮挡布局）
    fig = plt.figure(figsize=(11.5, 9.5))
    gs = GridSpec(1, 2, width_ratios=[5.5, 1.6], wspace=0.08)
    ax = fig.add_subplot(gs[0, 0])
    ax_info = fig.add_subplot(gs[0, 1])
    ax_info.axis('off')

    for idx, x, y, w, h in layout:
        is_strip = idx in strip_idx
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

    # 外框
    ax.add_patch(Rectangle((0, 0), W, H, fill=False, edgecolor=T['outline'],
                           linewidth=T['l_outline']))
    # 尺寸线
    dimension_arrow(ax, 0, -W * 0.03, W, -W * 0.03, f'W={W:.0f}')
    dimension_arrow(ax, -H * 0.03, 0, -H * 0.03, H, f'H={H:.0f}')

    ax.set_xlim(-W * 0.12, W * 1.02)
    ax.set_ylim(-H * 0.12, H * 1.02)
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color('#BDC3C7')

    method = '仅长条旋转' if target in (443, 533) else '基础行堆叠'
    ax.set_title(f'{n} 布图结果', fontsize=T['f_title'], color=T['annot'], fontweight='bold')

    # 右侧信息卡（不遮挡）
    method = '仅长条旋转' if target in (443, 533) else '基础行堆叠'
    lines = [
        ('数据集', f'{n}'),
        ('尺寸', f'{W:.0f} × {H:.0f}'),
        ('长宽比 R', f'{R:.3f}'),
        ('死区', f'{ds:.2f}%'),
        ('面积', f'{W*H:,.0f}'),
        ('构造', method),
        ('target', f'{target}'),
        ('长条块', f'{n_strip} (高亮)'),
    ]
    ax_info.text(0.02, 0.98, '结果信息', transform=ax_info.transAxes, ha='left', va='top',
                 fontsize=T['f_card'] + 1, color=T['annot'], fontweight='bold')
    y = 0.90
    for k, v in lines:
        ax_info.text(0.02, y, f'{k}：{v}', transform=ax_info.transAxes, ha='left', va='top',
                     fontsize=T['f_card'], color=T['annot'])
        y -= 0.115
    ax_info.text(0.02, 0.10, '图例', transform=ax_info.transAxes, ha='left', va='top',
                 fontsize=T['f_card'] + 1, color=T['annot'], fontweight='bold')
    ax_info.add_patch(Rectangle((0.03, 0.045), 0.25, 0.02, facecolor=T['fill_normal'],
                                edgecolor=T['edge_normal'], transform=ax_info.transAxes))
    ax_info.text(0.33, 0.045, '普通块', transform=ax_info.transAxes, fontsize=T['f_ann'],
                 color=T['annot'], va='center')
    ax_info.add_patch(Rectangle((0.03, 0.015), 0.25, 0.02, facecolor=T['fill_strip'],
                                edgecolor=T['edge_strip'], transform=ax_info.transAxes))
    ax_info.text(0.33, 0.015, '长条块 AR≥2.5', transform=ax_info.transAxes, fontsize=T['f_ann'],
                 color=T['annot'], va='center')

    fig.savefig(os.path.join(outdir, f'layout_{n}.png'), dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close(fig)
    print(f'  [layout_{n}] {W:.0f}×{H:.0f} R={R:.3f} 死区={ds:.2f}% 长条{n_strip} → layout_{n}.png')


def plot_scan(blk_base, blk_rot, n, lb, outdir):
    xs = list(range(lb, lb + 26))
    y_base = [ffd_max_side(blk_base, float(t)) for t in xs]
    y_rot = [ffd_max_side(blk_rot, float(t)) for t in xs]
    y_max = max(max(y_base), max(y_rot))
    y_min = lb - 2

    fig, ax = plt.subplots(figsize=(9.5, 6.5))
    # 可行/不可行区域：可行 = y ≤ target（y=x 对角线下方），动态 fill_between
    ax.fill_between(xs, y_min, xs, color=T['feasible'], zorder=0)
    ax.fill_between(xs, xs, y_max + 5, color=T['infeasible'], zorder=0)
    ax.text(0.99, 0.04, '可行区 (max ≤ target)', transform=ax.transAxes, ha='right',
            fontsize=T['f_ann'], color='#1E8449')
    ax.text(0.99, 0.97, '不可行区 (max > target)', transform=ax.transAxes, ha='right',
            fontsize=T['f_ann'], color='#C0392B')

    ax.plot(xs, xs, ':', color=T['ref'], lw=1.5, label='y = target')
    ax.plot(xs, y_base, 'o-', color=T['curve_base'], lw=T['l_main'],
            markersize=4, label='基础行堆叠')
    ax.plot(xs, y_rot, 's--', color=T['curve_rot'], lw=T['l_sub'],
            markersize=4, label='仅长条旋转')

    # 最优点
    opt = None
    for t, m in zip(xs, y_rot):
        if m <= t:
            opt = (t, m, 'rot')
            ax.scatter([t], [m], marker='*', s=320, color='#E67E22', zorder=5, edgecolor='white', linewidth=0.8)
            ax.annotate(f'最优 target={t}\nmax={m:.0f}', xy=(t, m), xytext=(t - 8, m + 25),
                        fontsize=T['f_ann'] + 1, color='#B9770E', fontweight='bold',
                        arrowprops=dict(arrowstyle='->', color='#B9770E', lw=1.5))
            break
    for t, m in zip(xs, y_base):
        if m <= t:
            ax.scatter([t], [m], marker='o', s=60, color='#2874A6', zorder=4, edgecolor='white')
            ax.annotate(f'基础 {t}', xy=(t, m), xytext=(t + 1, m + 10),
                        fontsize=T['f_ann'], color='#2874A6',
                        arrowprops=dict(arrowstyle='->', color='#2874A6', lw=1.0))
            break

    ax.set_xlabel('target_width (行宽上限)', fontsize=T['f_axis'])
    ax.set_ylabel('FFD 行堆叠 max(W,H)', fontsize=T['f_axis'])
    ax.set_title(f'{n} target_width 扫描 · 构造上界确定', fontsize=T['f_title'],
                 color=T['annot'], fontweight='bold')
    ax.grid(color=T['grid'], lw=T['l_grid'], ls='--', alpha=0.7)
    ax.tick_params(labelsize=T['f_tick'])
    ax.legend(loc='upper left', fontsize=T['f_ann'])
    ax.set_ylim(y_min, y_max + 5)

    fig.tight_layout(pad=0.5)
    p = os.path.join(outdir, f'scan_{n}.png')
    fig.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  [scan_{n}] 最优 target={opt[0] if opt else "?"} → {os.path.basename(p)}')


print('=== Q1 六图重绘（PRD token 体系）===')
for n, (use_rot, target) in CONF.items():
    blk = load_blocks(os.path.join(BASE, f'{n}.blocks'))
    lb = math.ceil(math.sqrt(sum(b.area for b in blk)))
    print(f'[{n}]')
    blocks = rotate_strips(blk) if use_rot else blk
    plot_floorplan(blocks, blk, target, n, OUT)
    plot_scan(blk, rotate_strips(blk), n, lb, OUT)
print('六图重绘完成')
