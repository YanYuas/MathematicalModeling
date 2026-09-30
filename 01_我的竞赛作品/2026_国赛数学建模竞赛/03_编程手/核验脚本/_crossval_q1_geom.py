# -*- coding: utf-8 -*-
"""Q1 几何**跨实现交叉验证**驱动（第二版）。

MATLAB 侧：`Q1_geometry.intersect_wedges`（polyshape 布尔求交）
Python 侧：`q1_main`（射线两两求交 + 角域过滤 + Andrew 凸包）

【第二版修正两处设计缺陷】
 ① **案例不真实**：第一版 θ 在 0~360° 里乱取 ⇒ 60 组里 48 组是空集，测的是"不相交"而非算法差异。
    现改为**真实场景**：取一个真源 S，示向度 = S 的真实方位 + 噪声（|噪声| ≤ 1°，与附件1 §2.2 一致）。
 ② **没对齐截断**：Python 侧不截断、MATLAB 的 polyshape 有 5000 m 边界 ⇒ 在"区域无界"的
    近平行配置上必然分歧，但那是"有没有圆域截断"的差别，不是算法差异。
    现**同时输出两套**：`raw_*`（原始交）与 `clip_*`（再套 Q3 实际用的 `clip_to_domain(R=1800)`），
    Python 侧做同样处理，两组分别比对。

用法：py -3.11 _crossval_q1_geom.py
退出码：0 = 两套结果都在容差内一致；1 = 有分歧。
"""
import json
import math
import os
import random
import subprocess
import sys

