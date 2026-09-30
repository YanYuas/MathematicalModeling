# -*- coding: utf-8 -*-
"""Q4 **迷你模拟器**（离线复现定向源物理，用于调优与回归）。

与 `_mini_sim_q3.py` 的关系：
  · Q3 版只实现全向源；**本文件**在其之上加入 **定向源**（附录1(3)：覆盖 = 定向方向两侧各 90°，
    即一个过源的**闭半平面**），因此可以离线检验 Q4 的策略、量虚拟时间、跑极端组合回归，
    **不占用真模拟器的演练/正式次数**（这是 V2.0 工作说明 §四 缺口 #1 的离线补位）。

复现的规则（承 Q3 版，增量标 ✚）：
  · 目标域 r=1800；源在域内；每源一个频道（1..20 互不相同）；有效接收半径 ∈ [1000,1500]
  · ✚ 定向源：`dir` = 定向方向方位角 ψ；`u = (cosψ, sinψ)`
  · ✚ 可测判据（附件2 §2.2 / 附录1(3)）：`‖P−G‖ ≤ R` **且** `(P−G)·u ≥ 0`（含边界）
  · ✚ `near` 同样要求落在扇区内（附录2(9)）-> 定向源**盲侧贴到 1 m 也返回 no_signal**
  · /measure 耗时 = 移动(|Δpos|/5) + 切换频道(1 s，仅当与**测向机当前频道**不同) + 检测 5 s
  · /clear  耗时 = 移动 + 精确定位并清除（未发现 3 s / 成功 5 s）；**不切换频道**；
    ✚ 成功条件**与朝向无关**（附录2(8)）—— 这正是扫掠清除成立的依据
  · 虚拟时钟只在 accepted=true 时推进；/enter、/exit 不推进
  · /__stats 暴露真值（对应演练测试结束会给出总数/定向数）

用法：
    py -3.11 _mini_sim_q4.py --port 20291 --seed 2026 --n 13
    py -3.11 _mini_sim_q4.py --port 20291 --seed 2026 --n 13 --pos extreme   # 全贴边界+全朝外
"""
import argparse
import json
import math
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

LOCK = threading.Lock()
ST = {}
TOL = 1e-9


def _unit(deg):
    a = math.radians(deg)
    return (math.cos(a), math.sin(a))


def reset(seed, n, dir_frac=1.0, r_eff=None, pos_mode="random", fixed=False):
    """fixed=True：摆一个**已知**的定向源（(300,400)、频道 7、R=1200、ψ=90°）
    专供 `test_sector_probe` 用 —— 这样该回归只依赖本文件，不依赖共享的 `_mock_simulator.py`。
    几何与共享 mock 的 `sector` 模式一致（含边界；near 也需在扇区内）。"""
    if fixed:
        ST.clear()
        ST.update({
            "seed": seed, "sources": [{"ch": 7, "x": 300.0, "y": 400.0,
                                       "r": 1200.0, "dir": 90.0}],
            "cleared": set(),
            "pos": (0.0, 0.0), "channel": 1, "vt": 0.0,
            "entered": False, "exited": False,
            "requests": 0, "measures": 0, "clears": 0,
            "clear_hit": 0, "clear_miss": 0,
            "move_m": 0.0, "move_s": 0.0, "switch_s": 0.0, "measure_s": 0.0, "clear_s": 0.0,
            "near": 0, "direction": 0, "no_signal": 0,
        })
        return

    rnd = random.Random(seed)
    chans = rnd.sample(range(1, 21), n)
    srcs = []
    for c in chans:
        is_dir = rnd.random() < dir_frac

        if pos_mode == "extreme":
            # 最坏情形（断言 5 / 退化 G9）：全贴边界 + 定向方向全朝**圆外**
            rr = rnd.uniform(1780.0, 1800.0)
            phi = rnd.uniform(0, 2 * math.pi)
            x, y = rr * math.cos(phi), rr * math.sin(phi)
            psi = math.degrees(math.atan2(y, x))      # 朝外法向
        elif pos_mode == "boundary":
            rr = rnd.uniform(1750.0, 1800.0)
            phi = rnd.uniform(0, 2 * math.pi)
            x, y = rr * math.cos(phi), rr * math.sin(phi)
            psi = rnd.uniform(0, 360)
        else:
            while True:
                x, y = rnd.uniform(-1800, 1800), rnd.uniform(-1800, 1800)
                if 400 * 400 < x * x + y * y <= 1800 * 1800:
                    break
            psi = rnd.uniform(0, 360)

        r = r_eff if r_eff else rnd.uniform(1000.0, 1500.0)
        srcs.append({"ch": c, "x": x, "y": y, "r": r,
                     "dir": (psi if is_dir else None)})

    ST.clear()
    ST.update({
        "seed": seed, "sources": srcs, "cleared": set(),
        "pos": (0.0, 0.0), "channel": 1, "vt": 0.0,
        "entered": False, "exited": False,
        "requests": 0, "measures": 0, "clears": 0,
        "clear_hit": 0, "clear_miss": 0,
        "move_m": 0.0, "move_s": 0.0, "switch_s": 0.0, "measure_s": 0.0, "clear_s": 0.0,
        "near": 0, "direction": 0, "no_signal": 0,
    })


