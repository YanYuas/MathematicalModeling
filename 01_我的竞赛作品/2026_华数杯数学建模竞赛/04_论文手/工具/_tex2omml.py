# -*- coding: utf-8 -*-
"""LaTeX 数学 -> Word OMML 转换器（覆盖本论文公式语法：frac/cases/sqrt/上下标/命令/转义）"""
import re
from docx.oxml import parse_xml

MNS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
WNS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def r(t):  return f'<m:r><m:t xml:space="preserve">{t}</m:t></m:r>'
def sub(e, s): return f'<m:sSub><m:e>{e}</m:e><m:sub>{s}</m:sub></m:sSub>'
def sup(e, s): return f'<m:sSup><m:e>{e}</m:e><m:sup>{s}</m:sup></m:sSup>'
def frac(n, d): return f'<m:f><m:num>{n}</m:num><m:den>{d}</m:den></m:f>'
def delim(e, b='(', c=')'): return f'<m:d><m:dPr><m:begChr m:val="{b}"/><m:endChr m:val="{c}"/></m:dPr><m:e>{e}</m:e></m:d>'
def func(name, e): return f'<m:func><m:fName>{r(name)}</m:fName><m:e>{e}</m:e></m:func>'
def rad(e): return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{e}</m:e></m:rad>'
def om(n): return f'<m:oMath>{n}</m:oMath>'

SYM = {
    'ge': '≥', 'le': '≤', 'ne': '≠', 'forall': '∀', 'vee': '∨', 'wedge': '∧',
    'cup': '∪', 'cdot': '·', 'pm': '±', 'to': '→', 'in': '∈', 'approx': '≈',
    'Delta': 'Δ', 'varepsilon': 'ε', 'Phi': 'Φ', 'sigma': 'σ', 'alpha': 'α',
    'lambda': 'λ', 'mu': 'μ', 'Omega': 'Ω', 'tau': 'τ', 'Sigma': 'Σ',
    'langle': '⟨', 'rangle': '⟩', 'qquad': '   ', 'quad': '  ', 'times': '×',
    'sum': '∑', 'min': 'min', 'max': 'max', 'ln': 'ln', 'sin': 'sin', 'cos': 'cos',
    'infty': '∞', 'cdot': '·',
}
ESCAPED = {'\\{':'{', '\\}':'}', '\\|':'|', '\\,':'', '\\;':'', '\\!':'', '\\ ':' '}

