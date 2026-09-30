#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q1 Fig4-6 期刊级图表生成（基于多AI协作方案）

设计来源：
- DeepSeek-V4-Pro分析
- 交互动画设计师完整方案
- Nature期刊技术标准

数据保真原则：
- 不修改原始计算数据
- 仅改变视觉映射方式
- 保留数学结论完整性
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, Wedge, Rectangle, FancyArrowPatch
from matplotlib import gridspec
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
from scipy.stats import gaussian_kde
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

# ═══════════════════════════════════════════════════════════
# 配色方案 - Ink & Ochre (与fig1-3保持一致)
# ═══════════════════════════════════════════════════════════
PALETTE_A = {
    "ink": "#1C1C1C",        # 墨色 - 主要结构
    "slate": "#5B6B73",      # 板岩 - 次要元素
    "paper": "#F7F4EE",      # 纸色 - 背景
    "field": "#C5D4E0",      # 场域 - 浅色区域
    "geometry": "#2C4A6E",   # 几何蓝 - 几何元素
    "ochre": "#C47B2B",      # 赭石 - 强调色(唯一)
    "rust": "#8C3A2A",       # 锈红 - 深色强调
    "sage": "#4F6F5C",       # 鼠尾草 - 辅助色
}

# 线宽标准
LW = {'main': 2.2, 'theory': 1.4, 'aux': 0.7}

# matplotlib配置
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42

# 数据目录
DATA_DIR = '题一/实验结果/parameter_sweep_data'
FIG_DIR = '题一/实验结果/figs'
os.makedirs(FIG_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════
# Fig4: γ分布收敛动画（4帧演化序列）
# 设计：交互动画设计师
# ═══════════════════════════════════════════════════════════
def fig4_convergence_animation(save_path=None):
    """
    γ分布收敛动画（4帧演化序列）

    Frame 1: 理论预测（空白+Jung边界）
    Frame 2: n=100 初步采样
    Frame 3: n=500 中期收敛
    Frame 4: 最终完整分布
    """
    print('\n' + '='*60)
    print('生成Fig4: γ分布收敛动画（4帧）')
    print('='*60)

    # 加载数据
    data_file = os.path.join(DATA_DIR, 'fig4_gamma_distribution.json')
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    gamma_values = np.array(data['gamma_values'])
    print(f'加载γ值数据: n={len(gamma_values)}')

    # Jung定理边界
    JUNG_LOWER = 1.0
    JUNG_UPPER = 2.0 / np.sqrt(3)  # ≈1.1547

    # 创建4个子图
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=150)
    fig.patch.set_facecolor(PALETTE_A['paper'])
    axes = axes.flatten()

    # Frame配置
    frames = [
        {'n': 0, 'title': 'Frame 1: Theory Prediction'},
        {'n': 100, 'title': 'Frame 2: Initial Sampling (n=100)'},
        {'n': 500, 'title': 'Frame 3: Mid-term Convergence (n=500)'},
        {'n': len(gamma_values), 'title': f'Frame 4: Final Distribution (n={len(gamma_values)})'}
    ]

    for idx, (ax, frame) in enumerate(zip(axes, frames)):
        ax.set_facecolor(PALETTE_A['paper'])

        # Jung理论窄带背景
        ax.axvspan(JUNG_LOWER, JUNG_UPPER, alpha=0.12, facecolor=PALETTE_A['field'], zorder=0)

        # 边界虚线
        ax.axvline(JUNG_LOWER, linestyle='--', linewidth=LW['theory'],
                   color=PALETTE_A['slate'], alpha=0.6, label='Jung lower')
        ax.axvline(JUNG_UPPER, linestyle='--', linewidth=LW['theory'],
                   color=PALETTE_A['rust'], alpha=0.6, label='Jung upper')

        if frame['n'] > 0:
            # 使用前n个样本
            sample = gamma_values[:frame['n']]

            # 直方图
            bins = 15 if frame['n'] <= 100 else (25 if frame['n'] <= 500 else 30)
            ax.hist(sample, bins=bins, alpha=0.6, color=PALETTE_A['ochre'],
                   edgecolor=PALETTE_A['ink'], linewidth=0.5, density=True,
                   label=f'Histogram (bins={bins})')

            # KDE曲线（反射边界）
            if len(sample) >= 10:
                # 反射边界处理
                mirror_lower = 2*JUNG_LOWER - sample[sample < JUNG_LOWER+0.05]
                mirror_upper = 2*JUNG_UPPER - sample[sample > JUNG_UPPER-0.05]
                reflected = np.concatenate([mirror_lower, sample, mirror_upper])

                kde = gaussian_kde(reflected, bw_method='scott')
                x_range = np.linspace(JUNG_LOWER-0.02, JUNG_UPPER+0.02, 200)
                density = kde(x_range)

                # 截断到理论边界
                mask = (x_range >= JUNG_LOWER) & (x_range <= JUNG_UPPER)
                ax.plot(x_range[mask], density[mask], color=PALETTE_A['geometry'],
                       linewidth=LW['main'], label='KDE (reflected boundary)')

            # 均值线
            if frame['n'] == len(gamma_values):
                mean_val = np.mean(sample)
                ax.axvline(mean_val, linestyle='-', linewidth=LW['main'],
                          color=PALETTE_A['rust'], alpha=0.8, label=f'Mean={mean_val:.4f}')

        # 双箭头标注（只在Frame 4）
        if frame['n'] == len(gamma_values):
            y_max = ax.get_ylim()[1]
            arrow_y = y_max * 0.95
            ax.annotate('', xy=(JUNG_UPPER, arrow_y), xytext=(JUNG_LOWER, arrow_y),
                       arrowprops=dict(arrowstyle='<->', color=PALETTE_A['ink'],
                                      linewidth=LW['main'], shrinkA=0, shrinkB=0))
            ax.text((JUNG_LOWER+JUNG_UPPER)/2, arrow_y*1.05,
                   f'Jung width ≈ {JUNG_UPPER-JUNG_LOWER:.4f}',
                   ha='center', va='bottom', fontsize=9, color=PALETTE_A['ink'])

        # 设置
        ax.set_xlabel('γ = R_MEC / R_lower', fontsize=10, color=PALETTE_A['ink'])
        ax.set_ylabel('Probability Density', fontsize=10, color=PALETTE_A['ink'])
        ax.set_xlim(0.98, 1.18)
        ax.set_title(frame['title'], fontsize=11, color=PALETTE_A['ink'], fontweight='bold')
        ax.tick_params(labelsize=9, colors=PALETTE_A['slate'])
        ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(PALETTE_A['slate'])
        ax.spines['bottom'].set_color(PALETTE_A['slate'])
        ax.grid(False)

    plt.tight_layout()

    # 保存
    if save_path is None:
        save_path = os.path.join(FIG_DIR, 'fig4_convergence_animation')

    plt.savefig(f'{save_path}.png', dpi=600, bbox_inches='tight', facecolor=PALETTE_A['paper'])
    plt.savefig(f'{save_path}.svg', bbox_inches='tight', facecolor=PALETTE_A['paper'])
    print(f'✅ Fig4已保存: {save_path}.png + .svg')

    return fig, axes


