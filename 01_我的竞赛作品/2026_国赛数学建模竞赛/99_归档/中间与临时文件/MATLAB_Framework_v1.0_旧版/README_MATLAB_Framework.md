% ========================================================================
% MATLAB 框架使用说明文档
% ========================================================================
% 文件: README_MATLAB_Framework.md
% 日期: 2026-09-11
% ========================================================================

# CUMCM2026 B题 Q3/Q4 MATLAB 框架使用说明

> ## ⚠️ 2026-09-12 变更（**跑测试前先看这段**）
>
> 本目录已从「第二套实现」升级为 **Q3/Q4 主线 + 可交的机器狗程序**（E1 裁定）。变更要点：
>
> | 文件 | 变化 |
> |---|---|
> | **`Q3正式测试操作手册.md`** | 🆕 **实测前必读**：交付物清单 / 时间窗 / 操作顺序 / 7 条红线 / 已知缺口 |
> | **`一键_跑Q3.bat`** | 🆕 一键入口（**纯 ASCII**，提示输入队号，自动找 R2026a/R2022b） |
> | `main_Q3Q4.m` | **`robot_id` 改运行期参数**（附件2 §5.1，源码不再写死队号）；新增**表 1 四列**打印；修收尾"只 break 不清除"、除零 `NaN`、`load_config` 死分支 |
> | `SimulatorClient.m` | **新增 JSONL 自记录日志**（附件1 §4.6 / 附件2 §12 明文要求，旧版**零落盘**）；**双检查**（HTTP 状态 + `accepted`）；**重试口径合规**（只有传输层失败才复用原 ID 重试；`accepted=false` / 4xx **不重试**）。修 2 个真缺陷 |
> | `test_SimulatorClient_logging.m` | 🆕 离线 5 模式自测（配 `核验脚本/_mock_simulator.py`，免 pytest / 免联网） |
>
> **用法**：双击 `一键_跑Q3.bat` → 输队号 → 到模拟器点开始 → 程序自动 `/enter` → 跑完打印表 1 四列。
> **自检**：双击 `核验脚本\一键_跑MATLAB离线自测.bat`（不占正式测试次数）。
> **正文以下内容为 2026-09-11 原稿**，其中"双套实现"等表述已由 E1 裁定取代 —— 以本横幅与操作手册为准。

## 📁 文件结构

```
MATLAB_Framework/                    ← 运行目录：所有 .m 必须在本层（MATLAB 路径 + 一键 bat 依赖）
├── 🔴 main_Q3Q4.m                 主控（阶段 A/B 融合 + 任务表调度 + 三路清除派发）
├── 🔴 SimulatorClient.m           HTTP 客户端类（含 JSONL 自记录日志）
├── 🔴 clear_source.m              三路清除：direct / sweep / homing
├── 🔴 optimize_route.m            路径优化（NN + 2-opt）
├── 🔴 Q1_geometry.m               Q1 几何（polyshape 求交 / Welzl 最小包围圆 / 旋转卡壳）
├──    ChannelStateMachine.m       频道状态管理
├──    generate_triangular_grid.m  三角网格生成（d 为运行期参数）
├──    check_coverage.m            覆盖自检
├──    triangulate_source.m        交会定位
├──    design_constants.m          权威常数
├──    sweep_clear_exact.m         精确扫掠（辅）
├──    Q4_extensions.m             Q4 扩展（未端到端验证）
├──    run_assertions.m            断言总入口（Q3 8/8 + Q4 8/8）
├──    test_*.m                    9 个回归测试（见下）
├──    crossval_q1_geom.m          Q1 几何跨实现交叉验证
├──    一键_跑Q3.bat               🆕 一键入口（纯 ASCII）
├──    Q3正式测试操作手册.md        ⚠️ 实测前必读
├──    README_MATLAB_Framework.md  本文档
├──    logs/                       🚫 gitignore —— 含真实队号，不入包
└──    文档_历史/                   2026-09-11 前旧稿（内容已过时）
```

**回归测试清单**（`核验脚本/一键_跑MATLAB离线自测.bat` 跑其中 11 项）：
`test_SimulatorClient_logging`（5 模式合规）｜`test_clear_source_homing`｜
`test_homing_convergence`｜`test_sweep_clear`｜`test_phaseC_homing`｜`test_optimize_route`｜
`test_Q1_geometry`｜`test_Q4_extensions`｜`run_assertions`

