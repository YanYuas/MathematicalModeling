# -*- coding: utf-8 -*-
"""Q1 主图：不可变数学事实 —— 高精度独立复算（mpmath, 40 dps）。

帝国机制 阶段0 权威证据脚本。从定义出发，不引用任何既有图或既有结论。
产物: verify_facts.json  （后续所有专家方案与绘图脚本的唯一数值口径）
"""
import json, math, itertools, hashlib, os, sys
import mpmath as mp

mp.mp.dps = 40
EPS_DEG = mp.mpf(1)
RAD = mp.pi/180

S1 = (mp.mpf(0), mp.mpf(0))
S2 = (mp.mpf(600), mp.mpf(0))
G  = (mp.mpf(300), mp.mpf(500))

def u(phi_deg):
    p = phi_deg*RAD
    return (mp.cos(p), mp.sin(p))

def ray(P, phi):
    d = u(phi)
    return (P[0], P[1], d[0], d[1])

def ray_x(r1, r2):
    x1,y1,dx1,dy1 = r1; x2,y2,dx2,dy2 = r2
    den = dx1*dy2 - dy1*dx2
    if abs(den) < mp.mpf('1e-30'): return None
    t = ((x2-x1)*dy2 - (y2-y1)*dx2)/den
    return (x1 + t*dx1, y1 + t*dy1)

def in_wedge(P, S, theta, eps=EPS_DEG):
    vx, vy = P[0]-S[0], P[1]-S[1]
    if mp.sqrt(vx*vx+vy*vy) < mp.mpf('1e-20'): return True
    ang = mp.degrees(mp.atan2(vy, vx))
    d = mp.fmod(ang-theta+180, 360) - 180
    return abs(d) <= eps + mp.mpf('1e-25')

def hull(pts):
    pts = sorted(set((mp.nstr(x,30), mp.nstr(y,30)) for x,y in pts), key=lambda t:(mp.mpf(t[0]),mp.mpf(t[1])))
    pts = [(mp.mpf(a),mp.mpf(b)) for a,b in pts]
    if len(pts) <= 2: return pts
    def cr(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[]
    for p in pts:
        while len(lo)>=2 and cr(lo[-2],lo[-1],p)<=0: lo.pop()
        lo.append(p)
    up=[]
    for p in reversed(pts):
        while len(up)>=2 and cr(up[-2],up[-1],p)<=0: up.pop()
        up.append(p)
    return lo[:-1]+up[:-1]

def diam(V):
    best=mp.mpf(0); pr=None
    for a,b in itertools.combinations(V,2):
        d=mp.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2)
        if d>best: best,pr=d,(a,b)
    return best,pr

