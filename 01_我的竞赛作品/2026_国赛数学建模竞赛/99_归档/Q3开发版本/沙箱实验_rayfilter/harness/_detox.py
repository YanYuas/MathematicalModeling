# -*- coding: utf-8 -*-
"""去 AI 味 · 机械部分：只改注释文本，代码与字符串一律不碰。

清掉四类痕迹：
  ① `% ====...` 横幅分隔线
  ② `**加粗**` 的 markdown 星号
  ③ 注释里的 emoji（⚠️ 之类）
  ④ 指向团队内部流程文档的引用《Q3 调优经验与补丁记录》P-2 ——
     评委看不到那份文档，留着只会显得代码在自说自话
  ⑤ 注释里的 `⇒` 换成中文顿挫

改完必须用 `_code_hash.py` 验证「纯代码哈希」逐位不变。
"""
import glob
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BANNER = re.compile(r'^%\s*[=\-]{10,}\s*$')
BOLD = re.compile(r'\*\*([^*\n]+)\*\*')
EMOJI = re.compile(r'[⚠️✅❌⭐✔✗\U0001f534\U0001f7e1\U0001f7e2]')
# 《…》指向团队内部的流程文档，评委看不到 —— 连同"详见/见/理由见"与随后的 P-编号
# 整段删掉，不要留"详见P-2。"这种残句
DOCREF = re.compile(
    r'\s*[；;，,、。]?\s*'
    r'(?:详见|参见|理由见|依据见|见)\s*'
    r'《[^》]{2,40}》'
    r'\s*(?:[Pp]-?\d+(?:\s*[、，,]\s*[Pp]-?\d+)*)?'
    r'\s*[。；]?')
DOCREF_LOOSE = re.compile(r'《[^》]{2,40}》\s*(?:[Pp]-?\d+)?\s*[。；]?')


def split_comment(line):
    """把一行拆成 (代码部分, 注释部分或 None)。字符串里的 % 不算注释。

    MATLAB 的 `...` 续行符之后**整段都是注释** —— 这里必须一并返回，
    否则 `fprintf(..., ...  % 注释)` 这种行尾注释会被漏掉。
    """
    i, n, out = 0, len(line), []
    while i < n:
        c = line[i]
        if c == "'":
            if out and (out[-1].isalnum() or out[-1] in "_)]}.'"):
                out.append(c); i += 1; continue
            j = i + 1
            while j < n:
                if line[j] == "'":
                    if j + 1 < n and line[j + 1] == "'":
                        j += 2; continue
                    break
                j += 1
            out.append(line[i:j + 1]); i = j + 1; continue
        if line[i:i + 3] == '...':
            k = line.find('%', i + 3)
            if k >= 0:
                return ''.join(out) + line[i:k], line[k:]
            out.append(line[i:]); return ''.join(out), None
        if c == '%':
            return ''.join(out), line[i:]
        out.append(c); i += 1
    return line, None


def detox_text(body):
    """注释正文的清理（`%%` 单元格标记之外的都走这里）。

    前导空白单独摘出来保存 —— 否则 `% ⇒ 判据…` 这种行会被清成 `%判据…`，
    少了 `%` 后面那个空格，缩进层次就没了。
    """
    lead = re.match(r'[ \t]*', body).group(0)
    body = body[len(lead):]
    body = DOCREF.sub('', body)
    body = DOCREF_LOOSE.sub('', body)
    body = EMOJI.sub('', body)
    body = BOLD.sub(r'\1', body)
    body = body.replace('⇒', '，')
    body = re.sub(r'（\s*[、，,。；]*\s*）', '', body)
    body = re.sub(r'（\s*[、，,；]\s*', '（', body)
    body = re.sub(r'[、，,；]\s*）', '）', body)
    body = re.sub(r'\s*，\s*', '，', body)
    body = re.sub(r'，\s*，', '，', body)
    body = re.sub(r'^\s*[、，,。；]\s*', '', body)
    body = re.sub(r'[ \t]+$', '', body)
    if lead and body and not body.startswith(' '):
        body = lead + body          # 原样还回前导空白（压缩成 1 个空格会把用法块的缩进弄丢）
    return body


def detox_comment(txt):
    if txt is None:
        return None
    marker, body = txt[:1], txt[1:]
    if body.startswith('%'):
        # `%%` 单元格标记本身保留，但标题文字照清
        return marker + '%' + detox_text(body[1:])
    return marker + detox_text(body)


# 控制台输出里同样要清的两类：markdown 星号（在终端显示为字面星号）
# 与 ⚠️✅❌（本机字体缺字，显示成方框）。`⇒`/`→`/`✓` 保留 —— 可读，且
# 《Q3正式测试操作手册》逐字引用了含它们的那两行。
STR_CLEAN = [
    (re.compile(r'\*\*([^*\n]*)\*\*'), r'\1'),
    (re.compile(r'[⚠️✅❌]+\s?'), ''),
]


def detox_string_literals(line):
    """只处理单引号字符串内部；字符串外的代码一律不动。"""
    out, i, n = [], 0, len(line)
    while i < n:
        c = line[i]
        if c == "'":
            if out and (out[-1].isalnum() or out[-1] in "_)]}.'"):
                out.append(c); i += 1; continue
            j = i + 1
            while j < n:
                if line[j] == "'":
                    if j + 1 < n and line[j + 1] == "'":
                        j += 2; continue
                    break
                j += 1
            lit = line[i:j + 1]
            for rx, rep in STR_CLEAN:
                lit = rx.sub(rep, lit)
            out.append(lit); i = j + 1; continue
        out.append(c); i += 1
    return ''.join(out)


def detox_file(path):
    # 交付树是混合行尾：10 个文件 CRLF、其余 LF。必须逐个保留原样，
    # 否则 git 会把整个文件当成重写（本次实测踩到过）。
    raw = open(path, 'rb').read()
    use_crlf = b'\r\n' in raw
    src = raw.decode('utf-8').replace('\r\n', '\n')
    out = []
    in_block = False
    for line in src.split('\n'):
        s = line.lstrip()
        if in_block:
            out.append(line)                  # 块注释原样保留
            if s.startswith('%}'):
                in_block = False
            continue
        if s.startswith('%{'):
            in_block = True
            out.append(line); continue
        if BANNER.match(s):
            continue                          # 整行横幅丢掉
        code, cmt = split_comment(line)
        code = detox_string_literals(code)
        if cmt is None:
            out.append(code)
        else:
            new = detox_comment(cmt)
            if new.strip() == '%':
                # 独立的 `%` 行必须留着：MATLAB 的 help 块靠连续 `%` 行，
                # 空行会截断它（`help f` 就只剩第一行）—— 这是功能回归
                out.append(code + '%')          # 缩进必须留着
            else:
                out.append(code + new)
    text = '\n'.join(out)
    text = re.sub(r'\n{3,}', '\n\n', text)
    if use_crlf:
        text = text.replace('\n', '\r\n')
    return text


def main():
    root = sys.argv[1]
    n = 0
    for p in sorted(glob.glob(os.path.join(root, '*.m'))):
        old = open(p, encoding='utf-8', newline='').read()
        new = detox_file(p)
        if new != old:
            open(p, 'w', encoding='utf-8', newline='').write(new)
            n += 1
    print('已处理 %d 个文件' % n)


if __name__ == '__main__':
    main()
