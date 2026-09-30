# -*- coding: utf-8 -*-
"""
Q2 论文配图（规范集）—— 严格按 `04_论文手/Q2/正稿.md` 的图号与标题出图

为什么要这一套
--------------
现存两套图都**不能直接进论文**：
  · 建模手集 `03_编程手/Q2/实验结果/figs/fig5_2_*.png`（6 张）
    —— 文件名号与**图内标题号**均与正稿错位（其"图5.2-1"是候选区域，而正稿的
       图 5.2-1 是最优配置示意；且缺 图 5.2-2 三行关系式、图 5.2-7 跨问对比）。
  · 编程手集 `03_编程手/Q2/实验结果/Fig1..Fig6.png`（6 张）—— 标题为英文，编号另一套。
两套图的**内容**都可用，故本脚本以正稿编号重出全部 8 张，作为唯一投稿集；
两套旧图原样保留（留痕，不删除）。

正稿图清单（`正稿.md`）
    图 5.2-1 最优配置示意（源-两测点直角三角形 + Thales 圆过源）
    图 5.2-2 三行关系式示意（Δ、b、d₂、φ）
    图 5.2-3 候选区域图（左：两条线段；右：双翼形）
    图 5.2-4 权衡曲线（φ_min^max = arccos(Δd/R) vs Δd）
    图 5.2-5 退化对比示意（b=0 三点共线 vs b≠0）
    图 5.2-6 E 等高线与可行域边界
    图 5.2-7 跨问对比（问题一原例 vs 问题二候选位）
    图 5.2-8【新增】定理 5.2-3 配套（α=0 与含 α∈[−1°,1°] 的可保证交会角对比）

输出：`04_论文手/Q2/配图/fig5_2_*.png`（300 dpi）
依赖：numpy、matplotlib（无需模拟器）
"""
import math
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Arc, Polygon

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "04_论文手", "Q2", "配图"))
os.makedirs(OUT, exist_ok=True)

# ---------- 基准参数（正稿 5.2.0） ----------
EPS_DEG = 1.0
EPS = math.radians(EPS_DEG)
D_HAT = 752.5          # 源距区间中点
D_DD = 747.5           # 源距区间半宽
PHI_MIN = 40.0         # 目标最小交会角
R_WORST = 1000.0       # 最坏接收半径
D_LO, D_HI = 5.0, 1500.0
B_MIN = D_DD * math.tan(math.radians(PHI_MIN))
B_MAX = math.sqrt(R_WORST ** 2 - D_DD ** 2)

FIG = []


def save(fig, name, caption):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    FIG.append((name, caption))
    print("  ✓", name, "—", caption)


def E_of(a, b, d1=D_HAT):
    """位置不确定度 E(a,b) = ε·√(d₁²+d₂²)/sinφ（向量化）。b→0 时发散。"""
    d2 = np.hypot(d1 - a, b)
    with np.errstate(divide="ignore", invalid="ignore"):
        e = EPS * np.sqrt(d1 ** 2 + d2 ** 2) * d2 / np.abs(b)
    return e


# ==================================================================
print("=" * 72)
print("Q2 规范配图 → ", OUT)
print("=" * 72)

# ---------------------------------------------------------------- 图 5.2-1
print("\n[图 5.2-1] 最优配置示意")
fig, ax = plt.subplots(figsize=(7.2, 5.4))
d1, b = 700.0, 620.0
S1 = np.array([0.0, 0.0])
S2 = np.array([d1, b])
G = np.array([d1, 0.0])
C = (S1 + S2) / 2.0
Rc = np.linalg.norm(S2 - S1) / 2.0

ax.add_patch(Circle(C, Rc, fill=False, ls="--", lw=1.6, ec="#1f77b4", alpha=0.9,
                    label="以 S₁S₂ 为直径的圆（Thales 圆）"))
