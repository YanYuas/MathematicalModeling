# -*- coding: utf-8 -*-
"""只重绘【论文实际使用的两张旧版图】到 v2.1 标准，修掉"图内绘制的 Unicode 缺字"。

为什么只做两张：
  论文 图 5.1-2 ← 库 图5.1-10_交会定位区域构造（源码绘制 `θ₁ θ₂ S₁ S₂` 下标 ⇒ 方框）
  论文 图 5.1-3 ← 库 图5.1-3_Jung反例（源码绘制 `✅ ❌` emoji ⇒ 方框）
  论文 图 5.1-4 ← 库 图5.1-4_Jung夹逼（源码只有 `→ √ ≤`，均为常用字形 ⇒ 无缺字风险，不动）
  论文 图 5.1-5 ← 队友 v2.1 已修（fig5_1_5_vertex_filtering）✅
  论文 图 5.1-1 ← 库 99_旧版存档/Q1_MAIN_01_角域示意_优化版（另有来源，见 README）

做法（不手抄 100 行绘图代码，避免与源脚本漂移）：
  读 v1 源码 → 字符串级替换缺字字形 → exec 成模块 → 只调两个函数
配套三个 P0 修复：suptitle 置空、figsize>8 缩到 0.6×、mathtext.fontset='stix'
"""
import io
import os
import re
import sys
import warnings

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)

SRC = 'q1_figures_beautified.py'
SUFFIX = '_v2.1'

# 需要重绘的两张（函数名 → 说明）
TARGETS = [
    ('fig_5_1_3_jung_counterexample', '论文 图 5.1-3（等边三角形反例）'),
    ('fig_5_1_10_geometry_construction', '论文 图 5.1-2（两站交会定位区域构造）'),
]

# 字形替换：Unicode → mathtext / 纯文本（顺序敏感：长模式在前）
SUBS = [
    # 复合下标先替换，否则 S₁S₂ 会变成 $$ 相邻
    ('S₁S₂', r'$S_1S_2$'),
    ('θ₁', r'$\theta_1$'),
    ('θ₂', r'$\theta_2$'),
    ('S₁', r'$S_1$'),
    ('S₂', r'$S_2$'),
    ('V₁', r'$V_1$'),
    ('V₂', r'$V_2$'),
    ('V₃', r'$V_3$'),
    ('V₄', r'$V_4$'),
    # emoji（matplotlib 的 YaHei/SimHei 均无此字形 ⇒ 方框）
    ('✅ ', ''),   # 标签里本就写着「可覆盖」，emoji 是冗余
    ('❌ ', ''),   # 同上
    ('✅', ''),
    ('❌', ''),
]

RISK = re.compile(r'[₀-₉⁰-⁹ⁿ✅❌]')

src = io.open(SRC, encoding='utf-8').read()
# 去掉源码自带的 __main__ 运行块（不要一次跑全部图）
src = re.sub(r'\nif __name__ == [\'"]__main__[\'"]:.*\Z', '\n', src, flags=re.S)

for a, b in SUBS:
    src = src.replace(a, b)

ns = {'__name__': 'q1_beautified_v1', '__file__': os.path.join(HERE, SRC)}
exec(compile(src, SRC, 'exec'), ns)

# ---------- P0 修复补丁 ----------
plt.rcParams['mathtext.fontset'] = 'stix'          # P0-2
matplotlib.figure.Figure.suptitle = lambda self, *a, **k: None   # P0-3 无内嵌标题

_orig_subplots = plt.subplots


def subplots(*a, **k):
    fs = k.get('figsize')
    if fs and fs[0] > 8:                            # P0-1 figsize 过大 ⇒ 缩到 ~0.6×
        k['figsize'] = (round(fs[0] * 0.6, 2), round(fs[1] * 0.6, 2))
    return _orig_subplots(*a, **k)


plt.subplots = subplots

_orig_save = ns['save_fig']


def save_fig(fig, name, *a, **k):
    return _orig_save(fig, name + SUFFIX, *a, **k)


ns['save_fig'] = save_fig

# ---------- 跑 ----------
print('matplotlib %s | 目标 %d 张 | 缺字替换 %d 条' % (matplotlib.__version__, len(TARGETS), len(SUBS)))
bad_total = 0
for fname, desc in TARGETS:
    fn = ns.get(fname)
    if fn is None:
        print('  !! 源码中找不到 %s' % fname)
        continue
    body = re.search(r'\ndef %s\(.*?(?=\ndef |\Z)' % re.escape(fname), src, re.S)
    residual = sorted(set(RISK.findall(body.group(0)))) if body else []
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        fn()
        glyph = [str(x.message) for x in w if 'missing from font' in str(x.message).lower()
                 or 'Glyph' in str(x.message)]
    bad_total += len(glyph)
    print('  %-34s %s' % (fname, desc))
    print('     替换后残留风险字符: %s' % (''.join(residual) if residual else '无'))
    print('     matplotlib 缺字告警: %d 条 %s' % (len(glyph), ('| ' + glyph[0][:90]) if glyph else ''))

print('\n合计缺字告警: %d 条' % bad_total)
print('（0 条 = 无方框）')
