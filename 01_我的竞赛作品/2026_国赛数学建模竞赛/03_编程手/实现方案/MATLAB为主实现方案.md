# MATLAB 为主实现方案

> ✅ **裁定：以 MATLAB 为主（2026-09-12，队员裁决）**
> 本文件主张「**以 MATLAB 为主**」，曾与同一提交中 `03_编程手/README.md` 所引**回执**的「Python 为主」
> 三处互斥（见 `99_归档/一次性往来_2026-09-11/建模手核验-编程手回执-2026-09-11.md` §二.1）。
> **该冲突已由队员裁决：本项目 Q3/Q4 的实现以 MATLAB 为主。**
> ⇒ 本文件恢复为**有效方案**；Python 侧（`Q3/实验结果/q3_main*.py`）降为**对照/留痕实现**，**不删除**。
> 已同步：`版本管理规范.md` §七、`03_编程手/README.md` §三、`99_归档/一次性往来_2026-09-11/README.md` §三。
>
> ---

> 决策方：编程手 | 日期：2026-09-11 晚
> 目标：以 MATLAB 为主实现 Q3/Q4，响应建模手转交清单

---

## 一、决策理由

### 为什么选择 MATLAB 为主？

1. **竞赛标准工具优势**
   - 评委更熟悉 MATLAB
   - 论文代码截图更专业
   - 符合数模竞赛传统

2. **长期价值**
   - 可复用于其他数模竞赛
   - 易于理解和维护
   - 适合团队协作

3. **功能完整性**
   - MATLAB 数值计算更强
   - 内置优化工具箱
   - 可视化更便捷

4. **避免混乱**
   - 明确一个主实现，不分散精力
   - Python 作为快速验证工具
   - 职责清晰

---

## 二、当前 MATLAB 框架问题诊断

### 建模手指出的 6 处 TODO（含行号）

| # | 文件 | 位置 | 问题 | 优先级 |
|---|------|------|------|--------|
| 1 | `triangulate_source.m` | L16 | 需要 Q1 几何算法 | 🔴 P0 |
| 2 | `Q1_geometry.m` | L42 | `intersect_wedges` 占位 | 🔴 P0 |
| 3 | `Q1_geometry.m` | L64 | `minimum_enclosing_circle` 简化版 | 🔴 P0 |
| 4 | `Q1_geometry.m` | L78 | 旋转卡壳算法未实现 | 🟡 P2 |
| 5 | `clear_source.m` | L48 | 扫掠清除简化版 | 🟡 P1 |
| 6 | `optimize_route.m` | L35 | 2-opt 优化未实现 | 🟡 P2 |

### 核心问题

**🔴 关键阻塞**：Q1 几何三件套未实现
- 半平面交算法（求凸多边形 L）
- 最小包围圆（Welzl 算法）
- 直径计算（旋转卡壳，可选）

**影响范围**：
- `triangulate_source.m` 无法正常工作
- 验收线① M5 无法测试
- Q3/Q4 定位精度受影响

---

## 三、MATLAB 为主实现方案

### 3.1 总体策略

**核心思路**：Python → MATLAB 算法翻译

1. **利用 Python 版本**
   - Python Q1 算法已验证通过（1014行）
   - 直接翻译核心算法到 MATLAB
   - 保证数值一致性

2. **分步实施**
   - Step 1: Q1 几何模块（P0）
   - Step 2: Q3 完整功能（P0）
   - Step 3: Q4 扩展功能（P1）
   - Step 4: 优化和断言（P1/P2）

3. **验证策略**
   - 每个模块用 Q1 基准算例验证
   - Python/MATLAB 交叉验证
   - 确保数值误差 < 1e-6

---

### 3.2 详细实施计划

#### Phase 1: Q1 几何模块（P0）- 4小时

**任务 1.1：半平面交算法**（2小时）

```matlab
% 文件: Q1_geometry.m
% 函数: intersect_wedges(wedges)

% 算法流程：
% 1. 每个角域的两条边界射线转为半平面
% 2. 构造半平面不等式 Ax <= b
% 3. 求所有半平面的交集（凸多边形）
% 4. 返回顶点列表

% 参考：Python 版 q1_main.py L150-L280
```

**实现方法**：
- 方案 A：直接翻译 Python 算法
- 方案 B：使用 MATLAB `polyshape` + 布尔运算
- **推荐**：方案 B（简单高效）

**验证**：Q1 基准算例（S1=(0,0), S2=(39.598,0), θ1=45°, θ2=135°）

