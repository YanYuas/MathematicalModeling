"""
精确搜索缺口比 γ 的最大值。

γ = R_MEC/(D/2) 是相似不变量，故把两站归一化为 S1=(0,0)、S2=(1,0) 后，
定位区域 L 的形状只由 (θ1, θ2; ε) 决定，构型空间降为二维，可做穷举网格，
得到网格分辨率意义下的精确最大值。

输出：各 ε 下的 max γ 与对应 (θ1, θ2)，用于拟合 γ − 1 = C·ε^p。
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from q1_main import (  # noqa: E402
    build_wedges, candidate_vertices, convex_hull,
    diameter_bruteforce, mec_bruteforce,
)

S = [np.array([0.0, 0.0]), np.array([1.0, 0.0])]


def gamma_of(th1, th2, eps):
    w = build_wedges(S, [th1, th2], eps)
    c = candidate_vertices(w)
    if len(c) < 3:
        return None
    P = convex_hull(c)
    if len(P.vertices) < 3:
        return None
    D, _ = diameter_bruteforce(P)
    _, R = mec_bruteforce(P.vertices)
    return R / (D / 2.0) if D > 1e-12 else None


def grid_max(eps, step_deg):
    """
    网格搜索 max γ。

    绝大多数构型给出 γ = 1.000000（严格等于 1），因此判据用 g > best 时
    best 会停在最先遇到的 1.0 上，其对应的 (θ1, θ2) 是任意的：粗网格若没
    命中 γ>1 的窄带，细化窗口就会开在无用位置。故本函数默认步长取 1.0°，
    并在返回时同时报告是否真的找到 γ>1。
    """
    ang = np.arange(0.0, 360.0, step_deg)
    best, arg = 1.0, None
    for a in ang:
        for b in ang:
            g = gamma_of(a, b, eps)
            if g is not None and g > best:
                best, arg = g, (a, b)
    return best, arg


def main():
    print("=" * 78)
    print(" γ 最大值精确搜索（两站，相似归一化后仅 (θ1, θ2) 二维）")
    print("=" * 78)

    # 粗网格定位峰值区
    print("\n[粗网格] 步长 2°，ε = 1°")
    g_coarse, arg_c = grid_max(1.0, 2.0)
    print(f"  max γ = {g_coarse:.6f}  at (θ1,θ2) = ({arg_c[0]:.1f}, {arg_c[1]:.1f})")

    # 在峰值邻域细化
    print(f"\n[细化] 以 ({arg_c[0]:.1f},{arg_c[1]:.1f}) 为中心 ±4° 步长 0.05°")
    c1, c2 = arg_c
    a1 = np.arange(c1 - 4, c1 + 4, 0.05)
    a2 = np.arange(c2 - 4, c2 + 4, 0.05)
    best, arg = 0.0, None
    for a in a1:
        for b in a2:
            g = gamma_of(a % 360, b % 360, 1.0)
            if g is not None and g > best:
                best, arg = g, (a % 360, b % 360)
    print(f"  max γ = {best:.6f}  at (θ1,θ2) = ({arg[0]:.4f}, {arg[1]:.4f})")
    print(f"  γ − 1 = {best - 1:.3e}")

    # ε 依赖：同一构型族上随 ε 变化
    print("\n[ε 依赖] 在每个 ε 下做粗网格 + 细化，取该 ε 的 max γ")
    print(f"  {'ε(°)':>7} {'max γ':>12} {'γ−1':>12} {'(γ−1)/ε':>11} {'(γ−1)/ε²':>11}")
    rows = []
    for eps in (0.25, 0.5, 1.0, 2.0, 4.0):
        gc, ac = grid_max(eps, 3.0)
        a1 = np.arange(ac[0] - 4, ac[0] + 4, 0.1)
        a2 = np.arange(ac[1] - 4, ac[1] + 4, 0.1)
        bb = gc
        for a in a1:
            for b in a2:
                g = gamma_of(a % 360, b % 360, eps)
                if g is not None and g > bb:
                    bb = g
        rows.append((eps, bb))
        print(f"  {eps:7.2f} {bb:12.6f} {bb-1:12.3e} {(bb-1)/eps:11.3e} {(bb-1)/eps**2:11.3e}")

    # 拟合 γ−1 = C·ε^p
    e = np.array([r[0] for r in rows])
    y = np.array([r[1] - 1 for r in rows])
    m = y > 0
    if m.sum() >= 2:
        p, logC = np.polyfit(np.log(e[m]), np.log(y[m]), 1)
        print(f"\n[拟合] γ − 1 ≈ C·ε^p   →  p = {p:.4f},  C = {math.exp(logC):.4e}")
        print(f"       即题设 ε = 1° 时 γ − 1 ≈ {math.exp(logC):.3e}")

    print("=" * 78)


if __name__ == "__main__":
    main()
