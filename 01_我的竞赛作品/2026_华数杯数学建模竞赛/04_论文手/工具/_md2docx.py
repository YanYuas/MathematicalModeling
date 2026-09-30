# -*- coding: utf-8 -*-
"""MD -> DOCX 转换（stdlib + python-docx，处理本项目的表格/标题/加粗/列表/LaTeX公式）"""
import re, sys
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from _tex2omml import latex_par_auto

def add_runs(par, text):
    # 先拆 **bold** 与 `code`，再处理单 *italic*，最后 \* -> *
    text = text.replace('\\*', '')  # 占位，防与 ** 冲突
    parts = re.split(r'(\*\*.*?\*\*|`[^`]*`)', text)
    for tok in parts:
        if not tok:
            continue
        if tok.startswith('**') and tok.endswith('**'):
            r = par.add_run(tok[2:-2].replace('', '*'))
            r.bold = True
        elif tok.startswith('`') and tok.endswith('`'):
            r = par.add_run(tok[1:-1].replace('', '*'))
            r.font.name = 'Consolas'
        else:
            seg = tok.replace('', '*')
            # 单星 italic：成对 *...*
            m = re.match(r'^\*(.+)\*$', seg)
            if m:
                r = par.add_run(m.group(1))
                r.italic = True
            else:
                par.add_run(seg)

def set_cn_font(doc):
    st = doc.styles['Normal']
    st.font.name = 'Times New Roman'
    st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

def main(md_path, out_path):
    doc = Document()
    set_cn_font(doc)
    lines = open(md_path, encoding='utf-8').read().split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s or s == '---':
            i += 1
            continue
        # LaTeX 显示公式 $$...$$
        if s == '$$' or s.startswith('$$'):
            buf = []
            if s.startswith('$$') and s != '$$':
                buf.append(s[2:].strip())
                i += 1
                while i < len(lines) and '$$' not in lines[i]:
                    buf.append(lines[i]); i += 1
                if i < len(lines): i += 1
            else:
                i += 1
                while i < len(lines) and lines[i].strip() != '$$':
                    buf.append(lines[i]); i += 1
                if i < len(lines): i += 1
            latex = '\n'.join(buf).strip()
            if latex:
                body = doc.element.body
                sectPr = body.find(qn('w:sectPr'))
                p = latex_par_auto(latex)
                if sectPr is not None:
                    sectPr.addprevious(p)
                else:
                    body.append(p)
            continue
        # 引用
        if s.startswith('>'):
            p = doc.add_paragraph()
            add_runs(p, s[1:].strip())
            for r in p.runs:
                r.italic = True
            p.paragraph_format.left_indent = Pt(18)
            i += 1
            continue
        # 标题
        m = re.match(r'^(#{1,6})\s+(.*)$', line)
        if m:
            p = doc.add_heading('', level=min(len(m.group(1)), 3))
            add_runs(p, m.group(2))
            i += 1
            continue
        # 表格
        if s.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s:\-|]+\|$', lines[i + 1].strip()):
            header = [c.strip() for c in s.strip('|').split('|')]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            ncol = len(header)
            tb = doc.add_table(rows=1 + len(rows), cols=ncol)
            tb.style = 'Table Grid'
            for j, c in enumerate(header):
                tb.cell(0, j).text = c
            for ri, row in enumerate(rows):
                for j in range(min(ncol, len(row))):
                    tb.cell(ri + 1, j).text = row[j]
            doc.add_paragraph()
            continue
        # 无序列表
        m = re.match(r'^\s*[-*]\s+(.*)$', line)
        if m:
            p = doc.add_paragraph(style='List Bullet')
            add_runs(p, m.group(1))
            i += 1
            continue
        # 有序列表
        m = re.match(r'^\s*(\d+)\.\s+(.*)$', line)
        if m:
            p = doc.add_paragraph(style='List Number')
            add_runs(p, m.group(2))
            i += 1
            continue
        # 普通段落
        p = doc.add_paragraph()
        add_runs(p, s)
        i += 1
    doc.save(out_path)
    print('OK ->', out_path)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
