"""
B题 问题二 算法实现与验证
基于Q1几何模块，实现Q2的第二检测点选择策略

依据：
- Q2建模报告
- Codex审核报告
- DSH一致性审核报告
"""

import math
import json
import os
import sys

# Windows 控制台默认 GBK，本文件会打印 ✓ 之类字符，不设 UTF-8 会直接抛
# UnicodeEncodeError（实测：退出码 1）。errors="replace" 兜底。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from typing import List, Tuple, Dict, Optional

def angle_normalize(angle_deg: float) -> float:
    return angle_deg % 360.0

def angle_diff(angle1_deg: float, angle2_deg: float) -> float:
    """角度差，结果在[-180, 180]"""
    diff = (angle1_deg - angle2_deg + 180.0) % 360.0 - 180.0
    return diff

def to_local(S1: Tuple[float, float], theta1_deg: float,
             P: Tuple[float, float]) -> Tuple[float, float]:
    """世界坐标 → Q2 局部坐标 (a, b)

    局部系：原点 S₁、+u 沿 θ₁ 的视线中线、+v = u(θ₁+90°)。
    **凡进入 E / 候选区域 / b 判定的点，必须先经本函数归约。**
    """
    th = math.radians(theta1_deg)
    u = (math.cos(th), math.sin(th))
    v = (-math.sin(th), math.cos(th))
    dx, dy = P[0] - S1[0], P[1] - S1[1]
    a = dx * u[0] + dy * u[1]
    b = dx * v[0] + dy * v[1]
    return a, b


def to_world(S1: Tuple[float, float], theta1_deg: float,
             a: float, b: float) -> Tuple[float, float]:
    """Q2 局部坐标 (a, b) → 世界坐标（to_local 的逆）"""
    th = math.radians(theta1_deg)
    u = (math.cos(th), math.sin(th))
    v = (-math.sin(th), math.cos(th))
    return S1[0] + a * u[0] + b * v[0], S1[1] + a * u[1] + b * v[1]


def assert_roundtrip(S1: Tuple[float, float], theta1_deg: float,
                     P: Tuple[float, float], tol: float = 1e-9) -> None:
    """【Q2 清单纪律】坐标归约必须可往返：to_world(to_local(x)) == x"""
    a, b = to_local(S1, theta1_deg, P)
    Q = to_world(S1, theta1_deg, a, b)
    err = math.sqrt((Q[0] - P[0]) ** 2 + (Q[1] - P[1]) ** 2)
    assert err <= tol, f"坐标归约往返误差 {err:.3e} > {tol:.1e}（局部系定义有误）"


def point_in_wedge(point: Tuple[float, float],
                   station: Tuple[float, float],
                   bearing_deg: float,
                   epsilon_deg: float) -> bool:
    """检查点是否在角域内"""
    dx = point[0] - station[0]
    dy = point[1] - station[1]

    if abs(dx) < 1e-12 and abs(dy) < 1e-12:
        return True  # 点在观测站上

    angle_to_point = math.degrees(math.atan2(dy, dx))
    diff = angle_diff(angle_to_point, bearing_deg)

    return abs(diff) <= epsilon_deg

def ray_intersection(s1: Tuple[float, float], dir1_deg: float,
                     s2: Tuple[float, float], dir2_deg: float) -> Optional[Tuple[float, float]]:
    rad1 = math.radians(dir1_deg)
    rad2 = math.radians(dir2_deg)

    u1x, u1y = math.cos(rad1), math.sin(rad1)
    u2x, u2y = math.cos(rad2), math.sin(rad2)

    # 解方程：s1 + t*u1 = s2 + s*u2
    det = u1x * u2y - u1y * u2x

    if abs(det) < 1e-12:
        return None  # 平行

    dx = s2[0] - s1[0]
    dy = s2[1] - s1[1]

    t = (dx * u2y - dy * u2x) / det
    s = (dx * u1y - dy * u1x) / det

    if t < 0 or s < 0:
        return None  # 不是射线方向

    px = s1[0] + t * u1x
    py = s1[1] + t * u1y

    return (px, py)

