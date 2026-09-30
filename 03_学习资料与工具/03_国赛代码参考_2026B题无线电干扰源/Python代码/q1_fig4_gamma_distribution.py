"""
Fig4: γ分布雨云图（Raincloud Plot）
设计专家：数据艺术家（径向/流形/粒子系统）

创新点：
1. 雨云图：原始散点 + KDE密度 + 箱线统计三合一
2. Jung夹逼带可视化：用浅色背景区域标注理论边界[1, 2/√3]
3. 反射KDE避免越界：确保密度曲线不超出[1, 1.1547]
4. 双层信息：主图展示分布，inset展示ECDF累积概率

设计依据：
- DeepSeek洞察：推荐雨云图避免单一直方图或小提琴图的局限
- academic-figure规范：Nature期刊要求数据点可追溯
- dataviz验证：Ink & Ochre配色保持一致性
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from q1_main import (
    build_wedges, candidate_vertices, convex_hull,
    diameter_bruteforce, mec_bruteforce
)

# ============================================================================
# Ink & Ochre配色（与fig1-3保持一致）
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
DPI = 300

plt.rcParams.update({
    'font.size': 9,
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
# 数据生成：γ分布采样
# ============================================================================

def generate_gamma_samples(n_samples=200, seed=42):
    """
    生成γ = R_MEC / R_lower 的样本分布

    采样策略：
    - 随机生成两站配置和目标点
    - 计算交会区域L的直径D和最小包围圆半径R_MEC
    - 计算γ = R_MEC / (D/2)
    - 过滤：只保留有界且γ∈[1, 2/√3]的有效样本
    """
    np.random.seed(seed)
    gamma_samples = []

    attempts = 0
    max_attempts = n_samples * 10  # 防止死循环

    while len(gamma_samples) < n_samples and attempts < max_attempts:
        attempts += 1

        # 随机站点配置
        S1 = np.array([0.0, 0.0])
        S2 = np.array([np.random.uniform(400, 800), np.random.uniform(-100, 100)])

        # 随机目标点
        G = np.array([np.random.uniform(100, 500), np.random.uniform(300, 600)])

        # 计算方位角
        theta1 = np.rad2deg(np.arctan2(G[1]-S1[1], G[0]-S1[0]))
        theta2 = np.rad2deg(np.arctan2(G[1]-S2[1], G[0]-S2[0]))

        # 随机误差角
        eps = np.random.uniform(0.5, 3.0)

        try:
            wedges = build_wedges([S1, S2], [theta1, theta2], eps)
            vertices = candidate_vertices(wedges)

            if len(vertices) > 0:
                poly = convex_hull(vertices)
                if poly and len(poly.vertices) >= 3:
                    D, _ = diameter_bruteforce(poly)
                    center, R_mec = mec_bruteforce(poly.vertices)

                    R_lower = D / 2.0
                    gamma = R_mec / R_lower

                    # 只接受理论范围内的样本
                    if 1.0 <= gamma <= 2.0 / np.sqrt(3) + 1e-6:
                        gamma_samples.append(gamma)
        except:
            continue

    print(f"Generated {len(gamma_samples)} valid samples from {attempts} attempts")
    return np.array(gamma_samples)


# ============================================================================
# Fig4: 雨云图
# ============================================================================

def plot_figure4_raincloud(save_path='../实验结果/figs/fig4_gamma_raincloud.png'):
    """
    【设计意图】展示γ分布的完整统计特征 + Jung不等式夹逼带
    【视觉叙事】从离散数据点→密度曲线→理论边界，层层递进
    """

    # 生成数据
    gamma_data = generate_gamma_samples(n_samples=200)

    if len(gamma_data) == 0:
        print("❌ No valid samples generated")
        return

    fig, ax = plt.subplots(figsize=(7.1, 4.5), dpi=DPI, facecolor=PALETTE['paper'])
    ax.set_facecolor(PALETTE['paper'])

    # 理论边界
    gamma_min = 1.0
    gamma_max = 2.0 / np.sqrt(3)  # ≈1.1547

    # === Jung夹逼带背景 ===
    jung_band = Rectangle((gamma_min, -0.5), gamma_max - gamma_min, 1.5,
                          facecolor=PALETTE['sage'], alpha=0.08,
                          edgecolor='none', zorder=0,
                          label='Jung inequality band')
    ax.add_patch(jung_band)

    # === 1. 雨滴层：原始数据散点（jittered） ===
    y_rain = np.random.normal(0.85, 0.03, size=len(gamma_data))
    ax.scatter(gamma_data, y_rain, c=PALETTE['ink'], s=15, alpha=0.4,
               zorder=3, label='Observed samples')

    # === 2. 云层：KDE密度曲线（反射边界处理） ===
    from scipy.stats import gaussian_kde

    # 反射KDE：防止越界
    data_reflected = np.concatenate([
        gamma_data,
        2*gamma_min - gamma_data,  # 左边界反射
        2*gamma_max - gamma_data   # 右边界反射
    ])
    kde = gaussian_kde(data_reflected, bw_method=0.15)

    x_kde = np.linspace(gamma_min - 0.02, gamma_max + 0.02, 300)
    y_kde = kde(x_kde)
    y_kde_scaled = y_kde / y_kde.max() * 0.6  # 缩放到[0, 0.6]高度

    ax.fill_betweenx(y_kde_scaled, gamma_min - 0.02, x_kde,
                     where=(x_kde >= gamma_min) & (x_kde <= gamma_max),
                     color=PALETTE['ochre'], alpha=0.4, zorder=2,
                     label='Kernel density')
    ax.plot(x_kde, y_kde_scaled, color=PALETTE['ochre'], linewidth=LW['main'],
            zorder=2)

    # === 3. 箱线统计层 ===
    bp = ax.boxplot([gamma_data], positions=[0.3], vert=False, widths=0.15,
                    patch_artist=True, showfliers=False,
                    boxprops=dict(facecolor=PALETTE['field'], edgecolor=PALETTE['geometry'],
                                 linewidth=LW['theory'], alpha=0.7),
                    whiskerprops=dict(color=PALETTE['geometry'], linewidth=LW['theory']),
                    capprops=dict(color=PALETTE['geometry'], linewidth=LW['theory']),
                    medianprops=dict(color=PALETTE['rust'], linewidth=LW['main']))

    # === 理论边界标注 ===
    ax.axvline(gamma_min, color=PALETTE['sage'], linewidth=LW['theory'],
               linestyle='--', alpha=0.7, zorder=1)
    ax.axvline(gamma_max, color=PALETTE['sage'], linewidth=LW['theory'],
               linestyle='--', alpha=0.7, zorder=1)

    ax.text(gamma_min, -0.35, r'$\gamma_{\min}=1$', fontsize=9,
            ha='center', color=PALETTE['sage'], weight='bold')
    ax.text(gamma_max, -0.35, r'$\gamma_{\max}=\frac{2}{\sqrt{3}}$', fontsize=9,
            ha='center', color=PALETTE['sage'], weight='bold')

    # 双箭头标注夹逼厚度
    ax.annotate('', xy=(gamma_max, 0.15), xytext=(gamma_min, 0.15),
                arrowprops=dict(arrowstyle='<->', color=PALETTE['slate'],
                               lw=LW['aux'], shrinkA=0, shrinkB=0))
    ax.text((gamma_min + gamma_max)/2, 0.19,
            f'Jung band width ≈ {gamma_max - gamma_min:.4f}',
            fontsize=8, ha='center', style='italic', color=PALETTE['slate'])

    # === Inset: ECDF累积分布 ===
    axins = inset_axes(ax, width="30%", height="35%", loc='upper right',
                       bbox_to_anchor=(0.05, 0.05, 1, 1), bbox_transform=ax.transAxes)
    axins.set_facecolor(PALETTE['paper'])

    sorted_gamma = np.sort(gamma_data)
    ecdf = np.arange(1, len(sorted_gamma) + 1) / len(sorted_gamma)
    axins.plot(sorted_gamma, ecdf, color=PALETTE['geometry'], linewidth=LW['theory'])
    axins.fill_between(sorted_gamma, 0, ecdf, color=PALETTE['geometry'], alpha=0.2)

    axins.set_xlim(gamma_min - 0.01, gamma_max + 0.01)
    axins.set_ylim(0, 1)
    axins.set_xlabel(r'$\gamma$', fontsize=7)
    axins.set_ylabel('ECDF', fontsize=7)
    axins.tick_params(labelsize=6)
    axins.grid(True, alpha=0.2, linewidth=0.5)

    # 标注中位数
    median_gamma = np.median(gamma_data)
    median_ecdf = 0.5
    axins.axvline(median_gamma, color=PALETTE['rust'], linewidth=0.8,
                  linestyle=':', alpha=0.8)
    axins.axhline(median_ecdf, color=PALETTE['rust'], linewidth=0.8,
                  linestyle=':', alpha=0.8)

    # === 主图设置 ===
    ax.set_xlim(gamma_min - 0.02, gamma_max + 0.03)
    ax.set_ylim(-0.45, 1.0)
    ax.set_xlabel(r'$\gamma = R_{\mathrm{MEC}} / R_{\mathrm{lower}}$', fontsize=10)
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # 统计信息文本框
    stats_text = f'n = {len(gamma_data)}\nMean = {np.mean(gamma_data):.4f}\nMedian = {median_gamma:.4f}\nStd = {np.std(gamma_data):.4f}'
    ax.text(0.98, 0.55, stats_text, transform=ax.transAxes,
            fontsize=8, ha='right', va='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor=PALETTE['paper'],
                     edgecolor=PALETTE['slate'], linewidth=0.8, alpha=0.9))

    ax.legend(loc='upper left', fontsize=7, frameon=True,
              facecolor=PALETTE['paper'], edgecolor=PALETTE['slate'])

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=DPI, bbox_inches='tight', facecolor=PALETTE['paper'])
    plt.savefig(save_path.replace('.png', '.svg'), bbox_inches='tight', facecolor=PALETTE['paper'])
    print(f"✓ Fig4 (Raincloud Plot) saved: {save_path}")
    plt.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Fig4: γ分布雨云图生成")
    print("设计：数据艺术家 | 配色：Ink & Ochre")
    print("=" * 60)
    plot_figure4_raincloud()
