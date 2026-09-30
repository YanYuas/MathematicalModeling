# 问题四项目结构

## 目录结构

```
问题4/
├── code/                           # (未创建，因代码较少直接放根目录)
├── figures/                        # 生成的图表
│   ├── Q4_optimal_layout.pdf      # 最优布局方案图
│   ├── Q4_area_comparison.pdf     # 面积对比图
│   └── Q4_module_properties.pdf   # 模块属性图
├── reports/                        # 报告
│   └── RESULTS_REPORT.md          # 计算结果报告
├── q4_solve.py                    # 暴力枚举版求解器（超时）
├── q4_solve2.py                   # 优化版求解器（主要使用）
├── visualize_q4.py                # 可视化脚本
└── verify_solution.py             # 验证脚本
```

## 核心文件说明

### 求解器

1. **q4_solve2.py** ⭐ 主要求解器
   - 优化算法：固定模块 + 剪枝 + 启发式初始化
   - 运行时间：< 5秒
   - 输出：最小包络面积、布局方案

2. **q4_solve.py**
   - 暴力枚举版（全排列 × 全朝向 × 全候选位置）
   - 运行时间：> 300秒（已超时）
   - 用于对照验证

### 可视化与验证

3. **visualize_q4.py**
   - 生成3张论文用图表（PDF矢量格式）
   - 中文标注，无标题（由论文caption提供）

4. **verify_solution.py**
   - 独立验证最优解的正确性
   - 检查：面积守恒、无重叠、包络计算、几何完整性
   - 结果：✓ PASS

### 报告

5. **reports/RESULTS_REPORT.md**
   - 完整的计算结果报告
   - 包含：算法说明、最优解、验证、图表说明、可复现步骤

## 关键结果

- **最小包络面积：30.0**（6×5矩形）
- **死区占比：20.0%**
- **唯一最优解：1个**
- **验证状态：✓ 通过**（无重叠、面积守恒、几何完整）

## 使用方法

### 运行求解

```bash
python q4_solve2.py
```

### 生成图表

```bash
python visualize_q4.py
```

### 验证结果

```bash
python verify_solution.py
```

## 依赖

- Python 3.x
- matplotlib（可视化）
- 标准库：itertools

## 交付物清单

✓ 求解代码（q4_solve2.py）  
✓ 可视化代码（visualize_q4.py）  
✓ 验证代码（verify_solution.py）  
✓ 结果报告（RESULTS_REPORT.md）  
✓ 论文用图表（3张PDF）  
✓ 项目说明（本文件）

---

**生成时间**：2026-08-09  
**状态**：✓ 完成
