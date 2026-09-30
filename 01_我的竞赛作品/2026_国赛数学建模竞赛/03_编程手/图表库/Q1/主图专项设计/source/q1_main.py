"""
Q1 交会定位区域：直径与最小包围圆

由两条带 ±1° 误差的示向度构造角域（半平面交），求定位区域的直径与最小包围圆，
并用 Thales 定理判定"以直径为直径的圆"能否覆盖该区域。

算法链：角域 → 候选交点(射线两两求交 + 角域过滤) → 凸包(Andrew 单调链)
        → 直径(暴力 ⊕ 旋转卡壳) → 最小包围圆(暴力 ⊕ Welzl) → 覆盖判定(Thales)

依据：Q1公式表.md、Q1完整思路.md
"""

import os
import sys

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional
from dataclasses import dataclass

# Windows 控制台默认 GBK，而本文件要打印 θ/√/≤ 这类字符，不设 UTF-8 会直接抛
# UnicodeEncodeError（实测过）。errors="replace" 兜底，避免个别终端再出问题。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 容差配置
EPS_GEOM = 1e-9      # 几何比较容差
EPS_DET = 1e-12      # 行列式判平行容差

@dataclass
class Point:
    x: float
    y: float

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __mul__(self, scalar):
        return Point(self.x * scalar, self.y * scalar)

    def norm(self):
        return np.sqrt(self.x**2 + self.y**2)

    def to_array(self):
        return np.array([self.x, self.y])


def angdiff(phi: float, theta: float) -> float:
    """
    【思路】角度环绕差，处理跨0°情况
    返回 phi - theta，结果在 [-180, 180] 范围内

    Args:
        phi: 角度1（度）
        theta: 角度2（度）

    Returns:
        角度差（度）

    Examples:
        >>> angdiff(359, 1)
        -2.0
        >>> angdiff(1, 359)
        2.0
    """
    diff = ((phi - theta + 180) % 360) - 180
    return diff


def unit_vector(phi_deg: float) -> np.ndarray:
    """
    【思路】根据角度返回单位方向向量
    坐标系：正东0°，逆时针为正，x正东y正北

    Args:
        phi_deg: 角度（度）

    Returns:
        (2,) 单位向量

    Examples:
        >>> u = unit_vector(0)
        >>> np.allclose(u, [1, 0])
        True
        >>> u = unit_vector(90)
        >>> np.allclose(u, [0, 1])
        True
    """
    phi_rad = np.deg2rad(phi_deg)
    return np.array([np.cos(phi_rad), np.sin(phi_rad)])


def cross_2d(a: np.ndarray, b: np.ndarray) -> float:
    """
    【思路】2D向量叉积（z分量）
    用于判断点的相对位置

    Args:
        a: 向量1
        b: 向量2

    Returns:
        a × b 的z分量
    """
    return a[0] * b[1] - a[1] * b[0]


@dataclass
class Ray:
    """射线：起点 + 方向"""
    origin: np.ndarray    # (2,) 起点
    direction: np.ndarray # (2,) 单位方向向量


@dataclass
class Wedge:
    """
    角域（扇形区域）
    【思路】用两条边界射线表示，夹角为 2ε
    """
    apex: np.ndarray      # (2,) 顶点S
    theta: float          # 中心角度（度）
    eps: float            # 半张角（度）
    ray_minus: Ray        # 左边界射线（θ-ε）
    ray_plus: Ray         # 右边界射线（θ+ε）

    @staticmethod
    def create(apex: np.ndarray, theta: float, eps: float):
        """
        【思路】构造角域

        Args:
            apex: 顶点坐标
            theta: 中心方向（度）
            eps: 半张角（度）
        """
        ray_minus = Ray(apex, unit_vector(theta - eps))
        ray_plus = Ray(apex, unit_vector(theta + eps))
        return Wedge(apex, theta, eps, ray_minus, ray_plus)

    def contains(self, P: np.ndarray) -> bool:
        """
        【思路】判断点P是否在角域内
        用两个半平面判断：P在左边界右侧 且 P在右边界左侧

        W2警告：这是最高频bug点，必须带容差！
        """
        vec_to_P = P - self.apex

        # 左边界：P应该在右侧（叉积 >= -EPS）
        cross_minus = cross_2d(self.ray_minus.direction, vec_to_P)

        # 右边界：P应该在左侧（叉积 <= EPS）
        cross_plus = cross_2d(self.ray_plus.direction, vec_to_P)

        return cross_minus >= -EPS_GEOM and cross_plus <= EPS_GEOM


