# -*- coding: utf-8 -*-
import os, re
# 【2026-09-12 修正】原为硬编码 `D:\MathModel\HelloMathModeling\04_论文手\Q1\...`
# —— 那是**另一台机器的路径**（本机仓库根为 `D:\YanYuas\MathematicalModeling\HelloMathModeling`），
# 重跑会失败或改到陈旧副本。改为按脚本位置推导（2026-09-12 本目录由 `Q1/` 上移至 `Q1/_公式工具/`）。
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '问题一公式_LaTeX编辑器.html')
html = open(p, encoding='utf-8').read()
html = re.sub(r",\s*url\(fonts/[^)]*\.woff\)\s*format\(['\"]woff['\"]\)", '', html)
html = re.sub(r",\s*url\(fonts/[^)]*\.ttf\)\s*format\(['\"]truetype['\"]\)", '', html)
open(p, 'w', encoding='utf-8').write(html)
print('剩余 fonts/ 引用:', len(re.findall(r'url\(fonts/', html)))
print('HTML 大小:', len(html.encode('utf-8')) // 1024, 'KB')
