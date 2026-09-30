# -*- coding: utf-8 -*-
"""_analyze_real_runs.py —— 真机日志分解：时间账 + 「还剩多少余量」量化

用法：
    py -3.11 _analyze_real_runs.py [--date 20260913] [--dir <logs目录>]

对每局 robot_*.jsonl：
  ① 时间账：移动/5 + 检测×5 + 频道切换×1 + 清除(成功5/失败3)
     与 session_end.virtual_time_s 对比 ⇒ 残差应 ≈ 0（验证计价模型正确）
  ② 行程分解：取「访问点集」= 被检测过的格点 ∪ 各源的清除位置，
     对它求 NN+2-opt 最优巡回（从起点起）⇒ 与实际行程比 = 路线调度浪费
     ⚠️ 该下界含"不必绕路但必须探测"的部分（homing/sweep 的探点行程），
        故 gap% 是**余量上界**，不是可回收量。
  ③ 汇总：均摊 s/源、总时间、源数分组

判据：时间账残差 |resid| 应 < 15 s（否则计价模型与模拟器不符，后续数字全废）。
"""
import argparse
import glob
import io
import json
import math
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SQRT3_2 = math.sqrt(3.0) / 2.0


def grid_points(d=1000.0, r_domain=1800.0):
    """与 generate_triangular_grid 同构：中心 + 六边形(d) + 六边形(2d)"""
    span = int(r_domain / d) + 2
    pts = []
    for j in range(-span, span + 1):
        for i in range(-span, span + 1):
            x = i * d + j * d / 2.0
            y = j * d * SQRT3_2
            if math.hypot(x, y) <= r_domain + 1e-6:
                pts.append((x, y))
    return pts


def radial_grid(d_inner=1000.0, r_outer=1300.0, phase_inner=0.0, phase_outer=None):
    """与 generate_radial_grid 同构：中心 + 六边形(r_inner) + 六边形(r_outer)，两环错开 30°。"""
    if phase_outer is None:
        phase_outer = math.pi / 6.0
    pts = [(0.0, 0.0)]
    for k in range(6):
        a1 = phase_inner + k * math.pi / 3.0
        pts.append((d_inner * math.cos(a1), d_inner * math.sin(a1)))
        a2 = phase_outer + k * math.pi / 3.0
        pts.append((r_outer * math.cos(a2), r_outer * math.sin(a2)))
    return pts


def read_grid_info(path):
    """从自记录日志里读 `grid_info`（2026-09-13 起 main_Q3Q4 每局都写）。
    返回 (style, r_outer, d) 或 None（旧日志没有这条）。"""
    for ln in io.open(path, encoding="utf-8", errors="replace"):
        try:
            d = json.loads(ln)
        except Exception:
            continue
        if d.get("kind") == "grid_info":
            return (d.get("grid_style"), d.get("r_outer"), d.get("grid_spacing"))
    return None


def nearest_grid(p, grid, tol=1.5):
    for g in grid:
        if abs(p[0] - g[0]) <= tol and abs(p[1] - g[1]) <= tol:
            return g
    return None


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def tour_len(order, pts):
    return sum(dist(pts[order[i]], pts[order[i + 1]]) for i in range(len(order) - 1))


def nn_order(pts):
    n = len(pts)
    un = set(range(1, n))
    order = [0]
    cur = 0
    while un:
        nxt = min(un, key=lambda j: dist(pts[cur], pts[j]))
        order.append(nxt)
        un.discard(nxt)
        cur = nxt
    return order


def two_opt(order, pts, max_pass=60):
    best = tour_len(order, pts)
    for _ in range(max_pass):
        improved = False
        for i in range(1, len(order) - 1):
            for j in range(i + 1, len(order)):
                cand = order[:i] + order[i:j + 1][::-1] + order[j + 1:]
                l = tour_len(cand, pts)
                if l < best - 1e-9:
                    order, best, improved = cand, l, True
        if not improved:
            break
    return order, best


def optimal_open_tour(pts):
    """pts[0] 固定为起点"""
    if len(pts) <= 2:
        return tour_len(list(range(len(pts))), pts)
    return two_opt(nn_order(pts), pts)[1]


def load(path):
    recs = []
    with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except Exception:
                pass
    return recs


