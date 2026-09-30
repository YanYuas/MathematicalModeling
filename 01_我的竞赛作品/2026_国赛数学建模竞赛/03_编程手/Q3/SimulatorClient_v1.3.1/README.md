# Q3 SimulatorClient 发布版

> ## ⚠️ 本机核验注记（总控，2026-09-12；**原文未删，改动处逐条标出**）
>
> 本包 2026-09-12 由编程手经 QQ 推送，2026-09-12 归入 `03_编程手/Q3/SimulatorClient_v1.3.1/`。
> 核验结论详见 **`核验报告_总控_2026-09-12.md`**。三条要点：
>
> 1. 🔴 **原文的「状态：已通过实时模拟器验证」缺产物支撑** —— 本包**无 `logs/`**（原文自己要求
>    "提交前删除 logs/ 内容"，删后即无证据），且外部旁证不支持（模拟器统计队列 0 行、无 `:2026` 监听）。
>    ⇒ 该声明**降级为「编程手自报」（未复核）**。
> 2. 🔴 **本包 36 项测试实测 13 通过 / 23 失败** —— 原文「P0-17 修正验证：36项单元测试全部实现」
>    **不等于验证通过**：失败 4 类根因**全在测试侧**（测试按**旧签名**构造，如传 `position_error_m=`
>    而 `src/` 现为 `svd_error_deg=`；调 `clear(0,0)` 而接口是 `clear(x,y,channel)`）。
>    编程手从未跑过这批测试（其说明自述本机 pytest 环境损坏）⇒ **静态声称，非验证结论**。
>    详见 `核验报告_总控_2026-09-12.md` **§七**。
> 2. 🔴 **已修 1 处会导致脚本跑不起来的缺陷** —— `test_simulator.py` 的 `sys.path` 原来指向
>    **队友本机目录** `01_修改区_WorkInProgress/去AI化代码库/Q3/src`，本包 `src/` 在根目录 ⇒
>    原文教的 `python test_simulator.py --robot-id ...` **必然 `ModuleNotFoundError`**。已改为 `Path(__file__).parent / "src"`。
> 3. 🔴 **合规**：原文 `README` 与 `SimulatorClient统一接口设计.md` 共 **4 处出现真实队号**（代码侧干净）。
>    赛题要求支撑材料中隐去队号 ⇒ 已就地替换为 `YOUR_ROBOT_ID`。
>
> ⚠️ **定位提醒**：按 **E1 裁定（Q3/Q4 以 MATLAB 为主）**，本包属 **Python 对照/留痕**，**不是主线**。

## 重要提醒

**根据赛题要求，代码中不得硬编码参赛队号！**

所有测试脚本和示例代码均使用命令行参数传入队号：

```bash
python test_simulator.py --robot-id YOUR_ROBOT_ID
```

## 目录结构

```
Q3_SimulatorClient_v1.3.1/          ← 实际目录名（原文写 "Q3/"，已按实况更正）
├── src/                            # 核心代码
│   ├── simulator_client.py         # 统一接口定义（145 行）
│   ├── http_simulator_client.py    # HTTP协议实现（492 行）
│   └── offline_simulator_client.py # 离线模式实现（475 行）
├── tests/test_simulator_client.py  # 单元测试（879 行 / 36 个 test）
├── test_simulator.py               # 端到端脚本（130 行）
├── SimulatorClient统一接口设计.md    # ⚠️ **v1.0，早于全部 P0 修正**（见该文件顶部注记）
├── P0-16_P0-17_修正说明.md
└── 快速开始.txt
```

> ⚠️ **原文此处的目录树列了 `examples/` 与 `logs/`，两者在包里都不存在**（已按实况更正）：
> `examples/` 从未交付；`logs/` 由客户端**运行时自动创建**（`log_dir` 默认 `./logs`，即**相对当前工作目录**）。

## 核心功能

### 1. HttpSimulatorClient - HTTP协议实现

**已修正17项P0问题，通过36项核心测试**

```python
from src.http_simulator_client import HttpSimulatorClient

# 使用命令行参数传入队号
client = HttpSimulatorClient(
    robot_id="YOUR_ROBOT_ID",  # 从命令行参数获取
    arena_id="default",
    base_url="http://127.0.0.1:2026"
)

# 进入场地
enter_response = client.enter()
if not enter_response.accepted:
    print(f"进入失败: {enter_response.error}")
    exit(1)

# 测量
outcome = client.measure(x=0, y=0, channel=1)
if outcome.accepted:
    print(f"测量结果: {outcome.result.measure_result}")
    if outcome.result.svd_deg is not None:
        print(f"信号强度: {outcome.result.svd_deg} dB")

# 清除
outcome = client.clear(x=100, y=100, channel=1)
if outcome.accepted:
    print(f"清除结果: {outcome.result.clear_result}")

# 退出
outcome = client.exit()
```

### 2. 自动日志记录

**满足赛题要求："机器狗程序应自行记录测试过程中的指令序列、响应信息等内容"**

所有HTTP请求和响应自动记录到 `logs/` 目录：

- 文件格式: `test_YYYYMMDD_HHMMSS.jsonl`
- 每行一个JSON对象，包含完整的请求和响应信息
- 记录内容：
  - `timestamp`: 墙钟时间戳
  - `request_id`: 请求唯一标识
  - `request_payload`: 完整请求体
  - `response_payload`: 完整响应体
  - `http_status`: HTTP状态码
  - `response_received`: 是否收到HTTP响应
  - `accepted`: 模拟器是否接受操作
  - `virtual_time_s`: 虚拟时间
  - `transport_error`: 传输错误（如有）
  - `protocol_error`: 协议错误（如有）

### 3. 命令行使用示例