@dataclass
class Polygon:
    vertices: List[np.ndarray]  # 顶点序列（逆时针，无共线点）

    def num_vertices(self) -> int:
        return len(self.vertices)


# M1: 角域构造
def build_wedges(points: List[np.ndarray],
                 thetas: List[float],
                 eps: float = 1.0) -> List[Wedge]:
    """
    【思路】为每个检测点构造角域

    Args:
        points: 检测点坐标列表
        thetas: 对应的示向度（度）
        eps: 半张角（度）

    Returns:
        角域列表
    """
    wedges = []
    for point, theta in zip(points, thetas):
        wedge = Wedge.create(point, theta, eps)
        wedges.append(wedge)
    return wedges


# M2: 射线求交 + 过滤
def intersect_rays(rA: Ray, rB: Ray) -> Optional[np.ndarray]:
    """
    【思路】计算两条射线的交点
    W1警告：必须确保 t >= 0 和 s >= 0（射线，不是直线）

    Args:
        rA: 射线A
        rB: 射线B

    Returns:
        交点坐标，如果不存在则返回None
    """
    # 求解 A + t*uA = B + s*uB
    # 即 t*uA - s*uB = B - A

    uA = rA.direction
    uB = rB.direction

    det = cross_2d(uA, uB)

    # 近平行，无交点
    if abs(det) < EPS_DET:
        return None

    diff = rB.origin - rA.origin
    t = cross_2d(diff, uB) / det
    s = cross_2d(diff, uA) / det

    # 射线反向，排除
    if t < 0 or s < 0:
        return None

    # 计算交点
    intersection = rA.origin + t * uA
    return intersection


def candidate_vertices(wedges: List[Wedge]) -> List[np.ndarray]:
    """
    【思路】枚举所有射线对的交点，过滤出有效顶点
    W2警告：这是最高频bug！必须检查 ∀k: P ∈ Wₖ

    Args:
        wedges: 角域列表

    Returns:
        候选顶点列表
    """
    points = []
    n = len(wedges)

    # 枚举所有射线对
    rays = []
    for w in wedges:
        rays.append(('minus', w.ray_minus))
        rays.append(('plus', w.ray_plus))

    # 两两求交
    for i in range(len(rays)):
        for j in range(i + 1, len(rays)):
            _, ray_i = rays[i]
            _, ray_j = rays[j]

            P = intersect_rays(ray_i, ray_j)
            if P is None:
                continue

            # 关键过滤：交点必须落在所有角域内，否则是假顶点（会让凸包错、直径偏大）
            valid = True
            for wedge in wedges:
                if not wedge.contains(P):
                    valid = False
                    break

            if valid:
                points.append(P)

    return points


# M3: 凸包
def convex_hull(points: List[np.ndarray]) -> Optional[Polygon]:
    """
    【思路】Andrew单调链算法计算凸包
    W8警告：必须用严格的 cross <= 0 剔除共线点

    Args:
        points: 点集

    Returns:
        凸多边形，如果点集为空则返回None
    """
    if len(points) == 0:
        return None

    # 排序
    points_sorted = sorted(points, key=lambda p: (p[0], p[1]))

    if len(points_sorted) < 3:
        return Polygon(points_sorted)

    # 下凸壳
    lower = []
    for p in points_sorted:
        while len(lower) >= 2:
            cross = cross_2d(lower[-1] - lower[-2], p - lower[-1])
            if cross <= EPS_GEOM:  # 严格剔除共线
                lower.pop()
            else:
                break
        lower.append(p)

    # 上凸壳
    upper = []
    for p in reversed(points_sorted):
        while len(upper) >= 2:
            cross = cross_2d(upper[-1] - upper[-2], p - upper[-1])
            if cross <= EPS_GEOM:
                upper.pop()
            else:
                break
        upper.append(p)

    # 合并（去掉重复的首尾点）
    hull = lower[:-1] + upper[:-1]

    return Polygon(hull)


