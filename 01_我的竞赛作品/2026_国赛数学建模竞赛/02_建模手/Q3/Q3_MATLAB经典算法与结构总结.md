# Q3 MATLAB代码中的经典算法与结构总结

> **代码规模**：~2000行，16个.m文件  
> **时间**：2026-09-11  
> **质量评价**：数学内核优秀（Agent 1/2验证通过），工程实现待完善

---

## 一、核心算法清单（按复杂度排序）

### 🔴 高级算法（教科书级）

#### 1. **Welzl最小包围圆算法**（O(n)期望）
**文件**：`Q1_geometry.m:64-171`

**算法特点**：
- **随机增量式**递归算法
- 期望时间复杂度 **O(n)**（最坏O(n²)）
- 1991年由Emo Welzl提出

**核心思想**：
```matlab
function [c, r] = welzl_recursive(P, R, n)
    % P: 剩余点集, R: 边界点集
    if n == 0 || length(R) == 3
        return min_circle_trivial(R);  % 基础情况
    end
    
    p = P(randi(n));  % 随机选点（关键！）
    [c, r] = welzl_recursive(P, R, n-1);  % 递归不含p
    
    if norm(p - c) <= r
        return [c, r];  % p在圆内
    else
        return welzl_recursive(P, [R; p], n-1);  % p必在边界
    end
end
```

**数学基础**：
- 最小包围圆由≤3个点唯一确定
- 边界点集R的增长是单调的
- 随机化保证期望线性复杂度

**应用场景**：Q1定位区域L的最小外接圆 → R_MEC判据

---

#### 2. **半平面交算法**（O(n log n)）
**文件**：`Q1_geometry.m:13-61`

**算法特点**：
- 使用MATLAB内置`polyshape`的布尔运算
- 本质是**Sutherland-Hodgman裁剪**的推广
- 复杂度取决于polyshape实现（通常O(n log n)）

**核心思想**：
```matlab
function L = intersect_wedges(wedges)
    result_poly = polyshape(大正方形);  % 初始全平面
    
    for i = 1:length(wedges)
        sector = construct_sector(wedges(i));  % 构造扇形
        result_poly = intersect(result_poly, sector);  % 逐个求交
    end
    
    L = result_poly.Vertices;  % 提取交集顶点
end
```

**几何背景**：
- 角域 = 半平面
- n个半平面交 = 凸多边形
- 退化情况：空集、无界域

**应用场景**：多个观测角域的交会定位

---

#### 3. **旅行商问题近似算法**（贪心最近邻）
**文件**：`optimize_route.m`

**算法特点**：
- 经典**贪心最近邻**（Nearest Neighbor Heuristic）
- 时间复杂度 **O(n²)**
- 近似比无理论保证，实践中通常1.2-1.5倍最优解

**核心思想**：
```matlab
function route = greedy_nearest_neighbor(points)
    current = [0, 0];  % 起点
    unvisited = 1:n;
    route = [];
    
    while ~isempty(unvisited)
        [~, idx] = min(distances(current, points(unvisited, :)));
        next = unvisited(idx);
        route = [route; next];
        current = points(next, :);
        unvisited(idx) = [];
    end
end
```

**已知问题**：
- 审核报告指出：这是**上界算法**，不能用于验证下界
- 文档错误地用它验证703.7168s的移动时间下界

**改进方向**：
- 2-opt局部优化
- 最小生成树（MST）下界
- Christofides算法（1.5倍近似比）

---

### 🟡 中级算法

#### 4. **有限状态机**（FSM）
**文件**：`ChannelStateMachine.m`

**设计模式**：
- **状态模式**（State Pattern）
- 状态：`empty` / `exploring` / `triangulating` / `confirmed_empty`

**状态转移**：
```matlab
classdef ChannelStateMachine
    properties
        state           % 当前状态
        observations    % 观测历史
        no_signal_positions  % P0-7修复：按点id去重的集合
    end
    
    methods
        function update(obj, position_id, result)
            switch obj.state
                case 'empty'
                    if result == 'signal'
                        obj.state = 'exploring';
                    end
                case 'exploring'
                    if length(obj.observations) >= 2
                        obj.state = 'triangulating';
                    end
                % ... 其他转移
            end
        end
    end
end
```

