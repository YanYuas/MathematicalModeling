# -*- coding: utf-8 -*-
"""m2_data.py — Q2 独立实现 阶段P0：数据解析 + 校验
解析 .blocks/.nets/.pl（GSRC bookshelf），完全独立于编程手 hpwl.py（交叉核实）。
校验：总面积 / 线网数 / 终端数 三匹配。
"""
import os
import math
import re

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "2026年第七届华数杯数学建模竞赛赛题", "B题 VLSI布图规划设计", "附件")

# 期望值（建模手实测，用于回归校验）
EXPECT = {
    'n100': dict(area=179501, nets=885, terms=334, side=454.34),
    'n200': dict(area=175696, nets=1585, terms=564, side=449.50),
    'n300': dict(area=273170, nets=1893, terms=569, side=560.49),
}


class Block:
    __slots__ = ('idx', 'name', 'w', 'h')

    def __init__(self, idx, name, w, h):
        self.idx = idx
        self.name = name
        self.w = float(w)
        self.h = float(h)

    @property
    def area(self):
        return self.w * self.h

    def aspect_ratio(self):
        return max(self.w, self.h) / min(self.w, self.h)

    def rotate(self):
        """旋转90°：交换宽高"""
        self.w, self.h = self.h, self.w


def parse_blocks(path):
    """返回 (blocks: {name:(w,h)}, terminals: [name])"""
    blocks, terminals = {}, []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(('Num', '//')):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            name, kind = parts[0], parts[1]
            if kind == 'terminal':
                terminals.append(name)
                continue
            if kind == 'block':
                # 提取所有 (x,y) 点
                coords = re.findall(r'\((-?\d+),\s*(-?\d+)\)', line)
                xs = [int(a) for a, _ in coords]
                ys = [int(b) for _, b in coords]
                w = max(xs) - min(xs)
                h = max(ys) - min(ys)
                blocks[name] = (w, h)
    return blocks, terminals


def parse_pl(path):
    d = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            p = line.split()
            if len(p) >= 3:
                d[p[0]] = (int(p[1]), int(p[2]))
    return d


def parse_nets(path):
    """返回 nets: [[pin...], ...]"""
    nets = []
    with open(path, encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith('//')]
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith(('NumNets', 'NumPins')):
            i += 1
            continue
        m = re.match(r'NetDegree\s*:\s*(\d+)', line)
        if m:
            deg = int(m.group(1))
            i += 1
            nets.append(lines[i:i + deg])
            i += deg
        else:
            i += 1
    return nets


def load(name):
    """加载并校验，返回数据字典。校验失败抛 AssertionError。"""
    blocks, terminals = parse_blocks(os.path.join(BASE, name + '.blocks'))
    term_pos = parse_pl(os.path.join(BASE, name + '.pl'))
    nets = parse_nets(os.path.join(BASE, name + '.nets'))

    A = sum(w * h for w, h in blocks.values())
    S = math.sqrt(A * 1.15)

    # 回归校验
    exp = EXPECT[name]
    ok = True
    ok &= abs(A - exp['area']) < 1
    ok &= len(nets) == exp['nets']
    ok &= len(terminals) == exp['terms']
    ok &= len(term_pos) == exp['terms']

    # 线网结构统计
    deg = {}
    mixed = 0
    io_nets = []
    for net in nets:
        d = len(net)
        deg[d] = deg.get(d, 0) + 1
        has_term = any(p in term_pos for p in net)
        has_mod = any(p in blocks for p in net)
        if has_term and has_mod:
            mixed += 1
            io_nets.append(net)

    stats = dict(
        blocks=blocks, terminals=terminals, term_pos=term_pos, nets=nets,
        area=A, side=S, num_blocks=len(blocks),
        degree_hist=deg, mixed_nets=mixed, io_nets=io_nets,
    )
    if not ok:
        raise AssertionError(
            f'{name} 校验失败: area={A} (exp {exp["area"]}), nets={len(nets)} '
            f'(exp {exp["nets"]}), terms={len(terminals)}/{len(term_pos)} (exp {exp["terms"]})')
    return stats


if __name__ == '__main__':
    print('=== 阶段P0: 数据解析 + 校验 ===')
    for name in ['n100', 'n200', 'n300']:
        d = load(name)
        io_area = sum(w * h for w, h in d['blocks'].values())
        print(f'{name}: blocks={d["num_blocks"]} area={d["area"]:.0f} '
              f'side={d["side"]:.2f} nets={len(d["nets"])} terms={len(d["term_pos"])}')
        print(f'    度数分布={dict(sorted(d["degree_hist"].items()))} 混合网={d["mixed_nets"]}')
    print('阶段P0: ALL PASS')
