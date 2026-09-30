# -*- coding: utf-8 -*-
"""裁决前核验: 匿名裁决包中"候选A/B 反例卡"所依赖的全部数值断言。"""
import math
import q1_geometry_core as q

print("=" * 78)
print("核验 1: 等边三角形反例 (裁决包事实 #3)")
print("=" * 78)
e = q.equilateral(1.0)
print(f"  边长 a=1;  D = {e['D']:.10f}   (应为 1)")
print(f"  R_MEC = {e['R_MEC']:.10f}   (应为 1/sqrt(3) = {1/math.sqrt(3):.10f})")
print(f"  D/2   = {e['jung_lo']:.10f}")
print(f"  D/sqrt3 = {e['jung_hi']:.10f}")
print(f"  gamma = R_MEC/(D/2) = {e['gamma']:.10f}   (裁决包称 2/sqrt(3) = {2/math.sqrt(3):.10f})")
print(f"  最小顶点角 = {e['min_angle']:.6f} deg   (应为 60)")
print(f"  直径圆覆盖 L ? {e['covers']}   (应为 False)")
print(f"  >>> 裁决包 gamma=2/sqrt(3) 断言: {'正确' if abs(e['gamma']-2/math.sqrt(3))<1e-9 else '错误'}")

print()
print("=" * 78)
print("核验 2: '以底边为直径的圆漏掉第三点' 的几何")
print("=" * 78)
base = [(0.0,0.0),(1.0,0.0)]
apex = (0.5, math.sqrt(3)/2)
c = (0.5, 0.0); r = 0.5
d = math.dist(apex, c)
print(f"  底边 (0,0)-(1,0) 为直径 => 圆心 (0.5,0), 半径 0.5")
print(f"  第三顶点 (0.5, {math.sqrt(3)/2:.6f}) 到圆心距离 = {d:.10f}")
print(f"  超出量 = {d - r:.10f}  > 0  => {'第三顶点在圆外 (断言成立)' if d>r else '断言不成立'}")
v1=(-0.5, math.sqrt(3)/2); v2=(0.5, math.sqrt(3)/2)
ang = math.degrees(math.acos((v1[0]*v2[0]+v1[1]*v2[1])/(math.hypot(*v1)*math.hypot(*v2))))
print(f"  第三顶点处张角 ∠(底边两端) = {ang:.6f} deg  < 90  => 断言成立")

print()
print("=" * 78)
print("核验 3: 基准算例各顶点 ∠P2 X P4 —— '在每个顶点画角弧' 是否合法")
print("=" * 78)
b = q.baseline()
V,(P,Q) = b["V"], b["ends"]
names = ["P1","P2","P3","P4"]
for name, X in zip(names, V):
    v1=(P[0]-X[0],P[1]-X[1]); v2=(Q[0]-X[0],Q[1]-X[1])
    n1,n2 = math.hypot(*v1), math.hypot(*v2)
    if n1 < 1e-9 or n2 < 1e-9:
        print(f"  {name} {tuple(round(x,4) for x in X)}  ∠ = 退化 (X 即直径端点, 弦长为 0) —— 不可画角弧")
    else:
        cs=max(-1,min(1,(v1[0]*v2[0]+v1[1]*v2[1])/(n1*n2)))
        print(f"  {name} {tuple(round(x,4) for x in X)}  ∠ = {math.degrees(math.acos(cs)):.4f} deg  —— 可画角弧")
print("  >>> 4 个顶点中仅 2 个有定义; 规格若写'每个顶点'即含无定义标注 (实现陷阱)")

print()
print("=" * 78)
print("核验 4: gamma 的尺度无关性 (裁决包淘汰规则: 不得把米制值写成通用数轴)")
print("=" * 78)
for scale, tag in [(1.0,"原尺度"), (0.001,"米->毫米量纲"), (1000.0,"放大1000倍")]:
    S1=(0.0,0.0); S2=(600.0*scale,0.0); G=(300.0*scale,500.0*scale)
    th1=math.degrees(math.atan2(G[1],G[0])); th2=math.degrees(math.atan2(G[1],G[0]-S2[0]))
    ws=[q.Wedge(S1,th1,1.0), q.Wedge(S2,th2,1.0)]
    L=q.locate(ws); D,_=q.diameter(L["vertices"]); C,R=q.mec(L["vertices"])
    print(f"  {tag:>12}: D={D:>14.4f}  R_MEC={R:>12.4f}  gamma={R/(D/2):.10f}")
print("  >>> gamma 与尺度无关 (恒为 1.0000); 米制数值 39.5983/19.7992/22.8621 随尺度变化。")
print("      故通用 Jung 数轴必须用归一化 r=R/(D/2) ∈ [1, 2/sqrt(3)], 不能标米制刻度。")
