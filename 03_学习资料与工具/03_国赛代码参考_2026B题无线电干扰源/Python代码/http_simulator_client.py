"""
HTTP协议实现 v1.3
"""
import requests
import time
import uuid
import json
import math
from pathlib import Path
from typing import Optional, Mapping, Any

from simulator_client import (
    SimulatorClient, ActionOutcome, MeasureResult, ClearResult,
    ExitResult, EnterResponse
)


class HttpSimulatorClient(SimulatorClient):
    """
    HTTP协议实现（P0全量修正版）

    修正历史：
    - P0-10: _build_payload()包含request_id
    - P0-11: ActionOutcome使用Generic[T]
    - P0-12: request_payload和result分离
    - P0-14: exit()强制校验exit_reason="user_exit"
    - P0-15: executed改名为response_received
    - P1-14: 响应结构校验
    """

    def __init__(self,
                 robot_id: str,
                 arena_id: str = "default",
                 base_url: str = "http://127.0.0.1:2026",
                 timeout: float = 10.0,
                 max_retries: int = 3,
                 log_dir: str = "./logs"):

        self.robot_id = robot_id
        self.arena_id = arena_id
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

        # 状态
        self._session = requests.Session()
        self._request_counter = 0
        self._last_accepted_virtual_time = 0.0
        self._current_channel = 1
        self._current_position = (0.0, 0.0)
        self._enter_wall_time: Optional[float] = None
        self._enter_remaining_real: Optional[float] = None

        # 日志
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self._jsonl_path = self._log_dir / f"test_{timestamp}.jsonl"

    def _validate_input(self, x: float, y: float, channel: int):
        """
        输入校验（HTTP和离线共用）

        P1补充：拒绝小数频道、非法数值
        """
        # 频道必须是整数
        if not isinstance(channel, int) or isinstance(channel, bool):
            raise ValueError(f"频道必须是整数，得到: {channel} (type={type(channel).__name__})")

        if not (1 <= channel <= 20):
            raise ValueError(f"频道必须在1-20之间，得到: {channel}")

        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError(f"坐标必须是有限数: ({x}, {y})")

        if not (-2000000 <= x <= 2000000 and -2000000 <= y <= 2000000):
            raise ValueError(f"坐标超出合理范围: ({x}, {y})")

    def _new_request_id(self) -> str:
        """生成新的请求ID"""
        self._request_counter += 1
        return f"req_{self._request_counter}_{uuid.uuid4().hex[:8]}"

    def _build_payload(self, request_id: str, extra: Mapping[str, Any]) -> dict[str, Any]:
        """
        P0-10: 构建完整请求体（包含request_id）
        """
        return {
            "arena_id": self.arena_id,
            "robot_id": self.robot_id,
            "request_id": request_id,
            **extra,
        }

    def _validate_response_structure(self, data: dict, endpoint: str) -> Optional[str]:
        """
        响应结构校验

        P0-14: 成功/exit时强制校验exit_reason="user_exit"
        P1补充: 校验virtual_time_s为有限非负数、svd_deg范围等
        """
        if not isinstance(data, dict):
            return "响应不是JSON对象"

        if "accepted" not in data:
            return "缺少accepted字段"

        if not isinstance(data.get("accepted"), bool):
            return "accepted不是布尔值"

        if data["accepted"]:
            if "virtual_time_s" not in data:
                return "accepted=true但缺少virtual_time_s"

            vt = data["virtual_time_s"]
            if not isinstance(vt, (int, float)):
                return "virtual_time_s不是数字"

            if not math.isfinite(vt) or vt < 0:
                return f"virtual_time_s非法: {vt}"

        # /enter特定校验
        if endpoint == "/enter" and data.get("accepted"):
            required_fields = [
                "max_virtual_duration_s",
                "max_real_duration_s",
                "remaining_real_duration_s"
            ]
            for field in required_fields:
                if field not in data:
                    return f"enter响应缺少{field}"

                val = data[field]
                if not isinstance(val, (int, float)):
                    return f"{field}不是数字"

                if not math.isfinite(val) or val < 0:
                    return f"{field}非法: {val}"

        # /measure特定校验
        if endpoint == "/measure" and data.get("accepted"):
            if "measure_result" not in data:
                return "measure响应缺少measure_result"

            result = data["measure_result"]
            if result not in ["no_signal", "direction", "near"]:
                return f"measure_result值非法: {result}"

            if result == "direction":
                if "svd_deg" not in data:
                    return "direction响应缺少svd_deg"

                svd = data["svd_deg"]
                if not isinstance(svd, (int, float)):
                    return "svd_deg不是数字"

                if not math.isfinite(svd):
                    return "svd_deg不是有限数"

                # P1: 校验范围[0, 360)
                if not (0 <= svd < 360):
                    return f"svd_deg超出范围[0, 360): {svd}"

        # /clear特定校验
        if endpoint == "/clear" and data.get("accepted"):
            if "clear_result" not in data:
                return "clear响应缺少clear_result"

            result = data["clear_result"]
            if result not in ["success", "no_target_in_range"]:
                return f"clear_result值非法: {result}"

        # P0-14: /exit特定校验
        if endpoint == "/exit" and data.get("accepted"):
            if "exit_reason" not in data:
                return "exit响应缺少exit_reason"

            reason = data["exit_reason"]
            if reason != "user_exit":
                return f"exit_reason非法: {reason}（官方协议为'user_exit'）"

        return None

    def _send_request(self, endpoint: str, request_id: str,
                     payload: dict[str, Any]) -> ActionOutcome:
        """
        发送HTTP请求

        P0-15: response_received取代executed
        """
        wall_start = time.monotonic()

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._session.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    timeout=self.timeout
                )

                wall_elapsed = time.monotonic() - wall_start

                # 检查HTTP状态
                if response.status_code != 200:
                    # P0-16: 解析非200响应的JSON（如果存在）
                    error_payload = None
                    try:
                        error_payload = response.json()
                    except (json.JSONDecodeError, ValueError):
                        pass  # 无法解析则留空

                    outcome = ActionOutcome(
                        response_received=False,  # P0-15
                        accepted=False,
                        request_id=request_id,
                        attempt_count=attempt,
                        request_payload=payload,
                        response_payload=error_payload,  # P0-16: 记录错误响应
                        http_status=response.status_code,
                        transport_error=f"HTTP {response.status_code}"
                    )
                    self._log_action(outcome, wall_elapsed)

                    # 400/409/415不重试
                    if response.status_code in [400, 409, 415]:
                        return outcome

                    if attempt < self.max_retries:
                        time.sleep(0.5)
                        continue
                    return outcome

                # 解析JSON
                try:
                    data = response.json()
                except (json.JSONDecodeError, ValueError) as e:
                    outcome = ActionOutcome(
                        response_received=False,
                        accepted=False,
                        request_id=request_id,
                        attempt_count=attempt,
                        request_payload=payload,
                        http_status=200,
                        protocol_error=f"JSON解析失败: {e}"
                    )
                    self._log_action(outcome, wall_elapsed)
                    return outcome

                # 响应结构校验
                struct_error = self._validate_response_structure(data, endpoint)
                if struct_error:
                    outcome = ActionOutcome(
                        response_received=False,
                        accepted=False,
                        request_id=request_id,
                        attempt_count=attempt,
                        request_payload=payload,
                        response_payload=data,
                        http_status=200,
                        protocol_error=struct_error
                    )
                    self._log_action(outcome, wall_elapsed)
                    return outcome

                # 检查accepted
                accepted = data["accepted"]
                virtual_time = data.get("virtual_time_s") if accepted else None

                outcome = ActionOutcome(
                    response_received=True,  # P0-15: 收到可解析响应
                    accepted=accepted,
                    request_id=request_id,
                    attempt_count=attempt,
                    request_payload=payload,
                    response_payload=data,
                    http_status=200,
                    virtual_time_s=virtual_time
                )

                # 仅accepted=True时更新
                if accepted and virtual_time is not None:
                    self._last_accepted_virtual_time = virtual_time

                self._log_action(outcome, wall_elapsed)
                return outcome

            except requests.Timeout:
                if attempt < self.max_retries:
                    time.sleep(0.5)
                    continue

                outcome = ActionOutcome(
                    response_received=False,
                    accepted=False,
                    request_id=request_id,
                    attempt_count=attempt,
                    request_payload=payload,
                    transport_error="请求超时"
                )
                self._log_action(outcome, time.monotonic() - wall_start)
                return outcome

            except requests.RequestException as e:
                if attempt < self.max_retries:
                    time.sleep(0.5)
                    continue

                outcome = ActionOutcome(
                    response_received=False,
                    accepted=False,
                    request_id=request_id,
                    attempt_count=attempt,
                    request_payload=payload,
                    transport_error=str(e)
                )
                self._log_action(outcome, time.monotonic() - wall_start)
                return outcome

        raise RuntimeError("不应到达此处")

    def _log_action(self, outcome: ActionOutcome, wall_elapsed: float):
        """JSON Lines追加日志"""
        log_entry = {
            "timestamp": time.time(),
            "wall_elapsed_s": wall_elapsed,
            "request_id": outcome.request_id,
            "attempt_count": outcome.attempt_count,
            "request_payload": dict(outcome.request_payload),
            "response_payload": dict(outcome.response_payload) if outcome.response_payload else None,
            "http_status": outcome.http_status,
            "response_received": outcome.response_received,  # P0-15
            "accepted": outcome.accepted,
            "virtual_time_s": outcome.virtual_time_s,
            "transport_error": outcome.transport_error,
            "protocol_error": outcome.protocol_error
        }

        with open(self._jsonl_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def enter(self) -> EnterResponse:
        """实现：进入测试"""
        request_id = self._new_request_id()
        payload = self._build_payload(request_id, {})

        outcome = self._send_request("/enter", request_id, payload)

        if not outcome.is_success():
            return EnterResponse(
                accepted=False,
                virtual_time_s=0.0,
                max_virtual_duration_s=0.0,
                max_real_duration_s=0.0,
                remaining_real_duration_s=0.0,
                error=outcome.transport_error or outcome.protocol_error or "未接受"
            )

        data = outcome.response_payload

        # 记录墙钟起点
        self._enter_wall_time = time.monotonic()
        self._enter_remaining_real = data["remaining_real_duration_s"]

        # 初始化状态
        self._current_channel = 1
        self._current_position = (0.0, 0.0)

        return EnterResponse(
            accepted=True,
            virtual_time_s=data["virtual_time_s"],
            max_virtual_duration_s=data["max_virtual_duration_s"],
            max_real_duration_s=data["max_real_duration_s"],
            remaining_real_duration_s=data["remaining_real_duration_s"]
        )

    def measure(self, x: float, y: float, channel: int) -> ActionOutcome[MeasureResult]:
        """实现：检测"""
        self._validate_input(x, y, channel)

        request_id = self._new_request_id()
        payload = self._build_payload(request_id, {
            "position": {"x": x, "y": y},
            "channel": channel
        })

        outcome = self._send_request("/measure", request_id, payload)

        if outcome.is_success():
            # 更新状态
            self._current_position = (x, y)
            self._current_channel = channel

            # 解析结果
            data = outcome.response_payload
            measure_result = data["measure_result"]
            svd_deg = data.get("svd_deg") if measure_result == "direction" else None

            # P0-12: 填充result字段，不覆盖payload
            return ActionOutcome(
                response_received=outcome.response_received,
                accepted=outcome.accepted,
                request_id=outcome.request_id,
                attempt_count=outcome.attempt_count,
                request_payload=outcome.request_payload,
                response_payload=outcome.response_payload,
                result=MeasureResult(
                    measure_result=measure_result,
                    svd_deg=svd_deg
                ),
                http_status=outcome.http_status,
                virtual_time_s=outcome.virtual_time_s
            )

        return outcome

    def clear(self, x: float, y: float, channel: int) -> ActionOutcome[ClearResult]:
        """实现：清除"""
        self._validate_input(x, y, channel)

        request_id = self._new_request_id()
        payload = self._build_payload(request_id, {
            "position": {"x": x, "y": y},
            "channel": channel
        })

        outcome = self._send_request("/clear", request_id, payload)

        if outcome.is_success():
            # 更新位置（不更新频道）
            self._current_position = (x, y)

            # 解析结果
            data = outcome.response_payload
            clear_result = data["clear_result"]

            return ActionOutcome(
                response_received=outcome.response_received,
                accepted=outcome.accepted,
                request_id=outcome.request_id,
                attempt_count=outcome.attempt_count,
                request_payload=outcome.request_payload,
                response_payload=outcome.response_payload,
                result=ClearResult(clear_result=clear_result),
                http_status=outcome.http_status,
                virtual_time_s=outcome.virtual_time_s
            )

        return outcome

    def exit(self) -> ActionOutcome[ExitResult]:
        """
        实现：退出测试

        P0-14: exit_reason已在_validate_response_structure强制校验
        """
        request_id = self._new_request_id()
        payload = self._build_payload(request_id, {})

        outcome = self._send_request("/exit", request_id, payload)

        if outcome.is_success():
            data = outcome.response_payload
            exit_reason = data["exit_reason"]  # P0-14: 已验证为"user_exit"

            return ActionOutcome(
                response_received=outcome.response_received,
                accepted=outcome.accepted,
                request_id=outcome.request_id,
                attempt_count=outcome.attempt_count,
                request_payload=outcome.request_payload,
                response_payload=outcome.response_payload,
                result=ExitResult(exit_reason=exit_reason),
                http_status=outcome.http_status,
                virtual_time_s=outcome.virtual_time_s
            )

        return outcome

    def remaining_real_time_s(self) -> float:
        """动态计算剩余现实时间"""
        if self._enter_wall_time is None:
            return 0.0

        elapsed = time.monotonic() - self._enter_wall_time
        remaining = self._enter_remaining_real - elapsed

        # 预留30秒收尾
        return max(0.0, remaining - 30.0)

    def last_accepted_virtual_time_s(self) -> float:
        """返回最后一次accepted=True的虚拟时间"""
        return self._last_accepted_virtual_time
