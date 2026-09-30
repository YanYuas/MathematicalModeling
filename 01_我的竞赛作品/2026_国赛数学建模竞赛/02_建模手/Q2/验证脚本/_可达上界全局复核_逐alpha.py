# -*- coding: utf-8 -*-
"""
Q2 可达交会角上界 phi_min^max —— 全局复核（修正版）

【为什么上一版判据错了】
上一版用 `min_alpha n(alpha) / max_{alpha,r} d2` 作判据。因分子取 min、分母取 max 是
两个**不同** alpha 处取的，该量是 G 的**下界**（Q <= G），故它**不能**用来证明
"40° 全局不可达"。方向搞反，结论作废，脚本保留在 `_可达上界全局严格复核.py`（留痕）。

【正确判据】源的真实参数 (r, alpha) 是**同一个**，故必须逐 alpha 耦合：

    G(a,b) = min_{alpha in [-eps,eps]}  n(alpha) / D(alpha)
    其中 n(alpha) = |a sin alpha - b cos alpha|            （与 r 无关）
         D(alpha) = max_{r in [5,1500]} d2(r, alpha)         （d2^2 关于 r 为开口向上抛物线 => r 取端点）
    可行性另需  max_{alpha} D(alpha) <= R_worst

其中 D(alpha) = sqrt(a^2+b^2+r*^2 - 2 r* (a cos alpha + b sin alpha))，
r* = argmax，即 r* = 5 若 s=a cos alpha + b sin alpha <= (5+1500)/2 否则 1500
     （两条抛物线端点比较，取较大者）。

alpha 维用 801 点密采样 => 数值上等价于精确。

输出：mesh 上的 max G。若该值 < 40 且远小于 40，则"40° 不可达"获得**接近全局**的支撑；
      否则论文的 39.6161deg 需重述。
"""
import math
import numpy as np

EPS = math.radians(1.0)
R_WORST = 1000.0
R_MAX = 1500.0
R_MIN = 5.0
ALPHAS = np.linspace(-EPS, EPS, 801)


def _D2(r, a, b, al):
    return a * a + b * b + r * r - 2.0 * r * (a * math.cos(al) + b * math.sin(al))


def D_max(al, a, b):
    """max over r in [5,1500] of d2，严格（抛物线端点取大者）。"""
    d_lo = _D2(R_MIN, a, b, al)
    d_hi = _D2(R_MAX, a, b, al)
    return math.sqrt(max(d_lo, d_hi))


def G(a, b):
    """该 (a,b) 能保证的交会角（度）。不可行/退化 => 0。"""
    if a == 0.0 and b == 0.0:
        return 0.0
    worst = None
    Dmax_all = 0.0
    for al in ALPHAS:
        D = D_max(al, a, b)
        if D > Dmax_all:
            Dmax_all = D
        n = abs(a * math.sin(al) - b * math.cos(al))
        if D <= 0.0:
            return 0.0
        ratio = n / D
        if worst is None or ratio < worst:
            worst = ratio
    if Dmax_all > R_WORST:
        return 0.0
    if worst is None or worst <= 0.0:
        return 0.0
    return math.degrees(math.asin(min(worst, 1.0)))


def scan(a_lo, a_hi, b_lo, b_hi, step, label):
    a = np.arange(a_lo, a_hi + 1e-9, step)
    b = np.arange(b_lo, b_hi + 1e-9, step)
    best, at = 0.0, None
    hit40 = []
    for aa in a:
        for bb in b:
            g = G(aa, bb)
            if g >= 40.0:
                hit40.append((aa, bb, g))
            if g > best:
                best, at = g, (aa, bb)
    print(f"  {label}: step={step}m  {len(a)}x{len(b)}={len(a)*len(b)} 点")
    print(f"    max phi = {best:.6f}deg  at (a,b)=({at[0]:.2f},{at[1]:.2f})")
    if hit40:
        print(f"    *** 出现 >=40deg 的点 {len(hit40)} 个，前 3：{hit40[:3]}")
    else:
        print(f"    全网格无 >=40deg 的点")
    return best, at


print("=" * 74)
print("Q2 可达交会角上界 —— 全局复核（逐 alpha 耦合判据，修正版）")
print(f"eps={math.degrees(EPS)}deg  R_worst={R_WORST}  r in [{R_MIN},{R_MAX}]  alpha 801 点")
print("=" * 74)

print("\n[0] 基线自检")
print("  期望：a=752.5 处，b<=638 有正保证且 <40；b>=650 直接不可行")
for bb in (627.226974, 638.0, 650.0, 664.261808):
    print(f"    b={bb:10.4f}  G={G(752.5, bb):8.4f}deg")
print("  期望：alpha=0 时 (752.5, 664.262) 附近 G ~= 41.626")
print(f"    a=752.5,b=664.261808 -> D_max at a=0 : "
      f"{math.degrees(math.asin(min(abs(752.5*0.0 - 664.261808*1.0)/D_max(0.0,752.5,664.261808),1.0))):.4f}deg (单 alpha=0 参考)")

print("\n[1] 全局粗扫")
g1, at1 = scan(-400, 1800, 0, 1200, 20.0, "coarse")

print("\n[2] 粗扫最优邻域细扫")
g2, at2 = scan(at1[0] - 60, at1[0] + 60, max(0.0, at1[1] - 60), at1[1] + 60, 2.0, "fine")

print("\n[3] 再细扫")
g3, at3 = scan(at2[0] - 6, at2[0] + 6, max(0.0, at2[1] - 6), at2[1] + 6, 0.25, "ultra")

print("\n[4] 加宽验证：b 撑到 1200 / a 撑到 2400 的粗扫（确认没有更远的峰）")
scan(-800, 2400, 0, 1400, 40.0, "wide")

print("\n[5] 结论")
print(f"  全局最大可保证交会角 = {g3:.4f}deg  at ({at3[0]:.2f},{at3[1]:.2f})")
print(f"  对照报告值 39.616116deg，差 {abs(g3-39.616116):.4f}deg")
print(f"  40deg 可达？ {'是（需重述）' if g3 >= 40.0 else '否（本网格未出现）'}")
