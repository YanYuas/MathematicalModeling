"""
Q3 机器狗搜索定位与清除 —— Python 对照实现

本文件是 MATLAB 主程序（main_Q3Q4.m 及其函数集）的 Python 对照实现，
用于对同一套几何与策略做交叉验证：角域交会定位、最小包围圆、覆盖自检、
三路清除选择与频道状态机。

对照口径：
1. 三角网格覆盖（保证发现）
2. Q1 几何管线复用（交会定位）
3. 三路清除（直接/扫掠/homing）
4. 频道状态机（完备性判定）
5. 两阶段巡游（侦察→清除）

差异说明：半平面交、Welzl 最小包围圆、凸包判定等少数步骤在 MATLAB 侧为精确
实现，本文件保留占位或近似写法，交叉验证以 MATLAB 侧结果为准。本文件不直接
用于正式提交。

Q4 接口预留：
- halfplane()：半平面扇区
- is_surrounding()：surrounding 判定
- extend_grid_for_Q4()：外扩环带
"""

import numpy as np
import requests
import json
import uuid
import time
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

# 全局配置

# 容差配置
EPS_GEOM = 1e-9      # 几何比较容差
EPS_ANGLE = 1e-6     # 角度容差（度）

# 物理参数（题设）
R_DOMAIN = 1800.0    # 圆域半径 [m]
R_SENSOR = 1000.0    # 最坏接收半径 [m]（设计用）
R_CLEAR = 20.0       # 清除半径 [m]
R_NEAR = 5.0         # near 阈值 [m]
VELOCITY = 5.0       # 移动速度 [m/s]
EPSILON_DEG = 1.0    # 示向度误差半角 [°]
EPSILON_RAD = np.radians(EPSILON_DEG)

# 时间参数
T_MEASURE = 5.0      # 检测耗时 [s]
T_SWITCH = 1.0       # 切换频道耗时 [s]
T_CLEAR_SUCCESS = 5.0    # 清除成功耗时 [s]
T_CLEAR_FAIL = 3.0       # 清除失败耗时 [s]
T_RESERVE = 60.0     # 收尾预留 [s]
T_REAL_MAX = 1200.0  # 现实时间上限 [s]

# 覆盖网格参数（双轨）
D_GRID_1000 = 1000.0
D_GRID_1500 = 1500.0

# Homing 参数
LAMBDA_IDEAL = 2 * np.sin(EPSILON_RAD / 2)  # 0.0174531（理想收缩率）
LAMBDA_SAFE = np.sin(EPSILON_RAD) + 2 * EPSILON_RAD  # 0.0523590（工程收缩率）
R_STAR = 84.0369     # 扫掠/homing 拐点 [m]

# 频道参数
N_CHANNELS = 20
INITIAL_CHANNEL = 1

# 数据结构

@dataclass
class Point:
    """点"""
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
    """频道状态（五状态机）"""
    UNDISCOVERED = "未发现"
    LOCATED = "已定位"
    APPROACHING = "逼近中"
    CLEARED = "已清除"
    CONFIRMED_EMPTY = "已确认空"


@dataclass
class SourceInfo:
    """已定位的源信息"""
    channel: int
    L: List[Point]           # 定位区域（凸多边形）
    c_star: Point            # 最小包围圆圆心（清除点）
    R_MEC: float             # 最小包围圆半径
    discovered_at: Tuple[Point, Point]  # 发现的两个检测点


# M1：HTTP+JSON 客户端

