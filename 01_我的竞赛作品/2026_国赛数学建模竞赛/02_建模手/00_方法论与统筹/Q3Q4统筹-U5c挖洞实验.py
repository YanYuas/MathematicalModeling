"""U5-c「挖洞」实验：观测点凸包外约束 G ∉ int conv(S) 对 R_MEC 的实际改善

背景：Q3Q4 统筹命题 U5 给出——若某源在点集 S（全部测到 direction 的点）上被观测，
则 G ∉ int conv(S)。问：把这条约束用在定位区域上（L ← L \\ int conv(S)）能否缩小 R_MEC？

用法：python u5c_hole_experiment.py
依赖：numpy
"""

import numpy as np

EPS = np.deg2rad(1.0)      # 示向度误差半角
R_DISK = 1800.0            # 目标圆域半径


# ---------- 三角格 ----------
def lattice(d, margin=1.0):
    pts = []
    n = int((R_DISK * (1 + margin)) / d) + 3
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x = d * (i + j * 0.5)
            y = d * (j * np.sqrt(3.0) / 2.0)
            if x * x + y * y <= R_DISK * R_DISK:
                pts.append((x, y))
    return np.array(pts)


# ---------- 多边形裁剪（Sutherland-Hodgman，保留 n·X >= b） ----------
def clip(poly, n, b):
    out = []
    m = len(poly)
    for i in range(m):
        A = poly[i]
        B = poly[(i + 1) % m]
        da = n @ A - b
        db = n @ B - b
        if da >= 0:
            out.append(A)
        if (da > 0) != (db > 0):
            t = da / (da - db)
            out.append(A + t * (B - A))
    return out


def wedge_halves(S, G, eps):
    """过 S 指向 G 的 ±eps 楔形 -> 两个半平面 (n, b)，判据 n·X >= b"""
    ang = np.arctan2(G[1] - S[1], G[0] - S[0])
    u_lo = np.array([np.cos(ang - eps), np.sin(ang - eps)])
    u_hi = np.array([np.cos(ang + eps), np.sin(ang + eps)])
    n1 = np.array([-u_lo[1], u_lo[0]])
    n2 = np.array([u_hi[1], -u_hi[0]])
    return [(n1, n1 @ S), (n2, n2 @ S)]


def region_poly(S1, S2, G, eps=EPS, R=2000.0):
    """两站交会定位区域（多边形）。R 为初始裁剪方框，远离源的位置不影响本实验。"""
    poly = [np.array([-R, -R]), np.array([R, -R]), np.array([R, R]), np.array([-R, R])]
    for S in (S1, S2):
        for n, b in wedge_halves(S, G, eps):
            poly = clip(poly, n, b)
            if len(poly) < 3:
                return None
    return np.array(poly)


# ---------- 凸包（Andrew 单调链） ----------
def hull(P):
    P = np.unique(np.round(P, 9), axis=0)
    if len(P) < 3:
        return P
    P = P[np.lexsort((P[:, 1], P[:, 0]))]
    def half(pts):
        st = []
        for p in pts:
            while len(st) >= 2 and np.cross(st[-1] - st[-2], p - st[-2]) <= 0:
                st.pop()
            st.append(p)
        return st
    return np.array(half(P)[:-1] + half(P[::-1])[:-1])


def inside_strict(P, H):
    """P: (n,2) 点；H: 凸包顶点（逆时针）。严格在里面（容差 1e-9）。"""
    m = len(H)
    if m < 3:
        return np.zeros(len(P), dtype=bool)
    ok = np.ones(len(P), dtype=bool)
    for i in range(m):
        A, B = H[i], H[(i + 1) % m]
        e = B - A
        cr = e[0] * (P[:, 1] - A[1]) - e[1] * (P[:, 0] - A[0])
        ok &= cr > 1e-9
    return ok


def sample_poly(poly, step=0.5):
    lo = poly.min(axis=0)
    hi = poly.max(axis=0)
    xs = np.arange(lo[0], hi[0] + step, step)
    ys = np.arange(lo[1], hi[1] + step, step)
    XX, YY = np.meshgrid(xs, ys)
    P = np.column_stack([XX.ravel(), YY.ravel()])
    m = len(poly)
    keep = np.ones(len(P), dtype=bool)
    for i in range(m):
        A, B = poly[i], poly[(i + 1) % m]
        e = B - A
        cr = e[0] * (P[:, 1] - A[1]) - e[1] * (P[:, 0] - A[0])
        keep &= cr >= 0
    return P[keep]


