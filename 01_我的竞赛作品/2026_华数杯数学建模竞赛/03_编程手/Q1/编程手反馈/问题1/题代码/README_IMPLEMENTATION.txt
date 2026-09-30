================================================================================
B*-Tree Floorplanning Implementation - Quick Reference
================================================================================

COMPLETED TASKS:
  [OK] Task 0: Data Loader (data_loader.py)
  [OK] Task 1: B*-Tree Core Structure (btree.py)

================================================================================
1. DATA LOADER MODULE (data_loader.py)
================================================================================

Classes:
--------
Block(idx, name, w, h)
  - Properties: idx, name, w, h, area, rotated, x, y
  - Methods:
    * rotate(): Swap w and h, toggle rotated flag
    * aspect_ratio(): Return max(w,h) / min(w,h)

Functions:
----------
parse_block_line(line) -> (name, width, height)
  - Extracts block info from .blocks file format
  - Format: "bX block 4 (x1,y1) (x2,y2) (x3,y3) (x4,y4)"

load_blocks(filepath) -> List[Block]
  - Loads and validates .blocks file
  - Auto-detects dataset (n100/n200/n300) by total area
  - Prints validation summary

get_block_stats(blocks) -> dict
  - Returns: count, total_area, min/max/avg area, aspect ratios

Usage Example:
--------------
from data_loader import load_blocks
from config import DATA_PATHS

blocks = load_blocks(DATA_PATHS['n100'])
# Output: [OK] Data loaded [n100], 100 blocks, area=179501

================================================================================
2. B*-TREE MODULE (btree.py)
================================================================================

Classes:
--------
ContourLine()
  - Maintains (x_start, x_end, height) segments
  - Methods:
    * max_height_in_range(x_start, x_end): Query max height in range
    * update(x_start, x_end, new_height): Update contour after placement
    * get_max_height(): Return overall max height
  - Complexity: O(1) amortized per operation

BTreeNode(block)
  - Properties: block, left, right, parent, x, y
  - Represents one block and its spatial relationships
  - Left child = placed to the right of parent
  - Right child = placed above parent

BTree(blocks)
  - Main floorplanning engine
  - Methods:
    * pack() -> (W, H, R): Decode tree to coordinates, O(n) complexity
    * get_layout() -> List[(idx, x, y, w, h)]: Get placement results
    * build_random_tree(seed): Create random tree for testing
    * build_from_sequence(sequence): Build from permutation (for SA)
    * check_tree_validity() -> bool: Verify tree structure

Algorithm (pack method):
------------------------
1. Initialize contour line at height 0
2. DFS traversal (preorder):
   - Root: place at (0, 0)
   - Left child: x = parent.x + parent.w
   - Right child: x = parent.x (same x as parent)
   - For both: y = contour.max_height_in_range(x, x+w)
3. After each placement: update contour
4. Track max W and H

Guarantees:
-----------
- No overlaps (by construction)
- O(n) time complexity for packing
- Works with arbitrary tree structures

Usage Example:
--------------
from btree import BTree
from data_loader import load_blocks
from config import DATA_PATHS

# Load data
blocks = load_blocks(DATA_PATHS['n100'])

# Create tree and pack
tree = BTree(blocks)
tree.build_random_tree(seed=42)
W, H, R = tree.pack()

print(f"Bounding box: {W:.1f} x {H:.1f}")
print(f"Aspect ratio: {R:.3f}")

# Get placement coordinates
layout = tree.get_layout()
for idx, x, y, w, h in layout:
    print(f"Block {idx}: ({x:.1f}, {y:.1f}) size={w:.1f}x{h:.1f}")

================================================================================
3. PERFORMANCE CHARACTERISTICS
================================================================================

Dataset    Blocks   Pack Time    Result (Random Tree)
--------   ------   ---------    ---------------------
n100       100      0.34 ms      W=350, H=1755, R=5.01
n200       200      0.75 ms      W=321, H=2152, R=6.70
n300       300      1.33 ms      W=363, H=3455, R=9.52

Notes:
- Random tree gives poor aspect ratios (expected)
- Need SA optimization to improve placement
- Packing time scales linearly O(n)

================================================================================
4. NEXT STEPS (For SA Implementation)
================================================================================

Required Components:
--------------------
1. Perturbation operators (rotate, swap, move)
2. Cost function (area, aspect ratio, or weighted)
3. Simulated Annealing scheduler
4. Initial solution generator (FFD or random)

Integration Points:
-------------------
- BTree.build_from_sequence(seq): Build tree from permutation
- BTree.pack(): Evaluate cost after perturbation
- Block.rotate(): Apply rotation operator

Expected Flow:
--------------
1. Generate initial sequence (FFD or random)
2. Build tree from sequence
3. Pack and evaluate cost
4. Apply perturbation
5. Rebuild tree
6. Accept/reject based on SA criteria
7. Repeat until convergence

================================================================================
5. VALIDATION CHECKLIST
================================================================================

Data Loader:
  [OK] Parses .blocks files correctly
  [OK] Validates total area against expected values
  [OK] Handles all 3 datasets (n100, n200, n300)
  [OK] Block.rotate() swaps dimensions correctly
  [OK] Block.aspect_ratio() computes correctly

B*-Tree:
  [OK] ContourLine maintains correct heights
  [OK] pack() produces no overlaps
  [OK] pack() runs in O(n) time
  [OK] All blocks are placed
  [OK] Tree validity checks pass
  [OK] Coordinates are non-negative

Performance:
  [OK] n100: < 1ms packing time
  [OK] n200: < 2ms packing time
  [OK] n300: < 3ms packing time

================================================================================
6. KEY IMPLEMENTATION DETAILS
================================================================================

Why ContourLine is Critical:
-----------------------------
Without contour line: Finding y-coordinate requires scanning all previously
placed blocks -> O(n) per node -> O(n^2) total complexity

With contour line: Query max height in O(1) amortized -> O(n) total

Contour Line Operations:
-------------------------
- Segments represent horizontal "skyline" of placed blocks
- Update: Split overlapping segments, merge adjacent same-height segments
- Query: Scan segments overlapping with [x_start, x_end)

DFS Traversal Order:
--------------------
Must visit parent before children to establish correct placement base.
Left child uses parent's right edge as x-coordinate.
Right child uses parent's top edge as y-coordinate.

Tree Structure -> Spatial Relationships:
-----------------------------------------
The tree encodes relative positions, not absolute coordinates.
Absolute coordinates are computed during pack() via DFS + contour.

================================================================================
FILE LOCATIONS
================================================================================

Implementation:
  C:\Users\29845\Desktop\华数杯\问题1\题代码\data_loader.py
  C:\Users\29845\Desktop\华数杯\问题1\题代码\btree.py
  C:\Users\29845\Desktop\华数杯\问题1\题代码\config.py

Data Files:
  C:\Users\29845\Desktop\华数杯\2026年第七届华数杯数学建模竞赛赛题\
    B题 VLSI布图规划设计\附件\n100.blocks
    B题 VLSI布图规划设计\附件\n200.blocks
    B题 VLSI布图规划设计\附件\n300.blocks

================================================================================
END OF REFERENCE
================================================================================
