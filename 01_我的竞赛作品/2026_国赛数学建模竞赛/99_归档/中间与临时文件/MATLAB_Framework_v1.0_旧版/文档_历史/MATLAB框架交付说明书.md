> ## ⚠️ 历史文档（2026-09-11 稿）—— **文中 TODO 已全部完成，勿据本文判断现状**
>
> 本文写作于「Q1 几何模块还是占位函数」的阶段。以下条目**均已实现并有实测证据**：
>
> | 文中所述 | 现状 | 证据 |
> |---|---|---|
> | `Q1_geometry.intersect_wedges()` 占位函数 | ✅ polyshape 布尔求交 | 跨实现交叉验证 79 案例，截断后分歧 0 |
> | `minimum_enclosing_circle()` 简化版（质心近似） | ✅ Welzl 算法 | 同上，最差相对偏差 3.5e-11 |
> | 扫掠清除「包围盒网格采样」简化版 | ✅ 重写为定向短走 | `test_sweep_clear.m`（`/clear=2, /measure=1, 行程 20 m`） |
> | 路径优化「贪心最近邻」 | ✅ 2-opt 已启用 | `test_optimize_route.m`（15464 → ≤12100 m） |
>
> **现行文档**（以此为准）：
> - `../README_MATLAB_Framework.md` —— 框架索引与文件地图
> - `../Q3正式测试操作手册.md` —— **实测前必读**
>
> 保留本文仅为追溯设计意图与早期验收线。

# MATLAB 框架交付说明书

> 交付方：编程手 | 接收方：建模手/团队 | 日期：2026-09-11 晚
> 框架类型：MATLAB | 状态：框架完成，待精化

---

## 一、交付内容清单

### 1.1 核心交付物

| 文件 | 行数 | 状态 | 说明 |
|------|------|------|------|
| `main_Q3Q4.m` | 200 | ✅ 完整 | 主控脚本，Q3/Q4 通用 |
| `SimulatorClient.m` | 140 | ✅ 完整 | HTTP 客户端类 |
| `ChannelStateMachine.m` | 90 | ✅ 完整 | 频道状态管理类 |
| `generate_triangular_grid.m` | 45 | ✅ 完整 | 三角网格生成 |
| `check_coverage.m` | 55 | ✅ 完整 | 覆盖自检 |
| `triangulate_source.m` | 25 | ⚠️ 占位 | 交会定位（需 Q1 算法） |
| `clear_source.m` | 165 | ✅ 完整 | 三路清除策略 |
| `Q1_geometry.m` | 110 | ⚠️ 简化 | Q1 几何模块（需精化） |
| `optimize_route.m` | 70 | ✅ 完整 | 路径优化（贪心） |
| `README_MATLAB_Framework.md` | - | ✅ 完整 | 使用说明文档 |

**总计**：10 个文件，~900 行代码

---

## 二、与 Python 框架的对比

| 特性 | Python 框架 | MATLAB 框架 | 优势 |
|------|-------------|-------------|------|
| HTTP 通信 | `requests` | `webwrite` | MATLAB 内置，无需第三方库 |
| 数值计算 | `numpy` | 原生矩阵 | MATLAB 更高效 |
| 类定义 | `class` | `classdef ... handle` | 语法略有不同 |
| 数据结构 | `dict` | `struct` | MATLAB 更适合数值型 |
| 调试 | 断点+print | 断点+工作区查看 | MATLAB 调试体验更好 |
| 可视化 | `matplotlib` | `plot` | MATLAB 内置，无需配置 |
| 竞赛适配 | ⚠️ 非主流 | ✅ **标准工具** | 评委更熟悉 MATLAB |

**核心优势**：
1. ✅ MATLAB 是数模竞赛的**标准工具**，评委更认可
2. ✅ 无需配置环境，内置所有数值计算功能
3. ✅ 可视化、调试、矩阵运算都更便捷
4. ✅ 论文中的代码截图更专业

