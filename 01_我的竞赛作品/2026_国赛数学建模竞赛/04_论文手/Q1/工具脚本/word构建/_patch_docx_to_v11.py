# -*- coding: utf-8 -*-
"""
问题一论文.docx —— 按正稿 v1.1 对齐的定点补丁（仅用标准库，无需 python-docx）

背景
----
`build_docx.py` 是**手写 prose 独立构建**（不是由 `正稿.md` 生成），且其 OUT 硬编码
`D:\\MathModel\\...`（错路径）。因此 Word 交付件长期静默偏离正稿，带着三侧联合审计
已判定为错的内容（A1「右端趋近等边三角形」🔴、A2【实测待填】🟡）。

本脚本不重建文档，只对 `word/document.xml` 做两类定点操作：
  1) 定点替换：按唯一文本串替换 `<w:t>` 内容 / 单元格内容 / 题注编号
  2) 定点插入：在锚点段落后插入新的段/公式/表格（第四层结构定理、§6.3 理论补充）
其余部件（styles/settings/theme/footer/numbering/TOC域）原样保留。

用法：python _patch_docx_to_v11.py [--dry]
"""
import os
import re
import sys
import shutil
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.path.abspath(os.path.join(HERE, "..", "问题一论文.docx"))
BAK = os.path.abspath(os.path.join(HERE, "..", "_word_build", "问题一论文_pre_v11_backup.docx"))

DRY = "--dry" in sys.argv
LOG = []


def log(msg):
    LOG.append(msg)
    print(msg)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------- 段落 / 表格 部件模板（与现有文档一致） ----------
BODY_PPR = ('<w:pPr><w:spacing w:line="360" w:lineRule="auto" w:before="0" w:after="0"/>'
            '<w:ind w:firstLineChars="200" w:firstLine="480"/><w:jc w:val="both"/></w:pPr>')
BODY_RPR = ('<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="宋体"/>'
            '<w:b w:val="0"/><w:sz w:val="24"/></w:rPr>')
BOLD_BODY_PPR = ('<w:pPr><w:spacing w:line="360" w:lineRule="auto" w:before="0" w:after="0"/>'
                 '<w:ind w:firstLineChars="200" w:firstLine="480"/><w:jc w:val="both"/></w:pPr>')
BOLD_BODY_RPR = ('<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="宋体"/>'
                 '<w:b/><w:sz w:val="24"/></w:rPr>')
CAP_PPR = '<w:pPr><w:spacing w:before="80" w:after="80"/><w:jc w:val="center"/></w:pPr>'
CAP_RPR = ('<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="宋体"/>'
           '<w:b/><w:sz w:val="21"/></w:rPr>')
FORM_PPR = ('<w:pPr><w:spacing w:line="360" w:lineRule="auto" w:before="60" w:after="60"/>'
            '<w:jc w:val="center"/></w:pPr>')
TOTAL_W = 9072


def P(text, kind="body"):
    """生成一个 w:p。kind: body | boldbody | subhead | form | cap"""
    if kind == "body":
        ppr, rpr = BODY_PPR, BODY_RPR
    elif kind == "boldbody":
        ppr, rpr = BOLD_BODY_PPR, BOLD_BODY_RPR
    elif kind == "subhead":
        ppr = ('<w:pPr><w:spacing w:line="360" w:lineRule="auto" w:before="120" w:after="60"/>'
               '<w:jc w:val="left"/></w:pPr>')
        rpr = BOLD_BODY_RPR
    elif kind == "form":
        ppr, rpr = FORM_PPR, BODY_RPR
    elif kind == "cap":
        ppr, rpr = CAP_PPR, CAP_RPR
    else:
        raise ValueError(kind)
    return '<w:p>%s<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r></w:p>' % (ppr, rpr, esc(text))


