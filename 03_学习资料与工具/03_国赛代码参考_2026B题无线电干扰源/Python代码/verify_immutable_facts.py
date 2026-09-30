# -*- coding: utf-8 -*-
"""Q1 主图：不可变数学事实的独立复算与断言。

帝国机制 阶段0 证据脚本。不依赖任何既有图/既有结论，从定义重新计算。
输出 verify_facts.json，供后续所有专家方案与绘图脚本引用。
"""
import json, math, itertools, hashlib, os
from fractions import Fraction

EPS_DEG = 1.0
RAD = math.pi / 180.0

def u(phi_deg):
    p = phi_deg * RAD
    return (math.cos(p), math.sin(p))

def ray(P, phi_deg):
    d = u(phi_deg)
    return (P[0], P[1], d[0], d[1])

def ray_intersect(r1, r2):
    """r = (x0,y0,dx,dy). 返回交点或 None（平行）。"""
    x1,y1,dx1,dy1 = r1
    x2,y2,dx2,dy2 = r2
    den = dx1*dy2 - dy1*dx2
    if abs(den) < 1e-14: return None
    t = ((x2-x1)*dy2 - (y2-y1)*dx2) / den
    return (x1 + t*dx1, y1 + t*dy1)

def in_wedge(P, S, theta_deg, eps_deg=EPS_DEG):
    """W = {S + t*u(phi): t>=0, |phi-theta|<=eps} 的凸角域成员判定（用两条边界半平面）。"""
    vx, vy = P[0]-S[0], P[1]-S[1]
    n = math.hypot(vx, vy)
    if n < 1e-12: return True
    ang = math.degrees(math.atan2(vy, vx))
    d = (ang - theta_deg + 180.0) % 360.0 - 180.0
    return abs(d) <= eps_deg + 1e-9

def hull(points):
    pts = sorted(set((round(x,10), round(y,10)) for x,y in points))
    if len(pts) <= 2: return pts
    def cross(o,a,b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lower=[]
    for p in pts:
        while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=1e-12: lower.pop()
        lower.append(p)
    upper=[]
    for p in reversed(pts):
        while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=1e-12: upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]

def poly_diameter(V):
    best=0.0; pair=None
    for a,b in itertools.combinations(V,2):
        d=math.dist(a,b)
        if d>best: best, pair = d, (a,b)
    return best, pair