class Parser:
    def __init__(self, s):
        self.s = s; self.i = 0
    def peek(self, k=0):
        return self.s[self.i + k] if self.i + k < len(self.s) else ''
    def end(self): return self.i >= len(self.s)
    def skip_ws(self):
        while not self.end() and self.s[self.i] in ' \n\t': self.i += 1

    def group_raw(self):
        """读下一组的原文：花括号 / 括号 / 方括号 / 转义 / 命令 / 单字符"""
        c = self.peek()
        if not c:
            return ''
        if c == '{':
            self.i += 1; s = self.i; depth = 1
            while not self.end():
                if self.peek() == '{': depth += 1
                elif self.peek() == '}':
                    depth -= 1
                    if depth == 0: break
                self.i += 1
            out = self.s[s:self.i]; self.i += 1
            return out
        if c in '([':
            close = {'(':')','[':']'}[c]
            self.i += 1; s = self.i; depth = 1
            while not self.end():
                ch = self.s[self.i]
                if ch == c: depth += 1
                elif ch == close:
                    depth -= 1
                    if depth == 0: break
                self.i += 1
            inner = self.s[s:self.i]
            if self.peek() == close: self.i += 1  # 消费闭括号
            return inner
        if c == '\\':
            if self.s[self.i:self.i+2] in ESCAPED:
                self.i += 2
                return ESCAPED[self.s[self.i-2:self.i]]
            m = re.match(r'\\[a-zA-Z]+', self.s[self.i:])
            if m:
                self.i += len(m.group(0))
                return '\\' + m.group(0)[1:]
            self.i += 1
            return self.s[self.i-1:self.i]
        ch = self.s[self.i]; self.i += 1
        return ch

    def parse_until(self, stop_char):
        parts = []
        while not self.end() and self.peek() != stop_char:
            parts.append(self.expr())
        return ''.join(parts)

    def expr(self):
        node = self.atom()
        while True:
            c = self.peek()
            if c and c in '_^':
                self.i += 1
                arg_om = self.parse(self.group_raw())
                node = sub(node, arg_om) if c == '_' else sup(node, arg_om)
            else:
                break
        return node

    def atom(self):
        c = self.peek()
        if c == '\\':
            if self.s[self.i:self.i+2] in ESCAPED:
                self.i += 2
                return ESCAPED[self.s[self.i-2:self.i]]
            m = re.match(r'\\([a-zA-Z]+)', self.s[self.i:])
            if not m:
                self.i += 1
                return r(self.s[self.i-1:self.i])
            cmd = m.group(1); self.i += len(m.group(0))
            if cmd in ('frac', 'dfrac'):
                n = self.parse(self.group_raw()); d = self.parse(self.group_raw())
                return frac(n, d)
            if cmd == 'text':
                return r(self.group_raw())
            if cmd == 'sqrt':
                return rad(self.parse(self.group_raw()))
            if cmd == 'begin':
                env = self.group_raw()
                return self.cases(env)
            if cmd == 'left':
                # 定界符：\{ \} \lceil \rceil ( ) [ ] |
                two = self.s[self.i:self.i+2]
                if two == '\\{': self.i += 2; b = '{'
                elif two == '\\}': self.i += 2; b = '}'
                elif two == '\\|': self.i += 2; b = '|'
                elif self.s[self.i:self.i+6] == '\\lceil': self.i += 6; b = '⌈'
                elif self.s[self.i:self.i+7] == '\\rceil': self.i += 7; b = '⌉'
                elif self.s[self.i:self.i+7] == '\\langle': self.i += 7; b = '⟨'
                elif self.s[self.i:self.i+8] == '\\rangle': self.i += 8; b = '⟩'
                else:
                    b = self.peek(); self.i += 1
                inner = self.parse_until_right()
                self.skip_ws()
                if self.s[self.i:self.i+6] == '\\right':
                    self.i += 6
                    two = self.s[self.i:self.i+2]
                    if two == '\\{': self.i += 2; e = '{'
                    elif two == '\\}': self.i += 2; e = '}'
                    elif two == '\\|': self.i += 2; e = '|'
                    elif self.s[self.i:self.i+6] == '\\lceil': self.i += 6; e = '⌈'
                    elif self.s[self.i:self.i+7] == '\\rceil': self.i += 7; e = '⌉'
                    elif self.s[self.i:self.i+8] == '\\rangle': self.i += 8; e = '⟩'
                    else:
                        e = self.peek(); self.i += 1
                    return delim(inner, b, e)
                return inner
            if cmd in ('max', 'min', 'ln', 'sin', 'cos'):
                self.skip_ws()
                if self.peek() in '{(':
                    arg = self.parse(self.group_raw())
                    return func(cmd, arg)
                return r(cmd)
            if cmd in SYM:
                return r(SYM[cmd])
            return r(cmd)
        # 普通字符（含 `|`、`=`、数字）
        ch = self.s[self.i]; self.i += 1
        return r(ch)

    def parse_until_right(self):
        parts = []
        while not self.end():
            if self.s[self.i:self.i+6] == '\\right': break
            parts.append(self.expr())
        return ''.join(parts)

    def cases(self, env):
        # 找 \end{cases}
        end_idx = self.s.find('\\end', self.i)
        body = self.s[self.i:end_idx] if end_idx >= 0 else self.s[self.i:]
        self.i = (end_idx + 4) if end_idx >= 0 else len(self.s)
        # 消费 \end 后的 {cases}
        if self.peek() == '{': self.group_raw()
        rows = []
        for row in re.split(r'\\\\', body):
            cells = [c.strip() for c in row.split('&')]
            rows.append([self.parse(c) for c in cells])
        ncols = max(len(rw) for rw in rows)
        mrs = []
        for row in rows:
            cells_xml = ''.join(f'<m:e>{row[j] if j < len(row) else r(" ")}</m:e>' for j in range(ncols))
            mrs.append(f'<m:mr>{cells_xml}</m:mr>')
        m_el = (f'<m:m><m:mPr><m:mcs>'
                f'<m:mc><m:mcPr><m:count m:val="{ncols}"/><m:mcJc m:val="left"/></m:mcPr>'
                f'{"<m:e></m:e>"*ncols}</m:mc></m:mcs></m:mPr>'
                f'{"".join(mrs)}</m:m>')
        return delim(m_el, '{', '')

    def parse(self, s):
        p = Parser(s)
        out = []
        while not p.end():
            out.append(p.expr())
        return ''.join(out)


