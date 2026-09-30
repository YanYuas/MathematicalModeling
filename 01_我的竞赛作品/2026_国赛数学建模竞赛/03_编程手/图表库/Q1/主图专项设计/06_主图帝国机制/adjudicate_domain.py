# -*- coding: utf-8 -*-
"""阶段三: 等边反例的定义域裁决 —— 族 A / B / C 的构造与反例搜索。

族 A: 任意有界凸多边形
族 B: 两个同半角前向角域的非空有界交集
族 C: 任意 n>=2 个同半角前向角域的非空有界交集
"""
import math, random, itertools, json, os
import q1_geometry_core as q

R3 = math.sqrt(3)

def analyze(wedges, tol=1e-7):
    H = [hp for w in wedges for hp in w.halfplanes()]
    bnd, gap = q.is_bounded(H)
    raw = q.intersect_halfplanes(H, tol)
    if not bnd or len(raw) < 3:
        return None
    V = q.order_ccw(raw)
    if len(V) < 3:
        return None
    area = abs(sum(V[i][0]*V[(i+1) % len(V)][1] - V[(i+1) % len(V)][0]*V[i][1]
                   for i in range(len(V))))/2.0
    if area < 1e-14:
        return None
    D, ends = q.diameter(V)
    if D < 1e-12:
        return None
    C, R = q.mec(V)
    ok, minang = q.diameter_circle_covers(V, *ends)
    return dict(V=V, D=D, ends=ends, C=C, R=R, gamma=R/(D/2),
                covers=ok, minang=minang, area=area, nv=len(V))

def ang_of(v):
    return math.degrees(math.atan2(v[1], v[0]))


# =====================================================================
print("="*78)
print("族 C: 等边三角形的显式构造 (n = 3, 同半角 eps = 1 deg)")
print("="*78)

def equilateral_in_C(back=30.0, side=1.0):
    """每个站放在某条边的延长线上、距该边起点 back 处;
    楔形的一条边界射线与该边共线, 另一条朝三角形内部旋转 2*eps = 2 度。"""
    T = [(0.0, 0.0), (side, 0.0), (side/2.0, side*R3/2.0)]
    ws = []
    for i in range(3):
        P, Q = T[i], T[(i+1) % 3]
        dx, dy = Q[0]-P[0], Q[1]-P[1]
        L = math.hypot(dx, dy)
        ux, uy = dx/L, dy/L
        S = (P[0] - back*ux, P[1] - back*uy)
        th = ang_of((ux, uy)) + 1.0          # 射线方向 = 边长方向 and +2 度
        ws.append(q.Wedge(S, th, 1.0))
    return ws, T

T = [(0.0, 0.0), (1.0, 0.0), (0.5, R3/2.0)]
for back in (22.0, 24.0, 24.3, 24.5, 25.0, 30.0, 60.0):
    ws, _ = equilateral_in_C(back=back)
    r = analyze(ws)
    if r is None:
        print(f"  back={back:>6.1f}  -> 交集非有界/退化"); continue
    # 与目标等边三角形逐点比对
    err = max(min(math.dist(v, t) for t in T) for v in r["V"])
    print(f"  back={back:>6.1f}  顶点数={r[chr(110)+chr(118)]}  D={r[chr(68)]:.6f}  R_MEC={r[chr(82)]:.6f}"
          f"  gamma={r[chr(103)+chr(97)+chr(109)+chr(109)+chr(97)]:.6f}  覆盖={r[chr(99)+chr(111)+chr(118)+chr(101)+chr(114)+chr(115)]}"
          f"  与等边三角形顶点的最大偏差={err:.2e}")

print()
ws, _ = equilateral_in_C(back=30.0)
r = analyze(ws)
print("  站坐标与指向 (back=30):")
for i, w in enumerate(ws):
    print(f"    S{i+1} = ({w.S[0]:.4f}, {w.S[1]:.4f})   theta{i+1} = {w.theta:.4f} deg"
          f"   两条边界射线方向 = {w.theta-1:.4f}, {w.theta+1:.4f}")
print(f"  交集顶点: {[tuple(round(c,6) for c in v) for v in r[chr(86)]]}")
print(f"  目标等边三角形: {[tuple(round(c,6) for c in t) for t in T]}")
print(f"  D = {r[chr(68)]:.10f}  (应为 1)")
print(f"  R_MEC = {r[chr(82)]:.10f}  (应为 1/sqrt(3) = {1/R3:.10f})")
print(f"  gamma = {r[chr(103)+chr(97)+chr(109)+chr(109)+chr(97)]:.10f}  (应为 2/sqrt(3) = {2/R3:.10f})")
print(f"  直径圆覆盖 = {r[chr(99)+chr(111)+chr(118)+chr(101)+chr(114)+chr(115)]}  (应为 False)")
print("  >>> 结论: 等边三角形在族 C (n=3, 同半角) 中可达, 故 gamma = 2/sqrt(3) > 1 在族 C 中可达。")
