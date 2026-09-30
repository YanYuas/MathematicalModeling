"""
m_v1_archive.py — 重现初版六图（PRD 重绘前）作为归档素材
初版风格：tab20 彩色块 + 红色外框 + 简单标题；扫描 = 双曲线 + 最优点标注。
输出：归档_初版图/layout_n*.png + scan_n*.png
"""
import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from m_data import load_blocks, Block
from m_construct import construct_initial_tree, ffd_max_side
from m_btree import check_overlap

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '归档_初版图')
os.makedirs(OUT, exist_ok=True)
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

CONF = {'n100': (True, 443), 'n200': (False, 432), 'n300': (True, 533)}


def rotate_strips(blocks, threshold=2.5):
    return [Block(b.idx, b.name, max(b.w, b.h), min(b.w, b.h)) if b.aspect_ratio() >= threshold
            else Block(b.idx, b.name, b.w, b.h) for b in blocks]


def plot_floorplan_v1(blocks, target, n):
    tree = construct_initial_tree(blocks, method='ffd', target_width=float(target))
    W, H, R = tree.pack()
    layout = tree.get_layout()
    A_total = sum(b.area for b in blocks)
    ds = (W * H - A_total) / (W * H) * 100
    no_ov, _ = check_overlap(layout)

    fig, ax = plt.subplots(figsize=(10, 10))
    colors = plt.cm.tab20.colors
    for idx, x, y, w, h in layout:
        ax.add_patch(Rectangle((x, y), w, h, facecolor=colors[idx % 20],
                               edgecolor='black', linewidth=0.5, alpha=0.85))
        cx, cy = x + w / 2, y + h / 2
        if w > 25 and h > 20:
            ax.text(cx, cy, str(idx), ha='center', va='center', fontsize=5)
        else:
            ax.text(cx, cy, str(idx), ha='center', va='center', fontsize=4, rotation=90)
    ax.add_patch(Rectangle((0, 0), W, H, fill=False, edgecolor='red', linewidth=2.5))
    ax.set_xlim(-5, W + 5)
    ax.set_ylim(-5, H + 5)
    ax.set_aspect('equal')
    ax.set_title(f'{n}: {W:.0f}×{H:.0f}  R={R:.3f}  死区={ds:.2f}%  无重叠={no_ov}')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f'layout_{n}.png'), dpi=130)
    plt.close(fig)
    print(f'  [归档] layout_{n}.png ({W:.0f}×{H:.0f})')


def plot_scan_v1(blk_base, blk_rot, n, lb):
    xs = list(range(lb, lb + 26))
    y_base = [ffd_max_side(blk_base, float(t)) for t in xs]
    y_rot = [ffd_max_side(blk_rot, float(t)) for t in xs]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(xs, y_base, 'o-', label='基础行堆叠', markersize=3)
    ax.plot(xs, y_rot, 's--', label='仅长条旋转', markersize=3)
    ax.plot(xs, xs, 'k:', label='y = target', linewidth=0.8)
    for y, lab in ((y_base, '基础'), (y_rot, '旋转')):
        for t, m in zip(xs, y):
            if m <= t:
                ax.axvline(t, color='green', alpha=0.3)
                ax.annotate(f'{lab}最优 {t}', xy=(t, m), xytext=(t + 1, m + 8),
                            arrowprops=dict(arrowstyle='->'), fontsize=9)
                break
    ax.set_xlabel('target_width')
    ax.set_ylabel('FFD 行堆叠 max(W,H)')
    ax.set_title(f'{n} target_width 扫描（最低交叉点 = 最优边长）')
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f'scan_{n}.png'), dpi=130)
    plt.close(fig)
    print(f'  [归档] scan_{n}.png')


print(f'=== 初版图归档 → {OUT} ===')
for n, (use_rot, target) in CONF.items():
    blk = load_blocks(os.path.join(BASE, f'{n}.blocks'))
    lb = math.ceil(math.sqrt(sum(b.area for b in blk)))
    blocks = rotate_strips(blk) if use_rot else blk
    plot_floorplan_v1(blocks, target, n)
    plot_scan_v1(blk, rotate_strips(blk), n, lb)
print('归档完成')