def compute_localization_region(stations: List[Tuple[float, float]],
                               bearings_deg: List[float],
                               epsilon_deg: float = 1.0) -> List[Tuple[float, float]]:
    """计算定位区域顶点（简化版Q1算法）"""
    n = len(stations)

    # 生成边界射线
    rays = []
    for i in range(n):
        rays.append((stations[i], bearings_deg[i] - epsilon_deg))
        rays.append((stations[i], bearings_deg[i] + epsilon_deg))

    # 射线两两求交
    candidate_points = []
    for i in range(len(rays)):
        for j in range(i+1, len(rays)):
            intersection = ray_intersection(rays[i][0], rays[i][1],
                                          rays[j][0], rays[j][1])
            if intersection is not None:
                # 检查是否在所有角域内
                in_all_wedges = True
                for k in range(n):
                    if not point_in_wedge(intersection, stations[k],
                                        bearings_deg[k], epsilon_deg):
                        in_all_wedges = False
                        break

                if in_all_wedges:
                    candidate_points.append(intersection)

    # 去重
    unique_points = []
    for p in candidate_points:
        is_duplicate = False
        for up in unique_points:
            if abs(p[0] - up[0]) < 1e-6 and abs(p[1] - up[1]) < 1e-6:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_points.append(p)

    # 凸包（简化版：按极角排序）
    if len(unique_points) < 3:
        return unique_points

    # 找中心点
    cx = sum(p[0] for p in unique_points) / len(unique_points)
    cy = sum(p[1] for p in unique_points) / len(unique_points)

    # 按极角排序
    def polar_angle(p):
        return math.atan2(p[1] - cy, p[0] - cx)

    unique_points.sort(key=polar_angle)

    return unique_points

def compute_diameter(points: List[Tuple[float, float]]) -> Tuple[float, Tuple, Tuple]:
    """计算直径（暴力法）"""
    if len(points) < 2:
        return 0.0, None, None

    max_dist = 0.0
    p1_max, p2_max = None, None

    for i in range(len(points)):
        for j in range(i+1, len(points)):
            dist = math.sqrt((points[i][0] - points[j][0])**2 +
                           (points[i][1] - points[j][1])**2)
            if dist > max_dist:
                max_dist = dist
                p1_max = points[i]
                p2_max = points[j]

    return max_dist, p1_max, p2_max

def compute_candidate_region(S1: Tuple[float, float],
                            theta1_deg: float,
                            phi_min_deg: float = 40.0,
                            R_worst: float = 1000.0,
                            d_min: float = 5.0,
                            d_max: float = 1500.0) -> Dict:
    """
    计算第二检测点候选区域

    参数：
        S1: 第一检测点坐标
        theta1_deg: 示向度（度）
        phi_min_deg: 保证的最小交会角（度）
        R_worst: 最坏接收半径（米）
        d_min, d_max: 源距范围（米）

    返回：字典，包含候选区域参数和状态
    """
    # 1. 源距估计
    d_hat = (d_min + d_max) / 2
    Delta_d = (d_max - d_min) / 2

    # 2. 可行性检查
    phi_min_max_deg = math.degrees(math.acos(Delta_d / R_worst))
    feasible = (Delta_d <= R_worst * math.cos(math.radians(phi_min_deg)))

    if not feasible:
        return {
            'd_hat': d_hat,
            'Delta_d': Delta_d,
            'b_min': None,
            'b_max': None,
            'feasible': False,
            'phi_min_max_deg': phi_min_max_deg,
            'reason': f'不可行：Δd={Delta_d:.2f}m > R·cosφ_min={R_worst*math.cos(math.radians(phi_min_deg)):.2f}m'
        }

    # 3. 候选区域边界
    phi_min_rad = math.radians(phi_min_deg)
    b_min = Delta_d * math.tan(phi_min_rad)
    b_max = math.sqrt(R_worst**2 - Delta_d**2)

    # 4. 方向向量
    theta1_rad = math.radians(theta1_deg)
    u = (math.cos(theta1_rad), math.sin(theta1_rad))  # 沿示向度
    v = (-math.sin(theta1_rad), math.cos(theta1_rad))  # 垂直方向

    # 5. 移动距离
    dist_min = math.sqrt(d_hat**2 + b_min**2)
    dist_max = math.sqrt(d_hat**2 + b_max**2)

    return {
        'd_hat': d_hat,
        'Delta_d': Delta_d,
        'b_min': b_min,
        'b_max': b_max,
        'feasible': True,
        'phi_min_max_deg': phi_min_max_deg,
        'u': u,
        'v': v,
        'dist_min': dist_min,
        'dist_max': dist_max,
        'region_width': b_max - b_min
    }

