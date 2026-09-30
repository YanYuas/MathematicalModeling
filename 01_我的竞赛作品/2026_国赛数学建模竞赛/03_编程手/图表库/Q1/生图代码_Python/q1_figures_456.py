#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
⚠️⚠️ 数据完整性警示 —— 本脚本产出的 Fig4 不可用于论文 ⚠️⚠️
=============================================================================
本脚本 main 块（约第 297-304 行）用 np.random.beta / np.random.uniform
**直接编造 γ 分布**，注释亦自承"生成测试数据 (实际应该从参数扫描结果读取)"。
该图不是实验数据，进入论文即构成伪造实验。

【请改用以下之一】
  1) q1_figures_3d_expert.py  --- 合法蒙特卡洛（随机只用于抽样配置，
     结果走真实几何管线）。它产出 figs/fig4_3d.png、fig5_3d.png、fig6_3d.png。
  2) 让本脚本改读 q1_scan_results.json（由 q1_scan.py 产出的真实扫描数据）。

【背景】见：
  - 03_编程手/Q1/实验结果/Q1_参数扫描报告.md §8「数据完整性警示」
  - 00_任务总控/权威数字表.md §七「已废弃数据（留痕）」

此外 main 块用 plt.show() 而非 savefig，无文件落盘。
=============================================================================

Q1 Fig4-6 期刊级图表生成
基于DeepSeek-V4-Pro + Claude Opus 5多AI协作方案

Fig4: γ分布 Raincloud plot + Jung窄带
Fig5: φ-D关系 信息图融合
Fig6: 参数空间 2D热力图+等高线

配色方案: Ink & Ochre (与fig1-3一致)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, Wedge, Rectangle, ConnectionPatch
from matplotlib import gridspec
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
from scipy.stats import gaussian_kde
from scipy import stats
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))
from q1_main import *

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
LW = {
    'main': 2.2,      # 主要元素
    'theory': 1.4,    # 理论界/参考线
    'aux': 0.7,       # 辅助线
}

# matplotlib中文字体配置
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42


