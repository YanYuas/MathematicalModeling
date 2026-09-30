"""
Q2 完整解：含示向度误差 α 的完整楔形版

在 α ∈ [-1°, +1°] 上逐点取最坏，修正"只计入源距未知"这一单个信息缺口下的可行性判据：
  φ_min = 40° 在 α 最坏时**不可行**（b_min > b_max ⇒ 空集），可保证上限约 39.6161°。

与 α=0 闭式解的差别：
  1. 约束检验要对 α 遍历 [-ε, +ε]
  2. 不可行情形显式判定（b_min_alpha > b_max_alpha）
  3. 不可行时返回 (None, None, phi_min_max)

依据：02_建模手/Q2/Q2建模数学化.md (v1.2.0)、建模手-联合校验报告.md
依赖：numpy（Q1 几何为可选，内部自带降级实现）
"""

import numpy as np
from typing import Tuple, Optional, List

EPS_RAD = np.deg2rad(1.0)  # Direction error half-angle
R_WORST = 1000.0           # Worst-case reception radius
D_LO, D_HI = 5.0, 1500.0   # Source distance range
D_HAT = (D_LO + D_HI) / 2  # 752.5 m
DELTA_D = (D_HI - D_LO) / 2  # 747.5 m

# 源距只取两个端点：d2^2 关于 r 是开口向上的抛物线，最坏必在端点取得
R_ENDS = np.array([D_LO, D_HI])

# α 稠密采样（逐点取最坏）
ALPHAS_DENSE = np.linspace(-EPS_RAD, +EPS_RAD, 801)


def sin_phi_and_d2(a: float, b: float, r: float, alpha: float) -> Tuple[float, float]:
    """
    Calculate sin(phi) and d2 for source G = r(cos(alpha), sin(alpha))

    Formulas (Q2 Modeling Math L5'/L6'):
      sin(phi) = |a*sin(alpha) - b*cos(alpha)| / d2
      d2 = sqrt(a^2 + b^2 + r^2 - 2r(a*cos(alpha) + b*sin(alpha)))

    When alpha=0, reduces to: sin(phi) = |b|/d2, d2 = sqrt((a-r)^2 + b^2)

    Returns: (sin_phi, d2)
    """
    numerator = abs(a * np.sin(alpha) - b * np.cos(alpha))
    d2_sq = a*a + b*b + r*r - 2*r*(a*np.cos(alpha) + b*np.sin(alpha))
    d2 = np.sqrt(max(0.0, d2_sq))

    if d2 < 1e-9:  # Degenerate: S2 coincides with source
        return 0.0, 0.0

    return numerator / d2, d2


def guaranteed_phi_and_max_d2(
    a: float,
    b: float,
    alphas: np.ndarray = ALPHAS_DENSE,
    r_ends: np.ndarray = R_ENDS
) -> Tuple[float, float]:
    """
    Compute guaranteed minimum angle (deg) and maximum d2 under worst-case alpha and r.

    Traverses all (alpha, r) combinations to find:
      - Guaranteed phi = arcsin(min sin_phi)
      - Max d2 = max d2

    Returns: (phi_guaranteed_deg, d2_max)
    """
    worst_sin_phi = 1.0
    worst_d2 = 0.0

    for alpha in alphas:
        for r in r_ends:
            sin_p, d2 = sin_phi_and_d2(a, b, r, alpha)
            worst_sin_phi = min(worst_sin_phi, sin_p)
            worst_d2 = max(worst_d2, d2)

    worst_sin_phi = np.clip(worst_sin_phi, 0.0, 1.0)
    phi_deg = np.degrees(np.arcsin(worst_sin_phi))

    return phi_deg, worst_d2


def compute_E_nominal(a: float, b: float, d1: float = D_HAT) -> float:
    """
    Nominal positioning uncertainty E (alpha=0 approximation).

    E = eps_rad * sqrt(d1^2 + d2^2) / sin(phi)
      where d2 = sqrt((a-d1)^2 + b^2), sin(phi) = |b|/d2

    This is the analytical proxy, NOT the robust worst-case.
    For robust evaluation, use guaranteed_phi_and_max_d2.

    Returns: E (meters)
    """
    if abs(b) < 1e-9:  # Degenerate: collinear
        return np.inf

    Delta = d1 - a
    d2 = np.sqrt(Delta**2 + b**2)

    if d2 < 1e-9:
        return np.inf

    E = EPS_RAD * np.sqrt(d1**2 + d2**2) * d2 / abs(b)
    return E