# ═══════════════════════════════════════════════════════════
# Fig5: φ-D关系演化轨迹（双层叠加）
# 设计：交互动画设计师
# ═══════════════════════════════════════════════════════════
def fig5_trajectory_cloud(save_path=None):
    """
    φ-D关系演化轨迹（双层叠加）

    底层：所有(φ,D)样本点"数据云"
    前层：3条关键路径（最优/对称/非对称）
    """
    print('\n' + '='*60)
    print('生成Fig5: φ-D轨迹云+关键路径')
    print('='*60)

    # 加载数据
    data_file = os.path.join(DATA_DIR, 'fig5_phi_D_relation.json')
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    data_cloud = data['data_cloud']
    optimal_path = data['optimal_path']
    symmetric_path = data['symmetric_path']

    print(f'加载数据: 总样本{len(data_cloud)}, 最优路径{len(optimal_path)}, 对称路径{len(symmetric_path)}')

    # 创建画布
    fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
    ax.set_facecolor(PALETTE_A['paper'])
    fig.patch.set_facecolor(PALETTE_A['paper'])

    # 底层：数据云
    phi_cloud = [p['phi'] for p in data_cloud]
    D_cloud = [p['D'] for p in data_cloud]
    ax.scatter(phi_cloud, D_cloud, s=8, alpha=0.15, c=PALETTE_A['slate'],
              edgecolors='none', zorder=1, label='All samples (data cloud)')

    # 前层：最优路径
    if len(optimal_path) > 0:
        phi_opt = sorted([p['phi'] for p in optimal_path])
        D_opt = [p['D'] for p in optimal_path if p['phi'] in phi_opt]
        ax.plot(phi_opt, D_opt, color=PALETTE_A['geometry'], linewidth=LW['main']*1.2,
               marker='o', markersize=6, label='Optimal path (θ₁=θ₂=60°)', zorder=5)

    # 对称路径
    if len(symmetric_path) > 10:
        phi_sym = sorted(list(set([p['phi'] for p in symmetric_path])))
        D_sym_avg = [np.mean([p['D'] for p in symmetric_path if abs(p['phi']-phi)<0.01])
                     for phi in phi_sym]
        ax.plot(phi_sym, D_sym_avg, color=PALETTE_A['ochre'], linewidth=LW['main'],
               marker='s', markersize=5, label='Symmetric path (θ₁=θ₂)', zorder=4)

    # 设置
    ax.set_xlabel('φ: Detection Error (degrees)', fontsize=12, color=PALETTE_A['ink'])
    ax.set_ylabel('D: Diameter (m)', fontsize=12, color=PALETTE_A['ink'])
    ax.set_title('Fig5: φ-D Relationship Exploration Trajectory',
                fontsize=13, color=PALETTE_A['ink'], fontweight='bold')
    ax.tick_params(labelsize=10, colors=PALETTE_A['slate'])
    ax.legend(loc='upper left', fontsize=10, framealpha=0.95)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(PALETTE_A['slate'])
    ax.spines['bottom'].set_color(PALETTE_A['slate'])
    ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.5, color=PALETTE_A['slate'])

    plt.tight_layout()

    # 保存
    if save_path is None:
        save_path = os.path.join(FIG_DIR, 'fig5_trajectory_cloud')

    plt.savefig(f'{save_path}.png', dpi=600, bbox_inches='tight', facecolor=PALETTE_A['paper'])
    plt.savefig(f'{save_path}.svg', bbox_inches='tight', facecolor=PALETTE_A['paper'])
    print(f'✅ Fig5已保存: {save_path}.png + .svg')

    return fig, ax


