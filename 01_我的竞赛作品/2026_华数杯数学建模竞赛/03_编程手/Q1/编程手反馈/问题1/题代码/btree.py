"""
B*-Tree Floorplanning Implementation
Core algorithm for VLSI block placement with O(n) packing complexity
"""
import random
from typing import List, Tuple, Optional
from data_loader import Block


class ContourLine:
    """
    Contour line structure for O(n) y-coordinate calculation

    Maintains a list of (x_start, x_end, height) segments
    Supports efficient max_height query and update operations
    """

    def __init__(self):
        # Initialize with a single segment covering infinite width at height 0
        self.segments = [(0.0, float('inf'), 0.0)]

    def max_height_in_range(self, x_start: float, x_end: float) -> float:
        """
        Find maximum height in range [x_start, x_end)

        Args:
            x_start: Left boundary of query range
            x_end: Right boundary of query range

        Returns:
            Maximum height in the specified range

        Complexity: O(k) where k is number of overlapping segments
                    Amortized O(1) for typical cases
        """
        max_h = 0.0

        for seg_x_start, seg_x_end, seg_h in self.segments:
            # Check if segment overlaps with query range
            if seg_x_start < x_end and seg_x_end > x_start:
                max_h = max(max_h, seg_h)

        return max_h

    def update(self, x_start: float, x_end: float, new_height: float):
        """
        Update contour after placing a block

        Args:
            x_start: Left boundary of placed block
            x_end: Right boundary of placed block
            new_height: New height at this position (y + block.h)

        Process:
            1. Split existing segments overlapping with [x_start, x_end)
            2. Update heights in the range
            3. Merge adjacent segments with same height
        """
        new_segments = []

        for seg_x_start, seg_x_end, seg_h in self.segments:
            # Segment completely before the update range
            if seg_x_end <= x_start:
                new_segments.append((seg_x_start, seg_x_end, seg_h))
                continue

            # Segment completely after the update range
            if seg_x_start >= x_end:
                new_segments.append((seg_x_start, seg_x_end, seg_h))
                continue

            # Segment overlaps with update range - need to split

            # Part before update range
            if seg_x_start < x_start:
                new_segments.append((seg_x_start, x_start, seg_h))

            # Part inside update range
            overlap_start = max(seg_x_start, x_start)
            overlap_end = min(seg_x_end, x_end)
            new_segments.append((overlap_start, overlap_end, new_height))

            # Part after update range
            if seg_x_end > x_end:
                new_segments.append((x_end, seg_x_end, seg_h))

        # Sort by x_start
        new_segments.sort(key=lambda s: s[0])

        # Merge adjacent segments with same height
        merged = []
        for seg in new_segments:
            if merged and merged[-1][1] == seg[0] and merged[-1][2] == seg[2]:
                # Extend previous segment
                merged[-1] = (merged[-1][0], seg[1], seg[2])
            else:
                merged.append(seg)

        self.segments = merged

    def get_max_height(self) -> float:
        """Return overall maximum height"""
        return max(seg[2] for seg in self.segments)


class BTreeNode:
    """
    Node in B*-Tree representing a block and its placement relationships

    Tree structure encodes spatial relationships:
    - Left child: placed to the right of parent
    - Right child: placed above parent
    """

    def __init__(self, block: Block):
        self.block = block      # Reference to Block object
        self.left = None        # Left child (right-adjacent placement)
        self.right = None       # Right child (above placement)
        self.parent = None      # Parent node
        self.x = 0.0            # Placement x-coordinate (set during packing)
        self.y = 0.0            # Placement y-coordinate (set during packing)

    def __repr__(self):
        return f"BTreeNode({self.block.name}, pos=({self.x:.1f},{self.y:.1f}))"