def TBL(header, rows):
    """生成一个 w:tbl。对齐现有文档：TableGrid + 居中 + 表头灰底加粗。"""
    ncol = len(header)
    w = TOTAL_W // ncol
    out = ['<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:type="auto" w:w="0"/>'
           '<w:jc w:val="center"/><w:tblLook w:firstColumn="1" w:firstRow="1" w:lastColumn="0"'
           ' w:lastRow="0" w:noHBand="0" w:noVBand="1" w:val="04A0"/></w:tblPr><w:tblGrid>']
    out += ['<w:gridCol w:w="%d"/>' % w] * ncol
    out.append('</w:tblGrid>')

    def row(cells, bold=False, shade=False):
        s = ['<w:tr>']
        for c in cells:
            s.append('<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="%d"/><w:vAlign w:val="center"/>' % w)
            if shade:
                s.append('<w:shd w:val="clear" w:fill="#D9D9D9"/>')
            s.append('</w:tcPr><w:p><w:pPr><w:spacing w:line="240" w:lineRule="auto"'
                     ' w:before="20" w:after="20"/><w:ind w:firstLineChars="0" w:firstLine="0"/>'
                     '<w:jc w:val="center"/></w:pPr><w:r><w:rPr>'
                     '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="宋体"/>')
            s.append('<w:b/>' if bold else '<w:b w:val="0"/>')
            s.append('<w:sz w:val="21"/></w:rPr><w:t xml:space="preserve">%s</w:t></w:r></w:p></w:tc>'
                     % esc(c))
        s.append('</w:tr>')
        return ''.join(s)

    out.append(row(header, bold=True, shade=True))
    for r in rows:
        out.append(row(r))
    out.append('</w:tbl>')
    return ''.join(out)


# ==================================================================
# 读入
# ==================================================================
zin = zipfile.ZipFile(DOCX)
doc = zin.read("word/document.xml").decode("utf-8")
orig_len = len(doc)


def wt_replace(old, new, required=True, count=1):
    """把 <w:t>old</w:t> 精确替换为 <w:t>new</w:t>。"""
    global doc
    o = '<w:t>%s</w:t>' % esc(old)
    if doc.count(o) == 0:
        # 兼容带 xml:space 的情形
        o = '<w:t xml:space="preserve">%s</w:t>' % esc(old)
    n = doc.count(o)
    if n == 0:
        if required:
            raise SystemExit("❌ 未找到待替换文本：%r" % old[:60])
        log("  (skip) 未找到：%r" % old[:50])
        return False
    if count is not None and n != count:
        log("  ⚠️ %r 出现 %d 次（期望 %d）" % (old[:40], n, count))
    doc = doc.replace(o, '<w:t xml:space="preserve">%s</w:t>' % esc(new))
    log("  ✓ 替换：%r → %r" % (old[:44], new[:44]))
    return True


def wt_sub(old, new, required=True):
    """在任意 <w:t> 内容**内部**做子串替换（用于长句中的“表5-x”“图5-x”引用）。"""
    global doc
    n = [0]

    def fix(m):
        inner = m.group(2)
        if old in inner:
            n[0] += inner.count(old)
            inner = inner.replace(old, new)
        return m.group(1) + inner + m.group(3)

    doc = re.sub(r'(<w:t[^>]*>)(.*?)(</w:t>)', fix, doc, flags=re.S)
    if n[0] == 0:
        if required:
            raise SystemExit("❌ 未找到子串：%r" % old)
        log("  (skip) 未找到子串：%r" % old[:50])
        return False
    log("  ✓ 子串替换 %d 处：%r → %r" % (n[0], old[:40], new[:40]))
    return True


def renumber_tables_figures():
    """把 表5-x / 图5-x 统一为 表 5.1-x / 图 5.1-x（表5-5..5-8 前移一位，表5-4 不编号）。"""
    global doc
    TBL_MAP = {1: "表 5.1-1", 2: "表 5.1-2", 3: "表 5.1-3",
               5: "表 5.1-4", 6: "表 5.1-5", 7: "表 5.1-6", 8: "表 5.1-7"}
    cnt = [0]

    def fix(m):
        inner = m.group(2)

        def t(mm):
            cnt[0] += 1
            return TBL_MAP[int(mm.group(1))]

        inner = re.sub(r"表5-([1-8])", t, inner)
        inner = re.sub(r"图5-([1-8])", lambda mm: "图 5.1-%s" % mm.group(1), inner)
        return m.group(1) + inner + m.group(3)

    doc = re.sub(r'(<w:t[^>]*>)(.*?)(</w:t>)', fix, doc, flags=re.S)
    log("  ✓ 编号统一：%d 处表号 + 图号" % cnt[0])