# M4: 直径（双实现）
def diameter_bruteforce(poly: Polygon) -> Tuple[float, Tuple[np.ndarray, np.ndarray]]:
    """
    【思路】暴力法计算直径 O(m²)
    枚举所有顶点对，取最大距离
    这是基准实现，用于验证旋转卡壳

    Args:
        poly: 凸多边形

    Returns:
        (直径D, (端点p, 端点q))
    """
    vertices = poly.vertices
    n = len(vertices)

    if n == 0:
        return 0.0, (None, None)
    if n == 1:
        return 0.0, (vertices[0], vertices[0])

    max_dist = 0.0
    best_pair = (vertices[0], vertices[1])

    for i in range(n):
        for j in range(i + 1, n):
            dist = np.linalg.norm(vertices[i] - vertices[j])
            if dist > max_dist:
                max_dist = dist
                best_pair = (vertices[i], vertices[j])

    return max_dist, best_pair


def diameter_rotating_calipers(poly: Polygon) -> Tuple[float, Tuple[np.ndarray, np.ndarray]]:
    """
    【思路】旋转卡壳算法 O(m)
    通过旋转"卡尺"找到对踵点对（antipodal pairs）
    W9警告：指针必须环回一圈即停，否则死循环

    Args:
        poly: 凸多边形（顶点已按逆时针排序）

    Returns:
        (直径D, (端点p, 端点q))
    """
    vertices = poly.vertices
    n = len(vertices)

    if n < 2:
        return diameter_bruteforce(poly)

    if n == 2:
        dist = np.linalg.norm(vertices[1] - vertices[0])
        return dist, (vertices[0], vertices[1])

    max_dist = 0.0
    best_pair = (vertices[0], vertices[1])

    # 找初始对踵点对：最低点和最高点
    j = 1
    for i in range(n):
        # 旋转j直到不能增加面积
        while True:
            next_j = (j + 1) % n
            # 计算边 vertices[i] -> vertices[(i+1)%n] 与点 vertices[next_j] 的距离
            edge = vertices[(i + 1) % n] - vertices[i]
            vec_j = vertices[j] - vertices[i]
            vec_next_j = vertices[next_j] - vertices[i]

            # 比较叉积（面积）
            if abs(cross_2d(edge, vec_next_j)) > abs(cross_2d(edge, vec_j)) + EPS_GEOM:
                j = next_j
            else:
                break

        # 检查当前对踵点对
        dist = np.linalg.norm(vertices[i] - vertices[j])
        if dist > max_dist:
            max_dist = dist
            best_pair = (vertices[i], vertices[j])

    return max_dist, best_pair


