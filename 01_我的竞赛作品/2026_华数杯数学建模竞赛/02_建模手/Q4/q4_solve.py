# -*- coding: utf-8 -*-
"""q4_solve.py — Q4 验证题精确求解（严格几何）
4 模块（T/L/2矩形）最小包络面积。暴力枚举朝向与摆放。
重叠检测 = 严格 SAT：任一边相交 OR 任一顶点被对方包含（凹多边形安全）。
"""
import itertools, math

MODULES = [
    {"id": "b1", "type": "T", "area": 12, "verts": [(1,0),(3,0),(3,2),(4,2),(4,4),(0,4),(0,2),(1,2)]},
    {"id": "b2", "type": "L", "area": 6,  "verts": [(0,0),(2,0),(2,2),(1,2),(1,4),(0,4)]},
    {"id": "b3", "type": "rect", "area": 2, "verts": [(0,0),(2,0),(2,1),(0,1)]},
    {"id": "b4", "type": "rect", "area": 4, "verts": [(0,0),(1,0),(1,4),(0,4)]},
]
TOTAL_AREA = 24


def rotate_verts(verts, deg):
    if deg == 0:
        return [(float(x), float(y)) for x, y in verts]
    rad = math.radians(deg)
    c, s = math.cos(rad), math.sin(rad)
    out = []
    for x, y in verts:
        nx = round(x * c - y * s, 6)
        ny = round(x * s + y * c, 6)
        out.append((nx, ny))
    minx = min(v[0] for v in out); miny = min(v[1] for v in out)
    return [(x - minx, y - miny) for x, y in out]


def poly_bbox(verts):
    xs = [v[0] for v in verts]; ys = [v[1] for v in verts]
    return min(xs), min(ys), max(xs), max(ys)


def cross(o, a, b):
    return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])


def seg_intersect(p1, p2, p3, p4, eps=1e-9):
    """线段 p1p2 与 p3p4 是否相交（含端点和共线）。"""
    d1 = cross(p3, p4, p1); d2 = cross(p3, p4, p2)
    d3 = cross(p1, p2, p3); d4 = cross(p1, p2, p4)
    if ((d1 > eps and d2 < -eps) or (d1 < -eps and d2 > eps)) and \
       ((d3 > eps and d4 < -eps) or (d3 < -eps and d4 > eps)):
        return True
    # 端点落在对方线段上（含共线部分）
    def on_seg(p, q, r, e):
        return min(q[0], r[0])-e <= p[0] <= max(q[0], r[0])+e and \
               min(q[1], r[1])-e <= p[1] <= max(q[1], r[1])+e
    if abs(d1) <= eps and on_seg(p1, p3, p4, eps): return True
    if abs(d2) <= eps and on_seg(p2, p3, p4, eps): return True
    if abs(d3) <= eps and on_seg(p3, p1, p2, eps): return True
    if abs(d4) <= eps and on_seg(p4, p1, p2, eps): return True
    return False


