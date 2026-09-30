# -*- coding: utf-8 -*-
"""q1_geometry_core —— 问题一主图的"计算证据底座"（与版式无关）。

任何胜出方案都必须通过本模块的对象与断言，禁止在绘图脚本里硬编码几何数值。
全部对象由定义实时算出。

约定
----
角域:  W_i = { S_i + t*u(phi) : t >= 0, |phi-theta_i| <= eps },  u(phi)=(cos phi, sin phi)
半平面表示(用于求交):  W_i = { x : n1.(x-S_i) <= 0, n2.(x-S_i) <= 0 }
    d1 = u(theta-eps),  d2 = u(theta+eps)
    n1 = ( d1_y, -d1_x )    # d1 顺时针转 90 度, 为沿 d1 那条边的外法向
    n2 = ( -d2_y, d2_x )    # d2 逆时针转 90 度, 为沿 d2 那条边的外法向
"""
from __future__ import annotations
import itertools, math, json, os
from dataclasses import dataclass, field

EPS_TOL = 1e-9
RAD = math.pi / 180.0


# ---------------------------------------------------------------- 基础
def u(phi_deg: float) -> tuple[float, float]:
    p = phi_deg * RAD
    return (math.cos(p), math.sin(p))


@dataclass(frozen=True)
class Wedge:
    """一个带误差的示向度角域。"""
    S: tuple[float, float]
    theta: float          # 度
    eps: float = 1.0      # 度

    def halfplanes(self):
        """返回 [(nx, ny, c)] 表示 n.(x) <= c。"""
        out = []
        for sgn in (-1.0, +1.0):
            dx, dy = u(self.theta + sgn * self.eps)
            if sgn < 0:                      # 沿 d1 的边, 外法向 n1
                nx, ny = dy, -dx
            else:                            # 沿 d2 的边, 外法向 n2
                nx, ny = -dy, dx
            out.append((nx, ny, nx * self.S[0] + ny * self.S[1]))
        return out

    def contains(self, P, tol=1e-7):
        vx, vy = P[0] - self.S[0], P[1] - self.S[1]
        if math.hypot(vx, vy) < tol:
            return True
        ang = math.degrees(math.atan2(vy, vx))
        d = (ang - self.theta + 180.0) % 360.0 - 180.0
        return abs(d) <= self.eps + tol

    def boundary_rays(self):
        """两条边界射线的 (原点, 单位方向)。"""
        return [(self.S, u(self.theta - self.eps)), (self.S, u(self.theta + self.eps))]

    def fan_polygon(self, r, n=24):
        """用于绘制扇形的折线（r 为画到多远的截断半径）。"""
        pts = [self.S]
        for k in range(n + 1):
            phi = self.theta - self.eps + (2 * self.eps) * k / n
            dx, dy = u(phi)
            pts.append((self.S[0] + r * dx, self.S[1] + r * dy))
        pts.append(self.S)
        return pts


# ---------------------------------------------------------------- 凸区域
def _line_intersect(h1, h2):
    n1x, n1y, c1 = h1
    n2x, n2y, c2 = h2
    det = n1x * n2y - n1y * n2x
    if abs(det) < 1e-14:
        return None
    return ((c1 * n2y - c2 * n1y) / det, (n1x * c2 - n2x * c1) / det)


def _feasible(P, H, tol=1e-7):
    return all(nx * P[0] + ny * P[1] <= c + tol for nx, ny, c in H)


def intersect_halfplanes(H, tol=1e-7):
    """半平面交的顶点集（无序，去重）。凸、可能为空。"""
    V = []
    for h1, h2 in itertools.combinations(H, 2):
        P = _line_intersect(h1, h2)
        if P is None or not _feasible(P, H, tol):
            continue
        if not any(math.dist(P, Q) < 1e-7 for Q in V):
            V.append(P)
    return V


def order_ccw(V):
    """按质心极角排序，得到凸多边形顶点序。"""
    if len(V) < 3:
        return list(V)
    cx = sum(p[0] for p in V) / len(V)
    cy = sum(p[1] for p in V) / len(V)
    return sorted(V, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))


def is_bounded(H):
    """L 有界 <=> 外法向不被任何闭半平面包含 <=> 法向角排序后最大相邻间隔 <= 180。"""
    angs = sorted(math.degrees(math.atan2(ny, nx)) % 360.0 for nx, ny, _ in H)
    gaps = [(angs[(i + 1) % len(angs)] - angs[i]) % 360.0 for i in range(len(angs))]
    mx = max(gaps) if gaps else 0.0
    return mx <= 180.0 + 1e-9, mx