class SimulatorClient:
    """
    与模拟器通信的唯一接口，处理幂等重试与现实时间跟踪
    """

    def __init__(self, base_url: str = "http://127.0.0.1:2026", timeout: float = 10.0):
        self.base_url = base_url
        self.timeout = timeout
        self.request_counter = 0
        self.remaining_real_time = T_REAL_MAX
        self.virtual_time = 0.0
        self.session = requests.Session()
        # 协议字段：附件2 §5.1 / §7.1 必填
        self.arena_id = "default"
        self.robot_id = "CUMCM2026"   # 运行期替换为真实参赛队号
        # 墙钟起点（表 1 第 4 列 程序运行时间 = /enter → 结束）
        import time as _t
        self.t_enter_wall = None
        self.elapsed_wall = 0.0

    def _new_request_id(self) -> str:
        """生成新的请求 ID"""
        self.request_counter += 1
        return f"req_{self.request_counter}_{uuid.uuid4().hex[:8]}"

    def _send_request(self, endpoint: str, payload: dict, request_id: Optional[str] = None) -> dict:
        """
        发送请求，处理幂等重试

        Args:
            endpoint: API 端点
            payload: 请求体
            request_id: 请求 ID（重试时复用）

        Returns:
            响应 JSON
        """
        if request_id is None:
            request_id = self._new_request_id()

        payload["request_id"] = request_id
        url = f"{self.base_url}{endpoint}"

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.post(url, json=payload, timeout=self.timeout)

                # 检查 HTTP 状态
                if response.status_code != 200:
                    print(f"[警告] HTTP 状态 {response.status_code}: {response.text}")
                    if response.status_code == 409:  # ID 冲突
                        raise ValueError("请求 ID 冲突，不应重试")
                    if attempt < max_retries - 1:
                        time.sleep(0.5)
                        continue
                    raise RuntimeError(f"HTTP 错误 {response.status_code}")

                data = response.json()

                # 检查 accepted
                if not data.get("accepted", False):
                    raise RuntimeError(f"请求被拒绝: {data}")

                # 更新现实时间
                if "remaining_real_duration_s" in data:
                    self.remaining_real_time = data["remaining_real_duration_s"]

                return data

            except requests.exceptions.Timeout:
                print(f"[警告] 请求超时，第 {attempt+1}/{max_retries} 次")
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                else:
                    raise

            except requests.exceptions.RequestException as e:
                print(f"[警告] 网络错误: {e}，第 {attempt+1}/{max_retries} 次")
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                else:
                    raise

    def enter(self) -> dict:
        """启动测试会话"""
        import time as _t
        resp = self._send_request("/enter", {
            "arena_id": self.arena_id, "robot_id": self.robot_id,   # 必填
        })
        self.t_enter_wall = _t.time()   # 墙钟起点（表 1 第 4 列）
        return resp

    def measure(self, x: float, y: float, channel: int, prev_channel: int) -> dict:
        """
        检测

        Args:
            x, y: 位置
            channel: 频道
            prev_channel: 前一频道（用于计算切换成本）

        Returns:
            响应：{"result": "no_signal"|"near"|"direction", "svd_deg": ...}
        """
        payload = {
            "arena_id": self.arena_id,        # 必填
            "robot_id": self.robot_id,        # 必填
            "position": {"x": x, "y": y},     # 嵌套结构
            "channel": channel,
        }
        resp = self._send_request("/measure", payload)

        # 更新虚拟时间
        move_time = 0.0  # 由调用者计算移动时间
        switch_time = T_SWITCH if channel != prev_channel else 0.0
        self.virtual_time += T_MEASURE + switch_time + move_time

        return resp

    def clear(self, x: float, y: float, channel: int) -> dict:
        """
        清除

        Returns:
            响应：{"result": "success"|"no_target_in_range"}
        """
        payload = {
            "arena_id": self.arena_id,        # 必填
            "robot_id": self.robot_id,        # 必填
            "position": {"x": x, "y": y},     # 嵌套结构
            "channel": channel,
        }
        resp = self._send_request("/clear", payload)

        # 更新虚拟时间（不含切换）
        if resp.get("result") == "success":
            self.virtual_time += T_CLEAR_SUCCESS
        else:
            self.virtual_time += T_CLEAR_FAIL

        return resp

    def exit(self) -> dict:
        """结束测试会话"""
        return self._send_request("/exit", {})

    def get_remaining_time(self) -> float:
        """获取剩余现实时间"""
        return self.remaining_real_time

    def check_time_safety(self) -> bool:
        """检查是否有足够时间继续"""
        return self.remaining_real_time > T_RESERVE + 0.1


# M2：三角网格生成

def generate_triangular_grid(d: float, R: float = R_DOMAIN) -> List[Point]:
    """
    生成间距 d 的三角格，圆域裁剪后得检测点集 P

    Args:
        d: 网格间距 [m]
        R: 圆域半径 [m]

    Returns:
        检测点列表

    公式：三角格布点
    """
    # 三角格基矢
    a1 = np.array([d, 0])
    a2 = np.array([d/2, np.sqrt(3)*d/2])

    # 生成范围（留 margin 避免边界漏）
    margin = d / np.sqrt(3)
    max_coord = R + margin
    n_max = int(np.ceil(max_coord / d)) + 1

    points = []
    for i in range(-n_max, n_max + 1):
        for j in range(-n_max, n_max + 1):
            p = i * a1 + j * a2
            # 圆域裁剪
            if np.linalg.norm(p) <= R:
                points.append(Point(p[0], p[1]))

    # 去重（欧氏距离 < 1e-6）
    unique_points = []
    for p in points:
        is_duplicate = False
        for q in unique_points:
            if (p - q).norm() < 1e-6:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_points.append(p)

    print(f"[网格] d={d:.1f} m, 生成 {len(unique_points)} 个检测点")
    return unique_points


