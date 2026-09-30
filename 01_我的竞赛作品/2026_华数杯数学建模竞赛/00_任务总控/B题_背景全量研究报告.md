# B题 VLSI布图规划设计 — 背景全量研究报告

> 研究日期：2026-08-07 | 模式：deep-research Verbose | 本地实证 + 6路并行Web研究 + 参考论文全文精读
> 用途：建模思路 / 编程指导 / 论文素材

---

## 执行摘要

B题本质是**学术经典的 VLSI 布图规划（floorplanning）问题**，赛题数据经逐字段验证**就是 GSRC 标准基准集 n100/n200/n300 的原始数据**（模块数/线网数/总面积/终端坐标全部吻合），参考文献[2]（Chen & Chang, IEEE TCAD 2006）即本问题的权威解法：**B*-Tree 表示 + 快速模拟退火（Fast-SA）**。这意味着：(1) 求解路线已被论文给出，风险低；(2) 论文中的实验数字（成功率、线长、死区）可直接作为**对标真值**；(3) 必须诚实引用参考文献，不得包装成"原创发现"。

四问难度递进：Q1 纯面积最小化（无轮廓无线网，最简单）→ Q2 固定轮廓+HPWL（核心，需自适应权重）→ Q3 死区比例下界（在 Q2 模型上做可行性二分搜索）→ Q4 L/T 非矩形模块（B*-Tree 需子块分解+邻接扩展，最复杂）。

最大的两个坑：(1) **固定轮廓可行性随死区比例坍缩**——死区 <5-8% 时可行布局可能不存在，这是 Q3 的答案边界；B*-Tree 在固定轮廓下成功率远高于序列对（100% vs 50-71% @10%空白），选型正确。(2) **SA 随机性**——需固定种子+多次运行取最优，否则交卷结果不可复现。

**总体置信度：高**（数据识别、算法路线、对标数值均有强证据）。主要缺口：GSRC 的 mm² 绝对线长数值在论文 PDF 中为图片，需人工读表。

---

## 一、题设、条件与约束形式化

### 1.1 问题结构

| 问 | 目标 | 约束 | 复杂度 |
|---|---|---|---|
| Q1 | 芯片轮廓面积最小；面积相同时长宽比→1 | 模块不重叠、不超轮廓；轮廓不固定 | 低 |
| Q2 | 总 HPWL 最小 | 固定正方形轮廓（死区15%）、不重叠、不超界、90°旋转 | 中 |
| Q3 | 死区比例最小值（存在可行布局） | Q2 模型 + 死区比例可变 | 中（二分套 Q2） |
| Q4 | 4 个 L/T 型模块包络面积最小 | 模块可旋转 90/180/270° | 高（表示法扩展） |

### 1.2 数据 = GSRC 基准（已逐字段验证）

| | n100 | n200 | n300 |
|---|---|---|---|
| 硬模块 | 100 | 200 | 300 |
| Terminal | 334 | 564 | 569 |
| 线网数 | **885** | **1585** | **1893** |
| 引脚数 | 1873 | 3599 | 4358 |
| 模块总面积 | **179501** | **175696** | **273170** |
| Q2轮廓边长(15%) | 454.3 | 449.5 | 560.5 |
| 终端坐标范围 | 0–444 | 0–438 | 0–548 |

与 GSRC 权威统计（BICA 2023 论文集 Table 2 独立复核）逐值吻合。参考论文 Table V 报告 GSRC n100/n200/n300 = **885/1585/1893 nets**，完全一致。