def r_mec(P, step=1.0):
    """暴力最小包围圆：候选圆心取点集 bbox 外扩后的网格。"""
    if len(P) == 0:
        return np.nan
    lo = P.min(axis=0)
    hi = P.max(axis=0)
    cx = np.arange(lo[0], hi[0] + step, step)
    cy = np.arange(lo[1], hi[1] + step, step)
    best = np.inf
    for x in cx:
        d2 = (P[:, 0] - x) ** 2
        for y in cy:
            r = np.max(np.sqrt(d2 + (P[:, 1] - y) ** 2))
            if r < best:
                best = r
    return best


def run(d, R_eff, n_G=60, n_u=8, seed=0):
    rng = np.random.default_rng(seed)
    P = lattice(d)
    rows = []
    for _ in range(n_G):
        # 源落在圆域内（留出边距，避免退化）
        while True:
            g = rng.uniform(-1, 1, 2) * R_DISK * 0.95
            if np.linalg.norm(g) < R_DISK * 0.9:
                break
        for k in range(n_u):
            psi = 2 * np.pi * k / n_u
            u = np.array([np.cos(psi), np.sin(psi)])
            v = P - g
            dist = np.linalg.norm(v, axis=1)
            in_sector = v @ u >= 0
            in_range = dist <= R_eff
            S = P[in_sector & in_range]
            if len(S) < 2:
                rows.append(dict(nS=len(S), n3=False, dR=np.nan, r0=np.nan, r1=np.nan))
                continue
            # 取离源最近的两点作为交会站（Q3/Q4 的 homing 起点逻辑）
            order = np.argsort(np.linalg.norm(S - g, axis=1))
            S1, S2 = S[order[0]], S[order[1]]
            poly = region_poly(S1, S2, g)
            if poly is None or len(poly) < 3:
                rows.append(dict(nS=len(S), n3=False, dR=np.nan, r0=np.nan, r1=np.nan))
                continue
            Lp = sample_poly(poly, step=0.5)
            if len(Lp) < 5:
                continue
            r0 = r_mec(Lp, step=1.0)
            H = hull(S)
            hole = inside_strict(Lp, H)
            Lp2 = Lp[~hole]
            r1 = r_mec(Lp2, step=1.0) if len(Lp2) >= 5 else np.nan
            rows.append(dict(nS=len(S), n3=(len(S) >= 3), dR=(r0 - r1) if np.isfinite(r1) else np.nan,
                             r0=r0, r1=r1, frac_hole=hole.mean()))
    return rows


def summarize(tag, rows):
    n = len(rows)
    nS = np.array([r["nS"] for r in rows])
    dR = np.array([r["dR"] for r in rows], dtype=float)
    fr = np.array([r.get("frac_hole", 0.0) for r in rows], dtype=float)
    good = np.isfinite(dR)
    pos = good & (dR > 1e-6)
    print(f"--- {tag} ---")
    print(f"  配置数 {n} | |S| 分布: min={nS.min()} 中位={int(np.median(nS))} max={nS.max()} "
          f"| |S|>=3 占 {(nS >= 3).mean() * 100:.1f}%")
    print(f"  R_MEC 可算的配置 {int(good.sum())}")
    if good.sum():
        print(f"  挖洞削减 dR_MEC: 中位={np.median(dR[good]):.4f} m 最大={dR[good].max():.4f} m "
              f"| 正收益(>1e-6) {int(pos.sum())}/{int(good.sum())} = {pos.sum() / good.sum() * 100:.2f}%")
        print(f"  洞内被删的 L 采样点占比: 中位={np.median(fr[good]) * 100:.3f}% 最大={fr[good].max() * 100:.3f}%")
        if pos.sum():
            print(f"  正收益子集的 dR 中位={np.median(dR[pos]):.4f} m 最大={dR[pos].max():.4f} m")


if __name__ == "__main__":
    for d in (1500.0, 1000.0):
        for R_eff in (1000.0, 1500.0):
            summarize(f"d={d:.0f}  R_eff={R_eff:.0f}", run(d, R_eff))
    print()
    print("判读：dR_MEC 中位=0 且正收益占比 <1%  ==> U5-c 收益可忽略，P6 降级为不采纳")

