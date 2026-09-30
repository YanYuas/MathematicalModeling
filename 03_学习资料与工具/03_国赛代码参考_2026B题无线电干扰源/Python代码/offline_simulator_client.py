"""
离线仿真实现 v1.3
"""
import numpy as np
import time
import json
import math
from pathlib import Path
from typing import List, Set, Tuple, Optional, Dict
from dataclasses import dataclass

from simulator_client import (
    SimulatorClient, ActionOutcome, MeasureResult, ClearResult,
    ExitResult, EnterResponse
)


@dataclass(frozen=True)
class InterferenceSource:
    """
    干扰源定义

    P1补充：构造时校验唯一性和完整性
    """
    channel: int
    x: float
    y: float
    radius: float
    is_directional: bool = False
    direction_deg: Optional[float] = None

    def __post_init__(self):
        """校验源配置"""
        if not (1 <= self.channel <= 20):
            raise ValueError(f"频道必须在1-20之间: {self.channel}")

        if self.is_directional and self.direction_deg is None:
            raise ValueError(f"定向源必须提供direction_deg (channel={self.channel})")

        if not math.isfinite(self.x) or not math.isfinite(self.y):
            raise ValueError(f"源坐标非法: ({self.x}, {self.y})")

        if not (0 < self.radius < 10000):
            raise ValueError(f"源半径非法: {self.radius}")