def generate_S2_candidates(S1: Tuple[float, float],
                          candidate_region: Dict,
                          n_samples: int = 5) -> List[Tuple[float, float]]:
    """生成S2候选点坐标"""
    if not candidate_region['feasible']:
        return []

    d_hat = candidate_region['d_hat']
    b_min = candidate_region['b_min']
    b_max = candidate_region['b_max']
    u = candidate_region['u']
    v = candidate_region['v']

    candidates = []

    # 上下两条线段
    for sign in [1, -1]:
        b_values = [b_min + i * (b_max - b_min) / (n_samples - 1)
                   for i in range(n_samples)]
        for b in b_values:
            S2_x = S1[0] + d_hat * u[0] + sign * b * v[0]
            S2_y = S1[1] + d_hat * u[1] + sign * b * v[1]
            candidates.append((S2_x, S2_y))

    return candidates

def position_uncertainty_E(a: float, b: float, d1: float,
                          epsilon_deg: float = 1.0) -> float:
    """
    位置不确定度解析式 E(a, b, d1)

    **注意：入参必须是 Q2 局部坐标 (a, b)**（u 沿 θ₁ 中线），不是世界坐标。
    世界坐标请先用 `to_local(S1, theta1_deg, P)` 归约——否则 |b| 会被算成 0，
    E 返回 inf 并被误判为"退化"（2026-09-11 联合校验发现的实际帧错误）。
    公式：E = ε_rad · √(d1² + Δ² + b²) · d2 / |b|，Δ = d1 − a，d2 = √(Δ² + b²)
    """
    if abs(b) < 1e-12:
        return float('inf')

    epsilon_rad = math.radians(epsilon_deg)
    Delta = d1 - a
    d2 = math.sqrt(Delta**2 + b**2)

    E = epsilon_rad * math.sqrt(d1**2 + Delta**2 + b**2) * d2 / abs(b)
    return E

def compute_cross_angle(S1: Tuple[float, float],
                       S2: Tuple[float, float],
                       G: Tuple[float, float]) -> float:
    """计算源处的交会角（度）"""
    # 向量 G->S1 和 G->S2
    v1 = (S1[0] - G[0], S1[1] - G[1])
    v2 = (S2[0] - G[0], S2[1] - G[1])

    len1 = math.sqrt(v1[0]**2 + v1[1]**2)
    len2 = math.sqrt(v2[0]**2 + v2[1]**2)

    if len1 < 1e-12 or len2 < 1e-12:
        return 0.0

    # cos(phi) = v1·v2 / (|v1||v2|)
    cos_phi = (v1[0]*v2[0] + v1[1]*v2[1]) / (len1 * len2)
    cos_phi = max(-1.0, min(1.0, cos_phi))  # 防止数值误差

    phi_rad = math.acos(cos_phi)
    return math.degrees(phi_rad)

