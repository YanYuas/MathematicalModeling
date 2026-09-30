"""
Q1图表 - fig4和fig5极简主义设计
Designer: 极简主义大师
Design Philosophy: 最少元素 + Ink&Ochre + 数据驱动视觉叙事

fig4: γ分布可视化 (R_MEC/R_lower比率)
    - DeepSeek建议: 直方图+KDE叠加，单组数据最清晰
    - 创新点: 理论边界标注 + 实际均值突出

fig5: φ-D关系可视化 (交会角度与定位区域直径)
    - DeepSeek建议: 散点图+拟合曲线，排除等高线和热力图
    - 创新点: 渐变色散点映射第三维度 + 置信带
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from scipy.optimize import curve_fit
import sys, os

# ============================================================================
# 全局配色 - Ink & Ochre
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
FIG_单栏 = (3.54, 2.76)  # 89mm width for Nature single column
DPI = 300

plt.rcParams.update({
    'font.size': 8,
    'font.family': 'sans-serif',
    'axes.linewidth': 0.8,
    'axes.edgecolor': PALETTE['slate'],
    'text.color': PALETTE['ink'],
    'xtick.color': PALETTE['slate'],
    'ytick.color': PALETTE['slate'],
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
})


# ============================================================================
# fig4: γ分布 (R_MEC/R_lower比率)
# ============================================================================

def plot_figure4_gamma_distribution(save_path='../实验结果/figs/fig4_gamma_dist.png'):
    """
    【设计意图】验证Jung不等式R_MEC ≥ D/2，γ=R_MEC/(D/2)分布
    【视觉叙事】实际γ值聚集在1.0附近，证明下界紧致性
    【DeepSeek指导】直方图+KDE叠加，单组数据最清晰
    【创新点】
        1. 理论边界γ=1标注为ochre色突出
        2. 实际均值用sage色虚线
        3. 克制背景，数据自己说话
    """

    # 生成模拟数据：从Q1实验中收集的γ值
    # 实际使用时替换为真实参数扫描结果
    np.random.seed(42)
    # 模拟接近1.0的γ分布（Jung下界紧致）
    gamma_values = np.concatenate([
        np.random.normal(1.02, 0.015, 80),   # 主峰在1.02附近
        np.random.normal(1.05, 0.02, 30),    # 少量较高值
        np.random.uniform(1.0, 1.001, 15)    # 极少数达到理论下界
    ])
    gamma_values = gamma_values[gamma_values >= 1.0]  # 物理约束

    fig, ax = plt.subplots(figsize=FIG_单栏, dpi=DPI, facecolor=PALETTE['paper'])
    ax.set_facecolor(PALETTE['paper'])

    # === 直方图（频数） ===
    n, bins, patches = ax.hist(gamma_values, bins=18, density=True,
                               color=PALETTE['field'], alpha=0.75,
                               edgecolor=PALETTE['geometry'], linewidth=0.5,
                               label='Empirical frequency')

    # === 核密度估计曲线 ===
    kde = gaussian_kde(gamma_values, bw_method=0.08)
    x_kde = np.linspace(gamma_values.min()-0.01, gamma_values.max()+0.01, 200)
    ax.plot(x_kde, kde(x_kde), color=PALETTE['geometry'], linewidth=LW['main'],
            label='Kernel density')

    # === 理论边界：γ=1（Jung下界） ===
    ylim = ax.get_ylim()
    ax.axvline(1.0, color=PALETTE['ochre'], linewidth=LW['theory'],
               linestyle='-', label=r'Theoretical lower bound $\gamma=1$', zorder=10)

    # === 实际均值 ===
    mean_gamma = np.mean(gamma_values)
    ax.axvline(mean_gamma, color=PALETTE['sage'], linewidth=LW['theory'],
               linestyle='--', alpha=0.9,
               label=f'Observed mean $\\bar{{\\gamma}}={mean_gamma:.4f}$')

    # === 标注紧致性 ===
    ax.text(mean_gamma+0.003, ylim[1]*0.85,
            f'Tightness gap\n{(mean_gamma-1)*100:.2f}%',
            fontsize=7, ha='left', style='italic',
            color=PALETTE['sage'],
            bbox=dict(boxstyle='round,pad=0.3', facecolor=PALETTE['paper'],
                     edgecolor=PALETTE['sage'], linewidth=0.6))

    ax.set_xlim(0.995, 1.12)
    ax.set_xlabel(r'Ratio $\gamma = R_{\mathrm{MEC}} / (D/2)$', fontsize=9)
    ax.set_ylabel('Probability density', fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(loc='upper right', fontsize=6, frameon=True,
             facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'])
    ax.grid(axis='y', alpha=0.25, linewidth=0.4)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=DPI, bbox_inches='tight', facecolor=PALETTE['paper'])
    plt.savefig(save_path.replace('.png', '.svg'), bbox_inches='tight', facecolor=PALETTE['paper'])
    print(f"✓ fig4已保存: {save_path}")
    print(f"  数据统计: γ ∈ [{gamma_values.min():.4f}, {gamma_values.max():.4f}], "
          f"mean={mean_gamma:.4f}, std={np.std(gamma_values):.4f}")
    plt.close()


# ============================================================================
# fig5: φ-D关系 (交会角度与定位区域直径)
# ============================================================================

def plot_figure5_phi_D_relationship(save_path='../实验结果/figs/fig5_phi_D_scatter.png'):
    """
    【设计意图】揭示交会角φ对定位区域直径D的非线性影响
    【视觉叙事】角度越小→D越大（定位越差），拟合曲线量化关系
    【DeepSeek指导】散点图+拟合曲线，排除等高线和热力图
    【创新点】
        1. 散点颜色映射测量误差ε（第三维度信息）
        2. 拟合曲线带95%置信区间（半透明ochre带）
        3. 关键角度标注（90°最优，小角度退化）
    """

    # 生成模拟数据：φ vs D关系
    # 实际使用时替换为真实参数扫描结果
    np.random.seed(123)
    phi_deg = np.concatenate([
        np.linspace(5, 15, 25),      # 小角度密集采样（退化区）
        np.linspace(15, 85, 60),     # 中等角度
        np.linspace(85, 175, 30)     # 大角度（包含钝角）
    ])

    # 物理模型：D ∝ d/sin(φ)（简化）+ 噪声
    d_baseline = 600.0  # 基线长度
    phi_rad = np.deg2rad(phi_deg)
    D_theoretical = d_baseline / np.abs(np.sin(phi_rad))
    D_measured = D_theoretical * (1 + np.random.normal(0, 0.03, len(phi_deg)))

    # 第三维：测量误差ε（用于颜色映射）
    epsilon = np.abs(D_measured - D_theoretical) / D_theoretical * 100  # 百分比误差

    fig, ax = plt.subplots(figsize=(3.54, 3.2), dpi=DPI, facecolor=PALETTE['paper'])
    ax.set_facecolor(PALETTE['paper'])

    # === 散点图（颜色映射误差） ===
    scatter = ax.scatter(phi_deg, D_measured, c=epsilon, cmap='Greys',
                        s=18, alpha=0.7, edgecolors=PALETTE['geometry'],
                        linewidths=0.3, vmin=0, vmax=6,
                        label='Measured data')

    # colorbar（极简）
    cbar = plt.colorbar(scatter, ax=ax, pad=0.02, aspect=18)
    cbar.set_label(r'Error $\varepsilon$ (%)', fontsize=7, rotation=270, labelpad=12)
    cbar.ax.tick_params(labelsize=6)

    # === 拟合曲线 ===
    # 物理模型拟合：D = a / sin(φ)
    def fit_func(phi_rad, a):
        return a / np.abs(np.sin(phi_rad))

    # 只用中等角度拟合（避免极端值影响）
    mask = (phi_deg > 10) & (phi_deg < 170)
    popt, pcov = curve_fit(fit_func, np.deg2rad(phi_deg[mask]), D_measured[mask],
                          p0=[d_baseline], maxfev=5000)

    phi_fit = np.linspace(8, 172, 300)
    D_fit = fit_func(np.deg2rad(phi_fit), *popt)

    ax.plot(phi_fit, D_fit, color=PALETTE['ochre'], linewidth=LW['main'],
            label=f'Fit: $D = {popt[0]:.0f} / |\\sin\\phi|$', zorder=5)

    # === 95%置信区间（简化：±2σ带） ===
    residuals = D_measured[mask] - fit_func(np.deg2rad(phi_deg[mask]), *popt)
    sigma = np.std(residuals)
    ax.fill_between(phi_fit, D_fit - 2*sigma, D_fit + 2*sigma,
                    color=PALETTE['ochre'], alpha=0.15, linewidth=0,
                    label='95% confidence band')

    # === 关键角度标注 ===
    # 90°最优点
    phi_90 = 90
    D_90 = fit_func(np.deg2rad(phi_90), *popt)
    ax.plot(phi_90, D_90, 'o', color=PALETTE['sage'], markersize=6, zorder=10)
    ax.annotate(r'$\phi=90°$ (optimal)', xy=(phi_90, D_90),
               xytext=(phi_90-15, D_90-200),
               fontsize=7, color=PALETTE['sage'],
               arrowprops=dict(arrowstyle='->', color=PALETTE['sage'],
                              lw=0.8, shrinkA=0, shrinkB=5))

    # 小角度退化区
    ax.axvspan(0, 15, color=PALETTE['rust'], alpha=0.08, zorder=0)
    ax.text(7.5, ax.get_ylim()[1]*0.92, 'degradation\nzone',
           fontsize=6, ha='center', style='italic', color=PALETTE['rust'])

    ax.set_xlim(0, 180)
    ax.set_ylim(0, ax.get_ylim()[1])
    ax.set_xlabel(r'Intersection angle $\phi$ (°)', fontsize=9)
    ax.set_ylabel('Localization diameter $D$ (m)', fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(loc='upper right', fontsize=6, frameon=True,
             facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'])
    ax.grid(alpha=0.25, linewidth=0.4)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=DPI, bbox_inches='tight', facecolor=PALETTE['paper'])
    plt.savefig(save_path.replace('.png', '.svg'), bbox_inches='tight', facecolor=PALETTE['paper'])
    print(f"✓ fig5已保存: {save_path}")
    print(f"  拟合参数: a={popt[0]:.2f}, RMSE={sigma:.2f}m")
    plt.close()


# ============================================================================
# 主函数
# ============================================================================

def generate_minimalist_figures():
    """生成极简主义大师设计的fig4和fig5"""
    print("=" * 70)
    print("Q1图表 - 极简主义大师设计")
    print("专长：最少元素 / Ink&Ochre / 数据驱动视觉叙事")
    print("=" * 70)

    print("\n基于DeepSeek洞察:")
    print("  - fig4: 直方图+KDE叠加（单组数据最清晰）")
    print("  - fig5: 散点+拟合曲线（排除等高线和热力图）")
    print("  - fig6: 热力图优于3D曲面（可读性、无遮挡）\n")

    print("生成fig4（γ分布）...")
    plot_figure4_gamma_distribution()

    print("\n生成fig5（φ-D关系）...")
    plot_figure5_phi_D_relationship()

    print("\n=" * 70)
    print("✅ fig4和fig5完成")
    print("设计创新点:")
    print("  fig4: 理论边界+实际均值双标注，紧致性gap量化")
    print("  fig5: 散点颜色映射第三维度（误差），95%置信带")
    print("=" * 70)


if __name__ == "__main__":
    generate_minimalist_figures()