项目根目录提供了完整的测试脚本 `test_simulator.py`：

```bash
# 基本用法
python test_simulator.py --robot-id YOUR_ROBOT_ID

# 指定模拟器地址
python test_simulator.py --robot-id YOUR_ROBOT_ID --base-url http://localhost:2026

# 指定场地
python test_simulator.py --robot-id YOUR_ROBOT_ID --arena-id arena1

# 查看帮助
python test_simulator.py --help
```

> 📌 原文这三条示例写的是**真实队号**，已按赛题要求替换为占位符。

## 测试验证

### 编程手自报（2026-09-12，**总控未复核——原文的全部结论如下，仅原样保留**）

> ⚠️ 以下 4 条**均为编程手自报**。总控核验发现：本包**无 `logs/` 留痕**，
> 且本机外部旁证不支持（见顶部核验注记第 1 条）⇒ **状态从「已验证」降级为「自报」**。

- enter() - 进入成功
- measure() - 测量成功 (no_signal/direction响应)
- clear() - 清除成功 (no_target_in_range响应)
- exit() - 退出成功 (exit_reason="user_exit")

P0-16（非200响应解析JSON错误）、P0-17（36项单元测试全部实现）为编程手自报的修正验证。

### ✅ 总控侧可复核的证据

| 项 | 状态 |
|---|---|
| **36 项测试的代码实现** | ✅ **实查成立**：`grep -c "def test"` = **36**，且**无 `pass` 占位**（旧版 16 项占位的问题确已修） |
| **36 项测试的离线执行** | 🔴 **总控已实跑：13 通过 / 23 失败**（`py -3.11`，免 pytest）——**「P0-17 修正验证通过」不成立**。4 类根因**全在测试侧**（测试按旧签名/旧参数名构造，与 `src/` 脱节），详见 `核验报告_总控_2026-09-12.md` **§七**；复跑：`../../核验脚本/一键_跑Python客户端测试.bat` |
| **实时模拟器验证** | ❌ **无证据**（`logs/` 缺失 + 统计队列 0 行 + 无 `:2026` 监听） |

### 单元测试

```bash
# 本机推荐（免 pytest、免联网）：见 ../../核验脚本/一键_跑Python客户端测试.bat

# 装了 pytest 的话：
pytest tests/test_simulator_client.py -v

# 运行特定测试（类名/方法名已按实况更正；原文写的是不存在的
# TestHttpSimulatorClient::test_http_1_successful_enter）
pytest tests/test_simulator_client.py::TestHTTPProtocol::test_http_1_direction_response_parsing -v
```

## 代码提交注意事项

**重要：根据赛题规定**

> "各参赛队在附录中、支撑材料中提交代码时，注意将参赛队号隐去或使用占位符代替，以免违规。建议不要将参赛队号在程序中写死，而是以命令行参数等方式提供。"

本代码库已完全符合此要求：

1. ✅ 所有测试脚本使用 `--robot-id` 命令行参数
2. ✅ 核心代码不包含任何硬编码队号
3. ✅ 示例代码使用 `YOUR_ROBOT_ID` 占位符
4. ✅ 日志文件包含队号，但可在提交前清理

> ⚠️ **补充（总控 2026-09-12）**：原文第 1–3 条**对代码成立**（实查 `src/`、`tests/`、`test_simulator.py` 无 10 位以上数字串），
> 但**文档侧原有 4 处真实队号**（本文件 3 处 + `SimulatorClient统一接口设计.md` 1 处）
> —— 文档也属支撑材料，**已就地替换为 `YOUR_ROBOT_ID`**。
> 这正是原文检查清单里"审查文档中的示例代码"那一条要抓的，**原检查清单未覆盖文档**。

**提交前检查清单**：
- [ ] 删除或清空 `logs/` 目录
- [ ] 检查示例代码中的队号占位符
- [ ] 确认测试脚本使用命令行参数
- [ ] 审查文档中的示例代码

## 技术规格

- Python版本: 3.10+
- 依赖: **`requests`（HTTP客户端）+ `numpy`（离线实现用）+ `pytest`（仅跑单元测试）**
  —— ⚠️ 原文只写了 `requests`，**少报 numpy 与 pytest**；本机实测 numpy 2.4.6 / requests 2.34.2 已有、**pytest 缺失**
- 协议: HTTP/JSON
- 超时: 10秒（可配置）
- 重试: 最多3次（可配置）
- 日志: JSONL格式，自动轮转
- ⚠️ `log_dir` 默认 `./logs`（**相对当前工作目录**，换目录运行会写到别处）—— 未改，见核验报告 §四.G

## 问题修正历史

### P0级问题（已全部修正）
- P0-10: 请求体包含request_id
- P0-11: ActionOutcome泛型支持
- P0-12: request_payload和result分离
- P0-14: exit强制校验exit_reason
- P0-15: executed改名response_received
- P0-16: **非200响应解析JSON错误**
- P0-17: **36项测试全部实现**

## 联系与支持

如有问题，请参考：
- `SimulatorClient统一接口设计.md` - 完整接口文档
- `P0-16_P0-17_修正说明.md` - 最新修正详情
- `tests/test_simulator_client.py` - 测试用例参考

---

**版本**: v1.3.1  
**最后更新**: 2026-09-12（编程手）  
**状态**: ⚠️ **原文写「已通过实时模拟器验证 ✅」——该声明缺产物支撑，总控 2026-09-12 已降级为「编程手自报，未复核」**（见顶部核验注记）；
代码侧 36 项测试已实查存在且无占位；**离线执行待跑**（一键脚本已备）。按 E1 裁定，本包定位 = **Q3 Python 对照/留痕**，**非主线**。