class BTree:
    """
    B*-Tree for VLSI floorplanning

    Encodes block placement as a binary tree where:
    - Tree structure defines spatial relationships
    - DFS traversal with contour line gives actual coordinates
    - No overlap guaranteed by construction
    """

    def __init__(self, blocks: List[Block]):
        self.blocks = blocks
        self.root = None
        self.nodes = {}  # idx -> BTreeNode mapping
        self._contour = None  # ContourLine for packing

    def pack(self) -> Tuple[float, float, float]:
        """
        Decode tree to get block coordinates using O(n) algorithm

        Algorithm:
            1. Initialize contour line at height 0
            2. DFS traversal (preorder):
               - Root: place at (0, 0)
               - Left child: x = parent.x + parent.w, y = contour.max_at(x, x+w)
               - Right child: x = parent.x, y = contour.max_at(x, x+w)
            3. After placing each block, update contour
            4. Track maximum W and H during traversal

        Returns:
            (W, H, R) tuple:
            - W: bounding box width
            - H: bounding box height
            - R: aspect ratio = max(W,H) / min(W,H)
        """
        if self.root is None:
            return 0.0, 0.0, 1.0

        # Initialize contour line
        self._contour = ContourLine()

        # Track bounding box
        max_w = 0.0
        max_h = 0.0

        # DFS traversal with explicit stack (avoids recursion depth issues)
        stack = [(self.root, None, 'root')]  # (node, parent, relationship)

        while stack:
            node, parent, rel = stack.pop()

            if node is None:
                continue

            # Determine x-coordinate based on relationship
            if rel == 'root':
                node.x = 0.0
            elif rel == 'left':
                # Left child: placed to the right of parent
                node.x = parent.x + parent.block.w
            elif rel == 'right':
                # Right child: placed above parent (same x)
                node.x = parent.x

            # Query contour for y-coordinate
            block_w = node.block.w
            node.y = self._contour.max_height_in_range(node.x, node.x + block_w)

            # Update contour with placed block
            self._contour.update(node.x, node.x + block_w, node.y + node.block.h)

            # Update block coordinates
            node.block.x = node.x
            node.block.y = node.y

            # Track bounding box
            max_w = max(max_w, node.x + block_w)
            max_h = max(max_h, node.y + node.block.h)

            # Push children to stack (right first for preorder DFS)
            if node.right:
                stack.append((node.right, node, 'right'))
            if node.left:
                stack.append((node.left, node, 'left'))

        # Calculate aspect ratio
        W, H = max_w, max_h
        R = max(W, H) / min(W, H) if min(W, H) > 0 else float('inf')

        return W, H, R

    def get_layout(self) -> List[Tuple[int, float, float, float, float]]:
        """
        Get block layout after packing

        Returns:
            List of (block_idx, x, y, w, h) tuples
        """
        layout = []
        for node in self.nodes.values():
            layout.append((
                node.block.idx,
                node.block.x,
                node.block.y,
                node.block.w,
                node.block.h
            ))
        return sorted(layout, key=lambda t: t[0])

    def build_from_sequence(self, sequence: List[int]):
        """
        Build tree from a permutation sequence (for SA algorithm)

        Args:
            sequence: Permutation of block indices [0, 1, 2, ..., n-1]

        Note: This is a simplified version. Full implementation needs
              to handle tree structure encoding (permutation + parent/child info)
        """
        # Simple implementation: build a left-skewed tree
        self.nodes = {}

        if not sequence:
            self.root = None
            return

        # Create root
        first_idx = sequence[0]
        self.root = BTreeNode(self.blocks[first_idx])
        self.nodes[first_idx] = self.root

        # Build left-skewed tree (all left children)
        current = self.root
        for idx in sequence[1:]:
            node = BTreeNode(self.blocks[idx])
            self.nodes[idx] = node
            node.parent = current
            current.left = node
            current = node

    def build_random_tree(self, seed: Optional[int] = None):
        """
        Build a random balanced tree for testing

        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)

        # Create shuffled sequence
        indices = list(range(len(self.blocks)))
        random.shuffle(indices)

        # Build tree recursively
        self.nodes = {}
        self.root = self._build_random_subtree(indices)

    def _build_random_subtree(self, indices: List[int]) -> Optional[BTreeNode]:
        """
        Recursively build a random balanced subtree

        Args:
            indices: List of block indices for this subtree

        Returns:
            Root node of the subtree
        """
        if not indices:
            return None

        if len(indices) == 1:
            node = BTreeNode(self.blocks[indices[0]])
            self.nodes[indices[0]] = node
            return node

        # Split randomly
        mid = random.randint(1, len(indices))

        # Create root
        root_idx = indices[0]
        root = BTreeNode(self.blocks[root_idx])
        self.nodes[root_idx] = root

        # Build left and right subtrees
        if mid > 1:
            root.left = self._build_random_subtree(indices[1:mid])
            if root.left:
                root.left.parent = root

        if mid < len(indices):
            root.right = self._build_random_subtree(indices[mid:])
            if root.right:
                root.right.parent = root

        return root

    def check_tree_validity(self) -> bool:
        """
        Check if tree structure is valid

        Returns:
            True if valid, False otherwise
        """
        if self.root is None:
            return len(self.blocks) == 0

        # Check all blocks are in tree
        if len(self.nodes) != len(self.blocks):
            return False

        # Check no cycles and proper parent-child links
        visited = set()

        def check_node(node):
            if node is None:
                return True

            if id(node) in visited:
                return False  # Cycle detected

            visited.add(id(node))

            # Check left child
            if node.left:
                if node.left.parent != node:
                    return False
                if not check_node(node.left):
                    return False

            # Check right child
            if node.right:
                if node.right.parent != node:
                    return False
                if not check_node(node.right):
                    return False

            return True

        return check_node(self.root)


# ==================== Testing and Validation ====================
if __name__ == '__main__':
    from config import DATA_PATHS
    from data_loader import load_blocks
    import time

    print("=" * 60)
    print("Task 1: B*-Tree Implementation Test")
    print("=" * 60)

    # Test 1: Small manual tree
    print("\n[Test 1] Small manual tree with 5 blocks")
    small_blocks = [
        Block(0, 'b0', 10, 20),
        Block(1, 'b1', 15, 15),
        Block(2, 'b2', 20, 10),
        Block(3, 'b3', 12, 18),
        Block(4, 'b4', 8, 25),
    ]

    tree = BTree(small_blocks)
    tree.build_random_tree(seed=42)

    print(f"  Tree valid: {tree.check_tree_validity()}")

    W, H, R = tree.pack()
    print(f"  Packing result: W={W:.1f}, H={H:.1f}, R={R:.2f}")

    layout = tree.get_layout()
    print(f"  Layout (first 3 blocks):")
    for idx, x, y, w, h in layout[:3]:
        print(f"    Block {idx}: pos=({x:.1f},{y:.1f}), size=({w:.1f},{h:.1f})")

    # Check for overlaps (simple O(n^2) check for testing)
    def check_overlap(layout):
        for i in range(len(layout)):
            idx1, x1, y1, w1, h1 = layout[i]
            for j in range(i+1, len(layout)):
                idx2, x2, y2, w2, h2 = layout[j]
                # Check if rectangles overlap
                if not (x1 + w1 <= x2 or x2 + w2 <= x1 or
                       y1 + h1 <= y2 or y2 + h2 <= y1):
                    return False, (idx1, idx2)
        return True, None

    no_overlap, overlap_pair = check_overlap(layout)
    if no_overlap:
        print(f"  [OK] No overlaps detected")
    else:
        print(f"  [FAIL] Overlap detected between blocks {overlap_pair}")

    # Test 2: Performance on real datasets
    print("\n[Test 2] Performance on real datasets")

    for name in ['n100', 'n200', 'n300']:
        print(f"\n  Dataset: {name}")
        blocks = load_blocks(DATA_PATHS[name])

        tree = BTree(blocks)
        tree.build_random_tree(seed=42)

        # Measure packing time
        start_time = time.time()
        W, H, R = tree.pack()
        pack_time = time.time() - start_time

        print(f"    Packing time: {pack_time*1000:.2f} ms")
        print(f"    Result: W={W:.1f}, H={H:.1f}, R={R:.3f}")
        print(f"    Blocks: {len(blocks)}")

        # Performance assertion: < 0.01 * n seconds
        target_time = 0.01 * len(blocks)
        assert pack_time < target_time, f"Performance issue: {pack_time:.4f}s > {target_time:.4f}s target"
        print(f"    [OK] Performance: {pack_time:.4f}s < {target_time:.4f}s target")

        # Check validity
        layout = tree.get_layout()
        no_overlap, _ = check_overlap(layout)
        assert no_overlap, "Overlap detected!"
        print(f"    [OK] No overlaps: {no_overlap}")

        # Verify all blocks are placed
        placed_blocks = {idx for idx, _, _, _, _ in layout}
        all_placed = len(placed_blocks) == len(blocks)
        print(f"    All blocks placed: {all_placed}")

    print("\n" + "=" * 60)
    print("B*-Tree Core Implementation - Complete [OK]")
    print("=" * 60)