try:
    sys.stdout.reconfigure(errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
MATLAB_SRC = os.path.join(REPO, '03_编程手', 'MATLAB_Framework')
Q1_DIR = os.path.join(REPO, '03_编程手', 'Q1', '实验结果')
MATLAB = r'D:\R2026a_Windows\bin\matlab.exe'
CASES = os.path.join(HERE, '_crossval_cases.json')
ML_OUT = os.path.join(HERE, '_crossval_matlab.json')
REPORT = os.path.join(HERE, '_crossval_report.txt')
R_DOMAIN = 1800.0
REL_TOL = 1e-6


def bearing(src, p):
    return math.degrees(math.atan2(src[1] - p[1], src[0] - p[0])) % 360.0


def gen_cases():
    rnd = random.Random(20260912)
    cases = []

    def add(name, stations, thetas):
        cases.append({"name": name,
                      "stations": [[float(x), float(y)] for x, y in stations],
                      "thetas": [float(t) % 360.0 for t in thetas],
                      "eps": [1.0] * len(stations)})

    add("baseline_2wedge", [(0.0, 0.0), (600.0, 0.0)], [59.036, 120.964])

    def rnd_src():
        while True:
            x, y = rnd.uniform(-1780, 1780), rnd.uniform(-1780, 1780)
            if x * x + y * y <= 1780 * 1780:
                return (x, y)

    def rnd_station(src, mind=50.0):
        while True:
            x, y = rnd.uniform(-1800, 1800), rnd.uniform(-1800, 1800)
            if x * x + y * y <= 1800 * 1800 and math.hypot(x - src[0], y - src[1]) >= mind:
                return (x, y)

    # 真实场景：2~5 个站点，示向度 = 真实方位 + 均匀噪声
    for i in range(60):
        src = rnd_src()
        n = rnd.randint(2, 5)
        st = [rnd_station(src) for _ in range(n)]
        th = [bearing(src, p) + rnd.uniform(-1.0, 1.0) for p in st]
        add("real_%02d_n%d" % (i, n), st, th)

    # 真实最坏：噪声全部同号取满 ±1°（区域最大）
    for i in range(10):
        src = rnd_src()
        n = rnd.randint(2, 4)
        st = [rnd_station(src) for _ in range(n)]
        sgn = 1.0 if i % 2 == 0 else -1.0
        th = [bearing(src, p) + sgn * 1.0 for p in st]
        add("worst_%02d_n%d" % (i, n), st, th)

    # 真实细长：站点与源近共线（区域扁长，最考验数值）
    for i in range(8):
        src = rnd_src()
        ang = rnd.uniform(0, 360)
        st = []
        for k in range(3):
            d = 400.0 + 500.0 * k
            st.append((src[0] + d * math.cos(math.radians(ang)),
                       src[1] + d * math.sin(math.radians(ang))))
        th = [bearing(src, p) + rnd.uniform(-1.0, 1.0) for p in st]
        add("thin_%02d" % i, st, th)

    return cases


def run_python(cases):
    sys.path.insert(0, Q1_DIR)
    import numpy as np
    import q1_main as q1

    out = []
    for c in cases:
        st = [np.array(p, dtype=float) for p in c["stations"]]
        rec = {"name": c["name"]}
        try:
            w = q1.build_wedges(st, c["thetas"], c["eps"][0])
            v = q1.candidate_vertices(w)
            poly = q1.convex_hull(v)
        except Exception as e:
            rec["err"] = "%s: %s" % (type(e).__name__, e)
            out.append(rec)
            continue

        if poly is None or poly.num_vertices() < 1:
            rec.update({"raw_empty": True, "raw_R": None, "raw_D": None,
                        "raw_area": None, "raw_nv": 0,
                        "clip_empty": True, "clip_R": None, "clip_D": None, "clip_nv": 0})
            out.append(rec)
            continue

        P = poly.vertices
        _, r = q1.welzl_mec(P)
        D, _ = q1.diameter_bruteforce(poly)
        a = 0.0
        for i in range(len(P)):
            x1, y1 = P[i]
            x2, y2 = P[(i + 1) % len(P)]
            a += x1 * y2 - x2 * y1
        rec.update({"raw_empty": False, "raw_R": float(r), "raw_D": float(D),
                    "raw_area": abs(a) / 2.0, "raw_nv": int(len(P))})

        # 与 MATLAB 的 clip_to_domain 完全一致：只保留圆域内的顶点，**不重新求凸包**
        kept = [p for p in P if math.hypot(p[0], p[1]) <= R_DOMAIN + 1e-9]
        if not kept:
            rec.update({"clip_empty": True, "clip_R": None, "clip_D": None, "clip_nv": 0})
        else:
            K = [np.array(p, dtype=float) for p in kept]
            _, rc = q1.welzl_mec(K)
            rec.update({"clip_empty": False, "clip_R": float(rc),
                        "clip_D": float(_diam(K)), "clip_nv": len(kept)})
        out.append(rec)
    return out


def _diam(K):
    best = 0.0
    for i in range(len(K)):
        for j in range(i + 1, len(K)):
            d = math.hypot(K[i][0] - K[j][0], K[i][1] - K[j][1])
            if d > best:
                best = d
    return best


def compare(tag, py, ml, keys):
    lines, bad = [], []
    for a, b in zip(py, ml):
        name = a["name"]
        if a.get("err"):
            lines.append("%-22s [%s] Python 异常：%s" % (name, tag, a["err"]))
            bad.append(name)
            continue
        pa = bool(a.get(tag + "_empty"))
        pb = bool(b.get(tag + "_empty"))
        if pa != pb:
            lines.append("%-22s [%s] ❌ 空/非空不一致 Python空=%s MATLAB空=%s" % (name, tag, pa, pb))
            bad.append(name)
            continue
        if pa:
            lines.append("%-22s [%s] ✅ 均为空集" % (name, tag))
            continue
        worst = 0.0
        det = []
        for k in keys:
            va, vb = a.get(tag + "_" + k), b.get(tag + "_" + k)
            if va is None or vb is None:
                continue
            d = abs(float(va) - float(vb))
            rel = d / max(abs(float(va)), 1e-12)
            worst = max(worst, rel)
            det.append("%s %.1e" % (k, d))
        ok = worst <= REL_TOL
        if not ok:
            bad.append(name)
        lines.append("%-22s [%s] %s nv %s/%s ｜ %s ｜ 最差相对 %.1e"
                     % (name, tag, "✅" if ok else "❌", a.get(tag + "_nv"), b.get(tag + "_nv"),
                        " ｜ ".join(det), worst))
    return lines, bad


def main():
    cases = gen_cases()
    with open(CASES, "w", encoding="utf-8") as f:
        json.dump({"R_domain": R_DOMAIN, "cases": cases}, f, ensure_ascii=False, indent=1)

    py = run_python(cases)
    cmd = ("crossval_q1_geom('%s','%s')" % (CASES.replace("\\", "/"), ML_OUT.replace("\\", "/")))
    p = subprocess.run([MATLAB, "-nosplash", "-sd", MATLAB_SRC, "-batch", cmd],
                       capture_output=True, timeout=1800)
    if not os.path.exists(ML_OUT):
        print("MATLAB 侧未产出。stdout:")
        print((p.stdout or b"").decode("utf-8", "replace"))
        return 1
    ml = json.load(open(ML_OUT, encoding="utf-8"))
    if isinstance(ml, dict):
        ml = [ml]

    lines, bad = [], []
    hdr = ["Q1 几何跨实现交叉验证报告（第二版：真实案例 + 对齐截断）",
           "MATLAB：Q1_geometry.intersect_wedges（polyshape 布尔求交，自带 5000 m 边界）",
           "Python：q1_main（射线两两求交 + 角域过滤 + Andrew 凸包，不截断）",
           "案例 %d ｜ 相对容差 %.0e ｜ 圆域 R_domain=%.0f m" % (len(cases), REL_TOL, R_DOMAIN),
           ""]
    l1, b1 = compare("raw", py, ml, ["R", "D", "area"])
    l2, b2 = compare("clip", py, ml, ["R", "D"])
    lines = hdr + ["", "===== ① 原始交（raw_*）====="] + l1 + \
            ["", "===== ② 按 Q3 实际做法截断到 r=%.0f（clip_*）=====" % R_DOMAIN] + l2
    bad = sorted(set(b1 + b2))

    txt = "\n".join(lines)
    with open(REPORT, "w", encoding="utf-8", newline="") as f:
        f.write(txt + "\n")
    print(txt)
    print()
    print("=" * 72)
    print("案例 %d ｜ 原始交分歧 %d ｜ 截断后分歧 %d" % (len(cases), len(b1), len(b2)))
    if bad:
        print("分歧案例: %s" % ", ".join(bad))
    print("报告: %s" % REPORT)
    print("=" * 72)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