**关键口径细节**：
1. **GSRC 原始 .pl 按 10% 死区生成**（终端最大坐标 444 = √(179501×1.10)），赛题 Q2 用 **15%**——芯片略大，所有终端仍在界内。对标论文时注意此口径差。
2. 文件为标准 bookshelf 格式：`.blocks`（NumHardBlocks/NumTerminals + 4角点矩形 + `terminal` 行）、`.nets`（NetDegree 分组）、`.pl`（终端坐标）。
3. 模块全为矩形（"block 4"），无软模块、无 L/T——L/T 是 Q4 新引入。
4. 引脚在模块几何中心（题设简化）→ HPWL 是模块中心坐标的函数。
5. **线网结构**：2 引脚网占绝对多数（n100 中 787/885=89%，n200 75%，n300 72%）→ HPWL 近似曼哈顿距离加权和，计算可简化；全部模块都进线网；最大连接度 ~35。
6. Terminal 只参与 HPWL，不占面积、不参与重叠约束。

### 1.3 约束清单

- **不重叠**：任意两模块矩形内部不相交（可相邻、可留空隙）
- **不超轮廓**：模块完全落在 [0, W*]×[0, H*] 内
- **90°旋转**：硬模块可旋转（旋转后仍合法）
- **HPWL 定义**：线网外接轴对齐矩形半周长 = (max_x−min_x)+(max_y−min_y)；2引脚网 = 曼哈顿距离
- **死区比例**：死区 = (轮廓面积 − Σ模块面积)/轮廓面积；轮廓边长 W*=H*=√(总面积×(1+死区比例))
- **Q2/Q3 正方形轮廓**：W*=H*

---

## 二、行业理论与标准（建模思路）

### 2.1 问题复杂度

矩形布图规划是 **NP-hard**（Hakimi 1988 由划分问题归约证明）；但**给定表示（B*-Tree/SP 等）后 packing 是 O(n) 摊还多项式可解**——NP-hard 在于搜索最优表示。因此行业/学界一律用启发式（模拟退火/遗传/解析法），精确算法只能处理 <50 模块小实例（MCNC 5 个中 3 个可证最优）。**对 100-300 模块，模拟退火是标准答案。**

### 2.2 B*-Tree 表示法（参考文献[2]核心，已从全文精读）

- **结构**：有序二叉树。根=左下角模块。左孩子=右侧相邻的最低未访问模块（x 坐标 = 父的 x+w）；右孩子=正上方同 x 坐标模块。
- **一一对应**：合法"admissible placement"（无模块能再左移或下移）与 B*-Tree 一一对应 → 无冗余表示。
- **解码**：x 坐标一次前序遍历确定（O(n)）；y 坐标用**轮廓（contour/skyline）数据结构**均摊常数时间 → 每次扰动评估 **O(n)**。
- **解空间** O(n!·2^(2n)/n^1.5)，远小于 Sequence Pair 的 (n!)²。
- **相对 O-tree**：快 ~4.5 倍、内存省 ~60%（MCNC 实测）。

### 2.3 Fast-SA 三阶段退火（参考文献[2]）

区别于经典 SA（固定 λ≈0.85）与 TimberWolf（λ 在 0.8–0.95 间升降）：

1. **高温随机搜索**：接受概率→1，防初陷局部最优
2. **伪贪心局部搜索**（k 次迭代，c=100）：温度→0，几乎只接受改进
3. **爬山搜索**：温度回升跳出局部极小，再缓降收敛

温度更新：`T1 = Δ_avg / ln P`（P=初始接受概率≈0.9）；`Tn = T1·⟨Δcost⟩/(n·c)`（2≤n≤k）；`Tn = T1·⟨Δcost⟩/n`（n>k）。**Δ_avg/⟨Δcost⟩ 是 SA 前试扰动 n 次算出的平均代价变化**——成本归一化后 ⟨Δcost⟩<1 保证降温。

效果：相对经典 SA 在 GSRC 上 **12×（n100，k=7）至 13.9×（ami49）加速**，同质量死区更低（ami49：Fast-SA 2.00% vs 经典 2.62% vs 贪心 5.76%）。

### 2.4 扰动算子

**Op1 旋转**（O(1)，不变树结构）；**Op2 移动=删除+插入**（O(n)，变拓扑）；**Op3 交换两节点**；**Op4 软模块缩放**（Q4 才用）。删除三情形：叶子 O(1)/单孩子 O(1)/双孩子 O(h)。插入随机选父节点插左/右。

