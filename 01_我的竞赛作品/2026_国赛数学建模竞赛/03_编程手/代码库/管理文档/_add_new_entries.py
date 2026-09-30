# -*- coding: utf-8 -*-
"""把新增的原位文件补进代码库并写台账（--update 只刷新已有条目，不会新增）。
只写 代码库/，不动原位。
"""
import hashlib
import io
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
LEDGER = os.path.join(HERE, '_副本台账.json')

NEW = [
    ('Q3/核心_MATLAB主线/generate_radial_grid.m',
     '03_编程手/MATLAB_Framework/generate_radial_grid.m', '核心'),
    ('Q3/核心_MATLAB主线/main_batch_Q3Q4.m',
     '03_编程手/MATLAB_Framework/main_batch_Q3Q4.m', '核心'),
    ('Q3/测试/cmp_grid_second_nearest.m',
     '03_编程手/MATLAB_Framework/cmp_grid_second_nearest.m', '测试'),
    ('Q3/测试/test_clip_to_domain.m',
     '03_编程手/MATLAB_Framework/test_clip_to_domain.m', '测试'),
]


def md5b(data):
    return hashlib.md5(data.replace(b'\r\n', b'\n')).hexdigest()


ledger = json.load(io.open(LEDGER, encoding='utf-8'))
have = set(e['库内路径'] for e in ledger)
added = 0
for lib, src, cat in NEW:
    if lib in have:
        print('  已在台账:', lib)
        continue
    src_abs = os.path.join(REPO, src.replace('/', os.sep))
    if not os.path.exists(src_abs):
        print('  !! 原位缺失:', src)
        continue
    dst_abs = os.path.join(HERE, lib.replace('/', os.sep))
    os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
    shutil.copyfile(src_abs, dst_abs)
    data = open(dst_abs, 'rb').read()
    ledger.append({
        '库内路径': lib,
        '原位路径': src,
        '类别': cat,
        'bytes': len(data),
        'md5': md5b(data),
    })
    added += 1
    print('  + %-46s %d bytes' % (lib, len(data)))

io.open(LEDGER, 'w', encoding='utf-8', newline='').write(
    json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
print('\n新增 %d 条；台账现共 %d 条' % (added, len(ledger)))
