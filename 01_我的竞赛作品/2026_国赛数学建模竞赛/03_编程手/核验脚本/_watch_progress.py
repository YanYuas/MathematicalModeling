# -*- coding: utf-8 -*-
"""进度哨兵：比对 Q3 / Q4 两个工作窗口的目录状态，只打印**增量**。

背景：Q3 与 Q4 各开一个窗口并行推进（`MATLAB_Framework` / `MATLAB_Framework_v2.0`）。
总控每隔一段时间要看一眼进度，但把两个目录全量列一遍太贵。

本脚本**只读** —— 绝不写这两个目录，否则会与那边的窗口抢文件。
状态快照落在系统 TEMP，不进仓库。

用法：
    py -3.11 _watch_progress.py            # 打印自上次以来的增量，并更新快照
    py -3.11 _watch_progress.py --reset    # 丢弃快照，重新建立基线
    py -3.11 _watch_progress.py --full     # 额外打印两目录的 .m 差异（Q4 增量清单）
"""
import argparse
import hashlib
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
STATE = os.path.join(os.environ.get('TEMP', '/tmp'), '_q3q4_watch_state.json')

TARGETS = [
    ('Q3', os.path.join(REPO, '03_编程手', 'MATLAB_Framework')),
    ('Q4', os.path.join(REPO, '03_编程手', 'MATLAB_Framework_v2.0')),
]
SKIP_DIRS = {'logs', '.git', '__pycache__'}
WATCH_EXT = ('.m', '.bat', '.md', '.py')


def _md5(p):
    with open(p, 'rb') as f:
        return hashlib.md5(f.read().replace(b'\r\n', b'\n')).hexdigest()[:10]


def scan(root):
    """返回 {相对路径: [md5, 大小, mtime]}。只收 WATCH_EXT 后缀，跳过 logs/。"""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(WATCH_EXT):
                continue
            full = os.path.join(dirpath, fn)
            try:
                st = os.stat(full)
                out[os.path.relpath(full, root).replace('\\', '/')] = [_md5(full), st.st_size, int(st.st_mtime)]
            except OSError:
                continue
    return out


def log_summary(root):
    """logs/ 是本窗口"是否真的跑过模拟器"的证据。给最新一个日志、总份数与行数。"""
    empty = (0, None, 0, 0, '')
    d = os.path.join(root, 'logs')
    if not os.path.isdir(d):
        return empty
    fs = []
    for dirpath, _, filenames in os.walk(d):
        for fn in filenames:
            if fn.endswith('.jsonl'):
                p = os.path.join(dirpath, fn)
                try:
                    fs.append((os.stat(p).st_mtime, p, os.path.getsize(p)))
                except OSError:
                    pass
    if not fs:
        return empty
    fs.sort()
    mt, p, sz = fs[-1]
    try:
        with open(p, 'r', encoding='utf-8', errors='replace') as f:
            n = sum(1 for _ in f)
    except OSError:
        n = 0
    import datetime
    return (len(fs), os.path.basename(p), sz, n, datetime.datetime.fromtimestamp(mt).strftime('%H:%M:%S'))


def load_state():
    try:
        with open(STATE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def save_state(st):
    try:
        with open(STATE, 'w', encoding='utf-8') as f:
            json.dump(st, f, ensure_ascii=False)
    except OSError:
        pass


def mdiff(root_a, root_b):
    """两目录 .m 的差异 = Q4 相对 Q3 的增量清单。"""
    a, b = scan(root_a), scan(root_b)
    only_b = sorted(set(b) - set(a))
    only_a = sorted(set(a) - set(b))
    changed = sorted(k for k in set(a) & set(b) if a[k][0] != b[k][0])
    return only_b, only_a, changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reset', action='store_true')
    ap.add_argument('--full', action='store_true')
    a = ap.parse_args()

    prev = None if a.reset else load_state()
    now = {}
    for tag, root in TARGETS:
        if not os.path.isdir(root):
            print('%s 目录不存在: %s' % (tag, root))
            continue
        now[tag] = scan(root)

    if prev is None:
        print('=== 建立基线（首次运行）===')
        for tag, _ in TARGETS:
            if tag in now:
                print('  %s: %d 个受监视文件' % (tag, len(now[tag])))
    else:
        any_change = False
        for tag, _ in TARGETS:
            if tag not in now:
                continue
            old, new = prev.get(tag, {}), now[tag]
            add = sorted(set(new) - set(old))
            rm = sorted(set(old) - set(new))
            mod = sorted(k for k in set(old) & set(new) if old[k][0] != new[k][0])
            if not (add or rm or mod):
                print('[%s] 无变化' % tag)
                continue
            any_change = True
            print('[%s] 新增 %d ｜ 修改 %d ｜ 删除 %d' % (tag, len(add), len(mod), len(rm)))
            for k in add:
                print('   + %s' % k)
            for k in mod:
                print('   ~ %s  (%d→%d B)' % (k, old[k][1], new[k][1]))
            for k in rm:
                print('   - %s' % k)
        if not any_change:
            print('（两窗口本次均无文件变动）')

    print('-' * 68)
    for tag, root in TARGETS:
        if not os.path.isdir(root):
            continue
        ls = log_summary(root)
        if ls[0] == 0:
            print('[%s] logs/: 无日志' % tag)
        else:
            print('[%s] logs/: %d 份，最新 %s  (%d B, %d 行, %s)' % (tag, ls[0], ls[1], ls[2], ls[3], ls[4]))

    if a.full:
        ob, oa, ch = mdiff(TARGETS[0][1], TARGETS[1][1])
        print('-' * 68)
        print('Q4 相对 Q3 的 .m 增量：仅 Q4 有 %d ｜ 仅 Q3 有 %d ｜ 内容不同 %d' % (len(ob), len(oa), len(ch)))
        for k in ob:
            print('   Q4 独有: %s' % k)
        for k in ch:
            print('   已改动: %s' % k)
        for k in oa:
            print('   仅 Q3 有（应关注）: %s' % k)

    save_state(now)
    return 0


if __name__ == '__main__':
    sys.exit(main())