ax.plot([S1[0], S2[0]], [S1[1], S2[1]], "-", color="k", lw=1.6)
ax.plot([G[0], S1[0]], [G[1], S1[1]], "-", color="#d62728", lw=1.6)
ax.plot([G[0], S2[0]], [G[1], S2[1]], "-", color="#d62728", lw=1.6)
for P, nm, dx, dy in [(S1, "S₁", -55, -32), (S2, "S₂", 14, 10), (G, "G（源）", 12, -34)]:
    ax.plot(*P, "o", color="k", ms=6)
    ax.annotate(nm, P, textcoords="offset points", xytext=(dx, dy), fontsize=12)
ax.add_patch(Arc(G, 200, 200, theta1=0, theta2=180, color="#2ca02c", lw=2.0))
ax.annotate("φ = 90°", (d1 - 130, 55), color="#2ca02c", fontsize=13)
ax.plot([d1, d1], [0, b], ":", color="gray", lw=1.0)
ax.annotate("a = d₁（正侧方对齐）", ((d1) / 2, b + 40), fontsize=11, color="#1f77b4", ha="center")
ax.annotate("∠S₁GS₂ = 90° ⟺ G 落在以 S₁S₂ 为直径的圆上", (330, 300), fontsize=11.5)
ax.set_aspect("equal")
ax.set_xlim(-140, d1 + 240)
ax.set_ylim(-140, b + 200)
ax.set_xlabel("x（沿示向度中线，m）"); ax.set_ylabel("y（垂直中线，m）")
ax.set_title("图 5.2-1  最优第二检测点配置：源处直角 + Thales 圆过源", fontsize=12.5)
ax.legend(loc="upper left", fontsize=9.5); ax.grid(alpha=0.3)
save(fig, "fig5_2_1_optimal_config.png", "图 5.2-1 最优配置示意")

# ---------------------------------------------------------------- 图 5.2-2
print("\n[图 5.2-2] 三行关系式示意")
fig, ax = plt.subplots(figsize=(7.2, 5.4))
a_, b_ = 420.0, 470.0
G = np.array([D_HAT, 0.0]); S1 = np.array([0.0, 0.0]); S2 = np.array([a_, b_])
Dlt = D_HAT - a_
ax.plot([S1[0], S2[0]], [S1[1], S2[1]], "-", color="k", lw=1.6)
ax.plot([G[0], S1[0]], [G[1], S1[1]], "-", color="#d62728", lw=1.6)
ax.plot([G[0], S2[0]], [G[1], S2[1]], "-", color="#d62728", lw=1.6)
ax.plot([a_, a_], [0, b_], ":", color="gray", lw=1.2)
ax.plot([a_, D_HAT], [0, 0], ":", color="gray", lw=1.2)
ax.annotate("", (a_, 90), (a_ - Dlt, 90), arrowprops=dict(arrowstyle="<->", color="#1f77b4"))
ax.annotate("Δ = d₁ − a", ((a_ + D_HAT) / 2 - Dlt / 2, 105), color="#1f77b4", fontsize=12, ha="center")
ax.annotate("", (a_ + 42, b_), (a_ + 42, 0), arrowprops=dict(arrowstyle="<->", color="#2ca02c"))
ax.annotate("b", (a_ + 52, b_ / 2), color="#2ca02c", fontsize=13)
ax.add_patch(Arc(G, 150, 150, theta1=0, theta2=180, color="#9467bd", lw=2.0))
ax.annotate("φ", (D_HAT - 118, 52), color="#9467bd", fontsize=13)
ax.annotate("d₂", ((G[0] + S2[0]) / 2 + 26, b_ / 2 + 24), fontsize=12, color="#d62728", rotation=-63)
ax.annotate("d₁", (D_HAT / 2 - 30, -46), fontsize=12, color="#d62728")
for P, nm, dx, dy in [(S1, "S₁", -46, -30), (S2, "S₂", 14, 6), (G, "G（源）", 10, -32)]:
    ax.plot(*P, "o", color="k", ms=6)
    ax.annotate(nm, P, textcoords="offset points", xytext=(dx, dy), fontsize=12)
