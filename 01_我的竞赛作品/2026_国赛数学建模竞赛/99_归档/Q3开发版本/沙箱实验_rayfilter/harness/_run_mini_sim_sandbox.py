# -*- coding: utf-8 -*-
"""用迷你模拟器（`_mini_sim_q3.py`）离线跑 `main_Q3Q4` 并**量出耗时**。

为什么需要：真模拟器的演练次数虽不限，但一次要人工操作、且加密日志读不了；
本驱动用**确定性种子**离线复现同一批案例，可反复比较算法改动的效果，
量出 虚拟时间 / 清除比例 / 各分量构成 ⇒ 调优到目标均摊时间。

用法：
    py -3.11 _run_mini_sim.py                 # 默认 3 个种子
    py -3.11 _run_mini_sim.py --seeds 2026,7,99 --n 13
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

try:
    sys.stdout.reconfigure(errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
MATLAB_SRC = os.path.join(REPO, '03_编程手', 'MATLAB_Framework')
MINI = os.path.join(HERE, '_mini_sim_q3.py')
MATLAB = r'D:\R2026a_Windows\bin\matlab.exe'
PORT = 20311          # sandbox: avoid the shared 20290
REPORT = os.path.join(os.path.dirname(HERE), 'out', 'result.txt')


def kill_port(port):
    """【2026-09-12 修正】先把端口上的残留进程清掉。
    教训：上次驱动在 finally 之前崩了，留下一个**状态已跑完**的 mini-sim；
    下一次运行的 wait_port 看到端口通就以为自己的 sim 起来了，MATLAB 其实连到了旧 sim
    （其 /enter 会被 accepted=false 拒掉）⇒ 拿到"数字完全没变"的假结果。"""
    try:
        out = subprocess.run(['netstat', '-ano'], capture_output=True, text=True,
                             encoding='mbcs', errors='replace').stdout or ''
    except Exception:
        return
    import re
    pids = set()
    for ln in out.splitlines():
        if (':%d ' % port) in ln and 'LISTENING' in ln:
            m = re.search(r'(\d+)\s*$', ln.strip())
            if m:
                pids.add(m.group(1))
    for pid in pids:
        subprocess.run(['taskkill', '/PID', pid, '/F'], capture_output=True)


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
    for enc in ('utf-8', 'mbcs', 'cp936'):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode('utf-8', 'replace')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='2026,7,99')
    ap.add_argument('--n', type=int, default=13)
    ap.add_argument('--d', type=int, default=0, help='0=用 load_config 默认档；否则覆写网格间距')
    ap.add_argument('--r-outer', dest='r_outer', type=float, default=0.0,
                    help='0=用三角格（默认）；否则用径向布点，此值为外环半径（如 1500 / 1400 / 1300）')
    ap.add_argument('--src', default=None,
                    help='被测 .m 所在目录；默认 03_编程手/MATLAB_Framework。v2.0 工作用 --src 指过去')
    a = ap.parse_args()

    if a.src:
        globals()['MATLAB_SRC'] = os.path.abspath(a.src)
    if not os.path.isdir(MATLAB_SRC):
        sys.exit('被测目录不存在: %s' % MATLAB_SRC)
    print('被测目录: %s' % MATLAB_SRC)

    lines = []
    rows = []
    for seed in [int(s) for s in a.seeds.split(',')]:
        kill_port(PORT)
        time.sleep(0.3)
        sim = subprocess.Popen([sys.executable, MINI, '--port', str(PORT),
                                '--seed', str(seed), '--n', str(a.n)],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if not wait_port(PORT):
            sim.kill()
            print('迷你模拟器未就绪 (seed=%d)' % seed)
            continue
        # 【2026-09-13 修正】旧版把 `--d` 的值送到了**第 6 参数 `enter_wait_s`**，
        #   而不是第 5 参数 `grid_spacing` —— 文档却写着"覆写网格间距"。
        #   实测无副作用（迷你模拟器先起好，/enter 首次即成功，等待预算用不到），但属真错标，
        #   已按文档语义对齐：5=grid_spacing、6=enter_wait_s、7=r_outer。
        gs = ('%d' % a.d) if a.d else '[]'
        ro = ('%g' % a.r_outer) if a.r_outer else '[]'
        cmd = ("r = main_Q3Q4('Q3','TESTTEAM','MINI-{s}','http://127.0.0.1:{p}',{gs},[],{ro}); "
               "fprintf('MINI_DONE vt=%.2f cleared=%d', r.virtual_time, r.cleared_count)"
               ).format(s=seed, p=PORT, gs=gs, ro=ro)
        p = subprocess.run([MATLAB, '-nosplash', '-sd', MATLAB_SRC, '-batch', cmd],
                           capture_output=True, timeout=1800)
        out = dec(p.stdout or b'') + dec(p.stderr or b'')
        with open(os.path.join(os.path.dirname(HERE), 'out',
                               'matlab_%d.txt' % seed), 'w',
                  encoding='utf-8', newline='') as _fh:
            _fh.write(out)
        try:
            with urllib.request.urlopen('http://127.0.0.1:%d/__stats' % PORT, timeout=10) as r:
                st = json.loads(r.read().decode('utf-8'))
        except Exception as e:
            st = {'error': str(e)}
        sim.terminate()
        try:
            sim.wait(timeout=5)
        except Exception:
            sim.kill()

        tot = st.get('total_sources')
        cl = st.get('cleared')
        vt = st.get('virtual_time_s')
        bd = st.get('breakdown') or {}
        avg = (vt / cl) if (vt and cl) else None
        rows.append((seed, tot, cl, vt, avg, bd, st.get('uncleared_channels')))
        lines.append('===== seed=%d  n=%d =====' % (seed, a.n))
        lines.append('源总数 %s ｜ 已清除 %s ｜ 清除比例 %s' % (
            tot, cl, ('%.1f%%' % (100.0 * cl / tot)) if (tot and cl is not None) else '?'))
        lines.append('虚拟时间 %.1f s ｜ 均摊 %s' % (
            vt or 0, ('%.1f s/源' % avg) if avg else 'n/a'))
        lines.append('分量: 移动 %.0f ｜ 切换 %.0f ｜ 检测 %.0f ｜ 清除 %.0f ｜ 总移动 %.0f m' % (
            bd.get('move', 0), bd.get('switch', 0), bd.get('measure', 0),
            bd.get('clear', 0), st.get('move_m', 0)))
        lines.append('未清除频道: %s' % (st.get('uncleared_channels'),))
        if 'MINI_DONE' not in out:
            lines.append('⚠️ MATLAB 未正常收尾（可能异常退出）')
        lines.append('')

    print('\n'.join(lines))
    with open(REPORT, 'w', encoding='utf-8', newline='') as f:
        f.write('\n'.join(lines))
    # 汇总
    ok = [r for r in rows if r[4] is not None]
    if ok:
        print('=' * 72)
        print('均摊（%d 个种子）：%s' % (len(ok), ', '.join('%.0f s/源' % r[4] for r in ok)))
        print('平均均摊 %.1f s/源' % (sum(r[4] for r in ok) / len(ok)))
        cleared = [r[2] for r in ok if r[1]]
        totals = [r[1] for r in ok if r[1]]
        if totals:
            print('清除比例：%s' % ', '.join('%.0f%%' % (100.0 * c / t) for c, t in zip(cleared, totals)))
        print('报告：%s' % REPORT)
        print('=' * 72)
    return 0


if __name__ == '__main__':
    sys.exit(main())
