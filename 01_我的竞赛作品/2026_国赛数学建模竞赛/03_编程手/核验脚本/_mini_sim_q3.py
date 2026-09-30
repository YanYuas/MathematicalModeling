# -*- coding: utf-8 -*-
"""Q3 **迷你模拟器**（离线复现，用于调优与回归；不是协议 mock）。

与 `_mock_simulator.py` 的分工：
  · `_mock_simulator.py`  —— 只验**协议行为**（状态码 / accepted / 重试口径），时间模型是朴素的。
  · **本文件**            —— 复现**物理与计时**（附件1 §2 / 附件2 §4），因此**可以离线量耗时**，
                            无需占用真模拟器的演练次数，也便于反复对比算法改动。

复现的规则：
  · 目标域 r=1800；源在域内；每源一个频道（1..20 互不相同）；有效接收半径 ∈ [1000,1500]
  · /measure 耗时 = 移动(|Δpos|/5) + 切换频道(1 s，仅当与**测向机当前频道**不同) + 检测 5 s
  · /clear  耗时 = 移动 + 精确定位并清除（未发现 3 s / 成功 5 s）；**不切换频道**
  · 检测结果：距离>半径 → no_signal；距离≤5 且覆盖内 → near；否则 → direction(真实方位±误差)
  · 清除：指定频道未清除且距离≤20 → success；否则 no_target_in_range
  · 虚拟时钟只在 accepted=true 时推进；/enter、/exit 不推进
  · 结束（/exit）时把**本局源总数**通过 /__stats 暴露（对应演练测试结束会给出总数，附件1 §4.6）

用法：
    py -3.11 _mini_sim_q3.py --port 20290 --seed 2026 --n 13
    # 结束后读 /__stats 拿 总数/已清除/虚拟时间
"""
import argparse
import json
import math
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOCK = threading.Lock()
ST = {}


def reset(seed, n, directional=False):
    rnd = random.Random(seed)
    chans = rnd.sample(range(1, 21), n)
    srcs = []
    for c in chans:
        while True:
            x, y = rnd.uniform(-1800, 1800), rnd.uniform(-1800, 1800)
            if x * x + y * y <= 1800 * 1800 and (x * x + y * y) > 400 * 400:
                break
        srcs.append({"ch": c, "x": x, "y": y, "r": rnd.uniform(1000.0, 1500.0),
                     "dir": (rnd.uniform(0, 360) if directional else None)})
    ST.clear()
    ST.update({
        "seed": seed, "sources": srcs, "cleared": set(),
        "pos": (0.0, 0.0), "channel": 1, "vt": 0.0,
        "entered": False, "exited": False,
        "requests": 0, "measures": 0, "clears": 0,
        "move_m": 0.0, "move_s": 0.0, "switch_s": 0.0, "measure_s": 0.0, "clear_s": 0.0,
    })


def svd_error(x, y):
    """确定性伪随机误差 ∈[-1,1]°（真模拟器的误差在同一地点固定，附件1 §2.2）"""
    v = math.sin(x * 0.0131 + y * 0.0177) * 0.5 + math.sin(x * 0.0037 - y * 0.0091) * 0.5
    return max(-1.0, min(1.0, v))


class H(BaseHTTPRequestHandler):
    # HTTP/1.1 = 长连接。BaseHTTPRequestHandler 默认 HTTP/1.0（每次响应后关连接），
    # 而 MATLAB 的 Java HTTP 客户端每次重连约 1.1 s（2026-09-13 实测：HTTP/1.0 -> 1123 ms/req，
    # HTTP/1.1 -> 11 ms/req）=> 会让"程序墙钟"被高估约 100x。虚拟时间不受影响。
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
                self._send(200, {
                    "total_sources": len(ST["sources"]),
                    "cleared": len(ST["cleared"]),
                    "virtual_time_s": round(ST["vt"], 3),
                    "requests": ST["requests"],
                    "measures": ST["measures"], "clears": ST["clears"],
                    "breakdown": {"move": round(ST["move_s"], 1),
                                  "switch": round(ST["switch_s"], 1),
                                  "measure": round(ST["measure_s"], 1),
                                  "clear": round(ST["clear_s"], 1)},
                    "move_m": round(ST["move_m"], 1),
                    "uncleared_channels": sorted(
                        s["ch"] for s in ST["sources"] if s["ch"] not in ST["cleared"]),
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

        # ---- 移动耗时（两种指令都算），并更新落点 ----
        d = math.hypot(x - ST["pos"][0], y - ST["pos"][1])
        move = d / 5.0
        ST["pos"] = (x, y)
        ST["move_m"] += d
        ST["move_s"] += move
        ST["vt"] += move

        if p == "/measure":
            ST["measures"] += 1
            sw = 0.0
            if ch != ST["channel"]:
                sw = 1.0
                ST["switch_s"] += sw
                ST["vt"] += sw
            ST["channel"] = ch
            ST["measure_s"] += 5.0
            ST["vt"] += 5.0

            src = next((s for s in ST["sources"] if s["ch"] == ch), None)
            if src is None or ch in ST["cleared"]:
                res = {"measure_result": "no_signal"}
            else:
                dd = math.hypot(src["x"] - x, src["y"] - y)
                if dd > src["r"]:
                    res = {"measure_result": "no_signal"}
                elif dd <= 5.0:
                    res = {"measure_result": "near"}
                else:
                    brg = (math.degrees(math.atan2(src["y"] - y, src["x"] - x))) % 360.0
                    brg = (brg + svd_error(x, y)) % 360.0
                    res = {"measure_result": "direction", "svd_deg": round(brg, 2)}
            base.update(res)
            base["virtual_time_s"] = round(ST["vt"], 6)
            self._send(200, base)
            return

        # ---- /clear ----
        ST["clears"] += 1
        src = next((s for s in ST["sources"] if s["ch"] == ch), None)
        hit = src is not None and ch not in ST["cleared"] and \
            math.hypot(src["x"] - x, src["y"] - y) <= 20.0
        cost = 5.0 if hit else 3.0
        ST["clear_s"] += cost
        ST["vt"] += cost
        if hit:
            ST["cleared"].add(ch)
        base.update({"clear_result": "success" if hit else "no_target_in_range",
                     "virtual_time_s": round(ST["vt"], 6)})
        self._send(200, base)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=20290)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--n", type=int, default=13)
    ap.add_argument("--directional", action="store_true")
    a = ap.parse_args()
    reset(a.seed, a.n, a.directional)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), H)
    print("mini Q3 simulator on 127.0.0.1:%d seed=%d n=%d" % (a.port, a.seed, a.n), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
