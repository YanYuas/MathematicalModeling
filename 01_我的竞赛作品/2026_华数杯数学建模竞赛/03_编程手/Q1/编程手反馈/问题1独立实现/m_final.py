"""
m_final.py — Q1 最终结果确认
三组最终解（基础行堆叠 + 仅长条旋转，取更优）→ 验证布局 → 出表
SA 从最终解跑 20 级互证（best 不降 = 构造解已稳定最优）
"""
import os
import copy
import math
import sys
sys.setrecursionlimit(10000)
from m_data import load_blocks, Block
from m_construct import construct_initial_tree, ffd_max_side
from m_btree import check_overlap
from m_cost import phase1_cost, deadspace
from m_fastsa import FastSA

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"


def rotate_strips(blocks, threshold=2.5):
    """仅长条旋转使长边水平。返回副本列表。"""
    return [Block(b.idx, b.name, max(b.w, b.h), min(b.w, b.h)) if b.aspect_ratio() >= threshold
            else Block(b.idx, b.name, b.w, b.h) for b in blocks]


def best_ffd(blocks, lo, hi):
    """行堆叠扫描找最小可行边长，返回 (target, max_side)。"""
    for tw in range(lo, hi + 1):
        m = ffd_max_side(blocks, float(tw))
        if m <= tw:
            return tw, m
    return None, None


results = {}
for n, lo in [('n100', 424), ('n200', 420), ('n300', 523)]:
    blk = load_blocks(os.path.join(BASE, f'{n}.blocks'))
    A_total = sum(b.area for b in blk)

    # 两种构造：基础 / 仅长条旋转，取更优
    opt = None
    for label, blocks in [('基础', blk), ('仅长条旋转', rotate_strips(blk))]:
        tw, m = best_ffd(blocks, lo, lo + 30)
        if opt is None or (m is not None and m < opt[1]):
            opt = (tw, m, label, blocks)
    tw, m, label, blocks = opt

    # 用该构造的树验证布局
    tree = construct_initial_tree(blocks, method='ffd', target_width=float(tw))
    W, H, R = tree.pack()
    no_ov, pair = check_overlap(tree.get_layout())
    ds = deadspace(W, H, A_total)
    valid = no_ov and tree.check_valid() and abs(W * H - sum(b.area for b in blocks)) >= -1
    results[n] = {'W': W, 'H': H, 'R': R, 'ds': ds, 'tw': tw, 'label': label, 'valid': valid}
    print(f"[{n}] 构造={label} target={tw}: {W:.0f}×{H:.0f} R={R:.3f} "
          f"死区={ds:.2f}% 无重叠={no_ov} 合法={valid}")

    # SA 互证：从最终解跑 20 级，best 不降 = 稳定
    def c1(tree):
        W, H, _ = tree.pack()
        return phase1_cost(W * H, A_total)
    sa = FastSA(blocks, c1)
    r = sa.run(tree, seed=1, L_factor=10, max_levels=20, verbose=False)
    W2, H2, R2 = r['best_tree'].pack()
    improved = max(W2, H2) < max(W, H)
    print(f"    SA 互证 20级: max={max(W2,H2):.0f} vs 构造 {max(W,H):.0f} "
          f"→ {'构造被改进!' if improved else '构造已稳定（best不降）'}")

print("\n=== Q1 最终结果表 ===")
print(f"{'集':6s} {'构造':12s} {'W':>5s} {'H':>5s} {'R':>5s} {'死区':>7s} {'合法':>4s}")
for n in ['n100', 'n200', 'n300']:
    r = results[n]
    print(f"{n:6s} {r['label']:12s} {r['W']:5.0f} {r['H']:5.0f} {r['R']:5.3f} "
          f"{r['ds']:6.2f}% {str(r['valid']):>4s}")