**设计优点**：
- 状态显式化，易于调试
- 符合题目的阶段性流程

**已修复问题**：
- P0-7：原用计数器判空 → 改为按position_id去重集合

---

#### 5. **策略模式**（Strategy Pattern）
**文件**：`clear_source.m`

**三路策略**：
```matlab
function [success, cost, mode] = clear_source(source, config)
    if R_MEC <= 20
        mode = 'direct';        % 直接清除
    elseif R_MEC <= 84.0369
        mode = 'sweep';         % 扫掠清除
    else
        mode = 'homing';        % Homing逼近
    end
end
```

**设计常数**（来自建模手）：
- R_clear = 20m（题目给定）
- R_star = 84.0369m（设计常数H1推导）
- R_no_sweep = 992.3920m（安全裕度）

**已修复问题**：
- P0-2：扫掠清除原截断前N_sweep个点 → 改为遍历全部中心直到成功

---

#### 6. **网格生成算法**（三角剖分覆盖）
**文件**：`generate_triangular_grid.m`

**算法**：
- **等边三角形密铺**
- 覆盖半径 = d/√3（正三角形内切圆半径）

**生成逻辑**：
```matlab
function P = generate_triangular_grid(d, R_domain)
    h = d * sqrt(3) / 2;  % 三角形高
    
    for row = 0:max_rows
        y = row * h;
        x_offset = mod(row, 2) * (d/2);  % 奇数行错开
        
        for col = 0:max_cols
            x = col * d + x_offset;
            if norm([x, y]) <= R_domain
                P = [P; x, y];
            end
        end
    end
end
```

**数学基础**：
- d=1500m → 覆盖半径 866.025m
- d=1000m → 覆盖半径 577.350m
- 点数 Q3约7个，Q4约13个（实测）

---

### 🟢 基础算法

#### 7. **凸包算法**（Convex Hull）
**文件**：`Q4_extensions.m` 调用MATLAB内置`convhull`

**算法**：
- MATLAB使用**Quickhull算法**
- 平均 O(n log n)，最坏 O(n²)

**应用**：
```matlab
function is_surr = is_surrounding(G, P, R_eff)
    % 筛选R_eff内的点
    idx = vecnorm(P - G, 2, 2) <= R_eff;
    P_in = P(idx, :);
    
    % 凸包
    if size(P_in, 1) < 3
        is_surr = false;
        return;
    end
    k = convhull(P_in(:,1), P_in(:,2));
    hull = P_in(k, :);
    
    % 判断G是否在凸包内
    is_surr = inpolygon(G(1), G(2), hull(:,1), hull(:,2));
end
```

**数学定理**：
- **充要性命题**（Agent 1验证通过）：  
  `G ∈ conv{p: ||p-G|| ≤ R_eff}` ⟺ 任意朝向定向源必被至少一点测到

---

#### 8. **点在多边形内判定**（Ray Casting）
**文件**：MATLAB内置`inpolygon`

**算法**：
- **射线法**（Ray Casting Algorithm）
- 时间复杂度 O(n)

**原理**：
- 从点发射水平射线
- 统计与多边形边的交点数
- 奇数次 → 内部，偶数次 → 外部

---

#### 9. **欧几里得距离矩阵**
**文件**：多处使用`vecnorm`、`pdist2`

```matlab
% 向量化距离计算
distances = vecnorm(points - repmat(target, n, 1), 2, 2);

% 成对距离矩阵
D = pdist2(points_A, points_B);
```

**优势**：
- 避免显式循环
- 利用MATLAB向量化加速

---

## 二、数据结构设计

### 1. **结构体（struct）- 数据载体**

#### 观测结构
```matlab
observation = struct(...
    'position', [x, y], ...
    'position_id', id, ...
    'channel', c, ...
    'result', 'signal'/'no_signal', ...
    'svd_deg', angle ...
);
```