---

**任务 1.2：最小包围圆**（1.5小时）

```matlab
% 文件: Q1_geometry.m
% 函数: minimum_enclosing_circle(L)

% 算法：Welzl 递归算法
% 1. 随机选择点集
% 2. 递归构造最小包围圆
% 3. 边界条件：0/1/2/3 点的情况

% 参考：Python 版 q1_main.py L400-L550
```

**实现方法**：
- 翻译 Python Welzl 算法
- 或使用 MATLAB File Exchange 现成实现
- **推荐**：翻译 Python（可控）

**验证**：R_MEC = 19.799 m（Q1 基准）

---

**任务 1.3：凸多边形直径**（0.5小时）

```matlab
% 文件: Q1_geometry.m
% 函数: polygon_diameter(L)

% 算法：暴力 O(n²)（n 通常 < 10）
% 旋转卡壳 O(n log n) 可选

% 参考：Python 版 q1_main.py L350-L380
```

**实现方法**：
- 先实现暴力版（够用）
- P2 阶段可选优化为旋转卡壳

**验证**：D = 39.598 m（Q1 基准）

---

#### Phase 2: Q3 完整功能（P0）- 3小时

**任务 2.1：交会定位**（1小时）

```matlab
% 文件: triangulate_source.m
% 功能: 从观测交会定位源

% 流程：
% 1. 取两个观测构造角域
% 2. 调用 Q1_geometry.intersect_wedges
% 3. 调用 Q1_geometry.minimum_enclosing_circle
% 4. 返回 source_info 结构体
```

**集成**：
- 调用 Phase 1 完成的 Q1 几何模块
- 补充观测记录管理

---

**任务 2.2：断言自动化**（1.5小时）

```matlab
% 文件: run_assertions.m（新建）

% 实现断言 1-11（离线部分）：
% - 断言 1: 覆盖自检（已有）
% - 断言 2: 间距约束（已有）
% - 断言 3: 单元数下界（已有）
% - 断言 4: Q1 判据回归
% - 断言 5: homing 收缩率
% - 断言 6: 移动时间下界
% - 断言 10: 清除判据充要
% - 断言 11: 元断言
```

**重点**：断言 6（移动时间下界 >= 703.7168s）

---

**任务 2.3：主策略完善**（0.5小时）

```matlab
% 文件: main_Q3Q4.m
% 补充：
% - TSP 路径优化（贪心足够）
% - 两阶段巡游逻辑
% - 完备性判定
```

---

#### Phase 3: Q4 扩展功能（P1）- 4小时

**任务 3.1：外扩环带**（1小时）

```matlab
% 文件: generate_triangular_grid.m
% 修改: 支持 extend_for_Q4 参数

% 逻辑：
% 1. 生成 R < ||p|| <= R + d/√3 的环带格点
% 2. 与圆域内格点合并
% 3. 去重
```

**验证**：d=1000 → 13-15 点（含环带）

---

**任务 3.2：surrounding 判定**（1小时）

```matlab
% 文件: Q1_geometry.m（新增函数）
% 函数: is_surrounding(G, P, R_eff)

% 算法：
% 1. 筛选 ||p-G|| <= R_eff 的点
% 2. 求凸包
% 3. 判定 G 是否在凸包内
```

**参考**：Q4-F4

---

**任务 3.3：扇区探针**（1.5小时）

```matlab
% 文件: sector_probe.m（新建）
% 功能: 判别 no_signal 的原因（Q4 专用）

% 三点判别法（Q4-F15）：
% 1. 在 G 周围取 3 个检测点（相位 120°）
% 2. 统计观测次数 n_obs
% 3. 判定：0 → 无源，3 → 全向，1-2 → 定向
```

---

**任务 3.4：Q4 必过断言**（0.5小时）

```matlab
% 断言 1: surrounding 覆盖验证
% 断言 2: 外扩环带点数验证
% 断言 3: 扇区探针正确性
```

---

#### Phase 4: 优化和完善（P1/P2）- 3小时

**任务 4.1：设计常数落点**（0.5小时）

- H1: 免扫掠设计定理（992.3920）
- H2: 双轨网格基准值（30.2300 / 20.1533）

**任务 4.2：扫掠清除精确版**（1小时）

- 用三角格精确覆盖 L
- 密度 1.2091996

**任务 4.3：可视化和文档**（1.5小时）

- 路径可视化
- 下界对照图
- 使用说明完善

---

### 3.3 时间总计

