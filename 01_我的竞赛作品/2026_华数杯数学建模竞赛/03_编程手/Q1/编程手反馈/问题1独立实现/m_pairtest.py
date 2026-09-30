"""
m_pairtest.py — 配对预处理效果诊断
n100 有 15 长条(AR≥2.5)。互补配对 → 复合块，看 FFD 起点能否 < 444。
贪心配对：对每个长条，找互补长条（一高瘦一矮宽）使复合块 AR 最小。
"""
import os
from m_data import load_blocks
from m_construct import ffd_max_side, construct_initial_tree
from m_btree import check_overlap

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"


def pair_greedy(blocks, threshold=2.5):
    """贪心互补配对：长条 × 全块池中互补的矮宽块。建模手 F27/F28。
    返回 (配对后 blocks, pairs)。"""
    import copy as _c
    blk = [_c.deepcopy(b) for b in blocks]
    from m_data import Block as _B
    strips = [b for b in blk if b.aspect_ratio() >= threshold]
    strips.sort(key=lambda b: b.aspect_ratio(), reverse=True)
    used = set()
    pairs = []
    result = [b for b in blk]
    for s in strips:
        if s.idx in used:
            continue
        ar_s = s.aspect_ratio()
        best_m, best_score, best_cw, best_ch = None, ar_s, None, None
        for cand in blk:
            if cand.idx == s.idx or cand.idx in used:
                continue
            # 并排(F27): w=wi+wj, h=max
            cw1 = s.w + cand.w
            ch1 = max(s.h, cand.h)
            # 叠放(F28): w=max, h=hi+hj
            cw2 = max(s.w, cand.w)
            ch2 = s.h + cand.h
            for cw, ch in ((cw1, ch1), (cw2, ch2)):
                ar = max(cw, ch) / min(cw, ch) if min(cw, ch) > 0 else float('inf')
                if ar < best_score:
                    best_score, best_m, best_cw, best_ch = ar, cand, cw, ch
        # q = ar_s - best_score > 0.4 才算有效配对（显著变方）
        if best_m is not None and ar_s - best_score > 0.4:
            composite = _B(min(s.idx, best_m.idx), f"p{s.idx}_{best_m.idx}", best_cw, best_ch)
            result = [b for b in result if b.idx not in {s.idx, best_m.idx}]
            result.append(composite)
            pairs.append((s.idx, best_m.idx, best_cw, best_ch))
            used.update({s.idx, best_m.idx})
    return result, pairs


for n in ['n100', 'n200', 'n300']:
    blk = load_blocks(os.path.join(BASE, f'{n}.blocks'))
    A = sum(b.area for b in blk)
    orig = ffd_max_side(blk, float('inf')) if False else None
    m_no_pair = max(construct_initial_tree(blk, method='ffd').pack()[0],
                    construct_initial_tree(blk, method='ffd').pack()[1])
    paired, pairs = pair_greedy(blk)
    t = construct_initial_tree(paired, method='ffd')
    W, H, R = t.pack()
    no_ov, _ = check_overlap(t.get_layout())
    print(f"[{n}] 配对前 FFD max={m_no_pair:.0f} | 配对 {len(pairs)} 对 → {len(paired)}块 "
          f"配对后 FFD={W:.0f}×{H:.0f} max={max(W,H):.0f} 死区={(W*H-A)/(W*H)*100:.2f}% 无重叠={no_ov}")