---

## 三、框架设计理念（与 Python 一致）

### 3.1 三层结构

```
覆盖层（保证发现）
  ↓ generate_triangular_grid()
  ↓ check_coverage()
  
定位层（保证清除）
  ↓ triangulate_source()  (需 Q1 算法)
  ↓ Q1_geometry.m
  
清除层（保证效率）
  ↓ clear_source()
  ↓ direct_clear() / sweep_clear() / homing_clear()
```

### 3.2 三条红线（完全继承）

1. ❌ 接收半径必须按最坏 1000 m 设计
2. ❌ 覆盖自检必须含边界
3. ❌ 清除点是最小包围圆圆心，不是质心

### 3.3 两条验收线

- ① 覆盖与判据（M2/M3/M5）
- ② 收敛与完备（M8/M16）

---

## 四、已实现功能（✅ 可用）

### 4.1 模拟器通信（SimulatorClient）

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

% 时间跟踪
fprintf('虚拟时间: %.2f s\n', client.virtual_time);
fprintf('剩余时间: %.2f s\n', client.remaining_time);
```

**特性**：
- ✅ 自动幂等重试（最多 3 次）
- ✅ 虚拟时间和现实时间跟踪
- ✅ 输入参数校验
- ✅ 错误处理和友好提示

### 4.2 状态管理（ChannelStateMachine）

```matlab
state = ChannelStateMachine(20, 8);

% 更新状态
state.update(ch, pos_id, 'direction', result);
state.mark_cleared(ch);

% 完备性判定
[complete, stats] = state.check_completeness();
% stats.cleared, stats.confirmed_empty, stats.remaining
```

**状态机**：未发现 → 已定位 → 已清除 / 已确认空

### 4.3 网格生成与覆盖

```matlab
% Q3: d=1500, 无外扩
params = struct('d', 1500, 'R_domain', 1800, 'extend_for_Q4', false);
P = generate_triangular_grid(params);  % 7~9 点

% Q4: d=1000, 外扩环带
params.d = 1000;
params.extend_for_Q4 = true;
P = generate_triangular_grid(params);  % 10~12 点 + 环带

% 覆盖自检
coverage_ok = check_coverage(P, config);
```

**验证通过**：
- ✅ d=1500 → 8 点（理论 7-9）
- ✅ 覆盖最大距离 ≤ 1000 m
- ✅ 边界环带加密

### 4.4 三路清除策略

```matlab
% 根据 R_MEC 自动选择
[success, cost, mode] = clear_source(source, sim_client, config);
% mode: 'direct' / 'sweep' / 'homing'
```

**逻辑**：
- R_MEC ≤ 20 → 直接清除（5s）
- 20 < R_MEC ≤ 84.0369 → 扫掠（~10N s）
- R_MEC > 84.0369 → Homing（~213 s）

### 4.5 路径优化

```matlab
% 贪心最近邻
route = optimize_route(detection_points, [0; 0]);
```

---

## 五、待完善模块（⚠️ 需协助）

### 5.1 Q1 几何模块精确实现（🔴 优先）

**当前状态**：
- `Q1_geometry.intersect_wedges()`: 占位函数（返回空）
- `Q1_geometry.minimum_enclosing_circle()`: 简化版（质心近似）

**影响**：
- `triangulate_source()` 无法正常工作
- 验收线 ① 的 M5 无法测试
- Q3/Q4 定位精度受影响

**需要实现**：
1. **半平面交算法**：求多个角域的交集（凸多边形）
   - 输入：角域列表（每个角域 = 两条半平面）
   - 输出：凸多边形顶点列表 L

2. **Welzl 算法**：最小包围圆
   - 输入：点集 L
   - 输出：(c*, R_MEC)

3. **可选优化**：旋转卡壳（直径）

**参考资料**：
- Python 版：`03_编程手/Q1/实验结果/q1_main.py`
- 算法说明：`02_建模手/Q1/Q1建模数学化.md`
- MATLAB 示例：可搜索 "MATLAB convex hull" / "MATLAB smallest enclosing circle"

**建议行动**：
1. 从 Python 版翻译核心算法
2. 或使用 MATLAB 内置函数（`convhull`, `boundary` 等）
3. 验证 Q1 基准算例（R_MEC=19.799m）

---

### 5.2 扫掠清除精确实现

**当前状态**：简化版（包围盒网格采样）

**需要**：
- 用三角格精确覆盖定位区域 L
- 密度：1.2091996
- 计算 N_sweep = ceil(1.2091996 * (R_MEC/20)^2)

**优先级**：P1（模拟器到位后实测对比）

---

## 六、使用流程

### 6.1 环境准备

```matlab
% 1. 启动模拟器
% 2. 修改队号
edit main_Q3Q4.m
% 在 load_config() 中修改:
% config.robot_id = 'YOUR_TEAM_ID';
```

### 6.2 运行测试

```matlab
% 切换到框架目录
cd 'E:\CUMCM2026\HelloMathModeling\03_编程手\MATLAB_Framework'

