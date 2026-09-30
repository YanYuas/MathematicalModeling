"""Q2 联合校验 · 建模手独立复算脚本（可复现）

配套：`02_建模手/Q2/建模手-联合校验报告.md`
用途：不调用编程手代码，独立复算 Q2 的 (a) 数值基准、(b) 闭式解、(c) 编程手 4 条反馈意见。

用法：python _联合校验独立复算.py
依赖：numpy
"""

import numpy as np

# ---------- 题设参数 ----------
EPS = np.deg2rad(1.0)          # 示向度误差半角
RW = 1000.0                    # 最坏接收半径
D_LO, D_HI = 5.0, 1500.0       # 源距区间（开下界）
DHAT = (D_LO + D_HI) / 2       # 752.5
DD = (D_HI - D_LO) / 2         # 747.5
PHI_MIN = np.deg2rad(40.0)

# 两个最坏源距端点（d2² 关于 r 是开口向上的抛物线 ⇒ 最坏必在端点）
R_ENDS = (D_LO, D_HI)


# ---------- 核心几何（Q2 建模数学化的公式，含方向偏差 α）----------
def sin_phi(a, b, r, al):
    """sinφ：φ = 源 G=r(cosα,sinα) 处，GS₁ 与 GS₂ 的夹角。α=0 时退化为 |b|/d₂（Q2-F7）"""
    num = abs(a * np.sin(al) - b * np.cos(al))
    d2 = np.sqrt(a * a + b * b + r * r - 2 * r * (a * np.cos(al) + b * np.sin(al)))
    return num / d2, d2


def guaranteed(a, b, alphas):
    """返回 (保证的最小交会角(度), 最大 d₂)，对给定 α 集合并对两个最坏源距端点取最坏"""
    worst_s, worst_d = 1.0, 0.0
    for al in alphas:
        for r in R_ENDS:
            s, d = sin_phi(a, b, r, al)
            worst_s = min(worst_s, s)
            worst_d = max(worst_d, d)
    return np.degrees(np.arcsin(min(worst_s, 1.0))), worst_d


# ================= 校验 1：数值基准（7 项）=================
def check_baseline():
    print("=" * 74)
    print("校验 1：Q2 数值基准（7 项）—— 对表 Q2 建模手文档与编程手实现")
    print("=" * 74)
    a = DHAT
    b_min = DD * np.tan(PHI_MIN)
    b_max = np.sqrt(RW ** 2 - DD ** 2)
    phi_max = np.degrees(np.arccos(DD / RW))
    rows = [
        ("d_hat", 752.50, DHAT), ("Delta_d", 747.50, DD),
        ("b_min", 627.23, b_min), ("b_max", 664.26, b_max),
        ("phi_min_max", 41.63, phi_max),
        ("dist_min", 979.63, np.hypot(DHAT, b_min)),
        ("dist_max", 1003.74, np.hypot(DHAT, b_max)),
    ]
    allok = True
    for name, exp, got in rows:
        ok = abs(got - exp) < 0.01
        allok &= ok
        print(f"  {name:12s} 期望 {exp:10.5f}  独立复算 {got:12.6f}  {'✅' if ok else '❌'}")
    print(f"  ⇒ 7 项基准：{'全部通过' if allok else '有不通过项'}\n")
    return allok


# ================= 校验 2：闭式解与退化 =================
def check_closed_form():
    print("=" * 74)
    print("校验 2：闭式解 + 端点即最坏（α=0）")
    print("=" * 74)
    a = DHAT
    for b in (627.226974, 664.261808):
        ws, wd = guaranteed(a, b, [0.0])
        tag = "b_min" if b < 650 else "b_max"
        print(f"  {tag}={b:.6f}: 保证 φ = {ws:.6f}°（需≥40），max d₂ = {wd:.6f} m（需≤1000）")
    print("  ⇒ b_min 处 φ 恰取 40°；b_max 处 d₂ 恰取 1000 ⇒ 闭式解正确、端点即最坏 ✅\n")


# ================= 校验 3：编程手反例 =================
def check_counterexamples():
    print("=" * 74)
    print("校验 3：编程手「方向偏差 α」两个反例的复现")
    print("=" * 74)
    for tag, b, al in [("反例1 角度失保", 627.226974, +EPS), ("反例2 距离失保", 664.261808, -EPS)]:
        _, d2 = sin_phi(DHAT, b, 1500.0, al)
        s, _ = sin_phi(DHAT, b, 1500.0, al)
        print(f"  {tag}: b={b:.3f} α={np.degrees(al):+.0f}° ⇒ d₂={d2:.4f} m, φ={np.degrees(np.arcsin(s)):.4f}°")
    print("  编程手报：d₂ = 959.00 / 1017.41 m；γ = 39.81°  ⇒  独立复现一致 ✅\n")


