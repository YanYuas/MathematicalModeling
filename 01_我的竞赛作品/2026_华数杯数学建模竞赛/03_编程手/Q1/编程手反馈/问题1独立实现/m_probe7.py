"""
m_probe7.py — 行堆叠排序变体扫描（n100）
h降序(基准443) vs w降序 vs 随机×5 seed vs 面积降序
找 n100 <443 的构造排序
"""
import os
import math
import random
from m_data import load_blocks, Block

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"
blk = load_blocks(os.path.join(BASE, 'n100.blocks'))
A = sum(b.area for b in blk)
lb = math.ceil(math.sqrt(A))


def ffd_sort(blocks, order):
    """按给定顺序 FFD 行堆叠。order: 索引排列。返回 max(W,H)。"""
    layout, rows = [], []
    for idx in order:
        b = blocks[idx]
        placed = False
        for ri, (ry, rh, rw) in enumerate(rows):
            if rw + b.w <= tw_global:
                layout.append((idx, rw, ry))
                rows[ri] = (ry, max(rh, b.h), rw + b.w)
                placed = True
                break
        if not placed:
            ry = sum(r[1] for r in rows) if rows else 0.0
            layout.append((idx, 0.0, ry))
            rows.append((ry, b.h, b.w))
    W = max(x + blk[i].w for i, x, y in layout)
    ys = sorted({y for _, _, y in layout})
    H = sum(max(blk[i].h for i, _, yy in layout if abs(yy - y) < 1e-6) for y in ys)
    return max(W, H)


def scan(order, label, lo=424, hi=460):
    global tw_global
    for tw in range(lo, hi + 1):
        tw_global = tw
        m = ffd_sort(blk, order)
        if m <= tw:
            return tw, m
    return None, None


# h 降序（基准）
order_h = sorted(range(len(blk)), key=lambda i: blk[i].h, reverse=True)
tw, m = scan(order_h, 'h降序')
print(f"h降序: target={tw} max={m:.0f}")

# w 降序
order_w = sorted(range(len(blk)), key=lambda i: blk[i].w, reverse=True)
tw, m = scan(order_w, 'w降序')
print(f"w降序: target={tw} max={m:.0f}" if tw else "w降序: 无可行")

# 随机 5 seed
random.seed(0)
best = None
for s in range(5):
    order_r = list(range(len(blk)))
    random.shuffle(order_r)
    tw, m = scan(order_r, f'随机{s}')
    tag = f"随机{s}: target={tw} max={m:.0f}" if tw else f"随机{s}: 无可行"
    print(tag)
    if tw and (best is None or tw < best[0]):
        best = (tw, m)
print(f"\n最佳排序: {'h降序' if best is None or best[0]>=443 else '找到更好'} "
      f"({best[0]} vs 基准443)" if best else "无更优")
