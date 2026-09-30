# Q1 图表库环境配置指南

> **适用对象**：建模手、论文手、审核人员  
> **前置条件**：已安装 Python 3.10+  
> **版本**：v1.4.0 | 更新：2026-09-11

---

## 一、快速开始（3步）

### 1. 安装依赖

```bash
cd HelloMathModeling/03_编程手/图表库/Q1/01_生图代码
pip install -r requirements.txt
```

**预计耗时**：1-2分钟（取决于网络）

### 2. 生成所有图表

```bash
python generate_all.py
```

**预计耗时**：30-60秒（12张图表）

### 3. 验证输出

检查以下目录是否有图片生成（每张图都有PNG+SVG两个文件）：

```

├── 02_几何示意/           ← 8张图（5.1-1, 5.1-2, 5.1-3, 5.1-4, 5.1-5, 5.1-10）
├── 03_参数扫描/           ← 5张图（5.1-6, 5.1-8, 5.1-11, 5.1-12, 5.1-13）
├── 04_统计分布/           ← 1张图（5.1-7）
└── 05_算法流程/           ← 手绘图，不由代码生成
```

---

## 二、单独生成某张图

如果只需要重新生成某一张图（例如修改配色后），可以：

**方式1：Python交互**

```bash
cd 01_生图代码
python
```

```python
from q1_figures_beautified import fig_5_1_1_baseline
fig_5_1_1_baseline()  # 只生成图5.1-1
```

**方式2：修改 generate_all.py**

注释掉不需要生成的图，只保留需要的。

---

## 三、故障排除

### ❌ 问题1：`ModuleNotFoundError: No module named 'q1_main'`

**原因**：`q1_figures_beautified.py` 依赖 `q1_main.py`（Q1核心算法）

**解决**：
- 确保在 `01_生图代码/` 目录下运行
- 检查该目录是否包含 `q1_main.py`（约31KB）

### ❌ 问题2：`FileNotFoundError: q1_scan_results.json`

**原因**：扫描数据文件缺失

**解决**：
- 检查 `01_生图代码/q1_scan_results.json` 是否存在
- 文件大小应为 **409KB**（包含15+5+7+54组数据+8000蒙特卡洛样本）
- 如缺失，从备份恢复或联系编程手

### ❌ 问题3：中文显示为方块 □□□

**原因**：系统缺少微软雅黑字体

**解决**：
- **Windows**：应自动包含，无需操作
- **macOS**：安装 `Microsoft YaHei` 字体
- **Linux**：`sudo apt-get install fonts-wqy-microhei`
- **临时方案**：修改 `q1_figures_beautified.py` 第55行，将 `'Microsoft YaHei'` 改为 `'SimHei'` 或其他中文字体

### ❌ 问题4：`ImportError: cannot import name 'fig_5_1_1_baseline'`

**原因**：`q1_figures_beautified.py` 版本过旧

**解决**：
- 确保使用的是 v1.3+ 版本（文件大小约89KB）
- 检查文件头部是否包含 `# Q1 图表统一美化版 v2.0`

### ❌ 问题5：生成的图片为空白或不完整

**原因**：`matplotlib` 后端问题

**解决**：
- 在 `q1_figures_beautified.py` 顶部添加：
  ```python
  import matplotlib
  matplotlib.use('Agg')  # 使用非交互式后端
  ```

---

## 四、技术说明

### 数据来源（可追溯性）

| 数据源 | 文件 | 状态 | 备注 |
|--------|------|------|------|
| 参数扫描数据 | `q1_scan_results.json` | ✅ 已验证 | 418KB，联合校验通过 |
| 核心算法 | `q1_main.py` | ✅ 已验证 | 三侧审计通过，D一致到8位小数 |
| 权威数值 | `00_任务总控/权威数字表.md` | ✅ 已对齐 | §三 Q1结果 |

**数据完整性保证**：所有图表数值来自真实扫描，无编造。

### 设计规范（Ink & Ochre v2.0）

