# -*- coding: utf-8 -*-
"""_layout_check.py — 两个 24 最优解独立核验（扫描线 + 单位格双法）
横版（编程手解）与竖版（建模手核验解）都应覆盖 24 格、0 重叠。
"""
MODULES = {
    'b1': {'verts': [(1,0),(3,0),(3,2),(4,2),(4,4),(0,4),(0,2),(1,2)]},
    'b2': {'verts': [(0,0),(2,0),(2,2),(1,2),(1,4),(0,4)]},
    'b3': {'verts': [(0,0),(2,0),(2,1),(0,1)]},
    'b4': {'verts': [(0,0),(1,0),(1,4),(0,4)]},
}

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

def scan_overlap(A, oA, B, oB, n=400):
    vsA = [(x+oA[0], y+oA[1]) for x, y in A]; vsB = [(x+oB[0], y+oB[1]) for x, y in B]
    bA = bb(vsA); bB = bb(vsB)
    ylo = max(bA[1], bB[1]); yhi = min(bA[3], bB[3])
    if ylo >= yhi: return False
    eps = 1e-9
    def xints(v, y):
        xs = []
        for i in range(len(v)):
            x1, y1 = v[i]; x2, y2 = v[(i+1) % len(v)]
            if abs(y1-y2) < eps: continue
            if min(y1, y2) <= y+eps and y-eps <= max(y1, y2): xs.append(x1)
        xs.sort()
        return [(xs[k], xs[k+1]) for k in range(0, len(xs)-1, 2)]
    for k in range(n):
        y = ylo + (yhi-ylo)*(k+0.5)/n
        for a in xints(vsA, y):
            for b in xints(vsB, y):
                if max(a[0], b[0]) < min(a[1], b[1]) - eps: return True
    return False

def check(name, sol):
    placed = []
    for m, d, off in sol:
        v = rot(MODULES[m]['verts'], d)
        placed.append((v, off, m))
    ov = False
    for i in range(len(placed)):
        for j in range(i+1, len(placed)):
            v1, o1, m1 = placed[i]; v2, o2, m2 = placed[j]
            if scan_overlap(v1, o1, v2, o2) or (cells([(x+o1[0], y+o1[1]) for x, y in v1]) & cells([(x+o2[0], y+o2[1]) for x, y in v2])):
                print(f'  [FAIL] {name}: {m1} vs {m2} 重叠')
                ov = True
    covered = set.union(*[cells([(x+o[0], y+o[1]) for x, y in v]) for v, o, _ in placed])
    env = bb([p for v, o, _ in placed for p in [(x+o[0], y+o[1]) for x, y in v]])
    print(f'  {name}: 重叠={ov} 覆盖格数={len(covered)}/24 包络={env[2]-env[0]:.0f}×{env[3]-env[1]:.0f}')

# 横版（编程手解）
check('横版(编程手)', [('b1', 0, (0,0)), ('b2', 0, (-1,0)), ('b3', 90, (3,0)), ('b4', 0, (4,0))])
# 竖版（建模手核验解）
check('竖版(建模手)', [('b1', 180, (0,0)), ('b4', 0, (0,2)), ('b2', 180, (2,2)), ('b3', 90, (1,4))])
print('两解应均为 重叠=False 覆盖格数=24')
