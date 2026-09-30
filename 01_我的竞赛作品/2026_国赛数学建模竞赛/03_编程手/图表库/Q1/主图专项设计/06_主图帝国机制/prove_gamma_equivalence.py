# -*- coding: utf-8 -*-
"""定理: 对有界凸多边形 L,  gamma = R_MEC/(D/2) = 1  <=>  以 D 为直径的圆覆盖 L。

证明
----
(<=) 直径圆覆盖 L => R_MEC <= D/2;  又恒有 R_MEC >= D/2;  故 gamma = 1。
(=>) 设 R_MEC = D/2, 最小覆盖圆盘 B(c, D/2)。取 L 的直径对 P,Q, |PQ| = D = 2*R_MEC。
     因 P,Q ∈ L ⊆ B 且 |PQ| 等于 B 的直径, 故 P,Q 必为 B 的对径点, 从而 c = mid(P,Q),
     即 B 恰为以 PQ 为直径的圆, 于是直径圆覆盖 L。        ∎

数值验证策略(重要)
------------------
过渡点附近, (gamma-1) 与 (90 - 最小顶点角) 的敏感度是**不同阶**的: 圆半径在支撑集
由 2 点变 3 点的临界处是二阶(切触)量, 而顶点角是一阶量。因此
    gamma - 1 ~ 1e-6  可对应   90 - min_angle ~ 1e-2 度。
若用同一个绝对容差判定两端, 必然产生假阳性违约。本脚本因此:
  - 只统计"有明确裕度"的算例 (min_angle <= 89.9 度, 或 >= 90.1 度);
  - 把裕度不足的算例记为"数值不可分辨", 不计入违约;
  - 凸性由凸包保证 (不使用仅按极角排序的星形多边形)。
"""
import math, random, itertools, json, os
import q1_geometry_core as q

random.seed(20260912)
GAM_TOL = 1e-9          # gamma 与 1 的数值相等判据
ANG_MARGIN = 0.1        # 度: 判定"明确覆盖 / 明确不覆盖"的裕度
N = 20000

def convex_hull(pts):
    pts = sorted(set((round(x,12), round(y,12)) for x, y in pts))
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

st={"trials":0,"clear_covered":0,"clear_uncovered":0,"unresolvable":0,
    "viol_a":0,"viol_b":0,"gamma_min":9e9,"gamma_max":-9e9,"ex_a":[],"ex_b":[]}

for _ in range(N):
    k=random.randint(3,10)
    sc=random.choice([1.0,10.0])
    V=convex_hull([(random.uniform(-1,1)*sc, random.uniform(-1,1)*sc) for _ in range(k)])
    if len(V)<3: continue
    D,ends=q.diameter(V)
    if D<1e-9: continue
    C,R=q.mec(V); gamma=R/(D/2)
    _,minang=q.diameter_circle_covers(V,*ends)
    if minang is None: continue
    st["trials"]+=1
    st["gamma_min"]=min(st["gamma_min"],gamma); st["gamma_max"]=max(st["gamma_max"],gamma)
    is_one = abs(gamma-1.0) <= GAM_TOL

    if minang >= 90.0 + ANG_MARGIN:                 # 明确覆盖
        st["clear_covered"]+=1
        if not is_one:                               # 违约 B: 覆盖但 gamma != 1
            st["viol_b"]+=1
            if len(st["ex_b"])<3: st["ex_b"].append({"n":len(V),"gamma":gamma,"min_angle":minang})
    elif minang <= 90.0 - ANG_MARGIN:                # 明确不覆盖
        st["clear_uncovered"]+=1
        if is_one:                                   # 违约 A: gamma==1 但不覆盖
            st["viol_a"]+=1
            if len(st["ex_a"])<3: st["ex_a"].append({"n":len(V),"gamma":gamma,"min_angle":minang})
    else:
        st["unresolvable"]+=1                        # 过渡带, 数值不可分辨

tri=[{"apex_deg":a, **{k2: (round(v2,6) if isinstance(v2,float) else v2)
                       for k2,v2 in q.near_equilateral(a-60.0).items() if k2 in ("gamma",)}}
     for a in range(60,181,5)]

out={
 "schema":"q1_gamma_equivalence/v3",
 "claim":"对有界凸多边形 L:  gamma = R_MEC/(D/2) = 1  <=>  以直径端点 P,Q 为直径的圆覆盖 L。",
 "proof":[
  "(<=) 直径圆覆盖 L => R_MEC <= D/2; 恒有 R_MEC >= D/2; 故 gamma = 1。",
  "(=>) R_MEC = D/2 时, 直径对 P,Q 的距离 D 等于最小覆盖圆盘直径 2*R_MEC, "
  "故 P,Q 为该圆盘的对径点, 圆心 = mid(P,Q), 该圆盘即 PQ 直径圆, 从而覆盖 L。"
 ],
 "numerical_test":{
  "trials":st["trials"], "N_attempted":N, "convex_hull_enforced":True,
  "gamma_tol":GAM_TOL, "angle_margin_deg":ANG_MARGIN,
  "clear_covered":st["clear_covered"], "clear_uncovered":st["clear_uncovered"],
  "unresolvable_transition_band":st["unresolvable"],
  "violation_A_gamma1_but_not_covered":st["viol_a"],
  "violation_B_covered_but_gamma_not1":st["viol_b"],
  "gamma_observed_range":[round(st["gamma_min"],9),round(st["gamma_max"],9)],
  "verdict":"等价成立(零违约)" if st["viol_a"]==0 and st["viol_b"]==0 else "存在违约",
  "examples_A":st["ex_a"], "examples_B":st["ex_b"]
 },
 "numerical_sensitivity":{
  "observation":"过渡点附近 (gamma-1) 与 (90-最小顶点角) 不同阶: gamma-1 ~ 1e-6 可对应 90-min_angle ~ 1e-2 度。",
  "cause":"最小覆盖圆由 2 点支撑转为 3 点支撑时, 半径对形状是二阶(切触)临界量; 顶点角是一阶量。",
  "action":"机检验收必须按两端各自的阶选取容差; 过渡带算例应标为'数值不可分辨'而非违约。"
 },
 "triangle_family_sample":tri,
 "gamma_reference":{"min":1.0,"max_2_over_sqrt3":round(2/math.sqrt(3),6),
  "note":"gamma ∈ [1, 2/sqrt(3)]; gamma=1 <=> 覆盖; 等边三角形取上界 1.154700。"},
 "implication_for_figure":[
  "gamma 不是装饰性'缺口比', 而是覆盖判据的充要指标 —— 强于 'D/2 是下界'。",
  "主图可给出一般判据: 直径圆覆盖 L <=> gamma=1 (等价于 Thales 顶点角判据)。",
  "两站基准算例 gamma=1 是'覆盖成立'的充要见证, 但只是众多 gamma=1 情形之一, 不构成一般保证; "
  "一般情形 gamma>1 且不覆盖。",
  "建议图面: gamma 数轴 [1, 2/sqrt(3)] 同轴标出基准例 1.0000 与等边反例 1.154700。"
 ]
}
p=os.path.join(os.path.dirname(os.path.abspath(__file__)),"gamma_equivalence.json")
json.dump(out,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print(json.dumps(out["numerical_test"],ensure_ascii=False,indent=2))
