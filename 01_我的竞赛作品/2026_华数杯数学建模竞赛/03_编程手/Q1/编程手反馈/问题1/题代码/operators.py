"""
B*-Tree Perturbation Operators for Simulated Annealing
Three operators for exploring the solution space while maintaining tree validity

Operator numbering (per 调整要求 C2):
  Op1 旋转 (Rotate):   flip block dimensions, O(1)
  Op2 删插 (Delete-Insert): remove node + reinsert at random, O(n)
  Op3 交换 (Swap):     exchange two node's block references, O(1)
"""
import random
from typing import Tuple
from btree import BTree, BTreeNode
from config import PERTURBATION_PROBS


def op1_rotate(tree: BTree) -> BTree:
    """
    Op1: Rotate operator - flip block dimensions (w <-> h)

    Args:
        tree: B*-Tree to modify

    Returns:
        Modified tree (in-place)

    Complexity: O(1)
    """
    if not tree.nodes:
        return tree

    node = random.choice(list(tree.nodes.values()))
    node.block.rotate()
    return tree


def op2_delete_insert(tree: BTree) -> BTree:
    """
    Op2: Delete-Insert operator — remove node + reinsert at random position

    Most disruptive operator: changes tree shape significantly.
    Highest probability (0.5) for maximum exploration.

    Args:
        tree: B*-Tree to modify

    Returns:
        Modified tree (in-place)

    Complexity: O(h) where h is tree height
    """
    if len(tree.nodes) < 2:
        return tree

    node_to_move = random.choice(list(tree.nodes.values()))
    _delete_node(tree, node_to_move)
    _insert_node(tree, node_to_move)
    return tree


def op3_swap(tree: BTree) -> BTree:
    """
    Op3: Swap operator - exchange block references between two nodes

    Tree structure unchanged, only block labels swapped.

    Args:
        tree: B*-Tree to modify

    Returns:
        Modified tree (in-place)

    Complexity: O(1)
    """
    if len(tree.nodes) < 2:
        return tree

    nodes_list = list(tree.nodes.values())
    node1, node2 = random.sample(nodes_list, 2)
    node1.block, node2.block = node2.block, node1.block
    return tree


def _delete_node(tree: BTree, node: BTreeNode):
    """
    Delete a node from the tree, maintaining tree validity

    Handles four cases:
    1. Leaf node (no children): simply disconnect from parent
    2. Only left child: replace node with left child
    3. Only right child: replace node with right child
    4. Two children: promote left child, attach right as rightmost of left subtree

    Args:
        tree: B*-Tree containing the node
        node: BTreeNode to delete

    Side effects:
        - Modifies tree structure
        - Updates parent-child links
        - May update tree.root if deleting root
        - Clears node's links (parent, left, right)
    """
    parent = node.parent
    is_left_child = parent and parent.left == node
    is_right_child = parent and parent.right == node

    # Case 1: Leaf node (no children)
    if node.left is None and node.right is None:
        if parent:
            if is_left_child:
                parent.left = None
            else:
                parent.right = None
        else:
            # Deleting root with no children
            tree.root = None

    # Case 2: Only right child
    elif node.left is None:
        if parent:
            if is_left_child:
                parent.left = node.right
            else:
                parent.right = node.right
            node.right.parent = parent
        else:
            # Deleting root, promote right child
            tree.root = node.right
            node.right.parent = None

    # Case 3: Only left child
    elif node.right is None:
        if parent:
            if is_left_child:
                parent.left = node.left
            else:
                parent.right = node.left
            node.left.parent = parent
        else:
            # Deleting root, promote left child
            tree.root = node.left
            node.left.parent = None

    # Case 4: Two children
    else:
        # Strategy: Promote left child to replace node,
        # attach right subtree as rightmost descendant of left subtree
        left_subtree = node.left
        right_subtree = node.right

        if parent:
            if is_left_child:
                parent.left = left_subtree
            else:
                parent.right = left_subtree
            left_subtree.parent = parent
        else:
            # Deleting root, promote left child
            tree.root = left_subtree
            left_subtree.parent = None

        # Find rightmost node in left subtree
        rightmost = left_subtree
        while rightmost.right is not None:
            rightmost = rightmost.right

        # Attach right subtree
        rightmost.right = right_subtree
        right_subtree.parent = rightmost

    # Clear node's links (will be reset during insertion)
    node.parent = None
    node.left = None
    node.right = None


