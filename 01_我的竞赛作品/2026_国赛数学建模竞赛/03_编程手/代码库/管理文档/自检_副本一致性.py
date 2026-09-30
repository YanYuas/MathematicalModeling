# -*- coding: utf-8 -*-
"""核对 `代码库/` 的副本与**原位文件**是否一致（一条命令）。

为什么需要它：本项目曾在"去重"时把 `q1_main.py` 从 `01_生图代码/` 删掉，而那里的出图脚本
写着 `from q1_main import ...`（**依赖同目录 import**）⇒ **脚本当场跑不起来**。
⇒ 定下的规则是「**原位是权威，代码库是归集公示副本**」，那两者的**漂移就必须可检测**。

用法：
    py -3 自检_副本一致性.py            # 核对，列出漂移
    py -3 自检_副本一致性.py --update    # 以原位为准，刷新库内副本与台账
"""
import hashlib
import io
import json
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))   # 仓库根
LEDGER = os.path.join(HERE, '_副本台账.json')
UPDATE = '--update' in sys.argv


def md5b(data):
    return hashlib.md5(data.replace(b'\r\n', b'\n')).hexdigest()


def md5f(p):
    with open(p, 'rb') as f:
        return md5b(f.read())


if not os.path.exists(LEDGER):
    sys.exit('缺台账文件：%s（重跑收集脚本生成）' % LEDGER)

ledger = json.load(io.open(LEDGER, encoding='utf-8'))

ok = drift = gone = 0
rows = []
for r in ledger:
    lib = os.path.join(HERE, r['库内路径'].replace('/', os.sep))
    src = os.path.join(REPO, r['原位路径'].replace('/', os.sep))
    if not os.path.exists(src):
        gone += 1
        rows.append(('原位丢失', r['库内路径'], r['原位路径']))
        continue
    hs, hl = md5f(src), (md5f(lib) if os.path.exists(lib) else None)
    if hs == hl:
        ok += 1
    else:
        drift += 1
        rows.append(('漂移' if hl else '库内缺失', r['库内路径'], r['原位路径']))
        if UPDATE:
            os.makedirs(os.path.dirname(lib), exist_ok=True)
            shutil.copy2(src, lib)
            r['md5'] = hs
            r['bytes'] = os.path.getsize(src)

print('代码库副本自检 —— 共 %d 份' % len(ledger))
for tag, a, b in rows:
    print('  [%s] %s  ↔  %s' % (tag, a, b))
if not rows:
    print('  ✅ 全部一致（原位 == 库内）')

if UPDATE and rows:
    with io.open(LEDGER, 'w', encoding='utf-8', newline='') as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)
    print('已按原位刷新：%d 份副本 + 台账' % drift)

print('一致 %d ｜ 漂移 %d ｜ 原位丢失 %d' % (ok, drift, gone))

if UPDATE:
    # --update 的语义是"以原位为准修好"，修完即成功 ⇒ 退 0
    # （否则 `--update && 复核` 会被非零码短路，看起来像"修了但没好"）
    print('（--update 模式：已按原位对齐，退出码 0；如需严格核对请不带参数再跑一次）')
    sys.exit(0)

sys.exit(0 if not rows else 1)