def insert_after(anchor_text, blocks, required=True):
    """在包含 anchor_text 的段落之后插入 blocks（XML 片段列表）。"""
    global doc
    i = doc.find(anchor_text)
    if i < 0:
        if required:
            raise SystemExit("❌ 未找到锚点：%r" % anchor_text[:60])
        log("  (skip) 锚点未找到：%r" % anchor_text[:50])
        return False
    j = doc.find("</w:p>", i)
    if j < 0:
        raise SystemExit("❌ 锚点段落未闭合")
    j += len("</w:p>")
    doc = doc[:j] + "".join(blocks) + doc[j:]
    log("  ✓ 在 %r 后插入 %d 个块" % (anchor_text[:30], len(blocks)))
    return True


print("=" * 70)
print("Q1 docx → 正稿 v1.1 定点补丁")
print("=" * 70)

# ------------------------------------------------------------------
print("\n[1] 摘要：三层 → 四层 + 精确数字")
# ------------------------------------------------------------------
old_abs = ("针对带 ±1° 测向误差的交会定位精度问题，本文将“示向度”严格升格为 2° 角域"
           "（有界不确定性模型），证明角域为两半平面之交，从而定位区域必为凸多边形；据此以“边界射线")
i = doc.find(old_abs)
if i < 0:
    # 引号可能是全角/半角不同，退化为按前缀定位整段 <w:t>
    m = re.search(r'<w:t[^>]*>针对带 ±1° 测向误差的交会定位精度问题.*?</w:t>', doc, re.S)
    if not m:
        raise SystemExit("❌ 未定位到摘要段")
    old_full = m.group(0)
    new_abs = ("针对带 ±1° 测向误差的交会定位精度问题，本文将“示向度”严格升格为 2° 角域（有界不确定性模型），"
               "证明角域为两半平面之交，从而定位区域必为凸多边形；据此以“边界射线两两求交＋落在所有角域内过滤"
               "＋单调链凸包”精确构造定位区域，并以旋转卡壳与 O(m²) 暴力双实现求其直径 D，两实现结果完全一致。"
               "针对“以 D 为直径的圆能否覆盖定位区域”，本文给出四层递进回答：以等边三角形为反例证明对一般凸区域"
               "不能覆盖；由 Thales 定理建立充要判据（覆盖 ⟺ 所有顶点处 ∠PXQ ≥ 90°）；指出正确做法是求最小包围圆，"
               "其半径由 Jung 定理严格夹在 [D/2, D/√3] 内，最坏缺口 2/√3 ≈ 15.5%，等边三角形取等；第四层给出结构定理"
               "——证明中心对称紧凸集必满足 γ ≡ 1，并观察到定位区域的两条对边来自同一检测点、夹角恰为 2ε，即定位区域是"
               "“2ε-近平行四边形”（中心对称形状的 O(ε) 扰动），故 γ = 1 + O(ε)，数值实验（数十万组配置）表明"
               "题设 ε=1° 下 γ ≤ 1.01 —— 等边三角形在本题区域族内不可达，直径圆实际上总能覆盖。基准算例"
               "（S₁=(0,0)、S₂=(600,0)、源 (300,500)、ε=1°）得 D = 39.598 m、R_MEC = 19.799 m、缺口比 γ = 1.000"
               "（该例下界取等、恰好覆盖）；全部实测算例均满足 Jung 夹逼关系，该关系同时充当实现的自动正确性检验。")
    doc = doc.replace(old_full, '<w:t xml:space="preserve">%s</w:t>' % esc(new_abs))
    log("  ✓ 摘要整段替换（旧长度 %d → 新长度 %d）" % (len(old_full), len(new_abs)))
else:
    raise SystemExit("摘要段定位方式需复核")

# ------------------------------------------------------------------
print("\n[1.5] 去掉“该图由编程手配图”（须在编号统一之前，按原始 图5-x 拼写匹配）")
for old, new in [
    ("（示意见图5-5，该图由编程手配图）", "（示意见图 5.1-5）"),
    ("（反例示意见图5-3，该图由编程手配图）", "（反例示意见图 5.1-3）"),
    ("（该图由编程手配图）", ""),
]:
    wt_sub(old, new, required=False)

