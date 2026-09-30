# -*- coding: utf-8 -*-
"""抽出 MATLAB 源码的「纯代码」：去掉注释与空行，只留会执行的 token。

用途：去 AI 味只应改注释。改前改后各跑一次，哈希必须一致 —— 否则说明动了逻辑。
处理 MATLAB 的三类注释：行注释 %、块注释 %{ %}、以及字符串里的 % 不算注释。
'It''s' 这种转义单引号也要认。
"""
import glob
import hashlib
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


def mask_strings(src):
    """把单引号字符串的内容换成 <S>，只留"这里有个字符串"这个事实。

    去 AI 味会**故意**改控制台输出的字符串内容（清掉 markdown 星号与 ⚠️✅❌）。
    屏蔽内容后，哈希不变 ⟺ **逻辑与结构**没动，字符串改动另行逐条审。
    """
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c == "'":
            if out and (out[-1].isalnum() or out[-1] in "_)]}.'"):
                out.append(c); i += 1; continue
            j = i + 1
            while j < n:
                if src[j] == "'":
                    if j + 1 < n and src[j + 1] == "'":
                        j += 2; continue
                    break
                j += 1
            out.append("'<S>'"); i = j + 1; continue
        out.append(c); i += 1
    return ''.join(out)


def strip_comments(src):
    """返回只含代码的行（去掉行注释、块注释、空行与行尾空白）。"""
    out = []
    in_block = False
    for raw in src.split('\n'):
        line = raw
        s = line.lstrip()
        if in_block:
            if s.startswith('%}'):
                in_block = False
                line = s[2:]
            else:
                continue
        elif s.startswith('%{'):
            in_block = True
            continue
        code = []
        i = 0
        n = len(line)
        while i < n:
            c = line[i]
            if c == "'":                       # 字符串或转置
                if code and (code[-1].isalnum() or code[-1] in "_)]}.'"):
                    code.append(c); i += 1     # 转置运算符
                    continue
                j = i + 1
                while j < n:
                    if line[j] == "'":
                        if j + 1 < n and line[j + 1] == "'":
                            j += 2; continue
                        break
                    j += 1
                code.append(line[i:j + 1]); i = j + 1
                continue
            if c == '.' and line[i:i + 3] == '...':   # 续行符：其后是注释
                break
            if c == '%':
                break
            code.append(c); i += 1
        out.append(''.join(code).rstrip())
    return '\n'.join(l for l in out if l.strip())


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    digest = {}
    for p in sorted(glob.glob(os.path.join(root, '*.m'))):
        src = open(p, encoding='utf-8').read()
        digest[os.path.basename(p)] = hashlib.sha256(
            mask_strings(strip_comments(src)).encode('utf-8')).hexdigest()[:16]
    dest = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, '_code_hash.txt')
    with open(dest, 'w', encoding='utf-8', newline='\n') as fh:
        for k in sorted(digest):
            fh.write('%s  %s\n' % (digest[k], k))
    print('已写出 %d 个文件的纯代码哈希 -> %s' % (len(digest), dest))


if __name__ == '__main__':
    main()