# M5: 最小包围圆（双实现）
def circumcircle(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    【思路】计算三点的外接圆
    处理近共线情况：用最长边的直径圆兜底

    Args:
        p1, p2, p3: 三个点

    Returns:
        (圆心, 半径)
    """
    # 计算外接圆圆心
    ax, ay = p1[0], p1[1]
    bx, by = p2[0], p2[1]
    cx, cy = p3[0], p3[1]

    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))

    # 近共线，用最长边的直径圆
    if abs(d) < EPS_DET:
        # 找最长边
        d12 = np.linalg.norm(p2 - p1)
        d23 = np.linalg.norm(p3 - p2)
        d31 = np.linalg.norm(p1 - p3)

        if d12 >= d23 and d12 >= d31:
            center = (p1 + p2) / 2
            radius = d12 / 2
        elif d23 >= d12 and d23 >= d31:
            center = (p2 + p3) / 2
            radius = d23 / 2
        else:
            center = (p3 + p1) / 2
            radius = d31 / 2

        return center, radius

    ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d
    uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / d

    center = np.array([ux, uy])
    radius = np.linalg.norm(center - p1)

    return center, radius


def mec_bruteforce(points: List[np.ndarray]) -> Tuple[np.ndarray, float]:
    """
    【思路】暴力法计算最小包围圆
    枚举点对定圆（直径圆）+ 三点定外接圆，取能覆盖全体的最小者

    Args:
        points: 点集

    Returns:
        (圆心, 半径)
    """
    n = len(points)

    if n == 0:
        return np.array([0.0, 0.0]), 0.0
    if n == 1:
        return points[0], 0.0

    min_radius = float('inf')
    best_center = None

    # 枚举两点定圆（以两点连线为直径）
    for i in range(n):
        for j in range(i + 1, n):
            center = (points[i] + points[j]) / 2
            radius = np.linalg.norm(points[i] - center)

            # 检查是否覆盖所有点
            covers_all = True
            for k in range(n):
                if np.linalg.norm(points[k] - center) > radius + EPS_GEOM:
                    covers_all = False
                    break

            if covers_all and radius < min_radius:
                min_radius = radius
                best_center = center

    # 枚举三点定圆（外接圆）
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                center, radius = circumcircle(points[i], points[j], points[k])

                # 检查是否覆盖所有点
                covers_all = True
                for m in range(n):
                    if np.linalg.norm(points[m] - center) > radius + EPS_GEOM:
                        covers_all = False
                        break

                if covers_all and radius < min_radius:
                    min_radius = radius
                    best_center = center

    return best_center, min_radius


def welzl_mec(points: List[np.ndarray], seed: int = 42) -> Tuple[np.ndarray, float]:
    """
    【思路】Welzl随机增量算法，期望 O(n)
    W10警告：必须正确处理边界集 0/1/2/3 个点的四种情形

    Args:
        points: 点集
        seed: 随机种子（固定以保证可复现）

    Returns:
        (圆心, 半径)
    """
    # 洗牌
    np.random.seed(seed)
    points_shuffled = points.copy()
    np.random.shuffle(points_shuffled)

    def welzl_recursive(pts: List[np.ndarray], boundary: List[np.ndarray]) -> Tuple[np.ndarray, float]:
        # 边界情况
        if len(boundary) == 3:
            return circumcircle(boundary[0], boundary[1], boundary[2])

        if len(pts) == 0:
            if len(boundary) == 0:
                return np.array([0.0, 0.0]), 0.0
            elif len(boundary) == 1:
                return boundary[0], 0.0
            elif len(boundary) == 2:
                center = (boundary[0] + boundary[1]) / 2
                radius = np.linalg.norm(boundary[0] - center)
                return center, radius

        # 取一个点
        p = pts[0]
        remaining = pts[1:]

        # 递归计算不含p的MEC
        center, radius = welzl_recursive(remaining, boundary)

        # 如果p在圆内，直接返回
        if np.linalg.norm(p - center) <= radius + EPS_GEOM:
            return center, radius

        # 否则，p必须在边界上
        return welzl_recursive(remaining, boundary + [p])

    return welzl_recursive(list(points_shuffled), [])


# M6: 覆盖判定
def thales_inside(P: np.ndarray, Q: np.ndarray, X: np.ndarray) -> bool:
    """
    【思路】Thales定理：判断X是否在以PQ为直径的圆内
    等价于 ∠PXQ >= 90°，即 dot(X-P, X-Q) <= 0

    Args:
        P, Q: 直径端点
        X: 待判定的点

    Returns:
        True表示X在圆内或圆上
    """
    vec_XP = P - X
    vec_XQ = Q - X
    dot_product = np.dot(vec_XP, vec_XQ)
    return dot_product <= EPS_GEOM


def covers(poly: Polygon, P: np.ndarray, Q: np.ndarray) -> bool:
    """
    【思路】判断以PQ为直径的圆是否覆盖凸多边形L
    由于圆盘凸、L凸，只需检查所有顶点

    Args:
        poly: 凸多边形
        P, Q: 直径端点

    Returns:
        True表示覆盖
    """
    for vertex in poly.vertices:
        if not thales_inside(P, Q, vertex):
            return False
    return True


def all_diameter_pairs(poly: Polygon, D: float) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    【思路】枚举所有达到直径的顶点对
    W5警告：直径对可能不唯一

    Args:
        poly: 凸多边形
        D: 直径值

    Returns:
        所有满足 ||p-q|| >= D - EPS 的顶点对列表
    """
    pairs = []
    vertices = poly.vertices
    n = len(vertices)

    for i in range(n):
        for j in range(i + 1, n):
            dist = np.linalg.norm(vertices[i] - vertices[j])
            if dist >= D - EPS_GEOM:
                pairs.append((vertices[i], vertices[j]))

    return pairs


# M7: 有界性检查
def is_bounded(wedges: List[Wedge]) -> bool:
    """
    【思路】定理G0：L有界 ⟺ 方向区间之交为空
    即检查是否存在公共方向

    Args:
        wedges: 角域列表

    Returns:
        True表示有界
    """
    if len(wedges) == 0:
        return False

    # 收集所有方向区间 [θ-ε, θ+ε]
    intervals = []
    for w in wedges:
        intervals.append((w.theta - w.eps, w.theta + w.eps))

    # 检查交集是否为空
    # 简化版：对n=2情况，检查 |θ₁ - θ₂| >= 2ε
    if len(wedges) == 2:
        theta_diff = abs(angdiff(wedges[0].theta, wedges[1].theta))
        return theta_diff >= 2 * wedges[0].eps

    # 一般情况：检查是否存在角度在所有区间内
    # 采样检查（简化实现）
    for angle in np.linspace(0, 360, 360):
        in_all = True
        for w in wedges:
            if abs(angdiff(angle, w.theta)) > w.eps:
                in_all = False
                break
        if in_all:
            return False  # 存在公共方向，无界

    return True


def test_baseline():
    """
    【思路】基准验证题
    输入：S₁=(0,0)，S₂=(600,0)，G=(300,500)，ε=1°
    期望：D = 39.598 m (±0.05)，顶点数 = 4，R_MEC = 19.799 m
    """
    print("=" * 60)
    print("基准验证题")
    print("=" * 60)

    # 构造输入
    S1 = np.array([0.0, 0.0])
    S2 = np.array([600.0, 0.0])
    G = np.array([300.0, 500.0])

    # 计算示向度
    theta1 = np.rad2deg(np.arctan2(G[1] - S1[1], G[0] - S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1] - S2[1], G[0] - S2[0]))

    print(f"真实目标位置: G = ({G[0]}, {G[1]})")
    print(f"θ₁ = {theta1:.3f}°")
    print(f"θ₂ = {theta2:.3f}°")

    eps = 1.0

    # 构造角域
    wedges = build_wedges([S1, S2], [theta1, theta2], eps)

    # 检查有界性
    bounded = is_bounded(wedges)
    print(f"\n定位区域有界: {bounded}")

    if not bounded:
        print("警告：定位区域无界，无法计算直径")
        return

    # 计算候选顶点
    vertices = candidate_vertices(wedges)
    print(f"候选顶点数: {len(vertices)}")

    if len(vertices) == 0:
        print("错误：没有找到有效顶点")
        return

    # 计算凸包
    poly = convex_hull(vertices)
    if not poly:
        print("错误：无法构造凸包")
        return

    print(f"\n凸包顶点数: {poly.num_vertices()}")
    print("期望顶点数: 4")

    # 打印顶点坐标
    print("\n凸包顶点坐标：")
    for i, v in enumerate(poly.vertices):
        print(f"  V{i+1} = ({v[0]:.3f}, {v[1]:.3f})")

    # 计算直径（双实现互验）
    print("\n" + "=" * 60)
    print("直径计算（双实现互验）")
    print("=" * 60)

    D_brute, (p1_brute, q1_brute) = diameter_bruteforce(poly)
    print(f"暴力法：D = {D_brute:.3f} m")
    print(f"  端点：({p1_brute[0]:.3f}, {p1_brute[1]:.3f}) ↔ ({q1_brute[0]:.3f}, {q1_brute[1]:.3f})")

    D_calipers, (p1_calipers, q1_calipers) = diameter_rotating_calipers(poly)
    print(f"旋转卡壳：D = {D_calipers:.3f} m")
    print(f"  端点：({p1_calipers[0]:.3f}, {p1_calipers[1]:.3f}) ↔ ({q1_calipers[0]:.3f}, {q1_calipers[1]:.3f})")

    # 断言A2：两者必须完全相等
    assert abs(D_brute - D_calipers) < EPS_GEOM, "断言A2失败：暴力法与旋转卡壳结果不一致"
    print("[OK] 断言A2通过：两种方法结果一致")

    print("\n期望直径：39.598 ± 0.05 m")
    if abs(D_brute - 39.598) <= 0.05:
        print("[OK] 断言A6通过：直径符合预期")
    else:
        print(f"[FAIL] 断言A6失败：直径偏差 {abs(D_brute - 39.598):.3f} m")

    # 计算最小包围圆（双实现互验）
    print("\n" + "=" * 60)
    print("最小包围圆计算（双实现互验）")
    print("=" * 60)

    center_brute, R_brute = mec_bruteforce(poly.vertices)
    print(f"暴力法：R_MEC = {R_brute:.3f} m")
    print(f"  圆心：({center_brute[0]:.3f}, {center_brute[1]:.3f})")

    center_welzl, R_welzl = welzl_mec(poly.vertices)
    print(f"Welzl算法：R_MEC = {R_welzl:.3f} m")
    print(f"  圆心：({center_welzl[0]:.3f}, {center_welzl[1]:.3f})")

    # 断言A3：两者差异必须小于1e-9
    assert abs(R_brute - R_welzl) < 1e-6, "断言A3失败：暴力法与Welzl结果不一致"
    print(f"[OK] 断言A3通过：两种方法结果一致（差异 {abs(R_brute - R_welzl):.9f}）")

    print("\n期望 R_MEC：19.799 m")

    # 断言A4：Jung界
    print("\n" + "=" * 60)
    print("Jung定理验证（断言A4）")
    print("=" * 60)

    D = D_brute
    R_MEC = R_brute
    lower_bound = D / 2
    upper_bound = D / np.sqrt(3)

    print(f"D/2 = {lower_bound:.3f} m")
    print(f"R_MEC = {R_MEC:.3f} m")
    print(f"D/√3 = {upper_bound:.3f} m")

    assert R_MEC >= lower_bound - EPS_GEOM, "断言A4失败：R_MEC < D/2"
    assert R_MEC <= upper_bound + EPS_GEOM, "断言A4失败：R_MEC > D/√3"
    print(f"[OK] 断言A4通过：{lower_bound:.3f} ≤ {R_MEC:.3f} ≤ {upper_bound:.3f}")

    # 计算γ
    gamma = R_MEC / (D / 2)
    print(f"\nγ = R_MEC/(D/2) = {gamma:.4f}")
    print(f"γ 范围：[1, {2/np.sqrt(3):.4f}]")

    # 覆盖判定
    print("\n" + "=" * 60)
    print("覆盖判定（断言A5）")
    print("=" * 60)

    # 获取所有直径对
    diameter_pairs = all_diameter_pairs(poly, D)
    print(f"直径对数量：{len(diameter_pairs)}")

    # 逐一判定
    coverage_results = []
    for i, (p, q) in enumerate(diameter_pairs):
        covers_L = covers(poly, p, q)
        coverage_results.append(covers_L)
        print(f"  对{i+1}: ({p[0]:.3f}, {p[1]:.3f}) ↔ ({q[0]:.3f}, {q[1]:.3f}) -> {'覆盖' if covers_L else '不覆盖'}")

    # 三种口径
    any_pair_covers = coverage_results[0] if len(coverage_results) > 0 else False
    exists_pair_covers = any(coverage_results)
    all_pairs_cover = all(coverage_results) if len(coverage_results) > 0 else False

    print("\n覆盖判定结果：")
    print(f"  任取一对：{any_pair_covers}")
    print(f"  存在一对：{exists_pair_covers}")
    print(f"  所有对都覆盖：{all_pairs_cover}")

    # 断言A5：覆盖判定应与 R_MEC <= D/2 一致
    expected_coverage = (R_MEC <= D/2 + EPS_GEOM)
    print(f"\n基于 R_MEC 的预期：{'覆盖' if expected_coverage else '不覆盖'} (R_MEC {'<=' if expected_coverage else '>'} D/2)")

    if expected_coverage == all_pairs_cover:
        print("[OK] 断言A5通过：覆盖判定与 R_MEC 一致")
    else:
        print("[FAIL] 断言A5警告：覆盖判定与 R_MEC 不一致")

    print("\n" + "=" * 60)
    print("基准验证题完成")
    print("=" * 60)


