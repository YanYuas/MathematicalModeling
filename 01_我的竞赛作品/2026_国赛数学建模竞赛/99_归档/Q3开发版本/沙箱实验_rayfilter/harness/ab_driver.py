# -*- coding: utf-8 -*-
"""沙箱 A/B 驱动（加固版，独立于仓库的 `_run_mini_sim.py`）。

为什么不直接用仓库那版（2026-09-13 实测踩到）：
  ① 它把迷你模拟器的 stdout 接到 `PIPE` 却从不读取 —— 管道写满即死锁；
  ② 每个种子复用同一个固定端口 20290，与其它窗口/残留实例互相踩；
  ③ 卡住时只表现为"这个种子特别慢"，不报错。

本驱动：每局独占端口、子进程输出直接落文件、端口先确认空闲、失败重试一次、
并打印一张对照表。**只写在沙箱里，不动仓库脚本。**
"""
import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

SB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MINI = os.path.join(SB, 'harness', '_mini_sim_q3.py')
OUT = os.path.join(SB, 'out')
MATLAB = r'D:\R2026a_Windows\bin\matlab.exe'
PORT_BASE = 20800          # 避开 Q3 的 20290 与 Q4 的 20300-20699（见 窗口边界_给Q3窗口）
GAME_TIMEOUT = 900


def port_free(port):
    try:
        with socket.create_connection(('127.0.0.1', port), 0.3):
            return False
    except OSError:
        return True


def wait_port(port, want_up, timeout=25.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if port_free(port) != want_up:
            return True
        time.sleep(0.2)
    return False


def listeners(port):
    try:
        out = subprocess.run(['netstat', '-ano'], capture_output=True, text=True,
                             encoding='mbcs', errors='replace').stdout or ''
    except Exception:
        return []
    pids = set()
    for ln in out.splitlines():
        if (':%d ' % port) in ln and 'LISTENING' in ln:
            m = re.search(r'(\d+)\s*$', ln.strip())
            if m:
                pids.add(m.group(1))
    return sorted(pids)


def clear_port(port):
    for pid in listeners(port):
        subprocess.run(['taskkill', '/PID', pid, '/F'], capture_output=True)
    wait_port(port, want_up=False, timeout=8)


def dec(b):
    for enc in ('utf-8', 'mbcs', 'cp936'):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode('utf-8', 'replace')


def run_one(src, seed, port):
    """跑一局，返回 dict（含 vt / 清除数 / 分量）。失败抛异常。"""
    clear_port(port)
    sim_log = open(os.path.join(OUT, 'sim_%d.log' % seed), 'w',
                   encoding='utf-8', errors='replace')
    sim = subprocess.Popen(
        [sys.executable, MINI, '--port', str(port), '--seed', str(seed), '--n', '13'],
        stdout=sim_log, stderr=subprocess.STDOUT)      # 落文件，绝不接 PIPE
    try:
        if not wait_port(port, want_up=True):
            raise RuntimeError('迷你模拟器未就绪 (port=%d seed=%d)' % (port, seed))

        # 注意：MATLAB 串里自带 %d / %.2f，所以这里**不能**用 Python 的 % 格式化拼接
        cmd = ("r = main_Q3Q4('Q3','TESTTEAM','MINI-" + str(seed) + "','http://127.0.0.1:"
               + str(port) + "',[],[],[]); "
               "fprintf('MINI_DONE vt=%.2f cleared=%d', r.virtual_time, r.cleared_count);")
        p = subprocess.run([MATLAB, '-nosplash', '-sd', src, '-batch', cmd],
                           capture_output=True, timeout=GAME_TIMEOUT)
        matlab_out = dec(p.stdout or b'') + dec(p.stderr or b'')
        with open(os.path.join(OUT, 'matlab_%s_%d.txt' %
                               (os.path.basename(src), seed)), 'w',
                  encoding='utf-8', errors='replace') as fh:
            fh.write(matlab_out)

        if 'MINI_DONE' not in matlab_out:
            raise RuntimeError('MATLAB 未正常收尾 (seed=%d)' % seed)

        with urllib.request.urlopen('http://127.0.0.1:%d/__stats' % port, timeout=15) as r:
            st = json.loads(r.read().decode('utf-8'))
        return st, matlab_out
    finally:
        sim.terminate()
        try:
            sim.wait(timeout=6)
        except Exception:
            sim.kill()
        sim_log.close()
        clear_port(port)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--tag', required=True)
    ap.add_argument('--seeds', default='2026,7,99')
    ap.add_argument('--port', type=int, default=PORT_BASE)
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    src = os.path.abspath(a.src)
    rows = []
    for i, seed in enumerate(int(s) for s in a.seeds.split(',')):
        port = a.port + i
        res = None
        for attempt in (1, 2):
            try:
                res, mout = run_one(src, seed, port)
                break
            except Exception as exc:
                print('  [%s seed=%d] 第 %d 次失败: %s' % (a.tag, seed, attempt, exc))
                clear_port(port)
        if res is None:
            rows.append({'seed': seed, 'ok': False})
            continue
        n_clear = sum(1 for k in res.get('uncleared_channels') or [])
        rows.append({
            'seed': seed, 'ok': True,
            'total': res.get('total_sources'),
            'cleared': res.get('cleared'),
            'vt': res.get('virtual_time_s'),
            'move': (res.get('breakdown') or {}).get('move'),
            'switch': (res.get('breakdown') or {}).get('switch'),
            'measure': (res.get('breakdown') or {}).get('measure'),
            'clear': (res.get('breakdown') or {}).get('clear'),
            'move_m': res.get('move_m'),
            'uncleared': res.get('uncleared_channels'),
        })
        skips = re.findall(r'(?:声线过滤跳过|跳过「已定位且已排队待清」的重复检测) (\d+) 次',
                           mout)
        rows[-1]['skips'] = [int(x) for x in skips]

    print('\n===== %s =====' % a.tag)
    hdr = '%-6s %8s %8s %10s %9s %8s %8s %8s %10s %s' % (
        'seed', '源总数', '已清除', '虚拟时间', '均摊', '移动', '检测', '切换', '总移动m', '跳过')
    print(hdr)
    for r in rows:
        if not r.get('ok'):
            print('%-6d  FAILED' % r['seed'])
            continue
        avg = (r['vt'] / r['cleared']) if r['cleared'] else float('nan')
        print('%-6d %8s %8s %10.1f %9.1f %8.0f %8.0f %8.0f %10.0f %s' % (
            r['seed'], r['total'], r['cleared'], r['vt'], avg,
            r['move'] or 0, r['measure'] or 0, r['switch'] or 0, r['move_m'] or 0,
            r.get('skips')))
    ok = [r for r in rows if r.get('ok') and r.get('cleared')]
    if ok:
        print('平均均摊 %.1f s/源 ｜ 平均虚拟 %.0f s' % (
            sum(r['vt'] / r['cleared'] for r in ok) / len(ok),
            sum(r['vt'] for r in ok) / len(ok)))

    with open(os.path.join(OUT, 'ab_%s.json' % a.tag), 'w', encoding='utf-8') as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)
    return 0 if all(r.get('ok') for r in rows) else 1


if __name__ == '__main__':
    sys.exit(main())
