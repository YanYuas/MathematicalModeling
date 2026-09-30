# Q1 主图｜中转站 AI 生图提示词（无文字构图草案）

## 使用方式

- 比例：16:13.5（推荐自定义 1600×1350；若不支持，选接近 6:5 的竖向画幅）。
- 一次生成 4 张变体；选构图最接近坐标表的一张。
- 关闭自动文字、标题、logo 和水印。
- 成图只作视觉参考，论文终稿由 Python 按数学数据重绘。

## 可直接粘贴的主提示词（建议英文）

```text
Create a publication-grade, vector-like scientific diagram composition for a mathematical modeling paper. Canvas aspect ratio 16:13.5, white background, clean flat vector lines, no text whatsoever.

This is an ASYMMETRIC “forked proof bridge”, not a grid, not a dashboard, not a slide, not a three-column infographic.

Use normalized canvas coordinates where x=0 is left, x=100 is right, y=0 is top, y=100 is bottom:
1) Header strip: x=3–97, y=3–7. An extremely thin quiet horizontal conclusion strip; leave it almost empty, no words.
2) Input construction chain: x=4–96, y=11–30. A very wide but shallow band. Arrange three minimal abstract angle-wedge constructions on the left, then a small intersection symbol-like visual transition, then a deep-blue convex polygon, then a vertical diameter segment and a faint dashed candidate circle at the right end. Use thin pale-gray connectors; this is one continuous chain, not separate cards.
3) Large counterexample region: x=3–56.5, y=33–70.5. This must be the largest single visual region. Center a rust-red equilateral triangle. Its lower side is a diameter chord of a small gray dashed circle; the triangle’s upper vertex clearly lies outside this smaller circle. Overlay a larger desaturated-teal enclosing circle that contains all three vertices. Between the two circles, use a restrained pale-rust hatched annular gap. Make the triangle and its three small angle arcs the visual focus.
4) Criterion region: x=60.5–97, y=33–70.5. It aligns horizontally with the large counterexample but is visibly smaller. Draw a deep-blue irregular convex quadrilateral. Draw one vertical-ish diameter between two opposite vertices. From the other two vertices, draw very thin chords to both diameter endpoints and show two subtle rust-red angle arcs. Use only geometry, no labels.
5) Two distinct evidence paths: from the bottom of region 3 and region 4, use two thin pale-gray paths descending toward the lower band. They must meet in a T-shaped junction centered near x=55, y=77. Do not make a Y junction. The left path may be subtly dashed; the right path solid.
6) Universal synthesis band: x=4–96, y=76–89. A broad horizontal band. Draw a single restrained normalized interval visual: a dark-blue vertical anchor near x=27; a long pale-teal hatched interval extending to x=79; and a teal dashed upper-bound marker near x=79. It must feel like a single scientific metric band, no conventional plot axes and no tick labels.
7) Tiny verification pocket: x=62–96, y=92–99. A very small low-contrast pale-gray rounded rectangular pocket, intentionally quiet and subordinate, with only a miniature blue quadrilateral-and-circle motif; do not put text inside.

Visual hierarchy: large rust counterexample first; deep-blue criterion second; teal universal synthesis third; muted verification pocket last. Generous whitespace. Crisp 1–2 px vector strokes. Palette: deep navy #0F4D92, muted rust #B64342, desaturated teal #42949E, neutral gray #767676, very pale gray structural lines. Use line type and marker shapes to distinguish concepts; no shadows, gradients, 3D, textures, UI panels, cards, decoration.

Strict prohibitions: no readable text, no letters, no Chinese, no English, no numbers, no formulas, no legends, no labels, no axes, no coordinate grid, no logo, no watermark, no people, no photos, no circular infographic wheel, no equal-sized blocks, no horizontal three-panel design, no full-scene-plus-zoom-in layout, no poster styling, no flowchart boxes.
```

## 负面提示词（若中转站有 Negative Prompt）

```text
readable words, Chinese characters, English letters, numbers, equations, labels, captions, legends, axis labels, grid, UI dashboard, card layout, three equal columns, triptych, flowchart, full-view and zoom-in, poster, radial infographic, wheel infographic, photographs, people, 3D render, gradients, shadows, textures, logo, watermark, decorative arrows
```

## 坐标验收表（用来选图）

| 区域 | 归一化坐标 (x1,y1)–(x2,y2) | 视觉权重 |
|---|---|---|
| 顶部细条 | (3,3)–(97,7) | 极弱 |
| 输入链 | (4,11)–(96,30) | 中等、横向连续 |
| 等边反例 | (3,33)–(56.5,70.5) | 最大、红色主视觉 |
| Thales 判据 | (60.5,33)–(97,70.5) | 次级、蓝色 |
| gamma 综合带 | (4,76)–(96,89) | 横向综合 |
| 基准特例口袋 | (62,92)–(96,99) | 最弱、灰色 |

淘汰任何出现“等宽三栏”“满屏卡片”“反例与特例同样大”“文字/公式/坐标轴”的候选。
