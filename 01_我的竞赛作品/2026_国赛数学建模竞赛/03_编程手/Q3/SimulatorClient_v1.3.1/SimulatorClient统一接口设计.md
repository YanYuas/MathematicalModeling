# SimulatorClient 统一接口设计文档

> ## ⚠️ 版本关系注记（总控，2026-09-12）——**读本文前先看这条**
>
> 本文档是 **v1.0「设计阶段」产物**（文末自述"待审核：请确认设计方案后进入 Phase 2 实施"，落款时间早于代码），
> **不是已实现代码的说明**。实现过程（→ v1.3.1）**改了类型设计**，本文档未随之更新。
>
> **实查差异（本文档 ≠ `src/` 实际代码）**：
>
> | 项 | 本文档（v1.0 设计） | 实际代码（v1.3.1） |
> |---|---|---|
> | 结果类型 | `MeasureResult` / `ClearResult` 为 **`Enum`** | 均为 **`@dataclass` + 字符串字段**（`measure_result` / `clear_result`） |
> | 清除失败取值 | `ClearResult.FAILURE = "failure"` | **`"no_target_in_range"`**（与官方协议一致；文档的 `"failure"` 是设计阶段臆测值） |
> | 响应类名 | `MeasureResponse` / `ClearResponse` | 统一为 **`ActionOutcome[T]`** |
> | 审计字段 | 未涉及 | `request_payload` / `response_payload` / `response_received`（P0-12/P0-15 修正产物） |
>
> 本文档中 `ActionOutcome` / `response_received` / `request_payload` 出现次数为 **0** ⇒ **全部 P0 修正（含 P0-16/P0-17）都没进这份文档**。
> ⇒ **以 `src/` 代码为准**；本文档只作设计意图留痕。

## 设计原则

1. **接口与实现分离**：策略代码只依赖接口，不知道当前是在线还是离线
2. **严格协议对齐**：HTTP实现完全对接官方协议，离线实现严格复现规则
3. **从零重写**：不继承`q3_main.py`的缺陷，逐项验证后迁移
4. **结构化日志**：双时钟、完整request/response、可审计

---

## 一、统一接口定义

### 1.1 核心接口：SimulatorClient

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

class MeasureResult(Enum):
    """检测结果枚举"""
    NO_SIGNAL = "no_signal"
    DIRECTION = "direction"
    NEAR = "near"

class ClearResult(Enum):
    """清除结果枚举"""
    SUCCESS = "success"
    FAILURE = "failure"

@dataclass
class MeasureResponse:
    """检测响应（结构化）"""
    accepted: bool
    virtual_time_s: float
    result: MeasureResult
    svd_deg: Optional[float] = None  # 仅当result=DIRECTION时有效
    error: Optional[str] = None

@dataclass
class ClearResponse:
    """清除响应（结构化）"""
    accepted: bool
    virtual_time_s: float
    result: ClearResult
    error: Optional[str] = None

@dataclass
class EnterResponse:
    """进入响应（结构化）"""
    accepted: bool
    virtual_time_s: float
    max_virtual_duration_s: float
    max_real_duration_s: float
    remaining_real_duration_s: float
    error: Optional[str] = None

@dataclass
class ExitResponse:
    """退出响应（结构化）"""
    accepted: bool
    virtual_time_s: float
    total_sources: Optional[int] = None  # 总干扰源数（演练测试反馈）
    error: Optional[str] = None