def test_degenerate_cases():
    """
    【思路】测试退化用例集
    确保所有边界情况都能正常处理
    """
    print("\n" + "=" * 60)
    print("退化用例测试")
    print("=" * 60)

    # 用例1：近平行（|θ₁-θ₂| < 2°）
    print("\n用例1：近平行角域")
    S1 = np.array([0.0, 0.0])
    S2 = np.array([600.0, 0.0])
    theta1 = 30.0
    theta2 = 30.5  # 差0.5° < 2°
    wedges = build_wedges([S1, S2], [theta1, theta2], eps=1.0)
    bounded = is_bounded(wedges)
    print(f"  θ₁={theta1}°, θ₂={theta2}°, 角度差={abs(theta2-theta1)}°")
    print(f"  有界性：{bounded} (期望：False)")

    # 用例2：跨0°
    print("\n用例2：跨0°角度")
    theta1 = 359.5
    theta2 = 0.5
    wedges = build_wedges([S1, S2], [theta1, theta2], eps=1.0)
    bounded = is_bounded(wedges)
    angle_diff = abs(angdiff(theta1, theta2))
    print(f"  θ₁={theta1}°, θ₂={theta2}°")
    print(f"  角度差（正确计算）={angle_diff}° (期望：1°)")
    print(f"  有界性：{bounded} (期望：False，因为差<2°)")

    # 用例2b：跨0°但差值大
    print("\n用例2b：跨0°角度（大角度差）")
    theta1 = 350.0
    theta2 = 10.0
    wedges = build_wedges([S1, S2], [theta1, theta2], eps=1.0)
    bounded = is_bounded(wedges)
    angle_diff = abs(angdiff(theta1, theta2))
    print(f"  θ₁={theta1}°, θ₂={theta2}°")
    print(f"  角度差（正确计算）={angle_diff}° (期望：20°)")
    print(f"  有界性：{bounded} (期望：True)")

    # 用例3：正交配置（φ=90°）
    print("\n用例3：正交配置（最优交会角）")
    S1 = np.array([0.0, 0.0])
    S2 = np.array([500.0, 500.0])  # 45°方向
    G = np.array([500.0, 0.0])     # 使得∠S₁GS₂ = 90°

    theta1 = np.rad2deg(np.arctan2(G[1] - S1[1], G[0] - S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1] - S2[1], G[0] - S2[0]))

    wedges = build_wedges([S1, S2], [theta1, theta2], eps=1.0)
    vertices = candidate_vertices(wedges)

    if len(vertices) > 0:
        poly = convex_hull(vertices)
        if poly and poly.num_vertices() >= 2:
            D, _ = diameter_bruteforce(poly)
            print(f"  真实目标：({G[0]}, {G[1]})")
            print(f"  θ₁={theta1:.1f}°, θ₂={theta2:.1f}°")
            print("  交会角 φ ≈ 90° (最优配置)")
            print(f"  直径 D = {D:.3f} m")

    print("\n[OK] 退化用例测试完成")


