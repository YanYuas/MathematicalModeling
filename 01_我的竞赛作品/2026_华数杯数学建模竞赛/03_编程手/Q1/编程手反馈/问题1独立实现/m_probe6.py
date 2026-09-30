"""
m_probe6.py — 带宽度约束 skyline 构造探测
标准 skyline：每块放 [0,target] 内最低轮廓位置，可跨段填隙。
目标：n100 突破 443 → ~437（参考论文可达死区 5.57%）
"""
import os
import math
from m_data import load_blocks, Block
from m_btree import check_overlap

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"


def skyline_pack(blocks, target):
    """带宽度约束 skyline 行打包。返回 (W,H,layout)。"""
    srt = sorted(enumerate(blocks), key=lambda x: x[1].area, reverse=True)
    sky = [(0.0, float('inf'), 0.0)]
    layout = []
    max_h = 0.0
    max_w = 0.0
    for idx, b in srt:
        bw, bh = b.w, b.h
        # 若块宽 > target，旋转（长边朝下）
        if bw > target and bh <= target:
            bw, bh = bh, bw
        # 候选 x：0 和各段右端
        cands = {0.0}
        for a, bb, h in sky:
            if bb != float('inf') and a < target:
                cands.add(a)
        best = None
        for x in sorted(cands):
            if x + bw > target + 1e-9:
                continue
            # 覆盖 [x, x+bw] 的段最大高度
            y = max(h for a, bb, h in sky if a < x + bw and bb > x)
            # 新 max 高度
            nw = max(y + bh, max((s[2] for s in sky), default=0))
            if best is None or nw < best[0] or (abs(nw - best[0]) < 1e-9 and y < best[2]):
                best = (nw, x, y)
        if best is None:
            # 放不下，旋转或跳到下一行开头
            bw, bh = bh, bw
            x = 0.0
            y = max((s[2] for s in sky), default=0)
            best = (y + bh, x, y)
        _, bx, by = best
        layout.append((idx, bx, by, bw, bh))
        max_w = max(max_w, bx + bw)
        max_h = max(max_h, by + bh)
        # 更新 skyline
        be, bt = bx + bw, by + bh
        ns = []
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
    return max_w, max_h, layout


for n in ['n100', 'n200', 'n300']:
    blk = load_blocks(os.path.join(BASE, f'{n}.blocks'))
    A = sum(b.area for b in blk)
    lb = math.ceil(math.sqrt(A))
    print(f"\n[{n}] A={A:.0f} ⌈√A⌉={lb}")
    for tw in range(lb, lb + 26):
        W, H, layout = skyline_pack(blk, float(tw))
        m = max(W, H)
        if m <= tw:
            ds = (W * H - A) / (W * H) * 100
            print(f"  skyline target={tw}: {W:.0f}×{H:.0f} max={m:.0f} 死区={ds:.2f}% ✓ 首个可行")
            break
        if tw == lb:
            print(f"  skyline target={tw}: max={m:.0f} (不可行)")
