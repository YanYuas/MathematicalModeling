# -*- coding: utf-8 -*-
"""m3_breakthrough.py — M3 突破优化：溢出重定位
n100/n200 临界 gap 仅 1，尝试局部修复压进
"""
import os, sys, math
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path: sys.path.insert(0, _here)

from m2_data import load, Block
from m2_init import ffd_order_layout, skyline_order, orders


def rot_blk(blk, mode='tall'):
    """旋转策略: 'tall' = AR>=2.5 长边水平"""
    out = []
    for b in blk:
        if mode == 'tall':
            if max(b.w, b.h) / min(b.w, b.h) >= 2.5:
                out.append(Block(b.idx, b.name, max(b.w, b.h), min(b.w, b.h)))
            else:
                out.append(b)
        else:
            out.append(b)
    return out


def h_desc_layout(blk, S):
    """h_desc 行堆叠，返回 (feasible, W, H, layout)"""
    order = sorted(range(len(blk)), key=lambda i: -blk[i].h)
    layout = ffd_order_layout(blk, order, float(S))
    W = max((x + blk[i].w for i, x, y in layout), default=0.0)
    H = max((y + blk[i].h for i, x, y in layout), default=0.0)
    return (W <= S + 1e-9 and H <= S + 1e-9), W, H, layout


def row_decompose(blk, layout, S):
    """将布局分解为行。返回 rows = [{block_idx: (x,y)}, ...]"""
    # 按 y 坐标分组
    items = [(i, x, y, blk[i].h) for i, x, y in layout]
    items.sort(key=lambda t: t[2])  # sort by y
    rows = []
    current_row = {}
    current_y = None
    for idx, x, y, h in items:
        if current_y is None or abs(y - current_y) > 1:  # new row
            if current_row:
                rows.append((current_y, current_row))
            current_row = {}
            current_y = y
        current_row[idx] = (x, y)
    if current_row:
        rows.append((current_y, current_row))
    return rows


def try_breakthrough(name, S_target):
    """尝试在 S_target 处突破：h_desc + 溢出行旋转/重构
    返回 (success, best_W, best_H)"""
    data = load(name)
    blk0 = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]
    blk_tall = rot_blk(blk0, 'tall')

    feasible, W, H, layout = h_desc_layout(blk_tall, S_target)
    print(f'  [{name}] S={S_target} baseline: W={W:.0f} H={H:.0f} {"可行" if feasible else "超"+str(int(max(W,H)-S_target))}')

    if feasible:
        return True, W, H

    # 尝试1: 溢出行内每个块旋转90°
    # 找到高度超 S 的行
    rows = row_decompose(blk_tall, layout, S_target)
    overflow_rows = []
    for y, row_items in rows:
        row_h = max(blk_tall[i].h for i in row_items)
        if y + row_h > S_target:
            overflow_rows.append((y, row_items, row_h))

    if not overflow_rows:
        print(f'    无溢出行（罕见）')
        return False, W, H

    y0, row_items, row_h = overflow_rows[0]
    # 溢出量
    overflow = (y0 + row_h) - S_target
    print(f'    溢出行: y={y0:.0f}, 含{len(row_items)}块, 行高={row_h:.0f}, 溢出={overflow:.0f}')

    # 尝试：对溢出行中的每个块，尝试旋转(undo tall → original)后重打包
    for idx in list(row_items.keys()):
        blk_mod = list(blk_tall)
        orig_b = blk0[idx]
        tall_b = blk_tall[idx]
        # 如果被 tall 旋转过，还原则 w/h 互换
        if tall_b.w != orig_b.w or tall_b.h != orig_b.h:
            blk_mod[idx] = Block(idx, orig_b.name, orig_b.w, orig_b.h)
        else:
            # 没被 tall 旋过，尝试旋转90°
            blk_mod[idx] = Block(idx, orig_b.name, orig_b.h, orig_b.w)

        f, w, h, _ = h_desc_layout(blk_mod, S_target)
        if f:
            print(f'    >>> 突破! 旋转 b{idx} ({orig_b.name}) 后可行: W={w:.0f} H={h:.0f}')
            return True, w, h

    # 尝试2: 对溢出行中的每个块，尝试旋转(undo tall → original)后再尝试
    # 将溢出行中所有 tall 块全部还原
    blk_mod = list(blk_tall)
    changed = 0
    for idx in row_items:
        orig_b = blk0[idx]
        tall_b = blk_tall[idx]
        if tall_b.w != orig_b.w or tall_b.h != orig_b.h:
            blk_mod[idx] = Block(idx, orig_b.name, orig_b.w, orig_b.h)
            changed += 1
    if changed > 0:
        f, w, h, _ = h_desc_layout(blk_mod, S_target)
        if f:
            print(f'    >>> 突破! 溢出{changed}块还原原始方向后可行: W={w:.0f} H={h:.0f}')
            return True, w, h
        else:
            print(f'    溢出{changed}块还原: W={w:.0f} H={h:.0f} 仍超{int(max(w,h)-S_target)}')

    # 尝试3: skyline_h 策略
    order = sorted(range(len(blk_tall)), key=lambda i: -blk_tall[i].h)
    layout_s = skyline_order(blk_tall, order, float(S_target))
    W_s = max((x + blk_tall[i].w for i, x, y in layout_s), default=0.0)
    H_s = max((y + blk_tall[i].h for i, x, y in layout_s), default=0.0)
    f_s = W_s <= S_target + 1e-9 and H_s <= S_target + 1e-9
    if f_s:
        print(f'    >>> 突破! skyline_h: W={W_s:.0f} H={H_s:.0f}')
        return True, W_s, H_s
    else:
        print(f'    skyline_h: W={W_s:.0f} H={H_s:.0f} 超{int(max(W_s,H_s)-S_target)}')

    # 尝试4: skyline 按面积排序
    order_a = sorted(range(len(blk_tall)), key=lambda i: -blk_tall[i].area)
    layout_a = skyline_order(blk_tall, order_a, float(S_target))
    W_a = max((x + blk_tall[i].w for i, x, y in layout_a), default=0.0)
    H_a = max((y + blk_tall[i].h for i, x, y in layout_a), default=0.0)
    f_a = W_a <= S_target + 1e-9 and H_a <= S_target + 1e-9
    if f_a:
        print(f'    >>> 突破! skyline_area: W={W_a:.0f} H={H_a:.0f}')
        return True, W_a, H_a
    else:
        print(f'    skyline_area: W={W_a:.0f} H={H_a:.0f} 超{int(max(W_a,H_a)-S_target)}')

    return False, W, H


if __name__ == '__main__':
    print('=== M3 突破优化 ===')
    # n100: try S=442 (Q1M-1=442)
    ok100, w100, h100 = try_breakthrough('n100', 442)
    if ok100:
        data = load('n100')
        gamma = (442**2 - data['area']) / data['area']
        print(f'\n  n100 突破成功! S=442, Γ*={gamma:.4f}')
    else:
        print(f'\n  n100 未突破，保持 S=443')

    print()

    # n200: try S=431 (Q1M-1=431)
    ok200, w200, h200 = try_breakthrough('n200', 431)
    if ok200:
        data = load('n200')
        gamma = (431**2 - data['area']) / data['area']
        print(f'\n  n200 突破成功! S=431, Γ*={gamma:.4f}')
    else:
        print(f'\n  n200 未突破，保持 S=432')

    print()
    print('=== M3 完成 ===')