class SimulatorClient(ABC):
    """
    模拟器客户端统一接口
    
    职责：
    - 定义统一的动作接口（enter/measure/clear/exit）
    - 管理双时钟（wall-clock / virtual-time）
    - 幂等重试（request_id）
    - 结构化日志
    
    实现类：
    - HttpSimulatorClient：对接HTTP协议
    - OfflineSimulatorClient：离线仿真
    """
    
    @abstractmethod
    def enter(self) -> EnterResponse:
        """
        进入测试区域
        
        Returns:
            EnterResponse: 包含时间限制和初始状态
        """
        pass
    
    @abstractmethod
    def measure(self, x: float, y: float, channel: int) -> MeasureResponse:
        """
        在指定位置检测指定频道
        
        Args:
            x, y: 位置坐标（米）
            channel: 频道编号（1-20）
            
        Returns:
            MeasureResponse: 包含检测结果和虚拟时间
            
        时间消耗：
            - 频道切换：1秒（如果与上次不同）
            - 检测：5秒
        """
        pass
    
    @abstractmethod
    def clear(self, x: float, y: float, channel: int) -> ClearResponse:
        """
        在指定位置清除指定频道的干扰源
        
        Args:
            x, y: 位置坐标（米）
            channel: 频道编号（1-20）
            
        Returns:
            ClearResponse: 包含清除结果和虚拟时间
            
        条件：
            - 距离干扰源 ≤ 20米
            - 在干扰源有效覆盖角度内（如果是定向源）
            
        时间消耗：
            - 光学定位：3秒
            - 清除：2秒
        """
        pass
    
    @abstractmethod
    def exit(self) -> ExitResponse:
        """
        退出测试区域
        
        Returns:
            ExitResponse: 包含总干扰源数（演练测试）
        """
        pass
    
    # 状态查询接口
    @abstractmethod
    def get_virtual_time(self) -> float:
        """获取当前虚拟时间（秒）"""
        pass
    
    @abstractmethod
    def get_remaining_real_time(self) -> float:
        """获取剩余现实时间（秒）"""
        pass
    
    @abstractmethod
    def get_last_channel(self) -> Optional[int]:
        """获取上次检测的频道（用于计算切换成本）"""
        pass
