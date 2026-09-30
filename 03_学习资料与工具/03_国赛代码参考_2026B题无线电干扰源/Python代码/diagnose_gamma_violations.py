# -*- coding: utf-8 -*-
"""列出 gamma=1 但 Thales 判不覆盖的全部违约算例, 高精度逐项核对。"""
import math, random, itertools
import mpmath as mp
import q1_geometry_core as q
mp.mp.dps = 50
random.seed(20260912)

def random_convex(n, scale=1.0):
    pts=[(random.uniform(-1,1),random.uniform(-1,1)) for _ in range(n)]
    cx=sum(p[0] for p in pts)/n; cy=sum(p[1] for p in pts)/n
    pts=sorted(pts,key=lambda p: math.atan2(p[1]-cy,p[0]-cx))
    return [(x*scale,y*scale) for x,y in pts]

def hp(V):
    P=[(mp.mpf(repr(x)),mp.mpf(repr(y))) for x,y in V]
    return P

def mec_hp(P):
    def cover(c,r): return all(mp.sqrt((p[0]-c[0])**2+(p[1]-c[1])**2) <= r for p in P)
    best=None
    for a,b,c in itertools.combinations(P,3):
        d=2*(a[0]*(b[1]-c[1])+b[0]*(c[1]-a[1])+c[0]*(a[1]-b[1]))
        if abs(d)<mp.mpf('1e-40'): continue
        ux=((a[0]**2+a[1]**2)*(b[1]-c[1])+(b[0]**2+b[1]**2)*(c[1]-a[1])+(c[0]**2+c[1]**2)*(a[1]-b[1]))/d
        uy=((a[0]**2+a[1]**2)*(c[0]-b[0])+(b[0]**2+b[1]**2)*(a[0]-c[0])+(c[0]**2+c[1]**2)*(b[0]-a[0]))/d
        r=mp.sqrt((ux-a[0])**2+(uy-a[1])**2)
        if cover((ux,uy),r) and (best is None or r<best[1]): best=((ux,uy),r)
    for a,b in itertools.combinations(P,2):
        cc=((a[0]+b[0])/2,(a[1]+b[1])/2); r=mp.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2)/2
        if cover(cc,r) and (best is None or r<best[1]): best=(cc,r)
    return best

cnt=0
for _ in range(6000):
    n=random.randint(3,9)
    V=random_convex(n, random.choice([1.0,10.0]))
    if len(V)<3: continue
    D,ends=q.diameter(V)
    if D<1e-9: continue
    C,R=q.mec(V); gamma=R/(D/2)
    ok_m,ang_s=q.diameter_circle_covers(V,*ends,tol=0.05)
    if abs(gamma-1.0)<=1e-6 and not ok_m:
        cnt+=1
        P=hp(V)
        Ch,Rh=mec_hp(P)
        Dh=max(mp.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2) for a,b in itertools.combinations(P,2))
        gh=Rh/(Dh/2)
        # 每个顶点到 mid(直径对) 的距离 vs D/2
        Pa=hp([ends[0]])[0]; Pb=hp([ends[1]])[0]
        mid=((Pa[0]+Pb[0])/2,(Pa[1]+Pb[1])/2)
        rr=Dh/2
        worst=max((mp.sqrt((p[0]-mid[0])**2+(p[1]-mid[1])**2), i) for i,p in enumerate(P))
        print(f"违约 #{cnt}: n={len(V)}  gamma_hp={mp.nstr(gh,18)}  gamma-1={mp.nstr(gh-1,6)}")
        print(f"   直径圆半径 D/2 = {mp.nstr(rr,18)}")
        print(f"   最远顶点到 D/2 圆心 mid 的距离 = {mp.nstr(worst[0],18)}  (顶点 idx {worst[1]})")
        print(f"   ★ 超出量 = {mp.nstr(worst[0]-rr,6)}")
        print(f"   R_MEC_hp = {mp.nstr(Rh,18)}   Dh/2 = {mp.nstr(Dh/2,18)}")
        if cnt>=8: break
print("总违约:", cnt)
