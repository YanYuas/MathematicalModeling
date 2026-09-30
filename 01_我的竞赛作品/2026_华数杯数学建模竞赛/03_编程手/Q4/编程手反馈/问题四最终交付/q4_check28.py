# -*- coding: utf-8 -*-
"""q4_check28.py — 核实 28 解的真实性（缺口互补嵌入）
问题：回溯搜索（单位格法）发现最小包络 28，比 30 更优。
需核实：①28 解结构（含朝向）②单位格法与 SAT 的分歧谁对。
"""
import itertools, sys, io

# 避免 import 顶层执行
import importlib.util
spec = importlib.util.spec_from_file_location(
    "q4iv", r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\CLAUDE工作文件\编程手\Q4\编程手反馈\问题四最终交付\q4_independent_verify.py")
q4iv = importlib.util.module_from_spec(spec)
# 手动执行只取函数（不执行 print 顶层）——改为从源码提取函数太复杂，直接复制核心
MODULES = {
    "b1": {"type": "T", "area": 12, "verts": [(1,0),(3,0),(3,2),(4,2),(4,4),(0,4),(0,2),(1,2)]},
    "b2": {"type": "L", "area": 6,  "verts": [(0,0),(2,0),(2,2),(1,2),(1,4),(0,4)]},
    "b3": {"type": "rect", "area": 2, "verts": [(0,0),(2,0),(2,1),(0,1)]},
    "b4": {"type": "rect", "area": 4, "verts": [(0,0),(1,0),(1,4),(0,4)]},
}
def rotate_verts(verts, deg):
    if deg == 0: return [(float(x), float(y)) for x, y in verts]
    out = []
    for x, y in verts:
        if deg == 90: nx, ny = -y, x
        elif deg == 180: nx, ny = -x, -y
        elif deg == 270: nx, ny = y, -x
        out.append((nx, ny))
    minx = min(v[0] for v in out); miny = min(v[1] for v in out)
    return [(x-minx, y-miny) for x, y in out]
def poly_bbox(verts):
    return (min(v[0] for v in verts), min(v[1] for v in verts),
            max(v[0] for v in verts), max(v[1] for v in verts))
def point_in_poly(px, py, verts, eps=1e-9):
    inside = False; n = len(verts)
    for i in range(n):
        x1, y1 = verts[i]; x2, y2 = verts[(i+1) % n]
        if (y1 > py) != (y2 > py):
            xint = x1 + (py-y1)*(x2-x1)/(y2-y1)
            if px < xint: inside = not inside
    for i in range(n):
        x1, y1 = verts[i]; x2, y2 = verts[(i+1) % n]
        if abs((px-x1)*(y2-y1)-(py-y1)*(x2-x1)) <= eps and \
           min(x1,x2)-eps <= px <= max(x1,x2)+eps and \
           min(y1,y2)-eps <= py <= max(y1,y2)+eps:
            return True
    return inside
def unit_cells(verts):
    b = [min(v[0] for v in verts), min(v[1] for v in verts),
         max(v[0] for v in verts), max(v[1] for v in verts)]
    cells = set()
    for i in range(int(b[0]), int(b[2])):
        for j in range(int(b[1]), int(b[3])):
            if point_in_poly(i+0.5, j+0.5, verts):
                cells.add((i, j))
    return cells

# 搜索：全朝向 + 全排列 + 全整数格点，单位格法
mods = {"b1": [0,90,180,270], "b2": [0,90,180,270], "b3": [0,90], "b4": [0,90]}
rest = ["b2", "b3", "b4"]
verts_all = {mid: {d: rotate_verts(MODULES[mid]["verts"], d) for d in mods[mid]} for mid in rest}
best = [1e18]; best_sol = [None]
def recurse(depth, perm, placed):
    if depth >= len(perm):
        minx = min(po[0] for _,_,v,po in placed); maxx = max(po[0]+poly_bbox(v)[2] for _,_,v,po in placed)
        miny = min(po[1] for _,_,v,po in placed); maxy = max(po[1]+poly_bbox(v)[3] for _,_,v,po in placed)
        a = (maxx-minx)*(maxy-miny)
        if a < best[0]: best[0] = a; best_sol[0] = [(m,dg,po) for m,dg,v,po in placed]
        return
    mid = perm[depth]
    for deg in mods[mid]:
        verts = verts_all[mid][deg]
        w = poly_bbox(verts)[2]-poly_bbox(verts)[0]; h = poly_bbox(verts)[3]-poly_bbox(verts)[1]
        cands = set()
        for _,_,vv,po in placed:
            pb = poly_bbox(vv)
            cands.add((po[0]+pb[2]-pb[0], po[1]))
            cands.add((po[0], po[1]+pb[3]-pb[1]))
            cands.add((po[0]-w, po[1]))
            cands.add((po[0], po[1]-h))
        minx = int(min(po[0] for _,_,_,po in placed)-1); maxx = int(max(po[0]+poly_bbox(vv)[2] for _,_,vv,po in placed)+1)
        miny = int(min(po[1] for _,_,_,po in placed)-1); maxy = int(max(po[1]+poly_bbox(vv)[3] for _,_,vv,po in placed)+1)
        for x in range(minx, maxx+1):
            for y in range(miny, maxy+1): cands.add((float(x), float(y)))
        for off in cands:
            vshift = [(x+off[0], y+off[1]) for x, y in verts]
            bad = any(unit_cells(vv).intersection(unit_cells(vshift)) for _,_,vv,po in placed)
            if not bad:
                placed.append((mid, deg, vshift, off)); recurse(depth+1, perm, placed); placed.pop()
for b1deg in mods["b1"]:
    b1v = rotate_verts(MODULES["b1"]["verts"], b1deg)
    for perm in itertools.permutations(rest):
        recurse(0, perm, [("b1", b1deg, b1v, (0.0,0.0))])

print("== 单位格法搜索结果 ==")
print("最小包络:", best[0])
print("解 (mid, deg, off):", [(m,d,o) for m,d,o in best_sol[0]])

# 用编程手 SAT 交叉验证该解
sys.path.insert(0, r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\CLAUDE工作文件\编程手\Q4\编程手反馈\问题四最终交付")
from q4_solve2 import rotate_verts as r2, polys_overlap as p2
print("\n== 编程手 SAT 交叉验证 28 解 ==")
placed = []
ok = True
for mid, deg, off in best_sol[0]:
    v = r2(MODULES[mid]["verts"], deg)
    placed.append((mid, v, off))
    print(f"  {mid} rot{deg} off{off} bbox={poly_bbox([(x+off[0],y+off[1]) for x,y in v])}")
for i in range(len(placed)):
    for j in range(i+1, len(placed)):
        m1, v1, o1 = placed[i]; m2, v2, o2 = placed[j]
        ov = p2(v1, o1, v2, o2)
        if ov:
            print(f"  [SAT 判重叠] {m1} vs {m2}")
            ok = False
print("SAT 判 28 解: ", "无重叠 ✓" if ok else "存在重叠 ✗")

# 单位格法独立复核该解每一对
print("\n== 单位格法复核 28 解（每对）==")
ok2 = True
for i in range(len(placed)):
    for j in range(i+1, len(placed)):
        m1, v1, o1 = placed[i]; m2, v2, o2 = placed[j]
        vs1 = [(x+o1[0], y+o1[1]) for x,y in v1]
        vs2 = [(x+o2[0], y+o2[1]) for x,y in v2]
        inter = unit_cells(vs1) & unit_cells(vs2)
        if inter:
            print(f"  [单位格判重叠] {m1} vs {m2}: {len(inter)} 格")
            ok2 = False
print("单位格法复核 28 解: ", "无重叠 ✓" if ok2 else "存在重叠 ✗")
