# 设计工具（**不在生产路径上**）

这里放的是**点集设计/削减/基准**的一次性脚本与它们的输出留痕。
**`MATLAB_Framework_v2.0/` 根目录下没有任何 .m 调用它们**（2026-09-13 逐个 grep 核实过：
`q4_grid_search` / `q4_grid_optimize` / `q4_grid_optimize2` / `q4_grid_candidates` / `bench_http`
只出现在 `Q4_extensions.m` 与 `main_Q3Q4.m` 的**注释**里，不是调用）。
挪进子目录不影响任何生产路径，也不会被"平铺 27 个 .m 就是源码"的交付检查误收。

## 里面是什么

| 文件 | 作用 | 产出 |
|---|---|---|
| `q4_grid_search.m` | 细扫"内层格 + 外层正 n 边形环"的 (环半径, 点数, 相位)，报 surrounding 通过性与 MST | 选定 `r = R_domain+100`、`n = 12`、相位 0 |
| `q4_grid_optimize.m` | 对**规则格**做贪心删点（证明 31 点是格点意义下的极限：18 次删除全被拒） | — |
| `q4_grid_optimize2.m` | 细格 + 贪心削减（被 `q4_grid_search` 的构造法取代，留档） | — |
| `q4_grid_candidates.m` | 手工候选点集的批量对照（内外层组合） | — |
| `bench_http.m` | 拆开每次 HTTP 请求的耗时（webwrite / JSONL 落盘） | 抓到"HTTP/1.0 ⇒ 1.1 s/次"那个坑 |
| `_grid*.txt` `_assert_out.txt` | 上述脚本与断言的实际输出 | 证据留痕 |

## 怎么跑（**必须先挂路径**）

这些脚本要调根目录的 `Q4_extensions` / `Q1_geometry` 等，直接 `-sd 本目录` 会找不到。
从根目录跑并临时把本目录挂上 path：

```bat
matlab -nosplash -sd "..\MATLAB_Framework_v2.0" -batch "addpath('设计工具'); q4_grid_search()"
```

**换网格设计后必须重跑 `q4_grid_search.m`** —— 环半径的"通过区间"随半径/点数变化的，
不是写死的常数（现行结论：`r ∈ [1870, 1960]` 通过，`2000` 起失败，取 `1900`）。
