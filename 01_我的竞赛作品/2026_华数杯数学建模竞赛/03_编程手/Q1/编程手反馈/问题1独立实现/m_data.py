"""
m_data.py — 独立实现 阶段A：数据加载
建模手视角，与编程手 data_loader 独立。
解析 .blocks，提取模块 w/h，面积校验，长条统计。
"""
import math
import re
from dataclasses import dataclass
from typing import List

EXPECTED_AREAS = {'n100': 179501, 'n200': 175696, 'n300': 273170}

@dataclass
class Block:
    idx: int
    name: str
    w: float
    h: float
    rotated: bool = False

    @property
    def area(self) -> float:
        return self.w * self.h

    def aspect_ratio(self) -> float:
        m = min(self.w, self.h)
        return max(self.w, self.h) / m if m > 0 else float('inf')

    def rotate(self):
        self.w, self.h = self.h, self.w
        self.rotated = not self.rotated


def load_blocks(filepath: str) -> List[Block]:
    blocks = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('Num'):
                continue
            if 'block' not in line or 'terminal' in line:
                continue
            mname = re.match(r'(\w+)\s+block', line)
            if not mname:
                continue
            coords = re.findall(r'\((\d+),\s*(\d+)\)', line)
            if len(coords) != 4:
                continue
            xs = [int(x) for x, _ in coords]
            ys = [int(y) for _, y in coords]
            w = max(xs) - min(xs)
            h = max(ys) - min(ys)
            if w <= 0 or h <= 0:
                continue
            blocks.append(Block(len(blocks), mname.group(1), float(w), float(h)))
    return blocks


def verify(blocks: List[Block], name: str) -> bool:
    total = sum(b.area for b in blocks)
    ok = abs(total - EXPECTED_AREAS[name]) < 1
    strips = [b for b in blocks if b.aspect_ratio() >= 2.5]
    maxar = max(b.aspect_ratio() for b in blocks)
    print(f"[{name}] blocks={len(blocks)} A_total={total:.0f} (exp {EXPECTED_AREAS[name]}) "
          f"verify={'OK' if ok else 'FAIL'}")
    print(f"        strips(AR>=2.5)={len(strips)} max_AR={maxar:.2f} max_block_w={max(b.w for b in blocks):.0f}")
    return ok


if __name__ == '__main__':
    import os
    BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"
    all_ok = True
    for n in ['n100', 'n200', 'n300']:
        blk = load_blocks(os.path.join(BASE, f'{n}.blocks'))
        all_ok &= verify(blk, n)
    print(f"\n阶段A: {'ALL PASS' if all_ok else 'FAIL'}")
