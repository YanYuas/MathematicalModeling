#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VLSI布图数据统计脚本
解析.blocks文件，统计模块分类，计算理论下界/上界/死区率
"""

import re
import math
import json
import csv
from pathlib import Path
from typing import Dict, List, Tuple


def parse_blocks_file(filepath: str) -> List[Dict]:
    """
    解析.blocks文件，提取模块信息

    Args:
        filepath: .blocks文件路径

    Returns:
        模块列表，每个模块包含 {name, width, height, area, aspect_ratio}
    """
    modules = []

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

        # 使用正则表达式匹配block行
        # 格式：b0 block 4 (0, 0) (0, 33) (43, 33) (43, 0)
        pattern = r'(b\d+)\s+block\s+\d+\s+\((\d+),\s*(\d+)\)\s+\((\d+),\s*(\d+)\)\s+\((\d+),\s*(\d+)\)\s+\((\d+),\s*(\d+)\)'

        for match in re.finditer(pattern, content):
            name = match.group(1)

            # 提取四个角点
            coords = [
                (int(match.group(2)), int(match.group(3))),
                (int(match.group(4)), int(match.group(5))),
                (int(match.group(6)), int(match.group(7))),
                (int(match.group(8)), int(match.group(9)))
            ]

            # 计算宽度和高度
            x_coords = [c[0] for c in coords]
            y_coords = [c[1] for c in coords]

            width = max(x_coords) - min(x_coords)
            height = max(y_coords) - min(y_coords)
            area = width * height

            # 计算纵横比（max/min >= 1）
            if width > 0 and height > 0:
                aspect_ratio = max(width, height) / min(width, height)
            else:
                aspect_ratio = 1.0

            modules.append({
                'name': name,
                'width': width,
                'height': height,
                'area': area,
                'aspect_ratio': aspect_ratio
            })

    return modules


def classify_modules(modules: List[Dict]) -> Dict:
    """
    按纵横比分类模块

    Args:
        modules: 模块列表

    Returns:
        分类结果字典
    """
    square_like = []  # 纵横比 < 1.2
    strip_like = []   # 纵横比 > 2.5
    middle = []       # 1.2 <= 纵横比 <= 2.5

    for module in modules:
        ratio = module['aspect_ratio']

        if ratio < 1.2:
            square_like.append(module)
        elif ratio > 2.5:
            strip_like.append(module)
        else:
            middle.append(module)

    total_count = len(modules)

    return {
        'square_like': {
            'modules': square_like,
            'count': len(square_like),
            'ratio': len(square_like) / total_count * 100 if total_count > 0 else 0,
            'avg_aspect_ratio': sum(m['aspect_ratio'] for m in square_like) / len(square_like) if square_like else 0,
            'total_area': sum(m['area'] for m in square_like)
        },
        'strip_like': {
            'modules': strip_like,
            'count': len(strip_like),
            'ratio': len(strip_like) / total_count * 100 if total_count > 0 else 0,
            'avg_aspect_ratio': sum(m['aspect_ratio'] for m in strip_like) / len(strip_like) if strip_like else 0,
            'max_aspect_ratio': max((m['aspect_ratio'] for m in strip_like), default=0),
            'total_area': sum(m['area'] for m in strip_like),
            'module_names': [m['name'] for m in strip_like]
        },
        'middle': {
            'modules': middle,
            'count': len(middle),
            'ratio': len(middle) / total_count * 100 if total_count > 0 else 0,
            'avg_aspect_ratio': sum(m['aspect_ratio'] for m in middle) / len(middle) if middle else 0,
            'total_area': sum(m['area'] for m in middle)
        }
    }


def calculate_statistics(modules: List[Dict]) -> Dict:
    """
    计算整体统计指标

    Args:
        modules: 模块列表

    Returns:
        统计指标字典
    """
    # β: 模块总面积
    beta = sum(m['area'] for m in modules)

    # √β: 理论下界（方形边长）
    sqrt_beta = math.sqrt(beta)

    # α: 向上取整后的方形面积
    ceil_sqrt_beta = math.ceil(sqrt_beta)
    alpha = ceil_sqrt_beta ** 2

    # 理论最小死区率
    deadspace_rate = (alpha - beta) / alpha * 100 if alpha > 0 else 0

    # 平均和最大纵横比
    aspect_ratios = [m['aspect_ratio'] for m in modules]
    avg_aspect_ratio = sum(aspect_ratios) / len(aspect_ratios) if aspect_ratios else 0
    max_aspect_ratio = max(aspect_ratios) if aspect_ratios else 0

    return {
        'module_count': len(modules),
        'beta': beta,
        'sqrt_beta': sqrt_beta,
        'ceil_sqrt_beta': ceil_sqrt_beta,
        'alpha': alpha,
        'deadspace_rate': deadspace_rate,
        'avg_aspect_ratio': avg_aspect_ratio,
        'max_aspect_ratio': max_aspect_ratio
    }


def main():
    """主函数"""
    # 数据文件路径
    base_dir = Path(r"C:\Users\29845\Desktop\华数杯\2026年第七届华数杯数学建模竞赛赛题\B题 VLSI布图规划设计\附件")
    output_dir = Path(r"C:\Users\29845\Desktop\华数杯\问题1")

    datasets = ['n100', 'n200', 'n300']

    # 用于CSV输出
    csv_data = []

    # 用于JSON输出
    json_data = {}

    for dataset in datasets:
        print(f"\n处理 {dataset}...")

        # 解析文件
        filepath = base_dir / f"{dataset}.blocks"
        modules = parse_blocks_file(str(filepath))

        # 分类统计
        classification = classify_modules(modules)

        # 整体统计
        stats = calculate_statistics(modules)

        # 构建CSV行
        csv_row = {
            '数据集': dataset,
            '模块数': stats['module_count'],
            '模块总面积β': stats['beta'],
            '理论下界√β': f"{stats['sqrt_beta']:.2f}",
            '向上取整': stats['ceil_sqrt_beta'],
            '方形面积α': stats['alpha'],
            '理论死区率': f"{stats['deadspace_rate']:.2f}%",
            '近方形数量': classification['square_like']['count'],
            '近方形占比': f"{classification['square_like']['ratio']:.1f}%",
            '长条块数量': classification['strip_like']['count'],
            '长条块占比': f"{classification['strip_like']['ratio']:.1f}%",
            '中间块数量': classification['middle']['count'],
            '中间块占比': f"{classification['middle']['ratio']:.1f}%",
            '平均纵横比': f"{stats['avg_aspect_ratio']:.2f}",
            '最大纵横比': f"{stats['max_aspect_ratio']:.2f}"
        }
        csv_data.append(csv_row)

        # 构建JSON数据
        json_data[dataset] = {
            'total': stats['module_count'],
            'beta': stats['beta'],
            'sqrt_beta': round(stats['sqrt_beta'], 2),
            'ceil_sqrt_beta': stats['ceil_sqrt_beta'],
            'alpha': stats['alpha'],
            'deadspace_rate': round(stats['deadspace_rate'], 2),
            'avg_aspect_ratio': round(stats['avg_aspect_ratio'], 2),
            'max_aspect_ratio': round(stats['max_aspect_ratio'], 2),
            'square_like': {
                'count': classification['square_like']['count'],
                'ratio': round(classification['square_like']['ratio'], 1),
                'avg_aspect_ratio': round(classification['square_like']['avg_aspect_ratio'], 2),
                'total_area': classification['square_like']['total_area']
            },
            'strip_like': {
                'count': classification['strip_like']['count'],
                'ratio': round(classification['strip_like']['ratio'], 1),
                'avg_aspect_ratio': round(classification['strip_like']['avg_aspect_ratio'], 2),
                'max_aspect_ratio': round(classification['strip_like']['max_aspect_ratio'], 2),
                'total_area': classification['strip_like']['total_area'],
                'module_names': classification['strip_like']['module_names']
            },
            'middle': {
                'count': classification['middle']['count'],
                'ratio': round(classification['middle']['ratio'], 1),
                'avg_aspect_ratio': round(classification['middle']['avg_aspect_ratio'], 2),
                'total_area': classification['middle']['total_area']
            }
        }

        # 打印统计结果
        print(f"  模块数: {stats['module_count']}")
        print(f"  模块总面积 β: {stats['beta']}")
        print(f"  理论下界 √β: {stats['sqrt_beta']:.2f}")
        print(f"  向上取整: {stats['ceil_sqrt_beta']}")
        print(f"  方形面积 α: {stats['alpha']}")
        print(f"  理论死区率: {stats['deadspace_rate']:.2f}%")
        print(f"  近方形(<1.2): {classification['square_like']['count']} ({classification['square_like']['ratio']:.1f}%)")
        print(f"  长条块(>2.5): {classification['strip_like']['count']} ({classification['strip_like']['ratio']:.1f}%)")
        print(f"  中间块: {classification['middle']['count']} ({classification['middle']['ratio']:.1f}%)")
        print(f"  平均纵横比: {stats['avg_aspect_ratio']:.2f}")
        print(f"  最大纵横比: {stats['max_aspect_ratio']:.2f}")

    # 输出CSV文件
    csv_file = output_dir / "数据集基础统计.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
        if csv_data:
            writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
            writer.writeheader()
            writer.writerows(csv_data)
    print(f"\nCSV文件已保存: {csv_file}")

    # 输出JSON文件
    json_file = output_dir / "模块分类详细.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"JSON文件已保存: {json_file}")


if __name__ == '__main__':
    main()