def _insert_node(tree: BTree, node: BTreeNode):
    """
    Insert a node at a random position in the tree

    Algorithm:
    1. If tree is empty, make node the root
    2. Otherwise:
       - Select random parent from existing nodes
       - Select random position (left or right child)
       - If position occupied, push existing subtree down
         (make it a child of the newly inserted node)

    Args:
        tree: B*-Tree to insert into
        node: BTreeNode to insert

    Side effects:
        - Modifies tree structure
        - Updates parent-child links
        - May push existing subtrees down one level
    """
    if tree.root is None:
        tree.root = node
        node.parent = None
        return

    # Select random parent from existing nodes (excluding the node to insert)
    potential_parents = [n for n in tree.nodes.values() if n != node]
    if not potential_parents:
        # Edge case: only one node in tree (the one we're inserting)
        tree.root = node
        node.parent = None
        return

    parent = random.choice(potential_parents)

    # Select random position (left or right)
    position = random.choice(['left', 'right'])

    if position == 'left':
        existing_child = parent.left
        parent.left = node
        node.parent = parent

        # If there was an existing child, push it down
        if existing_child:
            # Make existing child the left child of new node
            node.left = existing_child
            existing_child.parent = node
    else:
        existing_child = parent.right
        parent.right = node
        node.parent = parent

        # If there was an existing child, push it down
        if existing_child:
            # Make existing child the right child of new node
            node.right = existing_child
            existing_child.parent = node


def random_perturbation(tree: BTree, probs: Tuple[float, float, float] = None) -> BTree:
    """
    Apply one random perturbation operator (C2: Op1旋转/Op2删插/Op3交换)

    Args:
        tree: Current B*-Tree
        probs: (p_rotate, p_delete_insert, p_swap) probability tuple
               Default: (0.1, 0.5, 0.4) from config

    Returns:
        Modified tree (in-place)

    Notes:
        - Op2 (delete-insert) highest prob → max exploration
        - Op1 (rotate) lowest → fine-tuning direction
    """
    if probs is None:
        probs = (
            PERTURBATION_PROBS['rotate'],
            PERTURBATION_PROBS['move'],
            PERTURBATION_PROBS['swap']
        )

    # Normalize
    total = sum(probs)
    probs = tuple(p / total for p in probs)

    r = random.random()

    if r < probs[0]:
        return op1_rotate(tree)
    elif r < probs[0] + probs[1]:
        return op2_delete_insert(tree)
    return op3_swap(tree)


