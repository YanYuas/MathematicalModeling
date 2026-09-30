"""Q2 创新可视化 v3.0 - P0核心三张

图1：Sankey流图 - 信息级联效应
图2：热力图动画 - 可行域崩塌
图3：等高线叠加 - E景观+约束边界

Dependencies: numpy, matplotlib, plotly, seaborn
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle, Polygon, Circle
import warnings
warnings.filterwarnings('ignore')

# 中文字体
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass

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
R_WORST = 1000.0
D_HAT = 752.5
DELTA_D = 747.5
PHI_MIN_40 = 40.0
B_MIN_ALPHA0 = DELTA_D * np.tan(np.radians(PHI_MIN_40))
B_MAX_ALPHA0 = np.sqrt(R_WORST**2 - DELTA_D**2)
PHI_MIN_MAX_ALPHA = 39.616116
A_OPT = 764.0
B_OPT = 651.0


# ==================== 图1：Sankey流图（信息级联） ====================
def figure1_sankey_flow():
    """
    Sankey流图：两个信息缺口的级联效应

    使用matplotlib手工绘制（plotly需要单独安装）
    """
    fig, ax = plt.subplots(figsize=(14, 10), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # 标题
    ax.text(5, 9.5, '信息级联效应：从完美信息到零裕度定点',
            fontsize=18, fontweight='bold', ha='center')

    # 定义节点位置（x, y, 宽度）
    nodes = {
        'perfect': (1, 8, 0.8),       # 完美信息
        'known_d': (3, 8.5, 0.6),     # 源距已知
        'unknown_d': (3, 7.5, 0.6),   # 源距未知
        'alpha0': (5, 8, 0.5),        # α=0
        'alpha_err': (5, 7, 0.5),     # α误差
        'phi90': (7, 8.5, 0.4),       # φ=90°
        'phi41': (7, 7.5, 0.4),       # φ=41.63°
        'phi39': (7, 6.5, 0.4),       # φ=39.616°
        'E_min': (9, 8.5, 0.3),       # E极小
        'E_med': (9, 7.5, 0.3),       # E中等
        'E_high': (9, 6.5, 0.3)       # E高/零裕度
    }

    # 绘制节点
    for key, (x, y, w) in nodes.items():
        if 'perfect' in key:
            color = OKABE_ITO['green']
            label = '完美信息'
        elif 'known' in key:
            color = '#90EE90'
            label = '源距已知'
        elif 'unknown' in key:
            color = '#FFD700'
            label = '源距未知\n(Δd=747.5m)'
        elif 'alpha0' in key:
            color = OKABE_ITO['blue']
            label = 'α=0°'
        elif 'alpha_err' in key:
            color = OKABE_ITO['orange']
            label = 'α∈[-1°,+1°]'
        elif 'phi90' in key:
            color = OKABE_ITO['green']
            label = 'φ=90°\n(最优)'
        elif 'phi41' in key:
            color = '#FFD700'
            label = 'φ≤41.63°'
        elif 'phi39' in key:
            color = OKABE_ITO['vermillion']
            label = 'φ≤39.616°\n(数值搜索)'
        elif 'E_min' in key:
            color = OKABE_ITO['green']
            label = 'E极小'
        elif 'E_med' in key:
            color = '#FFD700'
            label = 'E中等'
        else:
            color = OKABE_ITO['vermillion']
            label = 'E高\n零裕度定点'

        rect = Rectangle((x - w/2, y - 0.25), w, 0.5,
                        facecolor=color, edgecolor='black', linewidth=2, alpha=0.8)
        ax.add_patch(rect)
        ax.text(x, y, label, ha='center', va='center', fontsize=9, fontweight='bold')

    # 绘制流向箭头（简化版Sankey）
    def draw_flow(x1, y1, x2, y2, width, color, label=''):
        # 使用多边形模拟流
        y_offset = width / 2
        poly = Polygon([
            (x1, y1 - y_offset), (x1, y1 + y_offset),
            (x2, y2 + y_offset), (x2, y2 - y_offset)
        ], facecolor=color, edgecolor='none', alpha=0.4)
        ax.add_patch(poly)

        # 标注
        if label:
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mid_x, mid_y + 0.3, label, fontsize=8, ha='center',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

    # 第一级分支：完美信息 → 源距已知/未知
    draw_flow(1.4, 8, 2.7, 8.5, 0.3, OKABE_ITO['green'], '')
    draw_flow(1.4, 8, 2.7, 7.5, 0.3, '#FFD700', 'Δd=747.5m')

    # 第二级分支：源距已知 → φ=90°
    draw_flow(3.3, 8.5, 6.8, 8.5, 0.25, OKABE_ITO['green'], '')

    # 源距未知 → α=0 → φ≤41.63°
    draw_flow(3.3, 7.5, 4.75, 8, 0.25, OKABE_ITO['blue'], '')
    draw_flow(5.25, 8, 6.8, 7.5, 0.25, '#FFD700', '-48.4°')

    # 源距未知 → α误差 → φ≤39.616°
    draw_flow(3.3, 7.5, 4.75, 7, 0.25, OKABE_ITO['orange'], '')
    draw_flow(5.25, 7, 6.8, 6.5, 0.25, OKABE_ITO['vermillion'], '-2.01°')

    # 第三级：φ → E
    draw_flow(7.2, 8.5, 8.85, 8.5, 0.2, OKABE_ITO['green'], '')
    draw_flow(7.2, 7.5, 8.85, 7.5, 0.2, '#FFD700', '')
    draw_flow(7.2, 6.5, 8.85, 6.5, 0.2, OKABE_ITO['vermillion'], '')

    # 信息损失标注
    ax.annotate('', xy=(3, 6.8), xytext=(3, 6.2),
                arrowprops=dict(arrowstyle='->', lw=3, color='red'))
    ax.text(3, 6, '信息损失\n级联效应', ha='center', fontsize=11, fontweight='bold',
           color='red', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))

    # 图例
    legend_y = 1.5
    ax.text(1, legend_y, '颜色编码：', fontsize=10, fontweight='bold')
    ax.add_patch(Rectangle((1, legend_y - 0.5), 0.3, 0.2, facecolor=OKABE_ITO['green'], alpha=0.8))
    ax.text(1.5, legend_y - 0.4, '信息丰富', fontsize=9)
    ax.add_patch(Rectangle((3, legend_y - 0.5), 0.3, 0.2, facecolor='#FFD700', alpha=0.8))
    ax.text(3.5, legend_y - 0.4, '信息稀缺', fontsize=9)
    ax.add_patch(Rectangle((5, legend_y - 0.5), 0.3, 0.2, facecolor=OKABE_ITO['vermillion'], alpha=0.8))
    ax.text(5.5, legend_y - 0.4, '零裕度/空集', fontsize=9)

    plt.tight_layout()
    return fig


# ==================== 图2：热力图动画（可行域崩塌） ====================
def figure2_heatmap_animation():
    """
    热力图动画：4帧展示可行域随α的崩塌
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 14), dpi=300)
    fig.suptitle('可行域的崩塌：α从0°到±1°', fontsize=16, fontweight='bold')

    # 4个α值
    alphas = [0, 0.5, 0.9, 1.0]
    titles = [
        'α=0°（理想基准）\n可行域：大片区域',
        'α=±0.5°（轻微鲁棒）\n可行域：收缩至狭长条',
        'α=±0.9°（临界边缘）\n可行域：接近消失',
        'α=±1°（完全鲁棒）\n可行域：零裕度定点'
    ]

    # 网格
    a_range = np.linspace(D_HAT - 300, D_HAT + 300, 150)
    b_range = np.linspace(100, 900, 150)
    A, B = np.meshgrid(a_range, b_range)

    for idx, (ax, alpha_val, title) in enumerate(zip(axes.flat, alphas, titles)):
        # 简化的φ计算（定性）
        alpha_rad = np.radians(alpha_val)

        # 模拟φ值（简化公式）
        numerator = np.abs((A - D_HAT) * np.sin(alpha_rad) - B * np.cos(alpha_rad))
        d2 = np.sqrt((A - D_HAT)**2 + B**2 + R_WORST**2 - 2*R_WORST*((A-D_HAT)*np.cos(alpha_rad) + B*np.sin(alpha_rad)))
        d2 = np.maximum(d2, 1e-9)
        sin_phi = numerator / d2
        phi = np.degrees(np.arcsin(np.minimum(sin_phi, 1.0)))

        # 约束：φ≥40°, d2≤1000
        feasible = (phi >= PHI_MIN_40) & (d2 <= R_WORST)
        phi_masked = np.where(feasible, phi, np.nan)

        # 热力图
        im = ax.contourf(A, B, phi_masked, levels=15, cmap='RdYlGn', alpha=0.8)

        # 等高线
        contour = ax.contour(A, B, phi_masked, levels=[40, 50, 60, 70, 80],
                            colors='black', linewidths=1, alpha=0.5)
        ax.clabel(contour, inline=True, fontsize=8, fmt='%d°')

        # 标注关键点
        if alpha_val == 0:
            ax.axvline(D_HAT, color='blue', linestyle='--', linewidth=2, alpha=0.6)
            ax.plot([D_HAT, D_HAT], [B_MIN_ALPHA0, B_MAX_ALPHA0],
                   'b-', linewidth=4, label='可行区域')
        elif alpha_val == 1.0:
            ax.plot(A_OPT, B_OPT, '*', color='red', markersize=20,
                   markeredgecolor='black', markeredgewidth=1, label='零裕度定点')

        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel('a（沿示向度，m）', fontsize=10)
        ax.set_ylabel('b（垂直方向，m）', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
        ax.legend(fontsize=9)

        # colorbar
        if idx == 1:
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('φ（交会角，度）', fontsize=10)

    plt.tight_layout()
    return fig


# ==================== 图3：等高线叠加（E景观） ====================
def figure3_contour_overlay():
    """
    等高线叠加图：E景观 + 约束边界 + 关键点
    """
    fig, ax = plt.subplots(figsize=(12, 10), dpi=300)
    ax.set_title('定位不确定度E景观 + 约束边界 + 关键点',
                fontsize=14, fontweight='bold')
    ax.set_xlabel('a（沿示向度方向，m）', fontsize=12)
    ax.set_ylabel('b（垂直方向，m）', fontsize=12)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    # 网格
    a_grid = np.linspace(D_HAT - 400, D_HAT + 400, 200)
    b_grid = np.linspace(50, 950, 200)
    A, B = np.meshgrid(a_grid, b_grid)

    # 简化的E计算（定性地形）
    Delta_a = A - D_HAT
    E = 15 + 3 * np.sqrt(Delta_a**2 / 10000 + (B - 650)**2 / 10000)

    # 底层：E等高线填充（地形图风格）
    contourf = ax.contourf(A, B, E, levels=20, cmap='terrain', alpha=0.6)
    cbar = plt.colorbar(contourf, ax=ax)
    cbar.set_label('E（定位不确定度，m）', fontsize=11)

    # 中层：等高线
    contour = ax.contour(A, B, E, levels=15, colors='black',
                        linewidths=1, alpha=0.4)
    ax.clabel(contour, inline=True, fontsize=9, fmt='%.1f')

    # 中层：约束边界
    # φ≥40°约束（简化为b≥b_min）
    ax.axhline(B_MIN_ALPHA0, color=OKABE_ITO['vermillion'],
              linestyle='--', linewidth=3, alpha=0.8,
              label=f'φ≥40°约束（b≥{B_MIN_ALPHA0:.1f}m）')

    # d₂≤1000约束（圆弧）
    theta = np.linspace(0, 2*np.pi, 300)
    circle_x = D_HAT + R_WORST * np.cos(theta)
    circle_y = R_WORST * np.sin(theta)
    ax.plot(circle_x, circle_y, color=OKABE_ITO['orange'],
           linestyle='--', linewidth=3, alpha=0.8,
           label=f'd₂≤{R_WORST:.0f}m约束')

    # 交集区域填充（半透明绿色）
    b_feasible = np.linspace(B_MIN_ALPHA0, B_MAX_ALPHA0, 100)
    a_left = D_HAT - np.sqrt(np.maximum(0, R_WORST**2 - b_feasible**2))
    a_right = D_HAT + np.sqrt(np.maximum(0, R_WORST**2 - b_feasible**2))
    ax.fill_betweenx(b_feasible, a_left, a_right,
                     color=OKABE_ITO['green'], alpha=0.2,
                     label='可行域（α=0）')

    # 顶层：关键点
    # α=0候选区域
    ax.plot([D_HAT, D_HAT], [B_MIN_ALPHA0, B_MAX_ALPHA0],
           color=OKABE_ITO['blue'], linewidth=5, label='α=0候选区域')

    # 零裕度定点
    ax.plot(A_OPT, B_OPT, '*', color=OKABE_ITO['orange'],
           markersize=25, markeredgecolor='black', markeredgewidth=1.5,
           label=f'零裕度定点\n({A_OPT:.0f}, {B_OPT:.0f})', zorder=10)

    # S₁位置
    ax.plot(0, 0, 'o', color=OKABE_ITO['vermillion'], markersize=15,
           markeredgecolor='black', markeredgewidth=1, label='S₁', zorder=10)

    # 采样网格（展示搜索密度）
    sample_a = np.arange(D_HAT - 300, D_HAT + 300, 50)
    sample_b = np.arange(200, 900, 50)
    for a_val in sample_a:
        for b_val in sample_b:
            if B_MIN_ALPHA0 <= b_val <= B_MAX_ALPHA0:
                d2_check = np.sqrt((a_val - D_HAT)**2 + b_val**2)
                if d2_check <= R_WORST:
                    ax.plot(a_val, b_val, '.', color='gray',
                           markersize=3, alpha=0.3)

    ax.set_xlim(D_HAT - 400, D_HAT + 400)
    ax.set_ylim(50, 950)
    ax.legend(loc='upper left', fontsize=10, framealpha=0.95)
    ax.set_aspect('equal')

    plt.tight_layout()
    return fig


# ==================== 主函数 ====================
def generate_p0_figures(output_dir='./'):
    """生成P0核心三张创新图"""
    import os
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("Q2 创新可视化 v3.0 - P0核心三张")
    print("=" * 70)
    print()

    # 图1
    print("生成图1：Sankey流图（信息级联效应）...")
    fig1 = figure1_sankey_flow()
    fig1.savefig(os.path.join(output_dir, 'Fig1_Sankey流图_v3.0.png'),
                dpi=300, bbox_inches='tight')
    plt.close(fig1)
    print("✓ 图1完成")
    print()

    # 图2
    print("生成图2：热力图（可行域崩塌4帧）...")
    fig2 = figure2_heatmap_animation()
    fig2.savefig(os.path.join(output_dir, 'Fig2_热力图4帧_v3.0.png'),
                dpi=300, bbox_inches='tight')
    plt.close(fig2)
    print("✓ 图2完成")
    print()

    # 图3
    print("生成图3：等高线叠加（E景观）...")
    fig3 = figure3_contour_overlay()
    fig3.savefig(os.path.join(output_dir, 'Fig3_E景观叠加_v3.0.png'),
                dpi=300, bbox_inches='tight')
    plt.close(fig3)
    print("✓ 图3完成")
    print()

    print("=" * 70)
    print("✅ P0核心三张创新图生成完成！")
    print("=" * 70)
    print()
    print("创新要点：")
    print("  1. ✓ Sankey流图展示信息级联")
    print("  2. ✓ 热力图4帧展示可行域崩塌")
    print("  3. ✓ 多层叠加（等高线+约束+关键点）")
    print("  4. ✓ 地形图隐喻（E景观）")
    print("  5. ✓ 视觉冲击力强")
    print()


if __name__ == '__main__':
    import sys
    import io

    # UTF-8输出
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    output_directory = 'E:/CUMCM2026/WorkArea_数学国赛/Q2_问题二/图_v3.0_创新/'
    generate_p0_figures(output_directory)