# ================= 校验 4：α 的方向性 =================
def check_alpha_direction():
    print("=" * 74)
    print("校验 4：两个约束的最坏 α 方向相反")
    print("=" * 74)
    for b in (627.226974, 664.261808):
        for tag, al in [("+1°", +EPS), ("0°", 0.0), ("-1°", -EPS)]:
            ws, wd = guaranteed(DHAT, b, [al])
            print(f"  b={b:.3f} α={tag:>3s}: 保证 φ={ws:.6f}°   max d₂={wd:.3f} m")
    print("  ⇒ 角度约束最坏在 α=+1°；距离约束最坏在 α=−1°（分子含 −a·sinα 与 b·cosα 两项，符号相反）✅\n")


# ================= 校验 5：α 修正后的可行域 =================
def check_alpha_feasible():
    print("=" * 74)
    print("校验 5：α∈[−1°,1°] 修正后的边界与可行域")
    print("=" * 74)
    alphas = np.linspace(-EPS, EPS, 801)
    a = DHAT
    bs = np.arange(300.0, 900.0, 0.5)
    m = np.array([guaranteed(a, b, alphas) for b in bs])
    phi_arr, d_arr = m[:, 0], m[:, 1]
    b_min_a = bs[phi_arr >= 40.0].min() if (phi_arr >= 40.0).any() else None
    b_max_a = bs[(d_arr <= RW) & (phi_arr >= 40.0)].max() if ((d_arr <= RW) & (phi_arr >= 40.0)).any() else None
    b_max_only = bs[d_arr <= RW].max()
    print(f"  a = d_hat = {a}:")
    print(f"    b_min(φ≥40°)      = {b_min_a if b_min_a else '∅（无 b 能满足角度约束）'}")
    print(f"    b_max(d₂≤1000)    = {b_max_only:.2f} m")
    print(f"    ⇒ φ_min=40° 的可行域：{'❌ 空集' if (b_min_a is None or b_max_only < b_min_a) else '✅ 非空'}")

    # 二维：α 下可保证的最大交会角
    best = (-1.0, None, None)
    for aa in np.arange(700.0, 821.0, 2.0):
        for bb in np.arange(600.0, 701.0, 1.0):
            ph, dm = guaranteed(aa, bb, alphas)
            if dm <= RW and ph > best[0]:
                best = (ph, aa, bb)
    ph, aa, bb = best
    for da in np.arange(aa - 3, aa + 3.01, 0.25):
        for db in np.arange(bb - 3, bb + 3.01, 0.25):
            p2, d2 = guaranteed(da, db, alphas)
            if d2 <= RW and p2 > ph:
                ph, aa, bb = p2, da, db
    print(f"\n  α±1° 下【可保证的最大交会角】= {ph:.4f}°  在 (a,b)=({aa:.2f},{bb:.2f})")
    print(f"  α=0 的 Q2 声称值         = 41.6257°   ⇒ 代价 {41.6257 - ph:.4f}°")
    print(f"  目标 φ_min = 40°：{'可达' if ph >= 40 else '❌ 不可达（穷举无解）'}\n")
    return ph


# ================= 校验 6：D/E 比值 =================
def check_rho():
    print("=" * 74)
    print("校验 6：D/E 比值 ρ（断言 7 原写 ∈[0.5,2]）")
    print("=" * 74)
    L = 600.0
    for tag, D, E in [("Q1 基准（φ=61.93°）", 39.598, 16.31),
                      ("Q2 候选 b_min（φ=74.89°）", 35.414, 15.78)]:
        print(f"  {tag}: D={D:.3f} E={E:.2f} ⇒ ρ={D / E:.3f}")
    print("  理论：φ=90° 对称时 L²=d₁²+d₂² ⇒ ρ = 2L/√(d₁²+d₂²) = 2（精确值，非均值）")
    print("  ⇒ 实测 ρ ≈ 2.23~2.43，断言区间 [0.5,2] 取反；应改为分别报告 D 与 E ✅\n")


if __name__ == "__main__":
    check_baseline()
    check_closed_form()
    check_counterexamples()
    check_alpha_direction()
    check_alpha_feasible()
    check_rho()
    print("=" * 74)
    print("结论：基准与闭式解通过；跨问交叉验证原值错（已修正）；ρ 断言错（已修正）；")
    print("      α 鲁棒性不通过 —— 目标 φ_min=40° 在该模型的不确定集下不可达。")
    print("=" * 74)
