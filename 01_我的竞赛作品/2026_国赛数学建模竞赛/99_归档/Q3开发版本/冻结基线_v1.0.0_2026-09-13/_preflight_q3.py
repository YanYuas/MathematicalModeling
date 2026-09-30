# -*- coding: utf-8 -*-
"""Q3 正式测试 · 赛前预检（GO / NO-GO）。

赛题时间窗极窄（附件1 §4.2：倒计时 5 s → 25 分钟窗口 → /enter 后最多 20 分钟），
三次正式测试**不可重来**。跑之前用这个脚本把"能提前发现的全发现掉"。

检查项（任一 FAIL ⇒ NO-GO）：
  1. 模拟器在线         —— TCP 127.0.0.1:2026 可连
  2. 无残留 MATLAB      —— 上一局没退出会抢资源/写同一个 logs
  3. MATLAB 可执行文件  —— R2026a 优先，回退 R2022b（与 一键_跑Q3.bat 同一逻辑）
  4. 交付树未漂移       —— 受测版本必须逐字节等于冻结基线（否则成绩对应的是另一份代码）
  5. 源码不含真实队号   —— 格式规范要求支撑材料隐去队号（违规即整题不计分）
  6. logs 可写 + 磁盘   —— 自记录日志要落盘（附件1 §4.6 明文要求）
  7. 时间预算           —— 距 2026-09-13 17:30 的剩余时间够不够跑一局

用法:  py -3.11 _preflight_q3.py [--port 2026] [--team-id <队号>]
退出码: 0 = GO ｜ 1 = NO-GO
"""
import argparse
import datetime as dt
import os
import re
import shutil
import socket
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', 'HelloMathModeling'))
BASELINE = os.path.join(REPO, '03_编程手', 'MATLAB_Framework')
LOGS = os.path.join(BASELINE, 'logs')
MATLAB_CANDIDATES = [
    r'D:\R2026a_Windows\bin\matlab.exe',
    r'D:\R2022b_Windows\bin\matlab.exe',
]

# 一局的墙钟预算：MATLAB 启动 ~40 s + 程序运行上限。用于算"还来不来得及"
MINUTES_PER_GAME = 22
DEADLINE = dt.datetime(2026, 9, 13, 17, 30)

results = []


def record(ok, name, detail):
    results.append((ok, name, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}\n         {detail}")


def warn(name, detail):
    print(f"  [WARN] {name}\n         {detail}")


def check_simulator(port):
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=3):
            record(True, '模拟器在线', f'127.0.0.1:{port} 可连')
    except OSError as exc:
        record(False, '模拟器在线',
               f'127.0.0.1:{port} 连不上（{exc}）—— 先去启动模拟器并联网登录')


def check_stray_matlab():
    try:
        out = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq MATLAB.exe', '/NH', '/FO', 'CSV'],
            capture_output=True, text=True, timeout=20).stdout
    except Exception as exc:
        warn('无残留 MATLAB', f'查询失败，跳过：{exc}')
        return
    pids = re.findall(r'"MATLAB\.exe","(\d+)"', out)
    if not pids:
        record(True, '无残留 MATLAB', '没有 MATLAB.exe 在跑')
        return
    detail = (f'{len(pids)} 个 MATLAB.exe 在跑（PID {", ".join(pids)}）。'
              f'上一局没退干净会抢资源并混写 logs ⇒ 关掉再跑；'
              f'若是队友的窗口在跑，也请先停，正式测试期间只能有一个')
    record(False, '无残留 MATLAB', detail)


def check_matlab_exe():
    found = next((p for p in MATLAB_CANDIDATES if os.path.isfile(p)), None)
    if found:
        record(True, 'MATLAB 可执行文件', found)
    else:
        record(False, 'MATLAB 可执行文件',
               '两个候选路径都没有：' + ' ｜ '.join(MATLAB_CANDIDATES))


def check_drift():
    verifier = os.path.join(HERE, '_verify_baseline.py')
    if not os.path.isfile(verifier):
        warn('交付树未漂移', f'找不到 {verifier}，跳过')
        return
    r = subprocess.run([sys.executable, verifier, '--live'],
                       capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=60)
    if r.returncode == 0:
        record(True, '交付树未漂移', 'MATLAB_Framework 逐字节等于冻结基线 q3-v1.0.0')
    else:
        tail = [ln for ln in (r.stdout or '').splitlines() if ln.strip()][-4:]
        record(False, '交付树未漂移',
               '受测版本 ≠ 冻结基线！先回退：' + os.path.join(HERE, 'rollback_to_q3-v1.0.0.bat')
               + '\n         ' + ' / '.join(tail))