| 规格 | 数值 | 说明 |
|------|------|------|
| 分辨率 | 300 DPI | 论文印刷标准 |
| 输出格式 | PNG + SVG | 位图+矢量双格式 |
| 配色主调 | ink (#1A1A1A) | 主文字、轴线 |
| 画布底色 | paper (#FAF7F0) | 暖白色 |
| 强调色 | ochre (#C47B2B) | 直径D、关键发现 |
| 中文字体 | Microsoft YaHei | 或 SimHei 备用 |
| 英文字体 | Arial | 无衬线 |
| 线宽 | main=2.4, theory=1.6, aux=0.8 | 三级层级 |

### 版本管理

- **当前版本**：v1.4.0（路径规范化）
- **图片命名规则**：`图5.1-X_中文名称_v版本号.png/svg`
- **变更记录**：见 `../CHANGELOG.md`
- **版本升级流程**：
  1. 修改 `q1_figures_beautified.py`
  2. 运行 `generate_all.py`
  3. 旧版图片移入 `99_旧版存档/`
  4. 更新 `CHANGELOG.md`

---

## 五、给论文手的快速参考

### Word文档插入图片

```
插入 → 图片 → 浏览 → 
HelloMathModeling/03_编程手/图表库/Q1/02_几何示意/图5.1-1_基准算例_v1.3.png
```

**建议**：使用SVG格式获得更好的打印质量（Word 2016+支持）

### LaTeX引用

```latex
\usepackage{graphicx}

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.8\textwidth]{figures/fig5_1_1_baseline_v1_3.png}
  \caption{Q1基准算例：定位区域、直径与最小包围圆}
  \label{fig:q1_baseline}
\end{figure}
```

### 图号快速查找

详见 `../图号映射表.md`（如已创建）

---

## 六、开发者参考

### 修改配色

编辑 `q1_figures_beautified.py` 第36-47行 `PALETTE` 字典：

```python
PALETTE = {
    "ink":      "#1A1A1A",   # 主文字
    "ochre":    "#C47B2B",   # 强调色 ← 修改这里
    # ...
}
```

### 修改分辨率

编辑第50行：

```python
DPI = 300  # 改为 600 可获得更高分辨率
```

### 添加新图表

1. 在 `q1_figures_beautified.py` 中添加新函数 `fig_5_1_X_newname()`
2. 在 `generate_all.py` 的 `FIGURE_LIST` 中添加条目
3. 按版本管理流程更新文档

---

## 七、常见问题（FAQ）

**Q1：可以在Windows/macOS/Linux上运行吗？**  
A：可以。Python和依赖库都是跨平台的。

**Q2：生成图片需要多长时间？**  
A：单张约2-5秒，全部12张约30-60秒（取决于机器性能）。

**Q3：可以批量修改所有图片的配色吗？**  
A：可以。修改 `PALETTE` 后重新运行 `generate_all.py` 即可。

**Q4：SVG格式有什么优势？**  
A：矢量格式，无损缩放，适合印刷和演示。Word 2016+、LaTeX均支持。

**Q5：如何验证生成的图片是正确的？**  
A：检查关键数值（如D=39.598 m）是否与 `权威数字表.md` §三一致。

**Q6：可以修改图表生成逻辑吗？**  
A：可以，但注意：
- 不要修改核心数据（`q1_scan_results.json`）
- 修改后需重新验证数值一致性
- 在 `CHANGELOG.md` 中记录变更

---

## 八、相关文档索引

| 文档 | 路径 | 用途 |
|------|------|------|
| 权威数字表 | `00_任务总控/权威数字表.md` §三 | Q1数值验证依据 |
| 联合校验报告 | `02_建模手/Q1/建模手-联合校验报告.md` | 算法验证 |
| 总索引 | `../00_总索引.md` | 图表库完整说明 |
| 变更记录 | `../CHANGELOG.md` | 版本历史 |
| 编程清单 | `../../../编程手_Q1清单.md` | 实施规范 |

---

**维护者**：编程手  
**最后更新**：2026-09-11  
**下次审核**：图表库升级到 v2.0 时