def svd_error(x, y):
    """确定性伪随机误差 ∈[-1,1]°（同一地点误差固定，附件1 §2.2）"""
    v = math.sin(x * 0.0131 + y * 0.0177) * 0.5 + math.sin(x * 0.0037 - y * 0.0091) * 0.5
    return max(-1.0, min(1.0, v))


def visible(src, x, y):
    """可测性判据：距离 ≤ R_eff 且（若定向）落在闭半平面内。

    ⚠️ 2026-09-13 修：这里曾写成 `dx,dy = G−P` 却直接拿它点乘 u，**符号反了** ——
       扇区整体镜像 180°。对随机 u 的**统计量**没影响（镜像只是把 u 换个名字），
       但 `--pos extreme` 那一档（定向方向**朝圆外** = 真正的最坏情形）会退化成"朝圆内"，
       于是"极端档 100%"验的其实是最容易的档。由 `test_sector_probe` 打 `--fixed`
       场景时抓出来（那测试对几何有硬断言，镜像立刻露馅）。
       正确：点在扇区内 ⟺ **(P−G)·u ≥ 0**（附件1(3)「定向方向两侧各 90°（含）」）。
    """
    dx, dy = src["x"] - x, src["y"] - y      # dx,dy = G − P
    dd = math.hypot(dx, dy)
    if dd > src["r"] + TOL:
        return False, dd
    if src["dir"] is not None:
        ux, uy = _unit(src["dir"])
        if (-dx * ux - dy * uy) < -TOL:     # (P−G)·u ≥ 0，含边界
            return False, dd
    return True, dd


