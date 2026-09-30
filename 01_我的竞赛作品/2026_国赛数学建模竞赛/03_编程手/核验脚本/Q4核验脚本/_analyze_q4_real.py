# -*- coding: utf-8 -*-
"""Q4 **真机**局的时间构成分析（从机器狗自记录 JSONL 复原虚拟时间账本）。

为什么需要：`run_summary_*.json` 只给总数（T_vir / T̄ / 三路分布），
要降 T̄ 必须知道钱花在哪：移动 / 检测 / 切频 / 清除各占多少，以及移动里面
"扫描巡游"与"去清除点"各占多少、巡游长度离 MST 下界多远。

口径（与附件1 §2 / 附件2 §4 一致，逐条从日志复原）：
  · 相邻两次**合法动作**的位移 / 5 = 移动耗时
  · 频道与"测向机当前频道"不同 ⇒ +1 s（只有 /measure 会切频道）
  · /measure 固定 +5 s；/clear 命中 +5 s、未命中 +3 s
  · /clear 不改当前频道

⚠️ 只统计**真机局**（session_start.base_url 端口 2026）——
   回放局与被测程序共用同一 logs 目录（见 memory 的 q3-verify-tooling-traps）。

用法：
    py -3.11 _analyze_q4_real.py                     # 扫两个框架目录
    py -3.11 _analyze_q4_real.py --dir <logs目录>
"""
import argparse
import glob
import json
import math
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, '_q4_real_breakdown.txt')


def load(path):
    recs = []
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except Exception:
                pass
    return recs


def analyse(path):
    recs = load(path)
    ses = next((r for r in recs if r.get('kind') == 'session_start'), {})
    url = ses.get('base_url', '')
    if ':2026' not in url:
        return None            # 非真机（回放）

    move_s = meas_s = switch_s = clear_s = 0.0
    move_m = 0.0
    n_meas = n_clear = n_sw = 0
    cur_ch = 1
    prev = None
    scan_m = scan_n = 0        # 扫描段（/measure）的移动
    clear_m = clear_n = 0      # 清除段（/clear）的移动
    bad = 0
    for r in recs:
        if r.get('kind') != 'request' or not r.get('accepted'):
            continue
        ep = r.get('endpoint', '')
        if ep not in ('/measure', '/clear'):
            continue
        rp = r.get('request_payload') or {}
        pos = rp.get('position') or {}
        x, y = float(pos.get('x', 0)), float(pos.get('y', 0))
        if prev is not None:
            d = math.hypot(x - prev[0], y - prev[1])
            move_m += d
            move_s += d / 5.0
            if ep == '/measure':
                scan_m += d
                scan_n += 1
            else:
                clear_m += d
                clear_n += 1
        prev = (x, y)

        if ep == '/measure':
            n_meas += 1
            ch = rp.get('channel')
            if ch != cur_ch:
                n_sw += 1
                switch_s += 1.0
                cur_ch = ch
            meas_s += 5.0
        else:
            n_clear += 1
            res = (r.get('response_payload') or {}).get('clear_result')
            if res == 'success':
                clear_s += 5.0
            elif res == 'no_target_in_range':
                clear_s += 3.0
            else:
                bad += 1
    vt = move_s + meas_s + switch_s + clear_s
    return dict(path=os.path.basename(path), url=url, vt=vt, move_s=move_s, meas_s=meas_s,
                switch_s=switch_s, clear_s=clear_s, move_m=move_m, n_meas=n_meas,
                n_clear=n_clear, n_sw=n_sw, scan_m=scan_m, clear_m=clear_m,
                scan_n=scan_n, clear_n=clear_n, bad=bad, team=ses.get('robot_id', ''))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', default=None)
    ap.add_argument('--top', type=int, default=12)
    a = ap.parse_args()

    dirs = [a.dir] if a.dir else [
        os.path.join(REPO, '03_编程手', 'MATLAB_Framework_v2.0', 'logs'),
        os.path.join(REPO, '03_编程手', 'MATLAB_Framework', 'logs')]
    paths = []
    for d in dirs:
        paths += glob.glob(os.path.join(d, 'robot_*.jsonl'))
    if not paths:
        print('没找到 robot_*.jsonl')
        return 1

    rows = [r for r in (analyse(p) for p in paths) if r]
    rows = [r for r in rows if r['n_meas'] > 50]
    if not rows:
        print('没有真机局（base_url 端口需为 2026）')
        return 0

    rows.sort(key=lambda r: r['path'])
    lines = []
    lines.append('Q4 真机局时间构成（虚拟时间；只统计 base_url 端口 2026 的局）')
    lines.append('')
    lines.append('%-34s %8s %8s %7s %7s %7s | %7s %7s | %6s %6s %6s' % (
        'log', 'T_vir', 'move%', 'meas%', 'swi%', 'clr%', 'scan_km', 'clr_km',
        'nMeas', 'nClr', 'nSw'))
    lines.append('-' * 128)
    for r in rows[-a.top:]:
        lines.append('%-34s %8.0f %7.1f%% %6.1f%% %6.1f%% %6.1f%% | %7.2f %7.2f | %6d %6d %6d' % (
            r['path'], r['vt'], 100 * r['move_s'] / r['vt'], 100 * r['meas_s'] / r['vt'],
            100 * r['switch_s'] / r['vt'], 100 * r['clear_s'] / r['vt'],
            r['scan_m'] / 1000, r['clear_m'] / 1000, r['n_meas'], r['n_clear'], r['n_sw']))
    lines.append('')

    n = len(rows)
    avg = lambda k: sum(r[k] for r in rows) / n
    vt = avg('vt')
    lines.append('=== 真机 %d 局均值 ===' % n)
    lines.append('T_vir %.0f s ｜ 移动 %.0f s (%.0f%%) ｜ 检测 %.0f s (%.0f%%) ｜ '
                 '切频 %.0f s (%.0f%%) ｜ 清除 %.0f s (%.0f%%)' % (
                     vt, avg('move_s'), 100 * avg('move_s') / vt,
                     avg('meas_s'), 100 * avg('meas_s') / vt,
                     avg('switch_s'), 100 * avg('switch_s') / vt,
                     avg('clear_s'), 100 * avg('clear_s') / vt))
    lines.append('总移动 %.1f km（扫描段 %.1f km / %d 次，清除段 %.1f km / %d 次）' % (
        avg('move_m') / 1000, avg('scan_m') / 1000, avg('scan_n'),
        avg('clear_m') / 1000, avg('clear_n')))
    lines.append('/measure %.0f 次 ｜ /clear %.0f 次 ｜ 切频 %.0f 次' % (
        avg('n_meas'), avg('n_clear'), avg('n_sw')))
    lines.append('')
    lines.append('降 T̄ 的杠杆预算（按上面占比，砍 X%% 只动那一项 ⇒ 总时长降 X%%×该占比）：')
    lines.append('  移动砍 30%% ⇒ T_vir -%.0f s' % (0.30 * avg('move_s')))
    lines.append('  切频砍 50%% ⇒ T_vir -%.0f s' % (0.50 * avg('switch_s')))
    lines.append('  检测砍 20%% ⇒ T_vir -%.0f s' % (0.20 * avg('meas_s')))

    txt = '\n'.join(lines)
    print(txt)
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        f.write(txt + '\n')
    print('\n已写入: %s' % OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