# M3：覆盖自检

def coverage_check(P: List[Point], R_domain: float = R_DOMAIN,
                   R_sensor: float = R_SENSOR) -> Tuple[bool, float]:
    """
    验证 P 对 R_sensor-半径覆盖 D(0, R_domain)，含边界加密

    Args:
        P: 检测点集
        R_domain: 圆域半径
        R_sensor: 传感器半径

    Returns:
        (is_covered, max_distance)

    公式：覆盖半径判定
    """
    # 网格采样（步长 50 m）
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

    # 边界环带加密（1750~1800 m，步长 10 m）
    theta_samples = np.linspace(0, 2*np.pi, 360)
    for r in np.arange(1750, 1801, 10):
        for theta in theta_samples:
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            sample_points.append(np.array([x, y]))

    print(f"[覆盖自检] 采样点总数: {len(sample_points)}")

    # 检查每个采样点
    max_dist = 0.0
    failed_points = []

    for sp in sample_points:
        # 计算到最近检测点的距离
        min_dist = min((sp[0] - p.x)**2 + (sp[1] - p.y)**2 for p in P)
        min_dist = np.sqrt(min_dist)
        max_dist = max(max_dist, min_dist)

        if min_dist > R_sensor + EPS_GEOM:
            failed_points.append((sp, min_dist))

    is_covered = len(failed_points) == 0

    if is_covered:
        print(f"[覆盖自检] 通过，最大距离 {max_dist:.4f} m ≤ {R_sensor} m")
    else:
        print(f"[覆盖自检] 失败，{len(failed_points)} 个点超出覆盖")
        for sp, dist in failed_points[:5]:  # 只打印前 5 个
            print(f"  位置 ({sp[0]:.2f}, {sp[1]:.2f})，距离 {dist:.2f} m")

    return is_covered, max_dist


# M4：Q1 几何管线复用

def angdiff(phi: float, theta: float) -> float:
    """角度环绕差，范围 [-180, 180]"""
    diff = ((phi - theta + 180) % 360) - 180
    return diff


def wedge(S: Point, theta_deg: float, epsilon_deg: float = EPSILON_DEG) -> dict:
    """
    构造角域 W(S, θ, ε)

    复用 Q1 的角域定义
    """
    return {
        "station": S,
        "theta_deg": theta_deg,
        "epsilon_deg": epsilon_deg
    }


def intersect_wedges(wedges: List[dict]) -> List[Point]:
    """
    计算角域交集，返回定位区域 L（凸多边形顶点）

    复用 Q1 的角域求交

    本文件为占位实现：返回空列表；精确求交以 MATLAB 侧 polyshape 为准
    """
    # 占位实现：返回空列表表示未支持
    print("[警告] intersect_wedges 为占位实现")
    return []


def minimum_enclosing_circle(L: List[Point]) -> Tuple[Point, float]:
    """
    计算最小包围圆

    复用 Q1 的最小包围圆

    Returns:
        (c_star, R_MEC)：圆心和半径

    本文件为近似实现：以点集质心作圆心；精确算法见 MATLAB 侧 Welzl 实现
    """
    if not L:
        return Point(0, 0), float('inf')

    # 近似：用点集质心作圆心
    x_avg = sum(p.x for p in L) / len(L)
    y_avg = sum(p.y for p in L) / len(L)
    c_approx = Point(x_avg, y_avg)
    R_approx = max((p - c_approx).norm() for p in L)

    print("[警告] minimum_enclosing_circle 为近似实现")
    return c_approx, R_approx


def clip_to_domain(L: List[Point], R: float = R_DOMAIN) -> List[Point]:
    """
    圆域截断（Q3 新增）

    L* = L ∩ D(0, R)

    公式：凸多边形与圆的交集
    """
    # 占位实现：仅过滤超出圆域的顶点
    return [p for p in L if p.norm() <= R + EPS_GEOM]