class H(BaseHTTPRequestHandler):
    # HTTP/1.1 = 长连接。默认的 HTTP/1.0 会在每次响应后关连接，
    # 而 MATLAB 的 Java 客户端每次重连约 1.1 s（2026-09-13 实测）=> 离线计时会被严重高估。
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/__stats":
            with LOCK:
                srcs = ST["sources"]
                self._send(200, {
                    "total_sources": len(srcs),
                    "n_directional": sum(1 for s in srcs if s["dir"] is not None),
                    "cleared": len(ST["cleared"]),
                    "virtual_time_s": round(ST["vt"], 3),
                    "requests": ST["requests"],
                    "measures": ST["measures"], "clears": ST["clears"],
                    "clear_hit": ST["clear_hit"], "clear_miss": ST["clear_miss"],
                    "measure_kinds": {"direction": ST["direction"],
                                      "near": ST["near"],
                                      "no_signal": ST["no_signal"]},
                    "breakdown": {"move": round(ST["move_s"], 1),
                                  "switch": round(ST["switch_s"], 1),
                                  "measure": round(ST["measure_s"], 1),
                                  "clear": round(ST["clear_s"], 1)},
                    "move_m": round(ST["move_m"], 1),
                    "uncleared_channels": sorted(
                        s["ch"] for s in srcs if s["ch"] not in ST["cleared"]),
                    "uncleared_directional": sorted(
                        s["ch"] for s in srcs
                        if s["ch"] not in ST["cleared"] and s["dir"] is not None),
                })
            return
        self._send(404, {"error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            req = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send(400, {"accepted": False, "real_timestamp_ms": int(time.time() * 1000),
                             "virtual_time_s": 0, "error": "bad json"})
            return
        if self.path not in ("/enter", "/measure", "/clear", "/exit"):
            self._send(404, {"accepted": False, "real_timestamp_ms": int(time.time() * 1000),
                             "virtual_time_s": 0})
            return
        with LOCK:
            self._handle(req)

    def _handle(self, req):
        ts = int(time.time() * 1000)
        base = {"accepted": True, "real_timestamp_ms": ts}
        p = self.path
        ST["requests"] += 1

        if p == "/enter":
            if ST["entered"]:
                self._send(200, {"accepted": False, "real_timestamp_ms": ts, "virtual_time_s": 0})
                return
            ST["entered"] = True
            base.update({"virtual_time_s": 0, "max_virtual_duration_s": 360000,
                         "max_real_duration_s": 1200, "remaining_real_duration_s": 1200})
            self._send(200, base)
            return

        if p == "/exit":
            ST["exited"] = True
            base.update({"virtual_time_s": round(ST["vt"], 6), "exit_reason": "user_exit"})
            self._send(200, base)
            return

        if not ST["entered"] or ST["exited"]:
            self._send(200, {"accepted": False, "real_timestamp_ms": ts, "virtual_time_s": 0})
            return

        pos = req.get("position") or {}
        x, y = float(pos.get("x", 0)), float(pos.get("y", 0))
        ch = req.get("channel")

        d = math.hypot(x - ST["pos"][0], y - ST["pos"][1])
        move = d / 5.0
        ST["pos"] = (x, y)
        ST["move_m"] += d
        ST["move_s"] += move
        ST["vt"] += move

        if p == "/measure":
            ST["measures"] += 1
            if ch != ST["channel"]:
                ST["switch_s"] += 1.0
                ST["vt"] += 1.0
            ST["channel"] = ch
            ST["measure_s"] += 5.0
            ST["vt"] += 5.0

            src = next((s for s in ST["sources"] if s["ch"] == ch), None)
            if src is None or ch in ST["cleared"]:
                res = {"measure_result": "no_signal"}
            else:
                vis, dd = visible(src, x, y)
                if not vis:
                    res = {"measure_result": "no_signal"}
                elif dd <= 5.0:
                    res = {"measure_result": "near"}          # near 也要在扇区内（附录2(9)）
                else:
                    brg = math.degrees(math.atan2(src["y"] - y, src["x"] - x)) % 360.0
                    brg = (brg + svd_error(x, y)) % 360.0
                    res = {"measure_result": "direction", "svd_deg": round(brg, 2)}
            ST[res["measure_result"]] += 1
            base.update(res)
            base["virtual_time_s"] = round(ST["vt"], 6)
            self._send(200, base)
            return

        # ---- /clear：与朝向无关（附录2(8)）----
        ST["clears"] += 1
        src = next((s for s in ST["sources"] if s["ch"] == ch), None)
        hit = src is not None and ch not in ST["cleared"] and \
            math.hypot(src["x"] - x, src["y"] - y) <= 20.0
        cost = 5.0 if hit else 3.0
        ST["clear_s"] += cost
        ST["vt"] += cost
        if hit:
            ST["cleared"].add(ch)
            ST["clear_hit"] += 1
        else:
            ST["clear_miss"] += 1
        base.update({"clear_result": "success" if hit else "no_target_in_range",
                     "virtual_time_s": round(ST["vt"], 6)})
        self._send(200, base)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=20291)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--n", type=int, default=13)
    ap.add_argument("--dir-frac", dest="dir_frac", type=float, default=1.0,
                    help="定向源占比（0=纯全向 -> Q3⊂=Q4 退化自检；1=全定向）")
    ap.add_argument("--r-eff", dest="r_eff", type=float, default=0.0,
                    help="强制全部源的有效接收半径（0=随机 [1000,1500]；1000=最坏）")
    ap.add_argument("--pos", default="random", choices=["random", "boundary", "extreme"])
    ap.add_argument("--fixed", action="store_true",
                    help="摆一个已知定向源（(300,400) 频道7 R=1200 ψ=90°），供 test_sector_probe 用")
    a = ap.parse_args()
    reset(a.seed, a.n, a.dir_frac, (a.r_eff or None), a.pos, a.fixed)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), H)
    print("mini Q4 simulator on 127.0.0.1:%d seed=%d n=%d dir_frac=%.2f pos=%s"
          % (a.port, a.seed, a.n, a.dir_frac, a.pos), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
