#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q1参数扫描 - 生成Fig4-6所需数据

基于多AI协作方案：
- Fig4需要：γ分布数据（R_MEC/R_lower比率）
- Fig5需要：(φ,D)关系数据 + (θ₁,θ₂,φ)→D映射
- Fig6需要：(θ₁,θ₂)→D网格数据

数据保真原则：
- 使用q1_main.py的核心算法
- 不插值、不平滑、不归一化
- 保留原始计算结果
"""

import numpy as np
import sys
import os
import json
from tqdm import tqdm

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))
from q1_main import *

# ═══════════════════════════════════════════════════════════
# 参数扫描配置
# ═══════════════════════════════════════════════════════════

# 检测点配置（使用q1_main.py的默认配置）
d = 100.0  # 检测点到中心距离（米）
phi = 1.0  # 角度误差（度）

# 扫描范围
THETA_RANGE = np.arange(30, 151, 5)  # θ∈[30°,150°]，步长5°
PHI_RANGE = np.arange(0.5, 5.1, 0.5)  # φ∈[0.5°,5°]，步长0.5°

# 输出目录
OUTPUT_DIR = '题一/实验结果/parameter_sweep_data'
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════
# Fig4: γ分布数据扫描
# ═══════════════════════════════════════════════════════════
def generate_gamma_distribution_data():
    """
    生成γ分布数据（γ = R_MEC / R_lower）

    扫描策略：
    - 固定d=100m, φ=1°
    - 遍历θ₁∈[30°,150°], θ₂∈[30°,150°]
    - 计算每个配置的R_MEC和R_lower
    - 记录γ比率
    """
    print('\n' + '='*60)
    print('生成Fig4数据：γ分布')
    print('='*60)

    gamma_values = []
    configs = []

    total = len(THETA_RANGE) * len(THETA_RANGE)

    with tqdm(total=total, desc='扫描(θ₁,θ₂)网格') as pbar:
        for theta1 in THETA_RANGE:
            for theta2 in THETA_RANGE:
                # 构建3个检测点（均匀分布120°）
                theta3 = theta1 + 120  # 简化：第三个检测点

                # 生成角度测量（中心加噪声）
                angles = np.array([theta1, theta2, theta3])

                # 构建角域
                wedges = []
                for i, angle in enumerate(angles):
                    # 检测点坐标
                    detector = Point(
                        d * np.cos(np.radians(angle)),
                        d * np.sin(np.radians(angle))
                    )

                    # 角域：测量角度±误差
                    angle_measured = angle  # 真实值
                    wedge = Wedge(
                        detector,
                        angle_measured - phi,
                        angle_measured + phi
                    )
                    wedges.append(wedge)

                # 计算交会区域
                intersection_points = compute_intersection_region(wedges)

                if len(intersection_points) > 0:
                    # 计算凸包
                    hull_points = convex_hull_andrew(intersection_points)

                    if len(hull_points) >= 3:
                        # 计算直径
                        D, _, _ = diameter_rotating_calipers(hull_points)

                        # 计算最小外接圆
                        R_MEC, _ = minimum_enclosing_circle_welzl(hull_points)

                        # Jung定理下界
                        R_lower = D / 2.0

                        # 计算γ比率
                        gamma = R_MEC / R_lower if R_lower > 0 else np.nan

                        if not np.isnan(gamma) and 1.0 <= gamma <= 2.0/np.sqrt(3):
                            gamma_values.append(gamma)
                            configs.append({
                                'theta1': float(theta1),
                                'theta2': float(theta2),
                                'D': float(D),
                                'R_MEC': float(R_MEC),
                                'R_lower': float(R_lower),
                                'gamma': float(gamma)
                            })

                pbar.update(1)

    # 保存数据
    gamma_array = np.array(gamma_values)

    data = {
        'gamma_values': gamma_array.tolist(),
        'configs': configs,
        'scan_params': {
            'd': d,
            'phi': phi,
            'theta_range': THETA_RANGE.tolist()
        },
        'statistics': {
            'n': len(gamma_array),
            'mean': float(np.mean(gamma_array)),
            'median': float(np.median(gamma_array)),
            'std': float(np.std(gamma_array)),
            'min': float(np.min(gamma_array)),
            'max': float(np.max(gamma_array))
        }
    }

    output_file = os.path.join(OUTPUT_DIR, 'fig4_gamma_distribution.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f'\n✅ Fig4数据已保存: {output_file}')
    print(f'   样本数: {len(gamma_array)}')
    print(f'   γ范围: [{np.min(gamma_array):.4f}, {np.max(gamma_array):.4f}]')
    print(f'   均值: {np.mean(gamma_array):.4f}')
    print(f'   标准差: {np.std(gamma_array):.4f}')

    return data


# ═══════════════════════════════════════════════════════════
# Fig5: φ-D关系数据扫描
# ═══════════════════════════════════════════════════════════
def generate_phi_D_relation_data():
    """
    生成φ-D关系数据

    扫描策略：
    - 固定d=100m
    - 遍历φ∈[0.5°,5°], θ₁∈[30°,150°], θ₂∈[30°,150°]
    - 记录(φ,D,θ₁,θ₂)四元组
    """
    print('\n' + '='*60)
    print('生成Fig5数据：φ-D关系')
    print('='*60)

    data_cloud = []  # 所有采样点
    optimal_path = []  # 最优配置路径（θ₁=θ₂=60°）
    symmetric_path = []  # 对称配置路径（θ₁=θ₂）

    total = len(PHI_RANGE) * len(THETA_RANGE) * len(THETA_RANGE)

    with tqdm(total=total, desc='扫描(φ,θ₁,θ₂)空间') as pbar:
        for phi_val in PHI_RANGE:
            for theta1 in THETA_RANGE:
                for theta2 in THETA_RANGE:
                    # 构建3个检测点
                    theta3 = theta1 + 120
                    angles = np.array([theta1, theta2, theta3])

                    # 构建角域
                    wedges = []
                    for angle in angles:
                        detector = Point(
                            d * np.cos(np.radians(angle)),
                            d * np.sin(np.radians(angle))
                        )
                        wedge = Wedge(detector, angle - phi_val, angle + phi_val)
                        wedges.append(wedge)

                    # 计算交会区域
                    intersection_points = compute_intersection_region(wedges)

                    if len(intersection_points) > 0:
                        hull_points = convex_hull_andrew(intersection_points)

                        if len(hull_points) >= 3:
                            D, _, _ = diameter_rotating_calipers(hull_points)

                            point = {
                                'phi': float(phi_val),
                                'theta1': float(theta1),
                                'theta2': float(theta2),
                                'D': float(D)
                            }

                            data_cloud.append(point)

                            # 提取特定路径
                            if abs(theta1 - 60) < 2.5 and abs(theta2 - 60) < 2.5:
                                optimal_path.append(point)

                            if abs(theta1 - theta2) < 2.5:
                                symmetric_path.append(point)

                    pbar.update(1)

    # 保存数据
    data = {
        'data_cloud': data_cloud,
        'optimal_path': optimal_path,
        'symmetric_path': symmetric_path,
        'scan_params': {
            'd': d,
            'phi_range': PHI_RANGE.tolist(),
            'theta_range': THETA_RANGE.tolist()
        },
        'statistics': {
            'n_total': len(data_cloud),
            'n_optimal': len(optimal_path),
            'n_symmetric': len(symmetric_path)
        }
    }

    output_file = os.path.join(OUTPUT_DIR, 'fig5_phi_D_relation.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f'\n✅ Fig5数据已保存: {output_file}')
    print(f'   总样本数: {len(data_cloud)}')
    print(f'   最优路径: {len(optimal_path)}点')
    print(f'   对称路径: {len(symmetric_path)}点')

    return data


# ═══════════════════════════════════════════════════════════
# Fig6: (θ₁,θ₂)参数空间数据扫描
# ═══════════════════════════════════════════════════════════
def generate_param_space_data():
    """
    生成(θ₁,θ₂)参数空间数据

    扫描策略：
    - 固定d=100m, φ=1°
    - 遍历θ₁∈[30°,150°], θ₂∈[30°,150°]
    - 记录每个配置的D值
    - 生成粗网格（Δθ=10°）和精细网格（Δθ=2°）
    """
    print('\n' + '='*60)
    print('生成Fig6数据：(θ₁,θ₂)参数空间')
    print('='*60)

    # 粗网格（10°）
    theta_coarse = np.arange(0, 91, 10)
    D_coarse = np.zeros((len(theta_coarse), len(theta_coarse)))

    print('\n生成粗网格（Δθ=10°）...')
    with tqdm(total=len(theta_coarse)**2) as pbar:
        for i, theta1 in enumerate(theta_coarse):
            for j, theta2 in enumerate(theta_coarse):
                theta3 = theta1 + 120
                angles = np.array([theta1, theta2, theta3])

                wedges = []
                for angle in angles:
                    detector = Point(
                        d * np.cos(np.radians(angle)),
                        d * np.sin(np.radians(angle))
                    )
                    wedge = Wedge(detector, angle - phi, angle + phi)
                    wedges.append(wedge)

                intersection_points = compute_intersection_region(wedges)

                if len(intersection_points) > 0:
                    hull_points = convex_hull_andrew(intersection_points)
                    if len(hull_points) >= 3:
                        D, _, _ = diameter_rotating_calipers(hull_points)
                        D_coarse[i, j] = D
                    else:
                        D_coarse[i, j] = np.nan
                else:
                    D_coarse[i, j] = np.nan

                pbar.update(1)

    # 精细网格（2°，聚焦40-80°）
    theta_fine = np.arange(40, 81, 2)
    D_fine = np.zeros((len(theta_fine), len(theta_fine)))

    print('\n生成精细网格（Δθ=2°，聚焦40-80°）...')
    with tqdm(total=len(theta_fine)**2) as pbar:
        for i, theta1 in enumerate(theta_fine):
            for j, theta2 in enumerate(theta_fine):
                theta3 = theta1 + 120
                angles = np.array([theta1, theta2, theta3])

                wedges = []
                for angle in angles:
                    detector = Point(
                        d * np.cos(np.radians(angle)),
                        d * np.sin(np.radians(angle))
                    )
                    wedge = Wedge(detector, angle - phi, angle + phi)
                    wedges.append(wedge)

                intersection_points = compute_intersection_region(wedges)

                if len(intersection_points) > 0:
                    hull_points = convex_hull_andrew(intersection_points)
                    if len(hull_points) >= 3:
                        D, _, _ = diameter_rotating_calipers(hull_points)
                        D_fine[i, j] = D
                    else:
                        D_fine[i, j] = np.nan
                else:
                    D_fine[i, j] = np.nan

                pbar.update(1)

    # 找到全局最优点
    valid_mask = ~np.isnan(D_fine)
    if valid_mask.any():
        min_idx = np.nanargmin(D_fine)
        i_opt, j_opt = np.unravel_index(min_idx, D_fine.shape)
        theta1_opt = theta_fine[i_opt]
        theta2_opt = theta_fine[j_opt]
        D_opt = D_fine[i_opt, j_opt]
    else:
        theta1_opt = theta2_opt = D_opt = np.nan

    # 保存数据
    data = {
        'coarse_grid': {
            'theta_values': theta_coarse.tolist(),
            'D_matrix': D_coarse.tolist()
        },
        'fine_grid': {
            'theta_values': theta_fine.tolist(),
            'D_matrix': D_fine.tolist()
        },
        'optimal_point': {
            'theta1': float(theta1_opt) if not np.isnan(theta1_opt) else None,
            'theta2': float(theta2_opt) if not np.isnan(theta2_opt) else None,
            'D': float(D_opt) if not np.isnan(D_opt) else None
        },
        'scan_params': {
            'd': d,
            'phi': phi
        }
    }

    output_file = os.path.join(OUTPUT_DIR, 'fig6_param_space.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f'\n✅ Fig6数据已保存: {output_file}')
    print(f'   粗网格: {len(theta_coarse)}×{len(theta_coarse)}')
    print(f'   精细网格: {len(theta_fine)}×{len(theta_fine)}')
    if not np.isnan(D_opt):
        print(f'   最优点: θ₁={theta1_opt}°, θ₂={theta2_opt}°, D={D_opt:.2f}m')

    return data


# ═══════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════
if __name__ == '__main__':
    print('='*60)
    print('Q1参数扫描 - 多AI协作方案数据生成')
    print('='*60)
    print(f'输出目录: {OUTPUT_DIR}')

    # 生成Fig4数据
    fig4_data = generate_gamma_distribution_data()

    # 生成Fig5数据
    fig5_data = generate_phi_D_relation_data()

    # 生成Fig6数据
    fig6_data = generate_param_space_data()

    print('\n' + '='*60)
    print('✅ 所有参数扫描数据生成完成！')
    print('='*60)
    print(f'数据保存在: {OUTPUT_DIR}/')
    print(f'  - fig4_gamma_distribution.json')
    print(f'  - fig5_phi_D_relation.json')
    print(f'  - fig6_param_space.json')
    print('\n下一步：运行q1_figures_456_v2.py生成图表')
