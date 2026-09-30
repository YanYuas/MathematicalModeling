"""
m_stats.py — 多 seed 稳定性统计
构造解确定性（seed 无关）；SA 几何冷却多 seed 微调验证 best 不降。
输出：三组 × 5 seed，max 边长 / 死区 均值与方差。
"""
import os
import math
import statistics
import sys
sys.setrecursionlimit(10000)
from m_data import load_blocks, Block
from m_construct import construct_initial_tree
from m_cost import phase1_cost, deadspace
from m_fastsa import FastSA

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"
CONF = {'n100': (True, 443), 'n200': (False, 432), 'n300': (True, 533)}
SEEDS = 5


def rotate_strips(blocks, threshold=2.5):
    return [Block(b.idx, b.name, max(b.w, b.h), min(b.w, b.h)) if b.aspect_ratio() >= threshold
            else Block(b.idx, b.name, b.w, b.h) for b in blocks]


print(f"{'集':6s} {'构造max':>8s} {'SA各seed max':>20s} {'死区均值':>8s} {'死区std':>7s}")
for n, (use_rot, target) in CONF.items():
    blk = load_blocks(os.path.join(BASE, f'{n}.blocks'))
    A_total = sum(b.area for b in blk)
    blocks = rotate_strips(blk) if use_rot else blk
    init = construct_initial_tree(blocks, method='ffd', target_width=float(target))
    W0, H0, _ = init.pack()
    M0 = max(W0, H0)

    def c1(tree):
        W, H, _ = tree.pack()
        return phase1_cost(W * H, A_total)

    maxes = []
    dss = []
    for s in range(SEEDS):
        sa = FastSA(blocks, c1)
        r = sa.run(init, seed=s, L_factor=10, max_levels=15, verbose=False)
        W, H, R = r['best_tree'].pack()
        maxes.append(max(W, H))
        dss.append(deadspace(W, H, A_total))
    stable = all(m == M0 for m in maxes)
    print(f"{n:6s} {M0:8.0f} {str(maxes):>20s} {statistics.mean(dss):8.2f}% "
          f"{statistics.stdev(dss):7.3f}% {'✓稳定' if stable else '⚠变化'}")
print("\n多 seed 统计完成")
