# 问题2 数据可视化图表清单

**生成日期**: 2026-08-09  
**生成脚本**: generate_all_figures_v3_full.py  
**应用优化**: M1-M7 + C2

---

## 图表清单

### 核心分析图表（11张）

| 编号 | 文件名 | 描述 | 物理尺寸 (mm) | 文件大小 |
|------|--------|------|--------------|---------|
| **fig01** | `fig01_block_area_size_distribution` | 模块面积与形状分布（3×2矩阵，增强版） | 151.8 × 256.9 | PDF 86KB, PNG 1.86MB |
| **fig02** | `fig02_net_degree_distribution` | 线网度数分布（精致版） | 139.0 × 134.3 | PDF 30KB, PNG 0.37MB |
| **fig03** | `fig03_terminal_edge_distribution` | 终端边缘分布 | 152.7 × 69.3 | PDF 18KB, PNG 0.14MB |
| **fig04** | `fig04_dataset_dashboard` | 数据集仪表盘 | 154.5 × 123.2 | PDF 39KB, PNG 0.30MB |
| **fig05** | `fig05_hpwl_baseline_comparison` | HPWL基线对比与优化空间 | 120.9 × 76.9 | PDF 26KB, PNG 0.26MB |
| **fig06** | `fig06_aspect_ratio_distribution` | 宽高比分布 | 163.1 × 70.5 | PDF 29KB, PNG 0.21MB |
| **fig07** | `fig07_net_type_pie` | 线网类型饼图 | 174.8 × 62.1 | PDF 24KB, PNG 0.37MB |
| **fig08** | `fig08_hpwl_target_range` | HPWL优化目标区间 | 137.5 × 75.4 | PDF 27KB, PNG 0.22MB |
| **fig09** | `fig09_terminal_spatial_distribution` | 终端空间分布（散射图+轮廓框） | 170.6 × 81.4 | PDF 23KB, PNG 0.83MB |
| **fig10** | `fig10_area_cdf` | 面积累积分布函数（CDF） | 166.6 × 70.4 | PDF 28KB, PNG 0.24MB |
| **fig11** | `fig11_multi_dim_radar` | 多维特征雷达图 | 150.5 × 87.5 | PDF 41KB, PNG 0.46MB |

---

## 技术规格

### 输出格式
- **PDF**: 600 DPI, 矢量格式
- **PNG**: 600 DPI, 高清位图

### 尺寸标准
- **单栏宽度**: 85mm（部分图表适用）
- **双栏宽度**: 178mm（最大宽度）
- **验证结果**: ✅ 所有图表符合投稿规范（≤180mm）

### 配色方案（M6优化）
- **n100**: #1A4D7A（深蓝）
- **n200**: #2D7A6E（墨绿）
- **n300**: #E86428（暖橙）
- **网格透明度**: 0.15（C2优化）

---

## 应用的优化修改

| 编号 | 修改项 | 原值 | 新值 | 影响范围 |
|------|--------|------|------|---------|
| **M1** | figsize减半 | 各图不同 | 减半 | 所有11张图 |
| **M2** | font.size | 10 | 18 | 全局 |
| **M3** | savefig.dpi | 300 | 600 | 全局 |
| **M4** | 编号重命名 | main01 | fig15 | （本脚本不含3D图）|
| **M5** | HPWL单位 | 'HPWL' | 'HPWL (μm)' | fig05, fig08 |
| **M6** | 配色微调 | 原配色 | 增强对比度 | 全局 |
| **M7** | 极端值色 | 红色 | 橙色 | fig01 |
| **C2** | grid.alpha | 0.25 | 0.15 | 全局 |

---

## 生成统计

- **总图表数**: 11张
- **总文件数**: 22个（每张图PDF+PNG各1）
- **总存储**: 5.64 MB
- **生成耗时**: 7.5秒
- **验证通过率**: 100%（11/11）

---

## 使用说明

### 论文插图
- 推荐使用 **PDF格式**（矢量，支持无损缩放）
- 单栏图：fig05, fig08, fig11
- 双栏图：fig01, fig02, fig04, fig09

### 演示文稿
- 推荐使用 **PNG格式**（600 DPI高清）
- 直接插入PPT/Keynote，无需额外处理

### 重新生成
```bash
cd 问题2
python generate_all_figures_v3_full.py
```

---

**生成工具**: Python 3.x + Matplotlib + SciPy  
**质量保证**: 符合Nature/Science投稿规范  
**版本**: v3.0 完整优化版