def locate(wedges, tol=1e-7):
    """由角域族求 L。返回 dict。"""
    H = [hp for w in wedges for hp in w.halfplanes()]
    raw = intersect_halfplanes(H, tol)
    V = order_ccw(raw)
    bnd, gap = is_bounded(H)
    return {"halfplanes": H, "vertices": V, "bounded": bnd, "normal_gap_deg": gap}


# ---------------------------------------------------------------- 度量
def diameter(V):
    """凸多边形直径：只需检查顶点对。"""
    best, pr = 0.0, None
    for a, b in itertools.combinations(V, 2):
        d = math.dist(a, b)
        if d > best:
            best, pr = d, (a, b)
    return best, pr


def mec(V):
    """最小覆盖圆：穷举 1/2/3 点支撑集（Welzl 的等价穷举形式）。"""
    P = [(float(x), float(y)) for x, y in V]
    if not P:
        raise ValueError("空点集")
    best = None

    def cover(c, r):
        return all(math.dist(p, c) <= r + 1e-9 for p in P)

    for a, b, c in itertools.combinations(P, 3):
        d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
        if abs(d) < 1e-12:
            continue
        ux = ((a[0]**2 + a[1]**2) * (b[1] - c[1]) + (b[0]**2 + b[1]**2) * (c[1] - a[1])
              + (c[0]**2 + c[1]**2) * (a[1] - b[1])) / d
        uy = ((a[0]**2 + a[1]**2) * (c[0] - b[0]) + (b[0]**2 + b[1]**2) * (a[0] - c[0])
              + (c[0]**2 + c[1]**2) * (b[0] - a[0])) / d
        r = math.dist((ux, uy), a)
        if cover((ux, uy), r) and (best is None or r < best[1] - 1e-12):
            best = ((ux, uy), r)
    for a, b in itertools.combinations(P, 2):
        cc = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        r = math.dist(a, b) / 2
        if cover(cc, r) and (best is None or r < best[1] - 1e-12):
            best = (cc, r)
    if best is None:
        best = (P[0], 0.0)
    return best


def thales_angles(V, P, Q):
    """L 的每个顶点 X 处的 ∠PXQ（度）。直径端点自身退化，按 None 跳过。"""
    out = []
    for i, X in enumerate(V):
        v1 = (P[0] - X[0], P[1] - X[1])
        v2 = (Q[0] - X[0], Q[1] - X[1])
        n1, n2 = math.hypot(*v1), math.hypot(*v2)
        if n1 < 1e-9 or n2 < 1e-9:
            out.append((i, None))
            continue
        cs = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
        out.append((i, math.degrees(math.acos(cs))))
    return out


def diameter_circle_covers(V, P, Q, tol=1e-9):
    """Thales 判据：直径圆覆盖 L <=> 所有顶点 ∠PXQ >= 90°。"""
    angs = [a for _, a in thales_angles(V, P, Q) if a is not None]
    return (min(angs) >= 90.0 - tol), (min(angs) if angs else None)


# ---------------------------------------------------------------- 标准对象
def baseline():
    """两站基准算例（特例验证用）。"""
    S1, S2, G = (0.0, 0.0), (600.0, 0.0), (300.0, 500.0)
    th1 = math.degrees(math.atan2(G[1] - S1[1], G[0] - S1[0]))
    th2 = math.degrees(math.atan2(G[1] - S2[1], G[0] - S2[0]))
    ws = [Wedge(S1, th1, 1.0), Wedge(S2, th2, 1.0)]
    L = locate(ws)
    V = L["vertices"]
    D, ends = diameter(V)
    C, R = mec(V)
    ok, minang = diameter_circle_covers(V, *ends)
    return {"wedges": ws, "S1": S1, "S2": S2, "G": G, "theta1": th1, "theta2": th2,
            "L": L, "V": V, "D": D, "ends": ends, "C": C, "R_MEC": R,
            "covers": ok, "min_angle": minang,
            "gamma": R / (D / 2), "jung_lo": D / 2, "jung_hi": D / math.sqrt(3)}


def equilateral(side=1.0):
    """等边三角形反例（真实计算，不得以示意代替）。"""
    T = [(0.0, 0.0), (side, 0.0), (side / 2, side * math.sqrt(3) / 2)]
    V = order_ccw(T)
    D, ends = diameter(V)
    C, R = mec(V)
    ok, minang = diameter_circle_covers(V, *ends)
    return {"V": V, "D": D, "ends": ends, "C": C, "R_MEC": R,
            "covers": ok, "min_angle": minang,
            "jung_lo": D / 2, "jung_hi": D / math.sqrt(3),
            "gamma": R / (D / 2)}


