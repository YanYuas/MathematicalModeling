# -*- coding: utf-8 -*-
"""探测 Microsoft YaHei 对"图内绘制字符"的覆盖，列出所有缺字字符。

用途：不再手工猜哪些字符会变方框——直接把三个源脚本里"会画进图里"的字符
逐个查字体的 cmap，缺的即为方框来源。
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from matplotlib import font_manager
from matplotlib.ft2font import FT2Font

CANDIDATES = ['Microsoft YaHei', 'SimHei', 'Arial', 'DejaVu Sans']
SCRIPTS = [
    ('q1_figures_beautified.py', ['fig_5_1_1_baseline', 'fig_5_1_2_wedge_evolution',
                                 'fig_5_1_3_jung_counterexample', 'fig_5_1_4_jung_sandwich',
                                 'fig_5_1_5_vertex_filtering', 'fig_5_1_10_geometry_construction']),
]

fonts = {}
for name in CANDIDATES:
    try:
        path = font_manager.findfont(font_manager.FontProperties(family=name), fallback_to_default=False)
        fonts[name] = FT2Font(path)
    except Exception as e:
        print('!! 字体 %s 不可用: %s' % (name, e))

print('可用字体: %s\n' % ', '.join(fonts))


def missing_any(ch):
    """只要首选字体缺，就会落到下一个；全部缺才是真方框"""
    for f in fonts.values():
        if f.get_char_index(ord(ch)):
            return False
    return True


def missing_in(name, ch):
    f = fonts.get(name)
    return bool(f) and not f.get_char_index(ord(ch))


for script, funcs in SCRIPTS:
    if not os.path.exists(script):
        print('!! 缺脚本 %s' % script)
        continue
    src = io.open(script, encoding='utf-8').read()
    print('=' * 74)
    print('### %s' % script)
    for fn in funcs:
        m = re.search(r'\ndef %s\(.*?(?=\ndef |\Z)' % re.escape(fn), src, re.S)
        if not m:
            print('  !! 找不到 %s' % fn)
            continue
        body = m.group(0)
        # 只关心"会画进图"的字符：字符串字面量里的非 ASCII
        chars = set()
        for lit in re.findall(r"'([^'\n]*)'|\"([^\"\n]*)\"", body):
            s = lit[0] or lit[1]
            for ch in s:
                if ord(ch) > 127:
                    chars.add(ch)
        bad = sorted([c for c in chars if missing_any(c)], key=ord)
        also = sorted([c for c in chars if missing_in('Microsoft YaHei', c) and not missing_any(c)], key=ord)
        print('  %-34s 非ASCII字符 %2d 个 | 真缺字(全字体皆无) %d 个 %s | YaHei 缺但有兜底 %d 个 %s'
              % (fn, len(chars), len(bad), ''.join(bad) or '-', len(also), ''.join(also) or '-'))
        if bad:
            for c in bad:
                print('        U+%04X %s' % (ord(c), c))