### 2.5 成本函数与固定轮廓（Q2 成败核心）

- 面积+线长：`Cost = α·A/Anorm + (1−α)·W/Wnorm`（除以均值归一化）
- **固定轮廓加纵横比惩罚**：`Φ(F) = αA + βW + (1−α−β)(R−R*)²`，轮廓 `H*=√((1+Γ)A·R*)`, `W*=√((1+Γ)A/R*)`
- **自适应 α（论文100%成功率的机制，非"spreading"）**：`α = αbase + (1−αbase)·n_feasible/n`，αbase=0.5，n=最近500个解。可行解越多→纵横比惩罚权重越小→搜索集中于线长/面积。
- **不可旋转块预标定**：只能单一朝向放进轮廓的块，SA 前锁定朝向（死区 15% 下意义大）。
- **记录**：SA 全程记录最优解（min WL 或 min area），不是末态。

### 2.6 表示法全景与选型论证

| 表示法 | 解空间 | 解码 | 冗余 | 固定轮廓 | 非矩形 |
|---|---|---|---|---|---|
| Sequence Pair | (n!)² | O(n²)/O(nlogn) | 大 | 需slack moves | 可扩展 |
| **B*-Tree** | O(n!·2^(2n)/n^1.5) | **O(n)** | 无(admissible一一对应) | 自适应α**成功率100%** | 可扩展(见Q4) |
| O-tree | 同B*-Tree量级 | O(n) | 有 | 不直接 | 可 |
| Corner Sequence | 未给显式 | O(n) | 声称P-admissible | — | — |

**选型结论**：B*-Tree 解空间最小、线性解码、无冗余、固定轮廓下实测成功率远超序列对。ISPD'05 关键反直觉结论：**表示法差异对最终质量影响小，SA 调度/代价函数才是瓶颈**——不要在换表示法上耗时间。

### 2.7 固定轮廓可行性实证（Q3 答案边界）

- Adya & Markov 2003（固定轮廓奠基文）：成功率和线长强依赖**相对空白量**与**目标宽高比**；偏差显著恶化。
- 量化阈值（GSRC n100/n200/n300）：
  - **15%/10% 空白**：B*-Tree+自适应 α = **100% 成功率**
  - **8% 空白**：LFF 法近 100%（AR=1-4）
  - **6% 空白**：成功率骤降（n100 在 AR=1-4 下仅 54/24/46/30%）
  - **<5% 空白**：仅 PolarBear 等专门工具稳定出解；Parquet/B*-Tree/TCG-S 利用率差可达 2 倍
  - **1% 死区**：电压岛专用算法靠惩罚函数才 94%
- **含义：Q3 的"最小死区比例"大概率落在 5-10% 区间**，需用二分逼近 + 多次运行确认可行性。

### 2.8 各问建模落地方案

- **Q1**：面积-only SA，`Cost = A/Anorm + λ(R−1)²`（λ 小，纵横比作平局指标）。无轮廓约束，跑完直接得最小面积+长宽比。
- **Q2**：固定轮廓 15%，自适应 α + HPWL，预标定不可旋转块。对标参考论文 Table IV/V（成功率、线长减 6%）。
- **Q3**：Q2 模型套**死区比例二分搜索**（如 [0.05, 0.15]），每次二分点跑 Q2 的 SA 判断是否存在可行布局（多次运行取多数），收敛到最小 Γ。
- **Q4**：L 型拆 2 矩形、T 型拆 3 矩形，加**子块邻接（abutment）约束**；Wu/Chang/Chang 已证明 B*-Tree 对 rectilinear 块需**可行性条件**——存在无法从给定树生成可行布局的情形，须缩解空间；或采用 CBL（Corner Block List）扩展。L/T 块的 B*-Tree 子树排列严格受限（T 型三子块仅 8 个可行序列对而非 36）。

---

## 三、行业壁垒与方法（编程指导）

### 3.1 行业流程定位