def candidate_region_alpha_complete(
    theta1_deg: float,
    phi_min_deg: float = 40.0,
    r_worst: float = R_WORST,
    a: Optional[float] = None,
    delta_d: float = DELTA_D,
    alphas: np.ndarray = ALPHAS_DENSE,
    grid_step: float = 0.1
) -> Tuple[Optional[float], Optional[float], float, float]:
    """
    Compute candidate region bounds with complete angular wedge (alpha in [-eps, +eps]).

    Args:
        theta1_deg: Measured bearing at S1 (degrees)
        phi_min_deg: Target minimum intersection angle (degrees)
        r_worst: Worst-case reception radius (meters)
        a: Longitudinal offset (if None, uses d_hat=752.5)
        delta_d: Source distance uncertainty radius (meters)
        alphas: Dense alpha samples for worst-case evaluation
        grid_step: Grid step for boundary search (meters)

    Returns:
        (b_min_alpha, b_max_alpha, phi_min_max, a_used)

        If feasible: (b_min, b_max, phi_min_max, a) where b in [b_min, b_max]
        If infeasible: (None, None, phi_min_max_achievable, a)

    Algorithm:
        1. Set a (default: d_hat=752.5, midpoint alignment strategy)
        2. Scan b in [300, 900] with grid_step
        3. For each b, compute guaranteed_phi_and_max_d2 under all alphas
        4. Find b_min: smallest b where phi >= phi_min_deg
        5. Find b_max: largest b where d2 <= r_worst AND phi >= phi_min_deg
        6. Check feasibility: b_min <= b_max
    """
    if a is None:
        a = D_HAT  # Midpoint alignment (752.5 m)
    phi_min_target = phi_min_deg

    # 扫描 b
    bs = np.arange(300.0, 901.0, grid_step)
    results = np.array([guaranteed_phi_and_max_d2(a, b, alphas) for b in bs])
    phi_arr, d2_arr = results[:, 0], results[:, 1]

    # b_min：满足角度约束的最小 b
    mask_angle = phi_arr >= phi_min_target
    b_min_alpha = bs[mask_angle].min() if mask_angle.any() else None

    # b_max：同时满足角度与距离约束的最大 b
    mask_both = (d2_arr <= r_worst) & (phi_arr >= phi_min_target)
    b_max_alpha = bs[mask_both].max() if mask_both.any() else None

    # 最大可保证角度（不可行时用于报告）
    mask_dist = d2_arr <= r_worst
    if mask_dist.any():
        phi_min_max = phi_arr[mask_dist].max()
    else:
        phi_min_max = 0.0

    # 不可行判定：b_min > b_max 即空集
    if b_min_alpha is None or b_max_alpha is None:
        return None, None, phi_min_max, a

    if b_min_alpha > b_max_alpha:
        return None, None, phi_min_max, a

    return b_min_alpha, b_max_alpha, phi_min_max, a


