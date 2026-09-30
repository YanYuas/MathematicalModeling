# math_modeling.py — 数学建模算法库文档

## 概述

`math_modeling.py` 是一个汇集数学建模竞赛常用算法的 Python 库，包含 **67 个函数和类**，分为 17 个板块。所有函数均为纯函数设计（接受参数、返回结果、不打印不画图），可直接在建模项目中调用。

### 安装依赖

```bash
# 核心依赖（必须）
pip install numpy scipy

# 可选依赖（按需安装）
pip install scikit-learn pulp statsmodels
```

### 快速上手

```python
import numpy as np
from math_modeling import topsis_evaluate, gm11_predict

# TOPSIS综合评价
data = np.array([[89, 3999, 48], [92, 4299, 45], [78, 2999, 50]])
weights = np.array([0.3, 0.3, 0.4])
is_benefit = np.array([True, False, True])
scores, info = topsis_evaluate(data, weights, is_benefit)
print(f"排名: {info['ranking']}")

# GM(1,1)灰色预测
x0 = np.array([120, 135, 150, 170, 190, 215])
forecast, info = gm11_predict(x0, forecast_steps=3)
print(f"预测值: {forecast}, 精度: {info['grade']}")
```

---

## 目录

1. [评价方法](#1-评价方法) — 8个函数
2. [预测方法](#2-预测方法) — 6个函数
3. [线性优化](#3-线性优化) — 3个函数
4. [非线性优化](#4-非线性优化) — 3个函数
5. [动态规划](#5-动态规划) — 1个函数
6. [智能优化](#6-智能优化) — 3个函数
7. [图算法](#7-图算法) — 2个函数
8. [微分方程模型](#8-微分方程模型) — 3个函数
9. [降维方法](#9-降维方法) — 2个函数
10. [异常值检测](#10-异常值检测) — 2个函数
11. [插值方法](#11-插值方法) — 1个函数
12. [概率分布](#12-概率分布) — 9个类
13. [统计检验](#13-统计检验) — 4个函数
14. [参数估计](#14-参数估计) — 3个函数
15. [相关性分析](#15-相关性分析) — 5个函数
16. [中心极限定理](#16-中心极限定理) — 2个函数
17. [机器学习](#17-机器学习) — 9个函数

---

## 1. 评价方法

### `ahp_evaluate(judgment_matrix, check_consistency=True)`

**用途**: 层次分析法（AHP），通过判断矩阵的特征向量确定各指标的权重。

**数学原理**: 计算判断矩阵的最大特征值 `λmax` 及其对应的特征向量，特征向量归一化后即为权重。通过 `CI = (λmax - n)/(n-1)` 和 `CR = CI/RI` 检验矩阵一致性（`CR < 0.1` 表示通过一致性检验）。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `judgment_matrix` | np.ndarray (n,n) | 必填 | 1-9标度的判断矩阵，A[i,j]越大表示指标i比j越重要 |
| `check_consistency` | bool | True | 是否进行一致性检验 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `weights` | np.ndarray (n,) | 归一化权重向量 |
| `info` | dict | `max_eigenvalue`, `CI`, `CR`, `RI`, `is_consistent` |

**适用场景**: 多准则决策问题的指标权重确定（如供应商选择、项目评估）；专家评分系统中将主观判断量化为权重。

**示例**:
```python
A = np.array([[1, 2, 3], [1/2, 1, 2], [1/3, 1/2, 1]])
weights, info = ahp_evaluate(A)
# weights = [0.539, 0.297, 0.164]
# info['CR'] = 0.008 < 0.1 通过一致性检验
```

---

### `topsis_evaluate(data, weights, is_benefit=None)`

**用途**: TOPSIS综合评价法，将各方案与正理想解和负理想解比较，计算贴近度排序。

**数学原理**: 向量归一化 → 加权标准化 → 确定正/负理想解 → 计算到理想解的欧氏距离 `D^+`, `D^-` → 贴近度 `C = D^-/(D^+ + D^-)` → 按C降序排列。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `data` | np.ndarray (m,n) | 必填 | m个方案，n个指标 |
| `weights` | np.ndarray (n,) | 必填 | 各指标权重，和为1 |
| `is_benefit` | np.ndarray (n,) | 全True | True=效益型（越大越好），False=成本型（越小越好） |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `scores` | np.ndarray (m,) | 贴近度，越大越优 |
| `info` | dict | `ranking`, `d_plus`, `d_minus`, `ideal_plus`, `ideal_minus` |

**适用场景**: 多方案综合评价（如手机选购、供应商评估）；需要同时考虑效益型和成本型指标的决策问题。

**示例**:
```python
data = np.array([[89,3999,48], [92,4299,45], [78,2999,50]])
weights = np.array([0.3, 0.2, 0.5])
is_benefit = np.array([True, False, True])  # 价格越低越好
scores, info = topsis_evaluate(data, weights, is_benefit)
```

---

### `entropy_weight_evaluate(data)`

**用途**: 熵权法，利用信息熵自动确定各指标的客观权重，指标的变异程度越大权重越大。

**数学原理**: 归一化 → 计算比重 `p_ij` → 计算信息熵 `e_j = -kΣp·log(p)` → 冗余度 `d_j = 1-e_j` → 归一化得权重 `w_j = d_j/Σd` → 加权求和得综合得分。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `data` | np.ndarray (m,n) | 必填 | m个方案，n个指标（均视为效益型） |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `scores` | np.ndarray (m,) | 综合得分 |
| `info` | dict | `weights`, `entropy`, `ranking` |

**适用场景**: 无需主观赋权的综合评价（客观赋权）；指标重要性未知时的探索性分析。

---

### `fuzzy_comprehensive_evaluate(data, weights, criteria)`

**用途**: 模糊综合评价法，通过隶属度函数将定量指标映射到定性等级，实现综合评判。

**数学原理**: 为每个指标设定等级标准值，用线性隶属函数计算各等级的隶属度，加权合成综合评价向量，最后以等级赋分（优=最高分）求综合得分。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `data` | np.ndarray (m,n) | 必填 | m个评价对象，n个指标 |
| `weights` | np.ndarray (n,) | 必填 | 各指标权重 |
| `criteria` | np.ndarray (n,k) | 必填 | 各指标k个等级的标准值（每行从优到劣） |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `scores` | np.ndarray (m,) | 综合得分 |
| `info` | dict | `evaluation_matrix` (m×k), `ranking` |

**适用场景**: 定性与定量混合评价（如员工绩效考核）；带有模糊等级划分的综合评估。

---

### `grey_relational_evaluate(data, reference=None)`

**用途**: 灰色关联分析法，计算各方案与参考序列的灰色关联度，关联度越大方案越优。

**数学原理**: 数据归一化 → 计算与参考序列的绝对差 → 灰色关联系数 `γ = (min_d + ρ·max_d)/(Δ + ρ·max_d)`（`ρ=0.5`） → 对各指标取平均得关联度。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `data` | np.ndarray (m,n) | 必填 | m个方案，n个指标 |
| `reference` | np.ndarray (n,) | 各列最大值 | 理想参考序列 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `r` | np.ndarray (m,) | 灰色关联度 |
| `info` | dict | `ranking`, `gamma` (关联系数矩阵) |

**适用场景**: 小样本、信息不完全的评价问题；区域经济发展评估。

---

### `dea_evaluate(X, Y)`

**用途**: 数据包络分析（DEA-CCR投入导向模型），通过线性规划计算各决策单元的相对效率。

**数学原理**: 对每个DMU求解线性规划。目标：最小化投入比例θ。若θ=1且松弛变量为0则DEA有效，否则效率不足。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `X` | np.ndarray (n,m) | 必填 | n个DMU的m项投入 |
| `Y` | np.ndarray (n,s) | 必填 | n个DMU的s项产出 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `theta` | np.ndarray (n,) | 效率值（≥1有效） |
| `info` | dict | `is_efficient`, `lambda_`, `s_minus`, `s_plus` |

**适用场景**: 多投入多产出的效率评价（如企业效率、医院绩效）；无需预设投入产出权重的客观评价。

---

### `rsr_evaluate(data, weights, is_benefit=None)`

**用途**: 秩和比综合评价法，通过对各指标编秩加权求和得到RSR值，并分档排序。

**数学原理**: 对每个指标按方案值排序编秩（最优值秩为1，成本型反转） → 加权秩和比 `RSR = Σ(R_j·w_j)/m` → 按RSR值分4档（1档最优）。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `data` | np.ndarray (m,n) | 必填 | m个方案，n个指标 |
| `weights` | np.ndarray (n,) | 必填 | 权重 |
| `is_benefit` | np.ndarray (n,) | 全True | 效益型指标标记 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `rsr` | np.ndarray (m,) | 秩和比值 |
| `info` | dict | `ranking`, `grade`（分档1-4） |

**适用场景**: 医院、学校等多指标综合评价；对异常值不敏感的稳健评价。

---

## 2. 预测方法

### `gm11_predict(x0, forecast_steps=1)`

**用途**: GM(1,1)灰色预测模型，适用于数据量少（4-10个点）、信息不完全的预测问题。

**数学原理**: 1-AGO一次累加生成 → 最小二乘法估计发展系数a和灰作用量b → 时间响应函数 `x̂₁(k+1) = (x₀(1)-b/a)·exp(-ak) + b/a` → 累减还原。通过后验差比C和小误差概率P检验模型精度。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `x0` | np.ndarray (n,) | 必填 | 原始非负序列 |
| `forecast_steps` | int | 1 | 预测步数 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `forecast` | np.ndarray | 预测值 |
| `info` | dict | `a`, `b`, `fitted`, `C`, `P`, `grade`（好/合格/勉强/不合格） |

**适用场景**: 经济指标的短期预测；数据稀少情况下的趋势外推（如新产品销量预测）。

---

### `logistic_fit(t_data, y_data, predict_t=None)`

**用途**: Logistic生长曲线拟合，拟合S型增长函数 `y = K/(1+(K/y0-1)·exp(-rt))`。

**数学原理**: 使用 `scipy.optimize.curve_fit` 最小二乘拟合三个参数：环境容量K、增长率r、初值y0。报告决定系数R²。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `t_data` | np.ndarray | 必填 | 时间点 |
| `y_data` | np.ndarray | 必填 | 观测值 |
| `predict_t` | np.ndarray | None | 需要预测的时间点 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `fitted` | np.ndarray | 拟合值 |
| `info` | dict | `K`, `r`, `y0`, `predictions`, `r_squared` |

**适用场景**: 人口增长预测；市场饱和分析（产品生命周期）；技术扩散曲线拟合。

---

### `quadratic_exponential_smooth(data, alpha=0.3, forecast_steps=1)`

**用途**: 二次指数平滑（Holt线性趋势法），适用于具有线性趋势的时间序列。

**数学原理**: 一次平滑 `S₁[t] = α·y[t] + (1-α)·S₁[t-1]` → 二次平滑 `S₂[t] = α·S₁[t] + (1-α)·S₂[t-1]` → 截距 `a = 2S₁[-1] - S₂[-1]` → 趋势 `b = α/(1-α)·(S₁[-1] - S₂[-1])` → 预测 `ŷ(n+k) = a + b·k`。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `data` | np.ndarray (n,) | 必填 | 历史数据 |
| `alpha` | float | 0.3 | 平滑系数(0~1) |
| `forecast_steps` | int | 1 | 预测步数 |

**适用场景**: 具有线性趋势的销量预测；库存管理；短期趋势外推。

---

### `seasonal_index_predict(data, n_seasons=4, forecast_steps=1)`

**用途**: 季节指数预测法，将时间序列分解为趋势项和季节项分别预测后合成。

**数学原理**: 计算各季节的平均值与总平均的比值作为季节指数 → 去季节化 `deseasonalized = y/seasonal_idx` → 对去季节化数据拟合线性趋势 → 预测 = 趋势预测 × 季节指数。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `data` | np.ndarray | 必填 | 含完整周期的历史数据 |
| `n_seasons` | int | 4 | 每周期季节数 |
| `forecast_steps` | int | 1 | 预测步数 |

**适用场景**: 季节性明显的销售预测；旅游客流季度预测；电力负荷预测。

---

### `markov_predict(states, n_states=3, forecast_steps=5)`

**用途**: 马尔可夫链预测，基于状态转移概率矩阵预测未来状态的分布。

**数学原理**: 统计历史状态序列的转移计数量 → 计算转移概率矩阵 `P[i,j] = 从i转移到j的次数/从i转移的总次数` → 初始分布 × Pⁿ 得到第n步的状态分布。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `states` | np.ndarray (n,) int | 必填 | 历史状态序列（0到n_states-1） |
| `n_states` | int | 3 | 状态总数 |
| `forecast_steps` | int | 5 | 预测步数 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `forecast_distributions` | list[np.ndarray] | 未来每步的状态概率分布 |
| `info` | dict | `transition_matrix`, `steady_state`, `most_likely_states` |

**适用场景**: 股票涨跌状态预测；天气状态预测；市场份额变化分析。

---

### `gaussian_process_regress(X_train, y_train, X_test)`

**用途**: 高斯过程回归，使用RBF核进行小样本回归预测，并提供不确定性估计。

**数学原理**: 基于核方法的贝叶斯非参数回归，假设输出服从多元高斯分布，通过最大化对数边际似然优化核超参数，输出预测均值和标准差。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `X_train` | np.ndarray (n,d) | 必填 | 训练特征 |
| `y_train` | np.ndarray (n,) | 必填 | 训练标签 |
| `X_test` | np.ndarray (m,d) | 必填 | 测试特征 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `y_pred` | np.ndarray (m,) | 预测均值 |
| `info` | dict | `std`（预测标准差）, `rmse_train` |

**适用场景**: 小样本精确回归；需要不确定性量化的预测（如实验设计优化、参数调优）。

---

## 3. 线性优化

### `linear_programming_solve(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None, bounds=None, maximize=True)`

**用途**: 求解标准线性规划问题 `max/min cᵀx s.t. A_ub·x ≤ b_ub, A_eq·x = b_eq`。

**适用场景**: 生产资源分配优化；运输调度问题；投资组合分配。

### `integer_programming_solve(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None, maximize=True)`

**用途**: 整数规划求解器，所有决策变量为整数。

**适用场景**: 人员数量分配；设备采购数量规划；不可分割资源的分配。

### `zero_one_programming_solve(c, A_ub=None, b_ub=None, maximize=True)`

**用途**: 0-1规划求解器，所有决策变量只能取0或1。

**适用场景**: 项目选择问题（选或不选）；选址问题；设施布局决策。

---

## 4. 非线性优化

### `nonlinear_programming_solve(obj_func, x0, constraints=None, bounds=None)`

**用途**: 使用SLSQP方法求解带约束的非线性规划问题。

**适用场景**: 非线性成本优化；工程设计参数优化；经济均衡模型。

### `multi_objective_solve(obj_funcs, x0, weights=None, constraints=None, bounds=None)`

**用途**: 加权求和法多目标规划，将多个目标函数转化为单一加权目标。

**适用场景**: 利润与环保平衡分析；成本与质量权衡优化；帕累托前沿探索。

### `steepest_descent(grad_func, x0, learning_rate=0.1, max_iter=1000, tol=1e-6)`

**用途**: 最速下降法（梯度下降法），沿负梯度方向迭代寻优。

**适用场景**: 无约束凸优化；最小二乘问题；机器学习中的参数优化。

---

## 5. 动态规划

### `knapsack_dp(values, weights, capacity)`

**用途**: 0-1背包问题动态规划求解——在不超过背包容量的前提下最大化总价值。

**数学原理**: 状态方程 `dp[i][j] = max(v[i-1] + dp[i-1][j-w[i-1]], dp[i-1][j])`，回溯获取选择的物品。

**适用场景**: 有限资源分配；项目投资组合选择；货物装载优化。

---

## 6. 智能优化

### `genetic_algorithm_optimize(objective_func, bounds, pop_size=50, num_generations=100, ...)`

**用途**: 遗传算法——通过模拟自然选择（选择→交叉→变异）进行全局优化。

**数学原理**: 初始化种群 → 每代：轮盘赌选择父代 → 单点交叉生成子代 → 高斯变异 → 精英保留 → 收敛到最优。

**适用场景**: 多峰函数全局优化；复杂组合优化（如TSP）；机器学习超参数调优。

### `particle_swarm_optimize(objective_func, bounds, num_particles=30, max_iter=100, ...)`

**用途**: 粒子群优化算法——粒子在搜索空间中追踪个体和群体最优位置来收敛。

**数学原理**: `v = w·v + c1·r1·(pbest-x) + c2·r2·(gbest-x)` → `x = x + v`。

**适用场景**: 连续函数的全局优化；神经网络权重优化；参数寻优。

### `simulated_annealing_optimize(objective_func, bounds, initial_temp=100.0, cooling_rate=0.95, ...)`

**用途**: 模拟退火算法——通过模拟物理退火过程以一定概率接受劣解跳出局部最优。

**数学原理**: Metropolis准则：更优则接受；更差则以概率 `exp(-Δ/T)` 接受 → 温度随时间指数下降 `T *= cooling_rate`。

**适用场景**: 大规模组合优化；具有大量局部最优的复杂问题。

---

## 7. 图算法

### `dijkstra_shortest_path(adj_matrix, start_node)`

**用途**: Dijkstra单源最短路径算法，计算从指定源节点到图中所有其他节点的最短路径（要求边权非负）。

**数学原理**: 贪心算法：每次选取距离源节点最近的未访问节点标记为已访问，通过该节点松弛其邻居的距离。

**适用场景**: GPS导航路径规划；网络路由优化；物流配送路径规划。

### `floyd_all_pairs_shortest(adj_matrix)`

**用途**: Floyd-Warshall全源最短路径算法，一次计算出所有节点对之间的最短路径。

**数学原理**: 动态规划三重循环 `dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])`。

**适用场景**: 全网络可达性分析；交通网络连通性评估；社交网络距离度量。

---

## 8. 微分方程模型

### `sir_epidemic_solve(N, I0, beta, gamma, t_span=(0,100), n_points=1000)`

**用途**: SIR传染病模型 `dS/dt=-βSI/N, dI/dt=βSI/N-γI, dR/dt=γI`。

**参数**: `N`总人口, `I0`初始感染者, `beta`感染率, `gamma`恢复率。

**适用场景**: 疫情传播预测；谣言扩散模拟；创新产品市场渗透分析。

### `logistic_population_solve(P0, r, K, t_span=(0,200), n_points=1000)`

**用途**: Logistic人口增长模型 `dP/dt=r·P·(1-P/K)`。

**参数**: `P0`初始人口, `r`内禀增长率, `K`环境承载力。

**适用场景**: 人口增长预测；生物种群动态模拟；市场容量分析。

### `lanchester_war_solve(x0, y0, a, b, t_span=(0,10), max_steps=10000)`

**用途**: 兰彻斯特平方律战争模型 `dx/dt=-b·y, dy/dt=-a·x`。

**参数**: `x0`甲方初始兵力, `y0`乙方初始兵力, `a`乙方效能系数, `b`甲方效能系数。

**适用场景**: 军事对抗模拟；市场竞争分析（广告投入对抗）；资源消耗竞争模型。

---

## 9. 降维方法

### `pca_reduce(data, n_components=2, standardize=True)`

**用途**: 主成分分析线性降维，保留数据最大方差方向。

**适用场景**: 高维数据可视化；特征提取和降噪；去除多重共线性。

### `tsne_reduce(data, n_components=2, perplexity=30, random_state=42)`

**用途**: t-SNE非线性降维，保持局部邻域结构，适合高维数据的二维可视化。

**适用场景**: 聚类结果可视化；数据探索性分析；复杂数据结构的低维展示。

---

## 10. 异常值检测

### `three_sigma_outliers(data)`

**用途**: 3-sigma法则——将超出 `μ ± 3σ` 的点标记为异常值。

**适用场景**: 正态分布数据的异常值筛选；生产过程质量控制。

### `iqr_outliers(data, factor=1.5)`

**用途**: 箱型图IQR法——将超出 `Q1-1.5*IQR` 和 `Q3+1.5*IQR` 的点标记为异常值。

**适用场景**: 偏态或含异常值数据的稳健检测；数据清洗预处理。

---

## 11. 插值方法

### `lagrange_interpolate(x_sample, y_sample, x_interp)`

**用途**: 拉格朗日多项式插值，通过已知采样点拟合插值多项式估计未知点的值。

**数学原理**: 对每个插值点x构造n个拉格朗日基函数 `L_i(x) = Π_{j≠i} (x-x_j)/(x_i-x_j)`，插值结果为 `y(x) = Σ y_i·L_i(x)`。

**适用场景**: 缺失数据补全；数据平滑重采样；函数逼近。

---

## 12. 概率分布

9个概率分布类，均提供 `pdf/pmf()`, `cdf()`, `expectation()`, `variance()`, `std_dev()` 方法：

| 类名 | 分布 | 参数 | 典型应用 |
|------|------|------|----------|
| `Normal(mu, sigma)` | 正态分布 | μ均值, σ标准差 | 测量误差建模、自然现象 |
| `Beta(alpha, beta)` | Beta分布 | α, β > 0 | 概率/比例建模、贝叶斯先验 |
| `Gamma(k, lam)` | Gamma分布 | k形状, λ速率 | 等待时间、降水量 |
| `Geometric(p)` | 几何分布 | 0<p≤1 | 首次成功次数、寿命测试 |
| `Exponential(lam)` | 指数分布 | λ速率>0 | 元器件寿命、等待时间 |
| `Binomial(n, p)` | 二项分布 | n试验, p概率 | 抽样检验、成功率分析 |
| `HyperGeometric(N, M, n)` | 超几何分布 | N总体, M成功, n抽样 | 不放回抽样检验 |
| `Uniform(a, b)` | 均匀分布 | a下限, b上限 | 随机模拟、蒙特卡洛采样 |
| `Poisson(lam)` | 泊松分布 | λ>0 | 单位时间到达数、排队论 |

---

## 13. 统计检验

### `t_test_1sample(data, mu0=0, alpha=0.05, alternative='two-sided')`

**用途**: 单样本t检验——检验样本均值是否与给定值 `mu0` 有显著差异。

**适用场景**: 产品规格检验（如包装重量是否达标）；实验组均值与标准值的比较。

### `t_test_independent(data1, data2, alpha=0.05, alternative='two-sided', equal_var=True)`

**用途**: 独立样本t检验——检验两组独立样本的均值是否有显著差异。

**适用场景**: A/B测试效果对比；实验组与对照组的差异显著性检验。

### `t_test_paired(data1, data2, alpha=0.05, alternative='two-sided')`

**用途**: 配对样本t检验——检验两组配对数据的均值差异。

**适用场景**: 同一对象处理前后对比（如药效检验）；配对实验设计。

### `chi_squared_test(observed, alpha=0.05)`

**用途**: 卡方独立性检验——判断两个分类变量是否独立。

**适用场景**: 问卷调查的交叉分析；基因型分布是否符合理论预期。

---

## 14. 参数估计

### `mle_estimate(xs, param_grid, pmf_or_pdf)`

**用途**: 最大似然估计——通过网格搜索（穷举）使对数似然函数最大的参数值。

**适用场景**: 分布参数的点估计；当数据量较小时的参数拟合。

### `em_gmm_1d(xs, K=2, max_iter=100, tol=1e-4)`

**用途**: EM算法估计一维高斯混合模型参数——对包含多个高斯分量混合的数据进行无监督学习。

**数学原理**: E步计算各样本属于各分量的责任度 → M步用责任度加权更新均值、方差和混合系数 → 迭代至对数似然收敛。

**适用场景**: 混合分布分解（如男女生身高分布分离）；子群体识别。

### `bayes_estimate(xs, theta_grid, prior_func, likelihood_func)`

**用途**: 贝叶斯参数估计——结合先验分布和似然函数计算后验分布和后验均值。

**数学原理**: 贝叶斯定理 `P(θ|x) ∝ P(θ)·P(x|θ)` → 数值化网格计算后验概率 → 加权得后验均值。

**适用场景**: 先验知识较强的参数推断（如结合历史数据的估计）；小样本下的稳健参数估计。

---

## 15. 相关性分析

### `pearson_corr(x, y)`

**用途**: Pearson线性相关系数 — `cov(x,y)/(σx·σy)`，取值范围[-1,1]。

**适用场景**: 两个连续变量的线性相关性分析；特征工程中的特征筛选。

### `spearman_corr(x, y)`

**用途**: Spearman秩相关系数 — 基于秩次的非参数相关度量，对单调关系敏感。

**适用场景**: 异常值较多的数据；非线性但单调的趋势分析。

### `kendall_corr(x, y)`

**用途**: Kendall τ秩相关系数 — 基于数据对序关系一致性/不一致性计数的非参数度量。

**适用场景**: 小样本相关性检验；有序分类变量的关联分析。

### `covariance(x, y, sample=True)`

**用途**: 协方差计算。

### `chebyshev_bound(k)`

**用途**: 切比雪夫不等式界 `P(|X-μ| ≥ kσ) ≤ 1/k²`。

**适用场景**: 概率上界估计；样本量确定；理论证明辅助。

---

## 16. 中心极限定理

### `clt_lindeberg_levy(x, mu, var, n)`

**用途**: Lindeberg-Levy CLT — 计算i.i.d.样本和的正态近似概率。

**适用场景**: 大样本统计推断；置信区间构建原理教学。

### `clt_demoivre_laplace(k, n, p)`

**用途**: De Moivre-Laplace CLT — 二项分布的正态近似（带连续性校正）。

**适用场景**: 大样本比例估计；抽样调查结果分析。

---

## 17. 机器学习

### `kmeans_cluster(data, n_clusters=3, random_state=42, standardize=True)`

**用途**: K-means硬聚类——将数据划分为k个簇，最小化簇内平方和。

**适用场景**: 客户分群；图像颜色量化；市场细分。

### `gmm_cluster(data, n_components=3, covariance_type='full', random_state=42)`

**用途**: 高斯混合模型软聚类——用EM算法估计多个高斯分量的参数，给出各样本属于各类的概率。

**适用场景**: 数据分布有重叠的聚类；概率聚类分析。

### `hierarchical_cluster(data, n_clusters=3, method='ward')`

**用途**: 凝聚式层次聚类——自底向上合并最近的簇形成层次树。

**适用场景**: 系统发育分析；层次化数据探索；无需预设簇数的初步分析。

### `knn_classify(X_train, y_train, X_test, k=5)`

**用途**: K-近邻分类——基于测试样本的k个最近邻居的多数投票进行分类。

**适用场景**: 模式识别；简单高效的分类基准模型。

### `decision_tree_classify(X_train, y_train, X_test, max_depth=None)`

**用途**: 决策树分类（CART，Gini不纯度），可输出特征重要性。

**适用场景**: 需要可解释性的分类问题；特征重要性评估。

### `naive_bayes_classify(X_train, y_train, X_test, var_smoothing=1e-9)`

**用途**: 高斯朴素贝叶斯分类——假设各特征在类别条件下独立且服从高斯分布。

**适用场景**: 文本分类；高维稀疏数据分类；快速基线模型。

### `bp_neural_network_regress(X_train, y_train, X_test, hidden_layers=(10,), ...)`

**用途**: BP神经网络回归（MLP），使用ReLU激活和Adam优化器。

**适用场景**: 复杂非线性回归；非结构化数据的预测建模。

### `linear_regression_fit(X_train, y_train, X_test)`

**用途**: 多元线性回归——拟合 `y = X·β + ε` 并预测。

**适用场景**: 线性关系建模；经济预测；基准回归模型。

### `polynomial_regression_fit(X_train, y_train, X_test, degree=2)`

**用途**: 多项式回归——构造多项式特征后进行线性回归。

**适用场景**: 非线性数据的曲线拟合；趋势面分析。

---

## 附录A: 依赖对照表

| 函数 | 额外依赖 |
|------|----------|
| 评价方法（AHP, TOPSIS, 熵权, 模糊, 灰色关联, RSR） | 无（仅numpy） |
| `dea_evaluate` | scipy |
| `logistic_fit` | scipy |
| `gaussian_process_regress` | scikit-learn |
| 线性/整数/0-1规划 | pulp |
| 非线性规划, 多目标 | scipy |
| 微分方程（SIR, 人口, 战争） | scipy |
| PCA, t-SNE | scikit-learn |
| 统计分布类 | 无（仅math） |
| K-means, GMM, 层次聚类 | scikit-learn, scipy |
| KNN, 决策树, 朴素贝叶斯 | scikit-learn |
| BP神经网络, 线性回归, 多项式回归 | scikit-learn |

## 附录B: 常见建模工作流

### 综合评价问题
```
数据预处理 → 熵权法确定权重 → TOPSIS/灰色关联计算得分 → 排序
或
专家打分 → AHP确定权重 → 模糊综合评价 → 等级评定
```

### 预测问题
```
数据探索 → 判断数据量:
  数据≤10个 → GM(1,1)灰色预测
  有季节性 → 季节指数预测
  有线性趋势 → 二次指数平滑
  有S型增长 → Logistic曲线拟合
  需不确定性 → 高斯过程回归
```

### 优化问题
```
线性约束 → 线性规划/整数规划
非线性约束 → 非线性规划求解器
多峰/全局优化 → 遗传算法/粒子群/模拟退火
多目标权衡 → 多目标规划（加权法）
```

### 分类/聚类问题
```
有标签 → KNN/决策树/朴素贝叶斯
无标签 → K-means/GMM/层次聚类
高维数据 → PCA降维后聚类 → t-SNE可视化
```
