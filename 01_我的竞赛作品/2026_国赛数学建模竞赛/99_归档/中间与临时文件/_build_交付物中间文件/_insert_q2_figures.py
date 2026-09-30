# -*- coding: utf-8 -*-
"""把 问题二论文.docx 的 3 张图补进去（纯标准库，不依赖 python-docx）

背景：该 docx 与 `问题一论文.docx` 同病——**有图注、无图**（`word/media/` 为空、
`<w:drawing>` 计数 0），而正文有 3 条图注。

⚠️ **docx 的图号与规范集图号不同名**，故**按图注文字的内容**匹配，不按数字对应：
    docx 图5.2-1「权衡曲线（φ_min^max vs Δd）」            ← 规范集 图5.2-4 fig5_2_4_tradeoff_curve.png
    docx 图5.2-2「E 等高线与可行域边界」                    ← 规范集 图5.2-6 fig5_2_6_E_contour.png
    docx 图5.2-3「跨问对比（问题一原例与候选位并排）」        ← 规范集 图5.2-7 fig5_2_7_cross_question.png

「（配图由编程手提供）」是占位提示，**不应出现在最终论文**——脚本会把图注里的这句删掉并留痕。
"""
import io
import os
import re
import shutil
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DOCX = '06_交付物/问题二论文.docx'
BACKUP = '06_交付物/_build/问题二论文_插图前_backup.docx'
FIGD = '04_论文手/Q2/配图'

# (图注定位串, 图片文件, 需从图注中删去的占位语)
FIG = [
    ('图5.2-1', 'fig5_2_4_tradeoff_curve.png', '（配图由编程手提供）'),
    ('图5.2-2', 'fig5_2_6_E_contour.png', '（配图由编程手提供）'),
    ('图5.2-3', 'fig5_2_7_cross_question.png', '（配图由编程手提供）'),
]

EMU_PER_CM = 360000
WIDTH_CM = 13.5
MAX_H_CM = 19.0


def png_size(path):
    with open(path, 'rb') as f:
        b = f.read(33)
    assert b[:8] == b'\x89PNG\r\n\x1a\n', path
    return int.from_bytes(b[16:20], 'big'), int.from_bytes(b[20:24], 'big')


specs = []
for cap, fn, note in FIG:
    p = os.path.join(FIGD, fn)
    if not os.path.exists(p):
        sys.exit('MISSING ' + p)
    w, h = png_size(p)
    cw, ch = WIDTH_CM, WIDTH_CM * h / w
    if ch > MAX_H_CM:
        ch, cw = MAX_H_CM, MAX_H_CM * w / h
    specs.append(dict(cap=cap, path=p, fn=fn, note=note,
                      cx=int(cw * EMU_PER_CM), cy=int(ch * EMU_PER_CM)))
    print('%-9s %5dx%-5d  %5.2f x %5.2f cm  %s' % (cap, w, h, cw, ch, fn))

zin = zipfile.ZipFile(DOCX)
parts = {n: zin.read(n) for n in zin.namelist()}
zin.close()

doc = parts['word/document.xml'].decode('utf-8')
rels = parts['word/_rels/document.xml.rels'].decode('utf-8')
ct = parts['[Content_Types].xml'].decode('utf-8')

if 'Extension="png"' not in ct:
    if '<Default Extension="jpeg"' in ct:
        ct = ct.replace('<Default Extension="jpeg"',
                        '<Default Extension="png" ContentType="image/png"/><Default Extension="jpeg"', 1)
    else:
        ct = ct.replace('</Types>', '<Default Extension="png" ContentType="image/png"/></Types>', 1)
    print('Content_Types: 已注册 png')


def drawing(rid, cx, cy, name, did):
    return (
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
        '<wp:inline distT="0" distB="0" distL="0" distR="0">'
        '<wp:extent cx="%d" cy="%d"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
        '<wp:docPr id="%d" name="%s"/>'
        '<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:nvPicPr><pic:cNvPr id="%d" name="%s"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
        % (cx, cy, did, name, did, name, rid, cx, cy)
    )


new_rels = []
for i, s in enumerate(specs, start=1):
    media = 'word/media/image_q2_%d.png' % i
    parts[media] = open(s['path'], 'rb').read()
    rid = 'rIdQ2Img%d' % i
    new_rels.append('<Relationship Id="%s" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image_q2_%d.png"/>' % (rid, i))
    s['rid'] = rid
    print('  + %s (%d B)' % (media, len(parts[media])))
rels = rels.replace('</Relationships>', ''.join(new_rels) + '</Relationships>')

# 定位图注段：形如 "图5.2-1 权衡曲线…"（半角空格，本 docx 的写法）
paras = list(re.finditer(r'<w:p[ >].*?</w:p>', doc, re.S))
for s in specs:
    s['at'] = None
    for m in paras:
        t = re.sub('<[^>]+>', '', m.group(0)).strip()
        if t.startswith(s['cap']) and re.match(r'^' + re.escape(s['cap']) + r'[\s　]', t):
            s['at'] = m.start()
            break
    if s['at'] is None:
        print('  !! 找不到图注段 ' + s['cap'])

todo = sorted([s for s in specs if s['at'] is not None], key=lambda x: x['at'], reverse=True)
for s in todo:
    blk = drawing(s['rid'], s['cx'], s['cy'], s['cap'].replace(' ', ''), 700 + specs.index(s) + 1)
    doc = doc[:s['at']] + blk + doc[s['at']:]
    print('  插入 %s @ 原文偏移 %d（自后向前）' % (s['cap'], s['at']))

# 删掉图注里的占位语「（配图由编程手提供）」
for s in specs:
    if s['note'] and s['note'] in doc:
        doc = doc.replace(s['note'], '')
        print('  图注占位语已删：%s %s' % (s['cap'], s['note']))

parts['word/document.xml'] = doc.encode('utf-8')
parts['word/_rels/document.xml.rels'] = rels.encode('utf-8')
parts['[Content_Types].xml'] = ct.encode('utf-8')

os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
shutil.copy2(DOCX, BACKUP)
with zipfile.ZipFile(DOCX, 'w', zipfile.ZIP_DEFLATED) as zout:
    for n, b in parts.items():
        zout.writestr(n, b)

print('\n完成：插入 %d/%d 张；备份 → %s' % (len(todo), len(specs), BACKUP))
