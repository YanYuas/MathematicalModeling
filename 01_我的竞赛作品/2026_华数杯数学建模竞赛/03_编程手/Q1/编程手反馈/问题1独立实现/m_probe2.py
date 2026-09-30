"""
m_probe2.py — 邻域诊断：FFD/random 树的扰动分布
若 FFD 树邻域 min 面积 = 197136 → 444 是强局部最优（需配对/大扰动）
若邻域有更小 → SA 参数问题（迭代不足/温度）
"""
import os
import random
import copy
from m_data import load_blocks
from m_btree import BTree
from m_construct import construct_initial_tree
from m_operators import random_perturbation

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"
blk = load_blocks(os.path.join(BASE, 'n100.blocks'))
A_total = sum(b.area for b in blk)


def explore(label, tree, n_pert, seed=0):
    random.seed(seed)
    best_A, worst_A = float('inf'), 0
    best_wh = None
    t = copy.deepcopy(tree)
    for i in range(n_pert):
        random_perturbation(t)
        W, H, _ = t.pack()
        A = W * H
        if A < best_A:
            best_A, best_wh = A, (W, H)
        worst_A = max(worst_A, A)
    print(f"[{label}] {n_pert}次扰动: min_A={best_A:.0f} ({best_wh[0]:.0f}×{best_wh[1]:.0f}, "
          f"死区={(best_A-A_total)/best_A*100:.2f}%) max_A={worst_A:.0f}")


print("=== 邻域诊断 n100 ===")
ft = construct_initial_tree(blk, method='ffd')
W, H, _ = ft.pack()
print(f"FFD起点: {W:.0f}×{H:.0f} A={W*H:.0f}")

explore("FFD邻域", ft, 3000, seed=1)
explore("FFD邻域", ft, 3000, seed=2)
explore("FFD邻域", ft, 3000, seed=3)

# random 树邻域
rt = construct_initial_tree(blk, method='random', seed=7)
W0, H0, _ = rt.pack()
print(f"random起点: max={max(W0,H0):.0f} A={W0*H0:.0f}")
explore("random邻域", rt, 3000, seed=4)