## 🚀 快速开始

### 1. 环境要求

- MATLAB R2020a 或更高版本
- 需要的工具箱：
  - Statistics and Machine Learning Toolbox（可选，用于高级优化）
  - Optimization Toolbox（可选）

### 2. 启动模拟器

1. 从百度网盘下载模拟器：
   `https://pan.baidu.com/s/1P1yfVjY0RufU93XOdzhOLw?pwd=2026`

2. 启动模拟器，确保监听 `http://127.0.0.1:2026`

### 3. 运行测试

```matlab
% 在 MATLAB 中切换到框架目录
cd 'E:\CUMCM2026\HelloMathModeling\03_编程手\MATLAB_Framework'

% 运行 Q3
results = main_Q3Q4('Q3');

% 运行 Q4
results = main_Q3Q4('Q4');
```

## 📊 核心模块说明

### SimulatorClient（HTTP客户端）

**功能**：
- 封装 /enter, /measure, /clear, /exit 四条指令
- 自动处理幂等重试
- 跟踪虚拟时间和现实时间

**方法**：
```matlab
client = SimulatorClient('http://127.0.0.1:2026', 'TEAM_001');

% 进入测试
resp = client.enter();

% 检测
resp = client.measure(x, y, channel);

% 清除
resp = client.clear(x, y, channel);

% 退出
resp = client.exit();
```

### ChannelStateMachine（状态管理）

**功能**：
- 管理 20 个频道的状态
- 跟踪发现/定位/清除/确认空
- 实现完备性判定（定理 C）

**方法**：
```matlab
state = ChannelStateMachine(20, 8);

% 更新状态
state.update(channel, position_id, 'direction', result_data);

% 标记已清除
state.mark_cleared(channel);

% 检查完备性
[complete, stats] = state.check_completeness();
```

### 三角网格生成

**公式**: Q3-F10

```matlab
params = struct('d', 1500, 'R_domain', 1800, 'extend_for_Q4', false);
P = generate_triangular_grid(params);
```

**输出**：
- d=1500 → 7~9 点
- d=1000 → 10~12 点

### 三路清除策略

**公式**: Q3-F61

```matlab
[success, cost, mode] = clear_source(source, sim_client, config);
```

**策略**：
- R_MEC ≤ 20m → 直接清除
- 20 < R_MEC ≤ 84.0369m → 扫掠清除
- R_MEC > 84.0369m → Homing逼近

## ✅ 原「待完善模块」—— **三条均已实现**（2026-09-12 更新）

> ⚠️ 本节原为 2026-09-11 的 TODO 清单，**现已全部完成**，保留条目仅为追溯。
> 若看到别处仍写「占位函数 / 简化版 / 贪心」，那是未更新的旧稿。

### 1. Q1 几何管线 —— ✅ 已精确实现

- `Q1_geometry.intersect_wedges()`：**polyshape 布尔求交**（非占位）
- `Q1_geometry.minimum_enclosing_circle()`：**Welzl 算法**
- `Q1_geometry.polygon_diameter()`：旋转卡壳
- **证据**：跨实现交叉验证 `crossval_q1_geom.m` 对 79 个案例与 Python 侧
  （`q1_main.py` 半平面交）比对，**截断后分歧 0**，最差相对偏差 3.5e-11
  （报告：`03_编程手/核验脚本/_crossval_report.txt`）

### 2. 扫掠清除 —— ✅ 已重写为「定向短走」

- 旧版：按包围盒铺 20 m 格点逐个试 ⇒ 实测**试 19 次才命中**（白走 ~1000 m + 57 s）
- 现版：c\* 处测一次拿示向度 → 沿方位走一个清除半径再清 → 重复。**有保证命中**
  （1° 误差在 R ≤ 84 m 处横偏 ≤ 1.5 m）
- **证据**：`test_sweep_clear.m`（`/clear=2, /measure=1, 行程 20 m`）

### 3. 路径优化 —— ✅ 已启用 2-opt