ax.text(60, b_ + 190,
        "d₂ = √(Δ² + b²)\ncos φ = Δ / d₂\nsin φ = |b| / d₂",
        fontsize=13, family="DejaVu Sans",
        bbox=dict(boxstyle="round,pad=0.5", fc="#fff8e1", ec="#f0ad4e"))
ax.set_aspect("equal")
ax.set_xlim(-120, D_HAT + 220); ax.set_ylim(-120, b_ + 330)
ax.set_xlabel("x（沿示向度中线，m）"); ax.set_ylabel("y（垂直中线，m）")
ax.set_title("图 5.2-2  交会角的三行关系式", fontsize=12.5)
ax.grid(alpha=0.3)
save(fig, "fig5_2_2_three_relations.png", "图 5.2-2 三行关系式示意")

# ---------------------------------------------------------------- 图 5.2-3
print("\n[图 5.2-3] 候选区域图（简化版 + 双翼形）")
fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.0))

ax = axes[0]
ax.plot([D_HAT, D_HAT], [B_MIN, B_MAX], lw=5, color="#1f77b4", solid_capstyle="butt",
        label="候选段  $b\\in[b_{min},b_{max}]$")
ax.plot([D_HAT, D_HAT], [-B_MIN, -B_MAX], lw=5, color="#1f77b4", solid_capstyle="butt")
ax.plot(D_HAT, 0, "x", color="k", ms=8)
ax.annotate("a = d̂ = 752.5 m", (D_HAT, 0), textcoords="offset points", xytext=(-30, -34), fontsize=11)
ax.annotate(f"b_min = {B_MIN:.2f} m\nb_max = {B_MAX:.2f} m\n宽度 = {B_MAX-B_MIN:.2f} m",
            (D_HAT, B_MAX), textcoords="offset points", xytext=(-165, -18), fontsize=11,
            bbox=dict(boxstyle="round,pad=0.4", fc="#eaf3ff", ec="#1f77b4"))
ax.set_title("(a) 简化版：a 锁定为 d̂ 时的两条线段", fontsize=12)
ax.set_xlim(D_HAT - 260, D_HAT + 260); ax.set_ylim(-840, 840)
ax.set_xlabel("a（深度方向，m）"); ax.set_ylabel("b（横向偏移，m）")

ax = axes[1]
a_span = R_WORST * math.cos(math.radians(PHI_MIN)) - D_DD
aa = np.linspace(D_HAT - a_span, D_HAT + a_span, 400)
m = np.abs(aa - D_HAT) + D_DD
blo = m * math.tan(math.radians(PHI_MIN))
bhi = np.sqrt(np.maximum(R_WORST ** 2 - m ** 2, 0.0))
for sgn in (1, -1):
    xs = np.concatenate([aa, aa[::-1]])
    ys = sgn * np.concatenate([bhi, blo[::-1]])
    ax.add_patch(Polygon(np.c_[xs, ys], closed=True, fc="#1f77b4", alpha=0.18, ec="#1f77b4", lw=1.4))
ax.axvline(D_HAT, ls=":", color="k", lw=1.0)
ax.plot(D_HAT, 0, "x", color="k", ms=8)
ax.annotate("a = d̂", (D_HAT, 0), textcoords="offset points", xytext=(-12, -34), fontsize=11)
ax.annotate(f"a_span = R·cos φ_min − Δd = {a_span:.2f} m",
            (D_HAT, 700), ha="center", fontsize=10.5,
            bbox=dict(boxstyle="round,pad=0.4", fc="#fff8e1", ec="#f0ad4e"))
ax.set_title("(b) 完整版：允许 a 偏离 d̂ 时的两片翼形", fontsize=12)
ax.set_xlim(D_HAT - 500, D_HAT + 500); ax.set_ylim(-1080, 1080)
ax.set_xlabel("a（深度方向，m）"); ax.set_ylabel("b（横向偏移，m）")

fig.suptitle("图 5.2-3  第二检测点候选区域（Δd = 747.5 m，φ_min = 40°，R = 1000 m；"
             "以上为 α = 0 口径）", fontsize=12.5, y=1.02)