物理设计流程：RTL → 综合 → **布图规划(floorplanning) → 布局(placement) → CTS → 布线(routing)** → signoff。布图规划是物理设计**第一步**，定 die/core 边界、宏位置、I/O、电源骨架。商用：Synopsys ICC2（含 ML 宏放置）、Cadence Innovus。开源：**OpenROAD**（IFP 模块，`initialize_floorplan`；2025 GSoC 已支持 L/T/U 异形布图——直接呼应 Q4）。

### 3.2 whitespace/congestion 管理（死区含义）

- 死区比例惯例 **10-15%**（给布线、缓冲、电源留空间）；OpenROAD 利用率典型 30-80%。
- 业界用拥塞图驱动 whitespace 重分配，把空白优先划给高拥塞区。
- 论文写作素材：死区比例 = 1 − 利用率；现代文献多称"空白面积率 (white space ratio)"，首次出现括注"又称死区 (dead space)"。

### 3.3 可参考开源实现（与赛题格式对口）

- **choltz95/lipo-b--annealing**：B*-Tree 退火 + HPWL 驱动 MILP 详细放置，读 .block/.nets，Python 接口
- **yeshenpy/CORE**：C++ + pybind11，B*-Tree 表示、轮廓打包、HPWL/越界惩罚评估，读 .block/.nets——与赛题格式完全对口
- NTU 官方：http://eda.ee.ntu.edu.tw/research.htm（B*-Tree 论文作者维护）

### 3.4 编程要点清单

1. **轮廓数据结构**：packing 时维护 y 坐标分段轮廓，均摊 O(n)，不要用 O(n²) 两两比较
2. **增量评估**：交换后只重算受影响的子树/模块，别全量重打包
3. **成本归一化**：A/Anorm、W/Wnorm，否则 SA 温度公式失效（⟨Δcost⟩ 必须 <1）
4. **2引脚网主导**：HPWL = |Δx|+|Δy| 直接算，无需包围盒；多引脚网才开包围盒
5. **固定种子 + 多次运行取最优**：SA 随机性大（Cornell 实测 100 次中仅 70% 胜过随机重启爬山），交卷必须 best-of-N + 报告均值/标准差
6. **不可旋转块预标定**：死区 15% 下先算每个模块旋转后是否超界，锁定朝向
7. **自适应 α**：维护最近 n=500 解中可行解计数，动态调 α
8. **Terminal 处理**：固定坐标，不参与 packing，只进 HPWL；每网外接矩形算入终端坐标
9. **NP-hard 现实**：不追求全局最优，SA 收敛到可接受解即可，对标参考论文数字而非理论下界

### 3.5 HPWL 失真风险（Q2 结果解读）

HPWL 是真实布线长度（RSMT Steiner 线长）的**下界**：仅 2/3 引脚网取等；高扇出网低估严重（实测 StWL/HPWL 可达 ~1.27，如 ami33；≤3 引脚网几乎为 1.00）。存在"同 HPWL 差 53.5% 真实线长"的反例。赛题数据 2 引脚网占 72-89% → **失真小，HPWL 作目标函数是安全的**，论文可据此论证。

---

## 四、行业术语与论文素材

### 4.1 中英术语对照表

| 中文 | 英文 |
|---|---|
| 布图规划 | Floorplanning |
| 布局 | Placement |
| 物理设计 | Physical Design |
| 线网 | Net |
| 引脚/终端 | Pin / Terminal |
| 半周长线长 | HPWL (Half-Perimeter Wirelength) |
| 死区/空白面积 | Dead Space / White Space |
| 面积利用率 | Area Utilization |
| 固定轮廓/固定外框 | Fixed-Outline (Fixed-Die, FOF) |
| 硬模块/软模块 | Hard Block / Soft Block |
| 模拟退火 | Simulated Annealing |
| 退火调度/冷却进度表 | Annealing / Cooling Schedule |
| 冷却因子 | Cooling Factor λ |
| 扰动/扰动算子 | Perturbation / Move |
| 接受准则 | Metropolis Criterion |
| 序列对 | Sequence Pair |
| 轮廓结构 | Contour / Skyline |
| 布局合法化 | Legalization |
| 详细布局 | Detailed Placement |
| 直线型斯坦纳最小树 | RSMT (Rectilinear Steiner Minimum Tree) |