| 阶段 | 任务 | 时间 | 优先级 |
|------|------|------|--------|
| **Phase 1** | Q1 几何模块 | 4h | 🔴 P0 |
| **Phase 2** | Q3 完整功能 | 3h | 🔴 P0 |
| **Phase 3** | Q4 扩展功能 | 4h | 🟡 P1 |
| **Phase 4** | 优化完善 | 3h | 🟡 P1/P2 |
| **总计** | | **14h** | |

---

## 四、执行排期

### 今晚（9-11）- 4小时

**Phase 1: Q1 几何模块**
- 22:00-00:00 半平面交算法（2h）
- 00:00-01:30 最小包围圆（1.5h）
- 01:30-02:00 凸多边形直径（0.5h）

**验收标准**：
```matlab
% 运行 Q1 基准算例
[c_star, R_MEC] = test_Q1_baseline();
assert(abs(R_MEC - 19.799) < 0.01);
fprintf('✅ Q1 几何模块验证通过\n');
```

---

### 明天（9-12）- 7小时

**上午（4h）**：
- 08:00-09:00 Phase 2.1 交会定位（1h）
- 09:00-10:30 Phase 2.2 断言自动化（1.5h）
- 10:30-11:00 Phase 2.3 主策略完善（0.5h）
- 11:00-12:00 Phase 3.1 外扩环带（1h）

**下午（3h）**：
- 14:00-15:00 Phase 3.2 surrounding（1h）
- 15:00-16:30 Phase 3.3 扇区探针（1.5h）
- 16:30-17:00 Phase 3.4 Q4 断言（0.5h）

**验收标准**：
```matlab
% Q3 验证
results = main_Q3Q4('Q3');
assert(results.cleared_ratio == 1.0);  % 100%

% Q4 验证
results = main_Q3Q4('Q4');
assert(results.cleared_ratio == 1.0);  % 100%
```

---

### 后天（9-13）- 3小时

**上午（3h）**：
- 08:00-08:30 Phase 4.1 设计常数（0.5h）
- 08:30-09:30 Phase 4.2 扫掠精确版（1h）
- 09:30-11:00 Phase 4.3 可视化文档（1.5h）

**下午**：
- 模拟器测试
- 双轨标定
- 论文补充

---

## 五、技术路线

### 5.1 核心算法来源

**从 Python 到 MATLAB**：

```python
# Python 版（q1_main.py）
def intersect_wedges(wedges):
    # ... 半平面交算法
    return L

def minimum_enclosing_circle(L):
    # ... Welzl 算法
    return c_star, R_MEC
```

↓ 翻译 ↓

```matlab
% MATLAB 版（Q1_geometry.m）
function L = intersect_wedges(wedges)
    % ... 翻译算法
end

function [c_star, R_MEC] = minimum_enclosing_circle(L)
    % ... 翻译算法
end
```

**验证策略**：
- 相同输入 → 相同输出
- 数值误差 < 1e-6
- 交叉验证通过

---

### 5.2 快速实现技巧

**技巧 1：利用 MATLAB 内置函数**

```matlab
% 凸包
CH = convhull(points);

% 多边形布尔运算
poly1 = polyshape([x1, y1]);
poly2 = polyshape([x2, y2]);
poly_intersect = intersect(poly1, poly2);

% 点到多边形距离
d = pdist2(point, polygon_points);
```

**技巧 2：File Exchange 资源**

- Welzl 算法实现
- 旋转卡壳算法
- TSP 求解器

**技巧 3：向量化计算**

```matlab
% 避免循环
distances = sqrt(sum((P - pos).^2, 2));  % 向量化
min_dist = min(distances);

% 而非
for i = 1:size(P, 1)
    dist(i) = norm(P(i,:) - pos);
end
```

---

## 六、风险控制

### 6.1 主要风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| Q1 算法翻译困难 | 中 | 高 | Python 版已验证，逐行翻译 |
| 时间不足 | 低 | 高 | 14h 保守估计，有缓冲 |
| 数值精度问题 | 低 | 中 | 交叉验证，容差 1e-6 |
| 模拟器接口问题 | 中 | 中 | HTTP 客户端已实现 |

### 6.2 Plan B

**如果 Phase 1 超时**：
- 保底方案：使用 Python Q1 模块（通过系统调用）
- MATLAB 调用 Python：
  ```matlab
  [c_star, R_MEC] = pyrunfile('q1_wrapper.py', ['c_star', 'R_MEC'], L=L);
  ```