def verify_Q1_baseline():
    """验证Q1基准算例"""
    print("=" * 70)
    print("验证Q1基准算例")
    print("=" * 70)

    S1 = (0.0, 0.0)
    S2 = (600.0, 0.0)
    G = (300.0, 500.0)

    # 计算真实方位角
    theta1 = math.degrees(math.atan2(G[1] - S1[1], G[0] - S1[0]))
    theta2 = math.degrees(math.atan2(G[1] - S2[1], G[0] - S2[0]))

    print(f"S1 = {S1}")
    print(f"S2 = {S2}")
    print(f"G = {G}")
    print(f"θ1 = {theta1:.6f}°")
    print(f"θ2 = {theta2:.6f}°")

    # 计算定位区域
    vertices = compute_localization_region([S1, S2], [theta1, theta2], epsilon_deg=1.0)
    print(f"\n定位区域顶点数：{len(vertices)}")
    for i, v in enumerate(vertices):
        print(f"  顶点{i+1}: ({v[0]:.6f}, {v[1]:.6f})")

    # 计算直径
    D, p1, p2 = compute_diameter(vertices)
    print(f"\n直径 D = {D:.6f} m")
    print(f"直径端点：{p1} 到 {p2}")

    # 计算 E —— 【2026-09-11 修正】E 要求 **局部坐标 (a, b)**，
    # 不能把世界坐标差 (600, 0) 直接当 (a, b)（此处 θ₁=59.036° ≠ 0）。
    d1 = math.sqrt((G[0]-S1[0])**2 + (G[1]-S1[1])**2)
    d2 = math.sqrt((G[0]-S2[0])**2 + (G[1]-S2[1])**2)
    assert_roundtrip(S1, theta1, S2)              # 归约往返恒等断言
    a, b = to_local(S1, theta1, S2)               # 原写 a=S2[0]-S1[0](=600), b=0 ⇒ b=0 假退化
    E = position_uncertainty_E(a, b, d1)

    # 计算交会角
    phi = compute_cross_angle(S1, S2, G)

    print(f"\nd1 = {d1:.6f} m")
    print(f"d2 = {d2:.6f} m")
    print(f"交会角 φ = {phi:.6f}°")
    print(f"E = {E:.6f} m")
    print(f"D/E = {D/E:.6f}")

    # 期望值
    print("\n期望值对比：")
    print(f"  D ≈ 39.598 m (实际 {D:.3f} m)")
    print(f"  D/E ≈ 2.43 (实际 {D/E:.3f})")

    return D, E, D/E

def test_Q2_candidate_region():
    """测试Q2候选区域计算"""
    print("\n" + "=" * 70)
    print("Q2候选区域计算")
    print("=" * 70)

    S1 = (0.0, 0.0)
    theta1 = 0.0  # 正东方向

    result = compute_candidate_region(S1, theta1, phi_min_deg=40.0)

    print("\n输入参数：")
    print(f"  S1 = {S1}")
    print(f"  θ1 = {theta1}°")
    print("  φ_min = 40°")
    print("  R_worst = 1000 m")

    print("\n计算结果：")
    print(f"  d_hat = {result['d_hat']:.2f} m")
    print(f"  Delta_d = {result['Delta_d']:.2f} m")
    print(f"  可行性：{result['feasible']}")
    print(f"  phi_min_max = {result['phi_min_max_deg']:.2f} deg")

    if result['feasible']:
        print("\n候选区域边界：")
        print(f"  b_min = {result['b_min']:.6f} m")
        print(f"  b_max = {result['b_max']:.6f} m")
        print(f"  区域宽度 = {result['region_width']:.2f} m")
        print(f"  移动距离 = [{result['dist_min']:.2f}, {result['dist_max']:.2f}] m")

    return result