class OfflineSimulatorClient(SimulatorClient):
    """
    离线仿真实现（P0全量修正版）

    修正历史：
    - P0-13: clear()失败只加3秒，成功加5秒
    - P0-14: exit()返回"user_exit"（与HTTP一致）
    - P0-15: executed改名为response_received
    - P1-9: svd_deg归一化到[0, 360)
    - P1-10: 生成唯一request_id和日志
    - P1-12: exit()后禁止新动作
    - P1-13: 复用输入校验，明确虚拟时间上限行为
    """

    def __init__(self,
                 sources: List[InterferenceSource],
                 robot_id: str = "OFFLINE",
                 svd_error_deg: float = 1.0,
                 max_virtual_duration_s: float = 360000.0,
                 random_seed: int = 42,
                 log_dir: str = "./logs"):

        # P1: 校验源配置唯一性
        channels = [s.channel for s in sources]
        if len(channels) != len(set(channels)):
            raise ValueError(f"频道不唯一: {channels}")

        self.sources = sources
        self.robot_id = robot_id
        self.svd_error_deg = svd_error_deg
        self.max_virtual_duration_s = max_virtual_duration_s

        # 状态
        self._virtual_time = 0.0
        self._current_channel = 1
        self._current_position = (0.0, 0.0)
        self._cleared_channels: Set[int] = set()
        self._entered = False
        self._exited = False
        self._request_counter = 0

        # 误差缓存
        self._rng = np.random.RandomState(random_seed)
        self._svd_error_cache: Dict[Tuple[int, float, float], float] = {}

        # 日志
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self._jsonl_path = self._log_dir / f"offline_{timestamp}.jsonl"

    def _validate_input(self, x: float, y: float, channel: int):
        """输入校验（与HTTP共用逻辑）"""
        if not isinstance(channel, int) or isinstance(channel, bool):
            raise ValueError(f"频道必须是整数，得到: {channel} (type={type(channel).__name__})")

        if not (1 <= channel <= 20):
            raise ValueError(f"频道必须在1-20之间，得到: {channel}")

        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError(f"坐标必须是有限数: ({x}, {y})")

        if not (-2000000 <= x <= 2000000 and -2000000 <= y <= 2000000):
            raise ValueError(f"坐标超出合理范围: ({x}, {y})")

    def _new_request_id(self) -> str:
        """生成唯一request_id"""
        self._request_counter += 1
        return f"offline_req_{self._request_counter}"

    def _normalize_angle(self, angle: float) -> float:
        """归一化角度到[0, 360)"""
        result = angle % 360.0
        if result < 0:
            result += 360.0
        return result

    def _get_svd_error(self, channel: int, x: float, y: float) -> float:
        """同地点返回相同误差"""
        key = (channel, round(x, 2), round(y, 2))
        if key not in self._svd_error_cache:
            self._svd_error_cache[key] = self._rng.uniform(
                -self.svd_error_deg,
                self.svd_error_deg
            )
        return self._svd_error_cache[key]

    def _find_source(self, channel: int) -> Optional[InterferenceSource]:
        """查找指定频道的干扰源"""
        for source in self.sources:
            if source.channel == channel:
                return source
        return None

    def _is_in_directional_sector(self, source: InterferenceSource,
                                  robot_x: float, robot_y: float) -> bool:
        """判断机器人是否在定向源的有效扇区内（±90°）"""
        if not source.is_directional:
            return True

        angle_to_robot = np.degrees(np.arctan2(
            robot_y - source.y,
            robot_x - source.x
        ))
        angle_to_robot = self._normalize_angle(angle_to_robot)

        source_dir = self._normalize_angle(source.direction_deg)

        angle_diff = abs(angle_to_robot - source_dir)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff

        return angle_diff <= 90.0

    def _log_action(self, outcome: ActionOutcome):
        """记录离线日志"""
        log_entry = {
            "timestamp": time.time(),
            "request_id": outcome.request_id,
            "request_payload": dict(outcome.request_payload),
            "response_received": outcome.response_received,  # P0-15
            "accepted": outcome.accepted,
            "virtual_time_s": outcome.virtual_time_s,
            "result": str(outcome.result) if outcome.result else None
        }

        with open(self._jsonl_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False, default=str) + '\n')

    def enter(self) -> EnterResponse:
        """实现：进入测试"""
        self._entered = True
        self._exited = False
        self._virtual_time = 0.0
        self._current_channel = 1
        self._current_position = (0.0, 0.0)
        self._cleared_channels.clear()

        return EnterResponse(
            accepted=True,
            virtual_time_s=0.0,
            max_virtual_duration_s=self.max_virtual_duration_s,
            max_real_duration_s=float('inf'),
            remaining_real_duration_s=float('inf')
        )

    def measure(self, x: float, y: float, channel: int) -> ActionOutcome[MeasureResult]:
        """实现：检测"""
        self._validate_input(x, y, channel)

        request_id = self._new_request_id()
        payload = {"position": {"x": x, "y": y}, "channel": channel}

        # 检查是否已退出
        if not self._entered or self._exited:
            outcome = ActionOutcome(
                response_received=False,  # P0-15
                accepted=False,
                request_id=request_id,
                attempt_count=1,
                request_payload=payload,
                transport_error="必须先调用enter()且未调用exit()"
            )
            self._log_action(outcome)
            return outcome

        # 检查虚拟时间上限
        if self._virtual_time >= self.max_virtual_duration_s:
            outcome = ActionOutcome(
                response_received=False,
                accepted=False,
                request_id=request_id,
                attempt_count=1,
                request_payload=payload,
                transport_error="虚拟时间已达上限"
            )
            self._log_action(outcome)
            return outcome

        # 计算移动时间
        last_x, last_y = self._current_position
        move_dist = np.sqrt((x - last_x)**2 + (y - last_y)**2)
        move_time = move_dist / 5.0

        # 计算频道切换时间
        switch_time = 1.0 if channel != self._current_channel else 0.0

        # 检测时间
        measure_time = 5.0

        # 累加虚拟时间
        self._virtual_time += move_time + switch_time + measure_time

        # 更新状态
        self._current_position = (x, y)
        self._current_channel = channel

        # 查找干扰源
        source = self._find_source(channel)

        if source is None or channel in self._cleared_channels:
            outcome = ActionOutcome(
                response_received=True,  # P0-15
                accepted=True,
                request_id=request_id,
                attempt_count=1,
                request_payload=payload,
                response_payload={"measure_result": "no_signal"},
                result=MeasureResult(measure_result="no_signal"),
                virtual_time_s=self._virtual_time
            )
            self._log_action(outcome)
            return outcome

        # 计算距离
        dist = np.sqrt((x - source.x)**2 + (y - source.y)**2)

        # 超出有效接收半径
        if dist > source.radius:
            outcome = ActionOutcome(
                response_received=True,
                accepted=True,
                request_id=request_id,
                attempt_count=1,
                request_payload=payload,
                response_payload={"measure_result": "no_signal"},
                result=MeasureResult(measure_result="no_signal"),
                virtual_time_s=self._virtual_time
            )
            self._log_action(outcome)
            return outcome

        # 检查定向扇区
        if not self._is_in_directional_sector(source, x, y):
            outcome = ActionOutcome(
                response_received=True,
                accepted=True,
                request_id=request_id,
                attempt_count=1,
                request_payload=payload,
                response_payload={"measure_result": "no_signal"},
                result=MeasureResult(measure_result="no_signal"),
                virtual_time_s=self._virtual_time
            )
            self._log_action(outcome)
            return outcome

        # near判定
        if dist <= 5.0:
            outcome = ActionOutcome(
                response_received=True,
                accepted=True,
                request_id=request_id,
                attempt_count=1,
                request_payload=payload,
                response_payload={"measure_result": "near"},
                result=MeasureResult(measure_result="near"),
                virtual_time_s=self._virtual_time
            )
            self._log_action(outcome)
            return outcome

        # direction判定
        angle = np.degrees(np.arctan2(source.y - y, source.x - x))
        error = self._get_svd_error(channel, x, y)
        svd_deg = self._normalize_angle(angle + error)

        outcome = ActionOutcome(
            response_received=True,
            accepted=True,
            request_id=request_id,
            attempt_count=1,
            request_payload=payload,
            response_payload={"measure_result": "direction", "svd_deg": svd_deg},
            result=MeasureResult(measure_result="direction", svd_deg=svd_deg),
            virtual_time_s=self._virtual_time
        )
        self._log_action(outcome)
        return outcome

    def clear(self, x: float, y: float, channel: int) -> ActionOutcome[ClearResult]:
        """
        实现：清除

        P0-13: 失败只加3秒（光学定位），成功加5秒（光学+清除）
        """
        self._validate_input(x, y, channel)

        request_id = self._new_request_id()
        payload = {"position": {"x": x, "y": y}, "channel": channel}

        # 检查是否已退出
        if not self._entered or self._exited:
            outcome = ActionOutcome(
                response_received=False,
                accepted=False,
                request_id=request_id,
                attempt_count=1,
                request_payload=payload,
                transport_error="必须先调用enter()且未调用exit()"
            )
            self._log_action(outcome)
            return outcome

        # 检查虚拟时间上限
        if self._virtual_time >= self.max_virtual_duration_s:
            outcome = ActionOutcome(
                response_received=False,
                accepted=False,
                request_id=request_id,
                attempt_count=1,
                request_payload=payload,
                transport_error="虚拟时间已达上限"
            )
            self._log_action(outcome)
            return outcome

        # 计算移动时间
        last_x, last_y = self._current_position
        move_dist = np.sqrt((x - last_x)**2 + (y - last_y)**2)
        move_time = move_dist / 5.0

        # 先加移动时间
        self._virtual_time += move_time

        # 更新位置（不更新频道）
        self._current_position = (x, y)

        # 查找干扰源
        source = self._find_source(channel)

        if source is None or channel in self._cleared_channels:
            # P0-13: 失败只加3秒
            self._virtual_time += 3.0

            outcome = ActionOutcome(
                response_received=True,
                accepted=True,
                request_id=request_id,
                attempt_count=1,
                request_payload=payload,
                response_payload={"clear_result": "no_target_in_range"},
                result=ClearResult(clear_result="no_target_in_range"),
                virtual_time_s=self._virtual_time
            )
            self._log_action(outcome)
            return outcome

        # 清除只检查距离
        dist = np.sqrt((x - source.x)**2 + (y - source.y)**2)

        if dist > 20.0:
            # P0-13: 失败只加3秒
            self._virtual_time += 3.0

            outcome = ActionOutcome(
                response_received=True,
                accepted=True,
                request_id=request_id,
                attempt_count=1,
                request_payload=payload,
                response_payload={"clear_result": "no_target_in_range"},
                result=ClearResult(clear_result="no_target_in_range"),
                virtual_time_s=self._virtual_time
            )
            self._log_action(outcome)
            return outcome

        # P0-13: 清除成功加5秒（光学3秒+清除2秒）
        self._virtual_time += 5.0
        self._cleared_channels.add(channel)

        outcome = ActionOutcome(
            response_received=True,
            accepted=True,
            request_id=request_id,
            attempt_count=1,
            request_payload=payload,
            response_payload={"clear_result": "success"},
            result=ClearResult(clear_result="success"),
            virtual_time_s=self._virtual_time
        )
        self._log_action(outcome)
        return outcome

    def exit(self) -> ActionOutcome[ExitResult]:
        """
        实现：退出测试

        P0-14: 返回"user_exit"（与HTTP一致）
        """
        request_id = self._new_request_id()
        payload = {}

        if not self._entered:
            outcome = ActionOutcome(
                response_received=False,
                accepted=False,
                request_id=request_id,
                attempt_count=1,
                request_payload=payload,
                transport_error="必须先调用enter()"
            )
            self._log_action(outcome)
            return outcome

        # 标记已退出
        self._exited = True

        outcome = ActionOutcome(
            response_received=True,
            accepted=True,
            request_id=request_id,
            attempt_count=1,
            request_payload=payload,
            response_payload={"exit_reason": "user_exit"},  # P0-14: 与HTTP统一
            result=ExitResult(exit_reason="user_exit"),
            virtual_time_s=self._virtual_time
        )
        self._log_action(outcome)
        return outcome

    def remaining_real_time_s(self) -> float:
        """离线无现实时间限制"""
        return float('inf')

    def last_accepted_virtual_time_s(self) -> float:
        """返回当前虚拟时间"""
        return self._virtual_time