```

---

## 二、HTTP实现规范

### 2.1 HttpSimulatorClient

```python
class HttpSimulatorClient(SimulatorClient):
    """
    HTTP协议实现
    
    严格对接官方协议：
    - 附件2的字段名和数据类型
    - 幂等重试机制（request_id）
    - 超时和错误处理
    """
    
    def __init__(self, 
                 robot_id: str,
                 arena_id: str = "default",
                 base_url: str = "http://127.0.0.1:2026",
                 timeout: float = 10.0,
                 max_retries: int = 3):
        """
        Args:
            robot_id: 参赛队号（提交时替换为占位符）
            arena_id: 竞技场ID
            base_url: 模拟器URL
            timeout: 请求超时（秒）
            max_retries: 最大重试次数
        """
        self.robot_id = robot_id
        self.arena_id = arena_id
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        # 状态
        self._session = requests.Session()
        self._request_counter = 0
        self._virtual_time = 0.0
        self._remaining_real_time = 0.0
        self._last_channel: Optional[int] = None
        self._wall_start_time: Optional[float] = None
        
        # 日志
        self._logger = self._setup_logger()
    
    def _new_request_id(self) -> str:
        """生成新的请求ID（幂等重试用）"""
        self._request_counter += 1
        return f"req_{self._request_counter}_{uuid.uuid4().hex[:8]}"
    
    def _send_request(self, endpoint: str, payload: Dict[str, Any], 
                     request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        发送HTTP请求，带重试和错误处理
        
        Args:
            endpoint: API端点（/enter, /measure, /clear, /exit）
            payload: 请求体
            request_id: 请求ID（幂等重试）
            
        Returns:
            响应JSON
            
        异常：
            - requests.Timeout: 超时
            - requests.RequestException: 网络错误
            - RuntimeError: 服务器拒绝
        """
        if request_id is None:
            request_id = self._new_request_id()
        
        payload.update({
            "arena_id": self.arena_id,
            "robot_id": self.robot_id,
            "request_id": request_id
        })
        
        for attempt in range(self.max_retries):
            try:
                wall_time_before = time.time()
                
                response = self._session.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    timeout=self.timeout
                )
                
                wall_time_after = time.time()
                wall_elapsed = wall_time_after - wall_time_before
                
                # 解析响应
                data = response.json()
                
                # 记录日志
                self._log_request(endpoint, payload, data, wall_elapsed)
                
                # 检查accepted
                if not data.get("accepted", False):
                    error_msg = data.get("error", "未知错误")
                    raise RuntimeError(f"请求被拒绝: {error_msg}")
                
                # 更新状态
                if "virtual_time_s" in data:
                    self._virtual_time = data["virtual_time_s"]
                
                if "remaining_real_duration_s" in data:
                    self._remaining_real_time = data["remaining_real_duration_s"]
                
                return data
                
            except requests.Timeout:
                if attempt < self.max_retries - 1:
                    self._logger.warning(f"请求超时，重试 {attempt+1}/{self.max_retries}")
                    time.sleep(0.5)
                else:
                    raise
            
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    self._logger.warning(f"网络错误: {e}，重试 {attempt+1}/{self.max_retries}")
                    time.sleep(0.5)
                else:
                    raise
        
        raise RuntimeError("重试次数耗尽")
    
    def enter(self) -> EnterResponse:
        """实现接口：进入测试"""
        self._wall_start_time = time.time()
        
        data = self._send_request("/enter", {})
        
        return EnterResponse(
            accepted=data["accepted"],
            virtual_time_s=data["virtual_time_s"],
            max_virtual_duration_s=data["max_virtual_duration_s"],
            max_real_duration_s=data["max_real_duration_s"],
            remaining_real_duration_s=data["remaining_real_duration_s"]
        )
    
    def measure(self, x: float, y: float, channel: int) -> MeasureResponse:
        """实现接口：检测"""
        payload = {
            "position": {"x": x, "y": y},
            "channel": channel
        }
        
        data = self._send_request("/measure", payload)
        
        # 更新last_channel
        self._last_channel = channel
        
        # 解析measure_result字段
        result_str = data.get("measure_result")
        result = MeasureResult(result_str) if result_str else None
        
        svd_deg = data.get("svd_deg") if result == MeasureResult.DIRECTION else None
        
        return MeasureResponse(
            accepted=data["accepted"],
            virtual_time_s=data["virtual_time_s"],
            result=result,
            svd_deg=svd_deg
        )
    
    def clear(self, x: float, y: float, channel: int) -> ClearResponse:
        """实现接口：清除"""
        payload = {
            "position": {"x": x, "y": y},
            "channel": channel
        }
        
        data = self._send_request("/clear", payload)
        
        # 解析clear_result字段
        result_str = data.get("clear_result")
        result = ClearResult(result_str) if result_str else None
        
        return ClearResponse(
            accepted=data["accepted"],
            virtual_time_s=data["virtual_time_s"],
            result=result
        )
    
    def exit(self) -> ExitResponse:
        """实现接口：退出测试"""
        data = self._send_request("/exit", {})
        
        # 演练测试会返回total_sources
        total_sources = data.get("total_sources")
        
        return ExitResponse(
            accepted=data["accepted"],
            virtual_time_s=data["virtual_time_s"],
            total_sources=total_sources
        )
    
    def get_virtual_time(self) -> float:
        return self._virtual_time
    
    def get_remaining_real_time(self) -> float:
        return self._remaining_real_time
    
    def get_last_channel(self) -> Optional[int]:
        return self._last_channel
```

---

## 三、离线实现规范

### 3.1 OfflineSimulatorClient

```python
@dataclass
class InterferenceSource:
    """干扰源定义"""
    channel: int
    x: float
    y: float
    radius: float  # 有效接收半径
    is_directional: bool = False
    direction_deg: Optional[float] = None  # 定向角度
    beam_width_deg: Optional[float] = None  # 波束宽度

class OfflineSimulatorClient(SimulatorClient):
    """
    离线仿真实现
    
    严格复现：
    - near判定（距离≤5m）
    - clear判定（距离≤20m + 角度条件）
    - 频道切换时间（1秒）
    - 虚拟时间累加
    - 示向度误差（±1°）
    """
    
    def __init__(self, 
                 sources: List[InterferenceSource],
                 robot_id: str = "OFFLINE_TEST",
                 svd_error_deg: float = 1.0,
                 max_virtual_duration_s: float = 360000,
                 max_real_duration_s: float = 1200):
        """
        Args:
            sources: 干扰源列表（用于测试）
            robot_id: 机器人ID
            svd_error_deg: 示向度误差（度）
            max_virtual_duration_s: 最大虚拟时间
            max_real_duration_s: 最大现实时间
        """
        self.sources = sources
        self.robot_id = robot_id
        self.svd_error_deg = svd_error_deg
        self.max_virtual_duration_s = max_virtual_duration_s
        self.max_real_duration_s = max_real_duration_s
        
        # 状态
        self._virtual_time = 0.0
        self._wall_start_time: Optional[float] = None
        self._last_channel: Optional[int] = None
        self._cleared_sources: Set[int] = set()  # 已清除的源索引
        self._entered = False
        
        # 日志
        self._logger = self._setup_logger()
    
    def enter(self) -> EnterResponse:
        """实现接口：进入测试"""
        self._entered = True
        self._wall_start_time = time.time()
        self._virtual_time = 0.0
        
        return EnterResponse(
            accepted=True,
            virtual_time_s=0.0,
            max_virtual_duration_s=self.max_virtual_duration_s,
            max_real_duration_s=self.max_real_duration_s,
            remaining_real_duration_s=self.max_real_duration_s
        )
    
    def measure(self, x: float, y: float, channel: int) -> MeasureResponse:
        """实现接口：检测"""
        if not self._entered:
            raise RuntimeError("必须先调用enter()")
        
        # 计算虚拟时间增量
        time_cost = 5.0  # 检测时间
        if self._last_channel is not None and self._last_channel != channel:
            time_cost += 1.0  # 频道切换
        
        self._virtual_time += time_cost
        self._last_channel = channel
        
        # 查找对应频道的干扰源
        source = self._find_source(channel)
        
        if source is None or source in self._cleared_sources:
            # 无信号
            return MeasureResponse(
                accepted=True,
                virtual_time_s=self._virtual_time,
                result=MeasureResult.NO_SIGNAL
            )
        
        # 计算距离
        dist = np.sqrt((x - source.x)**2 + (y - source.y)**2)
        
        # 超出有效接收半径
        if dist > source.radius:
            return MeasureResponse(
                accepted=True,
                virtual_time_s=self._virtual_time,
                result=MeasureResult.NO_SIGNAL
            )
        
        # near判定
        if dist <= 5.0:
            return MeasureResponse(
                accepted=True,
                virtual_time_s=self._virtual_time,
                result=MeasureResult.NEAR
            )
        
        # direction判定
        # 计算示向度（从当前位置指向源的角度）
        angle = np.degrees(np.arctan2(source.y - y, source.x - x))
        if angle < 0:
            angle += 360
        
        # 添加±1度误差
        noise = np.random.uniform(-self.svd_error_deg, self.svd_error_deg)
        svd_deg = angle + noise
        
        return MeasureResponse(
            accepted=True,
            virtual_time_s=self._virtual_time,
            result=MeasureResult.DIRECTION,
            svd_deg=svd_deg
        )
    
    def clear(self, x: float, y: float, channel: int) -> ClearResponse:
        """实现接口：清除"""
        if not self._entered:
            raise RuntimeError("必须先调用enter()")
        
        # 虚拟时间：光学定位3秒 + 清除2秒
        self._virtual_time += 5.0
        
        # 查找对应频道的干扰源
        source_idx = self._find_source_idx(channel)
        
        if source_idx is None or source_idx in self._cleared_sources:
            return ClearResponse(
                accepted=True,
                virtual_time_s=self._virtual_time,
                result=ClearResult.FAILURE
            )
        
        source = self.sources[source_idx]
        
        # 距离判定
        dist = np.sqrt((x - source.x)**2 + (y - source.y)**2)
        
        if dist > 20.0:
            return ClearResponse(
                accepted=True,
                virtual_time_s=self._virtual_time,
                result=ClearResult.FAILURE
            )
        
        # 定向源的角度判定
        if source.is_directional:
            angle_to_robot = np.degrees(np.arctan2(y - source.y, x - source.x))
            if angle_to_robot < 0:
                angle_to_robot += 360
            
            angle_diff = abs(angle_to_robot - source.direction_deg)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            
            if angle_diff > source.beam_width_deg / 2:
                return ClearResponse(
                    accepted=True,
                    virtual_time_s=self._virtual_time,
                    result=ClearResult.FAILURE
                )
        
        # 清除成功
        self._cleared_sources.add(source_idx)
        
        return ClearResponse(
            accepted=True,
            virtual_time_s=self._virtual_time,
            result=ClearResult.SUCCESS
        )
    
    def exit(self) -> ExitResponse:
        """实现接口：退出测试"""
        if not self._entered:
            raise RuntimeError("必须先调用enter()")
        
        return ExitResponse(
            accepted=True,
            virtual_time_s=self._virtual_time,
            total_sources=len(self.sources)  # 离线测试直接返回
        )
    
    def _find_source(self, channel: int) -> Optional[InterferenceSource]:
        """查找指定频道的干扰源"""
        for source in self.sources:
            if source.channel == channel:
                return source
        return None
    
    def _find_source_idx(self, channel: int) -> Optional[int]:
        """查找指定频道的干扰源索引"""
        for idx, source in enumerate(self.sources):
            if source.channel == channel:
                return idx
        return None
```

---

## 四、结构化日志规范

### 4.1 日志格式

```python
@dataclass
class RequestLog:
    """请求日志（结构化）"""
    request_id: str
    wall_timestamp: float  # 墙钟时间戳
    virtual_time_s: float  # 虚拟时间
    endpoint: str
    request_data: Dict[str, Any]
    response_data: Dict[str, Any]
    wall_elapsed_s: float  # 墙钟耗时
    error: Optional[str] = None

class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, log_dir: str, robot_id: str):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.json_path = self.log_dir / f"test_{timestamp}.json"
        self.txt_path = self.log_dir / f"test_{timestamp}.txt"
        
        self.logs: List[RequestLog] = []
        self.robot_id = robot_id
        self.start_time = time.time()
    
    def log_request(self, log: RequestLog):
        """记录一次请求"""
        self.logs.append(log)
        
        # 写入JSON
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "robot_id": self.robot_id,
                "start_time": self.start_time,
                "logs": [asdict(log) for log in self.logs]
            }, f, indent=2, ensure_ascii=False)
        
        # 写入文本（人类可读）
        with open(self.txt_path, 'a', encoding='utf-8') as f:
            f.write(f"[{log.request_id}] {log.endpoint}\n")
            f.write(f"  虚拟时间: {log.virtual_time_s:.1f}s\n")
            f.write(f"  墙钟耗时: {log.wall_elapsed_s:.3f}s\n")
            f.write(f"  请求: {json.dumps(log.request_data, ensure_ascii=False)}\n")
            f.write(f"  响应: {json.dumps(log.response_data, ensure_ascii=False)}\n")
            f.write("-" * 70 + "\n")
```

---

## 五、使用示例

### 5.1 在线测试

```python
# 创建HTTP客户端
client = HttpSimulatorClient(
    robot_id="YOUR_ROBOT_ID",  # 原为真实队号，2026-09-12 按赛题要求脱敏
    base_url="http://127.0.0.1:2026"
)

# 进入测试
enter_resp = client.enter()
print(f"进入成功，虚拟时间上限: {enter_resp.max_virtual_duration_s}s")

# 检测
measure_resp = client.measure(x=0, y=0, channel=1)
if measure_resp.result == MeasureResult.DIRECTION:
    print(f"发现信号，示向度: {measure_resp.svd_deg}°")

# 清除
clear_resp = client.clear(x=100, y=200, channel=1)
if clear_resp.result == ClearResult.SUCCESS:
    print("清除成功")

# 退出
exit_resp = client.exit()
print(f"总干扰源数: {exit_resp.total_sources}")
```

### 5.2 离线测试

```python
# 定义测试场景
sources = [
    InterferenceSource(channel=1, x=500, y=800, radius=1200),
    InterferenceSource(channel=3, x=-600, y=400, radius=1100),
]

# 创建离线客户端
client = OfflineSimulatorClient(sources=sources)

# 相同的使用方式
enter_resp = client.enter()
measure_resp = client.measure(x=0, y=0, channel=1)
# ...
```

### 5.3 策略代码（与实现无关）

```python
def discover_sources(client: SimulatorClient) -> List[int]:
    """发现所有干扰源（不知道client是在线还是离线）"""
    found_channels = []
    
    grid = generate_grid(d=1500)
    
    for point in grid:
        for channel in range(1, 21):
            resp = client.measure(point.x, point.y, channel)
            
            if resp.result == MeasureResult.DIRECTION:
                found_channels.append(channel)
    
    return list(set(found_channels))
```

---

## 六、实施计划

### Phase 1: 接口定义（当前文档）
- [x] 设计统一接口
- [x] 定义响应数据结构
- [x] 规范日志格式

### Phase 2: HTTP实现
- [ ] 实现HttpSimulatorClient
- [ ] 单元测试（模拟服务器）
- [ ] 集成测试（真实模拟器）

### Phase 3: 离线实现
- [ ] 实现OfflineSimulatorClient
- [ ] 单元测试（已知场景）
- [ ] 对比在线/离线一致性

### Phase 4: 迁移策略代码
- [ ] 提取q3_main.py中已验证的部分
- [ ] 重构为依赖统一接口
- [ ] 验证功能完整性

---

**文档版本**: v1.0  
**创建时间**: 2026-09-12  
**待审核**: 请确认设计方案后进入Phase 2实施
