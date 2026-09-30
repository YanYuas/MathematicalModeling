# -*- coding: utf-8 -*-
"""Q2 数据全量统计（复用 hpwl 解析器）。用法: python 分析Q2数据.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hpwl import load, evaluate, strip_pack
from collections import Counter

if __name__ == '__main__':
    for name in ['n100', 'n200', 'n300']:
        d = load(name)
        blocks, nets = d['blocks'], d['nets']
        tp = d['term_pos']
        A, S = d['area'], d['side']
        # 线网结构
        tset = set(tp)
        ct = cm = cx = 0
        for net in nets:
            t = sum(1 for p in net if p in tset)
            if t == len(net): ct += 1
            elif t == 0: cm += 1
            else: cx += 1
        deg = Counter(len(n) for n in nets)
        # 基线
        pos0 = {k: (0, 0) for k in blocks}
        wl0, _ = evaluate(d, pos0)
        posS, rotS = strip_pack(blocks, S)
        wlS, _ = evaluate(d, posS, rotS)
        W = max(p[0] + (blocks[k][1] if rotS.get(k) else blocks[k][0]) for k, p in posS.items())
        H = max(p[1] + (blocks[k][0] if rotS.get(k) else blocks[k][1]) for k, p in posS.items())
        # 终端分布
        edges = [0]*4
        xmax = max(x for x, y in tp.values()); ymax = max(y for x, y in tp.values())
        for (x, y) in tp.values():
            if y < 0.5: edges[0] += 1
            elif abs(y - ymax) < 0.5: edges[1] += 1
            elif x < 0.5: edges[2] += 1
            else: edges[3] += 1
        print(f"[{name}] side={S:.2f} area={A} blocks={len(blocks)} terms={len(tp)}")
        print(f"  网: {len(nets)} 2pin={deg.get(2,0)}({deg.get(2,0)/len(nets)*100:.1f}%) 度分布={dict(sorted(deg.items()))}")
        print(f"  结构: 混合={cx} 纯块={cm} 纯终端={ct}")
        print(f"  终端分布(底/顶/左/右)={edges}")
        print(f"  HPWL: 全堆={wl0:.0f} strip={wlS:.0f} (strip占 {W:.0f}x{H:.0f})")
        print()
