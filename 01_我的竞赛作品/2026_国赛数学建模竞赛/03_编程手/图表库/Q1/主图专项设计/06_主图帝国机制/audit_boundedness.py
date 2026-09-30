# -*- coding: utf-8 -*-
"""对事实卡 #2 (D = max ||p-q||, p,q in L) 的边界条件审计。

路由文件只声明 L 是凸多边形, 未声明 L 有界。若 L 无界, 则 D 不存在(发散),
"直径圆" 与 Jung 夹逼均无从谈起。本脚本给出存在性反例并定位有界性条件。
"""
import math, json, itertools
import mpmath as mp
mp.mp.dps = 30

def wedge_contains(P, S, theta_deg, eps_deg):
    vx, vy = P[0]-S[0], P[1]-S[1]
    if vx == 0 and vy == 0: return True
    ang = mp.degrees(mp.atan2(vy, vx))
    d = mp.fmod(ang-theta_deg+180, 360)-180
    return abs(d) <= eps_deg

def sample_L(S_list, th_list, eps, box=4000, step=25):
    """在 box 范围内粗网格采样 L, 用于判断有界/无界迹象。"""
    pts=[]
    rng=range(-box, box+1, step)
    for x in rng:
        for y in rng:
            P=(mp.mpf(x), mp.mpf(y))
            if all(wedge_contains(P,S,th,eps) for S,th in zip(S_list,th_list)):
                pts.append((x,y))
    return pts

eps = mp.mpf(1)
cases = []

# 案例 1: 两站基准算例 (应有限)
S=[(mp.mpf(0),mp.mpf(0)),(mp.mpf(600),mp.mpf(0))]
TH=[mp.degrees(mp.atan2(500,300)), mp.degrees(mp.atan2(500,-300))]
p1 = sample_L(S, TH, eps, box=700, step=10)
far1 = max(math.hypot(*p) for p in p1) if p1 else None
cases.append({"case":"两站基准算例 S1=(0,0),S2=(600,0), 指向 G=(300,500)",
              "far_sample_radius": round(far1,2), "bounded":"是(采样半径有限, 且由4条射线围成)"})

# 案例 2: 两个同向楔形 (应无界)
S2_=[(mp.mpf(0),mp.mpf(0)),(mp.mpf(1),mp.mpf(0))]
TH2=[mp.mpf(0), mp.mpf(0)]
p2 = sample_L(S2_, TH2, eps, box=4000, step=50)
far2 = max(math.hypot(*p) for p in p2) if p2 else None
cases.append({"case":"两站同向楔形 S1=(0,0),S2=(1,0), 两者 theta 均为 0 度",
              "far_sample_radius": round(far2,2),
              "bounded":"否 —— 交集是无界楔形",
              "note":"x 可达采样上界 4000, 继续增大 x 仍在交集中"})

# 有界性判据(二维, 正确形式):
#   W_i = cone(d1_i, d2_i) = { n_i1.(x-S_i) <= 0, n_i2.(x-S_i) <= 0 },
#   其中 d1=u(theta-eps), d2=u(theta+eps),
#        n1=(d1_y, -d1_x)  (d1 顺时针转 90 度),  n2=(-d2_y, d2_x) (d2 逆时针转 90 度).
#   L = 四个半平面之交; L 有界 <=> 四个外法向量不被任何闭半平面包含
#   <=> 法向量按角度排序后相邻间隔的最大值 <= 180 度。
def normals_of(S_list, th_list, eps):
    ns=[]
    for th in th_list:
        for sgn, kind in ((-1,'n1'), (1,'n2')):
            p=(th+sgn*eps)*mp.pi/180
            dx, dy = mp.cos(p), mp.sin(p)
            ns.append((dy, -dx) if kind=='n1' else (-dy, dx))
    return ns

def bounded_by_normals(nrm):
    angs = sorted(mp.degrees(mp.atan2(n[1], n[0])) % 360 for n in nrm)
    gaps = [ (angs[(i+1)%len(angs)] - angs[i]) % 360 for i in range(len(angs)) ]
    mx = max(gaps)
    return (mx <= 180), float(mx), [round(float(a),4) for a in angs]

b1, mx1, a1 = bounded_by_normals(normals_of(S,TH,eps))
b2, mx2, a2 = bounded_by_normals(normals_of(S2_,TH2,eps))
cases[0]["normal_gap_max_deg"]=round(mx1,4); cases[0]["bounded_by_criterion"]=b1
cases[0]["outward_normals_deg"]=a1
cases[1]["normal_gap_max_deg"]=round(mx2,4); cases[1]["bounded_by_criterion"]=b2
cases[1]["outward_normals_deg"]=a2

out={
 "schema":"q1_boundedness_audit/v1",
 "finding":"路由文件事实卡把 D 定义为 L 上点对距离的最大值, 但未声明 L 有界。"
           "当各站角域方向过于一致时, L 可以是无界凸区域, 此时 D = +inf, "
           "直径圆与 Jung 夹逼均无定义。",
 "status":"对基准算例无影响(本例 L 有界); 但作为'一般结论'的陈述, 图与正文需要显式条件。",
 "criterion":"把每个角域写成两个半平面 n.(x-S)<=0 (n 为边界射线的外法向)。"
             "L 有界 <=> 全部外法向量不被任何闭半平面包含 "
             "<=> 外法向角排序后最大相邻间隔 <= 180 度。",
 "cases":cases,
 "implication_for_figure":[
   "主图在给出一般结论时必须让读者看到 'L 为有界凸多边形' 是前提, 而非默认成立。",
   "若主图只画一般凸多边形 L 而不提有界性, 严格审稿人可指出 D 未必存在。",
   "建议: 在图的'一般情形'分支上标注条件 L 有界(即角域方向不共半平面); "
   "基准算例自然满足该条件。"
 ]
}
import os
p=os.path.join(os.path.dirname(os.path.abspath(__file__)),"boundedness_audit.json")
open(p,"w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False,indent=2))
