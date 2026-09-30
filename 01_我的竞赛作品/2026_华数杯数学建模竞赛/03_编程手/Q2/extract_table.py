# -*- coding: utf-8 -*-
import fitz, glob, os
base = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计"
pdfs = glob.glob(os.path.join(base, "*.pdf"))
target = [p for p in pdfs if 'Modern' in p]
out = open(r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\CLAUDE工作文件\编程手\Q2\table_output.txt", 'w', encoding='utf-8')
out.write('found: %r\n' % target)
doc = fitz.open(target[0])
out.write('pages %d\n' % doc.page_count)
for pno in range(doc.page_count):
    txt = doc[pno].get_text()
    up = txt.upper()
    if 'TABLE V' in up or 'WIRELENGTH UNDER' in up or 'PARQUET' in up:
        out.write('='*30 + ' page %d ' % pno + '='*30 + '\n')
        out.write(txt + '\n\n')
out.close()
