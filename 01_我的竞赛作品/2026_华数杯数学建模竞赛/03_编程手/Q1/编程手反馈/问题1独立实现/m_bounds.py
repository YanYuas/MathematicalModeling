"""
m_bounds.py — 独立实现 阶段G：下界/上界
LB = ceil(√A_total)（建模手 F23）
UB = FFD 行堆叠扫描的最小可行方形边长（建模手 F25 正确口径）
"""
import math
import os
from typing import List
from m_data import Block, load_blocks
from m_construct import ffd_max_side, scan_upper_bound

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"


def compute_bounds(blocks: List[Block], hi_extra: int = 30):
    A = sum(b.area for b in blocks)
    lb = math.ceil(math.sqrt(A))
    ub, ub_m = scan_upper_bound(blocks, lb, lb + hi_extra + 10)
    return lb, ub, ub_m


if __name__ == '__main__':
    print("=== 阶段G: 独立下界/上界 ===")
    claims = {'n100': 443, 'n200': 440, 'n300': 538}
    print(f"{'集':6s} {'A_total':>9s} {'LB=⌈√A⌉':>9s} {'真UB':>6s} {'建模手声称UB':>10s} {'判定':>20s}")
    for n, claim in claims.items():
        blk = load_blocks(os.path.join(BASE, f'{n}.blocks'))
        lb, ub, ub_m = compute_bounds(blk)
        verdict = f"== 声称UB={claim} | 真UB={ub} | 差{ub-claim:+d}"
        print(f"{n:6s} {sum(b.area for b in blk):9.0f} {lb:9d} {ub:6d} {claim:10d} {verdict:>20s}")
        assert ub is not None, f"{n}: 扫描 {lb}-{lb+16} 无可行方形"
    print("\n阶段G: 边界独立确定完成")
