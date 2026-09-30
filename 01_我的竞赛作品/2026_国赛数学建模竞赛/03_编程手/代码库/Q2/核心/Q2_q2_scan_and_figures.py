# -*- coding: utf-8 -*-
"""
Q2 参数扫描 + 图表生成
基于 Q2_algorithm_implementation.py 的函数接口
扫描 Δd / φ_min / R 三组参数，生成 6 张论文必做图表
"""
import sys
import os
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge, FancyArrowPatch
from matplotlib.collections import PatchCollection

# 导入 Q2 算法实现
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from Q2_algorithm_implementation import (
    compute_candidate_region, position_uncertainty_E,
    to_local, to_world, compute_localization_region, compute_diameter
)

# 中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

EPS_DEG = 1.0
EPS_RAD = math.radians(EPS_DEG)
V = 5.0  # m/s

def scan_delta_d():
    """扫描 Δd：固定 φ_min=40°, R=1000，通过 d_min/d_max 控制 Δd"""
    results = []
    d_hat = 752.5  # 固定中点
    for dd in [200, 300, 400, 500, 600, 650, 700, 747.5]:
        d_min = d_hat - dd
        d_max = d_hat + dd
        cr = compute_candidate_region((0,0), 0.0, phi_min_deg=40.0, R_worst=1000.0,
                                       d_min=d_min, d_max=d_max)
        b_min = cr.get('b_min')
        b_max = cr.get('b_max')
        feasible = cr.get('feasible', False)
        phi_max = cr.get('phi_min_max_deg', float('nan'))
        # 名义 E（Δ=0, b=b_min）
        E_nom = position_uncertainty_E(d_hat, b_min, d_hat, EPS_RAD) if feasible and b_min and b_min > 0 else float('nan')
        results.append({
            'delta_d': dd, 'b_min': b_min if b_min else float('nan'),
            'b_max': b_max if b_max else float('nan'),
            'feasible': feasible, 'phi_min_max': phi_max,
            'E_nominal': E_nom, 'width': (b_max - b_min) if feasible and b_min and b_max else 0
        })
    return results

def scan_phi_min():
    """扫描 φ_min：固定 Δd=747.5 (d_min=5, d_max=1500), R=1000"""
    results = []
    for pm in [30, 35, 40, 45, 50, 55, 60, 70, 80, 90]:
        cr = compute_candidate_region((0,0), 0.0, phi_min_deg=pm, R_worst=1000.0,
                                       d_min=5.0, d_max=1500.0)
        b_min = cr.get('b_min')
        b_max = cr.get('b_max')
        results.append({
            'phi_min': pm, 'b_min': b_min if b_min else float('nan'),
            'b_max': b_max if b_max else float('nan'),
            'feasible': cr.get('feasible', False),
            'width': (b_max - b_min) if cr.get('feasible') and b_min and b_max else 0
        })
    return results

def scan_R():
    """扫描 R：固定 Δd=747.5 (d_min=5, d_max=1500), φ_min=40°"""
    results = []
    for R in [1000, 1100, 1200, 1250, 1300, 1400, 1500]:
        cr = compute_candidate_region((0,0), 0.0, phi_min_deg=40.0, R_worst=R,
                                       d_min=5.0, d_max=1500.0)
        b_min = cr.get('b_min')
        b_max = cr.get('b_max')
        results.append({
            'R': R, 'b_min': b_min if b_min else float('nan'),
            'b_max': b_max if b_max else float('nan'),
            'feasible': cr.get('feasible', False),
            'phi_min_max': cr.get('phi_min_max_deg', float('nan'))
        })
    return results

def compute_E_grid(a_range, b_range, d1=752.5):
    """计算 E 在 (a,b) 平面的等高线"""
    A, B = np.meshgrid(a_range, b_range)
    E = np.zeros_like(A)
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            a, b = A[i,j], B[i,j]
            E[i,j] = position_uncertainty_E(a, b, d1, EPS_RAD)
    return A, B, E

# ============ 图表生成 ============