% 运行 Q3
results = main_Q3Q4('Q3');

% 查看结果
fprintf('清除比例: %.1f%%\n', results.cleared_ratio * 100);
fprintf('虚拟时间: %.2f s\n', results.virtual_time);
```

### 6.3 调试技巧

```matlab
% 单步运行主脚本
dbstop in main_Q3Q4 at 50  % 在第 50 行设置断点
main_Q3Q4('Q3');

% 查看工作区变量
whos

% 测试单个模块
P = generate_triangular_grid(struct('d', 1500, 'R_domain', 1800, 'extend_for_Q4', false));
coverage_ok = check_coverage(P, config);
```

---

## 七、关键数值速查

| 参数 | MATLAB 变量 | 数值 | 公式 |
|------|-------------|------|------|
| 圆域半径 | `config.R_domain` | 1800 m | 题设 |
| 最坏接收半径 | `config.R_sensor` | **1000 m** | 设计 |
| 清除半径 | `config.R_clear` | **20 m** | 题设 |
| 网格间距（Q3） | `config.grid_spacing` | 1500 m | 配置 |
| Homing 收缩率 | `config.lambda_ideal` | 0.0174531 | Q3-F40 |
| 拐点 | `config.R_star` | 84.0369 m | Q3-F60 |
| 覆盖密度 | `config.coverage_density` | 1.2091996 | 常数 |

---

## 八、与建模手的接口

### 8.1 已验证数值

| 指标 | 理论值 | MATLAB 实测 | 状态 |
|------|--------|-------------|------|
| 覆盖点数（d=1500） | 7-9 | 8 | ✅ 吻合 |
| 覆盖点数（d=1000） | 10-12 | 11 | ✅ 吻合 |
| 覆盖最大距离 | ≤ 1000m | ~999.9m | ✅ 通过 |
| Q1 基准 R_MEC | 19.799m | - | ⏳ 需 Q1 算法 |

### 8.2 公式对照表

| 建模手公式 | MATLAB 实现 | 文件 |
|-----------|-------------|------|
| Q3-F10 三角格基矢 | `generate_triangular_grid.m` | ✅ |
| Q3-F11 覆盖自检 | `check_coverage.m` | ✅ |
| Q3-F18 清除判据 | `clear_source.m` | ✅ |
| Q3-F40 Homing 收缩 | `homing_clear()` | ✅ |
| Q3-F53 定理 C | `check_completeness()` | ✅ |
| Q3-F61 三路选择 | `clear_source.m` | ✅ |

---

## 九、MATLAB 特有优势

### 9.1 可视化支持

```matlab
% 绘制检测点网格
figure;
plot(P(:,1), P(:,2), 'bo', 'MarkerSize', 8);
hold on;
viscircles([0, 0], 1800, 'Color', 'r');
axis equal;
title('检测点网格');
```

### 9.2 实时监控

```matlab
% 在主循环中实时绘制
figure;
for i = 1:length(route)
    plot(current_pos(1), current_pos(2), 'rx', 'MarkerSize', 12);
    drawnow;
    pause(0.1);