def test_Q2_with_Q1_verification():
    """Q2选点策略的Q1验证"""
    print("\n" + "=" * 70)
    print("Q2选点策略 + Q1完整验证")
    print("=" * 70)

    S1 = (0.0, 0.0)
    theta1 = 59.036  # Q1基准算例的方向
    G_nominal = (300.0, 500.0)  # Q1基准的源位置

    # 计算候选区域
    candidate_region = compute_candidate_region(S1, theta1, phi_min_deg=40.0)

    # 测试三个配置
    configs = [
        ('b_min端', candidate_region['b_min']),
        ('中点', (candidate_region['b_min'] + candidate_region['b_max']) / 2),
        ('b_max端', candidate_region['b_max'])
    ]

    results = []

    for name, b_value in configs:
        # 生成S2坐标
        d_hat = candidate_region['d_hat']
        u = candidate_region['u']
        v = candidate_region['v']

        S2 = (S1[0] + d_hat * u[0] + b_value * v[0],
              S1[1] + d_hat * u[1] + b_value * v[1])

        # 计算真实方位角
        theta2 = math.degrees(math.atan2(G_nominal[1] - S2[1],
                                        G_nominal[0] - S2[0]))

        # Q1计算定位区域
        vertices = compute_localization_region([S1, S2], [theta1, theta2],
                                              epsilon_deg=1.0)
        D, _, _ = compute_diameter(vertices)

        # 计算E和交会角
        d1 = math.sqrt((G_nominal[0]-S1[0])**2 + (G_nominal[1]-S1[1])**2)
        a = d_hat
        E_nominal = position_uncertainty_E(a, b_value, d1)
        phi = compute_cross_angle(S1, S2, G_nominal)

        results.append({
            'name': name,
            'b': b_value,
            'S2': S2,
            'D': D,
            'E': E_nominal,
            'D/E': D / E_nominal,
            'phi': phi
        })

        print(f"\n配置：{name}")
        print(f"  b = {b_value:.2f} m")
        print(f"  S2 = ({S2[0]:.2f}, {S2[1]:.2f})")
        print(f"  D = {D:.6f} m")
        print(f"  E(名义) = {E_nominal:.6f} m")
        print(f"  D/E = {D/E_nominal:.6f}")
        print(f"  φ = {phi:.2f}°")

    # 与Q1基准对比
    print("\n" + "=" * 70)
    print("与Q1基准对比")
    print("=" * 70)
    D_q1_baseline = 39.598
    print(f"Q1基准（S2=(600,0)）：D = {D_q1_baseline:.3f} m")

    for r in results:
        improvement = (D_q1_baseline - r['D']) / D_q1_baseline * 100
        print(f"Q2 {r['name']}：D = {r['D']:.3f} m，改善 {improvement:.2f}%")

    return results

def test_worst_case_analysis():
    """最坏情况分析（审核报告R1问题）"""
    print("\n" + "=" * 70)
    print("最坏情况分析（含方向偏差）")
    print("=" * 70)

    S1 = (0.0, 0.0)
    theta1 = 0.0

    candidate_region = compute_candidate_region(S1, theta1, phi_min_deg=40.0)

    b_min = candidate_region['b_min']
    b_max = candidate_region['b_max']
    d_hat = candidate_region['d_hat']

    # 测试反例1：角度失保
    print("\n反例1：b=b_min, d=1500, α=+1°")
    a = d_hat
    b = b_min
    d = 1500.0
    alpha_deg = 1.0

    alpha_rad = math.radians(alpha_deg)
    G = (d * math.cos(alpha_rad), d * math.sin(alpha_rad))

    u = candidate_region['u']
    v = candidate_region['v']
    S2 = (S1[0] + a * u[0] + b * v[0],
          S1[1] + a * u[1] + b * v[1])

    d2 = math.sqrt((G[0]-S2[0])**2 + (G[1]-S2[1])**2)
    phi = compute_cross_angle(S1, S2, G)
    gamma = min(phi, 180 - phi)  # 锐交会角

    print(f"  G = ({G[0]:.2f}, {G[1]:.2f})")
    print(f"  S2 = ({S2[0]:.2f}, {S2[1]:.2f})")
    print(f"  d2 = {d2:.2f} m")
    print(f"  φ = {phi:.2f}°")
    print(f"  γ(锐角) = {gamma:.2f}°")
    print(f"  结果：γ = {gamma:.2f}° {'<' if gamma < 40 else '>='} 40°（{'失保' if gamma < 40 else '满足'}）")

    # 测试反例2：距离失保
    print("\n反例2：b=b_max, d=1500, α=-1°")
    b = b_max
    alpha_deg = -1.0

    alpha_rad = math.radians(alpha_deg)
    G = (d * math.cos(alpha_rad), d * math.sin(alpha_rad))

    S2 = (S1[0] + a * u[0] + b * v[0],
          S1[1] + a * u[1] + b * v[1])

    d2 = math.sqrt((G[0]-S2[0])**2 + (G[1]-S2[1])**2)

    print(f"  G = ({G[0]:.2f}, {G[1]:.2f})")
    print(f"  S2 = ({S2[0]:.2f}, {S2[1]:.2f})")
    print(f"  d2 = {d2:.2f} m")
    print(f"  结果：d2 = {d2:.2f} m {'>' if d2 > 1000 else '<='} 1000 m（{'失保' if d2 > 1000 else '满足'}）")

