# -*- coding: utf-8 -*-
"""q4_probe28.py — 聚焦验证 28 解（缺口互补嵌入）
构造候选布局（b3 rot90 嵌入 b1 缺口等），用单位格法 + SAT 双方法核对。
"""
MODULES = {
    "b1": {"area": 12, "verts": [(1,0),(3,0),(3,2),(4,2),(4,4),(0,4),(0,2),(1,2)]},
    "b2": {"area": 6,  "verts": [(0,0),(2,0),(2,2),(1,2),(1,4),(0,4)]},
    "b3": {"area": 2, "verts": [(0,0),(2,0),(2,1),(0,1)]},
    "b4": {"area": 4, "verts": [(0,0),(1,0),(1,4),(0,4)]},
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

def cross(o, a, b):
    return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
def seg_intersect(p1, p2, p3, p4, eps=1e-9):
    d1 = cross(p3,p4,p1); d2 = cross(p3,p4,p2); d3 = cross(p1,p2,p3); d4 = cross(p1,p2,p4)
    if ((d1 > eps and d2 < -eps) or (d1 < -eps and d2 > eps)) and \
       ((d3 > eps and d4 < -eps) or (d3 < -eps and d4 > eps)): return True
    def on_seg(p,q,r,e):
        return min(q[0],r[0])-e <= p[0] <= max(q[0],r[0])+e and min(q[1],r[1])-e <= p[1] <= max(q[1],r[1])+e
    if abs(d1)<=eps and on_seg(p1,p3,p4,eps): return True
    if abs(d2)<=eps and on_seg(p2,p3,p4,eps): return True
    if abs(d3)<=eps and on_seg(p3,p1,p2,eps): return True
    if abs(d4)<=eps and on_seg(p4,p1,p2,eps): return True
    return False
def sat_overlap(vertsA, offA, vertsB, offB, eps=1e-9):
    """严格 SAT：边相交 OR 顶点包含（凹块安全）。"""
    Ash = [(v[0]+offA[0], v[1]+offA[1]) for v in vertsA]
    Bsh = [(v[0]+offB[0], v[1]+offB[1]) for v in vertsB]
    bA = poly_bbox(Ash); bB = poly_bbox(Bsh)
    if bA[2] <= bB[0]+eps or bB[2] <= bA[0]+eps or bA[3] <= bB[1]+eps or bB[3] <= bA[1]+eps:
        return False
    for i in range(len(Ash)):
        p1, p2 = Ash[i], Ash[(i+1)%len(Ash)]
        for j in range(len(Bsh)):
            p3, p4 = Bsh[j], Bsh[(j+1)%len(Bsh)]
            if seg_intersect(p1,p2,p3,p4,eps): return True
    for v in Ash:
        if point_in_poly(v[0], v[1], Bsh, eps): return True
    for v in Bsh:
        if point_in_poly(v[0], v[1], Ash, eps): return True
    return False

def check_solution(name, sol):
    """sol: [(mid, deg, off)]。用单位格 + SAT 双核对，输出包络。"""
    print(f"\n=== {name} ===")
    placed = []
    for mid, deg, off in sol:
        v = rotate_verts(MODULES[mid]["verts"], deg)
        vs = [(x+off[0], y+off[1]) for x, y in v]
        placed.append((mid, v, off, vs))
        print(f"  {mid} rot{deg} off{off} bbox={poly_bbox(vs)} 面积={_area(vs)}")
    # 单位格法
    u_ok = True
    for i in range(len(placed)):
        for j in range(i+1, len(placed)):
            m1,_,_,vs1 = placed[i]; m2,_,_,vs2 = placed[j]
            if unit_cells(vs1) & unit_cells(vs2):
                print(f"  [单位格重叠] {m1} vs {m2}"); u_ok = False
    print(f"  单位格法: {'无重叠 ✓' if u_ok else '有重叠 ✗'}")
    # SAT
    s_ok = True
    for i in range(len(placed)):
        for j in range(i+1, len(placed)):
            m1,_,_,vs1 = placed[i]; m2,_,_,vs2 = placed[j]
            # 用原始局部 + off
            v1o = placed[i][1]; off1 = placed[i][2]; v2o = placed[j][1]; off2 = placed[j][2]
            if sat_overlap(v1o, off1, v2o, off2):
                print(f"  [SAT重叠] {m1} vs {m2}"); s_ok = False
    print(f"  SAT法: {'无重叠 ✓' if s_ok else '有重叠 ✗'}")
    # 包络
    minx = min(off[0]+poly_bbox(v)[0] for _,v,off,_ in placed)
    maxx = max(off[0]+poly_bbox(v)[2] for _,v,off,_ in placed)
    miny = min(off[1]+poly_bbox(v)[1] for _,v,off,_ in placed)
    maxy = max(off[1]+poly_bbox(v)[3] for _,v,off,_ in placed)
    print(f"  包络 {maxx-minx}×{maxy-miny} = {(maxx-minx)*(maxy-miny)}")
    return u_ok, s_ok

def _area(verts):
    n = len(verts); a = 0.0
    for i in range(n):
        j = (i+1) % n
        a += verts[i][0]*verts[j][1] - verts[j][0]*verts[i][1]
    return abs(a)/2.0

# 候选1：b3 rot90 (1x2) 嵌入 b1 缺口 (0,0)-(1,2)
# b1@(0,0) rot0, b2@(4,0) rot0, b3 rot90@(0,0) 填缺口, b4 rot90 4x1 填顶部?
# b1 4x4 缺口左(0,0)-(1,2)右(3,0)-(4,2)。b3 rot90 1x2 填左缺。
# b2 2x4 @(4,0): b2 右上缺(5,2)-(6,4)
sol1 = [("b1", 0, (0,0)), ("b2", 0, (4,0)), ("b3", 90, (0,0)), ("b4", 90, (4,4))]
check_solution("候选1: b3嵌左缺 + b4顶部", sol1)

# 候选2：b3 rot90 填右缺 (3,0)-(4,2)
sol2 = [("b1", 0, (0,0)), ("b2", 0, (4,0)), ("b3", 90, (3,0)), ("b4", 90, (0,4))]
check_solution("候选2: b3嵌右缺 + b4顶部", sol2)

# 候选3：b3 rot90 填 b2 右上缺 (5,2)-(6,4)? b2@(4,0) 右上缺(5,2)-(6,4)
sol3 = [("b1", 0, (0,0)), ("b2", 0, (4,0)), ("b3", 90, (5,2)), ("b4", 90, (0,4))]
check_solution("候选3: b3填b2右上缺", sol3)

# 候选4：b3 填缺口 + b4 竖放于左缺旁，包络 6x5?
sol4 = [("b1", 0, (0,0)), ("b2", 0, (4,0)), ("b3", 90, (0,0)), ("b4", 90, (2,4))]
check_solution("候选4: b3嵌左缺 b4@(2,4)", sol4)
