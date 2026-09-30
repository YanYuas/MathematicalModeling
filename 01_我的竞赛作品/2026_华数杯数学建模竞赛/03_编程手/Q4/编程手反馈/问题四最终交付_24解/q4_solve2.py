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
    """旋转多边形顶点（整数精确旋转，避免浮点误差）

    Args:
        verts: List[Tuple[int, int]] - 原始顶点坐标列表
        deg: int - 旋转角度，仅支持 0/90/180/270

    Returns:
        List[Tuple[float, float]] - 旋转后的顶点，归一化至第一象限

    算法：整数坐标变换 (x,y) → (-y,x) for 90°, 避免cos/sin的浮点误差
    """
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
    """检测两个多边形是否重叠（单位格法，修复共线贴边误判）

    Args:
        vertsA, vertsB: 多边形顶点列表（局部坐标）
        offA, offB: 偏移量（全局坐标）
        eps: 浮点比较精度阈值

    Returns:
        bool - True表示重叠，False表示分离

    算法：单位格法
        1. 将两个多边形应用偏移得到全局坐标
        2. 遍历覆盖区域内的所有整数格点
        3. 检查每个格点的中心是否同时在两个多边形内部
        4. 如果存在这样的格点 → 重叠，否则 → 不重叠

    优点：
        - 对正交多边形（顶点为整数坐标）是精确的
        - 天然支持共线贴边（贴边不会导致格点中心同时在两个多边形内）
        - 避免SAT的边界判定复杂性

    适用于凹多边形（T型、L型）
    修复原因：SAT在共线贴边时误判，导致漏掉完美平铺解（24）
    """
    Ash = [(v[0]+offA[0], v[1]+offA[1]) for v in vertsA]
    Bsh = [(v[0]+offB[0], v[1]+offB[1]) for v in vertsB]

    # 快速AABB包围盒预判
    bA = poly_bbox(Ash); bB = poly_bbox(Bsh)
    if bA[2] <= bB[0]+eps or bB[2] <= bA[0]+eps or bA[3] <= bB[1]+eps or bB[3] <= bA[1]+eps:
        return False

    # 计算并集包围盒的整数范围
    minx = int(min(bA[0], bB[0]))
    maxx = int(max(bA[2], bB[2]))
    miny = int(min(bA[1], bB[1]))
    maxy = int(max(bA[3], bB[3]))

    # 遍历格点，检查格点中心是否同时在两个多边形内部
    for x in range(minx, maxx + 1):
        for y in range(miny, maxy + 1):
            # 格点中心坐标
            cx, cy = x + 0.5, y + 0.5
            in_A = point_in_poly(cx, cy, Ash, eps)
            in_B = point_in_poly(cx, cy, Bsh, eps)
            if in_A and in_B:
                return True  # 同一格点被两个多边形占用 → 重叠

    return False


def gen_candidates(placed, verts):
    """生成候选放置位置（智能策略：边界对齐 + 缺口填充）

    Args:
        placed: List[Tuple[verts, offset]] - 已放置模块列表
        verts: 待放置模块的顶点列表

    Returns:
        List[Tuple[float, float]] - 候选位置的偏移坐标

    策略1 - 边界对齐：新模块边缘与已放模块边缘对齐（外部贴边）
    策略2 - 缺口填充：在现有布局的外扩范围内枚举整数格点（内嵌缺口）

    覆盖场景：外部扩展、内部嵌入、角落填充
    """
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
    """主求解函数，返回结果字典"""
    best_area, best_sols = _solve_internal()
    if best_sols:
        # 从第一个解中提取W和H
        first_sol = best_sols[0]
        # first_sol 是包含4个模块位置的列表
        all_verts = []
        for v, po, _, _ in first_sol:
            for vx, vy in v:
                all_verts.append((vx + po[0], vy + po[1]))
        minx = min(vx for vx, vy in all_verts)
        maxx = max(vx for vx, vy in all_verts)
        miny = min(vy for vx, vy in all_verts)
        maxy = max(vy for vx, vy in all_verts)
        W = maxx - minx
        H = maxy - miny
        return {
            "area": best_area,
            "W": W,
            "H": H,
            "solutions": best_sols
        }
    return None

def _solve_internal():
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
                    # 记录贪心解到best_sols（转换为nodes格式）
                    # cand顺序：b1, b3(mi=2), b2(mi=1), b4(mi=3)
                    greedy_sol = [None, None, None, None]
                    greedy_sol[0] = (cand[0][0], cand[0][1], 0, b1deg)  # b1
                    greedy_sol[2] = (cand[1][0], cand[1][1], 2, [d for d in orient_cands[2] if rotate_verts(MODULES[2]["verts"], d) == cand[1][0]][0])  # b3
                    greedy_sol[1] = (cand[2][0], cand[2][1], 1, [d for d in orient_cands[1] if rotate_verts(MODULES[1]["verts"], d) == cand[2][0]][0])  # b2
                    greedy_sol[3] = (cand[3][0], cand[3][1], 3, [d for d in orient_cands[3] if rotate_verts(MODULES[3]["verts"], d) == cand[3][0]][0])  # b4
                    best_sols.clear()
                    best_sols.append(greedy_sol)
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
    result = solve()
    if result:
        report(result["area"], result["solutions"])
    else:
        print("未找到可行解")
