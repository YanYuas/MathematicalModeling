# -*- coding: utf-8 -*-
"""m2_init.py — Q2 独立实现 阶段P2：构造初始化（线长导向）
目标：terminal-aware 构造，块向连接终端扩散，同时打包合法可转 B*-Tree。
方法：终端偏好坐标 + 多种排序 × skyline bottom-left 打包 → 转 B*-Tree。
探测：不同排序的线长/轮廓占用对比，判断 terminal-aware 价值。
"""
import math
from m2_data import Block, load
from m2_hpwl import evaluate, pack_dims, terminal_vs_internal
from m_btree import BTree, check_overlap
from m_construct import layout_to_btree, ffd_layout


def terminal_prefer(data):
    """每块偏好坐标 = 连接终端的平均位置；无终端内部块 = 图中心。
    终端固定边界 → 块被拉向连接它的终端。"""
    term = data['term_pos']
    blk_terms = {name: [] for name in data['blocks']}
    for net in data['nets']:
        ts = [p for p in net if p in term]
        if ts:
            for m in net:
                if m in data['blocks']:
                    blk_terms[m].extend(ts)
    prefer = {}
    for name in data['blocks']:
        ts = blk_terms[name]
        if ts:
            xs = [term[t][0] for t in ts]
            ys = [term[t][1] for t in ts]
            prefer[name] = (sum(xs) / len(xs), sum(ys) / len(ys))
        else:
            prefer[name] = (data['side'] / 2, data['side'] / 2)
    return prefer


def skyline_order(blocks, order, target):
    """按给定顺序 skyline 打包（bottom-left，加 target 宽度约束防竖条平铺/爆炸）。
    候选 x = 0 或各段右端，且 x+b.w ≤ target；y = [x,x+w) 最高点；选 y 最小。"""
    sky = [(0.0, float('inf'), 0.0)]
    out = []
    for idx in order:
        b = blocks[idx]
        cands = {0.0}
        for a, bb, _ in sky:
            if bb != float('inf'):
                cands.add(bb)
        best = None
        for x in sorted(cands):
            if x + b.w > target + 1e-9:
                continue
            y = max(h for a, bb, h in sky if a < x + b.w and bb > x)
            if best is None or y < best[1]:
                best = (x, y)
        x, y = best
        out.append((idx, x, y))
        be, bt = x + b.w, y + b.h
        ns = []
        for a, bb, h in sky:
            if bb <= x or a >= be:
                ns.append((a, bb, h))
            else:
                if a < x:
                    ns.append((a, x, h))
                ns.append((max(a, x), min(bb, be), bt))
                if bb > be:
                    ns.append((be, bb, h))
        ns.sort()
        merged = []
        for s in ns:
            if merged and merged[-1][1] == s[0] and abs(merged[-1][2] - s[2]) < 1e-9:
                merged[-1] = (merged[-1][0], s[1], s[2])
            else:
                merged.append(s)
        sky = merged
    return out


def orders(data, blk):
    """候选排序。返回 {名字: order列表}。"""
    prefer = terminal_prefer(data)
    A = {b.name: b.area for b in blk}
    return {
        'area_desc': sorted(range(len(blk)), key=lambda i: -A[blk[i].name]),
        'pref_x': sorted(range(len(blk)), key=lambda i: prefer[blk[i].name][0]),
        'pref_y': sorted(range(len(blk)), key=lambda i: prefer[blk[i].name][1]),
        'pref_yx': sorted(range(len(blk)), key=lambda i: (prefer[blk[i].name][1], prefer[blk[i].name][0])),
        'pref_xy': sorted(range(len(blk)), key=lambda i: (prefer[blk[i].name][0], prefer[blk[i].name][1])),
    }


