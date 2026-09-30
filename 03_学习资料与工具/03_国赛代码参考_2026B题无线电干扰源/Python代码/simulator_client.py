"""
SimulatorClient统一接口 v1.3
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Mapping, Any, Generic, TypeVar
from enum import Enum

T = TypeVar('T')

@dataclass(frozen=True)
class ActionOutcome(Generic[T]):
    """
    统一的动作结果封装

    修正历史：
    - P0-11: 声明为Generic[T]
    - P0-12: 拆分request_payload和result，避免覆盖
    - P0-15: 字段语义明确化
    """
    response_received: bool  # P0-15: 是否收到可解析HTTP响应（原executed字段）
    accepted: bool  # 动作是否被模拟器接受并登记（官方字段）
    request_id: str
    attempt_count: int

    # P0-12: 请求与响应分离
    request_payload: Mapping[str, Any]  # 原始请求体（不可变）
    response_payload: Optional[Mapping[str, Any]] = None  # 原始响应体
    result: Optional[T] = None  # 解析后的业务结果

    # HTTP相关
    http_status: Optional[int] = None
    transport_error: Optional[str] = None
    protocol_error: Optional[str] = None

    # 虚拟时间（仅accepted=True时有效）
    virtual_time_s: Optional[float] = None

    def is_success(self) -> bool:
        """是否成功执行且被接受"""
        return self.response_received and self.accepted


@dataclass(frozen=True)
class MeasureResult:
    """检测结果"""
    measure_result: str  # "no_signal" / "direction" / "near"
    svd_deg: Optional[float] = None  # 仅direction时有效


@dataclass(frozen=True)
class ClearResult:
    """清除结果"""
    clear_result: str  # "success" / "no_target_in_range"


@dataclass(frozen=True)
class ExitResult:
    """
    退出结果

    P0-14修正：exit_reason只接受官方值"user_exit"
    """
    exit_reason: str  # "user_exit"（官方协议唯一值）


@dataclass
class EnterResponse:
    """进入响应"""
    accepted: bool
    virtual_time_s: float
    max_virtual_duration_s: float
    max_real_duration_s: float
    remaining_real_duration_s: float
    error: Optional[str] = None


@dataclass
class PracticeOutcome:
    """
    演练测试结果补录（从模拟器界面手工记录）

    P1-11修正：get_clearance_rate()正确处理0和边界情况
    """
    total_sources_from_ui: Optional[int] = None
    cleared_sources_from_ui: Optional[int] = None
    case_code_from_ui: Optional[str] = None
    official_log_filename: Optional[str] = None

    def get_clearance_rate(self) -> Optional[float]:
        """
        计算清除率

        P1-11: 正确处理边界情况
        - 清除0个返回0.0（不是None）
        - 拒绝非法补录（总数≤0或清除>总数或负数）
        """
        if self.total_sources_from_ui is None or self.cleared_sources_from_ui is None:
            return None

        # 拒绝非法补录
        if self.total_sources_from_ui <= 0:
            raise ValueError(f"总源数必须>0，得到: {self.total_sources_from_ui}")

        if self.cleared_sources_from_ui < 0:
            raise ValueError(f"清除数不能为负，得到: {self.cleared_sources_from_ui}")

        if self.cleared_sources_from_ui > self.total_sources_from_ui:
            raise ValueError(f"清除数({self.cleared_sources_from_ui})不能大于总数({self.total_sources_from_ui})")

        return self.cleared_sources_from_ui / self.total_sources_from_ui


class SimulatorClient(ABC):
    """模拟器客户端统一接口"""

    @abstractmethod
    def enter(self) -> EnterResponse:
        """进入测试区域"""
        pass

    @abstractmethod
    def measure(self, x: float, y: float, channel: int) -> ActionOutcome[MeasureResult]:
        """检测"""
        pass

    @abstractmethod
    def clear(self, x: float, y: float, channel: int) -> ActionOutcome[ClearResult]:
        """清除"""
        pass

    @abstractmethod
    def exit(self) -> ActionOutcome[ExitResult]:
        """退出测试区域"""
        pass

    @abstractmethod
    def remaining_real_time_s(self) -> float:
        """获取剩余现实时间（秒）"""
        pass

    @abstractmethod
    def last_accepted_virtual_time_s(self) -> float:
        """获取最后一次accepted=True的虚拟时间"""
        pass