**如果 Phase 3 超时**：
- Q4 降级为 Q3 的简单扩展
- 保证 Q3 功能完整

---

## 七、Python 的角色

**定位**：快速验证工具 + 备选方案

**用途**：
1. **算法验证**：MATLAB 实现前用 Python 快速验证思路
2. **数值对照**：MATLAB 实现后与 Python 交叉验证
3. **调试工具**：MATLAB 出问题时用 Python 定位
4. **备选方案**：MATLAB 完全失败时的保底

**不做**：
- ❌ 不作为主实现
- ❌ 不用于正式测试
- ❌ 不用于论文代码

---

## 八、验收标准

### 8.1 Phase 1 验收（Q1 几何）

```matlab
% 测试脚本: test_Q1_geometry.m

% 测试 1: Q1 基准算例
wedges = [wedge([0,0], 45, 1); wedge([39.598,0], 135, 1)];
L = Q1_geometry.intersect_wedges(wedges);
[c_star, R_MEC] = Q1_geometry.minimum_enclosing_circle(L);
[D, p1, p2] = Q1_geometry.polygon_diameter(L);

assert(abs(D - 39.598) < 0.01, 'D 不匹配');
assert(abs(R_MEC - 19.799) < 0.01, 'R_MEC 不匹配');
fprintf('✅ Q1 几何模块通过\n');
```

### 8.2 Phase 2 验收（Q3 功能）

```matlab
% 测试脚本: test_Q3_complete.m

% 网格生成
P = generate_triangular_grid(struct('d', 1500, 'R_domain', 1800));
assert(7 <= length(P) <= 9, '点数不符');

% 覆盖自检
[ok, max_dist] = coverage_check(P, config);
assert(ok && max_dist <= 1000, '覆盖失败');

% 断言 1-11（离线部分）
run_assertions('Q3');
fprintf('✅ Q3 完整功能通过\n');
```

### 8.3 Phase 3 验收（Q4 功能）

```matlab
% 测试脚本: test_Q4_extensions.m

% 外扩环带
P_ext = generate_triangular_grid(struct('d', 1000, 'extend_for_Q4', true));
assert(13 <= length(P_ext) <= 15, '环带点数不符');

% surrounding
G = [1500, 0];
assert(is_surrounding(G, P_ext), 'surrounding 失败');

% Q4 断言
run_assertions('Q4');
fprintf('✅ Q4 扩展功能通过\n');
```

---

## 九、交付清单

### 9.1 代码文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `Q1_geometry.m` | 🔄 补全 | 半平面交 + MEC + 直径 |
| `triangulate_source.m` | 🔄 补全 | 交会定位 |
| `clear_source.m` | ✅ 保持 | 三路清除 |
| `generate_triangular_grid.m` | 🔄 扩展 | 支持 Q4 环带 |
| `sector_probe.m` | ➕ 新增 | 扇区探针 |
| `run_assertions.m` | ➕ 新增 | 断言 1-11 |
| `test_*.m` | ➕ 新增 | 验收测试 |

### 9.2 文档更新

- [x] MATLAB框架交付说明书（已有）
- [ ] 更新 TODO 标记（6处 → 0处）
- [ ] 补充算法说明
- [ ] 更新行数统计

---

## 十、总结

### ✅ 方案优势

1. **符合竞赛标准**：MATLAB 是数模竞赛主流工具
2. **时间可控**：14小时保守估计，3天完成
3. **质量保证**：逐步验证，Python 交叉对照
4. **可维护**：纯 MATLAB，无混合调用

### 📊 工作量对比

| 方案 | MATLAB 工作量 | Python 工作量 | 总计 |
|------|--------------|--------------|------|
| **Python 为主** | 3h（原型） | 6-9h（补全） | 9-12h |
| **MATLAB 为主** | 14h（完整） | 0h（验证） | 14h |

**差距**：仅 2-5h，可接受

### 🎯 最终目标

- ✅ MATLAB 完整可运行（Q3/Q4）
- ✅ 通过所有断言验证
- ✅ 模拟器测试 100% 清除
- ✅ 论文代码全部 MATLAB
- ✅ Python 保留作为验证工具

---

**决策确认**：✅ 以 MATLAB 为主实现

**下一步行动**：立即开始 Phase 1（Q1 几何模块，4h）

**承诺交付**：9-13 上午完成所有 MATLAB 代码

---

**编程手签名**：Claude Code  
**日期**：2026-09-11 晚  
**状态**：方案确定，立即执行