print("\n[2] 表编号统一为 5.1-x，并同步正文引用")
# ------------------------------------------------------------------
# 先处理“参数设置”表：正稿中它不编号，故单独改写（避免被编号映射带偏）
wt_sub("参数设置见表5-4。", "参数设置见下表。", required=False)
wt_replace("表5-4  参数设置", "参数设置（不参与正文表编号）", required=False)
renumber_tables_figures()
# 编号映射完成后，再修题注里与正稿不一致的措辞
wt_replace("表 5.1-5  参数扫描结果与理论趋势对照", "表 5.1-5　参数扫描结果与理论对照", required=False)
wt_replace("表 5.1-1  参数对定位区域直径的影响", "表 5.1-1　参数对定位区域直径的影响", required=False)
wt_replace("表 5.1-2  1° 误差的横向放大", "表 5.1-2　1° 误差的横向放大", required=False)
wt_replace("表 5.1-3  双实现交叉验证", "表 5.1-3　双实现交叉验证", required=False)
wt_replace("表 5.1-4  基准算例求解结果", "表 5.1-4　基准算例求解结果", required=False)
wt_replace("表 5.1-6  退化情形分类与处理", "表 5.1-6　退化情形分类与处理", required=False)
wt_replace("表 5.1-7  覆盖判定结果", "表 5.1-7　覆盖判定结果", required=False)

print("\n[3] 图题注措辞对齐正稿（编号已在上一步统一）")
wt_replace("图 5.1-1  示向度到 2° 角域的升格示意（单站楔形）",
           "图 5.1-1　示向度到 2° 角域的升格示意（单站楔形，标注 θ±1° 边界）", required=False)
wt_replace("图 5.1-2  两站交会定位区域构造（含边界射线、顶点标注、长度标注）",
           "图 5.1-2　两站交会定位区域构造（含边界射线、顶点标注、长度标注）", required=False)
wt_replace("图 5.1-3  等边三角形反例（直径圆与对角顶点、外接圆对照）",
           "图 5.1-3　等边三角形反例（直径圆与对角顶点、外接圆对照）", required=False)
wt_replace("图 5.1-4  Jung 夹逼示意（同一区域上叠加 D/2 圆与 D/√3 圆）",
           "图 5.1-4　Jung 夹逼示意（同一区域上叠加 D/2 圆与 D/√3 圆）", required=False)
wt_replace("图 5.1-5  顶点过滤示意（假交点与真顶点的对比）",
           "图 5.1-5　顶点过滤示意（假交点与真顶点的对比）", required=False)

# ------------------------------------------------------------------
print("\n[4] 表 5.1-4 基准算例：顶点坐标对齐正稿")
# ------------------------------------------------------------------
wt_replace("(311.866, 499.788)、(300.000, 480.772)、(300.000, 520.370)、(288.134, 499.788)",
           "(311.866, 499.793)、(300.000, 480.777)、(300.000, 520.375)、(288.134, 499.793)", required=False)
wt_sub("直径约 39.60 m，为清除半径", "直径约 39.598 m，为清除半径", required=False)

# ------------------------------------------------------------------
print("\n[5] 表 5.1-5 参数扫描：换实测数据 + 删【实测待填】")
# ------------------------------------------------------------------
for old, new in [
    ("20° → 120°", "20°–160°（15 点）"),
    ("D 随 φ 增大先减后增，φ=90° 附近最小", "D 在 φ = 90° 取最小值 20.95 m，向两侧增大"),
    ("符合 D ∝ 1/sin φ", "✅ 精确符合横向跨距 = 2ε_rad·L/sin φ（φ ≥ 90° 取等）"),
    ("2 / 3 / 4 / 6", "2/3/4/6/8（嵌套加站）"),
    ("D 随 n 增大单调不增", "D = 39.607 → 26.442 → 26.442 → 19.293 → 19.293 m，单调不增"),
    ("符合约束增多的直观", "✅ 符合"),
    ("0.5° / 1° / 2°", "0.25°–2°（7 点）"),
    ("D 近似线性随 ε 增长", "D/ε ∈ [39.572, 39.720]，波动 < 0.3%"),
    ("符合小角近似", "✅ D ∝ ε"),
    ("落在 [1.000, 1.1547]", "γ ∈ [1.000000, 1.001401]"),
    ("符合 Jung 界，右端趋近等边三角形", "✅ 满足 Jung 界 [1, 1.1547]；实际远低于上界"),
]:
    wt_replace(old, new, required=False)

