# -*- coding: utf-8 -*-
"""把全部**真机**演练局（端口 2026）抽成一张底表，供 Q3 演练数据汇总文档使用。
输出：_runs_table.tsv（制表符分隔，UTF-8）+ 控制台摘要。
只读日志，不改任何东西。
"""
import io
import json
import glob
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
LOGS = r"D:\YanYuas\MathematicalModeling\HelloMathModeling\03_编程手\MATLAB_Framework\logs"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_runs_table.tsv')


def load(path):
    ev = []
    for ln in io.open(path, encoding='utf-8', errors='replace'):
        try:
            d = json.loads(ln)
        except Exception:
            continue
        if d.get('kind') != 'request':
            if d.get('kind') == 'session_end':
                ev.append(('end', None, None, None, d))
            continue
        ep = d.get('endpoint')
        rp = d.get('request_payload') or {}
        rs = d.get('response_payload') or {}
        if ep == '/measure':
            ev.append(('m', rp.get('channel'), rp.get('position'), rs.get('measure_result'), rs))
        elif ep == '/clear':
            ev.append(('c', rp.get('channel'), rp.get('position'), rs.get('clear_result'), rs))
    return ev


def analyse(path):
    ev = load(path)
    # 网格档
    style = '?'
    for ln in io.open(path, encoding='utf-8', errors='replace'):
        try:
            d = json.loads(ln)
        except Exception:
            continue
        if d.get('kind') == 'grid_info':
            style = d.get('grid_style') or '?'
            break

    # 时间账
    move = meas = sw = clr = 0.0
    n_meas = n_sw = n_fail = 0
    prev = (0.0, 0.0); cur_ch = None
    cl = {}
    for k, ch, pos, res, rs in ev:
        if k == 'end':
            continue
        if pos is not None:
            p = (float(pos.get('x', 0)), float(pos.get('y', 0)))
            move += ((p[0] - prev[0]) ** 2 + (p[1] - prev[1]) ** 2) ** 0.5 / 5.0
            prev = p
        if k == 'm':
            n_meas += 1; meas += 5
            if ch != cur_ch:
                n_sw += 1; sw += 1.0        # 频道切换 1 s（仅在与上一测不同频道时计）
            cur_ch = ch
        else:
            clr += 5 if res == 'success' else 3
            cl.setdefault(ch, []).append(res)
            if res != 'success':
                n_fail += 1
    tvir = move + meas + sw + clr

    n_src = sum(1 for v in cl.values() if 'success' in v)
    n_direct = sum(1 for v in cl.values() if len(v) == 1 and v[0] == 'success')
    mx = max((len(v) for v in cl.values()), default=0)
    done = any(k == 'end' for k, *_ in ev)
    return dict(style=style, tvir=tvir, move=move, meas=meas, sw=sw, clr=clr,
                n_meas=n_meas, n_sw=n_sw, n_fail=n_fail, n_src=n_src,
                n_direct=n_direct, max_clear=mx, done=done)


rows = []
for f in glob.glob(os.path.join(LOGS, 'robot_*.jsonl')):
    try:
        d = json.loads(io.open(f, encoding='utf-8', errors='replace').readline())
    except Exception:
        continue
    if not d.get('base_url', '').endswith(':2026'):
        continue
    stamp = os.path.basename(f)[-19:-6]
    a = analyse(f)
    a['stamp'] = stamp
    rows.append(a)
rows.sort(key=lambda r: r['stamp'])

with io.open(OUT, 'w', encoding='utf-8', newline='') as fo:
    fo.write('时刻\t网格\t结束\t源数\t虚拟\t均摊\t移动\t检测\t切换\t清除\t检测次\t切换次\t失败次\tdirect\t最大clear\n')
    for r in rows:
        avg = r['tvir'] / r['n_src'] if r['n_src'] else float('nan')
        fo.write('%s\t%s\t%s\t%d\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%d\t%d\t%d\t%d\t%d\n'
                 % (r['stamp'], r['style'], 'Y' if r['done'] else 'N', r['n_src'],
                    r['tvir'], avg, r['move'], r['meas'], r['sw'], r['clr'],
                    r['n_meas'], r['n_sw'], r['n_fail'], r['n_direct'], r['max_clear']))

# ---- 摘要 ----
def stat(lst):
    if not lst:
        return (0, 0, 0)
    s = sorted(lst)
    return (len(s), s[len(s) // 2], sum(s) / len(s))


print('真机局数 %d ｜ 输出 %s' % (len(rows), OUT))
print()
done = [r for r in rows if r['done'] and r['n_src'] > 0]
print('有效局（有 session_end 且清除>0）：%d' % len(done))
print()
print('按网格档：')
for st in sorted(set(r['style'] for r in done)):
    g = [r for r in done if r['style'] == st]
    ns = [r['n_src'] for r in g]
    av = [r['tvir'] / r['n_src'] for r in g]
    tv = [r['tvir'] for r in g]
    print('  %-12s %2d 局 ｜ 源数 均值 %.1f（%d~%d）｜ 虚拟 均值 %.0f ｜ 均摊 均值 %.1f（%d~%d）'
          % (st, len(g), sum(ns) / len(ns), min(ns), max(ns),
             sum(tv) / len(tv), sum(av) / len(av), min(av), max(av)))
print()
print('清除方式（direct / 全部）：')
for st in sorted(set(r['style'] for r in done)):
    g = [r for r in done if r['style'] == st]
    td = sum(r['n_direct'] for r in g); tn = sum(r['n_src'] for r in g)
    print('  %-12s %d/%d = %.1f%%' % (st, td, tn, 100.0 * td / tn))
print()
mx = max(r['max_clear'] for r in done)
bad = [r['stamp'] for r in done if r['max_clear'] > 5]
print('最大单频道 /clear = %d ｜ 超过 5 次的局: %s' % (mx, bad if bad else '无'))
