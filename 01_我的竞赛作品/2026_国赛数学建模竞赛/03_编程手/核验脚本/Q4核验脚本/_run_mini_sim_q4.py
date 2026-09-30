# -*- coding: utf-8 -*-
"""用 Q4 迷你模拟器（`_mini_sim_q4.py`）离线跑 `main_Q3Q4('Q4', ...)` 并量出全套指标。

为什么需要（V2.0 工作说明 §四 缺口 #1）：
  真模拟器一次要人工操作、占据演练次数、加密日志读不了；Q4 又**零次端到端**。
  本驱动用确定性种子离线复现同一批案例 -> 可反复比较算法改动，量出
  虚拟时间 / 清除比例 / 三路清除分布 / 探针次数 / 请求数 / surrounding 自检结论，
  并把每局结果落成 CSV，供"再调试再优化"直接对照。

效率：**多个 mini-sim 起在不同端口 → 单次 MATLAB 会话跑完所有种子**
（MATLAB 启动约 40 s，逐种子各起一次会话太慢）。

用法：
    py -3.11 _run_mini_sim_q4.py                       # 默认 3 个种子
    py -3.11 _run_mini_sim_q4.py --seeds 2026,7,99 --n 13
    py -3.11 _run_mini_sim_q4.py --pos extreme --r-eff 1000   # 断言 5 最坏组合
    py -3.11 _run_mini_sim_q4.py --dir-frac 0           # Q3⊂=Q4 退化（纯全向）
"""
import argparse
import csv
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

try:
    # 控制台默认是 cp936；本文件含 ∈/ψ/×/‖ 等非 GBK 字符，强制 UTF-8 以免 --help 崩
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
DEFAULT_SRC = os.path.join(REPO, '03_编程手', 'MATLAB_Framework_v2.0')
MINI = os.path.join(HERE, '_mini_sim_q4.py')
MATLAB = r'D:\R2026a_Windows\bin\matlab.exe'
# 端口按本进程 PID 派生（**不是**固定 20300）：固定端口 + kill_port 会让两个窗口互相踩——
# 后起的杀掉先起的服务，先起的 MATLAB 连到别人的案例上，产出"看起来完全正常"的数字。
# 本项目 2026-09-13 已实测踩过（见 memory 的 q3-verify-tooling-traps），故这里按 PID 错开。
BASE_PORT = 20300 + (os.getpid() % 400)
REPORT = os.path.join(HERE, '_mini_sim_q4_result.txt')
CSVOUT = os.path.join(HERE, '_q4_offline_runs.csv')