def mec_exact(points):
    """最小覆盖圆：枚举 2 点/3 点支撑集（Welzl 的穷举等价形式）。"""
    P=[(float(x),float(y)) for x,y in points]
    best=None
    def cover(c,r):
        return all(math.dist(p,c) <= r + 1e-9 for p in P)
    # 3 点外接圆
    for a,b,c in itertools.combinations(P,3):
        ax,ay=a; bx,by=b; cx,cy=c
        d = 2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
        if abs(d) < 1e-12: continue
        ux=((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
        uy=((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
        r=math.dist((ux,uy),a)
        if cover((ux,uy),r) and (best is None or r<best[1]-1e-12): best=((ux,uy),r)
    # 2 点直径圆
    for a,b in itertools.combinations(P,2):
        c=((a[0]+b[0])/2,(a[1]+b[1])/2); r=math.dist(a,b)/2
        if cover(c,r) and (best is None or r<best[1]-1e-12): best=(c,r)
    # 1 点
    if best is None:
        best=(P[0],0.0)
    return best

# ---------------- 1. 两站基准算例 ----------------
S1=(0.0,0.0); S2=(600.0,0.0); G=(300.0,500.0)
theta1=math.degrees(math.atan2(500.0-0.0,300.0-0.0))
theta2=math.degrees(math.atan2(500.0-0.0,300.0-600.0))
theta1=round(theta1,6); theta2=round(theta2,6)

rays = [ray(S1,theta1-EPS_DEG), ray(S1,theta1+EPS_DEG),
        ray(S2,theta2-EPS_DEG), ray(S2,theta2+EPS_DEG)]
cand=[]
for r1,r2 in itertools.combinations(rays,2):
    p=ray_intersect(r1,r2)
    if p is None: continue
    if in_wedge(p,S1,theta1) and in_wedge(p,S2,theta2):
        cand.append(p)
V=hull(cand)
D,(Pa,Pb)=poly_diameter(V)
C,R=mec_exact(V)
gamma = R/(D/2)
jung_lo = D/2
jung_hi = D/math.sqrt(3.0)

# 覆盖判据（Thales）：以 P,Q 为直径的圆覆盖 L ⟺ 所有顶点 X 满足 ∠PXQ ≥ 90°
def thales_min_angle(V,P,Q):
    angs=[]
    for X in V:
        v1=(P[0]-X[0],P[1]-X[1]); v2=(Q[0]-X[0],Q[1]-X[1])
        n1=math.hypot(*v1); n2=math.hypot(*v2)
        if n1<1e-12 or n2<1e-12: continue
        angs.append(math.degrees(math.acos(max(-1,min(1,(v1[0]*v2[0]+v1[1]*v2[1])/(n1*n2))))))
    return min(angs), angs

minang, allang = thales_min_angle(V,Pa,Pb)

# ---------------- 2. 等边三角形反例 ----------------
side=1.0
T=[(0.0,0.0),(side,0.0),(side/2, side*math.sqrt(3)/2)]
Dt,(Ta,Tb)=poly_diameter(T)
Ct,Rt=mec_exact(T)
minang_t,_=thales_min_angle(T,Ta,Tb)

# ---------------- 3. 一般夹逼（Jung 定理） ----------------
# D/2 <= R_MEC <= D/sqrt(3)，等边三角形取上界；直径圆半径 D/2，故一般不能覆盖。
report = {
  "schema": "q1_main_figure_immutable_facts/v1",
  "generated_by": "verify_immutable_facts.py (帝国机制 阶段0 独立复算)",
  "inputs": {"eps_deg":EPS_DEG,"S1":S1,"S2":S2,"G":G},
  "derived_angles": {"theta1_deg":theta1,"theta2_deg":theta2},
  "L": {
    "n_vertices": len(V),
    "vertices": [{"name":f"P{i+1}","xy":[round(x,4),round(y,4)]} for i,(x,y) in enumerate(V)],
    "convex_hull_of_valid_ray_intersections": True
  },
  "diameter": {"D":round(D,4),"endpoints":[[round(Pa[0],4),round(Pa[1],4)],[round(Pb[0],4),round(Pb[1],4)]]},
  "mec": {"center":[round(C[0],4),round(C[1],4)],"R_MEC":round(R,4)},
  "jung": {"lower_D_over_2":round(jung_lo,4),"upper_D_over_sqrt3":round(jung_hi,4),
           "gamma_R_over_halfD":round(gamma,6),
           "gamma_equals_1": abs(gamma-1.0)<1e-6},
  "thales": {"min_vertex_angle_deg":round(minang,4),
             "all_vertices_ge_90": minang >= 90.0 - 1e-6,
             "per_vertex_deg":[round(a,4) for a in allang]},
  "counterexample_equilateral": {"side":side,"D":round(Dt,6),"R_MEC":round(Rt,6),
             "D_over_2":round(Dt/2,6),"D_over_sqrt3":round(Dt/math.sqrt(3),6),
             "diameter_circle_covers": False,
             "min_vertex_angle_deg":round(minang_t,4),
             "note":"等边三角形取 Jung 上界 R=D/sqrt(3)>D/2，以 D 为直径的圆不覆盖 L。"}
}
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"verify_facts.json")
with open(out,"w",encoding="utf-8") as f:
    json.dump(report,f,ensure_ascii=False,indent=2)

print(json.dumps(report,ensure_ascii=False,indent=2))
print("\n[sha256]", hashlib.sha256(json.dumps(report,sort_keys=True).encode()).hexdigest()[:16])
