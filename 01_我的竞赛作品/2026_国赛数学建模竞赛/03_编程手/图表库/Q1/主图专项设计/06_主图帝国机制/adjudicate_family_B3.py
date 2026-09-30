# -*- coding: utf-8 -*-
"""阶段三 第 4 部分: 族 B 中 gamma>1 的候选在高精度下是否成立 (排除浮点伪像)。"""
import math, itertools, random
import mpmath as mp
import q1_geometry_core as q
mp.mp.dps = 60

def halfplanes_hp(S, th, eps):
    out = []
    for sgn in (-1, 1):
        a = (th + sgn*eps)*mp.pi/180
        dx, dy = mp.cos(a), mp.sin(a)
        nx, ny = (dy, -dx) if sgn < 0 else (-dy, dx)
        out.append((nx, ny, nx*S[0] + ny*S[1]))
    return out

def vertices_hp(H, tol=mp.mpf("1e-40")):
    V = []
    for (n1x,n1y,c1), (n2x,n2y,c2) in itertools.combinations(H, 2):
        det = n1x*n2y - n1y*n2x
        if abs(det) < mp.mpf("1e-50"): continue
        X = ((c1*n2y - c2*n1y)/det, (n1x*c2 - n2x*c1)/det)
        if all(nx*X[0] + ny*X[1] <= c + tol for nx, ny, c in H):
            if not any(mp.sqrt((X[0]-Y[0])**2 + (X[1]-Y[1])**2) < mp.mpf("1e-25") for Y in V):
                V.append(X)
    return V

def mec_hp(P):
    def cover(c, r):
        t = r*mp.mpf("1e-30") + mp.mpf("1e-45")
        return all(mp.sqrt((p[0]-c[0])**2 + (p[1]-c[1])**2) <= r + t for p in P)
    best = None
    for a, b, c in itertools.combinations(P, 3):
        d = 2*(a[0]*(b[1]-c[1]) + b[0]*(c[1]-a[1]) + c[0]*(a[1]-b[1]))
        if abs(d) < mp.mpf("1e-50"): continue
        ux = ((a[0]**2+a[1]**2)*(b[1]-c[1]) + (b[0]**2+b[1]**2)*(c[1]-a[1]) + (c[0]**2+c[1]**2)*(a[1]-b[1]))/d
        uy = ((a[0]**2+a[1]**2)*(c[0]-b[0]) + (b[0]**2+b[1]**2)*(a[0]-c[0]) + (c[0]**2+c[1]**2)*(b[0]-a[0]))/d
        r = mp.sqrt((ux-a[0])**2 + (uy-a[1])**2)
        if cover((ux,uy), r) and (best is None or r < best[1]): best = ((ux,uy), r)
    for a, b in itertools.combinations(P, 2):
        cc = ((a[0]+b[0])/2, (a[1]+b[1])/2)
        r = mp.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)/2
        if cover(cc, r) and (best is None or r < best[1]): best = (cc, r)
    return best

def B_hp(phi, th1, th2, eps=1.0):
    S1 = (mp.mpf(0), mp.mpf(0))
    S2 = (mp.cos(mp.mpf(repr(phi))), mp.sin(mp.mpf(repr(phi))))
    H = halfplanes_hp(S1, mp.mpf(repr(th1)), mp.mpf(repr(eps))) + \
        halfplanes_hp(S2, mp.mpf(repr(th2)), mp.mpf(repr(eps)))
    V = vertices_hp(H)
    if len(V) < 3: return None
    D = max(mp.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2) for a, b in itertools.combinations(V, 2))
    if D < mp.mpf("1e-12"): return None
    m = mec_hp(V)
    if m is None: return None
    return dict(V=V, D=D, R=m[1], gamma=m[1]/(D/2), nv=len(V))

# 第 2 部分跑出的浮点 "最优" 候选
cand = (3.709424, 188.479129, 98.432269)
r = B_hp(*cand)
print("="*78)
print("候选 (浮点报告 gamma = 1.0005813) 的高精度复核")
print("="*78)
print("  phi=%.6f  th1=%.6f  th2=%.6f" % cand)
print("  顶点数 =", r["nv"])
print("  D     = %s" % mp.nstr(r["D"], 20))
print("  R_MEC = %s" % mp.nstr(r["R"], 20))
print("  gamma = %s" % mp.nstr(r["gamma"], 20))
print("  gamma - 1 = %s" % mp.nstr(r["gamma"] - 1, 8))
print("  >>> 该候选在高精度下 gamma %s 1" % (">" if r["gamma"] > 1 else "=" if r["gamma"] == 1 else "<"))

# 沿 phi 方向做一维高精度扫描, 看 gamma 能否真的超过 1
print()
print("="*78)
print("族 B: 固定 th1, th2, 高精度扫描 phi, 检验 max gamma")
print("="*78)
th1, th2 = 188.479129, 98.432269
gmax, phimax = mp.mpf(0), None
for k in range(201):
    phi = 2*math.pi*k/200.0
    try:
        rr = B_hp(phi, th1, th2)
    except Exception:
        continue
    if rr and rr["gamma"] > gmax:
        gmax, phimax = rr["gamma"], phi
print(f"  max gamma = {mp.nstr(gmax, 20)}   at phi = {phimax:.6f}")
print(f"  gamma - 1 = {mp.nstr(gmax-1, 8)}")

# 随机高精度扫描 (小样本, 因为高精度较慢)
print()
print("随机高精度扫描 400 例:")
random.seed(2026)
gmax2, arg2, viol = mp.mpf(0), None, 0
for _ in range(400):
    phi = random.uniform(0, 2*math.pi); a1 = random.uniform(0,360); a2 = random.uniform(0,360)
    try:
        rr = B_hp(phi, a1, a2)
    except Exception:
        continue
    if rr is None: continue
    if rr["gamma"] > 1 + mp.mpf("1e-30"):
        viol += 1
        if rr["gamma"] > gmax2: gmax2, arg2 = rr["gamma"], (phi, a1, a2)
print(f"  高精度下 gamma > 1 的实例数 = {viol} / 400")
if arg2:
    print(f"  最大 gamma = {mp.nstr(gmax2, 20)}  phi={arg2[0]:.6f} th1={arg2[1]:.6f} th2={arg2[2]:.6f}")
else:
    print("  未发现 gamma > 1 的实例")
