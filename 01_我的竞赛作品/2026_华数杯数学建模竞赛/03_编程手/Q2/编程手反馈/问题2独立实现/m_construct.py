"""
m_construct.py — 独立实现 阶段F：FFD 行堆叠构造 + 上界扫描
target_width 参数化（修复编程手 R5：固定 √A×1.05 导致 UB 口径漂移）。
扫描 target_width → 找可行方形最小边长 = 真构造上界。
"""
import math
from typing import List, Optional, Tuple
from m_data import Block
from m_btree import BTree, Node


def ffd_layout(blocks: List[Block], target_width: float) -> List[Tuple[int, float, float]]:
    """按高降序 FFD 行堆叠。行宽 ≤ target_width，行高=行内 max h。"""
    if not blocks:
        return []
    srt = sorted(enumerate(blocks), key=lambda x: x[1].h, reverse=True)
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


def ffd_max_side(blocks: List[Block], target_width: float) -> float:
    """FFD 行堆叠后 max(W,H)。W=实际行宽，H=Σ行高。"""
    layout = ffd_layout(blocks, target_width)
    W = max(x + blocks[i].w for i, x, y in layout)
    H = sum(max(blocks[i].h for i, _, y in layout if abs(y - yy) < 1e-6)
            for yy in sorted({y for _, _, y in layout}))
    # 更稳的行高求法：按 y 分组
    ys = sorted({y for _, _, y in layout})
    H = 0.0
    for y in ys:
        H += max(blocks[i].h for i, _, yy in layout if abs(yy - y) < 1e-6)
    return max(W, H)


def scan_upper_bound(blocks: List[Block], lo: int, hi: int) -> Tuple[Optional[int], float]:
    """从 lo 到 hi 扫描 target_width，找第一个 max(W,H)≤target 的可行方形边长。
    返回 (最小可行边长 or None, 该边长的 max 实测)。"""
    best = None
    best_m = None
    for wt in range(lo, hi + 1):
        m = ffd_max_side(blocks, float(wt))
        if m <= wt:
            best = wt
            best_m = m
            break
    return best, best_m


def layout_to_btree(blocks: List[Block], layout: List[Tuple[int, float, float]]) -> BTree:
    """行布局 → B*-Tree：同行左链，行首=上一行首的右孩子。"""
    blk = [Block(b.idx, b.name, b.w, b.h) for b in blocks]
    tree = BTree(blk)
    tree.nodes = {}
    if not layout:
        return tree
    srt = sorted(layout, key=lambda t: (t[2], t[1]))
    rows = []
    cur_y, cur = srt[0][2], [srt[0]]
    for it in srt[1:]:
        if abs(it[2] - cur_y) < 1e-6:
            cur.append(it)
        else:
            rows.append(cur)
            cur, cur_y = [it], it[2]
    rows.append(cur)

    root = Node(blk[rows[0][0][0]])
    tree.root = root
    tree.nodes[root.block.idx] = root
    cur = root
    for idx, _, _ in rows[0][1:]:
        nd = Node(blk[idx])
        tree.nodes[idx] = nd
        cur.left = nd
        nd.parent = cur
        cur = nd

    anchor = root
    for row in rows[1:]:
        idx0 = row[0][0]
        nd0 = Node(blk[idx0])
        tree.nodes[idx0] = nd0
        anchor.right = nd0
        nd0.parent = anchor
        anchor = nd0
        cur = nd0
        for idx, _, _ in row[1:]:
            nd = Node(blk[idx])
            tree.nodes[idx] = nd
            cur.left = nd
            nd.parent = cur
            cur = nd
    return tree


def construct_initial_tree(blocks: List[Block], method: str = 'ffd',
                           target_width: Optional[float] = None,
                           seed: Optional[int] = None) -> BTree:
    if method == 'random':
        t = BTree(blocks)
        t.build_random(seed=seed)
        return t
    if method == 'ffd':
        if target_width is None:
            A = sum(b.area for b in blocks)
            target_width = math.sqrt(A) * 1.05
        return layout_to_btree(blocks, ffd_layout(blocks, target_width))
    if method == 'skyline':
        return layout_to_btree(blocks, _skyline(blocks))
    raise ValueError(method)


def _skyline(blocks: List[Block]) -> List[Tuple[int, float, float]]:
    srt = sorted(enumerate(blocks), key=lambda x: x[1].area, reverse=True)
    sky = [(0.0, float('inf'), 0.0)]
    out = []
    for idx, b in srt:
        cands = {0.0}
        for a, bb, h in sky:
            if bb != float('inf'):
                cands.add(bb)
        best = None
        for x in sorted(cands):
            y = max(h for a, bb, h in sky if a <= x < bb + b.w)
            nw = max(y + b.h, max(s[2] for s in sky))
            if best is None or nw < best[0]:
                best = (nw, x, y)
        _, bx, by = best
        out.append((idx, bx, by))
        be, bt = bx + b.w, by + b.h
        ns, first = [], True
        for a, bb, h in sky:
            if bb <= bx or a >= be:
                ns.append((a, bb, h))
            else:
                if a < bx:
                    ns.append((a, bx, h))
                ns.append((max(a, bx), min(bb, be), bt))
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


if __name__ == '__main__':
    import os
    from m_data import load_blocks
    from m_btree import check_overlap
    BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"
    print("=== 阶段F: FFD 构造 + 上界扫描 ===")

    claims = {'n100': (424, 443), 'n200': (420, 440), 'n300': (523, 538)}
    for n, (lo, hi) in claims.items():
        blk = load_blocks(os.path.join(BASE, f'{n}.blocks'))
        A = sum(b.area for b in blk)

        # 编程手口径: target=√A×1.05
        m_prog = ffd_max_side(blk, math.sqrt(A) * 1.05)
        # 建模手声称上界
        m_claim = ffd_max_side(blk, float(hi))
        # 扫描真上界
        ub, ub_m = scan_upper_bound(blk, lo, hi + 6)

        print(f"[{n}] A_total={A:.0f} √A={math.sqrt(A):.2f} ⌈√A⌉={lo}")
        print(f"    target=√A×1.05 → max={m_prog:.0f}   (编程手口径)")
        print(f"    target={hi}（建模手UB声称） → max={m_claim:.0f}")
        print(f"    扫描真UB: 最小可行边长={ub}（若 None 则声称UB不可构造）, 该边长实测max={ub_m}")

        # 树有效性验证
        t = construct_initial_tree(blk, method='ffd')
        W, H, R = t.pack()
        no_ov, pair = check_overlap(t.get_layout())
        print(f"    FFD树 pack: W={W:.0f} H={H:.0f} R={R:.2f} 无重叠={no_ov} 树有效={t.check_valid()}")
        assert no_ov and t.check_valid()

    print("\n阶段F: ALL PASS")
