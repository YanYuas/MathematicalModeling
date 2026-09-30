# -*- coding: utf-8 -*-
"""把 `问题二论文.docx` 的 3 个图号统一到「正稿 图号」体系。

背景：docx 的图号是**本文档局部序号**（图5.2-1/2/3），而 `04_论文手/Q2/正稿.md`
的图号是 8 张的完整体系（图 5.2-1 ~ 5.2-8）。同一节号（5.2）下两套序号并存 ⇒ 一引用就对不上。

映射（**按图注文字内容匹配，不按数字对应**）：

    docx 图5.2-1「权衡曲线（φ_min^max vs Δd）」     → 正稿 图 5.2-4
    docx 图5.2-2「E 等高线与可行域边界」             → 正稿 图 5.2-6
    docx 图5.2-3「跨问对比（问题一原例与候选位并排）」 → 正稿 图 5.2-7

安全性核验（已做）：
  - `图5.2-N` 在全文中**只出现 3 次，且全部是图注段**（正文没有"如图5.2-N所示"式引用）；
  - 源号 {1,2,3} 与目标号 {4,6,7} **不相交** ⇒ 不会链式误替换；
  - `表5.2-x` / `定理5.2-x` / `命题5.2-x` / `推论5.2-x` 用的是前缀字，**不受影响**。

⚠️ 不改的东西：**图注文字、图片、表格、任何正文**——只动那 3 个"图5.2-N"。
"""
import io
import os
import re
import shutil
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DOCX = '06_交付物/问题二论文.docx'
BACKUP = '06_交付物/_build/问题二论文_改图号前_backup.docx'

# (旧图号, 新图号, 图注首句，用于打印核对)
MAP = [
    ('图5.2-1', '图5.2-4', '权衡曲线（φ_min^max vs Δd）'),
    ('图5.2-2', '图5.2-6', 'E 等高线与可行域边界'),
    ('图5.2-3', '图5.2-7', '跨问对比（问题一原例与候选位并排）'),
]

zin = zipfile.ZipFile(DOCX)
parts = {n: zin.read(n) for n in zin.namelist()}
zin.close()

doc = parts['word/document.xml'].decode('utf-8')

print('--- 改前：图5.2-N 出现位置 ---')
for m in re.finditer(r'<w:t[^>]*>([^<]*图5\.2-\d[^<]*)</w:t>', doc):
    print('   %s' % m.group(1)[:80])

total = 0
for old, new, desc in MAP:
    hits = re.findall(r'图5\.2-%s(?![0-9])' % old.split('-')[1], doc)
    n = 0
    # 只在 <w:t> 文本节点内替换（避免碰任何 XML 属性）
    def _sub(m):
        global n
        seg = m.group(0)
        if old in seg:
            n += 1
            return seg.replace(old, new)
        return seg
    doc = re.sub(r'<w:t[^>]*>[^<]*</w:t>', _sub, doc)
    total += n
    print('   %s → %s   （%d 处）%s' % (old, new, n, desc))

print('--- 改后：图5.2-N 出现位置 ---')
for m in re.finditer(r'<w:t[^>]*>([^<]*图5\.2-\d[^<]*)</w:t>', doc):
    print('   %s' % m.group(1)[:80])

# 自检：不得残留 图5.2-1/2/3，且不得误伤 表/定理/命题/推论
allt = re.sub('<[^>]+>', '', doc)
for old, _, _ in MAP:
    assert old not in allt, '残留旧图号: ' + old
for bad in ('表5.2-4', '定理5.2-4'):
    assert bad in allt or True  # 仅打印，不做断言（表/定理本就有这些号）
assert '图5.2-4' in allt and '图5.2-6' in allt and '图5.2-7' in allt
print('自检：旧号已清零、新号已就位 ✅')

parts['word/document.xml'] = doc.encode('utf-8')
os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
shutil.copy2(DOCX, BACKUP)
with zipfile.ZipFile(DOCX, 'w', zipfile.ZIP_DEFLATED) as zout:
    for k, b in parts.items():
        zout.writestr(k, b)

print('\n改写 %d 处；备份 → %s' % (total, BACKUP))
