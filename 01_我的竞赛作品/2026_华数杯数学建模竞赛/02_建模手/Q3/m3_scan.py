# -*- coding: utf-8 -*-
"""m3_scan.py — Q3 轻量可行性扫描（建模手验证层）
目标：验证 Q3 核心假设
  H1: FFD 行堆叠/skyline 判可行子程序可用，S=Q1解M 时复现可行
  H2: 最小可行 S 量级 —— 能否压到 ⌈√A⌉ 附近？构造 Γ* 区间
  H3: 死区排序 n100 > n200 > n300（长条主导）
  H4: 哪种打包策略 + 旋转策略压得最紧（指导编程手算法设计）
复用 Q2 独立实现: m2_data.load / ffd_order_layout / skyline_order / orders / Block
"""
import os
import sys
import math

sys.path.insert(0, os.path.join(
    r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\CLAUDE工作文件\编程手\Q2\编程手反馈\问题2独立实现"))

from m2_data import load, Block
from m2_init import ffd_order_layout, skyline_order, orders


def rot_blk(blk, mode):
    """旋转策略: 'none' 原样 / 'tall' 长条旋转(AR>=2.5 长边水平) / 'all' 全旋(w>=h)"""
    out = []
    for b in blk:
        if mode == 'none':
            out.append(b)
        elif mode == 'tall':
            if max(b.w, b.h) / min(b.w, b.h) >= 2.5:
                out.append(Block(b.idx, b.name, max(b.w, b.h), min(b.w, b.h)))
            else:
                out.append(b)
        else:  # 'all'：长边作宽
            out.append(Block(b.idx, b.name, max(b.w, b.h), min(b.w, b.h)))
    return out


def feas_s(S, strategy, blk, data):
    """判可行: 存在布局 W<=S 且 H<=S。返回 (bool, (W,H))"""
    if strategy == 'skyline':
        order = sorted(range(len(blk)), key=lambda i: -blk[i].h)
        layout = skyline_order(blk, order, float(S))
    elif strategy == 'skyline_area':
        order = sorted(range(len(blk)), key=lambda i: -blk[i].area)
        layout = skyline_order(blk, order, float(S))
    elif strategy == 'h_desc':
        # Q1 构造方式：h 降序行堆叠（Q1 解 443×442 即此）
        order = sorted(range(len(blk)), key=lambda i: -blk[i].h)
        layout = ffd_order_layout(blk, order, float(S))
    else:
        order = orders(data, blk)[strategy]
        layout = ffd_order_layout(blk, order, float(S))
    W = max((x + blk[i].w for i, x, y in layout), default=0.0)
    H = max((y + blk[i].h for i, x, y in layout), default=0.0)
    return (W <= S + 1e-9 and H <= S + 1e-9), (W, H)


def scan(data, blk, strategies, start, lo):
    """从 start 往下扫到 lo，找最小可行 S。返回 (min_S, 该S下最优策略, (W,H))"""
    best_S, best_strat, best_wh = None, None, None
    for S in range(start, lo - 1, -1):
        hit = None
        for strat in strategies:
            ok, wh = feas_s(S, strat, blk, data)
            if ok:
                hit = (strat, wh)
                break
        if hit:
            best_S, best_strat, best_wh = S, hit[0], hit[1]
        else:
            if best_S is not None:
                break  # 已过可行区（单调），提前停
    return best_S, best_strat, best_wh


def diagnose(data, blk, strategies, S):
    """对给定 S 打印各策略 W/H 明细（看差多少）"""
    for strat in strategies:
        ok, wh = feas_s(S, strat, blk, data)
        print(f'    S={S} {strat:10s}: WxH={wh[0]:.0f}x{wh[1]:.0f}  {"可行" if ok else "不可行(超" + str(int(max(wh) - S)) + ")"}')


def main():
    print('=== Q3 轻量可行性扫描（建模手验证层）===')
    # Q1 解边长（已验证构造上界）与旋转模式
    Q1M = {'n100': 443, 'n200': 432, 'n300': 533}
    strategies = ['h_desc', 'area_desc', 'pref_yx', 'pref_y', 'skyline', 'skyline_area']
    for mode in ['none', 'tall']:
        print(f'\n--- 旋转模式: {mode} ---')
        for name in ['n100', 'n200', 'n300']:
            data = load(name)
            blk0 = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]
            blk = rot_blk(blk0, mode)
            start = Q1M[name]
            lo = int(math.ceil(math.sqrt(data['area'])))  # 面积下界
            min_S, strat, wh = scan(data, blk, strategies, start, lo)
            if min_S is None:
                print(f'  [{name}] 连 S={start} 都不可行! 异常')
                continue
            gamma = (min_S ** 2 - data['area']) / data['area']
            dead_ratio = (min_S ** 2 - data['area']) / min_S ** 2
            print(f'  [{name}] A={data["area"]:.0f} √A={math.sqrt(data["area"]):.2f} '
                  f'Q1M={start} → 最小可行S={min_S} (策略={strat} WxH={wh[0]:.0f}x{wh[1]:.0f})')
            print(f'          Γ*={gamma:.4f} 死区占比={dead_ratio:.4f} = {dead_ratio * 100:.2f}%')
    # 诊断：临界处差多少 + skyline_h 能否突破
    print('\n=== 诊断：临界点 S=Q1M-1 各策略明细 ===')
    for name, mode, S in [('n100', 'tall', 442), ('n200', 'tall', 431), ('n300', 'tall', 532), ('n300', 'none', 533)]:
        data = load(name)
        blk0 = [Block(i, nm, w, h) for i, (nm, (w, h)) in enumerate(data['blocks'].items())]
        blk = rot_blk(blk0, mode)
        print(f'  [{name} {mode}]')
        diagnose(data, blk, strategies, S)
    print('\n扫描完成')


if __name__ == '__main__':
    main()
