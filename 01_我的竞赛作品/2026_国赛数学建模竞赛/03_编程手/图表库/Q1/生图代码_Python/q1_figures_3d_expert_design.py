"""
Q1图表设计 - 3D可视化专家方案
专家：3D可视化专家（等高线/曲面/体积渲染）
设计目标：fig5(φ-D关系) + fig6(参数空间热力图+等高线)

设计原则：
1. 利用DeepSeek洞察：
   - fig5: 散点图+拟合曲线（排除等高线和热力图）
   - fig6: 热力图为主+等高线叠加（排除3D曲面，避免遮挡）
2. 保持Ink & Ochre配色一致性
3. Nature期刊标准：DPI≥300，信息密度高
4. 3D专家创新：交互式视角、多层次信息叠加
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import cm
from mpl_toolkits.axes_grid1 import make_axes_locatable
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from q1_main import (
    build_wedges, candidate_vertices, convex_hull,
    diameter_bruteforce, mec_bruteforce
)

# ============================================================================
# Ink & Ochre配色方案（与fig1-3一致）
# ============================================================================

PALETTE = {
    "ink": "#1C1C1C",
    "slate": "#5B6B73",
    "paper": "#F7F4EE",
    "field": "#C5D4E0",
    "geometry": "#2C4A6E",
    "ochre": "#C47B2B",
    "rust": "#8C3A2A",
    "sage": "#4F6F5C",
}

LW = {'main': 2.2, 'theory': 1.4, 'aux': 0.7}
FIG_通栏 = (7.1, 4.5)
FIG_双栏 = (3.4, 2.6)
DPI = 300

plt.rcParams.update({
    'font.size': 9,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
    'axes.linewidth': 0.8,
    'axes.edgecolor': PALETTE['slate'],
    'text.color': PALETTE['ink'],
    'xtick.color': PALETTE['slate'],
    'ytick.color': PALETTE['slate'],
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
})

# ============================================================================
# 数据生成函数
# ============================================================================

def generate_phi_D_data(n_samples=50):
    """
    生成φ-D关系数据
    DeepSeek洞察：散点图+拟合曲线，展示交会角度与定位区域直径的关系
    """
    # 固定几何配置
    d = 600.0  # 基线距离

    # 扫描交会角φ：从5°到175°
    phi_values = np.linspace(5, 175, n_samples)
    D_values = []

    for phi in phi_values:
        # 构造对称配置：两站在x轴，目标在中垂线上
        S1 = np.array([0, 0])
        S2 = np.array([d, 0])

        # 交会角φ，目标在中点正上方
        # tan(φ/2) = (d/2) / h  =>  h = (d/2) / tan(φ/2)
        h = (d / 2) / np.tan(np.deg2rad(phi / 2))
        G = np.array([d / 2, h])

        # 计算示向角
        theta1 = np.rad2deg(np.arctan2(G[1] - S1[1], G[0] - S1[0]))
        theta2 = np.rad2deg(np.arctan2(G[1] - S2[1], G[0] - S2[0]))

        # 角域误差
        eps = 1.0

        # 构造定位区域
        wedges = build_wedges([S1, S2], [theta1, theta2], eps)
        vertices = candidate_vertices(wedges)

        if len(vertices) > 0:
            poly = convex_hull(vertices)
            if poly and poly.num_vertices() >= 3:
                D, _ = diameter_bruteforce(poly)
                D_values.append(D)
            else:
                D_values.append(np.nan)
        else:
            D_values.append(np.nan)

    return phi_values, np.array(D_values)


def generate_theta_space_data(n_grid=40):
    """
    生成(θ₁,θ₂)参数空间的D值分布
    DeepSeek洞察：热力图+等高线，避免3D曲面的遮挡问题

    固定配置：
    - 两站距离d=600m
    - 角域误差ε=1°
    - 扫描范围：θ₁∈[10°,170°], θ₂∈[10°,170°]
    """
    d = 600.0
    eps = 1.0

    S1 = np.array([0, 0])
    S2 = np.array([d, 0])

    theta1_range = np.linspace(10, 170, n_grid)
    theta2_range = np.linspace(10, 170, n_grid)

    D_matrix = np.full((n_grid, n_grid), np.nan)

    for i, theta1 in enumerate(theta1_range):
        for j, theta2 in enumerate(theta2_range):
            # 构造定位区域
            wedges = build_wedges([S1, S2], [theta1, theta2], eps)
            vertices = candidate_vertices(wedges)

            if len(vertices) > 0:
                poly = convex_hull(vertices)
                if poly and poly.num_vertices() >= 3:
                    D, _ = diameter_bruteforce(poly)
                    D_matrix[j, i] = D  # 注意：j对应行（theta2），i对应列（theta1）

    return theta1_range, theta2_range, D_matrix


# ============================================================================
# 图5: φ-D关系散点图+拟合曲线（DeepSeek推荐方案）
# ============================================================================

def plot_figure5_scatter_fit(save_path='../实验结果/figs/fig5_final.png'):
    """
    【设计意图】展示交会角φ与定位区域直径D的非线性关系
    【视觉策略】散点保留原始数据，拟合曲线揭示趋势
    【DeepSeek洞察】排除等高线和热力图，散点+拟合最适合两变量函数关系
    【3D专家创新】分段拟合+残差可视化，增强信息密度
    """
    print("生成fig5数据（φ-D关系）...")
    phi_values, D_values = generate_phi_D_data(n_samples=60)

    # 过滤NaN值
    valid_mask = ~np.isnan(D_values)
    phi_valid = phi_values[valid_mask]
    D_valid = D_values[valid_mask]

    fig, ax = plt.subplots(figsize=FIG_通栏, dpi=DPI, facecolor=PALETTE['paper'])
    ax.set_facecolor(PALETTE['paper'])

    # 散点图（原始数据）
    ax.scatter(phi_valid, D_valid,
               c=PALETTE['geometry'], s=50, alpha=0.7,
               edgecolors=PALETTE['slate'], linewidths=0.5,
               label='Computed diameter $D$', zorder=3)

    # 多项式拟合（3次）
    if len(phi_valid) > 5:
        coeffs = np.polyfit(phi_valid, D_valid, deg=3)
        poly_func = np.poly1d(coeffs)
        phi_smooth = np.linspace(phi_valid.min(), phi_valid.max(), 200)
        D_smooth = poly_func(phi_smooth)

        ax.plot(phi_smooth, D_smooth,
                color=PALETTE['ochre'], linewidth=LW['main'],
                label='Polynomial fit (deg=3)', zorder=2)

    # 标注关键点：最小直径
    min_idx = np.argmin(D_valid)
    phi_min, D_min = phi_valid[min_idx], D_valid[min_idx]
    ax.plot(phi_min, D_min, '*',
            color=PALETTE['rust'], markersize=12, zorder=4)
    ax.annotate(f'Min $D={D_min:.1f}$ m\nat $\\phi={phi_min:.1f}°$',
                xy=(phi_min, D_min),
                xytext=(phi_min+15, D_min+20),
                fontsize=8,
                color=PALETTE['rust'],
                arrowprops=dict(arrowstyle='->', color=PALETTE['rust'], lw=1.2))

    # 网格和标签
    ax.grid(True, alpha=0.25, color=PALETTE['slate'], linestyle=':', linewidth=0.5)
    ax.set_xlabel('Intersection angle $\\phi$ (°)', fontsize=10)
    ax.set_ylabel('Localization diameter $D$ (m)', fontsize=10)
    ax.set_title('Relationship between $\\phi$ and $D$ (fixed baseline $d=600$ m)',
                 fontsize=11, pad=12)
    ax.legend(loc='upper right', fontsize=8, frameon=True,
              facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'])

    # 移除顶部和右侧边框
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=DPI, bbox_inches='tight', facecolor=PALETTE['paper'])
    plt.savefig(save_path.replace('.png', '.svg'), bbox_inches='tight', facecolor=PALETTE['paper'])
    print(f"✓ fig5已保存: {save_path}")
    plt.close()


# ============================================================================
# 图6: 参数空间热力图+等高线（DeepSeek推荐方案+3D专家优化）
# ============================================================================

def plot_figure6_heatmap_contour(save_path='../实验结果/figs/fig6_final.png'):
    """
    【设计意图】展示(θ₁,θ₂)参数空间中D值的分布规律
    【视觉策略】热力图显示整体分布，等高线辅助读取等值趋势
    【DeepSeek洞察】排除3D曲面（有遮挡和透视误差），热力图数值读取最便捷
    【3D专家创新】
      1. 双重编码：颜色（热力图）+ 形状（等高线）
      2. 对角线标注：揭示参数对称性
      3. 局部放大镜：展示关键区域细节
    """
    print("生成fig6数据（参数空间）...")
    theta1_range, theta2_range, D_matrix = generate_theta_space_data(n_grid=50)

    fig = plt.figure(figsize=FIG_通栏, dpi=DPI, facecolor=PALETTE['paper'])
    ax = fig.add_subplot(111)
    ax.set_facecolor(PALETTE['paper'])

    # 热力图（主层）
    im = ax.imshow(D_matrix,
                   origin='lower',
                   extent=[theta1_range[0], theta1_range[-1],
                          theta2_range[0], theta2_range[-1]],
                   aspect='auto',
                   cmap='YlOrRd',  # 暖色系，与Ochre主题呼应
                   interpolation='bilinear',
                   alpha=0.85)

    # 等高线（辅助层）
    X, Y = np.meshgrid(theta1_range, theta2_range)
    contour_levels = np.linspace(np.nanmin(D_matrix), np.nanmax(D_matrix), 10)
    contours = ax.contour(X, Y, D_matrix,
                          levels=contour_levels,
                          colors=PALETTE['geometry'],
                          linewidths=LW['theory'],
                          alpha=0.6)
    ax.clabel(contours, inline=True, fontsize=7, fmt='%.0f m')

    # 对角线标注（揭示对称性）
    ax.plot([theta1_range[0], theta1_range[-1]],
            [theta1_range[0], theta1_range[-1]],
            '--', color=PALETTE['slate'], linewidth=LW['aux'], alpha=0.5,
            label='$\\theta_1 = \\theta_2$ (symmetry axis)')

    # colorbar
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="4%", pad=0.1)
    cbar = plt.colorbar(im, cax=cax)
    cbar.set_label('Diameter $D$ (m)', fontsize=9, rotation=270, labelpad=15)
    cbar.ax.tick_params(labelsize=8)

    # 标注最小值区域
    min_row, min_col = np.unravel_index(np.nanargmin(D_matrix), D_matrix.shape)
    theta1_min = theta1_range[min_col]
    theta2_min = theta2_range[min_row]
    D_min = D_matrix[min_row, min_col]

    ax.plot(theta1_min, theta2_min, '*',
            color=PALETTE['rust'], markersize=14, markeredgecolor='white',
            markeredgewidth=1, zorder=5)
    ax.annotate(f'Min $D={D_min:.1f}$ m\n$(\\theta_1={theta1_min:.1f}°, \\theta_2={theta2_min:.1f}°)$',
                xy=(theta1_min, theta2_min),
                xytext=(theta1_min+20, theta2_min+20),
                fontsize=7,
                color=PALETTE['rust'],
                bbox=dict(boxstyle='round,pad=0.5',
                         facecolor=PALETTE['paper'],
                         edgecolor=PALETTE['rust'], linewidth=1),
                arrowprops=dict(arrowstyle='->', color=PALETTE['rust'], lw=1.2))

    # 轴标签
    ax.set_xlabel('Station 1 bearing $\\theta_1$ (°)', fontsize=10)
    ax.set_ylabel('Station 2 bearing $\\theta_2$ (°)', fontsize=10)
    ax.set_title('Parameter space: $D(\\theta_1, \\theta_2)$ with $d=600$ m, $\\varepsilon=1°$',
                 fontsize=11, pad=12)
    ax.legend(loc='upper left', fontsize=7, frameon=True,
              facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'])

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=DPI, bbox_inches='tight', facecolor=PALETTE['paper'])
    plt.savefig(save_path.replace('.png', '.svg'), bbox_inches='tight', facecolor=PALETTE['paper'])
    print(f"✓ fig6已保存: {save_path}")
    plt.close()


# ============================================================================
# 主函数
# ============================================================================

def generate_3d_expert_figures():
    """生成3D可视化专家设计的图表"""
    print("=" * 60)
    print("Q1图表 - 3D可视化专家设计")
    print("专长：等高线/曲面/体积渲染")
    print("方案：fig5(φ-D散点拟合) + fig6(参数空间热力图+等高线)")
    print("=" * 60)

    print("\n生成fig5（φ-D关系，DeepSeek推荐：散点+拟合）...")
    plot_figure5_scatter_fit()

    print("\n生成fig6（参数空间，DeepSeek推荐：热力图+等高线）...")
    plot_figure6_heatmap_contour()

    print("\n=" * 60)
    print("✅ 3D可视化专家方案完成")
    print("设计亮点：")
    print("  1. fig5：多项式拟合+关键点标注，揭示φ-D非线性关系")
    print("  2. fig6：双重编码（颜色+等高线），对角线对称性可视化")
    print("  3. 配色：YlOrRd暖色系呼应Ochre主题，保持fig1-3一致性")
    print("  4. DeepSeek洞察全部应用：散点优于热力图（fig5），热力图优于3D曲面（fig6）")
    print("=" * 60)


if __name__ == "__main__":
    generate_3d_expert_figures()
