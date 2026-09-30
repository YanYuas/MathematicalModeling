"""
m_experiment.py — 独立实现 阶段H：三组最终解（FFD target 参数化）
关键发现：FFD 行堆叠 target_width 参数化扫描本身给最优解（真UB），
SA 从 FFD 起点无法改进（三算子邻域强局部最优）。
本脚本：对三组用 FFD(target=真UB) 构造，验证布局合法，与编程手对照。
"""
import os
import sys
sys.setrecursionlimit(10000)
from m_data import load_blocks
from m_construct import construct_initial_tree
from m_btree import check_overlap

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"
# 真UB（独立 FFD 扫描，见 m_bounds.py 阶段G）
true_ub = {'n100': 444, 'n200': 432, 'n300': 540}
# 编程手 results.csv（FFD twophase seed0）
prog = {'n100': (444.0, 444.0), 'n200': (440.0, 427.0), 'n300': (548.0, 519.0)}
# 建模手原声称上界
claim_ub = {'n100': 443, 'n200': 440, 'n300': 538}

print(f"{'集':6s} {'FFD(真UB)':>20s} {'R':>6s} {'死区':>7s} {'无重叠':>5s} {'编程手':>14s} {'判定':>26s}")
for n in ['n100', 'n200', 'n300']:
    blk = load_blocks(os.path.join(BASE, f'{n}.blocks'))
    A_total = sum(b.area for b in blk)
    ub = true_ub[n]
    tree = construct_initial_tree(blk, method='ffd', target_width=float(ub))
    W, H, R = tree.pack()
    no_ov, pair = check_overlap(tree.get_layout())
    ds = (W * H - A_total) / (W * H) * 100
    pw, ph = prog[n]
    pmax = max(pw, ph)
    verdict = f"优于编程手({pmax:.0f}->{max(W,H):.0f})" if max(W, H) < pmax else (
        "==编程手" if max(W, H) == pmax else "差于编程手")
    print(f"{n:6s} {W:.0f}×{H:.0f} max={max(W,H):.0f} {R:6.3f} {ds:6.2f}% {str(no_ov):5s} "
          f"{pw:.0f}×{ph:.0f} max={pmax:.0f} {verdict:>26s}")
    assert no_ov and tree.check_valid(), f"{n} 布局非法"

print("\n阶段H 完成：FFD(target=真UB) 即最优可行解，无需 SA")