def analyze(path, grid):
    recs = load(path)
    reqs = [r for r in recs if r.get("kind") == "request"]
    ends = [r for r in recs if r.get("kind") == "session_end"]
    vt = ends[0].get("virtual_time_s") if ends else None

    cur_ch = None
    prev = None
    start = None
    move = 0.0
    n_meas = n_switch = n_ok = n_bad = 0
    n_meas_grid = n_meas_probe = 0
    targets = []          # 访问点集
    seen = set()
    ch_ok = set()
    ch_dir = set()
    ch_clear_try = {}     # 频道 -> /clear 次数（含失败）
    ch_meas = {}          # 频道 -> /measure 次数

    for r in reqs:
        ep = r.get("endpoint", "")
        rp = r.get("request_payload") or {}
        pos = rp.get("position")
        p = None
        if isinstance(pos, dict) and "x" in pos and "y" in pos:
            p = (float(pos["x"]), float(pos["y"]))
            if start is None:
                start = p
            if prev is not None:
                move += dist(p, prev)
            prev = p
        resp = r.get("response_payload") or {}

        if ep == "/measure":
            n_meas += 1
            ch = rp.get("channel")
            if ch is not None:
                ch_meas[ch] = ch_meas.get(ch, 0) + 1
                if cur_ch is not None and ch != cur_ch:
                    n_switch += 1
                cur_ch = ch
            res = resp.get("measure_result")
            if res == "direction" and ch is not None:
                ch_dir.add(ch)
            if p is not None:
                g = nearest_grid(p, grid)
                if g is None:
                    n_meas_probe += 1
                else:
                    n_meas_grid += 1
                    k = ("G", g[0], g[1])
                    if k not in seen:
                        seen.add(k)
                        targets.append(g)
        elif ep == "/clear":
            ch = rp.get("channel")
            if ch is not None:
                ch_clear_try[ch] = ch_clear_try.get(ch, 0) + 1
            if resp.get("clear_result") == "success":
                n_ok += 1
                if ch is not None:
                    ch_ok.add(ch)
                if p is not None and ch is not None:
                    k = ("C", ch)
                    if k not in seen:
                        seen.add(k)
                        targets.append(p)
            else:
                n_bad += 1

    T_calc = move / 5.0 + n_meas * 5.0 + n_switch * 1.0 + n_ok * 5.0 + n_bad * 3.0
    resid = (vt - T_calc) if vt is not None else None

    bound = None
    if start is not None and len(targets) >= 2:
        bound = optimal_open_tour([start] + targets)

    return dict(
        path=path, n_src=n_ok, vt=vt, avg=(vt / n_ok if vt and n_ok else None),
        move=move, bound=bound,
        gap=(move - bound if bound else None),
        gap_pct=(100.0 * (move - bound) / bound if bound else None),
        n_meas=n_meas, n_meas_grid=n_meas_grid, n_meas_probe=n_meas_probe,
        n_switch=n_switch, n_ok=n_ok, n_bad=n_bad,
        T_calc=T_calc, resid=resid, n_dir_ch=len(ch_dir),
        missing=sorted(ch_dir - ch_ok),
        # 清除方式：单次 /clear 命中 = direct；≥2 次 = sweep 或 homing（探过点）
        n_direct=sum(1 for ch in ch_ok if ch_clear_try.get(ch, 0) == 1),
        n_multi=sum(1 for ch in ch_ok if ch_clear_try.get(ch, 0) > 1),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="只看该日期前缀，如 20260913")
    ap.add_argument("--dir", default=None)
    ap.add_argument("--all", action="store_true",
                    help="连离线自测产生的 robot_TESTTEAM_* 一起统计（默认剔除，它们 0 清除、会污染均值）")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    logdir = args.dir or os.path.join(here, "..", "MATLAB_Framework", "logs")
    files = sorted(glob.glob(os.path.join(logdir, "robot_*.jsonl")))
    if args.date:
        files = [f for f in files if args.date in os.path.basename(f)]
    if not args.all:
        # 离线自测（_test_enter_wait.py 等）也会在 logs/ 落盘，队号是 TESTTEAM
        files = [f for f in files if "TEST" not in os.path.basename(f)]
    files = [f for f in files if os.path.getsize(f) > 0]
    if not files:
        print("未找到日志：%s" % logdir)
        return 1

    # 【2026-09-13 修正】格点模型**按每局的 `grid_info` 选**，不再全局写死三角格。
    #   踩过的坑：径向档(外环 1300/相 30°)的外圈 6 点不是三角格格点 ⇒ 全局写死会把它们
    #   全部误判成"探点"（实测 5 局出现 66~94 个假"探点"，纯属坐标模型错误，不是 homing）。
    #   旧日志（无 grid_info）仍按三角格处理，但行末标 `[网格?]` 提醒该行的格点/探点两列不可信。
    print("格点模型：按每局 grid_info 选择（无该字段的旧日志按三角格处理并标记 [网格?]）")
    print()

    rows = []
    for f in files:
        m = re.search(r"_(\d{8})_(\d{6})\.jsonl$", os.path.basename(f))
        stamp = ("%s %s" % (m.group(1), m.group(2))) if m else os.path.basename(f)
        gi = read_grid_info(f)
        grid_ok = True
        if gi and gi[0] == "radial":
            grid = radial_grid(d_inner=gi[2] or 1000.0, r_outer=gi[1] or 1300.0)
        elif gi and gi[0] == "triangular":
            grid = grid_points(d=gi[2] or 1000.0)
        elif gi and gi[0] == "q4_extended":
            grid = grid_points(d=gi[2] or 1000.0)
            grid_ok = False          # 外扩环带模型不同，Q3 的格点/探点分类不适用
        else:
            grid = grid_points()
            grid_ok = False          # 旧日志：无法确证用的哪档
        a = analyze(f, grid)
        if a["vt"] is None:
            print("%-16s ⚠️ 无 session_end（未正常结束）" % stamp)
            continue
        a["stamp"] = stamp
        a["grid_ok"] = grid_ok
        a["grid_style"] = gi[0] if gi else "?"
        rows.append(a)

    if not rows:
        return 1

    hdr = ("%-16s %8s %4s %8s %8s %8s %8s %7s %5s %5s %5s %4s %4s %7s %6s %s"
           % ("时刻", "网格", "源数", "虚拟时间", "均摊", "行程", "巡回下界", "余量%",
              "检测", "格点", "探点", "切换", "失败", "时间账", "残差", "核对"))
    print(hdr)
    print("-" * len(hdr))
    for a in rows:
        if a["missing"]:
            note = "遗漏%s" % a["missing"]
        elif a["n_src"] == 0:
            note = "⚠ 0 清除（非正式局？）"
        elif a["n_dir_ch"] > a["n_src"]:
            note = "⚠ 检出多于清除"
        else:
            note = "OK"
        if not a["grid_ok"]:
            note += " [网格模型不适用⇒格点/探点两列不可信]"
        print("%-16s %8s %4d %8.0f %8.1f %8.0f %8.0f %6.1f%% %5d %5d %5d %4d %4d %7.0f %6.1f %s"
              % (a["stamp"], a["grid_style"], a["n_src"], a["vt"],
                 a["avg"] if a["avg"] is not None else float('nan'), a["move"], a["bound"] or 0,
                 a["gap_pct"] or 0, a["n_meas"], a["n_meas_grid"], a["n_meas_probe"],
                 a["n_switch"], a["n_bad"], a["T_calc"],
                 a["resid"] if a["resid"] is not None else float('nan'), note))

    used = [a for a in rows if a["n_src"] > 0]
    if not used:
        print()
        print("⚠️ 没有「清除数 > 0」的正式局，不做统计。")
        return 1
    n = len(used)
    avg_avg = sum(a["avg"] for a in used) / n
    avg_vt = sum(a["vt"] for a in used) / n
    avg_gap = sum(a["gap_pct"] for a in used) / n
    worst_res = max(abs(a["resid"]) for a in used)
    print()
    print("局数 %d ｜ 平均均摊 **%.1f s/源** ｜ 平均总时间 %.0f s ｜ 平均行程余量 %.1f%% ｜ 最大时间账残差 %.1f s"
          % (n, avg_avg, avg_vt, avg_gap, worst_res))

    groups = {}
    for a in used:
        groups.setdefault(a["n_src"], []).append(a)
    print()
    print("按源数分组（均摊 ／ 总时间 ／ 行程 ／ 余量%%）：")
    for k in sorted(groups):
        g = groups[k]
        kk = len(g)
        print("  源数 %2d × %d 局 ⇒ 均摊 %6.1f ｜ 总时间 %6.0f ｜ 行程 %6.0f ｜ 余量 %5.1f%%"
              % (k, kk, sum(x["avg"] for x in g) / kk, sum(x["vt"] for x in g) / kk,
                 sum(x["move"] for x in g) / kk, sum(x["gap_pct"] for x in g) / kk))

    d_tot = sum(a["n_direct"] for a in used)
    m_tot = sum(a["n_multi"] for a in used)
    probe_tot = sum(a["n_meas_probe"] for a in used)
    if d_tot + m_tot:
        print()
        print("清除方式（按频道 /clear 次数）：直接命中 %d 个（%.1f%%）｜ 非直接（sweep/homing，≥2 次）%d 个（%.1f%%）"
              % (d_tot, 100.0 * d_tot / (d_tot + m_tot), m_tot, 100.0 * m_tot / (d_tot + m_tot)))
        print("  ⇒ 非直接那部分才需要「离格点走一段」，是可优化的行程来源之一")
    print("探点检测（不在任何格点上的 /measure）合计 %d 次，占总检测 %.1f%%"
          % (probe_tot, 100.0 * probe_tot / sum(a["n_meas"] for a in used)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