#### 源结构
```matlab
source = struct(...
    'channel', c, ...
    'L', polygon_vertices, ...
    'c_star', [cx, cy], ...
    'R_MEC', radius, ...
    'D', diameter ...
);
```

---

### 2. **对象（classdef）- 封装状态**

#### 状态机类
```matlab
classdef ChannelStateMachine < handle  % handle = 引用语义
    properties
        state
        observations
        no_signal_positions  % 集合（cell array模拟）
    end
    
    methods
        function update(obj, ...)
            % 修改内部状态
        end
    end
end
```

**关键**：`< handle` 继承 → 引用传递（否则MATLAB默认值传递）

---

#### HTTP客户端类
```matlab
classdef SimulatorClient < handle
    properties
        base_url
        session  % HTTP会话对象
    end
    
    methods
        function obj = SimulatorClient(url)
            obj.base_url = url;
            obj.session = [];
        end
        
        function resp = post(obj, endpoint, body)
            % 幂等HTTP封装
        end
    end
end
```

**设计亮点**：
- 幂等性设计（每次请求独立）
- 超时重试机制
- JSON序列化/反序列化

---

### 3. **单例配置（config struct）**

```matlab
config = struct(...
    'R_domain', 1800, ...
    'velocity', 5, ...
    'R_clear', 20, ...
    'R_star', 84.0369, ...
    'T_detect', 5, ...
    'T_switch', 1, ...
    'T_clear_success', 5, ...
    'T_clear_fail', 3 ...
);
```

**模式**：全局配置传递，避免硬编码

---

## 三、编程范式与技巧

### 1. **函数式编程**

#### 高阶函数
```matlab
% arrayfun - 逐元素应用函数
distances = arrayfun(@(i) norm(points(i,:) - target), 1:n);

% cellfun - 逐cell应用
lengths = cellfun(@length, cell_array);
```

#### Lambda表达式
```matlab
is_valid = @(x) x > 0 && x < 100;
filtered = points(arrayfun(is_valid, points(:,1)), :);
```

---

### 2. **向量化编程**

**避免循环**：
```matlab
% BAD: 显式循环
for i = 1:n
    distances(i) = norm(points(i,:) - target);
end

% GOOD: 向量化
distances = vecnorm(points - repmat(target, n, 1), 2, 2);
```

**性能提升**：通常10-100倍

---

### 3. **错误处理**

#### Try-Catch包装
```matlab
try
    source = triangulate_source(obs, config);
    if ~isempty(source)
        discovered_sources{end+1} = source;
    end
catch ME
    warning('定位失败: %s', ME.message);
    continue;
end
```

**已修复**：P0-1将triangulate_source整体移入try，避免崩溃

---

### 4. **断言与自检**

```matlab
function results = run_assertions(mode)
    % 断言1: 覆盖自检
    assert(coverage_ratio >= 0.99, '覆盖率不足');
    
    % 断言2: 间距约束
    assert(all(min_distances >= d_expected * 0.99), '间距过小');
    
    % ... 8个断言
end
```

**价值**：自动化回归测试

**已修复**：断言真8/8（原虚假通过率）

---

## 四、算法复杂度分析

| 算法 | 时间复杂度 | 空间复杂度 | 瓶颈 |
|------|-----------|-----------|------|
| Welzl最小包围圆 | **O(n)期望** | O(n) | 递归栈深度 |
| 半平面交 | **O(n log n)** | O(n) | polyshape内部排序 |
| 凸多边形直径 | **O(n²)** | O(1) | 暴力枚举（可优化到O(n)旋转卡壳） |
| 贪心TSP | **O(n²)** | O(n) | 距离计算 |
| 三角网格生成 | **O(R²/d²)** | O(n) | 圆域面积/单元面积 |
| 凸包 | **O(n log n)** | O(n) | Quickhull |
| 点在多边形内 | **O(n)** | O(1) | 射线法 |

**整体复杂度**：
- Q3单次运行：O(n²)（路径优化主导）
- Q4扩展：O(n²)（环带点数增加）

---

## 五、代码质量评估

### ✅ 优点

