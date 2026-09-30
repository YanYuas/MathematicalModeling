# -*- coding: utf-8 -*-
"""核对专家A规格 R7 的合法性: "在【每个顶点】画角弧并标角度值"是否成立。"""
import q1_geometry_core as q

b = q.baseline()
V, (P, Q) = b["V"], b["ends"]
print("直径端点 P =", tuple(round(x,4) for x in P), " Q =", tuple(round(x,4) for x in Q))
print()
print(f"{'顶点':>4} {'坐标':>28} {'∠PXQ':>10}  说明")
for i, (name, X) in enumerate(zip(["P1","P2","P3","P4"], V)):
    v1 = (P[0]-X[0], P[1]-X[1]); v2 = (Q[0]-X[0], Q[1]-X[1])
    n1, n2 = (v1[0]**2+v1[1]**2)**.5, (v2[0]**2+v2[1]**2)**.5
    if n1 < 1e-9 or n2 < 1e-9:
        print(f"{name:>4} {str(tuple(round(x,4) for x in X)):>28} {'退化':>10}  X 是直径端点之一, 两条弦之一长度为 0")
    else:
        import math
        cs = max(-1,min(1,(v1[0]*v2[0]+v1[1]*v2[1])/(n1*n2)))
        print(f"{name:>4} {str(tuple(round(x,4) for x in X)):>28} {math.degrees(math.acos(cs)):>10.4f}  合法, 可画角弧")
print()
print("结论: 4 个顶点中只有 P1, P3 处 ∠PXQ 有定义; P2, P4 是直径端点, 角退化。")
print("      '在每个顶点画角弧并标角度值' 若字面执行, 会在 P2/P4 处产生无定义标注。")