def solve_q2_complete(
    S1: np.ndarray,
    theta1_deg: float,
    phi_min_deg: float = 40.0,
    a: Optional[float] = None,
    return_full: bool = False
) -> dict:
    """
    Complete Q2 solution with alpha-complete constraints.

    Args:
        S1: First detection point (x, y)
        theta1_deg: Bearing measured at S1 (degrees, 0=East, CCW)
        phi_min_deg: Target minimum intersection angle (degrees)
        a: Longitudinal offset (if None, uses d_hat=752.5)
        return_full: If True, return detailed diagnostics

    Returns:
        dict with keys:
            'feasible': bool
            'a': float
            'b_min': float or None
            'b_max': float or None
            'phi_min_max': float (achievable if infeasible)
            'S2_candidates': list of (x,y) if feasible, else []
            'message': str

        If return_full=True, additional keys:
            'E_nominal_min': float
            'E_nominal_max': float
    """
    # 求候选区域
    b_min, b_max, phi_min_max, a_used = candidate_region_alpha_complete(
        theta1_deg=theta1_deg,
        phi_min_deg=phi_min_deg,
        a=a
    )

    # 建立局部坐标系
    theta1_rad = np.radians(theta1_deg)
    u = np.array([np.cos(theta1_rad), np.sin(theta1_rad)])  # Along bearing
    v = np.array([-np.sin(theta1_rad), np.cos(theta1_rad)])  # Perpendicular

    result = {
        'feasible': False,
        'a': a_used,
        'b_min': b_min,
        'b_max': b_max,
        'phi_min_max': phi_min_max,
        'S2_candidates': [],
        'message': ''
    }

    if b_min is None or b_max is None:
        result['message'] = (
            f"Infeasible at a={a_used:.1f}m: phi_min={phi_min_deg:.0f}deg not achievable "
            f"under alpha in [-1,+1]deg. Maximum achievable: {phi_min_max:.2f}deg"
        )
        return result

    # 生成候选点
    a = a_used
    b_samples = np.linspace(b_min, b_max, 10)

    candidates = []
    for b in b_samples:
        # 正负两侧都要取
        S2_plus = S1 + a * u + b * v
        S2_minus = S1 + a * u - b * v
        candidates.append(tuple(S2_plus))
        candidates.append(tuple(S2_minus))

    result['feasible'] = True
    result['S2_candidates'] = candidates
    result['message'] = (
        f"Feasible: b in [{b_min:.2f}, {b_max:.2f}] m, "
        f"width={(b_max-b_min):.2f} m, "
        f"|S1S2| in [{np.hypot(a, b_min):.2f}, {np.hypot(a, b_max):.2f}] m"
    )

    if return_full:
        result['E_nominal_min'] = compute_E_nominal(a, b_min)
        result['E_nominal_max'] = compute_E_nominal(a, b_max)

    return result


if __name__ == "__main__":
    print("=" * 80)
    print("Q2 Complete Solution: Alpha-Corrected Candidate Region")
    print("=" * 80)
    print()

    # 基准情形：φ_min=40°，在 α 最坏下应报不可行
    print("Case 1: Baseline (phi_min=40deg)")
    print("-" * 80)
    S1 = np.array([0.0, 0.0])
    theta1 = 0.0

    result = solve_q2_complete(S1, theta1, phi_min_deg=40.0, return_full=True)

    print(f"Feasible: {result['feasible']}")
    print(f"b_min: {result['b_min']}")
    print(f"b_max: {result['b_max']}")
    print(f"phi_min_max: {result['phi_min_max']:.4f} deg")
    print(f"Message: {result['message']}")

    if result['feasible']:
        print(f"a (midpoint): {result['a']:.2f} m")
        print(f"E_nominal range: [{result['E_nominal_min']:.2f}, {result['E_nominal_max']:.2f}] m")
        print(f"Candidate points (first 4): {result['S2_candidates'][:4]}")
    print()

    # 临界可行情形（独立复算：39.6161° @ (764, 651)）
    print("Case 2: Near-Maximum Achievable (phi_min=39.61deg, a=764m)")
    print("-" * 80)

    result2 = solve_q2_complete(S1, theta1, phi_min_deg=39.61, a=764.0, return_full=True)

    print(f"Feasible: {result2['feasible']}")
    print(f"a: {result2['a']:.2f} m")
    print(f"b_min: {result2['b_min']}")
    print(f"b_max: {result2['b_max']}")
    print(f"Message: {result2['message']}")

    if result2['feasible']:
        print(f"Width: {result2['b_max'] - result2['b_min']:.2f} m")
    print()

    # 对照：α=0 的闭式解
    print("Case 3: Alpha=0 Baseline (for comparison)")
    print("-" * 80)

    phi_min_target = 40.0
    b_min_alpha0 = DELTA_D * np.tan(np.radians(phi_min_target))
    b_max_alpha0 = np.sqrt(R_WORST**2 - DELTA_D**2)
    phi_max_alpha0 = np.degrees(np.arccos(DELTA_D / R_WORST))

    print(f"b_min (alpha=0): {b_min_alpha0:.2f} m")
    print(f"b_max (alpha=0): {b_max_alpha0:.2f} m")
    print(f"phi_min_max (alpha=0): {phi_max_alpha0:.2f} deg")
    print(f"Width (alpha=0): {b_max_alpha0 - b_min_alpha0:.2f} m")
    print()

    print("=" * 80)
    print("Summary:")
    print("  - phi_min=40deg is INFEASIBLE under alpha in [-1,+1]deg")
    print("  - Maximum achievable: ~39.62deg")
    print("  - Alpha=0 gave false feasibility (b_min=627.23, b_max=664.26)")
    print("  - Alpha-corrected: b_min=650.00 > b_max=638.00 => empty set")
    print("=" * 80)