# ═══════════════════════════════════════════════════════════
# Fig4: γ分布 Raincloud plot
# DeepSeek推荐: 半小提琴+抖动散点+箱线图+Jung窄带
# ═══════════════════════════════════════════════════════════
def fig4_gamma_raincloud(gamma_values, save_path='题一/实验结果/figs/fig4_gamma_raincloud'):
    """
    生成γ分布的Raincloud plot

    参数:
        gamma_values: γ值数组 (R_MEC / R_lower)
        save_path: 保存路径(不含扩展名)

    设计要点(DeepSeek):
        1. 有界KDE: 反射边界,严格限制[1.0, 2/√3]
        2. Jung窄带: axvspan标注[1.0, 1.1547]
        3. 双箭头标注"夹逼厚度≈0.1547"
        4. 配色: 墨色点+赭石密度+浅灰背景
        5. Inset显示ECDF
    """
    # Jung定理边界
    JUNG_LOWER = 1.0
    JUNG_UPPER = 2.0 / np.sqrt(3)  # ≈1.1547
    JUNG_WIDTH = JUNG_UPPER - JUNG_LOWER

    # 创建画布
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    ax.set_facecolor(PALETTE_A['paper'])
    fig.patch.set_facecolor(PALETTE_A['paper'])

    # 1. Jung理论窄带背景
    ax.axvspan(JUNG_LOWER, JUNG_UPPER,
               alpha=0.12,
               facecolor=PALETTE_A['field'],
               zorder=0)

    # 2. 边界虚线
    ax.axvline(JUNG_LOWER,
               linestyle='--',
               linewidth=LW['theory'],
               color=PALETTE_A['slate'],
               alpha=0.6,
               label=f'Jung lower bound γ={JUNG_LOWER:.0f}')
    ax.axvline(JUNG_UPPER,
               linestyle='--',
               linewidth=LW['theory'],
               color=PALETTE_A['rust'],
               alpha=0.6,
               label=f'Jung upper bound γ={JUNG_UPPER:.4f}')

    # 3. 有界KDE (反射边界)
    # 使用反射法处理边界: 在边界外添加镜像数据
    mirror_lower = 2 * JUNG_LOWER - gamma_values[gamma_values < JUNG_LOWER + 0.05]
    mirror_upper = 2 * JUNG_UPPER - gamma_values[gamma_values > JUNG_UPPER - 0.05]
    reflected_data = np.concatenate([mirror_lower, gamma_values, mirror_upper])

    kde = gaussian_kde(reflected_data, bw_method='scott')
    x_range = np.linspace(JUNG_LOWER - 0.02, JUNG_UPPER + 0.02, 500)
    density = kde(x_range)

    # 截断到理论边界内
    mask = (x_range >= JUNG_LOWER) & (x_range <= JUNG_UPPER)
    x_plot = x_range[mask]
    density_plot = density[mask]

    # 绘制半小提琴(上半部分)
    y_baseline = 0
    ax.fill_between(x_plot, y_baseline, density_plot,
                     alpha=0.4,
                     facecolor=PALETTE_A['ochre'],
                     edgecolor=PALETTE_A['ochre'],
                     linewidth=LW['main'],
                     label='Kernel density (reflected boundary)')

    # 4. 抖动散点(下半部分)
    np.random.seed(42)
    jitter_y = -0.5 + np.random.normal(0, 0.05, size=len(gamma_values))
    ax.scatter(gamma_values, jitter_y,
               s=20,
               alpha=0.6,
               c=PALETTE_A['ink'],
               edgecolors='white',
               linewidths=0.5,
               zorder=5,
               label=f'Samples (n={len(gamma_values)})')

    # 5. 箱线图(中部)
    bp = ax.boxplot([gamma_values],
                     vert=False,
                     positions=[-1.2],
                     widths=0.3,
                     patch_artist=True,
                     boxprops=dict(facecolor=PALETTE_A['geometry'], alpha=0.6, linewidth=LW['aux']),
                     whiskerprops=dict(color=PALETTE_A['slate'], linewidth=LW['aux']),
                     capprops=dict(color=PALETTE_A['slate'], linewidth=LW['aux']),
                     medianprops=dict(color=PALETTE_A['rust'], linewidth=LW['main']),
                     flierprops=dict(marker='o', markerfacecolor=PALETTE_A['rust'],
                                    markersize=4, alpha=0.5))

    # 6. 双箭头标注"夹逼厚度"
    arrow_y = max(density_plot) * 1.15
    ax.annotate('',
                xy=(JUNG_UPPER, arrow_y),
                xytext=(JUNG_LOWER, arrow_y),
                arrowprops=dict(arrowstyle='<->',
                               color=PALETTE_A['ink'],
                               linewidth=LW['main'],
                               shrinkA=0, shrinkB=0))
    ax.text((JUNG_LOWER + JUNG_UPPER) / 2, arrow_y + 0.1,
            f'Jung sandwich width ≈ {JUNG_WIDTH:.4f}',
            ha='center', va='bottom',
            fontsize=10,
            color=PALETTE_A['ink'],
            bbox=dict(boxstyle='round,pad=0.3',
                     facecolor=PALETTE_A['paper'],
                     edgecolor=PALETTE_A['slate'],
                     alpha=0.9))

    # 7. Inset: ECDF (累积分布函数)
    axins = inset_axes(ax, width="35%", height="30%",
                       loc='upper left',
                       bbox_to_anchor=(0.62, 0.4, 1, 1),
                       bbox_transform=ax.transAxes)
    axins.set_facecolor(PALETTE_A['paper'])

    # 计算ECDF
    sorted_gamma = np.sort(gamma_values)
    ecdf = np.arange(1, len(sorted_gamma) + 1) / len(sorted_gamma)

    axins.step(sorted_gamma, ecdf,
               where='post',
               color=PALETTE_A['ochre'],
               linewidth=LW['main'])
    axins.axvline(JUNG_LOWER, linestyle=':', linewidth=LW['aux'], color=PALETTE_A['slate'], alpha=0.5)
    axins.axvline(JUNG_UPPER, linestyle=':', linewidth=LW['aux'], color=PALETTE_A['rust'], alpha=0.5)
    axins.axhline(0.5, linestyle=':', linewidth=LW['aux'], color=PALETTE_A['slate'], alpha=0.3)

    axins.set_xlabel('γ', fontsize=8, color=PALETTE_A['ink'])
    axins.set_ylabel('ECDF', fontsize=8, color=PALETTE_A['ink'])
    axins.set_xlim(JUNG_LOWER - 0.01, JUNG_UPPER + 0.01)
    axins.set_ylim(-0.05, 1.05)
    axins.tick_params(labelsize=7, colors=PALETTE_A['slate'])
    axins.spines['top'].set_visible(False)
    axins.spines['right'].set_visible(False)
    axins.grid(False)

    # 8. 主图设置
    ax.set_xlabel('γ = R_MEC / R_lower', fontsize=12, color=PALETTE_A['ink'])
    ax.set_ylabel('Probability Density / Scatter', fontsize=12, color=PALETTE_A['ink'])
    ax.set_xlim(0.98, 1.18)
    ax.set_ylim(-2.0, arrow_y + 0.3)
    ax.tick_params(labelsize=10, colors=PALETTE_A['slate'])
    ax.legend(loc='upper right', fontsize=9, framealpha=0.95,
             edgecolor=PALETTE_A['slate'], facecolor=PALETTE_A['paper'])

    # 去掉上/右边框
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(PALETTE_A['slate'])
    ax.spines['bottom'].set_color(PALETTE_A['slate'])
    ax.grid(False)

    # 统计信息文本框
    stats_text = f'n = {len(gamma_values)}\n'
    stats_text += f'mean = {np.mean(gamma_values):.4f}\n'
    stats_text += f'median = {np.median(gamma_values):.4f}\n'
    stats_text += f'std = {np.std(gamma_values):.4f}'

    ax.text(0.02, 0.98, stats_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.5',
                     facecolor=PALETTE_A['paper'],
                     edgecolor=PALETTE_A['slate'],
                     alpha=0.9))

    plt.tight_layout()

    # 保存
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(f'{save_path}.png', dpi=600, bbox_inches='tight', facecolor=PALETTE_A['paper'])
    plt.savefig(f'{save_path}.svg', bbox_inches='tight', facecolor=PALETTE_A['paper'])
    print(f'✅ Fig4已保存: {save_path}.png + .svg')

    return fig, ax


