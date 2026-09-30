#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Q1 图表一键生成工具

用法：
    cd 01_生图代码
    python generate_all.py

功能：
    - 生成所有12张Q1图表
    - 自动输出到对应分类目录
    - 显示生成进度和结果统计
"""

import sys
import os
import time

# 确保可以导入 q1_figures_beautified
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from q1_figures_beautified import (
    fig_5_1_1_baseline,
    fig_5_1_2_wedge_evolution,
    fig_5_1_3_jung_counterexample,
    fig_5_1_4_jung_sandwich,
    fig_5_1_5_vertex_filtering,
    fig_5_1_6_param_scan,
    fig_5_1_7_gamma_distribution,
    fig_5_1_8_n_and_grid,
    fig_5_1_10_geometry_construction,
    fig_5_1_11_sensitivity_triplet,
    fig_5_1_12_param_space_partition,
    fig_5_1_13_phi_D_theory,
)

# 图表清单（按论文引用顺序）
FIGURE_LIST = [
    ('5.1-1', fig_5_1_1_baseline, '基准算例', '几何示意'),
    ('5.1-2', fig_5_1_2_wedge_evolution, '角域构造演化', '几何示意'),
    ('5.1-3', fig_5_1_3_jung_counterexample, 'Jung反例', '几何示意'),
    ('5.1-4', fig_5_1_4_jung_sandwich, 'Jung夹逼', '几何示意'),
    ('5.1-5', fig_5_1_5_vertex_filtering, '顶点过滤', '几何示意'),
    ('5.1-6', fig_5_1_6_param_scan, '参数扫描', '参数扫描'),
    ('5.1-7', fig_5_1_7_gamma_distribution, 'γ缺口比分布', '统计分布'),
    ('5.1-8', fig_5_1_8_n_and_grid, 'n扫描+热力图', '参数扫描'),
    ('5.1-10', fig_5_1_10_geometry_construction, '交会定位区域构造', '几何示意'),
    ('5.1-11', fig_5_1_11_sensitivity_triplet, '灵敏度三联图', '参数扫描'),
    ('5.1-12', fig_5_1_12_param_space_partition, '参数空间四类分区', '参数扫描'),
    ('5.1-13', fig_5_1_13_phi_D_theory, 'φ-D曲线与理论式验证', '参数扫描'),
]

def main():
    """主函数：批量生成所有图表"""
    print("=" * 70)
    print("Q1 图表批量生成工具 v1.4.0")
    print("=" * 70)
    print(f"共 {len(FIGURE_LIST)} 张图表待生成")
    print("输出格式：PNG (300 DPI) + SVG (矢量)")
    print("-" * 70)

    success = 0
    failed = 0
    total_time = 0

    for fig_id, func, name, category in FIGURE_LIST:
        print(f"\n[图{fig_id}] {name} ({category})...", end=' ')

        start_time = time.time()
        try:
            func()
            elapsed = time.time() - start_time
            total_time += elapsed
            success += 1
            print(f"[OK] ({elapsed:.2f}s)")
        except Exception as e:
            failed += 1
            print(f"[FAIL]")
            print(f"    Error: {e}")

    # 统计结果
    print("\n" + "=" * 70)
    print("生成完成")
    print("=" * 70)
    print(f"✅ 成功: {success} 张")
    print(f"❌ 失败: {failed} 张")
    print(f"⏱️  总耗时: {total_time:.2f} 秒")

    if success > 0:
        print(f"📊 平均每张: {total_time/success:.2f} 秒")

    print("\n输出目录:")
    print("  - 02_几何示意/     (8张)")
    print("  - 03_参数扫描/     (5张)")
    print("  - 04_统计分布/     (1张)")
    print("  - 05_算法流程/     (手绘，不由代码生成)")
    print("=" * 70)

    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