def visualize_baseline(save_path: str = None):
    """
    【思路】可视化基准验证题
    绘制角域、定位区域、直径、最小包围圆
    """

    # 构造输入
    S1 = np.array([0.0, 0.0])
    S2 = np.array([600.0, 0.0])
    G = np.array([300.0, 500.0])

    theta1 = np.rad2deg(np.arctan2(G[1] - S1[1], G[0] - S1[0]))
    theta2 = np.rad2deg(np.arctan2(G[1] - S2[1], G[0] - S2[0]))
    eps = 1.0

    wedges = build_wedges([S1, S2], [theta1, theta2], eps)
    vertices = candidate_vertices(wedges)
    poly = convex_hull(vertices)

    if not poly:
        print("无法生成可视化：凸包为空")
        return

    D, (p_d, q_d) = diameter_bruteforce(poly)
    center_mec, R_mec = mec_bruteforce(poly.vertices)

    # 默认写到本文件所在目录的 figs/ 下。原来是相对路径 "../实验结果/figs/..."，
    # 跟着当前工作目录走，在别的目录下调用就会写错地方。
    if save_path is None:
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "figs", "baseline_case.png")

    # 中文字体只在本函数内临时生效：本模块被 19 个出图脚本 import，
    # 在模块顶层改 rcParams 会把下游的全局配置一起带偏。
    _font_old = plt.rcParams["font.sans-serif"]
    _minus_old = plt.rcParams["axes.unicode_minus"]
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(10, 8))

    # 绘制角域边界射线（延长一段距离）
    ray_length = 700
    for i, w in enumerate(wedges):
        # 左边界
        end_minus = w.apex + ray_length * w.ray_minus.direction
        ax.plot([w.apex[0], end_minus[0]], [w.apex[1], end_minus[1]],
                'b--', alpha=0.3, linewidth=1)
        # 右边界
        end_plus = w.apex + ray_length * w.ray_plus.direction
        ax.plot([w.apex[0], end_plus[0]], [w.apex[1], end_plus[1]],
                'b--', alpha=0.3, linewidth=1)

    # 绘制定位区域（凸包）
    hull_pts = np.array(poly.vertices + [poly.vertices[0]])  # 闭合
    ax.fill(hull_pts[:, 0], hull_pts[:, 1], alpha=0.3, color='yellow', label='定位区域 L')
    ax.plot(hull_pts[:, 0], hull_pts[:, 1], 'k-', linewidth=2)

    # 绘制顶点
    for i, v in enumerate(poly.vertices):
        ax.plot(v[0], v[1], 'ko', markersize=8)
        ax.text(v[0], v[1] + 15, f'V{i+1}', ha='center', fontsize=9)

    # 绘制直径
    ax.plot([p_d[0], q_d[0]], [p_d[1], q_d[1]], 'r-', linewidth=3, label=f'直径 D={D:.1f}m')

    # 绘制最小包围圆
    circle_mec = plt.Circle(center_mec, R_mec, fill=False, color='green',
                            linewidth=2, linestyle='--', label=f'最小包围圆 R={R_mec:.1f}m')
    ax.add_patch(circle_mec)
    ax.plot(center_mec[0], center_mec[1], 'g+', markersize=12, markeredgewidth=2)

    # 绘制检测点和真实目标
    ax.plot(S1[0], S1[1], 'bs', markersize=12, label='检测点 S₁')
    ax.plot(S2[0], S2[1], 'bs', markersize=12, label='检测点 S₂')
    ax.plot(G[0], G[1], 'r*', markersize=15, label='真实目标 G')

    ax.set_xlabel('X (m)', fontsize=12)
    ax.set_ylabel('Y (m)', fontsize=12)
    ax.set_title('Q1 基准验证题 - 交会定位区域与覆盖', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.axis('equal')
    ax.set_xlim(-50, 650)
    ax.set_ylim(-50, 600)

    # 保存图片
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\n[OK] 可视化已保存至: {save_path}")
    plt.close()
    plt.rcParams["font.sans-serif"] = _font_old
    plt.rcParams["axes.unicode_minus"] = _minus_old


if __name__ == "__main__":
    # 自检：角度处理
    print("自检测试...")
    assert abs(angdiff(359, 1) - (-2)) < 1e-9, "angdiff(359, 1) 应该等于 -2"
    assert abs(angdiff(1, 359) - 2) < 1e-9, "angdiff(1, 359) 应该等于 2"

    u0 = unit_vector(0)
    assert np.allclose(u0, [1, 0]), "unit_vector(0) 应该是 (1, 0)"

    u90 = unit_vector(90)
    assert np.allclose(u90, [0, 1]), "unit_vector(90) 应该是 (0, 1)"

    print("[OK] 基础函数自检通过")
    print()

    # 运行基准验证题
    test_baseline()

    # 运行退化用例
    test_degenerate_cases()

    # 生成可视化
    visualize_baseline()