# M6：频道状态机

class ChannelStateMachine:
    """
    管理 20 个频道的状态，完备性判定依赖它

    五状态：未发现 / 已定位 / 逼近中 / 已清除 / 已确认空
    """

    def __init__(self, n_channels: int = N_CHANNELS, n_positions: int = 8):
        self.n_channels = n_channels
        self.n_positions = n_positions

        # 状态
        self.state = {c: ChannelState.UNDISCOVERED for c in range(1, n_channels + 1)}

        # no_signal 计数器（用于"已确认空"判定）
        self.no_signal_positions = {c: set() for c in range(1, n_channels + 1)}  # 按检测点去重

        # 已定位的源信息
        self.sources: Dict[int, SourceInfo] = {}

    def update(self, channel: int, position_id: int, result: str,
               svd_deg: Optional[float] = None, L: Optional[List[Point]] = None):
        """
        更新频道状态

        Args:
            channel: 频道
            position_id: 检测点 ID
            result: "no_signal" | "near" | "direction"
            svd_deg: 示向度（direction 时）
            L: 定位区域（定位成功时）
        """
        if result == "no_signal":
            # 同一点重复 no_signal 不再累加；须覆盖 n_positions 个不同检测点才算确认空
            self.no_signal_positions[channel].add(position_id)
            # 全部不同检测点都 no_signal 时判为已确认空
            if len(self.no_signal_positions[channel]) >= self.n_positions:
                self.state[channel] = ChannelState.CONFIRMED_EMPTY
                print(f"[状态机] 频道 {channel} 已确认空")

        elif result == "direction":
            if self.state[channel] == ChannelState.UNDISCOVERED:
                self.state[channel] = ChannelState.LOCATED
                print(f"[状态机] 频道 {channel} 已定位")

        elif result == "near":
            self.state[channel] = ChannelState.LOCATED
            print(f"[状态机] 频道 {channel} 进入 near 范围")

    def mark_cleared(self, channel: int):
        """标记频道已清除"""
        self.state[channel] = ChannelState.CLEARED
        print(f"[状态机] 频道 {channel} 已清除")

    def check_completeness(self) -> Tuple[bool, dict]:
        """
        完备性判定

        Returns:
            (should_stop, status)
        """
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


# M11：三路清除选择

def direct_clear(c_star: Point, channel: int, client: SimulatorClient) -> Tuple[bool, float]:
    """
    直接清除（R_MEC ≤ 20）

    公式：清除半径判据
    """
    print(f"[清除] 直接清除 频道 {channel}，位置 {c_star.to_tuple()}")
    resp = client.clear(c_star.x, c_star.y, channel)
    success = (resp.get("result") == "success")
    cost = T_CLEAR_SUCCESS if success else T_CLEAR_FAIL
    return success, cost


def sweep_clear(L: List[Point], R_MEC: float, c_star: Point, channel: int,
                client: SimulatorClient) -> Tuple[bool, float]:
    """
    扫掠清除（20 < R_MEC ≤ 84.0369）

    公式：扫掠覆盖与清除次数
    """
    # 计算覆盖数
    N_sweep = int(np.ceil(1.2091996 * (R_MEC / 20.0)**2))
    print(f"[清除] 扫掠清除 频道 {channel}，R_MEC={R_MEC:.2f} m，需 {N_sweep} 次")

    # 生成半径 20 m 的圆盘覆盖 L 的中心（占位实现：用包围盒方网格采样）
    centers = []
    if L:
        # 简化：用 L 的包围盒
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

    # 逐个尝试清除
    # 不截断，按到 c* 的距离升序尝试（步距 20 m 时覆盖半径 14.14 ≤ 20，遍历全部必然命中）
    centers.sort(key=lambda p: (p.x - c_star.x)**2 + (p.y - c_star.y)**2)
    print(f"[清除] 扫掠候选中心 {len(centers)} 个（按距 c* 升序，不截断）")

    total_cost = 0.0
    for i, c in enumerate(centers):
        resp = client.clear(c.x, c.y, channel)
        if resp.get("result") == "success":
            total_cost += T_CLEAR_SUCCESS
            print(f"[清除] 扫掠成功，第 {i+1}/{N_sweep} 次")
            return True, total_cost
        else:
            total_cost += T_CLEAR_FAIL

    print(f"[清除] 扫掠失败（异常）")
    return False, total_cost


