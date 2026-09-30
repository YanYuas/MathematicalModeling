# -*- coding: utf-8 -*-
"""汇总 `MATLAB_Framework*/logs/run_summary_*.json` → 一张表（Q4 再调试的入口）。

为什么需要（V2.0 工作说明 §四 缺口 #1/#4/#5 + 《Q4调优经验与补丁记录》T-1）：
  每局 `main_Q3Q4` 都会落一份机器可读的 `run_summary_<问题>_<时间戳>.json`
  （含虚拟时间、三路清除分布、探针次数、请求数、surrounding 自检、R_MEC 分布…）。
  本脚本把它们摊平成 CSV/表，供"改一版 → 跑一遍 → 直接对照"。

⚠️ **真机 / 回放必须分开口径**（memory 的 q3-verify-tooling-traps）：
  回放局与被测程序共用同一份日志目录。判别字段：`is_replay`（= sim_url 端口非 2026），
  以及 `team == "TESTTEAM"`。默认只统计 `--only real`。

用法：
    py -3.11 _collect_q4_runs.py                 # 真机局
    py -3.11 _collect_q4_runs.py --only replay   # 离线回放局
    py -3.11 _collect_q4_runs.py --only all
"""
import argparse
import glob
import json
import os
import sys
from collections import Counter

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
FRAMEWORKS = [os.path.join(REPO, '03_编程手', 'MATLAB_Framework'),
              os.path.join(REPO, '03_编程手', 'MATLAB_Framework_v2.0')]
OUT = os.path.join(HERE, '_q4_summary_table.md')


def load_all():
    rows = []
    for fw in FRAMEWORKS:
        for p in sorted(glob.glob(os.path.join(fw, 'logs', 'run_summary_*.json'))):
            try:
                with open(p, encoding='utf-8') as f:
                    d = json.load(f)
            except Exception:
                continue
            d['_path'] = p
            d['_fw'] = 'v1' if fw.endswith('MATLAB_Framework') else 'v2.0'
            rows.append(d)
    return rows


def fnum(x, nd=1):
    if x is None:
        return '-'
    try:
        return ('%.' + str(nd) + 'f') % float(x)
    except Exception:
        return str(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='real', choices=['real', 'replay', 'all'])
    ap.add_argument('--prob', default='Q4', choices=['Q3', 'Q4', 'all'])
    a = ap.parse_args()

    rows = load_all()
    if not rows:
        print('没找到 run_summary_*.json —— 先跑一局（真机或离线）')
        return 1

    def keep(d):
        if a.prob != 'all' and d.get('problem_type') != a.prob:
            return False
        rep = bool(d.get('is_replay'))
        if a.only == 'real':
            return not rep
        if a.only == 'replay':
            return rep
        return True

    sel = [d for d in rows if keep(d)]
    print('全量 %d 份；本次口径 only=%s prob=%s ⇒ %d 局'
          % (len(rows), a.only, a.prob, len(sel)))
    if not sel:
        print('（该口径下没有局。真机局要 sim_url 端口 = 2026）')
        return 0

    lines = []
    lines.append('# 运行汇总（%s / %s）' % (a.only, a.prob))
    lines.append('')
    lines.append('| 时间戳 | 队号 | 案例 | 清除 | T_vir(s) | T̄(s/源) | 墙钟(s) | N | direct/sweep/homing/兜底 | 探针 | 请求 | surrounding | R_MEC中位 |')
    lines.append('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for d in sel:
        mc = d.get('mode_count') or {}
        sur = d.get('surrounding_fail')
        lines.append('| %s | %s | %s | %s | %s | %s | %s | %s | %d/%d/%d/%d | %s/%s | %s | %s | %s |' % (
            d.get('stamp', '-'), d.get('team', '-'), d.get('case_code') or '-',
            d.get('cleared_count', '-'), fnum(d.get('virtual_time_s')), fnum(d.get('avg_time_s')),
            fnum(d.get('program_run_time_s'), 2), d.get('n_grid_points', '-'),
            mc.get('direct', 0), mc.get('sweep', 0), mc.get('homing', 0), mc.get('homing_fallback', 0),
            d.get('n_probe_channels', 0), d.get('n_probe_success', 0),
            d.get('n_requests', '-'),
            ('OK' if sur == 0 else ('FAIL=%s' % sur) if sur is not None else '-'),
            fnum(d.get('R_MEC_median'), 2)))
    lines.append('')

    # 汇总统计
    vt = [d['virtual_time_s'] for d in sel if d.get('virtual_time_s')]
    tb = [d['avg_time_s'] for d in sel if d.get('avg_time_s')]
    run = [d['program_run_time_s'] for d in sel if d.get('program_run_time_s')]
    req = [d['n_requests'] for d in sel if d.get('n_requests')]
    cnt = Counter()
    for d in sel:
        for k, v in (d.get('mode_count') or {}).items():
            cnt[k] += (v or 0)
    cleared = sum(1 for d in sel if (d.get('cleared_count') or 0) > 0)
    lines.append('**汇总**：%d 局 ｜ 有清除的局 %d ｜ 平均 T̄ %s s/源 ｜ 平均 T_vir %s s ｜ '
                 '平均墙钟 %s s ｜ 平均请求 %s' % (
                     len(sel), cleared, fnum(sum(tb) / len(tb)) if tb else '-',
                     fnum(sum(vt) / len(vt)) if vt else '-',
                     fnum(sum(run) / len(run), 2) if run else '-',
                     fnum(sum(req) / len(req), 0) if req else '-'))
    lines.append('**三路合计**：direct %d ｜ sweep %d ｜ homing %d ｜ homing断线转扫掠 %d'
                 % (cnt['direct'], cnt['sweep'], cnt['homing'], cnt['homing_fallback']))
    bad = [d for d in sel if (d.get('surrounding_fail') or 0) > 0]
    if bad:
        lines.append('⚠️ 有 %d 局的 surrounding 自检失败 > 0 —— 先查环带（陷阱 W1/W2）' % len(bad))

    txt = '\n'.join(lines)
    print('=' * 78)
    print(txt)
    print('=' * 78)
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        f.write(txt + '\n')
    print('已写入: %s' % OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
