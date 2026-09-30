# -*- coding: utf-8 -*-
"""阶段三 第 2 部分: 族 B (n=2) 的反例搜索与中心对称性检验。"""
import math, random, json, os
import q1_geometry_core as q
from adjudicate_domain import analyze, ang_of  # noqa

random.seed(20260912)
TWO_PI = 2*math.pi

def sample_B(N):
    """WLOG |S2-S1| = 1 (位置整体放缩不改变 L 的形状与 gamma)。"""
    counts, best = {}, None
    for _ in range(N):
        phi = random.uniform(0, TWO_PI)
        S2 = (math.cos(phi), math.sin(phi))
        th1 = random.uniform(0, 360); th2 = random.uniform(0, 360)
        ws = [q.Wedge((0.0, 0.0), th1, 1.0), q.Wedge(S2, th2, 1.0)]
        r = analyze(ws)
        if r is None:
            continue
        counts[r["nv"]] = counts.get(r["nv"], 0) + 1
        key = (phi, th1, th2)
        if best is None or r["gamma"] > best[0]["gamma"]:
            best = (r, key)
    return best, counts

print("="*78)
print("族 B (n = 2, 同半角 eps = 1 deg): 随机搜索")
print("="*78)
best, counts = sample_B(200000)
print("  有界非空样本的顶点数分布:", dict(sorted(counts.items())))
print(f"  最大 gamma = {best[0][chr(103)+chr(97)+chr(109)+chr(109)+chr(97)]:.8f}"
      f"   顶点数 = {best[0][chr(110)+chr(118)]}   phi={best[1][0]:.4f} th1={best[1][1]:.4f} th2={best[1][2]:.4f}")

def build_B(phi, th1, th2):
    S2 = (math.cos(phi), math.sin(phi))
    return [q.Wedge((0.0, 0.0), th1, 1.0), q.Wedge(S2, th2, 1.0)]

# 局部爬山精化
p = list(best[1]); step = 0.5
for _ in range(4000):
    improved = False
    for i in range(3):
        for d in (+step, -step):
            cand = list(p); cand[i] += d
            r = analyze(build_B(*cand))
            if r and r["gamma"] > best[0]["gamma"] + 1e-12:
                best, p, improved = (r, tuple(cand)), cand, True
    if not improved:
        step *= 0.5
        if step < 1e-9:
            break
r, key = best
print(f"  精化后最大 gamma = {r[chr(103)+chr(97)+chr(109)+chr(109)+chr(97)]:.10f}"
      f"   顶点数={r[chr(110)+chr(118)]}  D={r[chr(68)]:.6f}  R_MEC={r[chr(82)]:.6f}")
print(f"  对应参数 phi={key[0]:.6f} rad  th1={key[1]:.6f}  th2={key[2]:.6f}")
print(f"  该例被直径圆覆盖? {r[chr(99)+chr(111)+chr(118)+chr(101)+chr(114)+chr(115)]}"
      f"   最小非端点顶点角 = {r[chr(109)+chr(105)+chr(110)+chr(97)+chr(110)+chr(103)]}")

print()
print("  族 B 中三角形是否可达 (顶点数=3)?",
      "是" if 3 in counts else "否 —— 抽样未见")
if 3 in counts:
    print(f"    三角形样本数 = {counts[3]} / {sum(counts.values())}")

# ---- 中心对称性检验: 基准两站算例 ----
print()
print("="*78)
print("族 B: 基准两站算例的中心对称性检验 (文档B 称 中心对称近似平行四边形)")
print("="*78)
b = q.baseline()
V = b["V"]
m1 = ((V[0][0]+V[2][0])/2, (V[0][1]+V[2][1])/2)   # 对角 P1P3 中点
m2 = ((V[1][0]+V[3][0])/2, (V[1][1]+V[3][1])/2)   # 对角 P2P4 中点
print(f"  对角 P1P3 中点 = ({m1[0]:.6f}, {m1[1]:.6f})")
print(f"  对角 P2P4 中点 = ({m2[0]:.6f}, {m2[1]:.6f})")
print(f"  两中点距离 = {math.dist(m1, m2):.6f}")
print("  中心对称 (平行四边形) 要求两中点重合 -> ",
      "成立" if math.dist(m1, m2) < 1e-9 else "不成立, 故基准 L 不是中心对称的")
print("  基准 L 的 gamma = %.6f" % b["gamma"])

# 检验: 何时才是平行四边形? 理论: |th2-th1| = 180 - 2*eps (mod 360)
print()
print("  理论: L 为平行四边形 <=> |theta2-theta1| = 180 - 2*eps (mod 360)")
th1 = b["theta1"]
for delta in (180-2, 61.9275, 180, 90):
    th2 = th1 + delta
    ws = [q.Wedge((0.0, 0.0), th1, 1.0), q.Wedge((600.0, 0.0), th2, 1.0)]
    rr = analyze(ws)
    if rr is None:
        print(f"    dtheta={delta:>8.4f}  -> 无界/退化"); continue
    Vv = rr["V"]
    if rr["nv"] == 4:
        a = ((Vv[0][0]+Vv[2][0])/2, (Vv[0][1]+Vv[2][1])/2)
        c = ((Vv[1][0]+Vv[3][0])/2, (Vv[1][1]+Vv[3][1])/2)
        dcen = math.dist(a, c)
    else:
        dcen = float("nan")
    print(f"    dtheta={delta:>8.4f}  顶点数={rr[chr(110)+chr(118)]}  对角中点距离={dcen:.3e}"
          f"  gamma={rr[chr(103)+chr(97)+chr(109)+chr(109)+chr(97)]:.8f}")