def mec(P_):
    P=[(mp.mpf(x),mp.mpf(y)) for x,y in P_]
    def cover(c,r): return all(mp.sqrt((p[0]-c[0])**2+(p[1]-c[1])**2) <= r+mp.mpf('1e-25') for p in P)
    best=None
    for a,b,c in itertools.combinations(P,3):
        ax,ay=a; bx,by=b; cx,cy=c
        d=2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
        if abs(d)<mp.mpf('1e-30'): continue
        ux=((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
        uy=((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
        r=mp.sqrt((ux-ax)**2+(uy-ay)**2)
        if cover((ux,uy),r) and (best is None or r<best[1]): best=((ux,uy),r)
    for a,b in itertools.combinations(P,2):
        cc=((a[0]+b[0])/2,(a[1]+b[1])/2); r=mp.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2)/2
        if cover(cc,r) and (best is None or r<best[1]): best=(cc,r)
    return best or (P[0],mp.mpf(0))

def thales(V,P,Q):
    """返回 L 的每个顶点 X 处的 ∠PXQ（度）。直径端点自身退化，跳过。"""
    out={}
    for i,X in enumerate(V):
        v1=(P[0]-X[0],P[1]-X[1]); v2=(Q[0]-X[0],Q[1]-X[1])
        n1=mp.sqrt(v1[0]**2+v1[1]**2); n2=mp.sqrt(v2[0]**2+v2[1]**2)
        if n1<mp.mpf('1e-20') or n2<mp.mpf('1e-20'): continue
        cs=(v1[0]*v2[0]+v1[1]*v2[1])/(n1*n2)
        cs=max(mp.mpf(-1),min(mp.mpf(1),cs))
        out[f"P{i+1}"]=mp.degrees(mp.acos(cs))
    return out

theta1 = mp.degrees(mp.atan2(G[1], G[0]-S1[0]))
theta2 = mp.degrees(mp.atan2(G[1], G[0]-S2[0]))

rays=[ray(S1,theta1-EPS_DEG),ray(S1,theta1+EPS_DEG),
      ray(S2,theta2-EPS_DEG),ray(S2,theta2+EPS_DEG)]
cand=[]
for r1,r2 in itertools.combinations(rays,2):
    p=ray_x(r1,r2)
    if p is None: continue
    if in_wedge(p,S1,theta1) and in_wedge(p,S2,theta2): cand.append(p)
V=hull(cand)
D,(Pa,Pb)=diam(V)
C,R=mec(V)
gamma=R/(D/2)
tj=thales(V,Pa,Pb)
minang=min(tj.values())

T=[(mp.mpf(0),mp.mpf(0)),(mp.mpf(1),mp.mpf(0)),(mp.mpf('0.5'),mp.sqrt(3)/2)]
Dt,(Ta,Tb)=diam(T); Ct,Rt=mec(T); tj_t=thales(T,Ta,Tb)
minang_t=min(tj_t.values())

def r4(x): return float(mp.nstr(x,12))
def n4(x): return round(float(x),4)
def n6(x): return round(float(x),6)

# 与路由文档(§6)公布口径的逐项比对
DOC={"P1":(288.1342,499.7929),"P2":(300.0,480.7768),"P3":(311.8658,499.7929),
     "P4":(300.0,520.3752),"D":39.5983,"R_MEC":19.7992,"center":(300.0,500.5760),
     "D_over_sqrt3":22.8621}
rep={
 "schema":"q1_main_figure_immutable_facts/v2",
 "method":"mpmath 40dps, 定义驱动复算 (verify_immutable_facts_v2.py)",
 "inputs":{"eps_deg":1.0,"S1":[0,0],"S2":[600,0],"G":[300,500]},
 "derived":{"theta1_deg":n6(theta1),"theta2_deg":n6(theta2)},
 "L":{"is_convex_polygon":True,"n_vertices":len(V),
      "vertices":{f"P{i+1}":[n4(x),n4(y)] for i,(x,y) in enumerate(V)}},
 "diameter":{"D":n4(D),"endpoints":["P2","P4"],
             "endpoints_xy":[[n4(Pa[0]),n4(Pa[1])],[n4(Pb[0]),n4(Pb[1])]]},
 "mec":{"center":[n4(C[0]),n4(C[1])],"R_MEC":n4(R)},
 "jung":{"lower":n4(D/2),"upper":n4(D/mp.sqrt(3)),"gamma":n6(gamma),"gamma_is_1":abs(gamma-1)<mp.mpf('1e-20')},
 "thales":{"criterion":"Pi;Q 直径圆覆盖 L  <=>  L 全部顶点 X 满足 angle PXQ >= 90deg",
           "vertex_angles_deg":{k:n4(v) for k,v in tj.items()},
           "min_deg":n4(minang),"baseline_is_covered":minang>=90},
 "counterexample_equilateral":{"side":1,"D":n6(Dt),"R_MEC":n6(Rt),"D_over_2":n6(Dt/2),
           "D_over_sqrt3":n6(Dt/mp.sqrt(3)),"vertex_angles_deg":{k:n6(v) for k,v in tj_t.items()},
           "min_deg":n6(minang_t),"diameter_circle_covers_L":False,
           "role":"证明一般结论: 半径 D/2 的直径圆不保证覆盖 L"},
 "conclusion":{"general":"以 D 为直径的圆一般不保证覆盖 L; 等边三角形为反例",
               "baseline_status":"两站基准算例 gamma=1 属于 D/2=R_MEC 的特例验证, 不是一般性质",
               "bounds":"D/2 <= R_MEC <= D/sqrt(3)"},
 "doc_crosscheck":{}
}
for k,(x,y) in [("P1",DOC["P1"]),("P2",DOC["P2"]),("P3",DOC["P3"]),("P4",DOC["P4"])]:
    i=int(k[1])-1; rep["doc_crosscheck"][k]={"doc":[x,y],"calc":[n4(V[i][0]),n4(V[i][1])],
        "match_at_4dp":(n4(V[i][0])==x and n4(V[i][1])==y)}
rep["doc_crosscheck"]["D"]={"doc":DOC["D"],"calc":n4(D),"match":n4(D)==DOC["D"]}
rep["doc_crosscheck"]["R_MEC"]={"doc":DOC["R_MEC"],"calc":n4(R),"match":n4(R)==DOC["R_MEC"]}
rep["doc_crosscheck"]["center"]={"doc":list(DOC["center"]),"calc":[n4(C[0]),n4(C[1])],
    "match":(n4(C[0])==DOC["center"][0] and n4(C[1])==DOC["center"][1])}
rep["doc_crosscheck"]["D_over_sqrt3"]={"doc":DOC["D_over_sqrt3"],"calc":n4(D/mp.sqrt(3)),
    "match":n4(D/mp.sqrt(3))==DOC["D_over_sqrt3"]}
rep["doc_crosscheck"]["all_match"]=all(
    (v.get("match_at_4dp") if "match_at_4dp" in v else v.get("match")) for v in rep["doc_crosscheck"].values())

out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"verify_facts.json")
with open(out,"w",encoding="utf-8") as f: json.dump(rep,f,ensure_ascii=False,indent=2)
print(json.dumps(rep,ensure_ascii=False,indent=2))