end
```

### 9.3 数据导出

```matlab
% 导出结果到 Excel
T = struct2table(results);
writetable(T, 'Q3_results.xlsx');

% 保存工作区
save('Q3_workspace.mat');
```

---

## 十、FAQ

### Q1: MATLAB 版本要求？
**A**: R2020a 或更高。主要需要 `webwrite`/`webread` 函数（R2014b+）。

### Q2: 需要哪些工具箱？
**A**: 无强制要求。基础版本即可运行。可选：
- Statistics and Machine Learning Toolbox（高级优化）
- Optimization Toolbox（精确 TSP）

### Q3: 如何从 Python 版迁移数据？
**A**: 
```python
# Python
import scipy.io
scipy.io.savemat('data.mat', {'P': P, 'results': results})
```
```matlab
% MATLAB
load('data.mat');
```

### Q4: HTTP 连接超时怎么办？
**A**: 修改 `SimulatorClient` 构造函数：
```matlab
obj.timeout = 30;  % 改为 30 秒
```

### Q5: 如何查看 HTTP 请求详情？
**A**: 在 `send_request()` 中添加：
```matlab
disp(jsonencode(payload));  % 显示发送内容
disp(jsonencode(resp));     % 显示响应内容
```

---

## 十一、下一步行动

### 建模手待办（🔴 优先）

- [ ] 协助 Q1 几何模块精确实现
  - 提供半平面交算法的 MATLAB 参考
  - 或从 Python 版翻译核心逻辑
  - 验证 Q1 基准算例

- [ ] 审阅 MATLAB 代码
  - 检查三条红线是否遵守
  - 检查公式引用是否正确
  - 检查数值常量是否一致

### 编程手待办（⏳ 模拟器到位后）

- [ ] 完成 Q1 几何模块精确实现
- [ ] 完成 `triangulate_source.m` 精确实现
- [ ] 模拟器连接测试
- [ ] 双轨标定（d=1000 vs d=1500）
- [ ] 通过验收线 ①/②

### 统筹待办

- [ ] 下载模拟器（用户操作）
- [ ] 确认使用 MATLAB 框架（替代 Python）
- [ ] 准备论文中的 MATLAB 代码截图

---

## 十二、交付确认

### 编程手声明

✅ 我确认 MATLAB 框架已完成：
- [x] 主控脚本（Q3/Q4 通用）
- [x] HTTP 客户端（幂等重试）
- [x] 状态管理（完备性判定）
- [x] 网格生成（覆盖自检通过）
- [x] 三路清除策略
- [x] 使用说明文档

⚠️ 待完善项已列明：
- [ ] Q1 几何模块精确实现（需协助）
- [ ] 扫掠清除精确实现（P1）

### 建模手/团队确认（请填写）

```
收到 MATLAB 框架：
[ ] main_Q3Q4.m
[ ] SimulatorClient.m
[ ] ChannelStateMachine.m
[ ] generate_triangular_grid.m
[ ] check_coverage.m
[ ] triangulate_source.m
[ ] clear_source.m
[ ] Q1_geometry.m
[ ] optimize_route.m
[ ] README_MATLAB_Framework.md

是否采用 MATLAB 框架（替代 Python）：
[ ] 是，使用 MATLAB 框架
[ ] 否，继续使用 Python 框架
[ ] 待定，需进一步讨论

建模手签名：__________ 日期：__________
```

---

**交付日期**：2026-09-11 晚  
**框架类型**：MATLAB  
**框架版本**：v1.0.0  
**状态**：框架完成，Q1 几何模块待精化  
**优势**：竞赛标准工具，评委认可度高

---

📋 MATLAB 框架已就绪，等待团队确认是否采用！
