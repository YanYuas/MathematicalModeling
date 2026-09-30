"""
m_probe3.py — 构造方法对比探测
FFD行堆叠(高降序) vs FFD行堆叠(面积降序) vs skyline
目标：找 n100 比 444 更小的可行方形边长（死区<8.95%）
"""
import os
import math
from m_data import load_blocks
from m_construct import construct_initial_tree, ffd_layout, ffd_max_side
from m_btree import check_overlap

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"


def ffd_area_layout(blocks, target_width):
    """按面积降序 FFD 行堆叠"""
    srt = sorted(enumerate(blocks), key=lambda x: x[1].area, reverse=True)
    layout, rows = [], []
    for idx, b in srt:
        placed = False
        for ri, (ry, rh, rw) in enumerate(rows):
            if rw + b.w <= target_width:
                layout.append((idx, rw, ry))
                rows[ri] = (ry, max(rh, b.h), rw + b.w)
                placed = True
                break
        if not placed:
            ry = sum(r[1] for r in rows) if rows else 0.0
            layout.append((idx, 0.0, ry))
            rows.append((ry, b.h, b.w))
    return layout


def layout_max_side(blocks, layout):
    W = max(x + blocks[i].w for i, x, y in layout)
    ys = sorted({y for _, _, y in layout})
    H = 0.0
    for y in ys:
        H += max(blocks[i].h for i, _, yy in layout if abs(yy - y) < 1e-6)
    return max(W, H)


for n in ['n100', 'n200', 'n300']:
    blk = load_blocks(os.path.join(BASE, f'{n}.blocks'))
    A = sum(b.area for b in blk)
    lb = math.ceil(math.sqrt(A))
    print(f"\n[{n}] A={A:.0f} ⌈√A⌉={lb}")

    # 1. skyline 构造
    t = construct_initial_tree(blk, method='skyline')
    W, H, R = t.pack()
    ds = (W * H - A) / (W * H) * 100
    print(f"  skyline:      {W:.0f}×{H:.0f} max={max(W,H):.0f} 死区={ds:.2f}%")

    # 2. FFD高降序 在 target=LB 起扫描
    for tw in range(lb, lb + 5):
        m = ffd_max_side(blk, float(tw))
        if m <= tw:
            print(f"  FFD高降序 target={tw}: max={m:.0f} ← 首个可行")
            break
        else:
            print(f"  FFD高降序 target={tw}: max={m:.0f} (不可行)")

    # 3. FFD面积降序扫描
    for tw in range(lb, lb + 5):
        lay = ffd_area_layout(blk, float(tw))
        m = layout_max_side(blk, lay)
        if m <= tw:
            print(f"  FFD面积降序 target={tw}: max={m:.0f} ← 首个可行")
            break
        else:
            print(f"  FFD面积降序 target={tw}: max={m:.0f} (不可行)")