wt_replace(
    "注：表 5.1-5 中扫描数值的具体取值待编程手实测后回填（【实测待填】），表中给出的是实测趋势与理论一致性结论。",
    "注：上表数值为编程手实测结果（源数据 `q1_scan_results.json`，418 KB；含 27 个定向扫描算例与 8000 例"
    "蒙特卡洛随机配置）。特别值得指出的是缺口比 γ 一项：理论上界为 2/√3 = 1.1547（等边三角形取等），"
    "但全部实测算例的 γ 都不超过 1.0014 —— 这并非“右端趋近等边三角形”，恰恰相反：等边三角形在本题的"
    "定位区域族内不可达（详见本节第四层的结构定理，以及 n = 2 情形下“锐角三角形恒有 γ = 1/sin(最大角)”"
    "的解析验证）。", required=False)

# ------------------------------------------------------------------
print("\n[6] 表 5.1-7 覆盖判定：补蒙特卡洛行与合计行")
# ------------------------------------------------------------------
wt_replace("等边三角形（理论反例）", "等边三角形（一般凸集的理论反例）", required=False)
wt_replace("全部扫描算例", "扫描算例（φ / n / ε 三组，27 例）", required=False)
wt_replace("∈ [1.000, 1.1547]", "全部 = 1.000", required=False)
wt_replace("无违例", "✅ 全部成立", required=False)
# 在覆盖判定表的 </w:tbl> 前补两行
anchor_cell = "扫描算例（φ / n / ε 三组，27 例）"
i = doc.find(anchor_cell)
if i > 0:
    k = doc.find("</w:tbl>", i)
    w4 = TOTAL_W // 4

    def _row(cells):
        s = ['<w:tr>']
        for c in cells:
            s.append('<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="' + str(w4) + '"/>'
                     '<w:vAlign w:val="center"/></w:tcPr><w:p><w:pPr>'
                     '<w:spacing w:line="240" w:lineRule="auto" w:before="20" w:after="20"/>'
                     '<w:ind w:firstLineChars="0" w:firstLine="0"/><w:jc w:val="center"/></w:pPr>'
                     '<w:r><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="宋体"/>'
                     '<w:b w:val="0"/><w:sz w:val="21"/></w:rPr>'
                     '<w:t xml:space="preserve">' + esc(c) + '</w:t></w:r></w:p></w:tc>')
        s.append('</w:tr>')
        return ''.join(s)

    extra = (_row(["随机配置 Monte-Carlo（8000 例，n=2..5）", "—", "∈ [1.000000, 1.001401]", "✅ 全部成立"])
             + _row(["全部实测算例合计", "—", "∈ [1.000000, 1.001401]", "无违例"]))
    doc = doc[:k] + extra + doc[k:]
    log("  ✓ 覆盖判定表补入 2 行（Monte-Carlo / 合计）")
else:
    log("  (skip) 未定位覆盖判定表")

