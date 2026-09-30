# Q3 代码交付包 — CleanArch 说明

> 面向建模手 | 2026-08-09 | 本机路径 `问题3/数据/`

---

## 一、依赖图（自下而上）

```
                   ┌──────────┐
                   │ run_q3.py│  ← 一键入口
                   └────┬─────┘
        ┌────────┬──────┼──────┬────────┐
        ▼        ▼      ▼      ▼        ▼
   m3_scan.py  m4_layer_b.py  m5_deliver.py  m3_breakthrough.py
   (可行性扫描) (层B HPWL)    (可视化)       (突破尝试)
        │           │
        └─────┬─────┘
              ▼
    ┌─────────┴─────────┐
    │  m2_init.py       │ ← 构造 (FFD/skyline/orders)
    │  m2_hpwl.py       │ ← HPWL 评估
    │  m_construct.py   │ ← FFD 布局 → B*-Tree
    └─────────┬─────────┘
              ▼
    ┌─────────┴─────────┐
    │  m_btree.py       │ ← B*-Tree + skyline contour 解码
    │  m_operators.py   │ ← 三扰动算子 (rotate/del-ins/swap)
    └─────────┬─────────┘
              ▼
    ┌─────────┴─────────┐
    │  m2_data.py       │ ← 数据解析 + Block 类 + 校验
    └───────────────────┘
```

## 二、文件清单

| 文件 | 行数 | 职责 |
|------|------|------|
| `run_q3.py` | 250 | **一键入口**：可行性扫描 → 层B → 可视化 |
| `m2_data.py` | 153 | `.blocks/.nets/.pl` 解析、Block 类、校验 |
| `m2_hpwl.py` | 110 | HPWL 评估 (evaluate/terminal_vs_internal) |
| `m2_init.py` | 180 | 构造初始化 (FFD/skyline/orders) |
| `m_btree.py` | 187 | B*-Tree + Contour O(n) 解码 |
| `m_operators.py` | 149 | 三扰动算子 (rotate 0.2 / del-ins 0.4 / swap 0.4) |
| `m_construct.py` | 195 | FFD 行堆叠 + layout→B*-Tree 转换 |
| `m3_scan.py` | 118 | Q3 可行性扫描（二分求 Γ*） |
| `m3_breakthrough.py` | 172 | 溢出重定位尝试（n100/n200 临界 gap=1） |
| `m4_layer_b.py` | 199 | 层B 贪心下降 HPWL 优化 |
| `m5_deliver.py` | 275 | 三组布图 + 可行性曲线 + 权衡曲线 |

## 三、一键运行

```bash
cd 问题3/数据
python run_q3.py
```

产出 `问题3/输出/`：
- `n100_gamma_star_layout.png`
- `n200_gamma_star_layout.png`
- `n300_gamma_star_layout.png`
- `feasibility_curve.png`
- `tradeoff_curve.png`
- `m4_results.json`

## 四、算法核心：贪心可行下降

```
INPUT: blocks, nets, terminals, S (轮廓边长)
OUTPUT: best HPWL + feasible layout

1. 构造初始树: FFD h_desc 行堆叠 → layout_to_btree
2. cur = 初始树
3. FOR i = 1..10000:
     cand = copy(cur)
     random_perturbation(cand)   # rotate/del-ins/swap
     IF pack(cand).M > S: CONTINUE   # 硬门：不可行直接拒绝
     IF HPWL(cand) < HPWL(cur): cur = cand   # 只接受线长下降
4. RETURN best HPWL
```

关键设计决策：
- **硬门**而非软惩罚：Q1/Q2 实践证明软惩罚导致 cur 漂移不可行
- **贪心下降**而非 SA 温度：Q2 独立实现证实可行内下降路径丰富，温度是负资产
- **B*-Tree 编码**：天然无重叠，O(n) 解码

## 五、关键数字速查

| 组 | A | Γ=0.15 的 S | Q1M (=S*) | Γ* | 死区占比 | HPWL(.15) | HPWL(Γ*) |
|---|---|---|---|---|---|---|---|
| n100 | 179,501 | 454.34 | 443 | 0.0933 | 8.53% | 244,564 | 246,460 |
| n200 | 175,696 | 449.50 | 432 | 0.0622 | 5.86% | 468,120 | 493,143 |
| n300 | 273,170 | 560.49 | 533 | 0.0400 | 3.84% | 705,918 | 789,261 |
