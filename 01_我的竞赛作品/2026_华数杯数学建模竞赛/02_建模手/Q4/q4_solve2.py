# -*- coding: utf-8 -*-
"""q4_solve2.py — Q4 验证题精确枚举（优化版）
优化：
  1. b1 固定于原点（平移不变性消除 4! 平移重复）
  2. 候选位置 = 已放模块边界对齐 + 缺口内整数格点
  3. 面积下界剪枝：部分放置的最小可能包络 ≥ best 则剪
  4. 严格 SAT 重叠检测（边相交 + 顶点包含）
输出：最小包络面积 + 所有达到该面积的摆放
"""
import itertools

MODULES = [
    {"id": "b1", "type": "T", "area": 12, "verts": [(1,0),(3,0),(3,2),(4,2),(4,4),(0,4),(0,2),(1,2)]},
    {"id": "b2", "type": "L", "area": 6,  "verts": [(0,0),(2,0),(2,2),(1,2),(1,4),(0,4)]},
    {"id": "b3", "type": "rect", "area": 2, "verts": [(0,0),(2,0),(2,1),(0,1)]},
    {"id": "b4", "type": "rect", "area": 4, "verts": [(0,0),(1,0),(1,4),(0,4)]},
]
TOTAL_AREA = 24


def rotate_verts(verts, deg):
    """整数旋转：0/90/180/270，精确无浮点误差。"""
    if deg == 0:
        return [(float(x), float(y)) for x, y in verts]
    out = []
    for x, y in verts:
        if deg == 90:
            nx, ny = -y, x
        elif deg == 180:
            nx, ny = -x, -y
        elif deg == 270:
            nx, ny = y, -x
        out.append((nx, ny))
    minx = min(v[0] for v in out); miny = min(v[1] for v in out)
    return [(x - minx, y - miny) for x, y in out]


def poly_bbox(verts):
    xs = [v[0] for v in verts]; ys = [v[1] for v in verts]
    return min(xs), min(ys), max(xs), max(ys)


def cross(o, a, b):
    return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])


def seg_intersect(p1, p2, p3, p4, eps=1e-9):
    d1 = cross(p3, p4, p1); d2 = cross(p3, p4, p2)
    d3 = cross(p1, p2, p3); d4 = cross(p1, p2, p4)
    if ((d1 > eps and d2 < -eps) or (d1 < -eps and d2 > eps)) and \
       ((d3 > eps and d4 < -eps) or (d3 < -eps and d4 > eps)):
        return True
    def on_seg(p, q, r, e):
        return min(q[0], r[0])-e <= p[0] <= max(q[0], r[0])+e and \
               min(q[1], r[1])-e <= p[1] <= max(q[1], r[1])+e
    if abs(d1) <= eps and on_seg(p1, p3, p4, eps): return True
    if abs(d2) <= eps and on_seg(p2, p3, p4, eps): return True
    if abs(d3) <= eps and on_seg(p3, p1, p2, eps): return True
    if abs(d4) <= eps and on_seg(p4, p1, p2, eps): return True
    return False


