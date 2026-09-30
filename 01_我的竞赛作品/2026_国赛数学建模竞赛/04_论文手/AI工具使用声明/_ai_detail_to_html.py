# -*- coding: utf-8 -*-
"""
把 `04_论文手/AI工具使用详情.md` 转成**可打印的 HTML**（纯标准库，无第三方依赖）。
用法：双击同目录的 `导出_AI工具使用详情.bat`，或在浏览器打开生成的 HTML 后 Ctrl+P → 另存为 PDF。

为什么不用 pandoc / Word：本机无 pandoc；规定只要求产出 `AI 工具使用详情.pdf` 这一文件名与格式，
浏览器"打印为 PDF"可稳定得到该文件，且中文字体与表格不会错乱。
"""
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "AI工具使用详情.md")
OUT = os.path.join(HERE, "AI工具使用详情.html")


def esc(s):
    return html.escape(s, quote=False)


def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", s)      # 链接只留文字
    return s


def md_to_html(md):
    out, i, lines = [], 0, md.splitlines()
    n = len(lines)
    while i < n:
        ln = lines[i]

        # 表格
        if ln.startswith("|") and i + 1 < n and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1]):
            head = [c.strip() for c in ln.strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            out.append("<table><thead><tr>" + "".join("<th>%s</th>" % inline(h) for h in head)
                       + "</tr></thead><tbody>")
            for r in rows:
                out.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            out.append("</tbody></table>")
            continue

        # 标题
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            lv = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lv, inline(m.group(2)), lv))
            i += 1
            continue

        # 引用
        if ln.startswith(">"):
            body = []
            while i < n and lines[i].startswith(">"):
                body.append(lines[i].lstrip(">").strip())
                i += 1
            out.append("<blockquote>%s</blockquote>" % "<br>".join(inline(b) for b in body))
            continue

        # 列表
        if re.match(r"^\s*[-*]\s+", ln) or re.match(r"^\s*\d+\.\s+", ln):
            ordered = bool(re.match(r"^\s*\d+\.\s+", ln))
            tag = "ol" if ordered else "ul"
            items = []
            while i < n and (re.match(r"^\s*[-*]\s+", lines[i]) or re.match(r"^\s*\d+\.\s+", lines[i])):
                items.append(re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", lines[i]))
                i += 1
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(x) for x in items), tag))
            continue

        if ln.strip() == "---":
            out.append("<hr>")
            i += 1
            continue

        if ln.strip() == "":
            i += 1
            continue

        out.append("<p>%s</p>" % inline(ln))
        i += 1
    return "\n".join(out)


def main():
    if not os.path.exists(SRC):
        print("[错误] 找不到源文件: %s" % SRC)
        sys.exit(1)
    md = open(SRC, encoding="utf-8").read()
    body = md_to_html(md)
    doc = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>AI 工具使用详情</title>
<style>
  @page { size: A4; margin: 20mm 18mm; }
  body { font-family: "SimSun","宋体",serif; font-size: 12pt; line-height: 1.7;
         color: #000; max-width: 900px; margin: 0 auto; padding: 12mm 8mm; }
  h1 { font-family: "SimHei","黑体",sans-serif; font-size: 18pt; text-align: center; margin: 0 0 6mm; }
  h2 { font-family: "SimHei","黑体",sans-serif; font-size: 14pt; margin: 7mm 0 3mm; }
  h3 { font-family: "SimHei","黑体",sans-serif; font-size: 12.5pt; margin: 5mm 0 2mm; }
  table { border-collapse: collapse; width: 100%; margin: 3mm 0; font-size: 10.5pt; }
  th, td { border: 1px solid #444; padding: 2mm 2.5mm; vertical-align: top; }
  th { background: #ececec; font-family: "SimHei","黑体",sans-serif; }
  blockquote { margin: 3mm 0; padding: 2mm 4mm; border-left: 3px solid #999; background: #f7f7f7; }
  code { font-family: Consolas, monospace; font-size: 10pt; background: #f2f2f2; padding: 0 1px; }
  hr { border: none; border-top: 1px solid #bbb; margin: 6mm 0; }
  p { margin: 2mm 0; }
  @media print { body { padding: 0; } }
</style></head>
<body>
<p style="text-align:center;font-size:10pt;color:#555;">
  —— 打印说明：Ctrl+P → 目标打印机选「另存为 PDF」→ 文件名填 <b>AI 工具使用详情.pdf</b> → 保存 ——
</p>
""" + body + "\n</body></html>\n"
    open(OUT, "w", encoding="utf-8", newline="\n").write(doc)
    print("[完成] 已生成: %s" % OUT)
    print("       下一步：在浏览器打开它 → Ctrl+P → 另存为 PDF → 文件名填 'AI 工具使用详情.pdf'")


if __name__ == "__main__":
    main()
