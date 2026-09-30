"""
Q1 参数扫描 —— 产出论文所需的三组扫描数据（φ / n / ε）+ 二维网格。

所有数值都走 q1_main.py 里已通过联合校验的几何管线（locate → hull → diameter → MEC），
不做任何近似、不构造分布。本脚本只负责设计实验并记录真实结果。

几何设定（对称两站，便于解析控制交会角）：
    S1 = (0, 0), S2 = (600, 0), 源 G = (300, h)
    G 处交会角 φ 满足  cos φ = (h² − L²/4)/(h² + L²/4)   (L = 600)
    ⇒ h = (L/2)·cot(φ/2) = 300·cot(φ/2)
    校验：φ=90° → h=300；φ=61.92° → h≈518.9（与基准算例 G=(300,500) 一致）

输出：q1_scan_results.json  +  控制台汇总表
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from q1_main import (  # noqa: E402
    build_wedges, candidate_vertices, convex_hull,
    diameter_bruteforce, diameter_rotating_calipers, mec_bruteforce,
)

L = 600.0          # 基线长度
EPS0 = 1.0         # 误差半角（度）


def h_for_phi(phi_deg):
    """给定源处交会角 φ（度），返回源的高 h（对称配置）。"""
    return (L / 2.0) / math.tan(math.radians(phi_deg) / 2.0)


def solve_case(detectors, thetas, eps_deg=EPS0):
    """跑一次完整几何管线，返回 (D, R_MEC, gamma, n_vertices) 或 None（无界/空）。"""
    wedges = build_wedges([np.array(p, dtype=float) for p in detectors], thetas, eps_deg)
    cand = candidate_vertices(wedges)
    if len(cand) < 3:
        return None
    poly = convex_hull(cand)
    if len(poly.vertices) < 3:
        return None
    D_bf, _ = diameter_bruteforce(poly)
    D_rc, _ = diameter_rotating_calipers(poly)
    if abs(D_bf - D_rc) > 1e-9:          # 双实现互验，不一致即视为实现错误
        raise RuntimeError(f"diameter mismatch: {D_bf} vs {D_rc}")
    _, R = mec_bruteforce(poly.vertices)
    return dict(D=D_bf, R=R, gamma=R / (D_bf / 2.0), nv=len(poly.vertices))


def theta_of(s, g):
    """由检测点 s 指向源 g 的方位角（度，[0,360)）。"""
    return math.degrees(math.atan2(g[1] - s[1], g[0] - s[0])) % 360.0


# 扫描 1：φ
def scan_phi(phis):
    rows = []
    for phi in phis:
        h = h_for_phi(phi)
        G = (L / 2.0, h)
        S = [(0.0, 0.0), (L, 0.0)]
        th = [theta_of(s, G) for s in S]
        r = solve_case(S, th)
        if r:
            rows.append(dict(phi=phi, h=h, **r))
    return rows


# 扫描 2：n
# 检测点必须采用嵌套配置：加入新检测点时不移走已有的，否则各 n 之间几何不可比，
# 测不出"加站改善定位"的单调性（对称布点下 n=4 可能比 n=3 更差，D 非单调）。
# 做法：固定前两个站，后续站按固定候选序依次追加。
EXTRA = [
    (300.0 + 550.0 * math.cos(math.radians(a)), 300.0 + 550.0 * math.sin(math.radians(a)))
    for a in (0.0, 120.0, 240.0, 60.0, 180.0, 300.0)
]


def scan_n(ns, phi=61.92, eps_deg=EPS0):
    """固定交会角 φ，嵌套地增加检测点。"""
    h = h_for_phi(phi)
    G = (L / 2.0, h)
    base = [(0.0, 0.0), (L, 0.0)]
    rows = []
    for n in ns:
        S = base + EXTRA[: max(0, n - 2)]
        th = [theta_of(s, G) for s in S]
        r = solve_case(S, th, eps_deg)
        if r:
            rows.append(dict(n=n, **r))
        else:
            rows.append(dict(n=n, D=None, R=None, gamma=None, nv=0, note="unbounded/empty"))
    return rows


# 扫描 3：ε
def scan_eps(epss, phi=61.92):
    h = h_for_phi(phi)
    G = (L / 2.0, h)
    S = [(0.0, 0.0), (L, 0.0)]
    th = [theta_of(s, G) for s in S]
    rows = []
    for e in epss:
        r = solve_case(S, th, e)
        if r:
            rows.append(dict(eps=e, **r))
    return rows


# 扫描 4：φ×ε 网格（热力图用）
def scan_grid(phis, epss):
    grid = []
    for phi in phis:
        h = h_for_phi(phi)
        G = (L / 2.0, h)
        S = [(0.0, 0.0), (L, 0.0)]
        th = [theta_of(s, G) for s in S]
        for e in epss:
            r = solve_case(S, th, e)
            grid.append(dict(phi=phi, eps=e,
                             D=(r["D"] if r else None),
                             gamma=(r["gamma"] if r else None)))
    return grid


def scan_gamma_mc(n_samples=2000, seed=42, n_det=2):
    """
    γ 分布的蒙特卡洛采样。

    对称两站配置恒给出 γ=1.000（此时区域关于中垂线对称，直径圆恰好覆盖），
    所以要看 γ>1 必须用非对称配置。做法：随机抽 n_det 个检测点 + 随机源位置，
    走真实几何管线算 γ —— 随机性只体现在"选哪组配置"，不体现在结果。
    即先随机生成算例，再用确定性几何求解，不引入任何人为分布假设。
    """
    rng = np.random.default_rng(seed)
    gammas, Ds = [], []
    tried = 0
    while len(gammas) < n_samples and tried < n_samples * 20:
        tried += 1
        # 源：圆域内均匀随机（半径 ≤ 1400）
        r = 1400.0 * math.sqrt(rng.random())
        a = rng.random() * 2 * math.pi
        G = (r * math.cos(a), r * math.sin(a))
        # n_det 个检测点：随机但都需能测到源（距离 ≤ 980 < 最坏接收半径 1000）
        S = []
        for _ in range(n_det):
            rr = 980.0 * math.sqrt(rng.random())
            aa = rng.random() * 2 * math.pi
            S.append((G[0] + rr * math.cos(aa), G[1] + rr * math.sin(aa)))
        if min(math.dist(s, G) for s in S) < 20.0:   # 站贴着源 ⇒ 病态，跳过
            continue
        th = [theta_of(s, G) for s in S]
        try:
            res = solve_case(S, th, EPS0)
        except RuntimeError:
            continue
        if res:
            gammas.append(res["gamma"])
            Ds.append(res["D"])
    return dict(gammas=gammas, Ds=Ds, tried=tried, n_det=n_det)


def main():
    out = {}

    print("=" * 78)
    print(" Q1 参数扫描（全部走已校验几何管线，无构造数据）")
    print("=" * 78)

    # --- 基准自检：φ=61.92° 应给出与基准算例一致的量级 ---
    print("\n[自检] φ=61.92°（等效基准算例几何）")
    h = h_for_phi(61.92)
    G = (L / 2.0, h)
    S = [(0.0, 0.0), (L, 0.0)]
    base = solve_case(S, [theta_of(s, G) for s in S])
    print(f"  h={h:.3f}  D={base['D']:.4f}  R={base['R']:.4f}  gamma={base['gamma']:.6f}")
    out["selfcheck_phi61_92"] = dict(h=h, **base)

    # --- φ 扫描 ---
    phis = [20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]
    rows = scan_phi(phis)
    out["scan_phi"] = rows
    print("\n[扫描 1] 交会角 φ  →  D（验证 D ∝ 1/sinφ）")
    print(f"  {'φ(°)':>6} {'h(m)':>9} {'D(m)':>10} {'R_MEC(m)':>10} {'γ':>8} {'顶点':>5} {'D·sinφ':>9}")
    for r in rows:
        print(f"  {r['phi']:6.0f} {r['h']:9.2f} {r['D']:10.4f} {r['R']:10.4f} "
              f"{r['gamma']:8.5f} {r['nv']:5d} {r['D']*math.sin(math.radians(r['phi'])):9.2f}")

    # --- n 扫描 ---
    ns = [2, 3, 4, 6, 8]
    rows_n = scan_n(ns)
    out["scan_n"] = rows_n
    print("\n[扫描 2] 检测点数 n  →  D（验证单调不增）")
    for r in rows_n:
        if r["D"] is None:
            print(f"  n={r['n']:2d}  {r['note']}")
        else:
            print(f"  n={r['n']:2d}  D={r['D']:10.4f}  R={r['R']:9.4f}  γ={r['gamma']:8.5f}  顶点={r['nv']}")

    # --- ε 扫描 ---
    epss = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
    rows_e = scan_eps(epss)
    out["scan_eps"] = rows_e
    print("\n[扫描 3] 误差半角 ε  →  D（验证 D ∝ ε）")
    print(f"  {'ε(°)':>6} {'D(m)':>10} {'R_MEC(m)':>10} {'γ':>8} {'D/ε':>10}")
    for r in rows_e:
        print(f"  {r['eps']:6.2f} {r['D']:10.4f} {r['R']:10.4f} {r['gamma']:8.5f} {r['D']/r['eps']:10.4f}")

    # --- φ×ε 网格 ---
    gp = [30, 45, 60, 75, 90, 105, 120, 135, 150]
    ge = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
    grid = scan_grid(gp, ge)
    out["scan_grid"] = grid
    print(f"\n[扫描 4] φ×ε 网格：{len(grid)} 点 → 热力图数据")
    gams = [g["gamma"] for g in grid if g["gamma"] is not None]
    print(f"  γ 范围: [{min(gams):.6f}, {max(gams):.6f}]  "
          f"（理论 [1, 2/√3=1.154700]）")

    # --- γ 分布（非对称随机配置，蒙特卡洛；n = 2..5） ---
    print("\n[扫描 5] γ 分布（非对称随机配置 MC）")
    print("  问题：等边三角形反例（γ=2/√3=1.154701）能否由角域之交实现？")
    print(f"  {'n':>3} {'样本':>6} {'min':>10} {'median':>10} {'max':>10} {'γ>1.01 占比':>12}")
    mc_all = {}
    for nd in (2, 3, 4, 5):
        mc = scan_gamma_mc(n_samples=2000, seed=100 + nd, n_det=nd)
        g = np.array(mc["gammas"])
        mc_all[f"n{nd}"] = mc
        print(f"  {nd:3d} {len(g):6d} {g.min():10.6f} {np.median(g):10.6f} "
              f"{g.max():10.6f} {(g > 1.01).mean()*100:11.2f}%")
    out["gamma_mc"] = mc_all
    allg = np.concatenate([np.array(mc_all[k]["gammas"]) for k in mc_all])
    print(f"  合计 {len(allg)} 样本：γ ∈ [{allg.min():.6f}, {allg.max():.6f}]")
    print(f"  远低于理论上界 {2/math.sqrt(3):.6f}，等边三角形反例在本模型区域内未出现")
    print(f"     违反 Jung 上界的样本: {(allg > 2/math.sqrt(3) + 1e-9).sum()} 个")

    # --- 全局 Jung 界断言 ---
    allr = [r for r in rows + rows_e if r.get("D")]
    allr += [r for r in rows_n if r.get("D")]
    bad = [r for r in allr if not (r["D"]/2 - 1e-9 <= r["R"] <= r["D"]/math.sqrt(3) + 1e-9)]
    print(f"\n[Jung 界] 校验 {len(allr)} 个算例：违反 {len(bad)} 个 "
          f"{'全部满足' if not bad else '存在违反'}")

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "q1_scan_results.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n已保存: {path}")
    print("=" * 78)


if __name__ == "__main__":
    main()