def point_in_poly(px, py, verts, eps=1e-9):
    inside = False
    n = len(verts)
    for i in range(n):
        x1, y1 = verts[i]
        x2, y2 = verts[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            xint = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if px < xint:
                inside = not inside
    for i in range(n):
        x1, y1 = verts[i]
        x2, y2 = verts[(i + 1) % n]
        if abs((px-x1)*(y2-y1) - (py-y1)*(x2-x1)) <= eps and \
           min(x1,x2)-eps <= px <= max(x1,x2)+eps and \
           min(y1,y2)-eps <= py <= max(y1,y2)+eps:
            return True
    return inside


def polys_overlap(vertsA, offA, vertsB, offB, eps=1e-9):
    Ash = [(v[0]+offA[0], v[1]+offA[1]) for v in vertsA]
    Bsh = [(v[0]+offB[0], v[1]+offB[1]) for v in vertsB]
    bA = poly_bbox(Ash); bB = poly_bbox(Bsh)
    if bA[2] <= bB[0]+eps or bB[2] <= bA[0]+eps or bA[3] <= bB[1]+eps or bB[3] <= bA[1]+eps:
        return False
    nA, nB = len(Ash), len(Bsh)
    for i in range(nA):
        p1, p2 = Ash[i], Ash[(i+1) % nA]
        for j in range(nB):
            p3, p4 = Bsh[j], Bsh[(j+1) % nB]
            if seg_intersect(p1, p2, p3, p4, eps):
                return True
    for v in Ash:
        if point_in_poly(v[0], v[1], Bsh, eps): return True
    for v in Bsh:
        if point_in_poly(v[0], v[1], Ash, eps): return True
    return False


def gen_candidates(placed, verts):
    """候选 = 与已放模块边对齐 + 缺口内整数格点（外扩 1），覆盖内嵌。
    placed: [(verts, off), ...]"""
    if not placed:
        return [(0.0, 0.0)]
    cands = set()
    # 边界对齐
    for v, po in placed:
        pb = poly_bbox(v)
        w = pb[2]-pb[0]; h = pb[3]-pb[1]
        cands.add((po[0]+w, po[1]))
        cands.add((po[0], po[1]+h))
        cands.add((po[0]-poly_bbox(verts)[2]+poly_bbox(verts)[0], po[1]))
        cands.add((po[0], po[1]-poly_bbox(verts)[3]+poly_bbox(verts)[1]))
    # 缺口内/近邻整数格点
    minx = int(min(po[0] for _, po in placed) - 1)
    maxx = int(max(po[0] + poly_bbox(v)[2] for v, po in placed) + 1)
    miny = int(min(po[1] for _, po in placed) - 1)
    maxy = int(max(po[1] + poly_bbox(v)[3] for v, po in placed) + 1)
    for x in range(minx, maxx+1):
        for y in range(miny, maxy+1):
            cands.add((float(x), float(y)))
    return list(cands)


def solve():
    best_area = [1e18]
    best_sols = []
    # b1 固定原点，其余模块排列枚举
    rest = [1, 2, 3]
    orient_cands = {}
    for mi, m in enumerate(MODULES):
        orient_cands[mi] = [0, 90] if m["type"] == "rect" else [0, 90, 180, 270]
    # 预计算所有旋转后的顶点
    verts_all = {mi: {d: rotate_verts(m["verts"], d) for d in orient_cands[mi]}
                 for mi, m in enumerate(MODULES)}
    nodes = [None, None, None, None]

    def current_bbox():
        xs0 = [po[0] for v, po, _, _ in nodes if nodes[0] or True]
        # 简化：直接从 nodes 算
        minx = min(po[0] for v, po, _, _ in nodes if po is not None)
        miny = min(po[1] for v, po, _, _ in nodes if po is not None)
        maxx = max(po[0] + poly_bbox(v)[2] for v, po, _, _ in nodes if po is not None)
        maxy = max(po[1] + poly_bbox(v)[3] for v, po, _, _ in nodes if po is not None)
        return minx, miny, maxx, maxy

    def placed_now():
        return [(v, po) for item in nodes
                if item is not None and item[1] is not None
                for v, po, _, _ in [item]]

    def try_place(depth, remaining, order):
        """深度优先：按 order 顺序放置。depth = 已放索引（order 已确定）。"""
        nonlocal best_area, best_sols
        pn = placed_now()
        if depth > 1 and pn:
            minx = min(po[0] for _, po in pn)
            miny = min(po[1] for _, po in pn)
            maxx = max(po[0] + poly_bbox(v)[2] for v, po in pn)
            maxy = max(po[1] + poly_bbox(v)[3] for v, po in pn)
            if (maxx-minx)*(maxy-miny) >= best_area[0] - 1e-9:
                return
        if depth >= len(order):
            minx = min(po[0] for _, po in pn)
            miny = min(po[1] for _, po in pn)
            maxx = max(po[0] + poly_bbox(v)[2] for v, po in pn)
            maxy = max(po[1] + poly_bbox(v)[3] for v, po in pn)
            W = maxx - minx; H = maxy - miny
            area = W * H
            if area < best_area[0] - 1e-9:
                best_area[0] = area
                best_sols = [list(nodes)]
            elif abs(area - best_area[0]) < 1e-9:
                best_sols.append(list(nodes))
            return
        mi = order[depth]
        for deg in orient_cands[mi]:
            verts = verts_all[mi][deg]
            pn = placed_now()
            for off in gen_candidates(pn, verts):
                if pn:
                    bad = False
                    for vv, oo in pn:
                        if polys_overlap(vv, oo, verts, off):
                            bad = True
                            break
                    if bad:
                        continue
                nodes[mi] = (verts, off, mi, deg)
                try_place(depth + 1, remaining, order)
                nodes[mi] = (None, None, None, None)

    # 启发式贪心预求解（确定性，快速给出初始 best 供剪枝）
    def greedy_initial():
        """真实贪心：b1 各朝向原点，其余贴边枚举取最小包络。"""
        for b1deg in orient_cands[0]:
            cand = [(verts_all[0][b1deg], (0.0, 0.0))]
            for mi in [2, 1, 3]:  # b3(2), b2(6), b4(4)
                options = []
                for deg in orient_cands[mi]:
                    verts = verts_all[mi][deg]
                    for off in gen_candidates(cand, verts):
                        bad = any(polys_overlap(vv, oo, verts, off) for vv, oo in cand)
                        if not bad:
                            nxt = cand + [(verts, off)]
                            minx = min(po[0] for _, po in nxt)
                            miny = min(po[1] for _, po in nxt)
                            maxx = max(po[0] + poly_bbox(v)[2] for v, po in nxt)
                            maxy = max(po[1] + poly_bbox(v)[3] for v, po in nxt)
                            options.append((((maxx-minx)*(maxy-miny), maxx-minx+maxy-miny), (verts, off)))
                if options:
                    cand.append(min(options, key=lambda t: t[0])[1])
                else:
                    break
            if len(cand) == 4:
                minx = min(po[0] for _, po in cand)
                miny = min(po[1] for _, po in cand)
                maxx = max(po[0] + poly_bbox(v)[2] for v, po in cand)
                maxy = max(po[1] + poly_bbox(v)[3] for v, po in cand)
                a = (maxx-minx)*(maxy-miny)
                if a < best_area[0]:
                    best_area[0] = a
        print(f"  启发式初始 best = {best_area[0]}")

    greedy_initial()
    # b1 各朝向均试（T 型 4 朝向），其余 3 模块全排列
    for b1deg in orient_cands[0]:
        for order in itertools.permutations(rest):
            nodes[0] = (verts_all[0][b1deg], (0.0, 0.0), 0, b1deg)
            try_place(1, rest, [0] + list(order))
            nodes[0] = (None, None, None, None)
    return best_area[0], best_sols


def report(best_area, best_sols):
    print(f"最小包络面积 = {best_area:.1f}")
    print(f"死区 = {(best_area-TOTAL_AREA)/best_area*100:.2f}%")
    print(f"达到最优的摆放数 = {len(best_sols)}")
    for i, sol in enumerate(best_sols[:3]):
        print(f"\n--- 解 {i+1} ---")
        for v, po, mi, deg in sol:
            if po is None:
                continue
            xs = [round(p[0]+po[0], 1) for p in v]
            ys = [round(p[1]+po[1], 1) for p in v]
            print(f"  b{mi+1} (rot {deg}°): off({po[0]:.0f},{po[1]:.0f}) WxH={poly_bbox(v)[2]-poly_bbox(v)[0]:.0f}x{poly_bbox(v)[3]-poly_bbox(v)[1]:.0f}")


if __name__ == "__main__":
    area, sols = solve()
    report(area, sols)
