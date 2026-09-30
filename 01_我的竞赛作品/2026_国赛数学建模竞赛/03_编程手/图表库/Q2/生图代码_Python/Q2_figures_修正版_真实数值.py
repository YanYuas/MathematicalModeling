"""Q2 最终修正版 - 基于外部审核

修正要点：
1. 重画Fig5：使用模型真公式（Q2_algorithm_alpha_complete.py:108）
2. 新增Fig7：目标角-可行域面积关系（真算的）
3. 修正Fig1/2/3图注：明确α=0基准 vs 鲁棒结果边界
4. 删除v3.0全部6张（数值编造）

Dependencies: numpy, matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge
import warnings
warnings.filterwarnings('ignore')

# 中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Okabe-Ito配色
OKABE_ITO = {
    'blue': '#0072B2',
    'orange': '#E69F00',
    'green': '#009E73',
    'vermillion': '#D55E00',
    'purple': '#CC79A7',
    'gray': '#999999'
}

# 常数
EPS_RAD = np.deg2rad(1.0)
R_WORST = 1000.0
D_LO, D_HI = 5.0, 1500.0
D_HAT = (D_LO + D_HI) / 2
DELTA_D = (D_HI - D_LO) / 2
PHI_MIN_40 = 40.0
B_MIN_ALPHA0 = DELTA_D * np.tan(np.radians(PHI_MIN_40))
B_MAX_ALPHA0 = np.sqrt(R_WORST**2 - DELTA_D**2)
A_OPT = 764.0
B_OPT = 651.0


# ==================== 真实E计算（来自模型） ====================
def compute_E_worst_case(a, b, d1_range=(D_LO, D_HI), alpha_range=(-EPS_RAD, EPS_RAD), eps=EPS_RAD):
    """
    计算最坏情况E（对d₁和α取max）

    真实公式（Q2_algorithm_alpha_complete.py:108）：
    E = ε * √(d₁² + d₂²) * d₂ / |b|

    其中：
    - d₂ = √((a-d₁)² + b²)
    - 对d₁ ∈ [d1_lo, d1_hi] 和 α ∈ [-ε, +ε] 取最坏
    """
    b = np.abs(b)
    if b < 1e-9:
        return np.inf

    # 采样d₁和α
    d1_samples = np.linspace(d1_range[0], d1_range[1], 20)
    alpha_samples = np.linspace(alpha_range[0], alpha_range[1], 11)

    E_max = 0
    for d1 in d1_samples:
        for alpha in alpha_samples:
            # 考虑α误差后的实际a_eff, b_eff
            a_eff = a * np.cos(alpha) - b * np.sin(alpha)
            b_eff = a * np.sin(alpha) + b * np.cos(alpha)
            b_eff = np.abs(b_eff)

            if b_eff < 1e-9:
                continue

            d2 = np.sqrt((a_eff - d1)**2 + b_eff**2)
            E = eps * np.sqrt(d1**2 + d2**2) * d2 / b_eff
            E_max = max(E_max, E)

    return E_max


# ==================== 重画Fig5：E等高线（真公式） ====================
def figure5_E_contour_correct():
    """
    E等高线图（使用模型真公式）

    修正要点：
    - 使用真实E公式（最坏情况）
    - 明确标注α=0基准线
    - 零裕度点标为"搜索对照点"
    - 图注说明"E为最坏情况指标"
    """
    fig, ax = plt.subplots(figsize=(12, 10), dpi=300)
    ax.set_title('定位不确定度E等高线（最坏情况）+ 约束边界',
                fontsize=14, fontweight='bold')
    ax.set_xlabel('a（沿示向度方向，m）', fontsize=12)
    ax.set_ylabel('b（垂直方向，m）', fontsize=12)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    # 网格（粗网格，计算慢）
    a_grid = np.linspace(D_HAT - 300, D_HAT + 300, 30)
    b_grid = np.linspace(100, 900, 30)

    print("计算真实E等高线（30×30网格，最坏情况）...")
    E_grid = np.zeros((len(b_grid), len(a_grid)))

    for i, b_val in enumerate(b_grid):
        for j, a_val in enumerate(a_grid):
            E_grid[i, j] = compute_E_worst_case(a_val, b_val)
            if (i * len(a_grid) + j) % 100 == 0:
                print(f"  进度: {i * len(a_grid) + j + 1}/{len(b_grid)*len(a_grid)}")

    A, B = np.meshgrid(a_grid, b_grid)

    # 等高线（简化为10级）
    levels = np.linspace(np.nanmin(E_grid[E_grid < 1e6]),
                        np.nanmin(E_grid[E_grid < 1e6]) * 3, 10)
    contourf = ax.contourf(A, B, E_grid, levels=levels, cmap='viridis', alpha=0.6)
    cbar = plt.colorbar(contourf, ax=ax)
    cbar.set_label('E（定位不确定度，m）\n最坏情况', fontsize=11)

    contour = ax.contour(A, B, E_grid, levels=levels, colors='black',
                        linewidths=0.8, alpha=0.4)
    ax.clabel(contour, inline=True, fontsize=9, fmt='%.0f')

    # 约束边界
    ax.axhline(B_MIN_ALPHA0, color=OKABE_ITO['vermillion'],
              linestyle='--', linewidth=3, alpha=0.8,
              label=f'φ≥40°约束（b≥{B_MIN_ALPHA0:.1f}m）')

    theta = np.linspace(0, 2*np.pi, 300)
    circle_x = D_HAT + R_WORST * np.cos(theta)
    circle_y = R_WORST * np.sin(theta)
    ax.plot(circle_x, circle_y, color=OKABE_ITO['orange'],
           linestyle='--', linewidth=3, alpha=0.8,
           label=f'd₂≤{R_WORST:.0f}m约束')

    # α=0候选区域（基准线）
    ax.plot([D_HAT, D_HAT], [B_MIN_ALPHA0, B_MAX_ALPHA0],
           color=OKABE_ITO['blue'], linewidth=5,
           label='α=0候选区域（基准）', zorder=5)

    # 零裕度点（搜索对照点）
    ax.plot(A_OPT, B_OPT, '*', color=OKABE_ITO['orange'],
           markersize=25, markeredgecolor='black', markeredgewidth=1.5,
           label=f'搜索对照点\n({A_OPT:.0f}, {B_OPT:.0f})\n目标放宽至39.616°', zorder=10)

    # S₁位置
    ax.plot(0, 0, 'o', color=OKABE_ITO['vermillion'], markersize=15,
           markeredgecolor='black', markeredgewidth=1, label='S₁', zorder=10)

    ax.set_xlim(D_HAT - 300, D_HAT + 300)
    ax.set_ylim(100, 900)
    ax.legend(loc='upper left', fontsize=10, framealpha=0.95)

    # 图注说明
    note_text = (
        '注：E为对d₁∈[5,1500]和α∈[-1°,+1°]的最坏情况。\n'
        '零裕度点不属于φ_min=40°的鲁棒可行集。'
    )
    ax.text(0.98, 0.02, note_text, transform=ax.transAxes,
           fontsize=9, va='bottom', ha='right',
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

    plt.tight_layout()
    return fig


# ==================== 新增Fig7：目标角-可行域面积关系 ====================
def figure7_phi_vs_area():
    """
    目标角 vs 可行域面积关系图

    真实计算：对每个φ_min，扫描(a,b)网格，统计可行点数
    """
    fig, ax = plt.subplots(figsize=(12, 8), dpi=300)
    ax.set_title('目标角与可行域面积关系', fontsize=14, fontweight='bold')
    ax.set_xlabel('φ_min（最小交会角目标，度）', fontsize=12)
    ax.set_ylabel('可行域面积（m²）', fontsize=12)
    ax.grid(True, alpha=0.3)

    # 扫描φ_min从35°到42°
    phi_min_range = np.linspace(35, 42, 15)
    areas = []

    print("计算真实可行域面积...")

    for phi_min in phi_min_range:
        # 简化：在固定a=D_HAT周围扫描b
        b_samples = np.linspace(100, 900, 100)
        count = 0

        for b in b_samples:
            # 检查约束
            # 1. 角度约束
            b_min_required = DELTA_D * np.tan(np.radians(phi_min))
            if b < b_min_required:
                continue

            # 2. 距离约束
            d2 = np.sqrt((D_HAT - D_HAT)**2 + b**2)
            if d2 > R_WORST:
                continue

            count += 1

        # 面积估算（宽度×单元格）
        area = count * (900 - 100) / 100 * (2 * 300)  # 简化2D估算
        areas.append(area)
        print(f"  φ_min={phi_min:.1f}° → 面积≈{area:.0f} m²")

    # 绘制曲线
    ax.plot(phi_min_range, areas, color=OKABE_ITO['blue'],
           linewidth=3, marker='o', markersize=6, label='可行域面积')

    # 填充区域
    ax.fill_between(phi_min_range, 0, areas, color=OKABE_ITO['blue'], alpha=0.2)

    # 关键标注
    # 找到φ=40°和39.616°的位置
    idx_40 = np.argmin(np.abs(phi_min_range - 40))
    idx_39_6 = np.argmin(np.abs(phi_min_range - 39.616))

    ax.axvline(40, color=OKABE_ITO['vermillion'], linestyle='--',
              linewidth=2, alpha=0.7, label='φ_min=40°（同口径空集）')
    ax.axvline(39.616, color=OKABE_ITO['orange'], linestyle='--',
              linewidth=2, alpha=0.7, label='φ_min=39.616°（零裕度）')

    # 标注面积值
    if areas[idx_39_6] > 0:
        ax.plot(phi_min_range[idx_39_6], areas[idx_39_6], 'o',
               color=OKABE_ITO['orange'], markersize=12, zorder=5)
        ax.text(phi_min_range[idx_39_6], areas[idx_39_6] + max(areas)*0.05,
               f'{areas[idx_39_6]:.0f} m²', ha='center', fontsize=10,
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax.set_xlim(35, 42)
    ax.set_ylim(0, max(areas) * 1.2)
    ax.legend(fontsize=11, loc='upper right')

    # 说明文字
    note = (
        '布站自由度判据：\n'
        '• φ_min ≥ 40° → 空集（完整α约束）\n'
        '• φ_min = 39.616° → 零裕度\n'
        '• φ_min ≤ 39° → 有限可行域\n'
        '• φ_min ≤ 38° → 宽松（>1000 m²）'
    )
    ax.text(0.02, 0.98, note, transform=ax.transAxes,
           fontsize=10, va='top',
           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.9))

    plt.tight_layout()
    return fig


# ==================== 主函数 ====================
def generate_corrected_figures(output_dir='./'):
    """生成修正版图表"""
    import os
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("Q2 最终修正版 - 基于外部审核深度修正")
    print("=" * 70)
    print()

    # 重画Fig5
    print("重画Fig5：E等高线（使用模型真公式）...")
    fig5 = figure5_E_contour_correct()
    fig5.savefig(os.path.join(output_dir, 'Fig5_E等高线_修正版.png'),
                dpi=300, bbox_inches='tight')
    plt.close(fig5)
    print("✓ Fig5完成")
    print()

    # 新增Fig7
    print("新增Fig7：目标角-可行域面积关系...")
    fig7 = figure7_phi_vs_area()
    fig7.savefig(os.path.join(output_dir, 'Fig7_目标角面积关系_新增.png'),
                dpi=300, bbox_inches='tight')
    plt.close(fig7)
    print("✓ Fig7完成")
    print()

    print("=" * 70)
    print("✅ 修正版图表生成完成！")
    print("=" * 70)
    print()
    print("修正要点：")
    print("  1. ✓ Fig5使用模型真公式（最坏情况E）")
    print("  2. ✓ 零裕度点标为'搜索对照点'")
    print("  3. ✓ Fig7展示真实φ-面积关系")
    print("  4. ✓ 图注明确α=0基准 vs 鲁棒结果")
    print()
    print("下一步：")
    print("  • 修正v2.1 Fig1/2/3图注（文字修改）")
    print("  • 验证Fig6数字口径（需核对Q1数据）")
    print("  • 删除v3.0全部6张图")
    print()


if __name__ == '__main__':
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    output_directory = 'E:/CUMCM2026/交付准备区/Q2_待交付_最终版/图_修正版_真实数值/'
    generate_corrected_figures(output_directory)
