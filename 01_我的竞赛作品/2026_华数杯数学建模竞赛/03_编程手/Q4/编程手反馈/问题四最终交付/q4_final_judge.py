# -*- coding: utf-8 -*-
"""q4_final_judge.py — 解析精确重叠判定（扫描线法，正交多边形）
单位格法/半格法是采样近似；扫描线对正交多边形是解析精确的。
对每个 28 解逐对判定，最终裁决最小包络是否真为 28。
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

def x_interval_at_y(verts, y, eps=1e-9):
    """多边形在高度 y 处的水平截面 x 区间列表（扫描线）。
    对正交多边形：找边中与 y 相交的，构造 [x_lo, x_hi] 区间。"""
    xs = []
    n = len(verts)
    for i in range(n):
        x1, y1 = verts[i]; x2, y2 = verts[(i+1) % n]
        if abs(y1 - y2) < eps:  # 水平边，跳过（垂直扫描找竖直边）
            continue
        if min(y1, y2) <= y + eps and y - eps <= max(y1, y2):
            # 竖直边，x 固定
            xs.append(x1)
    xs.sort()
    # 竖直边两两配对成区间
    intervals = []
    for k in range(0, len(xs) - 1, 2):
        intervals.append((xs[k], xs[k+1]))
    return intervals

def scanline_overlap(vertsA, offA, vertsB, offB, n_slices=400, eps=1e-9):
    """扫描线法：在 y 方向密集采样，每层求两多边形 x 区间交集。
    正交多边形轴对齐 → 采样足够密即精确。"""
    vsA = [(x+offA[0], y+offA[1]) for x, y in vertsA]
    vsB = [(x+offB[0], y+offB[1]) for x, y in vertsB]
    bA = poly_bbox(vsA); bB = poly_bbox(vsB)
    ylo = max(bA[1], bB[1]); yhi = min(bA[3], bB[3])
    if ylo >= yhi: return False
    # 密集采样 y
    for k in range(n_slices):
        y = ylo + (yhi - ylo) * (k + 0.5) / n_slices
        ia = x_interval_at_y(vsA, y)
        ib = x_interval_at_y(vsB, y)
        for a in ia:
            for b in ib:
                lo = max(a[0], b[0]); hi = min(a[1], b[1])
                if hi - lo > eps:
                    return True
    return False

# 半格法（step 0.5）
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
def half_cells(verts):
    b = poly_bbox(verts)
    cells = set()
    i = int(b[0]*2)
    while i <= int(b[2]*2):
        j = int(b[1]*2)
        while j <= int(b[3]*2):
            if point_in_poly(i*0.5+0.25, j*0.5+0.25, verts):
                cells.add((round(i*0.5,2), round(j*0.5,2)))
            j += 1
        i += 1
    return cells
def unit_cells(verts):
    b = poly_bbox(verts)
    cells = set()
    for i in range(int(b[0]), int(b[2])):
        for j in range(int(b[1]), int(b[3])):
            if point_in_poly(i+0.5, j+0.5, verts):
                cells.add((i, j))
    return cells

def judge(name, sol):
    """sol: [(mid, deg, off)]。三种方法逐对判定。"""
    print(f"\n=== {name} ===")
    placed = []
    for mid, deg, off in sol:
        v = rotate_verts(MODULES[mid]["verts"], deg)
        vs = [(x+off[0], y+off[1]) for x, y in v]
        placed.append((mid, deg, off, v, vs))
    all_ok = True
    for i in range(len(placed)):
        for j in range(i+1, len(placed)):
            m1, d1, o1, v1, vs1 = placed[i]
            m2, d2, o2, v2, vs2 = placed[j]
            ov_scan = scanline_overlap(v1, o1, v2, o2)
            ov_unit = bool(unit_cells(vs1) & unit_cells(vs2))
            ov_half = bool(half_cells(vs1) & half_cells(vs2))
            if ov_scan or ov_unit or ov_half:
                all_ok = False
                print(f"  [重叠] {m1}vs{m2}: scan={ov_scan} unit={ov_unit} half={ov_half}")
    print(f"  {'✓ 无重叠' if all_ok else '✗ 有重叠'}")

# 全搜索（单位格法）得 28 解，抽取若干用扫描线裁决
mods = {"b1": [0,90,180,270], "b2": [0,90,180,270], "b3": [0,90], "b4": [0,90]}
rest = ["b2", "b3", "b4"]
verts_all = {mid: {d: rotate_verts(MODULES[mid]["verts"], d) for d in mods[mid]} for mid in rest}
best = [1e18]; best_sols = []
def recurse(depth, perm, placed):
    if depth >= len(perm):
        minx = min(po[0] for _,_,v,po in placed); maxx = max(po[0]+poly_bbox(v)[2] for _,_,v,po in placed)
        miny = min(po[1] for _,_,v,po in placed); maxy = max(po[1]+poly_bbox(v)[3] for _,_,v,po in placed)
        a = (maxx-minx)*(maxy-miny)
        if a < best[0]-1e-9: best[0] = a; best_sols[:] = [list(placed)]
        elif abs(a-best[0])<1e-9: best_sols.append(list(placed))
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
print(f"单位格法全搜索最小包络 = {best[0]}, 解数 = {len(best_sols)}")

# 用扫描线精确法重验所有最优解是否真无重叠
print("\n=== 扫描线法重验最优解 ===")
valid = 0
for sol in best_sols:
    placed = []
    for mid, deg, vshift, off in sol:
        v = rotate_verts(MODULES[mid]["verts"], deg)
        placed.append((mid, deg, off, v))
    ok = True
    for i in range(len(placed)):
        for j in range(i+1, len(placed)):
            m1,d1,o1,v1 = placed[i]; m2,d2,o2,v2 = placed[j]
            if scanline_overlap(v1, o1, v2, o2):
                ok = False
    if ok:
        valid += 1
print(f"扫描线法确认无重叠的最优解数 = {valid} / {len(best_sols)}")
if valid:
    for sol in best_sols:
        placed = [(m,d,o) for m,d,v,o in sol]
        minx = min(o[0] for _,_,o in placed); maxx = max(o[0]+poly_bbox(rotate_verts(MODULES[m]["verts"],d))[2] for m,d,o in placed)
        miny = min(o[1] for _,_,o in placed); maxy = max(o[1]+poly_bbox(rotate_verts(MODULES[m]["verts"],d))[3] for m,d,o in placed)
        print(f"  例: {[(m,d,o) for m,d,o in placed]} 包络 {(maxx-minx)}x{(maxy-miny)}")
        break
