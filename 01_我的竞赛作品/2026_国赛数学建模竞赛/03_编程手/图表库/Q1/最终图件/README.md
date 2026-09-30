# Q1 图表库 v3.0

## 图表契约

- **核心结论**：多站角域交会能把含测向误差的定位问题化为凸定位区域，并可用直径、最小包围圆和 Jung 界给出可核验的覆盖结论。
- **图形结构**：几何示意图采用“建立机制 → 反例/界 → 定位构造”的叙事；参数图与统计图用于验证理论式和稳健性。
- **唯一绘图后端**：Python / matplotlib。
- **数据来源**：`source/q1_scan_results.json` 的真实扫描结果；几何图由 `source/q1_main.py` 实时计算。单站楔形图为明确标注参数的理论示意。
- **版式**：白底、外置图注、Ink & Ochre 调色板；所有图导出 600 dpi PNG、SVG 与 PDF。

## 使用

```powershell
python q1_figures_v3.py
python q1_figures_v3.py --paper-only
```

完整运行会生成 12 张图。`--paper-only` 只生成正文引用的图 5.1-1 至 5.1-5。生成后 `图表清单_v3.json` 记录每张图的像素尺寸、导出完整性和输入数据 SHA-256。

## 正文图号映射

| 论文图号 | v3 资产 |
|---|---|
| 图 5.1-1 | `02_几何示意/fig5_1_1_single_station_wedge.png` |
| 图 5.1-2 | `02_几何示意/fig5_1_10_geometry_construction.png` |
| 图 5.1-3 | `02_几何示意/fig5_1_3_jung_counterexample.png` |
| 图 5.1-4 | `02_几何示意/fig5_1_4_jung_sandwich.png` |
| 图 5.1-5 | `02_几何示意/fig5_1_5_vertex_filtering.png` |
| 图 5.1-9 | `02_几何示意/fig5_1_9_algorithm_flowchart.png` |

历史版本保留在上级图库，v3 不覆盖它们。
