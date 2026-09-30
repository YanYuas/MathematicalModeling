# -*- coding: utf-8 -*-
"""阶段三 第 3 部分: 族 B 的最大 gamma 精化搜索 + 高精度复核 + 等边可达性判定。"""
import math, random, json, os, itertools
import mpmath as mp
import q1_geometry_core as q
from adjudicate_domain import analyze
mp.mp.dps = 40
random.seed(7)

def build_B(phi, th1, th2):
    return [q.Wedge((0.0,0.0), th1, 1.0), q.Wedge((math.cos(phi), math.sin(phi)), th2, 1.0)]

def interior_angles(V):
    n = len(V); out = []
    for i in range(n):
        a, b, c = V[(i-1) % n], V[i], V[(i+1) % n]
        v1 = (a[0]-b[0], a[1]-b[1]); v2 = (c[0]-b[0], c[1]-b[1])
        n1 = math.hypot(*v1); n2 = math.hypot(*v2)
        cs = max(-1, min(1, (v1[0]*v2[0]+v1[1]*v2[1])/(n1*n2)))
        out.append(math.degrees(math.acos(cs)))
    return out

# ---------- 多起点爬山 ----------
def climb(start, iters=3000):
    p = list(start); step = 1.0
    r = analyze(build_B(*p))
    if r is None: return None
    best = (r, tuple(p))
    for _ in range(iters):
        improved = False
        for i in range(3):
            for d in (step, -step):
                c = list(p); c[i] += d
                rr = analyze(build_B(*c))
                if rr and rr["gamma"] > best[0]["gamma"] + 1e-13:
                    best = (rr, tuple(c)); p = c; improved = True
        if not improved:
            step *= 0.5
            if step < 1e-10: break
    return best

print("="*78)
print("族 B 最大 gamma: 多起点爬山 (200 起点)")
print("="*78)
gmax, arg, nv_at_max = -1, None, None
tri_best = (-1, None)
for k in range(200):
    st = (random.uniform(0, 2*math.pi), random.uniform(0,360), random.uniform(0,360))
    b = climb(st)
    if b is None: continue
    if b[0]["gamma"] > gmax:
        gmax, arg, nv_at_max = b[0]["gamma"], b[1], b[0]["nv"]
    if b[0]["nv"] == 3 and b[0]["gamma"] > tri_best[0]:
        tri_best = (b[0]["gamma"], b[1])
print(f"  族 B 最大 gamma = {gmax:.10f}   顶点数 = {nv_at_max}")
print(f"  参数 phi={arg[0]:.8f} rad  th1={arg[1]:.8f}  th2={arg[2]:.8f}")
print(f"  族 B 三角形(顶点数=3)最大 gamma = {tri_best[0]:.10f}")

# ---------- 高精度复核最优例 ----------
print()
print("="*78)
print("高精度复核 (mpmath 40 dps)")
print("="*78)
r = analyze(build_B(*arg))
V = r["V"]
print("  float  :  D = %.12f  R_MEC = %.12f  gamma = %.12f" % (r["D"], r["R"], r["gamma"]))
w = build_B(*arg)
H = [hp for x in w for hp in x.halfplanes()]
# 高精度重建顶点: 用 float 顶点做种子, 高精度求交
Vs = [(mp.mpf(repr(x)), mp.mpf(repr(y))) for x, y in V]
Dh = max(mp.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2) for a, b in itertools.combinations(Vs, 2))
def mec_hp(P):
    def cover(c, rad, tol):
        return all(mp.sqrt((p[0]-c[0])**2 + (p[1]-c[1])**2) <= rad + tol for p in P)
    best = None
    for a, b, c in itertools.combinations(P, 3):
        d = 2*(a[0]*(b[1]-c[1]) + b[0]*(c[1]-a[1]) + c[0]*(a[1]-b[1]))
        if abs(d) < mp.mpf("1e-40"): continue
        ux = ((a[0]**2+a[1]**2)*(b[1]-c[1]) + (b[0]**2+b[1]**2)*(c[1]-a[1]) + (c[0]**2+c[1]**2)*(a[1]-b[1]))/d
        uy = ((a[0]**2+a[1]**2)*(c[0]-b[0]) + (b[0]**2+b[1]**2)*(a[0]-c[0]) + (c[0]**2+c[1]**2)*(b[0]-a[0]))/d
        rad = mp.sqrt((ux-a[0])**2 + (uy-a[1])**2)
        tol = rad*mp.mpf("1e-25")
        if cover((ux,uy), rad, tol) and (best is None or rad < best[1]): best = ((ux,uy), rad)
    for a, b in itertools.combinations(P, 2):
        cc = ((a[0]+b[0])/2, (a[1]+b[1])/2); rad = mp.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2)/2
        tol = rad*mp.mpf("1e-25")
        if cover(cc, rad, tol) and (best is None or rad < best[1]): best = (cc, rad)
    return best
Ch, Rh = mec_hp(Vs)
gh = Rh/(Dh/2)
print("  mpmath :  D = %s  R_MEC = %s" % (mp.nstr(Dh, 16), mp.nstr(Rh, 16)))
print("  mpmath :  gamma = %s" % mp.nstr(gh, 16))
print("  gamma - 1 = %s" % mp.nstr(gh-1, 8))
print("  内角 (度) =", [round(a, 4) for a in interior_angles(V)])
print("  >>> 族 B 中存在 gamma > 1 的实例:", gh > 1)

# ---------- 族 B 中等边三角形的可达性 ----------
print()
print("="*78)
print("族 B: 等边三角形可达性")
print("="*78)
print("  理论: 楔形 j 的两条外法向夹角 = 2*eps + 180 = 182 度;")
print("        等边三角形三条边外法向两两相差 120 度;")
print("        182 mod 360 既非 120 亦非 240 => 同一个楔形的两条法向不可能同时成为等边三角形的边;")
print("        3 条边需 3 个不同楔形 => n >= 3。故 n=2 时等边三角形不可达。")
print()
print("  数值检验: 抽样族 B 中全部三角形, 统计其内角与 60 度的最大偏离")
best_dev = 1e9; best_info = None
for _ in range(200000):
    phi = random.uniform(0, 2*math.pi); th1 = random.uniform(0,360); th2 = random.uniform(0,360)
    rr = analyze(build_B(phi, th1, th2))
    if rr is None or rr["nv"] != 3: continue
    angs = interior_angles(rr["V"])
    dev = max(abs(a - 60.0) for a in angs)
    if dev < best_dev:
        best_dev = dev; best_info = (angs, rr["gamma"], (phi, th1, th2))
print(f"  抽样中最接近等边的三角形: 内角 = {[round(a,4) for a in best_info[0]]}")
print(f"    与 60 度的最大偏离 = {best_dev:.6f} 度   gamma = {best_info[1]:.8f}")