def homing_clear(L: List[Point], channel: int, client: SimulatorClient) -> Tuple[bool, float]:
    """
    Homing 逼近清除（R_MEC > 84.0369）

    公式：homing 收缩与终止判据
    """
    print(f"[清除] Homing 逼近 频道 {channel}")

    # 初始位置（L 的中心）
    if not L:
        return False, 0.0

    x_avg = sum(p.x for p in L) / len(L)
    y_avg = sum(p.y for p in L) / len(L)
    pos = Point(x_avg, y_avg)

    # 初始检测
    resp = client.measure(pos.x, pos.y, channel, channel)
    if resp.get("result") == "near":
        return direct_clear(pos, channel, client)

    theta_old = resp.get("svd_deg")
    total_cost = T_MEASURE

    # 迭代逼近
    max_iterations = 10
    for k in range(max_iterations):
        # 估计距离（从 L 的直径）
        D = max((p - q).norm() for p in L for q in L) if len(L) > 1 else 100.0
        r_hat = D / 2.0

        # 步长 = r_hat
        h = r_hat

        # 沿测得方位移动
        theta_rad = np.radians(theta_old)
        pos = pos + Point(h * np.cos(theta_rad), h * np.sin(theta_rad))

        # 检测
        resp = client.measure(pos.x, pos.y, channel, channel)
        total_cost += T_MEASURE

        if resp.get("result") == "near":
            success, cost = direct_clear(pos, channel, client)
            return success, total_cost + cost

        theta_new = resp.get("svd_deg")

        # 反向检测
        if abs(angdiff(theta_new, theta_old)) > 90.0:
            print(f"[Homing] 检测到反向，回退半步")
            pos = pos + Point(-0.5 * h * np.cos(theta_rad), -0.5 * h * np.sin(theta_rad))
            resp = client.measure(pos.x, pos.y, channel, channel)
            total_cost += T_MEASURE
            theta_new = resp.get("svd_deg")

        theta_old = theta_new

    print(f"[Homing] 达到最大迭代次数")
    return False, total_cost


def clear_source(source: SourceInfo, client: SimulatorClient) -> Tuple[bool, float, str]:
    """
    Q3/Q4 通用清除接口（三路选择）

    公式：三路清除选择
    """
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


# Q4 接口预留

def halfplane(G: Point, u: np.ndarray) -> dict:
    """
    半平面 H(G, u) = {X : (X-G)·u ≥ 0}

    公式：半平面定义
    """
    return {"center": G, "normal": u}


def is_surrounding(G: Point, P: List[Point], R_eff: float = R_SENSOR) -> bool:
    """
    判定 G 是否被 P 包围（surrounding 条件）

    G ∈ conv({p ∈ P : ‖p-G‖ ≤ R_eff})

    公式：surrounding 判定
    """
    # 占位实现：以包围盒近似凸包判定
    nearby_points = [p for p in P if (p - G).norm() <= R_eff]
    if len(nearby_points) < 3:
        return False

    # 近似：检查 G 是否落在 nearby_points 的包围盒内
    x_min = min(p.x for p in nearby_points)
    x_max = max(p.x for p in nearby_points)
    y_min = min(p.y for p in nearby_points)
    y_max = max(p.y for p in nearby_points)

    return x_min <= G.x <= x_max and y_min <= G.y <= y_max


def extend_grid_for_Q4(P: List[Point], d: float) -> List[Point]:
    """
    外扩环带（消除 Q4 边界死角）

    P_ext = P ∪ {圆域外扩 d/√3 的环带格点}

    公式：外扩环带布点
    """
    # 外扩距离
    delta = d / np.sqrt(3)
    R_outer = R_DOMAIN + delta

    # 生成外扩环带上的格点
    P_ext = P.copy()

    # 占位实现：外扩环带格点尚未生成

    print(f"[Q4扩展] 外扩环带 d/√3 = {delta:.2f} m，原 {len(P)} 点 → {len(P_ext)} 点")
    return P_ext


# 主策略框架

