# -*- coding: utf-8 -*-
"""离线自测用的 **mock 模拟器**（不联网、不依赖真模拟器）。

用途：验证 `03_编程手/MATLAB_Framework/SimulatorClient.m` 在
「日志落盘 + HTTP状态/accepted 双检查 + 重试口径」上的行为是否合乎附件 2 §5.3/§12。

⚠️ **本 mock 不模拟时间物理**：它只按"每次 /measure +5 s"朴素累加 `virtual_time_s`，
   **不含移动耗时与频道切换耗时** ⇒ **不能用它评估策略的虚拟时间/平均定位清除时间**。
   那些数字只能从**真模拟器**的日志量（本文件的用途仅限：验证协议行为、重试口径、崩溃回归）。

关键点：**服务端记录收到的请求次数**，并用 GET /__stats 暴露
⇒ 测试才能断言"收到 400 时**没有**重试"这类行为（只看客户端自己是看不出来的）。

用法：
    py -3.11 _mock_simulator.py --mode ok            --port 20259
    py -3.11 _mock_simulator.py --mode accepted_false --port 20259
    py -3.11 _mock_simulator.py --mode http400        --port 20259
    py -3.11 _mock_simulator.py --mode http409        --port 20259

模式：
    ok              200 + accepted=true（/enter 给 remaining_real_duration_s=1200，其余推进 virtual_time_s）
    accepted_false  200 + accepted=false + virtual_time_s=0（附件2 §4.1：那个 0 不是当前虚拟时刻）
    http400         400 + JSON 体（结构错误）
    http409         409 + JSON 体（同 request_id 不同动作 / 并发）
    hang            不响应（用于验证传输层超时 → 可重试）
"""
import argparse
import json
import math
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# geo 模式用：真源位置 / 频道 / 有效接收半径（与 test_homing_convergence.m 约定一致）
GEO_SRC = (300.0, 400.0)
GEO_CHANNEL = 7
GEO_R_EFF = 1200.0

# sector 模式用：定向方向（度）。默认 90° ⇒ u = (0,1) ⇒ 扇区 = {y ≥ 400}。
DIR_DEG = 90.0

