# -*- coding: utf-8 -*-
"""离线自测驱动：mock 同时起在多个端口 → 单次 MATLAB 会话跑完全部测试。

为什么这样组织：MATLAB 启动约 40 秒，每个测试各起一次会话太慢；
mock 占不同端口可并发存在，于是只需**一次** MATLAB 启动。

覆盖两组：
  ① SimulatorClient 合规自测（5 模式）：ok / accepted_false / http400 / http409 / hang
     —— 验证 日志落盘 / HTTP状态与accepted双检查 / 重试口径
  ② clear_source homing 路径回归（2 模式）：homing / ok
     —— 验证 pdist 已替换、svd_deg 守卫生效（2026-09-12 真实演练崩在这条路径）

退出码：0 = 全过；1 = 有失败。
"""
import argparse
import os
import re
import socket
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(errors='replace')
    sys.stderr.reconfigure(errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
MATLAB_SRC = os.path.join(REPO, '03_编程手', 'MATLAB_Framework')
MOCK = os.path.join(HERE, '_mock_simulator.py')

# (mock 模式, 端口, MATLAB 调用表达式模板)
CLIENT_MODES = ['ok', 'accepted_false', 'http400', 'http409', 'hang']
CLEAR_TESTS = [('homing', 20264), ('ok', 20265)]
GEO_TEST = ('geo', 20266)          # 按真实几何回答，验证 homing 收敛
GEO2_TEST = ('geo', 20267)         # 同模式另一端口，验证 sweep_clear 定向短走
GEO3_TEST = ('geo', 20268)         # 同模式第三端口，验证阶段 C 单方位 homing
BASE_PORT = 20259


def wait_port(port, timeout=20.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection(('127.0.0.1', port), 0.3):
                return True
        except OSError:
            time.sleep(0.15)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--matlab', default=r'D:\R2026a_Windows\bin\matlab.exe')
    ap.add_argument('--src', default=None,
                    help='被测 .m 所在目录；默认 03_编程手/MATLAB_Framework。v2.0 工作用 --src 指过去')
    a = ap.parse_args()

    if a.src:
        globals()['MATLAB_SRC'] = os.path.abspath(a.src)
    if not os.path.isdir(MATLAB_SRC):
        sys.exit('被测目录不存在: %s' % MATLAB_SRC)
    print('被测目录: %s' % MATLAB_SRC)

    if not os.path.exists(a.matlab):
        sys.exit('找不到 MATLAB: %s' % a.matlab)

    mocks = [(m, BASE_PORT + i) for i, m in enumerate(CLIENT_MODES)] + CLEAR_TESTS + \
            [GEO_TEST, GEO2_TEST, GEO3_TEST]

    procs, jobs = [], []
    try:
        for mode, port in mocks:
            p = subprocess.Popen([sys.executable, MOCK, '--mode', mode, '--port', str(port)],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            procs.append(p)
            print('mock 起: mode=%-15s port=%d' % (mode, port), flush=True)
        for mode, port in mocks:
            if not wait_port(port):
                sys.exit('mock 未就绪: mode=%s port=%d' % (mode, port))

        # ① 客户端自测（先跑 —— 其中 ok 模式要断言 server_count==1，必须排在其它请求之前）
        for i, (mode, port) in enumerate(mocks[:len(CLIENT_MODES)]):
            jobs.append(("test_SimulatorClient_logging('%s', %d)" % (mode, port),
                         'client/%s' % mode))
        # ② clear_source homing 回归
        for mode, port in CLEAR_TESTS:
            jobs.append(("test_clear_source_homing('%s', %d)" % (mode, port),
                         'clear_source/%s' % mode))
        # ③ homing 收敛回归（geo mock 按真实几何回答）
        jobs.append(("test_homing_convergence(%d)" % GEO_TEST[1], 'homing_convergence'))
        # ③b sweep_clear 定向短走（同 geo mock，另一端口）
        jobs.append(("test_sweep_clear(%d)" % GEO2_TEST[1], 'sweep_clear'))
        # ③c 阶段 C 单方位 homing
        jobs.append(("test_phaseC_homing(%d)" % GEO3_TEST[1], 'phaseC_homing'))
        # ④ 路径优化回归（纯计算，不需要 mock）
        jobs.append(("test_optimize_route()", 'optimize_route'))
        # ⑤ 圆域截断回归（纯计算，不需要 mock）
        #    【2026-09-13 新增】钉死真机事故 084008 频道 5：旧 `clip_to_domain` 只丢圆外顶点
        #    ⇒ 细长交会区退化成 2 点、R_MEC 假性偏小 ⇒ 误派发 sweep ⇒ 96 次无效 /clear。
        jobs.append(("test_clip_to_domain()", 'clip_to_domain'))

        calls = []
        for i, (expr, label) in enumerate(jobs):
            calls.append('r%d = %s' % (i, expr))
        summary = ("fprintf('SELFTEST_SUMMARY %s\\n', mat2str([" +
                   ' '.join('r%d' % i for i in range(len(jobs))) + ']))')
        cmd = '; '.join(calls) + '; ' + summary

        print('\n启动 MATLAB（单次会话，跑 %d 项测试）...\n' % len(jobs), flush=True)
        r = subprocess.run([a.matlab, '-nosplash', '-sd', MATLAB_SRC, '-batch', cmd],
                           capture_output=True, timeout=1200)
        # 【2026-09-12 修正】MATLAB `-batch` 的 stdout 在中文 Windows 上是 **cp936**（不是 UTF-8）
        # ⇒ 按 UTF-8 解码会得到 U+FFFD + 乱码。级联解码：先 UTF-8，失败回退 mbcs/cp936。
        def dec(b):
            for enc in ('utf-8', 'mbcs', 'cp936'):
                try:
                    return b.decode(enc)
                except Exception:
                    continue
            return b.decode('utf-8', 'replace')
        out = dec(r.stdout or b'') + dec(r.stderr or b'')
        try:
            with open(os.path.join(HERE, '_selftest_result.txt'), 'w',
                      encoding='utf-8', newline='') as f:
                f.write(out)
        except OSError:
            pass
        print(out)

        mres = re.search(r'SELFTEST_SUMMARY \[([^\]]*)\]', out)
        if not mres:
            print('!! 未拿到 SELFTEST_SUMMARY（MATLAB 退出码 %s）' % r.returncode)
            return 1
        # mat2str(logical) 给的是 [true false ...]（不是 [1 0]）——两种都认
        flags = [x.strip().lower() in ('1', 'true') for x in mres.group(1).split()]
        print('=' * 72)
        allok = True
        for (expr, label), f in zip(jobs, flags):
            print('  %-26s %s' % (label, 'PASS' if f else 'FAIL'))
            allok = allok and f
        print('=' * 72)
        print('%d 项测试: %s' % (len(jobs), '全部通过' if allok else '有失败'))
        return 0 if allok else 1
    finally:
        for p in procs:
            p.terminate()
            try:
                p.wait(timeout=5)
            except Exception:
                p.kill()


if __name__ == '__main__':
    sys.exit(main())
