# -*- coding: utf-8 -*-
"""m2_hpwl.py — Q2 独立实现 阶段P1：HPWL 评估器
引脚 = 模块几何中心（旋转后中心变 (x+h/2, y+w/2)）；终端 = 固定坐标(.pl)。
HPWL(net) = (max_x - min_x) + (max_y - min_y)。
独立实现，基线复现验证正确性。
"""
import math
from m2_data import Block, load


def evaluate(data, pos, rot=None, sizes=None):
    """pos: {name:(x,y)} 左下角; rot: {name:bool(已旋转)}; sizes: {name:(w,h)} 当前方向（优先）.
    返回 (total_hpwl, per_net_list, pin_dict)."""
    pins = {}
    for name in data['blocks']:
        x, y = pos[name]
        if sizes is not None:
            ww, hh = sizes[name]
        else:
            w, h = data['blocks'][name]
            if rot is not None and rot.get(name):
                ww, hh = h, w
            else:
                ww, hh = w, h
        pins[name] = (x + ww / 2.0, y + hh / 2.0)
    for name, (x, y) in data['term_pos'].items():
        pins[name] = (float(x), float(y))

    total = 0.0
    per_net = []
    for net in data['nets']:
        xs = [pins[p][0] for p in net]
        ys = [pins[p][1] for p in net]
        h = (max(xs) - min(xs)) + (max(ys) - min(ys))
        total += h
        per_net.append(h)
    return total, per_net, pins


def terminal_vs_internal(data, pos, rot=None, sizes=None):
    """按网型分解：I/O 网（含终端）vs 内部网（纯模块）的 HPWL 贡献。"""
    _, per_net, pins = evaluate(data, pos, rot, sizes)
    io_total, in_total = 0.0, 0.0
    for net, h in zip(data['nets'], per_net):
        has_term = any(p in data['term_pos'] for p in net)
        if has_term:
            io_total += h
        else:
            in_total += h
    return io_total, in_total


def pack_dims(data, pos, rot=None):
    """当前布局的包围盒 W×H。"""
    if rot is None:
        rot = {}
    W = H = 0.0
    for name, (x, y) in pos.items():
        w, h = data['blocks'][name]
        if rot.get(name):
            w, h = h, w
        W = max(W, x + w)
        H = max(H, y + h)
    return W, H


def all_zero(data):
    """基线1：全堆 (0,0)（重叠，仅测尺度）。"""
    pos = {k: (0.0, 0.0) for k in data['blocks']}
    wl, _, _ = evaluate(data, pos)
    return wl


def ffd_stack(data, target=None):
    """基线2：FFD 行堆叠（独立实现，Q1 构造法）。返回 (pos, rot, W, H)。"""
    if target is None:
        target = data['side']
    blk = [Block(i, name, w, h) for i, (name, (w, h)) in enumerate(data['blocks'].items())]
    # 降序排面积
    blk.sort(key=lambda b: -b.area)
    pos, rot = {}, {}
    x = y = 0.0
    row_h = 0.0
    for b in blk:
        w, h = b.w, b.h
        if x + w > target + 1e-9 and x > 0:
            x = 0.0
            y += row_h
            row_h = 0.0
        pos[b.name] = (x, y)
        rot[b.name] = False
        x += w
        row_h = max(row_h, h)
    W, H = pack_dims(data, pos, rot)
    return pos, rot, W, H


if __name__ == '__main__':
    print('=== 阶段P1: HPWL 评估器验证 ===')
    for name in ['n100', 'n200', 'n300']:
        d = load(name)
        # 基线1: 全堆(0,0)
        wl0 = all_zero(d)
        # 基线2: FFD 行堆叠
        pos2, rot2, W, H = ffd_stack(d)
        wl2, per2, pins = evaluate(d, pos2, rot2)
        io_t, in_t = terminal_vs_internal(d, pos2, rot2)
        print(f'{name}: 全堆={wl0:,.0f}  FFD={wl2:,.0f}  FFD占用={W:.0f}x{H:.0f} '
              f'I/O网={io_t:,.0f} 内部网={in_t:,.0f}')
    print('阶段P1: 评估器就绪')