STATS = {"paths": [], "count": 0}
LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    mode = "ok"
    counter = {"virtual_time_s": 0}
    dir_count = 0          # homing 模式用：已返回过几次 direction

    def log_message(self, *args):
        pass  # 静音

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/__stats":
            with LOCK:
                self._send(200, dict(STATS))
            return
        self._send(404, {"error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            req = json.loads(raw.decode("utf-8"))
        except Exception:
            req = {}
        with LOCK:
            STATS["count"] += 1
            STATS["paths"].append(self.path)

        m = self.mode
        if m == "hang":
            time.sleep(60)
            return
        if m == "accepted_false":
            self._send(200, {"accepted": False, "real_timestamp_ms": int(time.time() * 1000),
                             "virtual_time_s": 0})
            return
        if m == "http400":
            self._send(400, {"accepted": False, "real_timestamp_ms": int(time.time() * 1000),
                             "virtual_time_s": 0, "error": "missing field"})
            return
        if m == "http409":
            self._send(409, {"accepted": False, "real_timestamp_ms": int(time.time() * 1000),
                             "virtual_time_s": 0, "error": "request_id reused with different action"})
            return

        # mode == geo：按**真实几何**回答，用于验证 homing 收敛
        #   真源固定在某点；/measure 返回指向它的真实方位（无噪声），距离 ≤5 m 返回 near；
        #   /clear 在 ≤20 m 返回 success。⇒ 一个收敛的 homing 应当**有限步内抵达并清掉**。
        if m == "geo":
            base = {"accepted": True, "real_timestamp_ms": int(time.time() * 1000)}
            base["virtual_time_s"] = self.counter["virtual_time_s"]
            pos = req.get("position") or {}
            ch = req.get("channel")
            x, y = float(pos.get("x", 0)), float(pos.get("y", 0))
            dx, dy = GEO_SRC[0] - x, GEO_SRC[1] - y
            d = math.hypot(dx, dy)
            if self.path == "/clear":
                ok = (ch == GEO_CHANNEL and d <= 20.0)
                base["clear_result"] = "success" if ok else "no_target_in_range"
                self.counter["virtual_time_s"] += 5 if ok else 3
            elif self.path == "/measure":
                if ch != GEO_CHANNEL:
                    base["measure_result"] = "no_signal"
                elif d <= 5.0:
                    base["measure_result"] = "near"
                elif d <= GEO_R_EFF:
                    base["measure_result"] = "direction"
                    base["svd_deg"] = round(math.degrees(math.atan2(dy, dx)) % 360.0, 2)
                else:
                    base["measure_result"] = "no_signal"
                self.counter["virtual_time_s"] += 5
            else:
                base["measure_result"] = "no_signal"
            self._send(200, base)
            return

        # mode == sector：**定向源**（Q4 扇区探针回归用）
        #   源在 GEO_SRC，定向方向 = DIR_DEG（单位向量 u）；有效覆盖 = 闭半平面 (P−G)·u ≥ 0。
        #   可测判据（附件2 §2.2 / 附录1(3)）：‖P−G‖ ≤ R_eff **且** (P−G)·u ≥ 0。
        #   near 同样要求在扇区内（附录2(9)）⇒ 盲侧贴到 1 m 也返回 no_signal。
        #   /clear 与朝向无关（附录2(8)）。
        if m == "sector":
            base = {"accepted": True, "real_timestamp_ms": int(time.time() * 1000)}
            base["virtual_time_s"] = self.counter["virtual_time_s"]
            pos = req.get("position") or {}
            ch = req.get("channel")
            x, y = float(pos.get("x", 0)), float(pos.get("y", 0))
            dx, dy = GEO_SRC[0] - x, GEO_SRC[1] - y
            d = math.hypot(dx, dy)
            ux = math.cos(math.radians(DIR_DEG))
            uy = math.sin(math.radians(DIR_DEG))
            in_sector = ((-dx) * ux + (-dy) * uy) >= -1e-9      # (P−G)·u ≥ 0，含边界
            if self.path == "/clear":
                ok = (ch == GEO_CHANNEL and d <= 20.0)
                base["clear_result"] = "success" if ok else "no_target_in_range"
                self.counter["virtual_time_s"] += 5 if ok else 3
            elif self.path == "/measure":
                if ch != GEO_CHANNEL or d > GEO_R_EFF or not in_sector:
                    base["measure_result"] = "no_signal"
                elif d <= 5.0:
                    base["measure_result"] = "near"
                else:
                    base["measure_result"] = "direction"
                    base["svd_deg"] = round(math.degrees(math.atan2(dy, dx)) % 360.0, 2)
                self.counter["virtual_time_s"] += 5
            else:
                base["measure_result"] = "no_signal"
            self._send(200, base)
            return

        # mode == ok
        if m == "homing":
            # 专供 clear_source 的 homing 回归测试：
            #   前 N 次 /measure 返回 direction（带 svd_deg），第 N+1 次起返回 near
            #   ⇒ 触发 homing 迭代 → 再触发 direct_clear → /clear 返回 success
            # 这样一次跑完：svd_of 守卫 / polygon_diameter 替换 / direct_clear 三条路径。
            base = {"accepted": True, "real_timestamp_ms": int(time.time() * 1000)}
            base["virtual_time_s"] = self.counter["virtual_time_s"] + 5
            self.counter["virtual_time_s"] += 5
            if self.path == "/clear":
                base["clear_result"] = "success"
            elif self.path == "/measure":
                Handler.dir_count += 1
                if Handler.dir_count <= 2:
                    base["measure_result"] = "direction"
                    base["svd_deg"] = 45.0
                else:
                    base["measure_result"] = "near"
            else:
                base["measure_result"] = "no_signal"
            self._send(200, base)
            return

        base = {"accepted": True, "real_timestamp_ms": int(time.time() * 1000)}
        if self.path == "/enter":
            base.update({"virtual_time_s": 0, "max_virtual_duration_s": 360000,
                         "max_real_duration_s": 1200, "remaining_real_duration_s": 1200})
        elif self.path == "/exit":
            base.update({"virtual_time_s": self.counter["virtual_time_s"],
                         "exit_reason": "user_exit"})
        else:
            self.counter["virtual_time_s"] += 5
            base.update({"virtual_time_s": self.counter["virtual_time_s"]})
            if self.path == "/measure":
                base.update({"measure_result": "no_signal"})
            else:
                base.update({"clear_result": "no_target_in_range"})
        self._send(200, base)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="ok")
    ap.add_argument("--port", type=int, default=20259)
    ap.add_argument("--dir-deg", dest="dir_deg", type=float, default=90.0,
                    help="sector 模式用：定向方向（度），覆盖 = 以该方向为外法向的闭半平面")
    a = ap.parse_args()
    Handler.mode = a.mode
    globals()["DIR_DEG"] = a.dir_deg
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print("mock simulator on 127.0.0.1:%d mode=%s" % (a.port, a.mode), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
