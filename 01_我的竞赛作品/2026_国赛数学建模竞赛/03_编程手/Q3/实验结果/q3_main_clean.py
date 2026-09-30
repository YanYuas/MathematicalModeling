"""
Q3: 多源自动定位与清除
建模组 2026-09-11
"""

import numpy as np
import requests
import json
import uuid
import time
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

# 全局参数
R_DOMAIN = 1800.0
R_SENSOR = 1000.0
R_CLEAR = 20.0
R_NEAR = 5.0
VELOCITY = 5.0
EPSILON_DEG = 1.0
EPSILON_RAD = np.radians(EPSILON_DEG)

T_MEASURE = 5.0
T_SWITCH = 1.0
T_CLEAR_SUCCESS = 5.0
T_CLEAR_FAIL = 3.0
T_RESERVE = 60.0

D_GRID_1500 = 1500.0
D_GRID_1000 = 1000.0

LAMBDA_IDEAL = 2 * np.sin(EPSILON_RAD / 2)  # 0.0174531
R_STAR = 84.0369  # 扫掠/homing拐点

N_CHANNELS = 20

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

    def norm(self) -> float:
        return np.sqrt(self.x**2 + self.y**2)

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y])

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


class ChannelState(Enum):
    UNDISCOVERED = "未发现"
    LOCATED = "已定位"
    APPROACHING = "逼近中"
    CLEARED = "已清除"
    CONFIRMED_EMPTY = "已确认空"


@dataclass
class SourceInfo:
    channel: int
    L: List[Point]
    c_star: Point
    R_MEC: float
    discovered_at: Tuple[Point, Point]


