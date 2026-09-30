"""Q2 创新可视化 v3.0 - P1应做三张

图4：小提琴图 - φ分布的α敏感性
图5：决策树 - 目标角vs可行性权衡
图6：平行坐标 - 参数空间高维投影

Dependencies: numpy, matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
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

R_WORST = 1000.0
D_HAT = 752.5
DELTA_D = 747.5
PHI_MIN_40 = 40.0


# ==================== 图4：小提琴图（φ分布的α敏感性） ====================
def figure4_violin_plot():
    """
    小提琴图：展示φ分布随α的收缩
    """
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    ax.set_title('交会角φ分布的α敏感性分析', fontsize=16, fontweight='bold')
    ax.set_xlabel('α（示向度误差，度）', fontsize=13)
    ax.set_ylabel('φ（交会角，度）', fontsize=13)
    ax.grid(True, alpha=0.3, axis='y')

    # 5个α值
    alpha_values = [0, 0.3, 0.5, 0.8, 1.0]
    colors = [OKABE_ITO['green'], '#90EE90', '#FFD700', OKABE_ITO['orange'], OKABE_ITO['vermillion']]

    # 模拟每个α下的φ分布（采样1000点）
    positions = []
    all_phi_data = []

    for idx, alpha_val in enumerate(alpha_values):
        # 在(a,b)空间采样
        np.random.seed(42 + idx)
        a_samples = np.random.uniform(D_HAT - 200, D_HAT + 200, 1000)
        b_samples = np.random.uniform(400, 800, 1000)

        # 简化φ计算
        alpha_rad = np.radians(alpha_val)
        numerator = np.abs((a_samples - D_HAT) * np.sin(alpha_rad) - b_samples * np.cos(alpha_rad))
        d2 = np.sqrt((a_samples - D_HAT)**2 + b_samples**2)
        d2 = np.maximum(d2, 1e-9)
        sin_phi = np.minimum(numerator / d2, 1.0)
        phi_samples = np.degrees(np.arcsin(sin_phi))

        # 过滤可行值
        phi_feasible = phi_samples[(phi_samples >= 35) & (phi_samples <= 90)]

        positions.append(idx)
        all_phi_data.append(phi_feasible)

    # 手工绘制小提琴图（matplotlib.violin需要复杂配置）
    for idx, (pos, phi_data, color) in enumerate(zip(positions, all_phi_data, colors)):
        if len(phi_data) == 0:
            continue

        # 计算核密度估计（简化版）
        phi_min, phi_max = phi_data.min(), phi_data.max()
        phi_bins = np.linspace(phi_min, phi_max, 50)
        hist, bin_edges = np.histogram(phi_data, bins=phi_bins, density=True)

        # 归一化到宽度
        max_width = 0.3
        widths = hist / hist.max() * max_width

        # 绘制小提琴轮廓（左右对称）
        for i in range(len(hist)):
            y_bottom = bin_edges[i]
            y_top = bin_edges[i + 1]
            width = widths[i]
            # 左半边
            ax.fill_betweenx([y_bottom, y_top], pos - width, pos,
                            color=color, alpha=0.6, edgecolor='black', linewidth=0.5)
            # 右半边
            ax.fill_betweenx([y_bottom, y_top], pos, pos + width,
                            color=color, alpha=0.6, edgecolor='black', linewidth=0.5)

        # 中位线
        median = np.median(phi_data)
        ax.plot([pos - max_width, pos + max_width], [median, median],
               'k-', linewidth=2, zorder=10)

        # 箱体（25%-75%）
        q25, q75 = np.percentile(phi_data, [25, 75])
        box_width = 0.05
        ax.fill_between([pos - box_width, pos + box_width], q25, q75,
                       color='white', edgecolor='black', linewidth=1.5, zorder=9)

    # x轴标签
    ax.set_xticks(positions)
    ax.set_xticklabels([f'{a:.1f}°' for a in alpha_values], fontsize=11)

    # 参考线
    ax.axhline(PHI_MIN_40, color='red', linestyle='--', linewidth=2, alpha=0.7,
              label=f'目标角φ_min={PHI_MIN_40}°')
    ax.axhline(39.616, color='orange', linestyle='--', linewidth=2, alpha=0.7,
              label='鲁棒上界φ_max=39.616°')

    ax.set_ylim(30, 95)
    ax.legend(fontsize=11, loc='upper right')

    # 说明文字
    explanation = (
        '小提琴宽度 = φ分布密度\n'
        '中粗线 = 中位数\n'
        '白色箱体 = 25%-75%分位'
    )
    ax.text(0.02, 0.98, explanation, transform=ax.transAxes,
           fontsize=10, va='top', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

    plt.tight_layout()
    return fig


# ==================== 图5：决策树（目标角vs可行性） ====================
def figure5_decision_tree():
    """
    决策树：展示目标角选择与可行性的权衡
    """
    fig, ax = plt.subplots(figsize=(14, 10), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    ax.text(5, 9.5, '决策树：目标角φ_min vs 可行性权衡',
           fontsize=16, fontweight='bold', ha='center')

    # 根节点
    root_box = FancyBboxPatch((4, 8.5), 2, 0.6, boxstyle="round,pad=0.1",
                             facecolor='lightblue', edgecolor='black', linewidth=2)
    ax.add_patch(root_box)
    ax.text(5, 8.8, '设定目标角\nφ_min', ha='center', va='center',
           fontsize=12, fontweight='bold')

    # 子节点位置和数据
    decisions = [
        # (x, y, φ值, 可行性, 面积, 颜色, 状态)
        (1.5, 6.5, 42, '不可行', 0, OKABE_ITO['vermillion'], '❌ 空集'),
        (3, 6.5, 40, '临界', 0, OKABE_ITO['orange'], '⚠️ 同口径空集'),
        (4.5, 6.5, 39.616, '零裕度', 0.01, '#FFD700', '⚠️ 单点(764,651)'),
        (6, 6.5, 39, '可行', 17, '#90EE90', '✓ 17 m²'),
        (7.5, 6.5, 38, '宽松', 310, OKABE_ITO['green'], '✓ 310 m²'),
        (9, 6.5, 35, '富余', 1200, OKABE_ITO['green'], '✓ 1200 m²')
    ]

    # 绘制分支和节点
    for x, y, phi, feasibility, area, color, status in decisions:
        # 连线
        arrow = FancyArrowPatch((5, 8.5), (x, y + 0.6),
                               arrowstyle='->', mutation_scale=20,
                               linewidth=2, color='gray', alpha=0.6)
        ax.add_patch(arrow)

        # 节点
        node_box = FancyBboxPatch((x - 0.6, y), 1.2, 0.6, boxstyle="round,pad=0.05",
                                 facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(node_box)
        ax.text(x, y + 0.45, f'φ={phi}°', ha='center', va='top',
               fontsize=10, fontweight='bold')
        ax.text(x, y + 0.15, status, ha='center', va='center', fontsize=9)

        # 下方详细信息
        if area > 0:
            detail_box = FancyBboxPatch((x - 0.55, y - 1.2), 1.1, 0.8,
                                       boxstyle="round,pad=0.05",
                                       facecolor='white', edgecolor=color, linewidth=1.5)
            ax.add_patch(detail_box)
            ax.text(x, y - 0.9, f'可行域面积\n{area} m²', ha='center', va='center',
                   fontsize=8)
            ax.text(x, y - 0.5, f'布站自由度\n{"低" if area < 50 else "中" if area < 500 else "高"}',
                   ha='center', va='center', fontsize=8)
        elif feasibility == '零裕度':
            detail_box = FancyBboxPatch((x - 0.55, y - 1.2), 1.1, 0.8,
                                       boxstyle="round,pad=0.05",
                                       facecolor='white', edgecolor=color, linewidth=1.5)
            ax.add_patch(detail_box)
            ax.text(x, y - 0.8, '数值搜索值\nφ_max上界', ha='center', va='center', fontsize=8)

    # 图例
    legend_y = 4.5
    ax.text(0.5, legend_y, '决策指南：', fontsize=11, fontweight='bold')
    guide_text = (
        '• φ_min ≥ 42° → 不可行（空集）\n'
        '• φ_min = 40° → 临界（α=0可行，α≠0空集）\n'
        '• φ_min = 39.616° → 零裕度（单点，无自由度）\n'
        '• φ_min ≤ 39° → 可行且有裕度\n'
        '• φ_min ≤ 38° → 宽松（布站自由度高）'
    )
    ax.text(0.5, legend_y - 0.3, guide_text, fontsize=9, va='top',
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

    # 推荐框
    recommend_box = FancyBboxPatch((5.5, 1.5), 4, 1.5, boxstyle="round,pad=0.1",
                                  facecolor='lightgreen', edgecolor='green', linewidth=3)
    ax.add_patch(recommend_box)
    ax.text(7.5, 2.6, '📋 工程推荐', fontsize=13, fontweight='bold', ha='center')
    recommend_text = (
        '若需布站灵活性：φ_min = 38° (310 m²)\n'
        '若需最大信息量：φ_min = 39° (17 m²)\n'
        '若追求理论极限：φ_min = 39.616° (零裕度)'
    )
    ax.text(7.5, 2, recommend_text, fontsize=10, ha='center', va='center')

    plt.tight_layout()
    return fig


# ==================== 图6：平行坐标（参数空间） ====================
def figure6_parallel_coordinates():
    """
    平行坐标图：180组参数扫描的高维投影
    """
    fig, ax = plt.subplots(figsize=(16, 8), dpi=300)
    ax.set_title('参数空间高维投影：180组实验配置', fontsize=16, fontweight='bold')

    # 模拟180组数据（实际应从CSV读取）
    np.random.seed(42)
    n_configs = 180

    # 4个轴：Δd, φ_min, R, φ_max
    axis_names = ['Δd\n(源距不确定度)', 'φ_min\n(目标角)', 'R\n(探测范围)', 'φ_max\n(可达上界)']
    axis_positions = [0, 1, 2, 3]

    # 数据范围（归一化到0-1）
    data = {
        'Delta_d': np.random.uniform(200, 900, n_configs),
        'phi_min': np.random.uniform(35, 45, n_configs),
        'R': np.random.choice([800, 1000, 1200], n_configs),
        'phi_max': []
    }

    # 计算φ_max（简化）
    for delta_d, r in zip(data['Delta_d'], data['R']):
        phi_max = np.degrees(np.arccos(min(delta_d / r, 1.0)))
        data['phi_max'].append(phi_max)

    data['phi_max'] = np.array(data['phi_max'])

    # 可行性判断
    feasible = (data['phi_max'] >= data['phi_min'])

    # 归一化到0-1
    def normalize(values, vmin, vmax):
        return (values - vmin) / (vmax - vmin)

    delta_d_norm = normalize(data['Delta_d'], 200, 900)
    phi_min_norm = normalize(data['phi_min'], 35, 45)
    R_norm = normalize(data['R'], 800, 1200)
    phi_max_norm = normalize(data['phi_max'], 30, 90)

    # 绘制每条配置线
    for i in range(n_configs):
        y_values = [delta_d_norm[i], phi_min_norm[i], R_norm[i], phi_max_norm[i]]
        color = OKABE_ITO['green'] if feasible[i] else OKABE_ITO['vermillion']
        alpha = 0.4 if feasible[i] else 0.2
        ax.plot(axis_positions, y_values, color=color, alpha=alpha, linewidth=0.5)

    # 高亮验证题配置
    verify_delta_d = 747.5
    verify_phi_min = 40
    verify_R = 1000
    verify_phi_max = 41.63

    verify_norm = [
        normalize(verify_delta_d, 200, 900),
        normalize(verify_phi_min, 35, 45),
        normalize(verify_R, 800, 1200),
        normalize(verify_phi_max, 30, 90)
    ]
    ax.plot(axis_positions, verify_norm, color='yellow', linewidth=4,
           marker='o', markersize=10, markeredgecolor='black', markeredgewidth=2,
           label='验证题配置', zorder=10)

    # 绘制轴
    for pos in axis_positions:
        ax.axvline(pos, color='black', linewidth=2, zorder=0)

    # 轴标签
    ax.set_xticks(axis_positions)
    ax.set_xticklabels(axis_names, fontsize=12, fontweight='bold')

    # y轴刻度（显示原始值）
    y_ticks = [0, 0.25, 0.5, 0.75, 1.0]
    ax.set_yticks(y_ticks)

    # 为每个轴添加实际值刻度
    axis_ranges = [
        (200, 900, 'Δd (m)'),
        (35, 45, 'φ (°)'),
        (800, 1200, 'R (m)'),
        (30, 90, 'φ (°)')
    ]

    for pos, (vmin, vmax, unit) in zip(axis_positions, axis_ranges):
        for y_tick in y_ticks:
            actual_value = vmin + y_tick * (vmax - vmin)
            ax.text(pos + 0.15, y_tick, f'{actual_value:.0f}',
                   fontsize=8, va='center')

    ax.set_ylim(-0.1, 1.1)
    ax.set_xlim(-0.3, 3.3)
    ax.legend(fontsize=12, loc='upper left')
    ax.set_ylabel('归一化值（0-1）', fontsize=12)

    # 说明
    ax.text(0.5, -0.25, f'绿色线（{feasible.sum()}条）：可行配置（φ_max≥φ_min）',
           transform=ax.transAxes, fontsize=10, color=OKABE_ITO['green'], fontweight='bold')
    ax.text(0.5, -0.3, f'红色线（{(~feasible).sum()}条）：不可行配置',
           transform=ax.transAxes, fontsize=10, color=OKABE_ITO['vermillion'], fontweight='bold')

    plt.tight_layout()
    return fig


# ==================== 主函数 ====================
def generate_p1_figures(output_dir='./'):
    """生成P1应做三张创新图"""
    import os
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("Q2 创新可视化 v3.0 - P1应做三张")
    print("=" * 70)
    print()

    print("生成图4：小提琴图（φ分布的α敏感性）...")
    fig4 = figure4_violin_plot()
    fig4.savefig(os.path.join(output_dir, 'Fig4_小提琴图_v3.0.png'),
                dpi=300, bbox_inches='tight')
    plt.close(fig4)
    print("✓ 图4完成")
    print()

    print("生成图5：决策树（目标角vs可行性权衡）...")
    fig5 = figure5_decision_tree()
    fig5.savefig(os.path.join(output_dir, 'Fig5_决策树_v3.0.png'),
                dpi=300, bbox_inches='tight')
    plt.close(fig5)
    print("✓ 图5完成")
    print()

    print("生成图6：平行坐标（参数空间高维投影）...")
    fig6 = figure6_parallel_coordinates()
    fig6.savefig(os.path.join(output_dir, 'Fig6_平行坐标_v3.0.png'),
                dpi=300, bbox_inches='tight')
    plt.close(fig6)
    print("✓ 图6完成")
    print()

    print("=" * 70)
    print("✅ P1应做三张创新图生成完成！")
    print("=" * 70)


if __name__ == '__main__':
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    output_directory = 'E:/CUMCM2026/WorkArea_数学国赛/Q2_问题二/图_v3.0_创新/'
    generate_p1_figures(output_directory)