# ═══════════════════════════════════════════════════════════
# Fig5: φ-D关系验证 (信息图融合)
# ═══════════════════════════════════════════════════════════
def fig5_phi_d_relation(phi_values, D_values, save_path='题一/实验结果/figs/fig5_phi_d_relation'):
    """
    生成φ-D关系图 (信息图融合)

    参数:
        phi_values: 检测误差φ数组 (度)
        D_values: 对应的区域直径D数组 (米)
        save_path: 保存路径(不含扩展名)

    设计要点(DeepSeek):
        1. 散点+误差棒显示实验数据
        2. 叠加理论曲线(虚线)
        3. 高亮关键点D=39.598m
        4. 注释φ-D非线性关系
    """
    # TODO: 需要参数扫描数据
    print('⚠️ Fig5需要参数扫描数据，待实现')
    pass


# ═══════════════════════════════════════════════════════════
# Fig6: 参数空间分类 (2D热力图+等高线)
# ═══════════════════════════════════════════════════════════
def fig6_param_space_heatmap(save_path='题一/实验结果/figs/fig6_param_space'):
    """
    生成(θ₁, θ₂)参数空间热力图

    设计要点(DeepSeek):
        1. 2D热力图: 可行区(奶油→赭石)，不可行区(灰+斜线)
        2. 等高线: γ=1.05, 1.10性能分级
        3. 边界: 粗暗线+白色描边
        4. Inset: 扇形剖面显示边界跃变
    """
    # TODO: 需要网格计算
    print('⚠️ Fig6需要网格计算，待实现')
    pass


# ═══════════════════════════════════════════════════════════
# 主函数 - 生成所有图表
# ═══════════════════════════════════════════════════════════
if __name__ == '__main__':
    print('='*60)
    print('Q1 Fig4-6 期刊级图表生成')
    print('基于DeepSeek + Claude多AI协作方案')
    print('='*60)

    # ===== Fig4: γ分布测试 =====
    print('\n【Fig4】生成γ分布Raincloud plot...')

    # ================================================================
    # ⚠️ 已停用：以下为用 np.random 编造的**合成 γ 分布**，不是实验数据。
    #    为防止误用，本脚本在此硬退出。请改用：
    #      - q1_figures_3d_expert.py（合法蒙特卡洛，产出 figs/fig4_3d.png）
    #      - 或让本脚本改读 q1_scan_results.json
    #    详见 Q1_参数扫描报告.md §8 与 权威数字表 §七。
    # ================================================================
    import sys as _sys
    _sys.exit("STOPPED: this script builds Fig4 from FABRICATED random data. "
              "Use q1_figures_3d_expert.py (legitimate Monte-Carlo) or read "
              "q1_scan_results.json instead. See Q1_参数扫描报告.md section 8.")

    # --- 以下原逻辑保留供参考，不会被执行 ---
    # 生成测试数据 (实际应该从参数扫描结果读取)
    np.random.seed(42)
    # 模拟γ分布: 大部分集中在1.0附近,少量接近上界
    gamma_test = np.concatenate([
        np.random.beta(50, 5, size=800) * 0.1547 + 1.0,  # 主要分布
        np.random.uniform(1.0, 1.1547, size=200)          # 均匀散布
    ])
    gamma_test = np.clip(gamma_test, 1.0, 1.1547)  # 确保在理论边界内

    fig4, ax4 = fig4_gamma_raincloud(gamma_test)
    plt.show()

    print('\n【Fig5】φ-D关系图...')
    print('⚠️ 需要参数扫描数据，跳过')

    print('\n【Fig6】参数空间热力图...')
    print('⚠️ 需要网格计算，跳过')

    print('\n' + '='*60)
    print('✅ Fig4已完成！Fig5-6需要额外数据')
    print('='*60)