- `optimize_route.m` 的 2-opt **已启用**（原版写好了但被注释掉，且目标函数漏算起点→首点）
- **效果**：13 格点巡回 15464 m → ≤12100 m；12 源按发现顺序 13160 m → 8789 m
- **证据**：`test_optimize_route.m`

## 📐 关键数值速查

| 参数 | 数值 | 公式 |
|------|------|------|
| 圆域半径 | 1800 m | 题设 |
| 最坏接收半径 | **1000 m** | 设计输入 |
| 清除半径 | **20 m** | 题设 |
| 网格间距（Q3） | 1500 m | 配置 |
| 网格间距（Q4） | 1000 m | 配置 |
| Homing 收缩率 | **0.0174531** | Q3-F40 |
| 扫掠/homing 拐点 | **84.0369 m** | Q3-F60 |
| 移动时间下界 | **703.72 s** | Q3-F48 |

## 🔧 配置参数修改

编辑 `main_Q3Q4.m` 中的 `load_config()` 函数：

```matlab
function config = load_config(problem_type)
    % 修改队号
    config.robot_id = 'YOUR_TEAM_ID';  % ← 改这里
    
    % 修改网格间距
    config.grid_spacing = 1500;  % Q3 推荐 1500
    
    % 修改时间预留
    config.time_reserve = 60;  % 收尾预留时间 [s]
end
```

## 🧪 测试验收线

### 验收线 ① 覆盖与判据

- [ ] M2：网格点数（d=1500: 7-9, d=1000: 10-12）
- [ ] M3：覆盖自检（最大距离 ≤ 1000m）
- [ ] M5：Q1 判据回归（需 Q1 精确实现）

### 验收线 ② 收敛与完备

- [ ] M8：Homing 收缩率（λ=0.0174531）
- [ ] M16：极端次序 100% 清除

## 📝 输出结果

运行完成后，`results` 结构体包含：

```matlab
results.cleared_count      % 已清除个数
results.total_count        % 总源数
results.cleared_ratio      % 清除比例（目标 100%）
results.virtual_time       % 虚拟时间 [s]
results.avg_time           % 平均定位清除时间 [s]
```

## 🐛 调试技巧

### 1. 开启详细日志

在主脚本中添加：
```matlab
config.verbose = true;
```

### 2. 单步测试

```matlab
% 只测试网格生成
params = struct('d', 1500, 'R_domain', 1800, 'extend_for_Q4', false);
P = generate_triangular_grid(params);

% 只测试覆盖
coverage_ok = check_coverage(P, config);
```

### 3. 模拟器连接测试

```matlab
client = SimulatorClient('http://127.0.0.1:2026', 'TEST');
try
    resp = client.enter();
    fprintf('连接成功！\n');
    client.exit();
catch ME
    fprintf('连接失败: %s\n', ME.message);
end
```

## 📚 相关文档

- **建模文档**: `02_建模手/Q3/Q3全解总览.md`
- **公式表**: `02_建模手/Q3/Q3公式表.md`
- **权威数字**: `00_任务总控/权威数字表.md`
- **Python 参考**: `03_编程手/Q3/实验结果/q3_main.py`

## 🔄 从 Python 迁移的变化

| Python | MATLAB | 说明 |
|--------|--------|------|
| `requests.post()` | `webwrite()` | HTTP 请求 |
| `class` | `classdef ... handle` | 类定义 |
| `dict` | `struct` | 数据结构 |
| `numpy.array` | 矩阵 | 数值计算 |
| `list.append()` | `[arr; new_row]` | 数组追加 |

## ⚡ 性能优化建议

1. **向量化**: MATLAB 的循环较慢，尽量用矩阵运算
2. **预分配**: `zeros(n, 2)` 而非动态增长
3. **避免重复计算**: 缓存距离矩阵

## 📞 问题反馈

发现问题请记录在：
`03_编程手/Q3/理论问题反馈.md`

---

**最后更新**: 2026-09-13
**框架版本**: v1.1.0（Q3 主线，已实跑验证）
**状态**: ✅ 已跑通 —— 13 局真实演练 100% 清除、均摊 369.6 s/源；离线 11 项自测全过
**现行操作文档**: `Q3正式测试操作手册.md`（**实测前必读**）
**历史文档**（2026-09-11 前，内容已过时）: `文档_历史/`
