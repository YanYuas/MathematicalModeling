# -*- coding: utf-8 -*-
"""族 B 的平行四边形可能性 + 中心对称性的正确核验 (用有界配置)。"""
import math, random
import q1_geometry_core as q

def analyze(wedges, tol=1e-7):
    H=[hp for w in wedges for hp in w.halfplanes()]
    bnd,_=q.is_bounded(H)
    raw=q.intersect_halfplanes(H,tol)
    if not bnd or len(raw)<3: return None
    V=q.order_ccw(raw)
    return dict(V=V, nv=len(V), bounded=bnd)

def B(t1,t2,phi=0.0):
    return [q.Wedge((0.0,0.0),t1,1.0), q.Wedge((math.cos(phi),math.sin(phi)),t2,1.0)]

def mid_dist(V):
    if len(V)!=4: return None
    a=((V[0][0]+V[2][0])/2,(V[0][1]+V[2][1])/2)
    c=((V[1][0]+V[3][0])/2,(V[1][1]+V[3][1])/2)
    return math.dist(a,c)

print("="*76)
print("族 B: 平行四边形 (对角中点重合) 何时出现?  S1=(0,0), S2=(1,0)")
print("="*76)
t1=59.036243
for dt in (0.0, 61.9275, 90.0, 150.0, 179.0, 180.0, 181.0, 200.0):
    r=analyze(B(t1,t1+dt))
    if r is None:
        H=[hp for w in B(t1,t1+dt) for hp in w.halfplanes()]
        bnd,gap=q.is_bounded(H)
        print(f"  dtheta={dt:>8.3f}  有界={bnd} (法向最大间隔 {gap:.3f} deg)  -> L 无界或空, 不属于族 B")
        continue
    d=mid_dist(r["V"])
    tag = "平行四边形" if (d is not None and d<1e-9) else "非平行四边形"
    print(f"  dtheta={dt:>8.3f}  顶点数={r[chr(110)+chr(118)]}  对角中点距离={d if d is None else round(d,6)}  -> {tag}")

print()
print("="*76)
print("基准两站算例的中心对称性 (文档B 的关键断言)")
print("="*76)
b=q.baseline(); V=b["V"]
m1=((V[0][0]+V[2][0])/2,(V[0][1]+V[2][1])/2)
m2=((V[1][0]+V[3][0])/2,(V[1][1]+V[3][1])/2)
print(f"  对角 P1P3 中点 = ({m1[0]:.6f}, {m1[1]:.6f})")
print(f"  对角 P2P4 中点 = ({m2[0]:.6f}, {m2[1]:.6f})")
print(f"  距离 = {math.dist(m1,m2):.6f}  =>  {'中心对称' if math.dist(m1,m2)<1e-9 else '不中心对称'}")
print(f"  gamma = {b[chr(103)+chr(97)+chr(109)+chr(109)+chr(97)]:.6f}")

print()
print("="*76)
print("族 B 中是否存在平行四边形? 大规模抽样")
print("="*76)
random.seed(11); n=0; para=0; tri=0; quad=0
for _ in range(200000):
    phi=random.uniform(0,2*math.pi); t1=random.uniform(0,360); t2=random.uniform(0,360)
    r=analyze(B(t1,t2,phi))
    if r is None: continue
    n+=1
    if r["nv"]==3: tri+=1
    if r["nv"]==4:
        quad+=1
        d=mid_dist(r["V"])
        if d is not None and d<1e-7: para+=1
print(f"  有界非空样本 = {n}   四边形 = {quad}   三角形 = {tri}")
print(f"  其中平行四边形 = {para}")
print("  >>> 族 B 中存在平行四边形" if para>0 else "  >>> 族 B 中未出现平行四边形 (与解析结论一致)")