# ═══════════════════════════════════════════════════════════
# Fig6: 三联渐进式热力图
# 设计：交互动画设计师
# ═══════════════════════════════════════════════════════════
def fig6_progressive_heatmap(save_path=None):
    """
    三联渐进式热力图（参数空间演化）

    Panel A: 粗网格探索（Δθ=10°）
    Panel B: 精细网格聚焦（Δθ=2°）
    Panel C: 对角线切片+对称性分析
    """
    print('\n' + '='*60)
    print('生成Fig6: 三联渐进式热力图')
    print('='*60)

    # 加载数据
    data_file = os.path.join(DATA_DIR, 'fig6_param_space.json')
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    theta_coarse = np.array(data['coarse_grid']['theta_values'])
    D_coarse = np.array(data['coarse_grid']['D_matrix'])
    theta_fine = np.array(data['fine_grid']['theta_values'])
    D_fine = np.array(data['fine_grid']['D_matrix'])
    opt_point = data['optimal_point']

    print(f'加载数据: 粗网格{D_coarse.shape}, 精细网格{D_fine.shape}')

    # 创建colormap (slate→ochre sequential)
    colors = [PALETTE_A['field'], PALETTE_A['ochre'], PALETTE_A['rust']]
    n_bins = 100
    cmap = LinearSegmentedColormap.from_list('slate_ochre', colors, N=n_bins)

    # 创建三联图
    fig = plt.figure(figsize=(18, 6), dpi=150)
    fig.patch.set_facecolor(PALETTE_A['paper'])
    gs = gridspec.GridSpec(1, 3, width_ratios=[1, 1, 1.2], wspace=0.3)

    # Panel A: 粗网格
    ax1 = fig.add_subplot(gs[0])
    ax1.set_facecolor(PALETTE_A['paper'])
    im1 = ax1.pcolormesh(theta_coarse, theta_coarse, D_coarse, cmap=cmap, shading='auto')
    ax1.contour(theta_coarse, theta_coarse, D_coarse, levels=5, colors='white',
               linewidths=0.7, alpha=0.6)
    ax1.set_xlabel('θ₁ (degrees)', fontsize=11, color=PALETTE_A['ink'])
    ax1.set_ylabel('θ₂ (degrees)', fontsize=11, color=PALETTE_A['ink'])
    ax1.set_title('Panel A: Coarse Grid (Δθ=10°)', fontsize=12, fontweight='bold')
    ax1.tick_params(labelsize=9, colors=PALETTE_A['slate'])
    plt.colorbar(im1, ax=ax1, label='D (m)')

    # Panel B: 精细网格
    ax2 = fig.add_subplot(gs[1])
    ax2.set_facecolor(PALETTE_A['paper'])
    im2 = ax2.pcolormesh(theta_fine, theta_fine, D_fine, cmap=cmap, shading='auto')
    ax2.contour(theta_fine, theta_fine, D_fine, levels=10, colors='white',
               linewidths=0.8, alpha=0.7)

    # 标注最优点
    if opt_point['theta1'] is not None:
        ax2.plot(opt_point['theta1'], opt_point['theta2'], 'w+', markersize=15,
                markeredgewidth=2.5, label=f"Optimal ({opt_point['theta1']:.0f}°,{opt_point['theta2']:.0f}°)")
        ax2.legend(loc='upper right', fontsize=9, framealpha=0.9)

    ax2.set_xlabel('θ₁ (degrees)', fontsize=11, color=PALETTE_A['ink'])
    ax2.set_ylabel('θ₂ (degrees)', fontsize=11, color=PALETTE_A['ink'])
    ax2.set_title('Panel B: Fine Grid (Δθ=2°, Focus 40-80°)', fontsize=12, fontweight='bold')
    ax2.tick_params(labelsize=9, colors=PALETTE_A['slate'])
    plt.colorbar(im2, ax=ax2, label='D (m)')

    # Panel C: 对角线切片
    ax3 = fig.add_subplot(gs[2])
    ax3.set_facecolor(PALETTE_A['paper'])
    im3 = ax3.pcolormesh(theta_fine, theta_fine, D_fine, cmap=cmap, shading='auto', alpha=0.6)

    # 对角线θ₁=θ₂
    ax3.plot([theta_fine[0], theta_fine[-1]], [theta_fine[0], theta_fine[-1]],
            'w--', linewidth=LW['main'], label='θ₁=θ₂ (Symmetric)')

    # θ₁+θ₂=90°线
    theta_sum90 = np.linspace(theta_fine[0], theta_fine[-1], 100)
    theta2_sum90 = 90 - theta_sum90
    mask = (theta2_sum90 >= theta_fine[0]) & (theta2_sum90 <= theta_fine[-1])
    ax3.plot(theta_sum90[mask], theta2_sum90[mask], color=PALETTE_A['sage'],
            linestyle='--', linewidth=LW['theory'], label='θ₁+θ₂=90°')

    ax3.set_xlabel('θ₁ (degrees)', fontsize=11, color=PALETTE_A['ink'])
    ax3.set_ylabel('θ₂ (degrees)', fontsize=11, color=PALETTE_A['ink'])
    ax3.set_title('Panel C: Symmetry Analysis', fontsize=12, fontweight='bold')
    ax3.tick_params(labelsize=9, colors=PALETTE_A['slate'])
    ax3.legend(loc='upper right', fontsize=9, framealpha=0.9)
    plt.colorbar(im3, ax=ax3, label='D (m)')

    plt.tight_layout()

    # 保存
    if save_path is None:
        save_path = os.path.join(FIG_DIR, 'fig6_progressive_heatmap')

    plt.savefig(f'{save_path}.png', dpi=600, bbox_inches='tight', facecolor=PALETTE_A['paper'])
    plt.savefig(f'{save_path}.svg', bbox_inches='tight', facecolor=PALETTE_A['paper'])
    print(f'✅ Fig6已保存: {save_path}.png + .svg')

    return fig, (ax1, ax2, ax3)


# ═══════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════
if __name__ == '__main__':
    print('='*60)
    print('Q1 Fig4-6 期刊级图表生成')
    print('基于多AI协作方案（交互动画设计师）')
    print('='*60)

    try:
        # 生成Fig4
        fig4, _ = fig4_convergence_animation()
        plt.close(fig4)

        # 生成Fig5
        fig5, _ = fig5_trajectory_cloud()
        plt.close(fig5)

        # 生成Fig6
        fig6, _ = fig6_progressive_heatmap()
        plt.close(fig6)

        print('\n' + '='*60)
        print('✅ 所有图表生成完成！')
        print('='*60)
        print(f'图表保存在: {FIG_DIR}/')
        print(f'  - fig4_convergence_animation.png + .svg (600 DPI)')
        print(f'  - fig5_trajectory_cloud.png + .svg (600 DPI)')
        print(f'  - fig6_progressive_heatmap.png + .svg (600 DPI)')

    except FileNotFoundError as e:
        print(f'\n❌ 错误: 数据文件未找到')
        print(f'   请先运行 q1_parameter_sweep.py 生成数据')
        print(f'   错误详情: {e}')
    except Exception as e:
        print(f'\n❌ 错误: {e}')
        import traceback
        traceback.print_exc()
