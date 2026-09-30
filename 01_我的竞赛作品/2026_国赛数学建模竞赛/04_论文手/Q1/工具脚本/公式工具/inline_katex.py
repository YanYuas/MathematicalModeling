# -*- coding: utf-8 -*-
"""修正：将内联 <style> 中 KaTeX 字体的相对 url 替换为 base64 data URI。"""
import os, re, base64

# 【2026-09-12 修正】原为硬编码 `D:\MathModel\HelloMathModeling\04_论文手\Q1`
# —— 那是**另一台机器的路径**（本机仓库根为 `D:\YanYuas\MathematicalModeling\HelloMathModeling`），
# 重跑会失败或改到陈旧副本。改为按脚本位置推导（本脚本与其操作对象同在 `_公式工具/`）。
base = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(base, '问题一公式_LaTeX编辑器.html')
font_dir = os.path.join(base, 'katex', 'fonts')

html = open(html_path, encoding='utf-8').read()
fonts = {}

def load_woff2(m):
    name = m.group(1)
    if name not in fonts:
        p = font_dir + '\\' + name + '.woff2'
        fonts[name] = base64.b64encode(open(p, 'rb').read()).decode()
    return 'url(data:font/woff2;base64,' + fonts[name] + ')'

def fix_style(m):
    css = m.group(1)
    return '<style>' + re.sub(r'url\(fonts/([A-Za-z0-9_-]+)\.woff2\)', load_woff2, css) + '</style>'

# 只替换包含 KaTeX 字体的 <style> 块
new_html = re.sub(r'<style>((?:(?!</style>).)*KaTeX.*?)</style>', fix_style, html, count=1, flags=re.S)
open(html_path, 'w', encoding='utf-8').write(new_html)
print('字体内联数:', len(fonts))
print('最终 HTML 大小:', len(new_html.encode('utf-8')) // 1024, 'KB')
print('残留相对字体引用:', bool(re.search(r'url\(fonts/', new_html)))
