# -*- coding: utf-8 -*-
"""
DSH 节点 · 维度6（一致性）独立核验脚本
目的：
  1) 独立复算 Q1 基准算例的 D（校验本脚本管线与 Q1 权威值 39.598 一致）
  2) 复算"跨问交叉验证 39.60→27.15"所用的 S2=(741.19,235.29) 配置
  3) 用 Q2 自己的选点规则（a=d_hat, b∈[b_min,b_max]）真正代入 Q1 算例，给出诚实数字
  4) 复算 D/E 比值，对照 Q2 报告断言6 的 [0.5,2] 带
纯标准库实现（环境无 numpy）。几何口径：角域=±1° 闭楔形（射线族），不截断目标圆域。
"""
import json
import math

EPS = math.radians(1.0)
D_HAT = 752.5
D_DELTA = 747.5
B_MIN = D_DELTA * math.tan(math.radians(40.0))
B_MAX = math.sqrt(1000.0 ** 2 - D_DELTA ** 2)


def u(theta):
    return (math.cos(theta), math.sin(theta))


def cross(d, p, S):
    return d[0] * (p[1] - S[1]) - d[1] * (p[0] - S[0])


def clip(poly, d, S):
    """保留 cross(d, p-S) >= 0 的部分（Sutherland-Hodgman）"""
    out = []
    n = len(poly)
    for i in range(n):
        A, B = poly[i], poly[(i + 1) % n]
        ca, cb = cross(d, A, S), cross(d, B, S)
        if ca >= 0:
            out.append(A)
        if (ca > 0 and cb < 0) or (ca < 0 and cb > 0):
            t = ca / (ca - cb)
            out.append((A[0] + t * (B[0] - A[0]), A[1] + t * (B[1] - A[1])))
    return out


def localization_region(S_list, theta_list, eps=EPS, half=20000.0):
    poly = [(-half, -half), (half, -half), (half, half), (-half, half)]
    for S, th in zip(S_list, theta_list):
        poly = clip(poly, u(th - eps), S)
        poly = clip(poly, (-u(th + eps)[0], -u(th + eps)[1]), S)
    return poly


def diameter(poly):
    best, pair = 0.0, None
    for i in range(len(poly)):
        for j in range(i + 1, len(poly)):
            d = math.dist(poly[i], poly[j])
            if d > best:
                best, pair = d, (poly[i], poly[j])
    return best, pair


def measure(S1, S2, G):
    """返回 (D, phi_deg, d1, d2, E, D/E)"""
    th1 = math.atan2(G[1] - S1[1], G[0] - S1[0])
    th2 = math.atan2(G[1] - S2[1], G[0] - S2[0])
    poly = localization_region([S1, S2], [th1, th2])
    D, _ = diameter(poly)
    d1 = math.dist(S1, G)
    d2 = math.dist(S2, G)
    # G 处视线夹角
    v1 = (S1[0] - G[0], S1[1] - G[1])
    v2 = (S2[0] - G[0], S2[1] - G[1])
    c = (v1[0] * v2[0] + v1[1] * v2[1]) / (math.hypot(*v1) * math.hypot(*v2))
    c = max(-1.0, min(1.0, c))
    phi = math.acos(c)
    E = EPS * math.hypot(d1, d2) / math.sin(phi) if math.sin(phi) > 1e-15 else float("inf")
    return dict(D=D, phi_deg=math.degrees(phi), d1=d1, d2=d2, E=E, D_over_E=D / E,
                vertices=len(poly))


def q2_rule_S2(theta1, a, b):
    """Q2 参数化：S2 = S1 + a*u + b*v （S1 取原点）"""
    ux, uy = u(theta1)
    return (a * ux - b * uy, a * uy + b * ux)


if __name__ == "__main__":
    res = {}

    # --- 1) Q1 基准算例（管线自检，权威值 D=39.598） ---
    S1, S2q1, G = (0.0, 0.0), (600.0, 0.0), (300.0, 500.0)
    r = measure(S1, S2q1, G)
    res["q1_baseline"] = r
    assert abs(r["D"] - 39.598) < 0.02, r["D"]

    # --- 2) 跨问交叉验证所用配置 S2=(741.19,235.29)（Δ=d1-a=0，a=真 d1） ---
    r2 = measure(S1, (741.19, 235.29), G)
    res["crossval_S2_741_235"] = r2

    # --- 3) 真·Q2 规则代入 Q1 算例：a=d_hat=752.5，b∈[b_min,b_max] ---
    theta1 = math.atan2(500.0, 300.0)
    honest = {}
    for name, b in (("b_min", B_MIN), ("b_max", B_MAX), ("b=514.5(越界)", 514.5)):
        S2 = q2_rule_S2(theta1, D_HAT, b)
        rr = measure(S1, S2, G)
        rr["S2"] = S2
        # 鲁棒性检查：对 d1∈(5,1500] 的 Δ 范围
        Deltas = [abs(d - D_HAT) for d in (5.0, 1500.0)]
        rr["d2_max_over_delta"] = max(math.hypot(dd, b) for dd in Deltas)
        rr["phi_min_over_delta_deg"] = min(math.degrees(math.asin(b / math.hypot(dd, b))) for dd in Deltas)
        honest[name] = rr
    res["q2_rule_on_q1_example"] = honest

    # --- 4) Q2 名义算例的 D/E（断言6 用） ---
    nom = {}
    for name, b in (("b_min", B_MIN), ("b_max", B_MAX)):
        S2 = q2_rule_S2(0.0, D_HAT, b)
        # 真源取 d1=d_hat（Δ=0），G=(752.5,0)
        rr = measure((0.0, 0.0), S2, (D_HAT, 0.0))
        rr["S2"] = S2
        nom[name] = rr
        # 远源 d1=1500 的 D/E
        G2 = (1500.0, 0.0)
        rr2 = measure((0.0, 0.0), S2, G2)
        rr2["S2"] = S2
        nom[name + "_d1500"] = rr2
    res["q2_nominal"] = nom

    res["constants"] = dict(b_min=B_MIN, b_max=B_MAX, d_hat=D_HAT, Delta_d=D_DELTA,
                            rho_band_assert6=[0.5, 2.0], q1_documented_D_over_E=2.43)

    print(json.dumps(res, ensure_ascii=False, indent=2))