# ------------------------------------------------------------------
print("\n[7] 插入第四层：结构定理（正稿 §5.1.7 第四层）")
# ------------------------------------------------------------------
fourth = [
    P("第四层：结构定理 —— 本模型区域族内直径圆实际上总能覆盖", "subhead"),
    P("前三层回答的是“对一般凸区域”的命题。本层进一步回答：“对本模型能生成的定位区域族”又如何？"),
    P("定理 5.7（中心对称 ⇒ γ ≡ 1）　设 K 为中心对称的紧凸集，c 为其对称中心，则 γ(K) = R_MEC / (D/2) = 1。",
      "boldbody"),
    P("证明：由最小包围圆的唯一性与 K 的中心对称性，MEC 的圆心必为 c，故 R_MEC = max_{x∈K} ‖x − c‖。"
      "又对任意 x ∈ K，其对径点 2c − x ∈ K，故"),
    P("D = max_{x,y∈K} ‖x − y‖ ≥ ‖x − (2c − x)‖ = 2‖x − c‖", "form"),
    P("取使 ‖x − c‖ 最大的 x 得 D ≥ 2R_MEC；另一方面显然 D ≤ 2R_MEC。故 D = 2R_MEC，即 γ = 1。证毕。"),
    P("数值验证：正方形、一般平行四边形、中心对称六边形均给出 γ = 1.000000；等边三角形给出 "
      "1.154692 ≈ 2/√3 ✓"),
    P("结构观察 5.1　定位区域 L 的两条对边分别落在同一检测点的两条边界射线上，而这两条射线的夹角恰为 2ε。"
      "因此 L 的两组对边各自偏离平行不超过 2ε —— L 是一个“2ε-近平行四边形”（n 个检测点时为“近平行 2n 边形”）。",
      "boldbody"),
    P("推论 5.5　由定理 5.7，严格中心对称的区域必有 γ = 1；而 L 只是中心对称形状的 O(ε) 扰动，故 "
      "γ = 1 + O(ε)。", "boldbody"),
    P("数值实验（本文实测，数十万组配置搜索）："),
    TBL(["误差半角 ε", "γ − 1 的实测上界"],
        [["0.05°", "1×10⁻⁶"], ["0.25°", "2.9×10⁻⁴"], ["1°（题设）", "5.7×10⁻³"],
         ["2°", "9.0×10⁻³"], ["4°", "3.4×10⁻²"]]),
    P("其中 n = 2 的情形可给出更强的结果：γ 是相似不变量，故两站构型在相似意义下只有 (θ₁, θ₂) 两个形状参数，"
      "可对其做穷举网格搜索（步长 2° 粗搜 + 0.05° 细化）。结果为"),
    P("n = 2, ε = 1°：  max γ = 1.000610，在 (θ₁, θ₂) = (89°, 91°) 取到 —— 该构型的区域退化为锐角三角形", "form"),
    P("（该三角形最大内角 α ≈ 88°，而对锐角三角形恒有 γ = 1/sin α，故 γ = 1/sin 88° = 1.00061 ✓ "
      "与网格结果精确吻合。）多站配置（n = 5）的搜索结果略高，为 γ = 1.0057。故 ε = 1° 下 γ 实测不超过 1.01，"
      "而理论上界为 2/√3 = 1.154701。"),
    P("结论：在本题的定位区域族内，等边三角形（γ = 1.154701）不可达；γ 与 1 的偏离随 ε 趋于零，"
      "题设 ε = 1° 时 γ ≤ 1.01。因此对本题实际出现的定位区域，以直径为直径的圆总能覆盖（至多差 1%）。",
      "boldbody"),
    P("诚实边界：本层由一条已证明的定理（中心对称 ⇒ γ ≡ 1）、一条几何事实（对边来自同一顶点、夹角 2ε）"
      "与数值实验共同支撑；“γ ≤ 1 + C·ε^p 的常数 C 与指数 p 尚未定出”（实测 γ−1 随 ε 大致呈平方增长，"
      "但受“取最大值”的采样误差影响，拟合不稳定），属开放问题。本文如实标注为实验发现而非定理。"),
]
insert_after("Jung 夹逼关系的示意见图 5.1-4。", fourth, required=False) or \
    insert_after("Jung 夹逼关系的示意见图5-4（该图由编程手配图）。", fourth, required=False)

# 图 5.1-3 的图注限定（防止误读）
note3 = [P("⚠️ 图注必须写明：本图是“一般凸集”的反例，用于说明“以直径为直径的圆不一定覆盖”这一数学事实；"
           "等边三角形在本题的定位区域族内不可达（见本节第四层：定理 5.7 + 结构观察 5.1），本题实测算例的 γ 均贴近 1.000。"
           "图注不加此限定会误导读者。")]
insert_after("图 5.1-3　等边三角形反例（直径圆与对角顶点、外接圆对照）", note3, required=False)

note4 = [P("应同时标注实测值：本题算例的 R_MEC 恒贴近下界 D/2（γ ≈ 1.000），而非上界 D/√3。")]
insert_after("图 5.1-4　Jung 夹逼示意（同一区域上叠加 D/2 圆与 D/√3 圆）", note4, required=False)