def main_strategy(d_grid: float = D_GRID_1500):
    """
    Q3 主策略：两阶段巡游

    阶段 A：侦察（发现所有源）
    阶段 B：清除（优化顺序清除）
    """
    print(" " * 60)
    print("Q3 多源自动定位与清除策略")
    print(" " * 60)

    # 初始化客户端
    client = SimulatorClient()

    # 启动会话
    print("\n[阶段 0] 启动会话...")
    resp = client.enter()
    print(f"剩余现实时间: {client.remaining_real_time:.1f} s")

    # 生成检测点集
    print(f"\n[阶段 1] 生成检测点集 (d={d_grid} m)...")
    P = generate_triangular_grid(d_grid)

    # 覆盖自检
    print("\n[阶段 2] 覆盖自检...")
    is_covered, max_dist = coverage_check(P)
    if not is_covered:
        print("[错误] 覆盖自检失败，退出")
        return

    # 初始化状态机
    fsm = ChannelStateMachine(n_channels=N_CHANNELS, n_positions=len(P))

    # 阶段 A：侦察
    print(f"\n[阶段 A] 侦察阶段（扫描 {len(P)} 个检测点）...")
    # 该步骤在 MATLAB 主程序阶段 A 中实现，本对照实现未展开

    # 阶段 B：清除
    print("\n[阶段 B] 清除阶段...")
    # 该步骤在 MATLAB 主程序阶段 B 中实现，本对照实现未展开

    # 收尾确认
    print("\n[阶段 C] 收尾确认...")
    should_stop, status = fsm.check_completeness()
    print(f"已清除: {status['cleared']}, 已确认空: {status['confirmed_empty']}, 剩余: {status['remaining']}")

    # 结束会话
    print("\n[结束] 调用 /exit...")
    client.exit()

    print(f"\n虚拟时间: {client.virtual_time:.2f} s")
    print(f"清除比例: {status['cleared']} / {status['cleared'] + status['remaining']}")
    print(" " * 60)


if __name__ == "__main__":
    # 自检（不依赖模拟器）
    import sys
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        sys.stdout.reconfigure(encoding="utf-8")   # Windows GBK 控制台需显式指定输出编码

    print("[测试] 运行验收线检查...")
    ok = True

    # 断言 2：间距约束 d ≤ √3·R_sensor（1732.0508 m）
    D_MAX = np.sqrt(3) * R_SENSOR
    print(f"[断言2] d 上限 = √3·R_sensor = {D_MAX:.4f} m")
    for d in (D_GRID_1000, D_GRID_1500):
        if d > D_MAX + EPS_GEOM:
            print(f"  d={d} 超过上限"); ok = False
    if ok:
        print("  通过")

    # 断言 3：单元数下界（平面圆盘覆盖最优密度 2π/(3√3)，N ≥ 4）
    N_UNITS_LB = 4
    for d in (D_GRID_1000, D_GRID_1500):
        n_units = np.pi * R_DOMAIN**2 / ((np.sqrt(3) / 2) * d**2)
        print(f"[断言3] d={d:.0f} m：圆域单元数 ≈ {n_units:.5f}（下界要求 ≥ {N_UNITS_LB}）")
        if n_units < N_UNITS_LB - EPS_GEOM:
            print("  不满足下界"); ok = False
    if ok:
        print("  通过")

    # M2 + M3：网格点数与覆盖自检（两档都跑）
    #   点数期望由单元数互验：d=1500 ， 5.224 单元 ， 7 点；d=1000 ， 11.75 单元 ， 13 点。
    #   裁剪边界效应使点数约为单元数的 1.1~1.5 倍，故取 [0.5×单元数, 1.6×单元数] 作合理带。
    #   点数期望由单元数互验，两档共用同一合理带。
    for d, expect_pts in ((D_GRID_1500, 7), (D_GRID_1000, 13)):
        P = generate_triangular_grid(d)
        n_units = np.pi * R_DOMAIN**2 / ((np.sqrt(3) / 2) * d**2)
        lo, hi = int(np.floor(0.5 * n_units)), int(np.ceil(1.6 * n_units))
        print(f"[M2] d={d:.0f} m：实测 {len(P)} 点，合理带 [{lo}, {hi}]，本次实测基准 {expect_pts}")
        if not (lo <= len(P) <= hi):
            print("  点数超出合理带"); ok = False

        covered, max_dist = coverage_check(P)
        print(f"[M3] d={d:.0f} m：覆盖自检 {'通过' if covered else '失败'}，最大距离 {max_dist:.4f} m")
        if not covered:
            ok = False

    print()
    if ok:
        print("[测试] 自检通过")
    else:
        print("[测试] 自检失败")
        sys.exit(1)

    # 主策略（需要模拟器）
    # main_strategy(d_grid=D_GRID_1500)