save(fig, "fig5_2_3_candidate_region.png", "图 5.2-3 候选区域图")

# ---------------------------------------------------------------- 图 5.2-4
print("\n[图 5.2-4] 权衡曲线")
fig, ax = plt.subplots(figsize=(7.6, 5.2))
dd = np.linspace(1, 900, 800)
for R, c in [(1000, "#d62728"), (1250, "#1f77b4"), (1500, "#2ca02c")]:
    ax.plot(dd, np.degrees(np.arccos(np.clip(dd / R, -1, 1))), lw=2.0, color=c, label=f"R = {R} m")
ax.axhline(PHI_MIN, ls="--", color="gray", lw=1.2)
ax.annotate("目标 φ_min = 40°", (860, 41.5), ha="right", fontsize=10.5, color="gray")
ax.plot(D_DD, 41.625718, "o", ms=9, color="#d62728")
ax.annotate("本算例：(Δd, φ_min^max)\n= (747.5, 41.626°)",
            (D_DD, 41.625718), textcoords="offset points", xytext=(-150, -58), fontsize=11,
            bbox=dict(boxstyle="round,pad=0.4", fc="#eaf3ff", ec="#d62728"))
ax.plot([D_DD, D_DD], [0, 41.625718], ":", color="#d62728", lw=1.0)
ax.axvline(766.044, ls=":", color="#2ca02c", lw=1.2)
ax.annotate("Δd 可行上限 766.044 m\n（R=1000, φ_min=40°）", (766.044, 78), fontsize=10,
            color="#2ca02c", ha="center")
ax.set_xlabel("源距不确定半宽 Δd（m）"); ax.set_ylabel("可保证交会角上界 φ_min$^{max}$（°）")
ax.set_xlim(0, 900); ax.set_ylim(0, 92)
ax.set_title("图 5.2-4  可保证交会角与源距不确定度的权衡（α = 0）", fontsize=12.5)
ax.legend(fontsize=10.5); ax.grid(alpha=0.3)
save(fig, "fig5_2_4_tradeoff_curve.png", "图 5.2-4 权衡曲线")

# ---------------------------------------------------------------- 图 5.2-5
print("\n[图 5.2-5] 退化对比示意")
fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.8))

ax = axes[0]
ax.plot([0, D_HAT + 200], [0, 0], "-", color="k", lw=1.4)
for P, nm, dy in [(np.array([0.0, 0.0]), "S₁", -30), (np.array([420.0, 0.0]), "S₂", -30),
                  (np.array([D_HAT, 0.0]), "G（源）", 16)]:
    ax.plot(*P, "o", color="k", ms=6)
    ax.annotate(nm, P, textcoords="offset points", xytext=(-8, dy), fontsize=12)
ax.annotate("三点共线 ⇒ 两条视线重合 ⇒ sin φ = 0 ⇒ E → ∞", (60, 68), fontsize=12, color="#d62728")
ax.annotate("（沿示向度前进：零信息）", (60, 34), fontsize=11, color="#d62728")
ax.set_xlim(-90, D_HAT + 250); ax.set_ylim(-70, 120)
ax.set_yticks([]); ax.set_xlabel("x（沿示向度中线，m）")
ax.set_title("(a) 退化：b = 0", fontsize=12)

ax = axes[1]
bb = np.linspace(1.0, 700, 900)
ax.plot(bb, E_of(D_HAT, bb), lw=2.0, color="#1f77b4")
ax.set_yscale("log")
ax.axhline(E_of(D_HAT, B_MIN), ls="--", color="#d62728", lw=1.2)
ax.annotate(f"b = b_min = {B_MIN:.2f} m\nE = {E_of(D_HAT, B_MIN):.2f} m", (B_MIN, E_of(D_HAT, B_MIN)),
            textcoords="offset points", xytext=(24, 34), fontsize=10.5, color="#d62728",
            arrowprops=dict(arrowstyle="->", color="#d62728"))