# ------------------------------------------------------------------
print("\n[8] §6.1(4) 三层 → 四层")
# ------------------------------------------------------------------
wt_sub("对覆盖问题给出反例、充要判据与定量界三层递进回答",
       "对覆盖问题给出反例、充要判据与定量界四层递进回答", required=False)

# ------------------------------------------------------------------
print("\n[9] 插入 §6.3 理论补充，并把原 6.3 改进方向 改为 6.4")
# ------------------------------------------------------------------
wt_replace("6.3 改进方向", "6.4 改进方向", required=False)
sec63 = [
    P("6.3 理论补充（对偶、不变量与 Helly 结构）", "h2") if False else None,
]
# 用现有 Heading 2 段落做模板（抓 “6.4 改进方向” 那一段的 XML）
m = re.search(r'<w:p>(?:(?!</w:p>).)*?6\.4 改进方向(?:(?!</w:p>).)*?</w:p>', doc, re.S)
if m:
    h2_tpl = m.group(0)
    h2_new = h2_tpl.replace("6.4 改进方向", "6.3 理论补充（对偶、不变量与 Helly 结构）")
    # 上面 wt_replace 已把 “6.3 改进方向” 改成 “6.4 改进方向”，模板可直接复用
else:
    h2_tpl, h2_new = None, None
    log("  ⚠️ 未抓到 Heading2 模板（改用加粗正文代替标题）")

