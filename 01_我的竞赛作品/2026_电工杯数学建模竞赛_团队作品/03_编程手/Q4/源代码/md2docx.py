"""
将 Q4论文内容.md 转换为格式化 Word 文档
"""
import re
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# -- 全局默认字体 --
style = doc.styles['Normal']
font = style.font
font.name = '宋体'
font.size = Pt(12)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

# -- 页面设置 --
for section in doc.sections:
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)


def add_heading_styled(text, level):
    """添加标题，黑体"""
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = '黑体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
        if level == 1:
            run.font.size = Pt(16)
        elif level == 2:
            run.font.size = Pt(14)
        else:
            run.font.size = Pt(13)
    return h


def add_para(text, bold_prefix=None):
    """添加段落，处理行内加粗"""
    p = doc.add_paragraph()
    # 处理 **bold** 标记
    parts = re.split(r'(\*\*.*?\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = p.add_run(part[2:-2])
            run.bold = True
        else:
            run = p.add_run(part)
        run.font.name = '宋体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
        run.font.size = Pt(12)
    return p


def set_cell_border(cell, **kwargs):
    """设置单元格边框"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('start', 'top', 'end', 'bottom', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            element = OxmlElement(f'w:{edge}')
            for attr in ['sz', 'val', 'color', 'space']:
                if attr in edge_data:
                    element.set(qn(f'w:{attr}'), str(edge_data[attr]))
            tcBorders.append(element)
    tcPr.append(tcBorders)


def add_table_from_lines(lines, col_widths=None):
    """从markdown表格行列表创建Word表格"""
    ncols = len(lines[0])
    nrows = len(lines)
    table = doc.add_table(rows=nrows, cols=ncols)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for i, row_cells in enumerate(lines):
        for j, cell_text in enumerate(row_cells):
            cell = table.cell(i, j)
            cell.text = ''
            p = cell.paragraphs[0]
            run = p.add_run(cell_text.strip())
            run.font.name = '宋体'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
            run.font.size = Pt(9)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # 表头加粗+灰色背景
            if i == 0:
                run.bold = True
                run.font.size = Pt(9.5)
                shading = OxmlElement('w:shd')
                shading.set(qn('w:fill'), 'D9E2F3')
                cell._tc.get_or_add_tcPr().append(shading)

    # 列宽
    if col_widths:
        for row in table.rows:
            for j, w in enumerate(col_widths):
                row.cells[j].width = Cm(w)

    return table


def parse_markdown(text):
    """解析markdown文本，生成Word文档"""
    lines = text.split('\n')

    i = 0
    table_buffer = []
    in_table = False
    in_quote = False

    while i < len(lines):
        line = lines[i]

        # 空行
        if line.strip() == '':
            if in_table and table_buffer:
                # 输出表格
                # 跳过表头分隔行 (|---|---|)
                header = table_buffer[0]
                rows = []
                for r in table_buffer[1:]:
                    if re.match(r'^\|[\s\-:|]+\|$', r.strip()):
                        continue
                    rows.append(r)
                # 解析每行
                parsed = []
                for r in [header] + rows:
                    cells = r.strip().strip('|').split('|')
                    parsed.append([c.strip() for c in cells])
                add_table_from_lines(parsed)
                table_buffer = []
                in_table = False
            i += 1
            continue

        # 表格行
        if line.strip().startswith('|'):
            in_table = True
            table_buffer.append(line)
            i += 1
            continue

        # 标题
        if line.startswith('# '):
            add_heading_styled(line[2:].strip(), 1)
        elif line.startswith('## '):
            add_heading_styled(line[3:].strip(), 2)
        elif line.startswith('### '):
            add_heading_styled(line[4:].strip(), 3)
        elif line.startswith('> '):
            # 引用
            quote_text = line[2:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1.5)
            # 处理加粗
            parts = re.split(r'(\*\*.*?\*\*)', quote_text)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    run = p.add_run(part[2:-2])
                    run.bold = True
                else:
                    run = p.add_run(part)
                run.font.name = '楷体'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')
                run.font.size = Pt(10.5)
                run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
        elif re.match(r'^\d+\.\s*\*\*', line):
            # 编号列表(加粗关键词)
            text = re.sub(r'^\d+\.\s*', '', line)
            p = doc.add_paragraph(style='List Number')
            parts = re.split(r'(\*\*.*?\*\*)', text)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    run = p.add_run(part[2:-2])
                    run.bold = True
                else:
                    run = p.add_run(part)
                run.font.name = '宋体'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
                run.font.size = Pt(12)
        else:
            add_para(line)

        i += 1

    # 残留表格
    if in_table and table_buffer:
        header = table_buffer[0]
        rows = [r for r in table_buffer[1:] if not re.match(r'^\|[\s\-:|]+\|$', r.strip())]
        parsed = [[c.strip() for c in r.strip().strip('|').split('|')] for r in [header] + rows]
        add_table_from_lines(parsed)


# ==== 主程序 ====
with open(r'C:\Users\29845\Desktop\问题4\Q4论文内容.md', 'r', encoding='utf-8') as f:
    content = f.read()

parse_markdown(content)

out_path = r'C:\Users\29845\Desktop\问题4\Q4论文内容.docx'
doc.save(out_path)
print(f'Word文档已生成: {out_path}')