def ffd_order_layout(blocks, order, target):
    """按 order 顺序行堆叠：块依次放，行内放不下开新行。整行同 y → layout_to_btree 友好。"""
    layout, rows = [], []
    for idx in order:
        b = blocks[idx]
        placed = False
        for ri, (ry, rh, rw) in enumerate(rows):
            if rw + b.w <= target:
                layout.append((idx, rw, ry))
                rows[ri] = (ry, max(rh, b.h), rw + b.w)
                placed = True
                break
        if not placed:
            ry = sum(r[1] for r in rows) if rows else 0.0
            layout.append((idx, 0.0, ry))
            rows.append((ry, b.h, b.w))
    return layout


def construct(data, order, blk=None, target=None):
    """按 order 行堆叠打包 → 转 B*-Tree。返回 (tree, layout)。"""
    if blk is None:
        blk = [Block(i, name, w, h) for i, (name, (w, h)) in enumerate(data['blocks'].items())]
    if target is None:
        target = data['side']
    layout = ffd_order_layout(blk, order, target)
    tree = layout_to_btree(blk, layout)
    return tree, layout


def q1warm_tree(data, blk=None, target=None):
    """Q1 方形解起点（warm start 迁移定理）：长条旋转 + h 降序行堆叠。
    Q1 独立实现 n100 443×442 / n200 432×432 / n300 533×532，全 < Q2 轮廓 S。"""
    if blk is None:
        blk = [Block(i, name, w, h) for i, (name, (w, h)) in enumerate(data['blocks'].items())]
    # 长条旋转预处理（AR≥2.5 长边水平）
    rot_blk = [Block(b.idx, b.name, max(b.w, b.h), min(b.w, b.h))
               if max(b.w, b.h) / min(b.w, b.h) >= 2.5 else b for b in blk]
    if target is None:
        # 用 Q1 最终边长（按块数识别数据集）
        tgt = {100: 443, 200: 432, 300: 533}.get(len(blk))
        target = tgt if tgt else data['side']
    order = sorted(range(len(rot_blk)), key=lambda i: -rot_blk[i].h)
    layout = ffd_order_layout(rot_blk, order, float(target))
    tree = layout_to_btree(rot_blk, layout)
    return tree, layout


def layout_pos_rot(data, blk, layout):
    """layout (idx,x,y) → (pos, rot)。"""
    pos, rot = {}, {}
    for idx, x, y in layout:
        b = blk[idx]
        pos[b.name] = (x, y)
        rot[b.name] = False
    return pos, rot


def compare_orders(data, blk, target=None, verbose=True):
    """对比各排序：线长 / 轮廓占用 / 是否超轮廓。"""
    res = {}
    for oname, order in orders(data, blk).items():
        tree, layout = construct(data, order, blk, target)
        W, H, R = tree.pack()
        pos, rot = layout_pos_rot(data, blk, layout)
        wl, _, _ = evaluate(data, pos, rot)
        io_t, in_t = terminal_vs_internal(data, pos, rot)
        M = max(W, H)
        feas = M <= data['side'] + 1e-6
        res[oname] = dict(wl=wl, W=W, H=H, R=R, feas=feas, io=io_t, internal=in_t)
        if verbose:
            print(f'  {oname:10s}: HPWL={wl:>9,.0f}  {W:.0f}x{H:.0f}  '
                  f'{"可行" if feas else "超轮廓"}{"!" if not feas else ""}  '
                  f'I/O={io_t:,.0f} 内部={in_t:,.0f}')
    return res


if __name__ == '__main__':
    print('=== 阶段P2: terminal-aware 构造初始化探测 ===')
    for name in ['n100', 'n200', 'n300']:
        data = load(name)
        blk = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]
        print(f'[{name}] S={data["side"]:.2f}')
        res = compare_orders(data, blk)
        # 最优排序（可行中最小线长）
        feas = {k: v for k, v in res.items() if v['feas']}
        best = min(feas, key=lambda k: feas[k]['wl']) if feas else min(res, key=lambda k: res[k]['wl'])
        print(f'  → 最优: {best} HPWL={res[best]["wl"]:,.0f}')
    print('阶段P2: 探测完成')
