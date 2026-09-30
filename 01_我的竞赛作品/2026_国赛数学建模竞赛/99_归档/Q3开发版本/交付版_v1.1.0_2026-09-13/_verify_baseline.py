# -*- coding: utf-8 -*-
"""Q3 稳定基线：冻结快照自检 + 原位漂移检测。

两个用途，刻意合在一个脚本里（同一个 MANIFEST 是唯一权威）：

  ① 验快照本身没坏：      py -3.11 _verify_baseline.py
  ② 验原位是否已被改动：  py -3.11 _verify_baseline.py --live
     `--live` 拿 MANIFEST 去比 `03_编程手/MATLAB_Framework/` —— 这是**回退判据**：
     退出码 0 说明原位仍逐字节等于 `git tag q3-v1.0.0` 冻结下来的那一版。

退出码：0 = 全部一致；1 = 有差异/缺失（以 MANIFEST 为准）。

为什么用 Python 而不是 md5sum：`.bat` 必须纯 ASCII（cmd.exe + cp936 会拆行），
而 `md5sum` 是 Git Bash 的东西、cmd.exe 里不一定在 PATH 上。逻辑放 Python，`.bat` 只留一行。
"""
import argparse
import hashlib
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, 'MANIFEST.txt')

# 快照根 → 仓库原位（快照是 HelloMathModeling 的兄弟目录）
LIVE_DEFAULT = os.path.abspath(
    os.path.join(HERE, '..', 'HelloMathModeling', '03_编程手', 'MATLAB_Framework'))


def read_manifest(path):
    """MANIFEST.txt 每行：<md5>  *<相对路径>"""
    entries = []
    with open(path, 'r', encoding='utf-8') as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip('\n')
            if not line or line.startswith('#'):
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                print(f'[WARN] MANIFEST 第 {lineno} 行无法解析，已跳过: {line!r}')
                continue
            digest, rel = parts
            entries.append((digest, rel.lstrip('*').replace('\\', '/')))
    return entries


def md5_of(path):
    h = hashlib.md5()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def check(root, entries, label):
    ok = missing = changed = 0
    for digest, rel in entries:
        full = os.path.join(root, rel)
        if not os.path.isfile(full):
            print(f'  [MISSING] {rel}')
            missing += 1
            continue
        got = md5_of(full)
        if got != digest:
            print(f'  [CHANGED] {rel}\n             期望 {digest}\n             实际 {got}')
            changed += 1
        else:
            ok += 1
    print(f'\n{label}: 一致 {ok} ｜ 改动 {changed} ｜ 缺失 {missing} ｜ 共 {len(entries)}')
    return missing + changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--live', action='store_true',
                    help='比对原位 MATLAB_Framework（回退判据），默认只验快照自身')
    ap.add_argument('--live-root', default=LIVE_DEFAULT,
                    help='覆盖原位目录（仓库搬动时用）')
    args = ap.parse_args()

    if not os.path.isfile(MANIFEST):
        print(f'[FAIL] 找不到 MANIFEST.txt: {MANIFEST}')
        return 1
    entries = read_manifest(MANIFEST)
    if not entries:
        print('[FAIL] MANIFEST.txt 里没有任何条目')
        return 1

    bad = check(HERE, entries, '冻结快照自检')
    if bad:
        print('⇒ 快照本身已损坏。不要用它回退。')
        return 1
    print('⇒ 快照完好。')

    if not args.live:
        return 0

    print(f'\n---- 原位漂移检测 ----\n根目录: {args.live_root}')
    if not os.path.isdir(args.live_root):
        print('[FAIL] 原位目录不存在（仓库搬动过？用 --live-root 指定）')
        return 1
    drift = check(args.live_root, entries, '原位 vs 冻结基线')
    if drift:
        print('\n⇒ 原位已被改动（或残留了 .orig/.bak）。')
        print('   回退：跑同目录的 rollback_to_q3-v1.0.0.bat，')
        print('   或在仓库里 git checkout q3-v1.0.0 -- 03_编程手/MATLAB_Framework/')
        return 1
    print('\n⇒ 原位逐字节等于 git tag q3-v1.0.0 的冻结版本。未漂移。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
