"""
m_operators.py — 独立实现 阶段C：三扰动算子
Op1 旋转 (rotate block w/h) / Op2 删插 (delete+reinsert node) / Op3 交换 (swap block refs)
建模手理论概率：rotate 0.1 / move 0.5 / swap 0.4
"""
import random
from typing import List, Tuple
from m_btree import BTree, Node


def op1_rotate(tree: BTree) -> None:
    nd = random.choice(list(tree.nodes.values()))
    nd.block.rotate()


def op2_delete_insert(tree: BTree) -> None:
    if len(tree.nodes) < 2:
        return
    nd = random.choice(list(tree.nodes.values()))
    _delete(tree, nd)
    _insert(tree, nd)


def op3_swap(tree: BTree) -> None:
    if len(tree.nodes) < 2:
        return
    n1, n2 = random.sample(list(tree.nodes.values()), 2)
    n1.block, n2.block = n2.block, n1.block


def _delete(tree: BTree, nd: Node):
    par = nd.parent
    is_l = par is not None and par.left is nd
    is_r = par is not None and par.right is nd
    if nd.left is None and nd.right is None:
        if par:
            if is_l:
                par.left = None
            else:
                par.right = None
        else:
            tree.root = None
    elif nd.left is None:
        child = nd.right
        if par:
            if is_l:
                par.left = child
            else:
                par.right = child
        else:
            tree.root = child
        child.parent = par
    elif nd.right is None:
        child = nd.left
        if par:
            if is_l:
                par.left = child
            else:
                par.right = child
        else:
            tree.root = child
        child.parent = par
    else:
        L, R = nd.left, nd.right
        if par:
            if is_l:
                par.left = L
            else:
                par.right = L
        else:
            tree.root = L
        L.parent = par
        rm = L
        while rm.right is not None:
            rm = rm.right
        rm.right = R
        R.parent = rm
    nd.parent = nd.left = nd.right = None


def _insert(tree: BTree, nd: Node):
    if tree.root is None:
        tree.root = nd
        return
    cands = [n for n in tree.nodes.values() if n is not nd]
    if not cands:
        tree.root = nd
        return
    par = random.choice(cands)
    if random.random() < 0.5:
        old = par.left
        par.left = nd
        nd.parent = par
        if old:
            nd.left = old
            old.parent = nd
    else:
        old = par.right
        par.right = nd
        nd.parent = par
        if old:
            nd.right = old
            old.parent = nd


def random_perturbation(tree: BTree, probs: Tuple[float, float, float] = (0.1, 0.5, 0.4)) -> None:
    p = [x / sum(probs) for x in probs]
    r = random.random()
    if r < p[0]:
        op1_rotate(tree)
    elif r < p[0] + p[1]:
        op2_delete_insert(tree)
    else:
        op3_swap(tree)


if __name__ == '__main__':
    import os
    from m_data import load_blocks
    BASE = r"C:\Users\21722\Desktop\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件"
    blk = load_blocks(os.path.join(BASE, 'n100.blocks'))

    t = BTree(blk)
    t.build_random(seed=7)
    init_nodes = set(id(n) for n in t.nodes.values())
    W0, H0, _ = t.pack()

    random.seed(0)
    counts = [0, 0, 0]
    for i in range(2000):
        op = random.random()
        if op < 0.1:
            counts[0] += 1
            op1_rotate(t)
        elif op < 0.6:
            counts[1] += 1
            op2_delete_insert(t)
        else:
            counts[2] += 1
            op3_swap(t)
        assert t.check_valid(), f"树失效 iter {i}"
        assert set(id(n) for n in t.nodes.values()) == init_nodes, f"node 集变化 iter {i}"

    W1, H1, _ = t.pack()
    print(f"[C] 2000次扰动后 树有效, node集不变")
    print(f"    初始 W={W0:.1f} H={H0:.1f} → 最终 W={W1:.1f} H={H1:.1f} (维度变化={'是' if abs(W0-W1)+abs(H0-H1)>0.1 else '否'})")
    print(f"    算子分布: Op1={counts[0]} Op2={counts[1]} Op3={counts[2]} (期望 200/1000/800)")
    assert abs(counts[0]-200) < 80 and abs(counts[1]-1000) < 120 and abs(counts[2]-800) < 120
    print("阶段C: ALL PASS")
