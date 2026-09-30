"""
m_probe5.py — n100 突破探测
1. 配对约束版：只配最极端 N 对长条（长边最大），复合块面积约束 → FFD 扫描
2. 宽松起点 SA：FFD(target=450) 起点 → SA phase1 40级 看能否 <444
"""
import os
import copy
import math
from m_data import load_blocks, Block
from m_construct import ffd_max_side, construct_initial_tree
from m_cost import phase1_cost
from m_fastsa import FastSA

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"
blk = load_blocks(os.path.join(BASE, 'n100.blocks'))
A_total = sum(b.area for b in blk)
lb = math.ceil(math.sqrt(A_total))
print(f"n100 A={A_total:.0f} ⌈√A⌉={lb} 基准最优 target=444")


def pair_top_strips(blocks, k, threshold=2.5):
    """只配最极端 k 个长条（长边最大），各找互补块（全池）。"""
    blk = [copy.deepcopy(b) for b in blocks]
    strips = sorted([b for b in blk if b.aspect_ratio() >= threshold],
                    key=lambda b: max(b.w, b.h), reverse=True)
    used = set()
    result = blk[:]
    pairs = 0
    for s in strips[:k]:
        if s.idx in used:
            continue
        ar_s = s.aspect_ratio()
        best_m, best_ar = None, ar_s
        for cand in blk:
            if cand.idx == s.idx or cand.idx in used:
                continue
            for cw, ch in ((s.w + cand.w, max(s.h, cand.h)), (max(s.w, cand.w), s.h + cand.h)):
                ar = max(cw, ch) / min(cw, ch)
                if ar < best_ar:
                    best_ar, best_m, bcw, bch = ar, cand, cw, ch
        if best_m is not None and ar_s - best_ar > 0.4:
            comp = Block(min(s.idx, best_m.idx), f"p{s.idx}_{best_m.idx}", bcw, bch)
            result = [b for b in result if b.idx not in {s.idx, best_m.idx}]
            result.append(comp)
            used.update({s.idx, best_m.idx})
            pairs += 1
    return result, pairs


# 1. 配对约束版
for k in [3, 5, 7, 10]:
    paired, np = pair_top_strips(blk, k)
    if np == 0:
        print(f"  配对 k={k}: 0 对，跳过")
        continue
    found = None
    for tw in range(lb, lb + 30):
        m = ffd_max_side(paired, float(tw))
        if m <= tw:
            found = (tw, m)
            break
    print(f"  配对 k={k} ({np}对, {len(paired)}块): target={found[0]} max={found[1]:.0f} "
          f"{'✓ 优于444' if found[1] < 444 else ''}" if found else f"  配对 k={k}: 无可行")

# 2. 宽松起点 SA
print("\n宽松起点 SA（FFD target=450 → phase1 40级）")
for target_w in [450, 460, 470]:
    init = construct_initial_tree(blk, method='ffd', target_width=float(target_w))
    W0, H0, _ = init.pack()

    def c1(tree):
        W, H, _ = tree.pack()
        return phase1_cost(W * H, A_total)
    sa = FastSA(blk, c1)
    r = sa.run(init, seed=42, L_factor=10, max_levels=40, verbose=False)
    W, H, R = r['best_tree'].pack()
    print(f"  target={target_w} 起点 max={max(W0,H0):.0f} → SA40级 max={max(W,H):.0f} "
          f"({W:.0f}×{H:.0f}) {'✓ <444' if max(W,H)<444 else ''}")