def fig1_candidate_region(scan_dd, savepath):
    """图1：候选区域宽度 vs Δd（主打图）"""
    fig, ax1 = plt.subplots(figsize=(10, 6))
    dd = [r['delta_d'] for r in scan_dd if r['feasible']]
    bmin = [r['b_min'] for r in scan_dd if r['feasible']]
    bmax = [r['b_max'] for r in scan_dd if r['feasible']]
    width = [r['width'] for r in scan_dd if r['feasible']]
    
    ax1.fill_between(dd, bmin, bmax, alpha=0.3, color='steelblue', label='候选区域 b∈[b_min,b_max]')
    ax1.plot(dd, bmin, 'o-', color='navy', label='b_min = Δd·tan φ_min')
    ax1.plot(dd, bmax, 's-', color='crimson', label='b_max = √(R²−Δd²)')
    
    # 标注不可行点
    for r in scan_dd:
        if not r['feasible']:
            ax1.axvline(x=r['delta_d'], color='gray', linestyle='--', alpha=0.3)
    
    ax1.axvline(x=747.5, color='orange', linestyle='--', linewidth=2, label='本题 Δd=747.5 m')
    ax1.set_xlabel('源距不确定半宽 Δd (m)', fontsize=12)
    ax1.set_ylabel('横向偏移 b (m)', fontsize=12)
    ax1.set_title('图5.2-1 候选区域随源距不确定度 Δd 的变化（φ_min=40°, R=1000m）', fontsize=13)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(savepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ 图1已保存: {savepath}")

def fig2_tradeoff_curve(scan_dd, savepath):
    """图2：权衡曲线 φ_min^max vs Δd"""
    fig, ax = plt.subplots(figsize=(10, 6))
    dd = [r['delta_d'] for r in scan_dd]
    phi_max = [r['phi_min_max'] for r in scan_dd]
    ax.plot(dd, phi_max, 'o-', color='darkgreen', linewidth=2, markersize=8, label='φ_min^max = arccos(Δd/R)')
    ax.axhline(y=40, color='orange', linestyle='--', linewidth=2, label='本题要求 φ_min=40°')
    ax.axvline(x=747.5, color='crimson', linestyle='--', linewidth=2, label='本题 Δd=747.5 m')
    ax.fill_between(dd, 0, phi_max, alpha=0.15, color='darkgreen', label='可达区域')
    ax.set_xlabel('源距不确定半宽 Δd (m)', fontsize=12)
    ax.set_ylabel('可保证交会角上界 φ_min^max (°)', fontsize=12)
    ax.set_title('图5.2-2 可保证交会角上界与源距不确定度的权衡（R=1000m）', fontsize=13)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 95)
    plt.tight_layout()
    plt.savefig(savepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ 图2已保存: {savepath}")

def fig3_E_contour(savepath):
    """图3：E 等高线图（叠加可行域边界）"""
    d1 = 752.5
    a_range = np.linspace(400, 1100, 100)
    b_range = np.linspace(0, 800, 100)
    A, B, E = compute_E_grid(a_range, b_range, d1)
    
    fig, ax = plt.subplots(figsize=(10, 7))
    levels = [15, 16, 17, 18, 20, 25, 30, 40, 60, 100]
    cs = ax.contour(A, B, E, levels=levels, cmap='viridis', linewidths=1.5)
    ax.clabel(cs, inline=True, fontsize=9, fmt='%.1f')
    
    # 最优线 a=d1
    ax.axvline(x=d1, color='crimson', linestyle='--', linewidth=2, label=f'最优线 a=d₁={d1} m (φ=90°)')
    # 退化线 b=0
    ax.axhline(y=0, color='gray', linestyle=':', linewidth=1.5, label='退化线 b=0 (E→∞)')
    # 候选区域（本题 Δd=747.5, φ_min=40°）
    b_min = 747.5 * math.tan(math.radians(40))
    b_max = math.sqrt(1000**2 - 747.5**2)
    ax.axhspan(b_min, b_max, xmin=0, xmax=1, alpha=0.15, color='orange', label=f'候选区域 b∈[{b_min:.1f},{b_max:.1f}]')
    
    ax.set_xlabel('纵向偏移 a (m)', fontsize=12)
    ax.set_ylabel('横向偏移 b (m)', fontsize=12)
    ax.set_title('图5.2-3 位置不确定度 E 在 (a,b) 平面的等高线（d₁=752.5m, ε=1°）', fontsize=13)
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, alpha=0.2)
    plt.tight_layout()
    plt.savefig(savepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ 图3已保存: {savepath}")

def fig4_optimality_thales(savepath):
    """图4：最优性示意图（Thales圆 + 正侧方对齐）"""
    fig, ax = plt.subplots(figsize=(9, 8))
    
    S1 = (0, 0)
    G = (300, 500)
    # 最优 S2：a=d1, b 取候选区 b_min
    d1 = math.sqrt(300**2 + 500**2)
    theta1 = math.degrees(math.atan2(500, 300))
    # 局部坐标 a=d1, b=627.23 → 世界坐标
    u = (math.cos(math.radians(theta1)), math.sin(math.radians(theta1)))
    v = (-math.sin(math.radians(theta1)), math.cos(math.radians(theta1)))
    S2_opt = (S1[0] + d1*u[0] + 627.23*v[0], S1[1] + d1*u[1] + 627.23*v[1])
    
    # Q1 原例 S2=(600,0)
    S2_q1 = (600, 0)
    
    # Thales 圆（以 S1S2_opt 为直径）
    center = ((S1[0]+S2_opt[0])/2, (S1[1]+S2_opt[1])/2)
    radius = math.sqrt((S2_opt[0]-S1[0])**2 + (S2_opt[1]-S1[1])**2)/2
    circle = Circle(center, radius, fill=False, color='crimson', linestyle='--', linewidth=2, label='Thales圆 (以S₁S₂为直径)')
    ax.add_patch(circle)
    
    # 点
    ax.plot(*S1, 'ko', markersize=10, label='S₁ (检测点1)')
    ax.plot(*G, 'r*', markersize=15, label='G (干扰源)')
    ax.plot(*S2_opt, 'bs', markersize=10, label='S₂* (Q2最优位, φ=90°)')
    ax.plot(*S2_q1, 'g^', markersize=10, label='S₂ (Q1原例, φ=61.9°)')
    
    # 视线
    ax.plot([S1[0], G[0]], [S1[1], G[1]], 'k-', alpha=0.5, linewidth=1)
    ax.plot([S2_opt[0], G[0]], [S2_opt[1], G[1]], 'b-', alpha=0.5, linewidth=1)
    ax.plot([S2_q1[0], G[0]], [S2_q1[1], G[1]], 'g-', alpha=0.3, linewidth=1)
    
    # 标注角度
    ax.annotate(f'φ=90°', xy=G, xytext=(G[0]+80, G[1]-30), fontsize=12, color='crimson', fontweight='bold')
    
    ax.set_xlabel('x (m)', fontsize=12)
    ax.set_ylabel('y (m)', fontsize=12)
    ax.set_title('图5.2-4 正交最优性：正侧方对齐时 φ=90°，源落在Thales圆上', fontsize=13)
    ax.legend(loc='lower left', fontsize=10)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(savepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ 图4已保存: {savepath}")

def fig5_improvement_comparison(savepath):
    """图5：Q1基准 vs Q2候选 改善效果对比"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    configs = ['Q1基准\n(S₂=(600,0))', 'Q2候选 b_min\n(φ=105°)', 'Q2候选 中点', 'Q2候选 b_max\n(φ=104°)']
    D_vals = [39.598, 35.414, 35.777, 36.151]
    E_vals = [16.311, 15.782, 15.994, 16.210]
    colors = ['gray', 'steelblue', 'lightblue', 'powderblue']
    
    bars1 = ax1.bar(configs, D_vals, color=colors, edgecolor='black', linewidth=0.5)
    ax1.set_ylabel('定位区域直径 D (m)', fontsize=12)
    ax1.set_title('(a) 定位区域直径对比', fontsize=13)
    for bar, val in zip(bars1, D_vals):
        ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3, f'{val:.2f}', ha='center', fontsize=10)
    ax1.grid(True, alpha=0.3, axis='y')
    
    bars2 = ax2.bar(configs, E_vals, color=colors, edgecolor='black', linewidth=0.5)
    ax2.set_ylabel('位置不确定度 E (m)', fontsize=12)
    ax2.set_title('(b) 位置不确定度对比', fontsize=13)
    for bar, val in zip(bars2, E_vals):
        ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.1, f'{val:.2f}', ha='center', fontsize=10)
    ax2.grid(True, alpha=0.3, axis='y')
    
    fig.suptitle('图5.2-5 Q2选点策略对定位精度的改善效果（D降幅10.57%, E降幅3.25%）', fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(savepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ 图5已保存: {savepath}")

def fig6_degradation(savepath):
    """图6：退化对比（b=0零信息 vs b≠0）"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    S1 = (0, 0)
    G = (300, 500)
    theta1 = math.degrees(math.atan2(500, 300))
    d1 = math.sqrt(300**2 + 500**2)
    u = (math.cos(math.radians(theta1)), math.sin(math.radians(theta1)))
    
    # b=0: S2在示向度射线上（三点共线）
    S2_deg = (S1[0] + d1*u[0], S1[1] + d1*u[1])
    # b≠0: 最优位
    v = (-math.sin(math.radians(theta1)), math.cos(math.radians(theta1)))
    S2_opt = (S1[0] + d1*u[0] + 627.23*v[0], S1[1] + d1*u[1] + 627.23*v[1])
    
    for ax, S2, title, color in [(ax1, S2_deg, '(a) 退化：b=0，三点共线', 'gray'), (ax2, S2_opt, '(b) 非退化：b≠0，φ=90°', 'steelblue')]:
        ax.plot(*S1, 'ko', markersize=10, label='S₁')
        ax.plot(*G, 'r*', markersize=15, label='G (源)')
        ax.plot(*S2, 's', color=color, markersize=10, label='S₂')
        ax.plot([S1[0], G[0]], [S1[1], G[1]], 'k-', alpha=0.5)
        ax.plot([S2[0], G[0]], [S2[1], G[1]], color=color, linestyle='-', alpha=0.5)
        # 示向度射线
        ax.plot([S1[0], S1[0]+800*u[0]], [S1[1], S1[1]+800*u[1]], 'k--', alpha=0.3, label='示向度射线')
        if ax == ax1:
            ax.annotate('三点共线\n定位零信息!', xy=(200, 350), fontsize=13, color='crimson', fontweight='bold')
        else:
            ax.annotate('φ=90°\n定位最优!', xy=(200, 350), fontsize=13, color='darkgreen', fontweight='bold')
        ax.set_xlabel('x (m)', fontsize=11)
        ax.set_ylabel('y (m)', fontsize=11)
        ax.set_title(title, fontsize=12)
        ax.legend(loc='lower left', fontsize=9)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
    
    fig.suptitle('图5.2-6 沿示向度前进(b=0)是零信息退化，必须横向偏移(b≠0)', fontsize=13, y=1.02)
    plt.tight_layout()
    plt.savefig(savepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ 图6已保存: {savepath}")

# ============ 主流程 ============
if __name__ == '__main__':
    outdir = os.path.dirname(os.path.abspath(__file__))
    figdir = os.path.join(outdir, 'figs')
    os.makedirs(figdir, exist_ok=True)
    
    print("=" * 60)
    print("Q2 参数扫描 + 图表生成")
    print("=" * 60)
    
    # 1. 参数扫描
    print("\n--- 参数扫描 ---")
    scan_dd = scan_delta_d()
    scan_pm = scan_phi_min()
    scan_R = scan_R()
    
    # 保存扫描结果
    scan_results = {
        'scan_delta_d': scan_dd,
        'scan_phi_min': scan_pm,
        'scan_R': scan_R
    }
    with open(os.path.join(outdir, 'q2_scan_results.json'), 'w', encoding='utf-8') as f:
        json.dump(scan_results, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 扫描结果已保存: q2_scan_results.json")
    
    # 打印关键结果
    print("\n--- Δd 扫描关键结果 ---")
    for r in scan_dd:
        print(f"  Δd={r['delta_d']:6.1f}: b_min={r['b_min']:.2f}, b_max={r['b_max']:.2f}, "
              f"可行={r['feasible']}, φ_max={r['phi_min_max']:.2f}°, E={r['E_nominal']:.2f}")
    
    print("\n--- φ_min 扫描关键结果 ---")
    for r in scan_pm:
        print(f"  φ_min={r['phi_min']:3d}°: b_min={r['b_min']:.2f}, b_max={r['b_max']:.2f}, "
              f"可行={r['feasible']}, 宽度={r['width']:.2f}")
    
    # 2. 生成图表
    print("\n--- 生成图表 ---")
    fig1_candidate_region(scan_dd, os.path.join(figdir, 'fig5_2_1_candidate_region.png'))
    fig2_tradeoff_curve(scan_dd, os.path.join(figdir, 'fig5_2_2_tradeoff_curve.png'))
    fig3_E_contour(os.path.join(figdir, 'fig5_2_3_E_contour.png'))
    fig4_optimality_thales(os.path.join(figdir, 'fig5_2_4_optimality_thales.png'))
    fig5_improvement_comparison(os.path.join(figdir, 'fig5_2_5_improvement.png'))
    fig6_degradation(os.path.join(figdir, 'fig5_2_6_degradation.png'))
    
    print("\n" + "=" * 60)
    print("✅ Q2 参数扫描 + 6张图表全部完成！")
    print("=" * 60)