def check_team_id_leak(team_id):
    pat = team_id if team_id else None
    hits = []
    if not os.path.isdir(BASELINE):
        warn('源码不含真实队号', f'找不到 {BASELINE}，跳过')
        return
    for name in os.listdir(BASELINE):
        if not name.endswith(('.m', '.bat', '.md')):
            continue
        path = os.path.join(BASELINE, name)
        try:
            text = open(path, 'r', encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        # 无队号时退化为"10 位以上数字串"启发式扫描
        for m in re.finditer(pat if pat else r'\d{10,}', text):
            hits.append(f'{name}:{text[:m.start()].count(chr(10)) + 1}')
    target = team_id or '10 位以上数字串'
    if hits:
        record(False, '源码不含真实队号',
               f'命中 {target}：' + ', '.join(hits[:8]) +
               '  —— 格式规范要求支撑材料隐去队号，违规即整题不计分')
    else:
        record(True, '源码不含真实队号', f'未命中 {target}')


def check_logs_writable():
    try:
        os.makedirs(LOGS, exist_ok=True)
        probe = os.path.join(LOGS, '.preflight_probe')
        with open(probe, 'w', encoding='utf-8') as fh:
            fh.write('ok')
        os.remove(probe)
    except OSError as exc:
        record(False, 'logs 可写', f'{LOGS} 不可写：{exc}')
        return
    total, used, free = shutil.disk_usage(LOGS)
    gb = free / (1024 ** 3)
    if gb < 1.0:
        record(False, 'logs 可写 + 磁盘', f'可写，但磁盘只剩 {gb:.2f} GB')
    else:
        record(True, 'logs 可写 + 磁盘', f'可写 ｜ 磁盘剩余 {gb:.1f} GB')


def check_logs_team_id(team_id):
    """logs/ 里每局日志都写着真实队号 —— 它不在源码里，但打包时会一起进去。

    源码扫描（check_team_id_leak）只看 .m/.bat/.md，看不到 logs/。
    而 logs/ 就在交付目录里 ⇒ 手工压缩 MATLAB_Framework/ 即泄漏队号。
    """
    if not os.path.isdir(LOGS):
        return
    names = [n for n in os.listdir(LOGS) if n.endswith('.jsonl')]
    hit = [n for n in names if (team_id and team_id in n) or (not team_id and 'TESTTEAM' not in n)]
    if not hit:
        record(True, 'logs/ 队号脱敏', f'{len(names)} 个日志，未见真实队号文件名')
        return
    warn('logs/ 队号脱敏',
         f'{LOGS} 下有 {len(hit)}/{len(names)} 个日志文件名含真实队号。'
         f'程序交付包**必须排除 logs/**（交付用 pack_handover.py 会自动排除），'
         f'手工压缩整个目录会泄漏队号 —— 格式规范要求支撑材料隐去队号')


def check_time_budget():
    now = dt.datetime.now()
    left = (DEADLINE - now).total_seconds() / 60.0
    if left <= 0:
        record(False, '时间预算', f'已过截止 {DEADLINE:%Y-%m-%d %H:%M}，不能启动新测试')
    elif left < MINUTES_PER_GAME:
        record(False, '时间预算',
               f'距截止仅 {left:.0f} 分钟，不足一局（按 {MINUTES_PER_GAME} 分钟估）')
    else:
        cap = min(3, int(left // MINUTES_PER_GAME))
        record(True, '时间预算',
               f'距截止 {left:.0f} 分钟 ⇒ 最多还能跑 {cap} 局（按 {MINUTES_PER_GAME} 分钟/局估）')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=2026)
    ap.add_argument('--team-id', default=None, help='本队队号，用于泄漏扫描')
    args = ap.parse_args()

    print('=' * 68)
    print('  Q3 正式测试 · 赛前预检')
    print(f'  {dt.datetime.now():%Y-%m-%d %H:%M:%S}')
    print('=' * 68)

    check_simulator(args.port)
    check_stray_matlab()
    check_matlab_exe()
    check_drift()
    check_team_id_leak(args.team_id)
    check_logs_writable()
    check_logs_team_id(args.team_id)
    check_time_budget()

    bad = [r for r in results if not r[0]]
    print('=' * 68)
    if bad:
        print(f'  NO-GO —— {len(bad)} 项未通过，先修再跑：')
        for _, name, _ in bad:
            print(f'    - {name}')
        print('=' * 68)
        return 1
    print('  GO —— 全部通过，可以开跑')
    print('  提醒：先双击 一键_跑Q3.bat 输队号，**再**到模拟器点「开始测试」')
    print('=' * 68)
    return 0


if __name__ == '__main__':
    sys.exit(main())
