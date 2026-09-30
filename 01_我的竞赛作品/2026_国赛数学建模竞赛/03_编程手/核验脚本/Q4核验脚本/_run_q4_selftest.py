# -*- coding: utf-8 -*-
"""**Q4 自己的**离线自测驱动（不依赖 Q3 窗口的脚本，只借用共享 mock 的**原有模式**）。

为什么要另起一份（2026-09-13，按 `00_任务总控/窗口边界_给Q4窗口_2026-09-13.md`）：
  · 共享的 `核验脚本/_run_client_selftest.py` 是双方共用的。我在里面加过 `SECTOR_TEST`，
    但那会让**对方的自测**依赖我加进 `_mock_simulator.py` 的 `sector` 分支 ——
    对方一旦重写那个文件，他们的自测就会因为我而变红。**这个反向依赖必须由我去掉。**
  · 扇区探针回归改跑**我自己的** `_mini_sim_q4.py --fixed`（摆一个已知定向源），
    于是我不再依赖共享 mock 的 `sector` 分支；共享 mock 这边只按**原有模式**使用。

用法：
    py -3.11 _run_q4_selftest.py
    py -3.11 _run_q4_selftest.py --src <v2.0 目录>

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
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
SHARED = os.path.join(REPO, '03_编程手', '核验脚本')
MOCK = os.path.join(SHARED, '_mock_simulator.py')          # 共享件：只用它的原有模式
MY_SIM = os.path.join(HERE, '_mini_sim_q4.py')            # 我自己的：扇区探针用
DEFAULT_SRC = os.path.join(REPO, '03_编程手', 'MATLAB_Framework_v2.0')
MATLAB = r'D:\R2026a_Windows\bin\matlab.exe'
BASE = 20400 + (os.getpid() % 300)                        # 按 PID 错开，避免与别的窗口抢端口

CLIENT_MODES = ['ok', 'accepted_false', 'http400', 'http409', 'hang']
CLEAR_TESTS = [('homing', BASE + 10), ('ok', BASE + 11)]
# 三项都跑在共享 mock 的 **geo** 模式上（按真实几何回答；mock 的模式名就是 'geo'）
GEO_TESTS = [('homing_convergence', BASE + 12), ('sweep_clear', BASE + 13),
             ('phaseC_homing', BASE + 14)]
GEO_MODE = 'geo'
SECTOR_PORT = BASE + 15


def wait_port(port, timeout=20.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection(('127.0.0.1', port), 0.3):
                return True
        except OSError:
            time.sleep(0.15)
    return False


def dec(b):
    for enc in ('mbcs', 'cp936', 'utf-8'):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode('utf-8', 'replace')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=DEFAULT_SRC)
    ap.add_argument('--matlab', default=MATLAB)
    a = ap.parse_args()
    src = os.path.abspath(a.src)
    if not os.path.isdir(src):
        sys.exit('被测目录不存在: %s' % src)
    if not os.path.exists(a.matlab):
        sys.exit('找不到 MATLAB: %s' % a.matlab)
    print('被测目录: %s' % src)

    procs, mocks = [], []
    try:
        # 共享 mock 的**原有模式**
        for i, m in enumerate(CLIENT_MODES):
            mocks.append(([sys.executable, MOCK, '--mode', m, '--port', str(BASE + i)], BASE + i))
        for m, port in CLEAR_TESTS:
            mocks.append(([sys.executable, MOCK, '--mode', m, '--port', str(port)], port))
        for _, port in GEO_TESTS:
            mocks.append(([sys.executable, MOCK, '--mode', GEO_MODE, '--port', str(port)], port))
        # 我自己的：已知定向源场景
        mocks.append(([sys.executable, MY_SIM, '--port', str(SECTOR_PORT), '--fixed'], SECTOR_PORT))

        for cmd, port in mocks:
            procs.append(subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
        for _, port in mocks:
            if not wait_port(port):
                sys.exit('mock 未就绪: port=%d' % port)

        jobs = []
        for i, m in enumerate(CLIENT_MODES):
            jobs.append(("test_SimulatorClient_logging('%s', %d)" % (m, BASE + i), 'client/%s' % m))
        for m, port in CLEAR_TESTS:
            jobs.append(("test_clear_source_homing('%s', %d)" % (m, port), 'clear_source/%s' % m))
        for name, port in GEO_TESTS:
            jobs.append(("test_%s(%d)" % (name, port), name))
        jobs.append(("test_sector_probe(%d)" % SECTOR_PORT, 'sector_probe（我的模拟器）'))
        jobs.append(("test_optimize_route()", 'optimize_route'))
        jobs.append(("test_clip_to_domain()", 'clip_to_domain'))
        jobs.append(("test_Q4_extensions()", 'Q4_extensions（几何回归）'))

        calls = ['r%d = %s' % (i, e) for i, (e, _) in enumerate(jobs)]
        summary = ("fprintf('Q4SELFTEST_SUMMARY %s\\n', mat2str([" +
                   ' '.join('r%d' % i for i in range(len(jobs))) + ']))')
        cmd = '; '.join(calls) + '; ' + summary

        print('\n启动 MATLAB（单次会话跑 %d 项）...\n' % len(jobs), flush=True)
        r = subprocess.run([a.matlab, '-nosplash', '-sd', src, '-batch', cmd],
                           capture_output=True, timeout=1800)
        out = dec(r.stdout or b'') + dec(r.stderr or b'')
        try:
            with open(os.path.join(HERE, '_q4_selftest_result.txt'), 'w',
                      encoding='utf-8', newline='') as f:
                f.write(out)
        except OSError:
            pass

        m = re.search(r'Q4SELFTEST_SUMMARY \[([^\]]*)\]', out)
        if not m:
            print(out[-3000:])
            print('!! 未拿到 Q4SELFTEST_SUMMARY（MATLAB 退出码 %s）' % r.returncode)
            return 1
        flags = [x.strip().lower() in ('1', 'true') for x in m.group(1).split()]
        print('=' * 74)
        allok = True
        for (_, label), f in zip(jobs, flags):
            print('  %-30s %s' % (label, 'PASS' if f else 'FAIL'))
            allok = allok and f
        print('=' * 74)
        print('%d 项：%s' % (len(jobs), '全部通过' if allok else '有失败'))
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