### 4.2 参考文献条目（GB/T 7714 现成）

1. 黄志鹏, 李兴权, 朱文兴. 超大规模集成电路布局的优化模型与算法[J]. 运筹学学报, 2021, 25(3): 15-36. DOI: 10.15960/j.cnki.issn.1007-6093.2021.03.002.
2. Chen T-C, Chang Y-W. Modern floorplanning based on B*-tree and fast simulated annealing[J]. IEEE TCAD, 2006, 25(4): 637-650.
3. Chang Y-C, Chang Y-W, Wu G-M, Wu S-W. B*-trees: A new representation for non-slicing floorplans[C]. DAC, 2000: 458-463.
4. Adya S N, Markov I L. Fixed-outline floorplanning: Enabling hierarchical design[J]. IEEE TVLSI, 2003, 11(6): 1120-1135.
5. Murata H, Fujiyoshi K, Nakatake S, Kajitani Y. Rectangle-packing-based module placement[C]. ICCAD, 1995: 472-479.
6. Wu G-M, Chang Y-C, Chang Y-W. Rectilinear block placement using B*-trees[J]. ACM TODAES, 2003, 8(2): 188-202.
7. Cheng C-K, Kahng A B, et al. An updated assessment of reinforcement learning for macro placement[J]. IEEE TCAD, 2023.
8. Mirhoseini A, Goldie A, et al. A graph placement methodology for fast chip design[J]. Nature, 2021, 594: 207-212.

### 4.3 论文结构惯例（华数杯 B 题）

标准结构：摘要（建模思想+算法+全部结果，最关键）→ 问题重述 → 问题分析（思路流程图）→ 模型假设+符号说明（不用程序变量写法如 a[0]）→ 模型建立与求解（算法原理+步骤+框图，数值结果第一）→ 模型检验与结果分析（表格化图形化）→ 模型评价与推广（含灵敏度分析）→ 参考文献+附录代码。正文 ≤20 页。

**2024 华数杯 B 题"VLSI电路单元自动布局"特等奖论文可对标**（CM2402789，约 28 页）：SA+粒子群互验、遗传算法、NSGA-II 双目标是获奖路径；HPWL 相对 RSMT 达 93.4%。

### 4.4 引言/背景素材

- "布图规划是 VLSI 物理设计的核心环节，属 NP 困难的多目标组合优化问题；现代布局通常分解为总体布局、合法化、详细布局三阶段。"（黄志鹏 2021）
- 近年趋势：机器学习/强化学习芯片布局（Google Circuit Training/AlphaChip）**争议极大**——UCSD 复现失败（ISPD 2023/TCAD 2023），CACM 质疑其诚信（Markov 2024），截至 2026 无同行评审的正面独立复现；Synopsys 高层公开表态 RL 未在核心 EDA 算法上奏效。**引用时表述为"claim + 争议双方观点"，年份注意：Nature 2021 发表，2024 年才命名 AlphaChip。**

---

## 五、反面论证（Devil's Advocate）与风险

**对主方案的质疑与回应：**

1. **"SA 对数十模块以上不实用"**（Ranjan 2001）：经典引用。但对 100-300 模块 GSRC，单次 SA 分钟级完成，批评弱。真正的风险不是慢，而是固定轮廓可行性（见 2.7）。
2. **B*-Tree 只覆盖 LB-compact 布局**：可能漏掉非压缩但线长更优的布局。ISPD'05 实测表示法差异对质量影响小，此风险有限。
3. **HPWL 低估真实线长**：多引脚网低估 3-27%。赛题 2 引脚网占 72-89%，失真小；论文中说明此边界即可。
4. **SA 随机性不可复现**：竞赛评分风险。对策=固定种子+best-of-N+报告统计量。
5. **Q4 L/T 模块破坏标准 B*-Tree**：直接拿矩形算子会产生大量非法/次优解。必须显式加子块邻接+可行性条件，或换 CBL/分解法。
6. **数据即 GSRC = 双刃剑**：优点是对标方便；缺点是评委会按参考论文数字检查——若结果明显差于论文基线会被扣分。必须把算法调到接近/超过 Table IV/V 水平。

