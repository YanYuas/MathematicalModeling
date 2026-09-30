# -*- coding: utf-8 -*-
"""灵敏度场景穷举核对：解决"全固定0°=28 vs 30"冲突。单位格重叠 + 面积剪枝。
cur 存 (局部顶点, offset)；计算时统一平移，避免二次平移 bug。"""
import itertools

MODULES = [
    {'id': 'b1', 'verts': [(1,0),(3,0),(3,2),(4,2),(4,4),(0,4),(0,2),(1,2)]},
    {'id': 'b2', 'verts': [(0,0),(2,0),(2,2),(1,2),(1,4),(0,4)]},
    {'id': 'b3', 'verts': [(0,0),(2,0),(2,1),(0,1)]},
    {'id': 'b4', 'verts': [(0,0),(1,0),(1,4),(0,4)]},
]

def rot(v, d):
    if d == 0:
        return [(float(x), float(y)) for x, y in v]
    out = []
    for x, y in v:
        if d == 90: nx, ny = -y, x
        elif d == 180: nx, ny = -x, -y
        else: nx, ny = y, -x
        out.append((nx, ny))
    mx = min(p[0] for p in out); my = min(p[1] for p in out)
    return [(x-mx, y-my) for x, y in out]

def bb(v):
    return min(p[0] for p in v), min(p[1] for p in v), max(p[0] for p in v), max(p[1] for p in v)

def pin(px, py, v):
    inside = False; n = len(v)
    for i in range(n):
        x1, y1 = v[i]; x2, y2 = v[(i+1) % n]
        if (y1 > py) != (y2 > py):
            xi = x1 + (py-y1)*(x2-x1)/(y2-y1)
            if px < xi: inside = not inside
    return inside

def cells(v):
    b = bb(v); s = set()
    for i in range(int(b[0]), int(b[2])):
        for j in range(int(b[1]), int(b[3])):
            if pin(i+0.5, j+0.5, v): s.add((i, j))
    return s

def sh(v, off):
    return [(x+off[0], y+off[1]) for x, y in v]

def search(deg_sets):
    verts_all = {mi: {d: rot(m['verts'], d) for d in deg_sets[mi]} for mi, m in enumerate(MODULES)}
    best = [10**9]; sols = []
    rest = [1, 2, 3]
    for b1d in deg_sets[0]:
        b1v = verts_all[0][b1d]
        for perm in itertools.permutations(rest):
            def try_place(k, cur):
                # cur: list of (局部v, off)
                if k >= len(perm):
                    ms = [p for v, o in cur for p in sh(v, o)]
                    bx = bb(ms)
                    a = (bx[2]-bx[0])*(bx[3]-bx[1])
                    if a < best[0]-1e-9:
                        best[0] = a; sols[:] = [list(cur)]
                    elif abs(a-best[0]) < 1e-9:
                        sols.append(list(cur))
                    return
                mi = perm[k]
                for d in deg_sets[mi]:
                    v = verts_all[mi][d]
                    minx = int(min(o[0] for _, o in cur)-1); maxx = int(max(o[0]+bb(vv)[2]-bb(vv)[0] for vv, o in cur)+1)
                    miny = int(min(o[1] for _, o in cur)-1); maxy = int(max(o[1]+bb(vv)[3]-bb(vv)[1] for vv, o in cur)+1)
                    for x in range(minx, maxx+1):
                        for y in range(miny, maxy+1):
                            off = (float(x), float(y))
                            # 剪枝：新 bbox ≥ best 且未放满则跳（下界安全）
                            if k+1 < len(perm):
                                ms2 = [p for vv, oo in cur for p in sh(vv, oo)] + sh(v, off)
                                bx2 = bb(ms2)
                                if (bx2[2]-bx2[0])*(bx2[3]-bx2[1]) >= best[0]:
                                    continue
                            if any(cells(sh(vv, oo)) & cells(sh(v, off)) for vv, oo in cur):
                                continue
                            try_place(k+1, cur + [(v, off)])
            try_place(0, [(b1v, (0.0, 0.0))])
    return best[0], len(sols)

scen = [
    ('全固定0°', [{0},{0},{0},{0}]),
    ('仅b3可旋转(0/90)', [{0},{0},{0,90},{0}]),
    ('b4固定0°其余自由', [{0,90,180,270},{0,90,180,270},{0,90},{0}]),
    ('b1固定90°其余自由', [{90},{0,90,180,270},{0,90},{0,90}]),
    ('全自由', [{0,90,180,270},{0,90,180,270},{0,90},{0,90}]),
]
for name, sets in scen:
    a, c = search(sets)
    print(f'{name}: 最小包络={a} 解数={c}')