def point_in_poly(px, py, verts, eps=1e-9):
    """射线法（顶点逆时针），含边界。"""
    inside = False
    n = len(verts)
    for i in range(n):
        x1, y1 = verts[i]
        x2, y2 = verts[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            xint = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if px < xint:
                inside = not inside
    # 边界检查：点是否在边上
    for i in range(n):
        x1, y1 = verts[i]
        x2, y2 = verts[(i + 1) % n]
        if abs((px-x1)*(y2-y1) - (py-y1)*(x2-x1)) <= eps and \
           min(x1,x2)-eps <= px <= max(x1,x2)+eps and \
           min(y1,y2)-eps <= py <= max(y1,y2)+eps:
            return True
    return inside


def polys_overlap(vertsA, offA, vertsB, offB, eps=1e-9):
    """严格重叠：边相交 OR 顶点包含。返回是否重叠。"""
    Ash = [(v[0]+offA[0], v[1]+offA[1]) for v in vertsA]
    Bsh = [(v[0]+offB[0], v[1]+offB[1]) for v in vertsB]
    # 包围盒粗判
    bA = poly_bbox(Ash); bB = poly_bbox(Bsh)
    if bA[2] <= bB[0]+eps or bB[2] <= bA[0]+eps or bA[3] <= bB[1]+eps or bB[3] <= bA[1]+eps:
        return False
    # 边相交
    nA, nB = len(Ash), len(Bsh)
    for i in range(nA):
        p1, p2 = Ash[i], Ash[(i+1) % nA]
        for j in range(nB):
            p3, p4 = Bsh[j], Bsh[(j+1) % nB]
            if seg_intersect(p1, p2, p3, p4, eps):
                return True
    # 顶点包含（一个在另一个内部）
    for v in Ash:
        if point_in_poly(v[0], v[1], Bsh, eps): return True
    for v in Bsh:
        if point_in_poly(v[0], v[1], Ash, eps): return True
    return False


def place_any_overlap(placed, verts, off):
    for v, o, _, _ in placed:
        if polys_overlap(v, o, verts, off):
            return True
    return False


def gen_candidates(placed, verts):
    """候选位置 = 已放模块包围盒外扩整数格（覆盖缺口内嵌位置）。"""
    w = poly_bbox(verts)[2] - poly_bbox(verts)[0]
    h = poly_bbox(verts)[3] - poly_bbox(verts)[1]
    cands = set()
    if not placed:
        return {(0.0, 0.0)}
    # 全放置区域的整数格点（外扩 1）
    minx = min(po[0] for pv, po, _, _ in placed) - 1
    maxx = max(po[0] + poly_bbox(pv)[2] for pv, po, _, _ in placed) + 1
    miny = min(po[1] for pv, po, _, _ in placed) - 1
    maxy = max(po[1] + poly_bbox(pv)[3] for pv, po, _, _ in placed) + 1
    x = float(int(minx))
    while x <= maxx:
        y = float(int(miny))
        while y <= maxy:
            cands.add((x, y))
            y += 1.0
        x += 1.0
    return cands


def solve():
    best = None
    cnt = 0
    orient_cands = []
    for m in MODULES:
        if m["type"] == "rect":
            orient_cands.append([0, 90])
        else:
            orient_cands.append([0, 90, 180, 270])
    perms = list(itertools.permutations(range(4)))
    for perm in perms:
        for ocombo in itertools.product(*[orient_cands[i] for i in perm]):
            orient = {k: ocombo[list(perm).index(k)] for k in perm}
            verts_by_mod = {k: rotate_verts(MODULES[k]["verts"], orient[k]) for k in perm}
            placed = []

            def dfs(depth):
                nonlocal best, cnt
                if depth == 4:
                    cnt += 1
                    minx = min(po[0] + poly_bbox(v)[0] for v, po, _, _ in placed)
                    miny = min(po[1] + poly_bbox(v)[1] for v, po, _, _ in placed)
                    maxx = max(po[0] + poly_bbox(v)[2] for v, po, _, _ in placed)
                    maxy = max(po[1] + poly_bbox(v)[3] for v, po, _, _ in placed)
                    W = maxx - minx; H = maxy - miny
                    area = W * H
                    if best is None or area < best["area"] - 1e-9 or \
                       (abs(area - best["area"]) < 1e-9 and W + H < best["W"] + best["H"]):
                        best = {"area": area, "W": W, "H": H,
                                "placed": [tuple(x) for x in placed]}
                    return
                k = perm[depth]
                verts = verts_by_mod[k]
                for off in gen_candidates(placed, verts):
                    if placed and place_any_overlap(placed, verts, off):
                        continue
                    placed.append((verts, off, MODULES[k]["id"], orient[k]))
                    dfs(depth + 1)
                    placed.pop()

            dfs(0)
    return best, cnt


def report(res):
    print(f"最小包络面积 = {res['area']:.1f}  (W×H = {res['W']:.1f}×{res['H']:.1f})")
    print(f"死区 = {(res['area']-TOTAL_AREA)/res['area']*100:.2f}%")
    print("最优摆放：")
    for v, off, mid, deg in res["placed"]:
        xs = [round(p[0]+off[0], 1) for p in v]
        ys = [round(p[1]+off[1], 1) for p in v]
        print(f"  {mid} (rot {deg}°): 偏移({off[0]:.0f},{off[1]:.0f}) 顶点{list(zip(xs, ys))}")


if __name__ == "__main__":
    res, cnt = solve()
    print(f"枚举 {cnt} 个无重叠布局")
    if res:
        report(res)
    else:
        print("无可行解？")