def latex_to_omml(latex):
    latex = latex.strip()
    latex = re.sub(r'\\qquad\s*\(([^)]+)\)', r'@@N(\1)@@', latex)
    latex = re.sub(r'\\quad\s*\(([^)]+)\)', r'@@N(\1)@@', latex)
    p = Parser(latex)
    out = []
    while not p.end():
        if p.s[p.i:p.i+3] == '@@N':
            m = re.match(r'@@N\(([^)]+)\)@@', p.s[p.i:])
            if m:
                p.i += len(m.group(0))
                out.append(r('(' + m.group(1) + ')'))
                continue
        out.append(p.expr())
    return om(''.join(out))

def latex_par(latex):
    xml = (f'<w:p xmlns:w="{WNS}" xmlns:m="{MNS}">'
           f'<w:pPr><w:jc w:val="center"/></w:pPr>{latex_to_omml(latex)}</w:p>')
    return parse_xml(xml)

def latex_par_auto(latex):
    """自动检测方程编号并生成方程段"""
    out = latex_to_omml(latex)
    nm = re.search(r'\((\d+)\)</m:t>', out)
    if nm:
        return latex_par_num(latex, nm.group(1))
    return latex_par(latex)

def latex_par_num(latex, num):
    """带方程号的居中公式：内容 + (N) 右对齐"""
    xml = (f'<w:p xmlns:w="{WNS}" xmlns:m="{MNS}">'
           f'<w:pPr><w:jc w:val="center"/><w:tabs><w:tab w:val="right" w:pos="9360"/></w:tabs></w:pPr>'
           f'{latex_to_omml(latex)}<w:r><w:tab/></w:r><w:r><w:t xml:space="preserve">({num})</w:t></w:r></w:p>')
    return parse_xml(xml)

if __name__ == '__main__':
    tests = [
        r'\min \Phi = \max(W, H) \qquad (1)',
        r'\text{s.t. } A \le A_{\text{opt}}(1+\varepsilon) \qquad (2)',
        r'M^2 = A\cdot R, \quad M = \sqrt{A\cdot R} \qquad (3)',
        r'\forall i\neq j:\ (x_i \ge x_j+w_j)\ \vee\ (x_j \ge x_i+w_i)\ \vee\ (y_i \ge y_j+h_j)\ \vee\ (y_j \ge y_i+h_i) \qquad (4)',
        r'T_1 = \frac{\Delta_{avg}}{|\ln P|}, \quad T_n = \begin{cases} \dfrac{T_1\langle\Delta cost\rangle}{n\cdot c}, & 2\le n \le k \\[8pt] \dfrac{T_1\langle\Delta cost\rangle}{n}, & n > k \end{cases} \qquad (5)',
        r'H_{\text{FFD}}(W) = \sum_{\text{行}} \max_{b \in \text{行}} h_b \qquad (6)',
        r'q(i,j) = \text{squareness}(i \cup j) - \max\{\text{squareness}(i), \text{squareness}(j)\}, \quad \text{仅 } q(i,j) > 0 \text{ 配对} \qquad (7)',
        r'A \ge A_{total} \quad \text{(面积下界)} \qquad (8)',
        r'A \ge \lceil \sqrt{A_{total}} \rceil^2 \quad \text{(方形下界，R=1)} \qquad (9)',
        r'H(W) \ge \max\left\{\frac{A_{total}}{W},\ \max_{b} h_b\right\} \quad \text{(固定宽下界)} \qquad (10)',
    ]
    for t in tests:
        try:
            o = latex_to_omml(t)
            parse_xml(f'<w:p xmlns:w="{WNS}" xmlns:m="{MNS}">{o}</w:p>')
            print('OK :', t[:50])
        except Exception as e:
            print('ERR:', t[:50], '|', e)