1. **算法选择恰当**：
   - Welzl算法是O(n)，比暴力O(n⁴)优秀
   - 半平面交用polyshape，避免手写复杂几何

2. **模块化清晰**：
   - Q1_geometry独立封装
   - 状态机单独成类
   - 策略模式分离三路清除

3. **向量化程度高**：
   - 大量使用MATLAB内置向量运算
   - 避免显式for循环

4. **数学内核正确**：
   - Agent 1/2验证：32个常数逐位吻合
   - Q1几何9位小数精度

### ⚠️ 缺点

1. **算法选择失误**：
   - 凸多边形直径用暴力O(n²)，应用旋转卡壳O(n)
   - TSP用贪心，应补充2-opt或MST下界

2. **工程实现问题**：
   - P0-1：字段名错误导致崩溃
   - P0-2：扫掠截断bug
   - P0-7：状态机计数器未去重

3. **性能未优化**：
   - 无随机种子（Welzl不可复现）
   - 无缓存机制
   - HTTP请求无连接池

---

## 六、可扩展性分析

### 容易扩展的部分

1. **新增清除策略**：
   - 策略模式天然支持
   - 只需添加新函数并修改if-elseif

2. **新增断言**：
   - run_assertions框架完整
   - 添加新case即可

3. **更换路径算法**：
   - optimize_route接口清晰
   - 替换内部实现不影响外部

### 难以扩展的部分

1. **多机器人协同**：
   - 状态机是单频道设计
   - 需要重构为multi-agent架构

2. **动态障碍物**：
   - 网格生成是静态的
   - 需要实时重规划

3. **不确定性源**：
   - R_eff当前假设已知
   - 需要贝叶斯滤波估计

---

## 七、教学价值

### 适合用于教学的算法

1. ⭐⭐⭐⭐⭐ **Welzl最小包围圆**
   - 经典随机增量式算法
   - 体现递归与分治思想
   - 代码简洁优雅

2. ⭐⭐⭐⭐ **状态机模式**
   - 设计模式典范
   - 状态转移可视化
   - 易于理解与调试

3. ⭐⭐⭐⭐ **半平面交**
   - 计算几何基础
   - 凸包的推广
   - 实用价值高

4. ⭐⭐⭐ **贪心TSP**
   - 经典NP-hard问题
   - 启发式算法入门
   - 展示近似算法思想

### 教学建议

- 讲Welzl时强调随机化的作用
- 讲状态机时画状态转移图
- 讲TSP时对比精确解与近似解

---

## 八、与Python版本对比

| 维度 | MATLAB版 | Python版 |
|------|---------|---------|
| 代码量 | ~2000行 | ~1500行 |
| 可读性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 性能 | 向量化快 | NumPy持平 |
| 几何库 | polyshape强大 | Shapely功能少 |
| 状态机 | classdef封装 | dataclass简洁 |
| 类型安全 | 弱类型 | 有类型提示 |

**结论**：MATLAB版几何计算更优雅，Python版工程结构更清晰

---

## 九、总结

### 核心算法排行（按重要性）

1. 🥇 **Welzl最小包围圆**（定位核心）
2. 🥈 **半平面交**（角域交会）
3. 🥉 **有限状态机**（流程控制）
4. **策略模式**（清除路由）
5. **三角网格覆盖**（巡逻基础）

### 代码质量总评

- **数学内核**：⭐⭐⭐⭐⭐（优秀）
- **算法选择**：⭐⭐⭐⭐（良好）
- **工程实现**：⭐⭐⭐（待改进）
- **可维护性**：⭐⭐⭐⭐（良好）

### 学习价值

本代码是**竞赛级数学建模代码的典范**：
- 算法与数学紧密结合
- 工程实现相对完整
- 适合作为算法教学案例

**建议学习路径**：
1. 先读Q1_geometry.m（最优雅）
2. 再读ChannelStateMachine.m（设计模式）
3. 最后读main_Q3Q4.m（整体架构）

---

**文档版本**：v1.0  
**创建时间**：2026-09-12  
**作者**：编程手审核总结