def kill_port(port):
    """先清掉端口上的残留进程（教训见 `_run_mini_sim.py` 的同名函数）。"""
    try:
        out = subprocess.run(['netstat', '-ano'], capture_output=True, text=True,
                             encoding='mbcs', errors='replace').stdout or ''
    except Exception:
        return
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
    # MATLAB -batch 的 stdout 在中文 Windows 上是 cp936（不是 UTF-8）：先试 mbcs/cp936，
    # 否则整段日志会变成乱码（2026-09-13 实测）
    for enc in ('mbcs', 'cp936', 'utf-8'):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode('utf-8', 'replace')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='2026,7,99')
    ap.add_argument('--n', type=int, default=13)
    ap.add_argument('--d', type=int, default=0, help='0=用 load_config 默认档（1000）；否则覆写网格间距')
    ap.add_argument('--dir-frac', dest='dir_frac', type=float, default=1.0)
    ap.add_argument('--r-eff', dest='r_eff', type=float, default=0.0, help='0=随机[1000,1500]；1000=最坏')
    ap.add_argument('--pos', default='random', choices=['random', 'boundary', 'extreme'])
    ap.add_argument('--fixed', action='store_true', help='已知定向源场景（供 test_sector_probe 用）')
    ap.add_argument('--src', default=DEFAULT_SRC, help='被测 .m 所在目录')
    ap.add_argument('--matlab', default=MATLAB)
    a = ap.parse_args()

    src = os.path.abspath(a.src)
    if not os.path.isdir(src):
        sys.exit('被测目录不存在: %s' % src)
    if not os.path.exists(a.matlab):
        sys.exit('找不到 MATLAB: %s' % a.matlab)
    print('被测目录: %s' % src)

    seeds = [int(s) for s in a.seeds.split(',')]
    gs = ('%d' % a.d) if a.d else '[]'

    procs, ports = [], []
    try:
        for i, seed in enumerate(seeds):
            port = BASE_PORT + i
            kill_port(port)
            time.sleep(0.2)
            cmd = [sys.executable, MINI, '--port', str(port), '--seed', str(seed),
                   '--n', str(a.n), '--dir-frac', str(a.dir_frac), '--pos', a.pos]
            if a.r_eff:
                cmd += ['--r-eff', str(a.r_eff)]
            if a.fixed:
                cmd += ['--fixed']
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            procs.append(p)
            ports.append(port)
        for port in ports:
            if not wait_port(port):
                sys.exit('mini Q4 sim 未就绪: port=%d' % port)
        print('mini Q4 sim ×%d 就绪（端口 %s）' % (len(ports), ports))

        calls = []
        for i, (seed, port) in enumerate(zip(seeds, ports)):
            k = i + 1                       # MATLAB 变量用 1 起始的 r1..rN（r{0} 不是合法变量名）
            calls.append(
                "try, r%d = main_Q3Q4('Q4','TESTTEAM','MINI-%d','http://127.0.0.1:%d',%s,[],[]); "
                "catch ME, r%d = struct(); fprintf('Q4ERR %%d %%s\\n', %d, ME.message); end"
                % (k, seed, port, gs, k, k))
        summary = ("for i=1:%d, ri = eval(sprintf('r%%d', i)); "
                   "if isfield(ri,'cleared_count'), "
                   "fprintf('Q4ROW %%d %%d %%.2f %%.1f %%.1f %%d %%d %%d %%d %%d %%d %%d %%d %%d %%.2f %%d %%d\\n', i, "
                   "ri.cleared_count, ri.virtual_time, ri.avg_time, ri.program_run_time, "
                   "ri.n_grid_points, ri.mode_count.direct, ri.mode_count.sweep, ri.mode_count.homing, "
                   "ri.n_probe_channels, ri.n_probe_success, ri.n_requests, ri.n_measure, ri.n_clear, "
                   "ri.R_MEC_median, ri.surrounding_fail, ri.mode_count.homing_fallback); "
                   "else, fprintf('Q4ROW %%d MISSING\\n', i); end, end" % len(seeds))
        cmd = '; '.join(calls) + '; ' + summary
        print('\n启动 MATLAB（单次会话跑 %d 局）...\n' % len(seeds), flush=True)
        r = subprocess.run([a.matlab, '-nosplash', '-sd', src, '-batch', cmd],
                           capture_output=True, timeout=3600)
        out = dec(r.stdout or b'') + dec(r.stderr or b'')
        try:
            with open(os.path.join(HERE, '_mini_sim_q4_console.txt'), 'w',
                      encoding='utf-8', newline='') as f:
                f.write(out)
        except OSError:
            pass

        rows = []
        for m in re.finditer(r'Q4ROW (\d+) ([^\n]+)', out):
            i = int(m.group(1)) - 1
            parts = m.group(2).split()
            if parts and parts[0] == 'MISSING':
                rows.append({'seed': seeds[i], 'error': 'MATLAB 未返回结果'})
                continue
            vals = [float(x) for x in parts]
            rows.append(dict(zip(
                ['seed', 'cleared', 'T_vir', 'T_bar', 'T_run', 'N', 'n_direct', 'n_sweep',
                 'n_homing', 'n_probe_ch', 'n_probe_ok', 'n_req', 'n_measure', 'n_clear',
                 'R_MEC_med', 'surr_fail', 'n_homfb'],
                [seeds[i]] + vals)))

        # 真值取自各 mini-sim 的 /__stats（演练测试结束会给出总数，附件1 §4.6）
        for i, port in enumerate(ports):
            if i >= len(rows):
                break
            try:
                with urllib.request.urlopen('http://127.0.0.1:%d/__stats' % port, timeout=10) as rr:
                    st = json.loads(rr.read().decode('utf-8'))
            except Exception as e:
                st = {'error': str(e)}
            rows[i]['total'] = st.get('total_sources')
            rows[i]['n_dir'] = st.get('n_directional')
            rows[i]['cleared_true'] = st.get('cleared')
            rows[i]['clears_hit'] = st.get('clear_hit')
            rows[i]['clears_miss'] = st.get('clear_miss')
            rows[i]['move_m'] = st.get('move_m')
            rows[i]['breakdown'] = st.get('breakdown')
            rows[i]['measure_kinds'] = st.get('measure_kinds')
            t, c = st.get('total_sources'), st.get('cleared')
            rows[i]['ratio'] = (100.0 * c / t) if (t and c is not None) else None

        lines = []
        lines.append('Q4 离线批跑：n=%d  dir_frac=%.2f  pos=%s  r_eff=%s  d=%s'
                     % (a.n, a.dir_frac, a.pos, (a.r_eff or 'random'), (a.d or 'default')))
        lines.append('')
        hdr = ('seed  total dir cleared ratio  T_vir   T_bar  T_run   N  dir/swp/hom  probe  req  '
               'clear(hit/miss)  R_MEC中位  surr失败  homFB')
        lines.append(hdr)
        lines.append('-' * len(hdr))
        for r_ in rows:
            if 'error' in r_:
                lines.append('%-5s  %s' % (r_['seed'], r_['error']))
                continue
            ratio = ('%.1f%%' % r_['ratio']) if r_.get('ratio') is not None else 'n/a'
            lines.append(
                '%-5d %5s %3s %7s %6s %7.0f %7.1f %6.1f %4d  %d/%d/%d      %d/%d  %4d  %d/%d  '
                '%9.2f  %s  %s' % (
                    r_['seed'], r_.get('total'), r_.get('n_dir'), r_.get('cleared_true'), ratio,
                    r_['T_vir'], r_['T_bar'], r_['T_run'], int(r_['N']),
                    int(r_['n_direct']), int(r_['n_sweep']), int(r_['n_homing']),
                    int(r_['n_probe_ch']), int(r_['n_probe_ok']), int(r_['n_req']),
                    r_.get('clears_hit'), r_.get('clears_miss'),
                    r_['R_MEC_med'], int(r_['surr_fail']), int(r_.get('n_homfb') or 0)))
        lines.append('')

        ok = [r_ for r_ in rows if 'error' not in r_ and r_.get('ratio') is not None]
        if ok:
            lines.append('均摊 T_bar：%s  平均 %.1f s/源'
                         % (', '.join('%.0f' % r_['T_bar'] for r_ in ok),
                            sum(r_['T_bar'] for r_ in ok) / len(ok)))
            lines.append('清除比例：%s'
                         % ', '.join('%.0f%%' % r_['ratio'] for r_ in ok))
            tot_req = sum(r_['n_req'] for r_ in ok)
            lines.append('请求总数 %d（均 %.0f/局）｜三路合计 direct %d / sweep %d / homing %d / homing断线转扫掠 %d'
                         % (tot_req, tot_req / len(ok),
                            sum(int(r_['n_direct']) for r_ in ok),
                            sum(int(r_['n_sweep']) for r_ in ok),
                            sum(int(r_['n_homing']) for r_ in ok),
                            sum(int(r_['n_homfb'] or 0) for r_ in ok)))
            lines.append('探针：补测频道 %d，成功 %d'
                         % (sum(int(r_['n_probe_ch']) for r_ in ok),
                            sum(int(r_['n_probe_ok']) for r_ in ok)))
            lines.append('程序墙钟：%s（均 %.1f s）'
                         % (', '.join('%.1f' % r_['T_run'] for r_ in ok),
                            sum(r_['T_run'] for r_ in ok) / len(ok)))
            # 虚拟时间构成（承 Q3 口径：主成本应是移动）
            bd = [r_['breakdown'] for r_ in ok if r_.get('breakdown')]
            if bd:
                avg = lambda k: sum(b.get(k, 0) for b in bd) / len(bd)
                # 口径：分子是"每局的均值"，分母也必须是"每局的均值之和"（早先把分母写成
                # 局间总和，占比被压到 1/3，2026-09-13 修）
                tot = (avg('move') + avg('switch') + avg('measure') + avg('clear')) or 1.0
                lines.append('虚拟时间构成（均值）：移动 %.0f s (%.0f%%) ｜ 切频 %.0f s (%.0f%%) ｜ '
                             '检测 %.0f s (%.0f%%) ｜ 清除 %.0f s (%.0f%%)'
                             % (avg('move'), 100 * avg('move') / tot,
                                avg('switch'), 100 * avg('switch') / tot,
                                avg('measure'), 100 * avg('measure') / tot,
                                avg('clear'), 100 * avg('clear') / tot))
                mv = [r_['move_m'] for r_ in ok if r_.get('move_m') is not None]
                if mv:
                    lines.append('总移动距离（均值）：%.0f m' % (sum(mv) / len(mv)))
            bad = [r_ for r_ in ok if r_.get('ratio') is not None and r_['ratio'] < 100.0]
            lines.append('未 100%% 的局：%s'
                         % (', '.join('seed=%s(%.0f%%)' % (r_['seed'], r_['ratio']) for r_ in bad)
                            or '无 —— 全部 100%'))
            if any(int(r_['surr_fail']) > 0 for r_ in ok):
                lines.append('! 有局的 surrounding 自检失败 >0 —— 先查环带（陷阱 W1/W2）')

        report = '\n'.join(lines)
        print('=' * 78)
        print(report)
        print('=' * 78)
        with open(REPORT, 'w', encoding='utf-8', newline='') as f:
            f.write(report + '\n')

        keys = ['seed', 'total', 'n_dir', 'cleared_true', 'ratio', 'T_vir', 'T_bar', 'T_run',
                'N', 'n_direct', 'n_sweep', 'n_homing', 'n_homfb', 'n_probe_ch', 'n_probe_ok',
                'n_req', 'n_measure', 'n_clear', 'clears_hit', 'clears_miss',
                'R_MEC_med', 'surr_fail', 'move_m']
        with open(CSVOUT, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            w.writeheader()
            for r_ in rows:
                w.writerow({k: r_.get(k) for k in keys})
        print('报告: %s\n逐局 CSV: %s' % (REPORT, CSVOUT))
        return 0
    finally:
        for p in procs:
            p.terminate()
            try:
                p.wait(timeout=5)
            except Exception:
                p.kill()


if __name__ == '__main__':
    sys.exit(main())