ax.annotate("b → 0 时 E 发散", (12, 2.4e3), fontsize=11, color="#1f77b4")
ax.set_xlabel("横向偏移 b（m）"); ax.set_ylabel("位置不确定度 E（m，对数轴）")
ax.set_title("(b) 横向偏移是信息的来源：E(b)", fontsize=12)
ax.grid(alpha=0.3, which="both")

fig.suptitle("图 5.2-5  退化对比：沿示向度前进（b = 0）无信息增益", fontsize=12.5, y=1.02)
save(fig, "fig5_2_5_degenerate.png", "图 5.2-5 退化对比示意")

# ---------------------------------------------------------------- 图 5.2-6
print("\n[图 5.2-6] E 等高线与可行域边界")
fig, ax = plt.subplots(figsize=(7.8, 5.8))
aa = np.linspace(150, 1350, 600)
bb = np.linspace(2, 900, 450)
A, B = np.meshgrid(aa, bb)
Em = E_of(A, B)
lev = np.logspace(math.log10(16), math.log10(400), 18)
cs = ax.contourf(A, B, Em, levels=lev, cmap="viridis", alpha=0.85)
plt.colorbar(cs, ax=ax, label="位置不确定度 E（m，对数分级）")
mc = np.abs(A - D_HAT) + D_DD
ax.contour(A, B, mc * math.tan(math.radians(PHI_MIN)) - B, levels=[0], colors="#ff4d4d", linewidths=2.2)
ax.contour(A, B, np.hypot(mc, B) - R_WORST, levels=[0], colors="w", linewidths=2.2)
ax.plot([D_HAT, D_HAT], [2, 900], ls=":", color="w", lw=1.6)
ax.plot(D_HAT, B_MIN, "o", ms=9, mfc="none", mec="#ff4d4d", mew=2.4)
ax.annotate(f"最优候选点 (d̂, b_min)\n= ({D_HAT:.1f}, {B_MIN:.2f})", (D_HAT, B_MIN),
            textcoords="offset points", xytext=(-30, 78), fontsize=10.5, color="w",
            bbox=dict(boxstyle="round,pad=0.35", fc="#00000066", ec="none"))
ax.plot([], [], color="#ff4d4d", lw=2.2, label="角度约束边界  b = m(a)·tan φ_min")
ax.plot([], [], color="w", lw=2.2, label="可探测边界  √(m(a)² + b²) = R")
ax.plot([], [], ls=":", color="w", lw=1.6, label="最优线  a = d̂")
ax.set_xlabel("a（深度方向，m）"); ax.set_ylabel("b（横向偏移，m）")
ax.set_title("图 5.2-6  E 等高线与可行域边界（Δd = 747.5 m，φ_min = 40°，R = 1000 m）", fontsize=12.5)
ax.legend(loc="upper right", fontsize=9.5, facecolor="#00000099", labelcolor="w")
save(fig, "fig5_2_6_E_contour.png", "图 5.2-6 E 等高线与可行域边界")

# ---------------------------------------------------------------- 图 5.2-7
print("\n[图 5.2-7] 跨问对比")
cases = [("问题一原例\nS₂=(600, 0)", 39.598, 16.31, 600.0, "#7f7f7f"),
         ("候选位 b=b_min\n(−150.68, 967.97)", 35.414, 15.78, 979.63, "#d62728"),
         ("候选位 中点\n(−166.56, 977.50)", 35.777, 15.99, 991.59, "#ff9f4d"),
         ("候选位 b=b_max\n(−182.44, 987.02)", 36.151, 16.21, 1003.74, "#f0ad4e")]
fig, axes = plt.subplots(1, 3, figsize=(14.0, 4.6))
x = np.arange(len(cases)); w = 0.38
Dv = [c[1] for c in cases]; Ev = [c[2] for c in cases]
Sv = [c[3] for c in cases]; col = [c[4] for c in cases]

axes[0].bar(x, Dv, w * 1.6, color=col)
for i, v in enumerate(Dv):
    axes[0].text(i, v + 0.35, f"{v:.3f}", ha="center", fontsize=10.5)