body63 = [
    P("本节给出三个理论观察，用于说明本问结构的深层性质。它们不改变主结果，但提供了理解问题的第二视角。"),
    P("命题 5.3（配极对偶与 Jung 定理的对偶形式）　对含原点为内点的闭凸集 C，定义其极集 "
      "C° = { y : ⟨x,y⟩ ≤ 1, ∀x ∈ C }。则有以下三条基本事实：", "boldbody"),
    P("( ⋂ᵢ Cᵢ )° = conv( ⋃ᵢ Cᵢ° )　　（交 ⟷ 包）", "form"),
    P("C ⊆ D　⟹　D° ⊆ C°　　（包含反转）", "form"),
    P("( B(0,R) )° = B(0, 1/R)", "form"),
    P("设 L 为含原点的紧凸集，记 R₀(L) = max{ ‖x‖ : x ∈ L }（以原点为中心的最小包围圆半径），则有 "
      "R₀(L) = 1 / inr( L° )。"),
    P("证明：由定义 inr(L°) = max{ r : B(0,r) ⊆ L° }。由包含反转与双极定理 (L°)° = L（对含原点的闭凸集成立），"
      "B(0,r) ⊆ L° ⟺ L ⊆ B(0,1/r)，故 inr(L°) = max{ r : L ⊆ B(0,1/r) } = 1 / min{ R : L ⊆ B(0,R) } "
      "= 1/R₀(L)。证毕。"),
    P("取 L 的最小包围圆圆心为原点，则 R₀(L) = R_MEC，于是 Jung 定理 R_MEC ≤ D/√3 对偶为 "
      "inr( L° ) ≥ √3 / D，等号当且仅当 L 为等边三角形。"),
    P("验证：等边三角形 L（外接圆半径 1、直径 D = √3、内切圆半径 1/2）的半平面表示为 "
      "{ x : ⟨û_k, x⟩ ≤ 1/2 }，故 L° = conv{ 2û₁, 2û₂, 2û₃ }，即外接圆半径 2、内切圆半径 2·cos 60° = 1 "
      "的等边三角形。于是 inr(L°) = 1 = √3/√3 = √3/D ✓ 取等。"),
    P("本文基准算例（§5.1.6）：R_MEC = 19.799、D = 39.598、√3/D = 0.04374。平移使最小包围圆圆心为原点后，"
      "其极集最紧半平面到原点的距离为 1/19.799 = 0.05051，故 inr(L°) = 0.05051 ≥ 0.04374 ✓ 成立"
      "（本例取下界 R_MEC = D/2，故取严格不等号）。"),
    P("自洽检验：把直径圆半径 D/2 代入对偶，得对偶内切半径 2/D；它与 Jung 界给出的 √3/D 之比为 "
      "2/√3 ≈ 1.1547 —— 与 §5.1.7 主推导给出的最坏缺口完全一致。对偶视角与主视角互相印证。"),
    P("命题 5.4（组合型的仿射不变性）　设 A 为可逆仿射变换。则 L 与 A(L) 的顶点数相同，且“哪两条边界射线"
      "产生哪个顶点”的对应关系相同。", "boldbody"),
    P("证明：仿射变换保持直线与凸性，故把凸多边形映为凸多边形、顶点映为顶点；角域 Wᵢ = Sᵢ + Kᵢ（Kᵢ 为锥）"
      "在 A 下映为 A(Sᵢ) + A(Kᵢ)；且 A(⋂ᵢ Wᵢ) = ⋂ᵢ A(Wᵢ)。故顶点与其射出对的对应关系被保持。证毕。"),
    P("推论：本问的答案分两部分——组合部分（顶点数、顶点与约束对的对应）是仿射不变量；度量部分"
      "（D、R_MEC、面积）依赖具体的角度与距离。等价地，L 的组合型由 2n 条边界射线的有序拟阵"
      "（oriented matroid）决定。据此，n = 2 时 L 的形状可由定理 5.3 完全分类："),
    TBL(["条件", "L 的形状", "顶点数"],
        [["方向区间相交", "无界（直径未定义）", "—"],
         ["区间不相交，一般位置", "凸四边形", "4"],
         ["区间不相交，且一个边界射线交点落在其余角域之外", "凸三角形", "3"],
         ["交集为空", "空集", "0"]]),
    P("基准算例中方向区间 [58.036°, 60.036°] 与 [119.964°, 121.964°] 不相交，属一般位置，实测恰得 4 个顶点 "
      "✓ 与分类一致。"),
    P("Helly 数「3」的三重奏　平面上的数值 d + 1 = 3 在本问中以三种面貌出现，且根源相同：", "boldbody"),
    TBL(["出现处", "陈述", "依据"],
        [["L ≠ ∅ 的判定", "任意 3 个角域相交 ⇒ 全体相交", "Helly 定理（平面 Helly 数 = 3）"],
         ["最小包围圆的决定", "MEC 由不超过 3 个边界点决定", "LP-type 组合维数 = 3"],
         ["Jung 上界取等", "等边三角形（3 点配置）取等", "三支撑点情形"]]),
    P("三者相互独立，但同为平面 Helly 数的体现。其工程含义有二：判定 L 是否为空只需检验三元组"
      "（n 较大时可作快速预筛）；最小包围圆算法的基（basis）大小不超过 3，实现时只需处理边界点数为 "
      "0/1/2/3 的四种情形。"),
]
anchor64 = "6.4 改进方向"
i = doc.find(anchor64)
if i > 0:
    k = doc.rfind("<w:p>", 0, i)
    blocks = ([] if h2_new is None else [h2_new]) + body63
    doc = doc[:k] + "".join(blocks) + doc[k:]
    log("  ✓ 在 §6.4 前插入 §6.3（%d 块，含标题）" % len(blocks))
else:
    log("  ⚠️ 未定位 §6.4，跳过 §6.3 插入")

# ------------------------------------------------------------------
print("\n[10] 参考文献 [7][8][10] 去掉“待核对”")
# ------------------------------------------------------------------
wt_sub("（元数据待核对）", "", required=False)
wt_sub("（版本待核对）", "", required=False)

# ==================================================================
print("\n" + "=" * 70)
print("document.xml: %d → %d 字符（Δ %+d）" % (orig_len, len(doc), len(doc) - orig_len))

if DRY:
    print("[--dry] 未写盘。")
    sys.exit(0)

if not os.path.exists(BAK):
    shutil.copy2(DOCX, BAK)
    print("已备份原文件 →", BAK)

tmp = DOCX + ".tmp"
with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "word/document.xml":
            data = doc.encode("utf-8")
        zout.writestr(item, data)
zin.close()
os.replace(tmp, DOCX)
print("已写回:", DOCX)
print("\n补丁条目：")
for l in LOG:
    print(" ", l)
