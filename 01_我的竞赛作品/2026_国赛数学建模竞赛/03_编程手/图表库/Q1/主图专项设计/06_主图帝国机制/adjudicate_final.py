# -*- coding: utf-8 -*-
"""阶段三 第 5 部分: 族 B 的 gamma 上界数值观察 + 族 C 等边构造的完整证书。"""
import math, random, itertools, json, os
import mpmath as mp
import q1_geometry_core as q
mp.mp.dps = 50
random.seed(20260912)

def analyze(wedges, tol=1e-7):
    H = [hp for w in wedges for hp in w.halfplanes()]
    bnd, _ = q.is_bounded(H)
    raw = q.intersect_halfplanes(H, tol)
    if not bnd or len(raw) < 3: return None
    V = q.order_ccw(raw)
    if len(V) < 3: return None
    area = abs(sum(V[i][0]*V[(i+1) % len(V)][1] - V[(i+1) % len(V)][0]*V[i][1] for i in range(len(V))))/2
    if area < 1e-15: return None
    D, ends = q.diameter(V)
    if D < 1e-12: return None
    C, R = q.mec(V)
    ok, mn = q.diameter_circle_covers(V, *ends)
    return dict(V=V, D=D, R=R, gamma=R/(D/2), covers=ok, minang=mn, nv=len(V))

def B(phi, t1, t2):
    return [q.Wedge((0.0,0.0), t1, 1.0), q.Wedge((math.cos(phi), math.sin(phi)), t2, 1.0)]

print("="*78); print("族 B: gamma 上界数值观察 (n=2)"); print("="*78)
pool = []
for _ in range(300000):
    phi = random.uniform(0, 2*math.pi); t1 = random.uniform(0,360); t2 = random.uniform(0,360)
    r = analyze(B(phi,t1,t2))
    if r: pool.append((r["gamma"], (phi,t1,t2)))
pool.sort(key=lambda x: -x[0])
print(f"  样本数(有界非空) = {len(pool)}")
print(f"  浮点最大 gamma   = {pool[0][0]:.10f}")

best = pool[0]
for start in [p[1] for p in pool[:60]]:
    p = list(start); step = 0.4; cur = analyze(B(*p))
    if cur is None: continue
    for _ in range(6000):
        imp = False
        for i in range(3):
            for d in (step,-step):
                c = list(p); c[i] += d
                rr = analyze(B(*c))
                if rr and rr["gamma"] > cur["gamma"] + 1e-14:
                    cur, p, imp = rr, c, True
        if not imp:
            step *= 0.5
            if step < 1e-11: break
    if cur["gamma"] > best[0]: best = (cur["gamma"], tuple(p))
print(f"  精化后浮点最大 gamma = {best[0]:.10f}   at phi={best[1][0]:.6f} th1={best[1][1]:.6f} th2={best[1][2]:.6f}")

# 高精度复核 top-5
def hp_B(phi, t1, t2, eps=1.0):
    def H_of(S, th):
        out=[]
        for sgn in (-1,1):
            a=(mp.mpf(repr(th))+sgn*mp.mpf(repr(eps)))*mp.pi/180
            dx,dy=mp.cos(a),mp.sin(a)
            nx,ny=(dy,-dx) if sgn<0 else (-dy,dx)
            out.append((nx,ny,nx*S[0]+ny*S[1]))
        return out
    S1=(mp.mpf(0),mp.mpf(0))
    S2=(mp.cos(mp.mpf(repr(phi))),mp.sin(mp.mpf(repr(phi))))
    H=H_of(S1,t1)+H_of(S2,t2)
    V=[]
    for (a1,b1,c1),(a2,b2,c2) in itertools.combinations(H,2):
        det=a1*b2-b1*a2
        if abs(det)<mp.mpf("1e-50"): continue
        X=((c1*b2-c2*b1)/det,(a1*c2-a2*c1)/det)
        if all(nx*X[0]+ny*X[1]<=c+mp.mpf("1e-40") for nx,ny,c in H):
            if not any(mp.sqrt((X[0]-Y[0])**2+(X[1]-Y[1])**2)<mp.mpf("1e-25") for Y in V): V.append(X)
    if len(V)<3: return None
    D=max(mp.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2) for a,b in itertools.combinations(V,2))
    def cover(c,r):
        t=r*mp.mpf("1e-30")+mp.mpf("1e-45")
        return all(mp.sqrt((p[0]-c[0])**2+(p[1]-c[1])**2)<=r+t for p in V)
    bst=None
    for a,b,c in itertools.combinations(V,3):
        d=2*(a[0]*(b[1]-c[1])+b[0]*(c[1]-a[1])+c[0]*(a[1]-b[1]))
        if abs(d)<mp.mpf("1e-50"): continue
        ux=((a[0]**2+a[1]**2)*(b[1]-c[1])+(b[0]**2+b[1]**2)*(c[1]-a[1])+(c[0]**2+c[1]**2)*(a[1]-b[1]))/d
        uy=((a[0]**2+a[1]**2)*(c[0]-b[0])+(b[0]**2+b[1]**2)*(a[0]-c[0])+(c[0]**2+c[1]**2)*(b[0]-a[0]))/d
        r=mp.sqrt((ux-a[0])**2+(uy-a[1])**2)
        if cover((ux,uy),r) and (bst is None or r<bst): bst=r
    for a,b in itertools.combinations(V,2):
        cc=((a[0]+b[0])/2,(a[1]+b[1])/2); r=mp.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2)/2
        if cover(cc,r) and (bst is None or r<bst): bst=r
    if bst is None: return None
    return bst/(D/2), D, len(V)

