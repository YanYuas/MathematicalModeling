# -*- coding: utf-8 -*-
"""Q2 HPWL 评估器（可复用模块）。
输入: .blocks/.nets/.pl
给定各 block 的位置(左下角)与方向，计算总 HPWL。
引脚=模块几何中心；终端引脚=固定坐标(.pl)。
用法:
    from hpwl import load, evaluate
    data = load('n100')
    wl = evaluate(data, pos_dict, rot_dict)
pos_dict: name->(x,y) 左下角; rot_dict: name->True(已旋转90°)
"""
import re, os, math

BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"

def parse_blocks(path):
    blocks = {}
    terminals = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(('Num', '//')):
                continue
            parts = line.split()
            name = parts[0]
            if parts[1] == 'terminal':
                terminals.append(name)
                continue
            if parts[1] == 'block':
                tuples = re.findall(r'\(-?\d+,\s*-?\d+\)', line)
                xs = [int(t.strip('()').split(',')[0]) for t in tuples]
                ys = [int(t.strip('()').split(',')[1]) for t in tuples]
                blocks[name] = (max(xs)-min(xs), max(ys)-min(ys))
    return blocks, terminals

def parse_pl(path):
    d = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            p = line.split()
            d[p[0]] = (int(p[1]), int(p[2]))
    return d

def parse_nets(path):
    nets = []
    with open(path, encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith('//')]
    i = 0
    while i < len(lines):
        if lines[i].startswith(('NumNets', 'NumPins')): i += 1; continue
        if lines[i].startswith('NetDegree'):
            deg = int(lines[i].split(':')[1]); i += 1
            nets.append(lines[i:i+deg]); i += deg
    return nets

def load(name):
    blocks, terminals = parse_blocks(os.path.join(BASE, name + '.blocks'))
    term_pos = parse_pl(os.path.join(BASE, name + '.pl'))
    nets = parse_nets(os.path.join(BASE, name + '.nets'))
    A = sum(w*h for w, h in blocks.values())
    S = math.sqrt(A * 1.15)   # Q2 正方形轮廓边长 Γ=0.15
    return dict(name=name, blocks=blocks, terminals=terminals,
                term_pos=term_pos, nets=nets, area=A, side=S)

def evaluate(data, pos, rot=None):
    """pos: name->(x,y) 左下角; rot: name->bool(已旋转)。返回总HPWL。"""
    if rot is None: rot = {}
    pins = {}
    for nm, (w, h) in data['blocks'].items():
        x, y = pos[nm]
        ww, hh = (h, w) if rot.get(nm) else (w, h)
        pins[nm] = (x + ww/2.0, y + hh/2.0)
    for nm, (x, y) in data['term_pos'].items():
        pins[nm] = (float(x), float(y))
    total = 0.0
    per_net = []
    for net in data['nets']:
        xs = [pins[p][0] for p in net]
        ys = [pins[p][1] for p in net]
        hpwl = (max(xs)-min(xs)) + (max(ys)-min(ys))
        total += hpwl
        per_net.append(hpwl)
    return total, per_net

def strip_pack(blocks, S):
    """正确 skyline bottom-left 打包（Chen&Chang 教材标准）。返回 pos,rot。"""
    bl = sorted(blocks.items(), key=lambda kv: -max(kv[1]))
    pos, rot = {}, {}
    sky = [(0.0, 0.0, float(S))]  # (x, y, width), sorted by x, non-overlap
    for nm, (w, h) in bl:
        cands = [(w, h)] if w == h else [(w, h), (h, w)]
        best = None  # (x, y, cw, ch, cand_rot)
        # 用所有 skyline 段起点 + 0 作为候选 x，允许跨段放置
        cand_x = sorted(set([0.0] + [sx for (sx, sy, sw) in sky]))
        for cw, ch in cands:
            for x in cand_x:
                if x + cw > S: continue
                x2 = x + cw
                # 该区间上方的最大高度（跨段）
                ymax = 0.0
                for (xx, yy, ww) in sky:
                    if xx < x2 and xx + ww > x:
                        ymax = max(ymax, yy)
                if ymax + ch <= S:
                    cand = (x, ymax, cw, ch)
                    if best is None or cand[1] < best[1] or (cand[1] == best[1] and x < best[0]):
                        best = (x, ymax, cw, ch, (cw, ch) == (h, w))
        if best is None:
            raise ValueError(f'cannot place {nm} {w}x{h} in {S}')
        x, y, cw, ch, is_rot = best
        pos[nm] = (x, y); rot[nm] = is_rot
        x2 = x + cw
        # 更新 skyline：切割被覆盖的段，插入新段
        new_sky = []
        for (sx, sy, sw) in sky:
            if sx >= x2 or sx + sw <= x:
                new_sky.append((sx, sy, sw))
            elif sx < x and sx + sw > x2:
                new_sky.append((sx, sy, x - sx))
                new_sky.append((x2, sy, sx + sw - x2))
            elif sx < x:
                new_sky.append((sx, sy, x - sx))
            elif sx + sw > x2:
                new_sky.append((x2, sy, sx + sw - x2))
        new_sky.append((x, y + ch, cw))
        # 合并相邻同高段
        new_sky.sort()
        merged = []
        for seg in new_sky:
            if merged and abs(merged[-1][1] - seg[1]) < 1e-9 and abs(merged[-1][0] + merged[-1][2] - seg[0]) < 1e-9:
                merged[-1] = (merged[-1][0], merged[-1][1], merged[-1][2] + seg[2])
            else:
                merged.append(seg)
        sky = merged
    return pos, rot

if __name__ == '__main__':
    import sys
    for name in ['n100', 'n200', 'n300']:
        d = load(name)
        n = len(d['blocks'])
        # 基线1: 所有块左下角放 (0,0)（重叠，仅测 HPWL 尺度）
        pos = {k: (0, 0) for k in d['blocks']}
        wl, _ = evaluate(d, pos)
        # 基线2: strip pack 填入轮廓
        S = d['side']
        pos2, rot2 = strip_pack(d['blocks'], S)
        wl2, per2 = evaluate(d, pos2, rot2)
        # 轮廓占用
        W = max(p[0]+(d['blocks'][k][1] if rot2.get(k) else d['blocks'][k][0]) for k, p in pos2.items())
        H = max(p[1]+(d['blocks'][k][0] if rot2.get(k) else d['blocks'][k][1]) for k, p in pos2.items())
        print(f"{name}: side={S:.2f}, area={d['area']}, blocks={n}, "
              f"HPWL(全堆(0,0))={wl:.0f}, HPWL(strip)={wl2:.0f}, strip占用WxH={W:.0f}x{H:.0f}")
        # 终端分布 per edge
        tp = d['term_pos']
        eps = 1e-6
        edges = {'bottom(y=0)': 0, 'top': 0, 'left(x=0)': 0, 'right': 0, 'inner': 0}
        for (x, y) in tp.values():
            if y < eps: edges['bottom(y=0)'] += 1
            elif abs(y - 444) < eps and name == 'n100': edges['top'] += 1
            elif abs(y - 438) < eps and name == 'n200': edges['top'] += 1
            elif abs(y - 548) < eps and name == 'n300': edges['top'] += 1
            elif x < eps: edges['left(x=0)'] += 1
            elif abs(x - max(tp.values(), key=lambda t: t[0])[0]) < eps: edges['right'] += 1
            else: edges['inner'] += 1
        print(f"   终端分布: {edges}")