def near_equilateral(deg=8.0):
    """接近等边的三角形族：展示 gamma 从 1 连续走到 1/sqrt(3)*... 的过渡（可选可视化）。"""
    a = 1.0
    apex = 60.0 + deg           # (0,0) 处的顶角
    ang = math.radians(apex)
    T = [(0.0, 0.0), (a, 0.0), (a * math.cos(ang), a * math.sin(ang))]
    V = order_ccw(T)
    D, ends = diameter(V)
    C, R = mec(V)
    ok, minang = diameter_circle_covers(V, *ends)
    return {"apex_deg": apex, "V": V, "D": D, "R_MEC": R, "gamma": R / (D / 2),
            "jung_lo": D / 2, "jung_hi": D / math.sqrt(3),
            "covers": ok, "min_angle": minang}


# ---------------------------------------------------------------- 断言
def run_assertions():
    F = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_facts.json"),
                       encoding="utf-8"))
    b = baseline()
    e = equilateral(1.0)
    checks = []

    def ck(name, cond, got=None, want=None, tol=None):
        checks.append({"assert": name, "pass": bool(cond),
                       **({"got": got} if got is not None else {}),
                       **({"want": want} if want is not None else {})})

    ck("L 为四边形 (4 顶点)", len(b["V"]) == 4, len(b["V"]), 4)
    ck("L 有界", b["L"]["bounded"], b["L"]["normal_gap_deg"], "<=180")
    exp = {"P1": (288.1342, 499.7929), "P2": (300.0, 480.7768),
           "P3": (311.8658, 499.7929), "P4": (300.0, 520.3752)}
    for i, (k, want) in enumerate(exp.items()):
        got = b["V"][i]
        ck(f"{k} 坐标 4 位小数一致",
           round(got[0], 4) == want[0] and round(got[1], 4) == want[1], [round(got[0],4), round(got[1],4)], list(want))
    ck("D == 39.5983", round(b["D"], 4) == 39.5983, round(b["D"], 4), 39.5983)
    ck("直径端点为 P2/P4",
       all(any(math.dist(p, q) < 1e-6 for q in (b["V"][1], b["V"][3])) for p in b["ends"]))
    ck("R_MEC == 19.7992", round(b["R_MEC"], 4) == 19.7992, round(b["R_MEC"], 4), 19.7992)
    ck("C* == (300, 500.5760)",
       round(b["C"][0], 4) == 300.0 and round(b["C"][1], 4) == 500.5760, [round(x,4) for x in b["C"]])
    ck("gamma == 1.0000 (本例)", abs(b["gamma"] - 1.0) < 1e-6, round(b["gamma"], 6))
    ck("本例被直径圆覆盖 (Thales)", b["covers"] and b["min_angle"] >= 90.0, round(b["min_angle"], 4))
    ck("每个顶点同时属于两个角域",
       all(all(w.contains(P) for w in b["wedges"]) for P in b["V"]))
    ck("Jung 夹逼成立 D/2 <= R_MEC <= D/sqrt(3)",
       b["jung_lo"] - 1e-9 <= b["R_MEC"] <= b["jung_hi"] + 1e-9,
       [round(b["jung_lo"],4), round(b["R_MEC"],4), round(b["jung_hi"],4)])
    ck("等边三角形: R_MEC == D/sqrt(3)", abs(e["R_MEC"] - e["jung_hi"]) < 1e-9, e["R_MEC"], e["jung_hi"])
    ck("等边三角形: 直径圆不覆盖 (反例成立)", (not e["covers"]) and e["min_angle"] < 90.0, round(e["min_angle"], 4))
    ck("等边三角形: gamma > 1", e["gamma"] > 1.0 + 1e-9, round(e["gamma"], 6))
    ck("与 verify_facts.json 口径一致 (D)", round(b["D"], 4) == F["diameter"]["D"])
    ck("与 verify_facts.json 口径一致 (R_MEC)", round(b["R_MEC"], 4) == F["mec"]["R_MEC"])

    npass = sum(1 for c in checks if c["pass"])
    return {"checks": checks, "n_pass": npass, "n_total": len(checks), "all_pass": npass == len(checks)}


if __name__ == "__main__":
    import sys
    r = run_assertions()
    for c in r["checks"]:
        print(("  PASS " if c["pass"] else "  FAIL ") + c["assert"],
              "" if c["pass"] else f"  got={c.get('got')} want={c.get('want')}")
    print(f"\n[contract] {r['n_pass']}/{r['n_total']} assertions passed; all_pass={r['all_pass']}")
    json.dump(r, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "geometry_core_contract.json"),
                      "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    sys.exit(0 if r["all_pass"] else 1)
