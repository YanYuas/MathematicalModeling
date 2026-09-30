# -*- coding: utf-8 -*-
"""
⚠️⚠️ 本脚本的判据是错的，结论作废；仅作留痕保留，请勿引用其结论 ⚠️⚠️
====================================================================
【错在哪】本脚本用 `min_alpha n(alpha) / max_{alpha,r} d2` 作判据 —— 分子取 min、
分母取 max，二者在**不同** alpha 处取得。由此得到的量 Q 与真正的保证角 G 满足

        Q  <=  G            （Q 是 G 的**下界**，不是上界）

因为对每个 alpha 都有 n(alpha) >= min n 且 d2(alpha) <= max d2，故
n(alpha)/d2(alpha) >= min n / max d2，逐 alpha 成立 ⇒ 取 min 后仍成立。

⇒ Q < 40° **不能**推出 G < 40°，即**不能**支撑"40° 全局不可达"这一**上界**断言。
   本脚本末尾打印的"严格判据下的全局最大可保证交会角 = 39.6107° …40deg 可达？否 ——
   全局严格确认不可达"是**方向搞反的产物**，结论作废。

【正确判据】源的真实参数 (r, alpha) 是同一个，(r, alpha) 联合最坏 ⇒ 必须逐 alpha 耦合：

        G(a,b) = min_{alpha in [-eps,eps]}  n(alpha) / D(alpha),
        D(alpha) = max_{r in [5,1500]} d2(r, alpha)

见同目录 `_可达上界全局复核_逐alpha.py`（**该脚本已精确复现 39.616116°**，且宽域网格
`a in [-800,2400]`、`b in [0,1400]` 内无任何 >=40° 的可行点）。

【保留理由】按 `版本管理规范` §五"不删除历史"，把这次判据方向搞反的过程留痕；
同时提醒：**"最坏化"必须对同一个不确定量实例同时取最坏，不能分子分母各取各的最坏。**

--------------------------------------------------------------------
以下为原（错误）说明，保留原样：

问题：`Q2_数值修订清单.md` 与本文 `建模手-联合校验报告.md` 给出的 39.6161°
      来自局部网格搜索（a in [700,821], b in [600,701]）⇒ 只是"下界可达点"，
      **不能**支撑"40° 不可达"这一上界断言。

本脚本给出**严格判据**（不依赖最坏 alpha 方向相反的启发式论证）：
  保证 phi >= phi_min  ⟺  min_alpha n(alpha)  >=  sin(phi_min) * max_{alpha,r} d2
其中 n(alpha) = |a sin a - b cos a|（与 r 无关），
     d2^2(r,alpha) = a^2+b^2+r^2 - 2r(a cos a + b sin a)（关于 r 为开口向上抛物线 => r 取端点）。

n 的取法（严格）：n = sqrt(a^2+b^2)*|sin(alpha - phi0)|，phi0 = atan2(b,a)。
  若 |phi0| <= eps => 区间含零点 => min n = 0（退化，不可行）
  否则 |sin| 在区间上无零点、单峰对称 => min 在两端点取到。
d2 的取法（严格）：max over alpha 在 {-eps, +eps, 驻点 atan2(b,a) 若落在区间内}，
  r 在 {5, R_max=1500} 端点。

然后对 (a,b) 全局细网格求 max phi_min。无需模拟器。
"""
import math
import numpy as np

EPS = math.radians(1.0)
R_WORST = 1000.0
R_MAX = 1500.0
R_MIN = 5.0


def min_num(a, b):
    """min over alpha in [-eps,eps] of |a*sin a - b*cos a|  —— 严格。"""
    rho = math.hypot(a, b)
    if rho == 0.0:
        return 0.0
    phi0 = math.atan2(b, a)              # a*sin x - b*cos x = rho*sin(x - phi0)
    if abs(phi0) <= EPS:                 # 零点落在区间内
        return 0.0
    cand = [abs(rho * math.sin(-EPS - phi0)), abs(rho * math.sin(EPS - phi0))]
    return min(cand)


