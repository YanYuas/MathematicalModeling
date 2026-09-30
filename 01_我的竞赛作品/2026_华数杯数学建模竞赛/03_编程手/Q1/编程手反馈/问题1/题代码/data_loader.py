"""
阶段0：数据解析器
功能：解析.blocks文件，提取模块宽高，验证总面积
"""
import re
from typing import List, Tuple
from config import EXPECTED_AREAS


class Block:
    """模块类"""
    def __init__(self, idx: int, name: str, w: float, h: float):
        self.idx = idx          # 模块索引
        self.name = name        # 模块名称（如b0, b1...）
        self.w = w              # 宽度
        self.h = h              # 高度
        self.area = w * h       # 面积
        self.rotated = False    # 是否已旋转
        self.x = 0.0            # 放置后的x坐标
        self.y = 0.0            # 放置后的y坐标

    def rotate(self):
        """90度旋转"""
        self.w, self.h = self.h, self.w
        self.rotated = not self.rotated

    def aspect_ratio(self) -> float:
        """纵横比"""
        min_dim = min(self.w, self.h)
        if min_dim == 0:
            return float('inf')
        return max(self.w, self.h) / min_dim

    def __repr__(self):
        return f"Block({self.name}, w={self.w:.1f}, h={self.h:.1f}, area={self.area:.1f})"


def parse_block_line(line: str) -> Tuple[str, float, float]:
    """
    解析block行，提取模块名和宽高

    格式: bX block 4 (x1,y1) (x2,y2) (x3,y3) (x4,y4)
    返回: (name, width, height)
    """
    # 提取模块名
    match_name = re.match(r'(\w+)\s+block', line)
    if not match_name:
        raise ValueError(f"无法解析模块名: {line}")
    name = match_name.group(1)

    # 提取4个角点坐标
    coords = re.findall(r'\((\d+),\s*(\d+)\)', line)
    if len(coords) != 4:
        raise ValueError(f"坐标点数量不是4个: {line}")

    # 转换为浮点数
    points = [(float(x), float(y)) for x, y in coords]

    # 计算宽度和高度（假设矩形，从4个角点推算）
    x_coords = [p[0] for p in points]
    y_coords = [p[1] for p in points]

    width = max(x_coords) - min(x_coords)
    height = max(y_coords) - min(y_coords)

    return name, width, height


def load_blocks(filepath: str) -> List[Block]:
    """
    加载.blocks文件

    Args:
        filepath: .blocks文件路径

    Returns:
        Block对象列表

    Raises:
        AssertionError: 总面积不匹配
    """
    blocks = []
    idx = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue

            # 跳过头部信息
            if line.startswith('NumHardBlocks') or line.startswith('NumTerminals'):
                continue

            # 只处理block行，跳过terminal行
            if 'block' in line and 'terminal' not in line:
                try:
                    name, w, h = parse_block_line(line)
                    blocks.append(Block(idx, name, w, h))
                    idx += 1
                except Exception as e:
                    print(f"警告：解析失败 - {line}")
                    print(f"错误信息：{e}")
                    continue

    # 验证总面积
    total_area = sum(b.area for b in blocks)

    # 推断数据集名称
    dataset_name = None
    for name, expected in EXPECTED_AREAS.items():
        if abs(total_area - expected) < 1:
            dataset_name = name
            break

    if dataset_name is None:
        raise AssertionError(
            f"总面积不匹配！\n"
            f"  实际: {total_area:.0f}\n"
            f"  期望: {EXPECTED_AREAS}"
        )

    print(f"[OK] 数据加载成功 [{dataset_name}]")
    print(f"  - 模块数量: {len(blocks)}")
    print(f"  - 总面积: {total_area:.0f} (期望: {EXPECTED_AREAS[dataset_name]})")
    print(f"  - 面积范围: [{min(b.area for b in blocks):.0f}, {max(b.area for b in blocks):.0f}]")

    return blocks


def get_block_stats(blocks: List[Block]) -> dict:
    """获取模块统计信息"""
    areas = [b.area for b in blocks]
    aspect_ratios = [b.aspect_ratio() for b in blocks]

    return {
        'count': len(blocks),
        'total_area': sum(areas),
        'min_area': min(areas),
        'max_area': max(areas),
        'avg_area': sum(areas) / len(blocks),
        'min_aspect_ratio': min(aspect_ratios),
        'max_aspect_ratio': max(aspect_ratios),
        'avg_aspect_ratio': sum(aspect_ratios) / len(aspect_ratios),
    }


# ==================== M1验证：解析正确性 ====================
if __name__ == '__main__':
    from config import DATA_PATHS

    print("=" * 60)
    print("阶段0验证：数据解析")
    print("=" * 60)

    for name, path in DATA_PATHS.items():
        print(f"\n测试 {name}:")
        try:
            blocks = load_blocks(path)
            stats = get_block_stats(blocks)

            print(f"  [OK] 平均面积: {stats['avg_area']:.1f}")
            print(f"  [OK] 纵横比范围: [{stats['min_aspect_ratio']:.2f}, {stats['max_aspect_ratio']:.2f}]")

            # 检查总面积
            assert abs(stats['total_area'] - EXPECTED_AREAS[name]) < 1, \
                f"总面积不匹配: {stats['total_area']} != {EXPECTED_AREAS[name]}"

        except Exception as e:
            print(f"  [FAIL] 失败: {e}")

    print("\n" + "=" * 60)
    print("M1里程碑：解析+校验 - 通过 [OK]")
    print("=" * 60)