---

## 六、证据台账与置信度

| 结论 | 状态 | 来源 | 置信度 |
|---|---|---|---|
| 赛题数据=GSRC基准 | confirmed | 本地计算 + BICA 2023 Table 2 独立复核 + 参考论文 Table V | 高 |
| B*-Tree 机制/成本函数/自适应α | confirmed | 参考论文全文精读（本地） | 高 |
| 固定轮廓成功率阈值(5-8%坍缩) | confirmed | Adya&Markov 2003, ISPD 2007, ISCAS 2006 多源一致 | 高 |
| SP固定轮廓成功率低(50-71%@10%) | confirmed | ISPD 2007 + B*-Tree 论文对比表 | 中高 |
| HPWL 低估(3-27%, 引脚数相关) | confirmed | Roy/Lu/Markov 2008 + UPC讲义 + ISEDA 2024 | 中高 |
| Fast-SA 12-13.9×加速 | confirmed | 参考论文全文 | 高 |
| AlphaChip 争议 | contested | Nature 2021 + Cheng&Kahng 2023 + Markov 2024 + Google反驳 | 中（未决） |
| MCNC HPWL 绝对值 | weak | 各论文口径混乱 | 低 |
| GSRC mm² 绝对线长 | 缺口 | 论文 PDF 中为图片 | 需人工读表 |

---

## 七、行动清单（下一步）

1. [ ] 搭建代码骨架：B*-Tree 构造/解码 + 轮廓数据结构 + 三扰动算子 + SA 框架
2. [ ] 用本地数据验证：Q1 面积最小化 → 检查是否达到论文死区水平（~2-5%）
3. [ ] 实现自适应 α + 固定轮廓 → Q2，对标 Table IV/V（成功率100%、线长≤323k）
4. [ ] Q3 二分搜索最小死区比例
5. [ ] Q4 L/T 分解 + 邻接约束扩展
6. [ ] 手动读参考论文 PDF 表格，记录 GSRC n100/n200/n300 的 mm² 线长真值（需打开 PDF 第 10-11 页）
7. [ ] 可视化：三组芯片布图 + 面积/长宽比/HPWL 表

---

## 附录 A — 主要来源

- 参考论文（赛题参考文献[2]）：https://cc.ee.ntu.edu.tw/~ywchang/Papers/tcad06-mfloorplanning.pdf
- B*-Trees 原论文 (DAC 2000)：https://dl.acm.org/doi/10.1145/337292.337573
- Adya & Markov 固定轮廓 (TVLSI 2003)：https://dl.acm.org/doi/abs/10.1109/TVLSI.2003.817546
- Corner Sequence (TVLSI 2003)：DOI 10.1109/TVLSI.2003.816137
- 黄志鹏等综述 (运筹学学报 2021)：https://www.ort.shu.edu.cn/CN/abstract/abstract18467.shtml
- 开源 B*-Tree 实现：https://github.com/choltz95/lipo-b--annealing 、https://deepwiki.com/yeshenpy/CORE
- OpenROAD：https://github.com/The-OpenROAD-Project/OpenROAD
- AlphaChip 争议：https://en.wikipedia.org/wiki/AlphaChip_(controversy) 、arXiv 2411.10053
- RL 再评估 (TCAD 2023)：arXiv 2302.11014
- ICCAD 2022/2023 竞赛：https://www.iccad-contest.org/
- 吉大学报 2025 中文综述：https://xuebao.jlu.edu.cn/lxb/CN/abstract/abstract5073.shtml