axes[0].axhline(20, ls="--", color="k", lw=1.1)
axes[0].annotate("清除半径 20 m", (3.4, 20.9), ha="right", fontsize=9.5)
axes[0].set_ylabel("定位区域直径 D（m）"); axes[0].set_ylim(0, 48)
axes[0].set_title("(a) D：10.57% 改善", fontsize=12)

axes[1].bar(x, Ev, w * 1.6, color=col)
for i, v in enumerate(Ev):
    axes[1].text(i, v + 0.22, f"{v:.2f}", ha="center", fontsize=10.5)
axes[1].set_ylabel("RMS 位置误差 E（m）"); axes[1].set_ylim(0, 20)
axes[1].set_title("(b) E：3.25% 改善", fontsize=12)

axes[2].bar(x, Sv, w * 1.6, color=col)
for i, v in enumerate(Sv):
    axes[2].text(i, v + 18, f"{v:.2f}", ha="center", fontsize=10.5)
axes[2].set_ylabel("两站间距 |S₁S₂|（m）"); axes[2].set_ylim(0, 1200)
axes[2].set_title("(c) 代价：行程 +63.3%", fontsize=12)

for ax in axes:
    ax.set_xticks(x)
    ax.set_xticklabels([c[0] for c in cases], fontsize=8.6)
    ax.grid(alpha=0.28, axis="y")
fig.suptitle("图 5.2-7  跨问对比：问题一原例 vs 问题二候选位（均为实测值）", fontsize=13, y=1.03)
save(fig, "fig5_2_7_cross_question.png", "图 5.2-7 跨问对比")

# ---------------------------------------------------------------- 图 5.2-8
print("\n[图 5.2-8] 定理 5.2-3 配套（α=0 vs 含 α）—— 需数值搜索，稍候")


def max_guaranteed_alpha(Dd, R=R_WORST, n_alpha=41,
                         a_lo=0.0, a_hi=1500.0, b_lo=0.0, b_hi=1500.0,
                         step=25.0, stages=((40.0, 2.0), (4.0, 0.25))):
    """数值求 max over (a,b) of  min over α 的保证交会角（逐 α 耦合判据）。

    【关键口径】源距 r 的可取范围必须与 α = 0 的闭式解 arccos(Δd/R) **一致**：
        r ∈ [d̂ − Δd, d̂ + Δd] ∩ [5, 1500]        （即 Δd 是"对源距的先验半宽"）
    若不这样取（例如一律取满 [5,1500]），则 Δd 根本不进入判据，曲线会退化为
    一条与 Δd 无关的水平线——那不是"两条曲线的对比"，而是口径不一致的伪像。

    判据：G(a,b) = min_α  n(α)/D(α)，n = |a sinα − b cosα|，
          D(α) = sqrt(max_{r∈{r_lo, r_hi}} d₂²)，且需 max_α D(α) ≤ R。
    """
    r_lo = max(D_LO, D_HAT - Dd)
    r_hi = min(D_HI, D_HAT + Dd)
    al = np.linspace(-EPS, EPS, n_alpha)
    ca, sa = np.cos(al), np.sin(al)

    def grid_best(a_lo, a_hi, b_lo, b_hi, st):
        a1 = np.arange(a_lo, a_hi + 1e-9, st)
        b1 = np.arange(max(b_lo, 0.0), b_hi + 1e-9, st)
        if a1.size < 2 or b1.size < 2:
            return None
        A, B = np.meshgrid(a1, b1)
        G = None
        Dmax = np.zeros_like(A)
        for k in range(al.size):
            s = A * ca[k] + B * sa[k]
            d_lo2 = A * A + B * B + r_lo ** 2 - 2 * r_lo * s
            d_hi2 = A * A + B * B + r_hi ** 2 - 2 * r_hi * s
            Dk = np.sqrt(np.maximum(d_lo2, d_hi2))
            Dmax = np.maximum(Dmax, Dk)
            n = np.abs(A * sa[k] - B * ca[k])
            r = np.where(Dk > 0, n / Dk, 0.0)
            G = r if G is None else np.minimum(G, r)
        G = np.where(Dmax <= R, G, -1.0)
        i = int(np.argmax(G))
        return (float(G.ravel()[i]), float(A.ravel()[i]), float(B.ravel()[i]))

    best = grid_best(a_lo, a_hi, b_lo, b_hi, step)
    if best is None:
        return None
    for radius, st in stages:
        g, a0, b0 = best
        cand = grid_best(a0 - radius, a0 + radius, b0 - radius, b0 + radius, st)
        if cand and cand[0] > g:
            best = cand
    if best is None or best[0] <= 0:
        return None
    return math.degrees(math.asin(min(best[0], 1.0))), best[1], best[2]