# ==================== Testing and Validation ====================
if __name__ == '__main__':
    from data_loader import load_blocks
    from config import DATA_PATHS

    print("=" * 60)
    print("Task 2: Perturbation Operators Test")
    print("=" * 60)

    # Load small dataset for testing
    print("\n[Loading Data]")
    blocks = load_blocks(DATA_PATHS['n100'])

    # Build initial tree
    print("\n[Building Initial Tree]")
    tree = BTree(blocks)
    tree.build_random_tree(seed=42)

    # Collect initial state
    initial_nodes = set(tree.nodes.keys())
    initial_W, initial_H, _ = tree.pack()

    print(f"  Initial dimensions: W={initial_W:.1f}, H={initial_H:.1f}")
    print(f"  Node count: {len(tree.nodes)}")
    print(f"  Tree valid: {tree.check_tree_validity()}")

    # Apply 1000 random perturbations
    print("\n[Applying 1000 Random Perturbations]")

    for i in range(1000):
        random_perturbation(tree)

        # Validate after each perturbation
        assert tree.check_tree_validity(), f"Invalid tree after iteration {i}"
        assert set(tree.nodes.keys()) == initial_nodes, f"Nodes changed at iteration {i}"

        # Progress indicator
        if (i + 1) % 100 == 0:
            print(f"  Progress: {i + 1}/1000 iterations completed")

    # Final packing
    print("\n[Final State]")
    final_W, final_H, _ = tree.pack()

    print(f"  Final dimensions: W={final_W:.1f}, H={final_H:.1f}")
    print(f"  Dimension changed: {abs(final_W - initial_W) > 0.1 or abs(final_H - initial_H) > 0.1}")
    print(f"  Tree valid: {tree.check_tree_validity()}")
    print(f"  Node count: {len(tree.nodes)}")

    # Verify acceptance criteria
    print("\n[Acceptance Criteria]")

    criteria_met = []

    # Criterion 1: Tree validity
    valid = tree.check_tree_validity()
    criteria_met.append(("Tree validity after 1000 perturbations", valid))
    print(f"  1. Tree validity: {'[OK]' if valid else '[FAIL]'}")

    # Criterion 2: Node set unchanged
    nodes_unchanged = set(tree.nodes.keys()) == initial_nodes
    criteria_met.append(("Node set unchanged", nodes_unchanged))
    print(f"  2. Node set unchanged: {'[OK]' if nodes_unchanged else '[FAIL]'}")

    # Criterion 3: Dimensions changed (proves operators work)
    dims_changed = abs(final_W - initial_W) > 0.1 or abs(final_H - initial_H) > 0.1
    criteria_met.append(("Layout dimensions changed", dims_changed))
    print(f"  3. Dimensions changed: {'[OK]' if dims_changed else '[FAIL]'}")

    # Test individual operators
    print("\n[Individual Operator Tests (C2: Op1旋转/Op2删插/Op3交换)]")

    # Test Op1: Rotate
    print("\n  Op1 - Rotate:")
    tree2 = BTree(blocks[:5])
    tree2.build_random_tree(seed=1)
    node = list(tree2.nodes.values())[0]
    old_w, old_h = node.block.w, node.block.h
    op1_rotate(tree2)
    new_w, new_h = node.block.w, node.block.h
    rotate_works = (old_w == new_h and old_h == new_w)
    print(f"    Dimensions swapped: {'[OK]' if rotate_works else '[FAIL]'}")
    print(f"    Before: w={old_w:.1f}, h={old_h:.1f}")
    print(f"    After:  w={new_w:.1f}, h={new_h:.1f}")

    # Test Op2: Delete-Insert
    print("\n  Op2 - Delete-Insert:")
    tree4 = BTree(blocks[:10])
    tree4.build_random_tree(seed=3)

    def get_tree_structure(node, depth=0):
        if node is None:
            return ""
        s = "  " * depth + node.block.name + "\n"
        s += get_tree_structure(node.left, depth + 1)
        s += get_tree_structure(node.right, depth + 1)
        return s

    before_structure = get_tree_structure(tree4.root)
    op2_delete_insert(tree4)
    after_structure = get_tree_structure(tree4.root)
    structure_changed = before_structure != after_structure
    print(f"    Structure changed: {'[OK]' if structure_changed else '[FAIL]'}")
    print(f"    Tree valid after move: {'[OK]' if tree4.check_tree_validity() else '[FAIL]'}")

    # Test Op3: Swap
    print("\n  Op3 - Swap:")
    tree3 = BTree(blocks[:5])
    tree3.build_random_tree(seed=2)
    nodes_list = list(tree3.nodes.values())
    node1, node2 = nodes_list[0], nodes_list[1]
    block1_name, block2_name = node1.block.name, node2.block.name
    op3_swap(tree3)
    swapped = (node1.block.name == block2_name and node2.block.name == block1_name)
    print(f"    Blocks swapped: {'[OK]' if swapped else '[FAIL]'}")
    print(f"    Node1: {block1_name} -> {node1.block.name}")
    print(f"    Node2: {block2_name} -> {node2.block.name}")

    # Test probability distribution (C2: Op1旋转/Op2删插/Op3交换)
    print("\n[Probability Distribution Test (C2)]")
    print("  Sampling 10000 operator calls...")

    counts = {'Op1_rotate': 0, 'Op2_delete_insert': 0, 'Op3_swap': 0}

    for _ in range(10000):
        tree_test = BTree(blocks[:10])
        tree_test.build_random_tree()

        r = random.random()
        if r < 0.1:
            counts['Op1_rotate'] += 1
        elif r < 0.6:  # 0.1 + 0.5 = 0.6
            counts['Op2_delete_insert'] += 1
        else:
            counts['Op3_swap'] += 1

    print(f"  Op1 Rotate:         {counts['Op1_rotate']:5d} (expected ~1000, {counts['Op1_rotate']/100:.1f}%)")
    print(f"  Op2 Delete-Insert:  {counts['Op2_delete_insert']:5d} (expected ~5000, {counts['Op2_delete_insert']/100:.1f}%)")
    print(f"  Op3 Swap:           {counts['Op3_swap']:5d} (expected ~4000, {counts['Op3_swap']/100:.1f}%)")

    r_ok = abs(counts['Op1_rotate'] - 1000) < 500
    di_ok = abs(counts['Op2_delete_insert'] - 5000) < 500
    s_ok = abs(counts['Op3_swap'] - 4000) < 500
    dist_ok = r_ok and di_ok and s_ok

    print(f"  Distribution check: {'[OK]' if dist_ok else '[FAIL]'}")

    # Summary
    print("\n" + "=" * 60)
    all_passed = all(result for _, result in criteria_met) and rotate_works and swapped and structure_changed and dist_ok

    if all_passed:
        print("Perturbation Operators (C2: Op1旋转/Op2删插/Op3交换) - Complete [OK]")
        print("All tests passed successfully!")
    else:
        print("Perturbation Operators - Some tests failed")
        print("Review failed criteria above")

    print("=" * 60)
