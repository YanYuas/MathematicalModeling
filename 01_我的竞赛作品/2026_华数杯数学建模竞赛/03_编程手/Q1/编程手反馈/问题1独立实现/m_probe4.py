"""
m_probe4.py — 旋转策略 + 配对优化探测
1. 所有块旋转使 w≥h（长边水平）→ FFD 行堆叠扫描
2. 仅长条旋转 → FFD 行堆叠扫描
3. 配对（只配最极端长条，约束复合块面积）→ FFD 行堆叠
目标：n100 找 <444
"""
import os
import copy
import math
from m_data import load_blocks, Block
from m_construct import ffd_max_side, construct_initial_tree, ffd_layout
from m_btree import check_overlap

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"


def rotate_all(blocks, only_strips=False, threshold=2.5):
    """返回旋转后 blocks（长边水平 w≥h）。"""
    out = []
    for b in blocks:
        nb = Block(b.idx, b.name, b.w, b.h)
        if (not only_strips) or nb.aspect_ratio() >= threshold:
            if nb.w < nb.h:
                nb.w, nb.h = nb.h, nb.w
        out.append(nb)
    return out


def scan(blocks, lo, hi, label):
    for tw in range(lo, hi + 1):
        m = ffd_max_side(blocks, float(tw))
        if m <= tw:
            print(f"  {label} target={tw}: max={m:.0f} ✓")
            return tw, m
        if tw - lo > 12:
            break
    print(f"  {label}: 无可行（扫描至 {hi}）")
    return None, None


for n in ['n100', 'n200', 'n300']:
    blk = load_blocks(os.path.join(BASE, f'{n}.blocks'))
    A = sum(b.area for b in blk)
    lb = math.ceil(math.sqrt(A))
    print(f"\n[{n}] A={A:.0f} ⌈√A⌉={lb} 当前最优(高降序)=", end="")
    base = None
    for tw in range(lb, lb + 30):
        m = ffd_max_side(blk, float(tw))
        if m <= tw:
            base = (tw, m)
            break
    print(f"target={base[0]} max={base[1]:.0f}" if base else "无")

    if base:
        # 1. 全旋转
        r_all = rotate_all(blk, only_strips=False)
        scan(r_all, lb, base[0] + 6, "全旋转长边水平")
        # 2. 仅长条旋转
        r_strip = rotate_all(blk, only_strips=True)
        scan(r_strip, lb, base[0] + 6, "仅长条旋转")