DDS = np.array([60.0, 120.0, 200.0, 300.0, 400.0, 500.0, 600.0, 680.0, 747.5, 800.0])
alpha0 = np.degrees(np.arccos(np.clip(DDS / R_WORST, -1, 1)))
with_alpha, pts = [], []
for d in DDS:
    r = max_guaranteed_alpha(d)
    if r is None:
        with_alpha.append(np.nan)
    else:
        with_alpha.append(r[0]); pts.append((d, r[0], r[1], r[2]))
        print("    Δd=%6.1f → φ=%7.4f°  at (a,b)=(%.1f, %.1f)" % (d, r[0], r[1], r[2]))
with_alpha = np.array(with_alpha)

fig, ax = plt.subplots(figsize=(7.8, 5.4))
ax.plot(DDS, alpha0, "-o", lw=2.0, ms=6, color="#1f77b4", label="α = 0（闭式  arccos(Δd/R)）")
ax.plot(DDS, with_alpha, "-s", lw=2.0, ms=6, color="#d62728",
        label="含 α ∈ [−1°, 1°]（数值搜索）")
ax.fill_between(DDS, with_alpha, alpha0, color="#d62728", alpha=0.14)
ax.axhline(PHI_MIN, ls="--", color="gray", lw=1.3)
ax.annotate("目标 φ_min = 40°", (830, 40.8), ha="right", fontsize=11, color="#555")
i = int(np.argmin(np.abs(DDS - D_DD)))
gap = alpha0[i] - with_alpha[i]
if not np.isnan(with_alpha[i]):
    ax.plot(D_DD, with_alpha[i], "o", ms=11, mfc="none", mec="#d62728", mew=2.6)
    ax.annotate(f"{with_alpha[i]:.4f}° @ Δd = 747.5 m\n（与 α=0 的 41.6257° 差 {gap:.4f}°）",
                (D_DD, with_alpha[i]), textcoords="offset points", xytext=(-215, -70), fontsize=11,
                color="#d62728",
                bbox=dict(boxstyle="round,pad=0.4", fc="#ffecec", ec="#d62728"))
ax.annotate("源距先验越准（Δd 越小）\nα=0 上界越高，但含 α 的保证\n增长慢得多 —— 两个独立缺口",
            (110, 66), fontsize=10.5,
            bbox=dict(boxstyle="round,pad=0.4", fc="#eaf3ff", ec="#1f77b4"))
ax.set_xlabel("源距不确定半宽 Δd（m）"); ax.set_ylabel("可保证交会角上界（°）")
ax.set_xlim(0, 860); ax.set_ylim(35, 92)
ax.set_title("图 5.2-8  定理 5.2-3：把示向度误差 α 一并最坏化后的可行性上界", fontsize=12.5)
ax.legend(fontsize=10.5, loc="lower left"); ax.grid(alpha=0.3)
save(fig, "fig5_2_8_theorem_523_bound.png", "图 5.2-8 定理 5.2-3 配套")

# ==================================================================
print("\n" + "=" * 72)
print("共 %d 张 → %s" % (len(FIG), OUT))
for n, c in FIG:
    print("  %-42s %s" % (n, c))