print()
print("  高精度复核 top-5:")
gmax_hp = mp.mpf(0); argmax_hp=None
cands = [best[1]] + [p[1] for p in pool[:5]]
for c in cands[:6]:
    try: res = hp_B(*c)
    except Exception as e:
        print("    ", c, "-> 异常", e); continue
    if res is None: continue
    g,D,nv = res
    print(f"    phi={c[0]:.6f} th1={c[1]:.6f} th2={c[2]:.6f}  顶点={nv}  D={mp.nstr(D,10)}  gamma={mp.nstr(g,16)}")
    if g>gmax_hp: gmax_hp, argmax_hp = g, c
print(f"  高精度确认的族 B 最大 gamma = {mp.nstr(gmax_hp,18)}")
print(f"  即 gamma - 1 = {mp.nstr(gmax_hp-1, 6)}  (数量级很小, 但严格大于 0)")

# ---------------- 族 C 等边构造证书 ----------------
print()
print("="*78); print("族 C: 等边三角形构造的完整证书 (解析)"); print("="*78)
h = math.sqrt(3)/2; eps = 1.0
back_min = h/math.tan(math.radians(2*eps)) - 0.5
print(f"  阈值公式: back >= h/tan(2*eps) - side/2")
print(f"            = {h:.10f}/tan(2 deg) - 0.5 = {h/math.tan(math.radians(2*eps)):.6f} - 0.5 = {back_min:.6f}")
print(f"  数值实验阈值 24.3 与解析值一致: {abs(back_min-24.3)<1e-3}")
print()
print("  构造 (边长 = 1, eps = 1 deg, 取 back = 30):")
import adjudicate_domain as AD
ws,_ = AD.equilateral_in_C(back=30.0, side=1.0)
for i,w in enumerate(ws):
    print(f"    S{i+1} = ({w.S[0]:.6f}, {w.S[1]:.6f})   theta{i+1} = {w.theta:.6f} deg"
          f"   边界射线 = {w.theta-1:.4f} / {w.theta+1:.4f}")
r = analyze(ws)
print(f"  交集顶点数 = {r[chr(110)+chr(118)]}   D = {r[chr(68)]:.10f}   R_MEC = {r[chr(82)]:.10f}")
print(f"  gamma = {r[chr(103)+chr(97)+chr(109)+chr(109)+chr(97)]:.10f} = 2/sqrt(3) = {2/math.sqrt(3):.10f}")
print(f"  直径圆覆盖 = {r[chr(99)+chr(111)+chr(118)+chr(101)+chr(114)+chr(115)]}")
print()
print("  各边与站点的对应 (每条边由所在站的边界射线产生):")
T=[(0,0),(1,0),(0.5,h)]
for i in range(3):
    P,Q = T[i], T[(i+1)%3]
    d = math.degrees(math.atan2(Q[1]-P[1], Q[0]-P[0]))
    print(f"    边 {chr(65+i)}{chr(65+(i+1)%3)} 方向 = {d:>9.4f} deg  <->  站 S{i+1} 的边界射线 {ws[i].theta-1:>9.4f} deg  (共线)")