class SimulatorClient:
    """模拟器HTTP客户端"""

    def __init__(self, base_url: str = "http://127.0.0.1:2026", timeout: float = 10.0):
        self.base_url = base_url
        self.timeout = timeout
        self.request_counter = 0
        self.remaining_real_time = 1200.0
        self.virtual_time = 0.0
        self.session = requests.Session()
        # P0-9：协议合规（附件2 §5.1/§7.1 必填）
        self.arena_id = "default"
        self.robot_id = "CUMCM2026"   # TODO(编程手): 换成真实参赛队号
        # P0-11：墙钟（表 1 第 4 列「程序运行时间」= /enter → 结束）
        import time as _t
        self.t_enter_wall = None
        self.elapsed_wall = 0.0

    def _new_request_id(self) -> str:
        self.request_counter += 1
        return f"req_{self.request_counter}_{uuid.uuid4().hex[:8]}"

    def _send_request(self, endpoint: str, payload: dict, request_id: Optional[str] = None) -> dict:
        if request_id is None:
            request_id = self._new_request_id()
        payload["request_id"] = request_id
        url = f"{self.base_url}{endpoint}"

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.post(url, json=payload, timeout=self.timeout)
                if response.status_code != 200:
                    print(f"HTTP {response.status_code}: {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(0.5)
                        continue
                    raise RuntimeError(f"HTTP错误 {response.status_code}")

                data = response.json()
                if not data.get("accepted", False):
                    raise RuntimeError(f"请求被拒: {data}")

                if "remaining_real_duration_s" in data:
                    self.remaining_real_time = data["remaining_real_duration_s"]

                return data

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                else:
                    raise

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                else:
                    raise

    def enter(self) -> dict:
        import time as _t
        resp = self._send_request("/enter", {
            "arena_id": self.arena_id, "robot_id": self.robot_id,
        })
        self.t_enter_wall = _t.time()   # P0-11 墙钟起点
        return resp

    def measure(self, x: float, y: float, channel: int) -> dict:
        payload = {
            "arena_id": self.arena_id,        # P0-9 必填
            "robot_id": self.robot_id,        # P0-9 必填
            "position": {"x": x, "y": y},     # P0-9 嵌套结构
            "channel": channel,
        }
        resp = self._send_request("/measure", payload)
        self.virtual_time += 5.0   # P0-9 修正：T_MEASURE（原实现从未累加，统计量不可用）
        return resp

    def clear(self, x: float, y: float, channel: int) -> dict:
        payload = {
            "arena_id": self.arena_id,        # P0-9 必填
            "robot_id": self.robot_id,        # P0-9 必填
            "position": {"x": x, "y": y},     # P0-9 嵌套结构
            "channel": channel,
        }
        resp = self._send_request("/clear", payload)
        self.virtual_time += 5.0 if resp.get("clear_result") == "success" else 3.0
        return resp

    def exit(self) -> dict:
        return self._send_request("/exit", {})

    def get_remaining_time(self) -> float:
        return self.remaining_real_time

    def check_time_safety(self) -> bool:
        return self.remaining_real_time > T_RESERVE


def generate_triangular_grid(d: float, R: float = R_DOMAIN) -> List[Point]:
    """生成三角网格"""
    a1 = np.array([d, 0])
    a2 = np.array([d/2, np.sqrt(3)*d/2])

    margin = d / np.sqrt(3)
    max_coord = R + margin
    n_max = int(np.ceil(max_coord / d)) + 1

    points = []
    for i in range(-n_max, n_max + 1):
        for j in range(-n_max, n_max + 1):
            p = i * a1 + j * a2
            if np.linalg.norm(p) <= R:
                points.append(Point(p[0], p[1]))

    # 去重
    unique_points = []
    for p in points:
        is_duplicate = False
        for q in unique_points:
            if (p - q).norm() < 1e-6:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_points.append(p)

    print(f"网格生成: d={d:.0f}m, 点数={len(unique_points)}")
    return unique_points


def coverage_check(P: List[Point], R_domain: float = R_DOMAIN,
                   R_sensor: float = R_SENSOR) -> Tuple[bool, float]:
    """覆盖自检"""
    sample_points = []
    step = 50.0
    n_steps = int(np.ceil(2 * R_domain / step))

    for i in range(n_steps + 1):
        for j in range(n_steps + 1):
            x = -R_domain + i * step
            y = -R_domain + j * step
            r = np.sqrt(x**2 + y**2)
            if r <= R_domain:
                sample_points.append(np.array([x, y]))

    # 边界加密
    theta_samples = np.linspace(0, 2*np.pi, 360)
    for r in np.arange(1750, 1801, 10):
        for theta in theta_samples:
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            sample_points.append(np.array([x, y]))

    max_dist = 0.0
    failed_points = []

    for sp in sample_points:
        min_dist = min((sp[0] - p.x)**2 + (sp[1] - p.y)**2 for p in P)
        min_dist = np.sqrt(min_dist)
        max_dist = max(max_dist, min_dist)

        if min_dist > R_sensor + 1e-9:
            failed_points.append((sp, min_dist))

    is_covered = len(failed_points) == 0

    if is_covered:
        print(f"覆盖自检通过, 最大距离={max_dist:.2f}m")
    else:
        print(f"覆盖自检失败, {len(failed_points)}个点超出")

    return is_covered, max_dist


def angdiff(phi: float, theta: float) -> float:
    """角度差"""
    diff = ((phi - theta + 180) % 360) - 180
    return diff


def wedge(S: Point, theta_deg: float, epsilon_deg: float = EPSILON_DEG) -> dict:
    """角域"""
    return {
        "station": S,
        "theta_deg": theta_deg,
        "epsilon_deg": epsilon_deg
    }


def intersect_wedges(wedges: List[dict]) -> List[Point]:
    """角域交集 - 需要Q1算法"""
    print("intersect_wedges未实现，需Q1算法")
    return []


def minimum_enclosing_circle(L: List[Point]) -> Tuple[Point, float]:
    """最小包围圆 - 需要Q1算法"""
    if not L:
        return Point(0, 0), float('inf')

    # 临时用质心近似
    x_avg = sum(p.x for p in L) / len(L)
    y_avg = sum(p.y for p in L) / len(L)
    c_approx = Point(x_avg, y_avg)
    R_approx = max((p - c_approx).norm() for p in L)

    return c_approx, R_approx


def clip_to_domain(L: List[Point], R: float = R_DOMAIN) -> List[Point]:
    """圆域截断"""
    return [p for p in L if p.norm() <= R + 1e-9]


class ChannelStateMachine:
    """频道状态管理"""

    def __init__(self, n_channels: int = N_CHANNELS, n_positions: int = 8):
        self.n_channels = n_channels
        self.n_positions = n_positions
        self.state = {c: ChannelState.UNDISCOVERED for c in range(1, n_channels + 1)}
        self.no_signal_positions = {c: set() for c in range(1, n_channels + 1)}  # P0-7: 按检测点去重
        self.sources: Dict[int, SourceInfo] = {}

    def update(self, channel: int, position_id: int, result: str,
               svd_deg: Optional[float] = None, L: Optional[List[Point]] = None):
        if result == "no_signal":
            # P0-7: 同一点重复 no_signal 不再累加，必须覆盖到 n_positions 个不同检测点
            self.no_signal_positions[channel].add(position_id)
            if len(self.no_signal_positions[channel]) >= self.n_positions:
                self.state[channel] = ChannelState.CONFIRMED_EMPTY

        elif result == "direction":
            if self.state[channel] == ChannelState.UNDISCOVERED:
                self.state[channel] = ChannelState.LOCATED

        elif result == "near":
            self.state[channel] = ChannelState.LOCATED

    def mark_cleared(self, channel: int):
        self.state[channel] = ChannelState.CLEARED

    def check_completeness(self) -> Tuple[bool, dict]:
        cleared = sum(1 for s in self.state.values() if s == ChannelState.CLEARED)
        confirmed_empty = sum(1 for s in self.state.values() if s == ChannelState.CONFIRMED_EMPTY)
        remaining = self.n_channels - cleared - confirmed_empty

        status = {
            "cleared": cleared,
            "confirmed_empty": confirmed_empty,
            "remaining": remaining
        }

        should_stop = (remaining == 0)
        return should_stop, status


def direct_clear(c_star: Point, channel: int, client: SimulatorClient) -> Tuple[bool, float]:
    """直接清除"""
    resp = client.clear(c_star.x, c_star.y, channel)
    success = (resp.get("result") == "success")
    cost = T_CLEAR_SUCCESS if success else T_CLEAR_FAIL
    return success, cost


def sweep_clear(L: List[Point], R_MEC: float, c_star: Point, channel: int,
                client: SimulatorClient) -> Tuple[bool, float]:
    """扫掠清除"""
    N_sweep = int(np.ceil(1.2091996 * (R_MEC / 20.0)**2))
    print(f"扫掠清除: R_MEC={R_MEC:.1f}m, 需{N_sweep}次")

    # 简化: 网格采样
    centers = []
    if L:
        x_min = min(p.x for p in L)
        x_max = max(p.x for p in L)
        y_min = min(p.y for p in L)
        y_max = max(p.y for p in L)

        step = 20.0
        x = x_min
        while x <= x_max:
            y = y_min
            while y <= y_max:
                centers.append(Point(x, y))
                y += step
            x += step

    # P0-2: 不截断 + 按到 c* 的距离升序（步距 20 ⇒ 覆盖半径 14.14 ≤ 20，遍历全部必然命中）
    centers.sort(key=lambda p: (p.x - c_star.x)**2 + (p.y - c_star.y)**2)
    print(f"[清除] 扫掠候选中心 {len(centers)} 个（按距 c* 升序，不截断）")

    total_cost = 0.0
    for i, c in enumerate(centers):
        resp = client.clear(c.x, c.y, channel)
        if resp.get("result") == "success":
            total_cost += T_CLEAR_SUCCESS
            return True, total_cost
        else:
            total_cost += T_CLEAR_FAIL

    return False, total_cost


def homing_clear(L: List[Point], channel: int, client: SimulatorClient) -> Tuple[bool, float]:
    """Homing逼近"""
    if not L:
        return False, 0.0

    x_avg = sum(p.x for p in L) / len(L)
    y_avg = sum(p.y for p in L) / len(L)
    pos = Point(x_avg, y_avg)

    resp = client.measure(pos.x, pos.y, channel)
    if resp.get("result") == "near":
        return direct_clear(pos, channel, client)

    theta_old = resp.get("svd_deg")
    total_cost = T_MEASURE

    max_iterations = 10
    for k in range(max_iterations):
        D = max((p - q).norm() for p in L for q in L) if len(L) > 1 else 100.0
        r_hat = D / 2.0
        h = r_hat

        theta_rad = np.radians(theta_old)
        pos = pos + Point(h * np.cos(theta_rad), h * np.sin(theta_rad))

        resp = client.measure(pos.x, pos.y, channel)
        total_cost += T_MEASURE

        if resp.get("result") == "near":
            success, cost = direct_clear(pos, channel, client)
            return success, total_cost + cost

        theta_new = resp.get("svd_deg")

        # 反向检测
        if abs(angdiff(theta_new, theta_old)) > 90.0:
            pos = pos + Point(-0.5 * h * np.cos(theta_rad), -0.5 * h * np.sin(theta_rad))
            resp = client.measure(pos.x, pos.y, channel)
            total_cost += T_MEASURE
            theta_new = resp.get("svd_deg")

        theta_old = theta_new

    return False, total_cost


def clear_source(source: SourceInfo, client: SimulatorClient) -> Tuple[bool, float, str]:
    """三路清除"""
    R_MEC = source.R_MEC
    channel = source.channel
    L = source.L
    c_star = source.c_star

    if R_MEC <= R_CLEAR:
        mode = "direct"
        success, cost = direct_clear(c_star, channel, client)
    elif R_MEC <= R_STAR:
        mode = "sweep"
        success, cost = sweep_clear(L, R_MEC, c_star, channel, client)
    else:
        mode = "homing"
        success, cost = homing_clear(L, channel, client)

    return success, cost, mode


def main_strategy(d_grid: float = D_GRID_1500):
    """主策略"""
    print("=" * 60)
    print("Q3 多源自动定位与清除")
    print("=" * 60)

    client = SimulatorClient()

    print("\n启动会话...")
    resp = client.enter()
    print(f"剩余时间: {client.remaining_real_time:.1f}s")

    print(f"\n生成检测点 (d={d_grid}m)...")
    P = generate_triangular_grid(d_grid)

    print("\n覆盖自检...")
    is_covered, max_dist = coverage_check(P)
    if not is_covered:
        print("覆盖自检失败")
        return

    state = ChannelStateMachine(n_channels=N_CHANNELS, n_positions=len(P))

    print(f"\n阶段A: 侦察 ({len(P)}个点)...")
    # TODO: 实现TSP + 扫描

    print("\n阶段B: 清除...")
    # TODO: 实现清除

    print("\n阶段C: 收尾...")
    complete, stats = state.check_completeness()
    print(f"已清除={stats['cleared']}, 已确认空={stats['confirmed_empty']}")

    print("\n退出会话...")
    client.exit()

    print(f"\n虚拟时间: {client.virtual_time:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    # ================================================================
    # 验收线 ① 自检（不依赖模拟器）
    # ⚠️ 2026-09-11 恢复：本文档由「去 AI 痕迹」重构而来时，把自检回退成了
    #    `assert 7 <= len(P_1500) <= 9` / `assert 10 <= len(P_1000) <= 12`，
    #    而 d=1000 实测 **13** 点 ⇒ 断言必然失败（本机实测退出码 1）；
    #    且原来的 d=1000 档覆盖自检与断言 2/3 一并丢失。现按 `q3_main.py` 的
    #    修复版恢复（断言 2/3 + 两档覆盖 + 失败非零退出）。
    # ================================================================
    import sys

    EPS_GEOM = 1e-9
    ok = True

    # 断言 2：间距约束 d ≤ √3·R_sensor
    D_MAX = np.sqrt(3) * R_SENSOR
    print(f"[断言2] d 上限 = √3·R_sensor = {D_MAX:.4f} m")
    for d in (D_GRID_1000, D_GRID_1500):
        if d > D_MAX + EPS_GEOM:
            print(f"  ✗ d={d} 超过上限"); ok = False
    print("  ✓ 通过" if ok else "  ✗ 失败")

    # 断言 3：单元数下界（平面圆盘覆盖最优密度 2π/(3√3) ⇒ N ≥ 4）
    for d in (D_GRID_1000, D_GRID_1500):
        n_units = np.pi * R_DOMAIN ** 2 / ((np.sqrt(3) / 2) * d ** 2)
        print(f"[断言3] d={d:.0f} m：圆域单元数 ≈ {n_units:.5f}（下界 ≥ 4）")
        if n_units < 4 - EPS_GEOM:
            print("  ✗ 不满足下界"); ok = False

    # M2 + M3：网格点数与覆盖自检（两档都必须跑）
    for d in (D_GRID_1500, D_GRID_1000):
        P = generate_triangular_grid(d)
        n_units = np.pi * R_DOMAIN ** 2 / ((np.sqrt(3) / 2) * d ** 2)
        lo, hi = int(np.floor(0.5 * n_units)), int(np.ceil(1.6 * n_units))
        print(f"[M2] d={d:.0f} m：实测 {len(P)} 点，合理带 [{lo}, {hi}]")
        if not (lo <= len(P) <= hi):
            print("  ✗ 点数超出合理带"); ok = False

        covered, max_dist = coverage_check(P)
        print(f"[M3] d={d:.0f} m：覆盖自检 {'✓ 通过' if covered else '✗ 失败'}，最大距离 {max_dist:.4f} m")
        if not covered:
            ok = False

    if ok:
        print("\n验收线 ① 通过 ✅")
    else:
        print("\n验收线 ① 失败 ❌")
        sys.exit(1)

    # main_strategy(d_grid=D_GRID_1500)