def max_d2(a, b):
    """max over alpha in [-eps,eps], r in {5,1500} of d2 —— 严格（r 端点 + alpha 端点/驻点）。"""
    alphas = [-EPS, EPS]
    phi0 = math.atan2(b, a)
    if abs(phi0) <= EPS:                 # 驻点（a cos a + b sin a 的最小值点）
        alphas.append(phi0)
    best = 0.0
    for al in alphas:
        s = a * math.cos(al) + b * math.sin(al)
        for r in (R_MIN, R_MAX):
            d2sq = a * a + b * b + r * r - 2.0 * r * s
            if d2sq > best:
                best = d2sq
    return math.sqrt(best)


def guarantee_angle(a, b):
    """该 (a,b) 能保证的交会角（度）。不满足 d2<=R_worst 或无正保证时返回 0。"""
    d = max_d2(a, b)
    if d > R_WORST:
        return 0.0
    n = min_num(a, b)
    if n <= 0.0:
        return 0.0
    s = n / d
    if s <= 0.0 or s > 1.0:
        return 0.0
    return math.degrees(math.asin(s))


def scan(a_lo, a_hi, b_lo, b_hi, step, label):
    a = np.arange(a_lo, a_hi + 1e-9, step)
    b = np.arange(b_lo, b_hi + 1e-9, step)
    best, at = 0.0, None
    for aa in a:
        for bb in b:
            g = guarantee_angle(aa, bb)
            if g > best:
                best, at = g, (aa, bb)
    print(f"  {label}: step={step}m, {len(a)}x{len(b)} = {len(a)*len(b)} 点")
    print(f"    max phi = {best:.6f}deg  at (a,b)=({at[0]:.1f},{at[1]:.1f})")
    return best, at


print("=" * 74)
print("⚠️ 判据错误版本（留痕）—— 结论不可引用，请用 _可达上界全局复核_逐alpha.py")
print("=" * 74)
print("本脚本用 min_alpha n / max_{alpha,r} d2 作判据，该量是 G 的下界，")
print("不能证不可达。以下数值仅作过程留痕，**下方'不可达'字样不成立**。")
print("=" * 74)
print()
print("=" * 74)
print("Q2 可达交会角上界 —— 全局复核（判据错误版，留痕）")
print(f"eps={math.degrees(EPS)}deg, R_worst={R_WORST}, r in [{R_MIN},{R_MAX}]")
print("=" * 74)

print("\n[0] 自检：alpha 修正后 a=d_hat 处是否真的空集")
for bb in (627.226974, 638.0, 650.0, 664.261808):
    print(f"  b={bb:10.4f}  max d2={max_d2(752.5, bb):10.4f}  min n={min_num(752.5, bb):10.4f}"
          f"  guarantee={guarantee_angle(752.5, bb):7.4f}deg")

print("\n[1] 全局粗扫（第一步）")
g1, at1 = scan(-400, 1800, 0, 1200, 20.0, "coarse")

print("\n[2] 在粗扫最优邻域细扫（第二步）")
g2, at2 = scan(at1[0] - 60, at1[0] + 60, max(0, at1[1] - 60), at1[1] + 60, 2.0, "fine")

print("\n[3] 再细扫（第三步）")
g3, at3 = scan(at2[0] - 6, at2[0] + 6, max(0, at2[1] - 6), at2[1] + 6, 0.25, "ultra")

print("\n[4] 结论")
print(f"  严格判据下的全局最大可保证交会角 = {g3:.4f}deg  at ({at3[0]:.2f},{at3[1]:.2f})")
print(f"  与 39.6161deg 相差 {abs(g3 - 39.616116):.4f}deg")
print(f"  ⚠️ 本量为 G 的下界；'40deg 不可达'的断言**不能**由本脚本得出（判据方向搞反）")

print("\n[5] alpha=0 对照（同判据，只把 eps 置 0 附近）")
EPS_BACK = EPS
EPS = 1e-12
print(f"  eps->0 时全局最大 = {scan(-400, 1800, 0, 1200, 20.0, 'alpha=0 coarse')[0]:.4f}deg")
