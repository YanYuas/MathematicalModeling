# -*- coding: utf-8 -*-
"""q4_find_min.py — 用正确重叠判定（单位格法）重搜最小包络
背景：编程手/建模手的 SAT 在"缺口互补嵌套"（b3 恰好填进 b1 缺口）时
把共线边界误判为重叠，导致漏掉缺口互补的更优解。单位格法正确。
本脚本：单位格法全搜索，候选 = 边界对齐 + 缺口内整数格（精确、不爆炸）。
"""
import itertools

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

# 半格密度核验：step=0.5 采样，更高精度（对照单位格）
def half_cells(verts):
    b = poly_bbox(verts)
    cells = set()
    i = int(b[0]*2)
    while i <= int(b[2]*2):
        j = int(b[1]*2)
        while j <= int(b[3]*2):
            px = i*0.5 + 0.25; py = j*0.5 + 0.25
            if point_in_poly(px, py, verts):
                cells.add((round(px,2), round(py,2)))
            j += 1
        i += 1
    return cells

def overlap_any(vertsA, offA, vertsB, offB, method='unit'):
    vsA = [(x+offA[0], y+offA[1]) for x, y in vertsA]
    vsB = [(x+offB[0], y+offB[1]) for x, y in vertsB]
    if method == 'unit':
        return bool(unit_cells(vsA) & unit_cells(vsB))
    else:
        return bool(half_cells(vsA) & half_cells(vsB))

# 已知可疑对：b3 rot90 @(3,0) 填 b1 右缺 (3,0)-(4,2)
b1 = rotate_verts(MODULES["b1"]["verts"], 0)
b3r = rotate_verts(MODULES["b3"]["verts"], 90)
print("=== 单位格 vs 半格 核对：b3 rot90 嵌 b1 右缺 (3,0) ===")
print("b1 右缺区域 (3,0)-(4,2) 是否为空:")
print("  b1 竖条 (1,0)-(3,2), 横条 (0,2)-(4,4)")
print("  (3,0)-(4,2): x∈[3,4] 竖条不含(到x=3), y∈[0,2] 横条不含(y≥2) → 空缺口 ✓")
print("单位格 b1∩b3:", sorted(unit_cells(b1) & unit_cells([(x+3,y) for x,y in b3r])))
print("半格 b1∩b3:", sorted(half_cells(b1) & half_cells([(x+3,y) for x,y in b3r])))
print("b3 rot90 cells:", sorted(unit_cells(b3r)), "面积2 ✓")

# 全搜索：单位格法（正确判定），候选=边界对齐+缺口内格点
print("\n=== 单位格法全搜索最小包络 ===")
mods = {"b1": [0,90,180,270], "b2": [0,90,180,270], "b3": [0,90], "b4": [0,90]}
rest = ["b2", "b3", "b4"]
verts_all = {mid: {d: rotate_verts(MODULES[mid]["verts"], d) for d in mods[mid]} for mid in rest}
best = [1e18]; best_sols = []

def recurse(depth, perm, placed):
    if depth >= len(perm):
        minx = min(po[0] for _,_,v,po in placed); maxx = max(po[0]+poly_bbox(v)[2] for _,_,v,po in placed)
        miny = min(po[1] for _,_,v,po in placed); maxy = max(po[1]+poly_bbox(v)[3] for _,_,v,po in placed)
        a = (maxx-minx)*(maxy-miny)
        if a < best[0]-1e-9:
            best[0] = a; best_sols[:] = [list(placed)]
        elif abs(a-best[0])<1e-9:
            best_sols.append(list(placed))
        return
    mid = perm[depth]
    for deg in mods[mid]:
        verts = verts_all[mid][deg]
        w = poly_bbox(verts)[2]-poly_bbox(verts)[0]; h = poly_bbox(verts)[3]-poly_bbox(verts)[1]
        # 剪枝
        minx = min(po[0] for _,_,_,po in placed); maxx = max(po[0]+poly_bbox(vv)[2] for _,_,vv,po in placed)
        miny = min(po[1] for _,_,_,po in placed); maxy = max(po[1]+poly_bbox(vv)[3] for _,_,vv,po in placed)
        if (maxx-minx)*(maxy-miny) >= best[0]-1e-9: continue
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

import sys
for b1deg in mods["b1"]:
    b1v = rotate_verts(MODULES["b1"]["verts"], b1deg)
    for perm in itertools.permutations(rest):
        recurse(0, perm, [("b1", b1deg, b1v, (0.0,0.0))])
print(f"最小包络 = {best[0]}")
print(f"达到数 = {len(best_sols)}")
for si, sol in enumerate(best_sols[:3]):
    print(f"解{si+1}: {[(m,d,po) for m,d,v,po in sol]}")
