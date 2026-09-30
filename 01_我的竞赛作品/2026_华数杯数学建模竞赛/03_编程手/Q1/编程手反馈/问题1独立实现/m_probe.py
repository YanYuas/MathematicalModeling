"""
m_probe.py — 探针：诊断 SA 为何卡在 FFD 444×444
1. random 起点 phase1 能否收敛 < 197136
2. FFD 起点 + 更长迭代（80级）能否突破
3. phase2 T1 采样是否被 penalty 污染（应只用合规 delta）
"""
import os
import copy
import random
import time
from m_data import load_blocks
from m_btree import BTree, check_overlap
from m_construct import construct_initial_tree
from m_cost import phase1_cost, phase2_cost
from m_fastsa import FastSA

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"
blk = load_blocks(os.path.join(BASE, 'n100.blocks'))
A_total = sum(b.area for b in blk)
print(f"A_total={A_total:.0f}, FFD起点 max=444 (死区8.95%)")


def probe(label, init, seed, L_factor, max_levels, verbose=False):
    def c1(tree):
        W, H, _ = tree.pack()
        return phase1_cost(W * H, A_total)
    sa = FastSA(blk, c1)
    t0 = time.time()
    r = sa.run(init, seed=seed, L_factor=L_factor, max_levels=max_levels, verbose=verbose)
    W, H, R = r['best_tree'].pack()
    print(f"[{label}] seed={seed} 级={r['levels']} cost={r['cost']:.4f} "
          f"W={W:.0f} H={H:.0f} max={max(W,H):.0f} 死区={(W*H-A_total)/(W*H)*100:.2f}% "
          f"时间={r['time']:.1f}s")
    return r


# Probe 1: random 起点, 60级, L=10n
print("\n=== Probe1: random起点 phase1 (60级) ===")
rt = construct_initial_tree(blk, method='random', seed=1)
W0, H0, _ = rt.pack()
print(f"  random初始: max={max(W0,H0):.0f} 死区={(W0*H0-A_total)/(W0*H0)*100:.0f}%")
r1 = probe("random60", rt, seed=1, L_factor=10, max_levels=60)

# Probe 2: FFD 起点, 80级 更长
print("\n=== Probe2: FFD起点 phase1 (80级) ===")
ft = construct_initial_tree(blk, method='ffd')
r2 = probe("ffd80", ft, seed=2, L_factor=10, max_levels=80)

# Probe 3: phase2 T1 采样诊断（从 phase1 最优出发）
print("\n=== Probe3: phase2 penalty 污染诊断 ===")
from m_fastsa import solve_two_phase
# 修正 solve_two_phase 的 Phi_norm：用初始 max 边而非 sqrt(A_opt)
init = construct_initial_tree(blk, method='ffd')
W0, H0, _ = init.pack()
Phi_norm = max(W0, H0)
res = solve_two_phase(blk, init, seed=3, Phi_norm=Phi_norm, verbose=True)
print(f"[probe3] A_opt={res['A_opt']:.0f} W={res['W']:.0f} H={res['H']:.0f} max={max(res['W'],res['H']):.0f}")
