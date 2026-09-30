# -*- coding: utf-8 -*-
"""把 图 5.1-1 ~ 5.1-5 插入 04_论文手/Q1/问题一论文.docx（纯标准库，不依赖 python-docx）

依据：04_论文手/Q1/论文组织方案.md §十五 配图计划 + 正稿.md 的图注原文。
插入位置：每张图插在对应【图注段】之前（中文排版：图在上、图注在下）。
"""
import os, re, shutil, sys, zipfile, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DOCX = '04_论文手/Q1/问题一论文.docx'
BACKUP = '04_论文手/Q1/_word_build/问题一论文_插图前备份.docx'

LIB = '03_编程手/图表库/Q1'
# 图注段定位串 → 图片源文件
FIG = [
    ('图 5.1-1', '99_旧版存档/04_主图优化版/Q1_MAIN_01_角域示意_优化版.png'),
    # 【2026-09-12 三次更新】逐字探测字体覆盖后确认：**只有 图 5.1-3 原来真有方框**
    #   —— 其源脚本把 `✅/❌` 画进 label（这两字符微软雅黑/SimHei/DejaVu 全都没有）。
    #   图 5.1-2（库 5.1-10）的下标 `₁₂` 有 DejaVu Sans 兜底，**不会方框**，
    #   但仍一并重绘，以与 v2.1 标准（figsize↓、无内嵌标题、mathtext）保持一致。
    #   重绘脚本：03_编程手/图表库/Q1/01_生图代码/_regen_paper_figs_v21.py
    ('图 5.1-2', '02_几何示意/fig5_1_10_geometry_construction_v2.1.png'),
    ('图 5.1-3', '02_几何示意/fig5_1_3_jung_counterexample_v2.1.png'),
    ('图 5.1-4', '02_几何示意/图5.1-4_Jung夹逼_v1.3.png'),
    # 图 5.1-5 由队友 v2.1 修复版替换（P0-1/4/7）
    ('图 5.1-5', '02_几何示意/fig5_1_5_vertex_filtering.png'),
]

EMU_PER_CM = 360000
WIDTH_CM = 13.5          # 正文插图宽度
MAX_H_CM = 19.0          # 高度上限（避免超页）

# ---------- 1. 读图片尺寸 ----------
def png_size(path):
    with open(path, 'rb') as f:
        b = f.read(33)
    assert b[:8] == b'\x89PNG\r\n\x1a\n', path
    w = int.from_bytes(b[16:20], 'big')
    h = int.from_bytes(b[20:24], 'big')
    return w, h

specs = []
for cap, rel in FIG:
    p = os.path.join(LIB, rel)
    if not os.path.exists(p):
        sys.exit('MISSING ' + p)
    w, h = png_size(p)
    cw = WIDTH_CM
    ch = cw * h / w
    if ch > MAX_H_CM:
        ch = MAX_H_CM
        cw = ch * w / h
    specs.append(dict(cap=cap, path=p, w=w, h=h,
                      cx=int(cw * EMU_PER_CM), cy=int(ch * EMU_PER_CM)))
    print('%s  %5dx%-5d  %5.2f x %5.2f cm  %s' % (cap, w, h, cw, ch, os.path.basename(p)))

# ---------- 2. 拆包 ----------
zin = zipfile.ZipFile(DOCX)
parts = {n: zin.read(n) for n in zin.namelist()}
zin.close()

doc = parts['word/document.xml'].decode('utf-8')
rels = parts['word/_rels/document.xml.rels'].decode('utf-8')
ct = parts['[Content_Types].xml'].decode('utf-8')

# ---------- 3. 注册 png 默认类型 ----------
if 'Extension="png"' not in ct:
    ct = ct.replace('<Default Extension="jpeg"',
                    '<Default Extension="png" ContentType="image/png"/><Default Extension="jpeg"', 1)
    if 'Extension="png"' not in ct:      # 没有 jpeg 默认项时的兜底
        ct = ct.replace('</Types>', '<Default Extension="png" ContentType="image/png"/></Types>', 1)
    print('Content_Types: 已注册 png')

# ---------- 4. 生成 media + 关系 + 绘制 XML ----------
def drawing(rid, cx, cy, name):
    return (
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
        '<wp:inline distT="0" distB="0" distL="0" distR="0">'
        '<wp:extent cx="%d" cy="%d"/>'
        '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
        '<wp:docPr id="%d" name="%s" descr="%s"/>'
        '<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:nvPicPr><pic:cNvPr id="%d" name="%s"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
        % (cx, cy, 900 + rid_num(rid), name, name, 900 + rid_num(rid), name, rid, cx, cy)
    )

def rid_num(rid):
    return int(re.sub(r'\D', '', rid) or 0)

new_rels = []
for i, s in enumerate(specs, start=1):
    media = 'word/media/image_q1_%d.png' % i
    parts[media] = open(s['path'], 'rb').read()
    rid = 'rIdQ1Img%d' % i
    new_rels.append('<Relationship Id="%s" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image_q1_%d.png"/>' % (rid, i))
    s['rid'] = rid
    s['media'] = media
    print('  + %s  (%d B)' % (media, len(parts[media])))

rels = rels.replace('</Relationships>', ''.join(new_rels) + '</Relationships>')

# ---------- 5. 插入图片段 ----------
paras = list(re.finditer(r'<w:p[ >].*?</w:p>', doc, re.S))

# 【关键】先按"图注在原文中的位置"排序，再自后向前插入
# —— 否则累计偏移量会把靠前的图注推错位（首版即栽在此）
for s in specs:
    s['at'] = None
    for m in paras:
        t = re.sub('<[^>]+>', '', m.group(0)).strip()
        # 【关键】必须匹配"图注段"而非"正文引用段"：
        #   图注形如 "图 5.1-1　示向度到…"（图号后是【全角空格】U+3000）
        #   正文引用形如 "图 5.1-1 给出单站角域的几何示意。"（图号后是半角空格）
        # 首版只判 startswith('图 5.1-1')，于是把正文引用段当成了图注，
        # 图被插到引用句之前（差一段）。此处收紧为全角空格。
        if re.match(r'^' + re.escape(s['cap']) + r'　', t):
            s['at'] = m.start()
            break
    if s['at'] is None:
        print('  !! 找不到图注段: ' + s['cap'])

todo = sorted([s for s in specs if s['at'] is not None], key=lambda x: x['at'], reverse=True)
inserted = 0
for s in todo:
    blk = drawing(s['rid'], s['cx'], s['cy'], s['cap'].replace(' ', ''))
    doc = doc[:s['at']] + blk + doc[s['at']:]
    inserted += 1
    print('  插入 %s @ 原文偏移 %d（自后向前）' % (s['cap'], s['at']))

parts['word/document.xml'] = doc.encode('utf-8')
parts['word/_rels/document.xml.rels'] = rels.encode('utf-8')
parts['[Content_Types].xml'] = ct.encode('utf-8')

# ---------- 6. 写回（保留备份） ----------
os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
shutil.copy2(DOCX, BACKUP)
with zipfile.ZipFile(DOCX, 'w', zipfile.ZIP_DEFLATED) as zout:
    for n, b in parts.items():
        zout.writestr(n, b)

print('\n完成：插入 %d/%d 张；备份 → %s' % (inserted, len(specs), BACKUP))
