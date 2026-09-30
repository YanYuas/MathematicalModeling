# Q3 Figures Design Spec

**Goal:** Generate 4 publication-quality MATLAB figures for Problem 3, each answering one explicit requirement in the problem statement.

**Approach:** 方案A — 4 independent figures, Q2 solution = C(中型)-D(中型)-G(大型), 3 stations 109万.

**Tech Stack:** MATLAB R2025a, data from `问题三测试/Q3表格_*.csv`

---

## Figure 1: 最优定价对比 (3.2)

**Data:** `Q3表格_最优定价.csv`
**Type:** Grouped bar chart
**Content:** 5 services × (基准价 vs 最优定价), both below benchmark
**Narrative:** "五项服务全面降价14.3%，S3价格满意度满分"
**Y-axis:** 元/次
**Color:** Blue=基准价, Warm orange=最优定价, dashed line at benchmark

## Figure 2: 年度利润瀑布图 (3.2)

**Data:** `Q3表格_年度利润.csv`
**Type:** Waterfall chart per station (3 subplots or 3 groups)
**Content:** 服务收入 → 直接支出 → 毛利润 → +补贴 → -运营-折旧 → 净利润≈0
**Narrative:** "补贴恰好填补运营亏损，保本微利"
**Color:** Green=positive, Red=negative, Blue=subsidy

## Figure 3: 满意度分解堆叠柱状 (3.2)

**Data:** `Q3表格_小区满意度.csv`
**Type:** Stacked bar chart, 10 communities
**Content:** S1(距离) + S2(利用率) + S3(价格) = total satisfaction
**Narrative:** "S3价格满分，但S2利用率崩塌至0.5，总满意度从0.90降至0.82"
**Highlight:** Price satisfaction component with distinct color
**Color:** Blue(S1) + Coral(S2) + Warm green(S3/price)

## Figure 4: 可及性双轴图 (3.3)

**Data:** `Q3表格_可及性分析.csv`
**Type:** Dual-axis: bars (可负担比例%) + line (需求满足率%)
**Content:** 3 groups = 自理/半失能/失能
**Narrative:** "失能老人悬崖：37.4%可负担 vs 自理100%"
**Color:** Bars by type, line in dark red

---

## Output
All figures → `c:/Users/29845/Desktop/Q3图/`
Scripts → `c:/Users/29845/Desktop/电工杯/问题三/图/`