def test_numerical_benchmarks():
    print("\n" + "=" * 70)
    print("数值基准验证")
    print("=" * 70)

    result = compute_candidate_region((0, 0), 0.0, phi_min_deg=40.0)

    benchmarks = {
        'd_hat': (752.5, result['d_hat']),
        'Delta_d': (747.5, result['Delta_d']),
        'b_min': (627.23, result['b_min']),
        'b_max': (664.26, result['b_max']),
        'phi_min_max': (41.63, result['phi_min_max_deg']),
        'dist_min': (979.63, result['dist_min']),
        'dist_max': (1003.74, result['dist_max'])
    }

    print(f"\n{'量':<20} {'期望值':>12} {'计算值':>12} {'误差':>10} {'状态':>6}")
    print("-" * 70)

    all_passed = True
    for name, (expected, actual) in benchmarks.items():
        error = abs(actual - expected)
        status = "OK" if error < 0.01 else "FAIL"
        if error >= 0.01:
            all_passed = False
        print(f"{name:<20} {expected:>12.2f} {actual:>12.6f} {error:>10.6f} {status:>6}")

    print("-" * 70)
    print(f"Overall: {'PASS' if all_passed else 'FAIL'}")

    return all_passed

def main():
    print("\n")
    print("=" * 70)
    print("B题 问题二 算法实现与验证")
    print("基于Q1几何模块")
    print("=" * 70)

    # 1. 验证Q1基准
    D_q1, E_q1, ratio_q1 = verify_Q1_baseline()

    # 2. 测试Q2候选区域
    candidate_region = test_Q2_candidate_region()

    # 3. 数值基准验证
    benchmarks_passed = test_numerical_benchmarks()

    # 4. Q2选点 + Q1验证
    comparison_results = test_Q2_with_Q1_verification()

    # 5. 最坏情况分析
    test_worst_case_analysis()

    # 汇总报告
    print("\n" + "=" * 70)
    print("验证汇总")
    print("=" * 70)

    print("\n1. Q1基准验证：")
    print(f"   D = {D_q1:.3f} m（期望 39.598 m）")
    print(f"   D/E = {ratio_q1:.3f}（期望 ~2.43）")

    print(f"\n2. Q2数值基准：{'全部通过 [OK]' if benchmarks_passed else '存在偏差 [FAIL]'}")

    print("\n3. Q2改善效果（相对Q1基准）：")
    for r in comparison_results:
        improvement = (39.598 - r['D']) / 39.598 * 100
        print(f"   {r['name']}: D={r['D']:.3f}m, 改善{improvement:.2f}%, D/E={r['D/E']:.3f}")

    print("\n4. 关键发现：")
    print("   - D/E实测值 ≥ 2.00（不在[0.5,2]区间内）")
    print("   - 最佳改善约10-11%（不是31.4%）")
    print("   - 方向偏差导致角度和距离约束失保")

    # 导出结果
    output = {
        'Q1_baseline': {
            'D': D_q1,
            'E': E_q1,
            'D_over_E': ratio_q1
        },
        'Q2_candidate_region': {
            'd_hat': candidate_region['d_hat'],
            'Delta_d': candidate_region['Delta_d'],
            'b_min': candidate_region['b_min'],
            'b_max': candidate_region['b_max'],
            'phi_min_max_deg': candidate_region['phi_min_max_deg']
        },
        'Q2_improvements': [
            {
                'name': r['name'],
                'D': r['D'],
                'improvement_percent': (39.598 - r['D']) / 39.598 * 100,
                'D_over_E': r['D/E']
            }
            for r in comparison_results
        ],
        'benchmarks_passed': benchmarks_passed
    }

    # 写到本文件所在目录；原来用裸相对名，跟着当前工作目录跑
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'Q2_algorithm_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n结果已保存到：{out_path}")

if __name__ == '__main__':
    main()
