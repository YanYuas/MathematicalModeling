"""
m_btree.py — 独立实现 阶段B：B*-Tree + skyline contour
建模手视角。完整二叉树（非 left-skew 退化），O(n) 解码。
左子 x = parent.x + parent.w；右子 x = parent.x；y = contour.max([x,x+w)).
"""
import random
import time
from typing import List, Tuple, Optional
from m_data import Block


class Contour:
    """skyline 轮廓：分段 (x0, x1, h) 列表，均摊 O(1) 查询/更新"""

    def __init__(self):
        self.segs = [(0.0, float('inf'), 0.0)]

    def max_in(self, x0: float, x1: float) -> float:
        mh = 0.0
        for a, b, h in self.segs:
            if a < x1 and b > x0:
                mh = max(mh, h)
        return mh

    def raise_to(self, x0: float, x1: float, h_new: float):
        out = []
        for a, b, h in self.segs:
            if b <= x0 or a >= x1:
                out.append((a, b, h))
                continue
            if a < x0:
                out.append((a, x0, h))
            oa, ob = max(a, x0), min(b, x1)
            out.append((oa, ob, h_new))
            if b > x1:
                out.append((x1, b, h))
        out.sort(key=lambda s: s[0])
        merged = []
        for s in out:
            if merged and merged[-1][1] == s[0] and abs(merged[-1][2] - s[2]) < 1e-9:
                merged[-1] = (merged[-1][0], s[1], s[2])
            else:
                merged.append(s)
        self.segs = merged


class Node:
    __slots__ = ('block', 'left', 'right', 'parent', 'x', 'y')

    def __init__(self, block: Block):
        self.block = block
        self.left = None
        self.right = None
        self.parent = None
        self.x = 0.0
        self.y = 0.0


class BTree:
    def __init__(self, blocks: List[Block]):
        self.blocks = blocks
        self.root: Optional[Node] = None
        self.nodes: dict = {}

    def pack(self) -> Tuple[float, float, float]:
        """前序解码，返回 (W, H, R)。admissible 布局天然无重叠。"""
        if self.root is None:
            return 0.0, 0.0, 1.0
        contour = Contour()
        max_w = max_h = 0.0
        stack = [(self.root, None, 'root')]
        while stack:
            nd, par, rel = stack.pop()
            if nd is None:
                continue
            bw, bh = nd.block.w, nd.block.h
            if rel == 'root':
                nd.x = 0.0
            elif rel == 'left':
                nd.x = par.x + par.block.w
            else:
                nd.x = par.x
            nd.y = contour.max_in(nd.x, nd.x + bw)
            contour.raise_to(nd.x, nd.x + bw, nd.y + bh)
            max_w = max(max_w, nd.x + bw)
            max_h = max(max_h, nd.y + bh)
            if nd.right:
                stack.append((nd.right, nd, 'right'))
            if nd.left:
                stack.append((nd.left, nd, 'left'))
        W, H = max_w, max_h
        R = max(W, H) / min(W, H) if min(W, H) > 0 else float('inf')
        return W, H, R

    def get_layout(self) -> List[Tuple[int, float, float, float, float]]:
        out = []
        for nd in self.nodes.values():
            out.append((nd.block.idx, nd.x, nd.y, nd.block.w, nd.block.h))
        return sorted(out, key=lambda t: t[0])

    def build_random(self, seed: Optional[int] = None):
        """真随机平衡树（非 left-skew），构造时用独立 block 副本防 rotate 串扰"""
        if seed is not None:
            random.seed(seed)
        blocks = [Block(b.idx, b.name, b.w, b.h) for b in self.blocks]
        self.nodes = {}
        self.root = self._subtree(blocks, None)

    def _subtree(self, blist: List[Block], parent: Optional[Node]) -> Optional[Node]:
        if not blist:
            return None
        root_b = blist[0]
        nd = Node(root_b)
        self.nodes[root_b.idx] = nd
        nd.parent = parent
        mid = random.randint(1, len(blist))
        if mid > 1:
            nd.left = self._subtree(blist[1:mid], nd)
        if mid < len(blist):
            nd.right = self._subtree(blist[mid:], nd)
        return nd

    def check_valid(self) -> bool:
        if self.root is None:
            return len(self.blocks) == 0
        if len(self.nodes) != len(self.blocks):
            return False
        seen = set()

        def walk(nd):
            if nd is None:
                return True
            if id(nd) in seen:
                return False
            seen.add(id(nd))
            if nd.left and (nd.left.parent is not nd or not walk(nd.left)):
                return False
            if nd.right and (nd.right.parent is not nd or not walk(nd.right)):
                return False
            return True
        return walk(self.root)


def check_overlap(layout) -> Tuple[bool, Optional[Tuple[int, int]]]:
    for i in range(len(layout)):
        _, x1, y1, w1, h1 = layout[i]
        for j in range(i + 1, len(layout)):
            _, x2, y2, w2, h2 = layout[j]
            if not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1):
                return False, (layout[i][0], layout[j][0])
    return True, None


if __name__ == '__main__':
    import os
    from m_data import load_blocks
    BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"

    print("=== 阶段B: B*-Tree 测试 ===")

    # Test1: 5块手动树
    sb = [Block(i, f'b{i}', w, h) for i, (w, h) in enumerate([(10, 20), (15, 15), (20, 10), (12, 18), (8, 25)])]
    t = BTree(sb)
    t.build_random(seed=42)
    W, H, R = t.pack()
    lay = t.get_layout()
    no_ov, pair = check_overlap(lay)
    print(f"[T1] 5块随机树: W={W:.1f} H={H:.1f} R={R:.2f} 无重叠={no_ov} 树有效={t.check_valid()}")
    assert no_ov and t.check_valid()

    # Test2: 三组随机树，性能+无重叠+面积守恒
    for n in ['n100', 'n200', 'n300']:
        blk = load_blocks(os.path.join(BASE, f'{n}.blocks'))
        tt = BTree(blk)
        t0 = time.time()
        tt.build_random(seed=1)
        W, H, R = tt.pack()
        dt = time.time() - t0
        A = W * H
        A_total = sum(b.area for b in blk)
        no_ov, pair = check_overlap(tt.get_layout())
        ok_perf = dt < 0.01 * len(blk)
        print(f"[T2] {n}: 随机树 W={W:.1f} H={H:.1f} R={R:.2f} A={A:.0f} A_total={A_total:.0f} "
              f"死区={(A-A_total)/A*100:.1f}% 时间={dt*1000:.1f}ms 无重叠={no_ov} 性能={'OK' if ok_perf else 'FAIL'}")
        assert no_ov and tt.check_valid() and ok_perf and A >= A_total - 1

    print("\n阶段B: ALL PASS")
