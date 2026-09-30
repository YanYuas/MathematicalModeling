"""
论文流程图 v4 — GridSpec精确网格, 无手写坐标
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial"],
    "axes.unicode_minus": False,
    "svg.fonttype": "none", "pdf.fonttype": 42,
})

BLUE='#4a90d9'; ORANGE='#e8a838'; GREEN='#5a9e6f'
GOLD='#D4A017'; GRAY='#999'; DARK='#1a1a2e'
BLUE_L='#ebf3fb'; ORANGE_L='#fef7ec'; GREEN_L='#edf7f0'

OUT = r'c:\Users\29845\Desktop\电工杯\问题二最终结果\q2_flowchart'

# ==================== HELPERS ====================
def rbox(ax, text, fc='white', fs=7, edge=None, pad=4, x=0.5, y=0.5, color='#222'):
    """Add rounded box text at (x,y) in axes coords"""
    bbox_dict = dict(boxstyle=f'round,pad={pad}', facecolor=fc,
                     edgecolor=edge or '#ddd', linewidth=0.5 if edge else 0)
    return ax.text(x, y, text, transform=ax.transAxes,
                   ha='center', va='center', fontsize=fs,
                   fontweight='normal', color=color,
                   bbox=bbox_dict, linespacing=1.2)

def title_box(ax, text, color, fs=7):
    bbox = dict(boxstyle='round,pad=3', facecolor=color, edgecolor='none')
    ax.text(0.5, 0.5, text, transform=ax.transAxes,
            ha='center', va='center', fontsize=fs,
            fontweight='bold', color='white', bbox=bbox, linespacing=1.15)

def plain_text(ax, text, fs=7, color='#333', bold=False, y=0.5):
    ax.text(0.5, y, text, transform=ax.transAxes,
            ha='center', va='center', fontsize=fs,
            color=color, fontweight='bold' if bold else 'normal', linespacing=1.1)

# ==================== FIGURE: 4-row grid ====================
# Row 0: title
# Row 1: data + problem
# Row 2: three columns (tall)
# Row 3: merge + table
fig = plt.figure(figsize=(330/25.4, 270/25.4))
gs = GridSpec(4, 3, figure=fig,
              height_ratios=[0.5, 1.2, 5, 3.5],
              hspace=0.08, wspace=0.06,
              left=0.04, right=0.96, top=0.98, bottom=0.02)

# ====== ROW 0: TITLE ======
ax_title = fig.add_subplot(gs[0, :])
ax_title.axis('off')
plain_text(ax_title, '问题二: 服务站选址与规模优化 — 算法流程图', fs=12, bold=True, color=DARK)

# ====== ROW 1: DATA + PROBLEM ======
ax_data = fig.add_subplot(gs[1, :])
ax_data.axis('off')
ax_data.set_xlim(0,1); ax_data.set_ylim(0,1)

# data bar
rbox(ax_data, '输入: 1.1预测 + 1.3消费约束日需求(8196次/日) + 距离矩阵 + 成本/满意度参数',
     fc='#f0f0f5', fs=7, y=0.8, color='#555')

# problem
bbox_p = dict(boxstyle='round,pad=5', facecolor=DARK, edgecolor='none')
ax_data.text(0.5, 0.35, 's_i∈{0,1,2,3} | 预算≤120万 | 半径≤1000m\nmax 覆盖率(至少一项服务/总人数) + max 满意度(0.2S1+0.3S2+0.5S3)',
             transform=ax_data.transAxes, ha='center', va='center',
             fontsize=7.5, color='white', bbox=bbox_p, linespacing=1.3)

# engine
bbox_e = dict(boxstyle='round,pad=2', facecolor=DARK)
ax_data.text(0.5, 0.08, '统一评估引擎: 连续S2+阻尼迭代→唯一均衡→(C,S)',
             transform=ax_data.transAxes, ha='center', va='center',
             fontsize=6, color='#ccc', bbox=bbox_e)

# ====== ROW 2: THREE COLUMNS ======
for col_idx, (col_title, col_color, col_bg, steps, output_text, extra) in enumerate([
    # COL A: NSGA-II
    ('方案A (主要)\nNSGA-II双目标Pareto GA', BLUE, BLUE_L,
     ['① 初始化种群(200)\n   整数编码 s_i∈{0,1,2,3}',
      '② 均衡求解→评估(C,S)',
      '③ 非支配排序+拥挤距离',
      '④ Pareto锦标赛选择\n   +交叉(pc=0.8)+变异(pm=0.15)',
      '⑤ 预算修复+精英保留(15)\n   循环150代 | 5次独立运行'],
     '→ 14个Pareto解\nC:40.9%~85.7%  S:90.0%~98.6%\n8/14命中枚举前沿',
     '耗时: ~68s'),
    # COL B: Layered GA
    ('方案B (次主要)\n分层先后优化GA', ORANGE, ORANGE_L,
     ['【第一层】最大化覆盖率 C\n→ GA(100个体×60代)\n→ C* = max C ≈ 85.7%',
      '【第二层】max(0.6C+0.4S)\n  C ≥ C*−0.01\n→ 热启动 + GA(60代)',
      '交叉变异+修复(同方案A)'],
     '→ 1个最优解\nCmax=85.6%  Smax=94.7%\nF=0.882(三方案最高)',
     '耗时: ~385s'),
    # COL C: Enumeration
    ('枚举 (辅助验证)\n遍历法', GREEN, GREEN_L,
     ['生成: ΣC(10,k)×3^k=235,011',
      '预算筛选→15,207可行解',
      '逐一评估(统一求解器)',
      '非支配排序→Pareto前沿',
      '验证: GA解∈前沿?'],
     '→ 19个Pareto解\nC:40.9%~85.7%  S:90.0%~98.6%\n全局最优保证',
     '耗时: ~89s'),
]):
    ax_col = fig.add_subplot(gs[2, col_idx])
    ax_col.axis('off')
    ax_col.set_xlim(0,1); ax_col.set_ylim(0,1)

    # Title
    title_box(ax_col, col_title, col_color, fs=6.5)

    # Steps - stacked vertically with proper spacing
    n = len(steps)
    y_start = 0.82
    y_step = 0.75 / n

    for si, step in enumerate(steps):
        y = y_start - si * y_step
        is_key = '【' in step
        bg = '#fff3d0' if (is_key and col_idx==1) else 'white'
        edge_c = col_color if is_key else '#ddd'
        rbox(ax_col, step, fc=bg, fs=5.2, edge=edge_c, pad=3.5, y=y, color='#333')

    # Output box
    y_out = y_start - n * y_step - 0.02
    bbox_out = dict(boxstyle='round,pad=4', facecolor=col_color)
    ax_col.text(0.5, y_out, output_text, transform=ax_col.transAxes,
                ha='center', va='center', fontsize=5.2, color='white',
                fontweight='bold', bbox=bbox_out, linespacing=1.15)

    # Time
    bbox_t = dict(boxstyle='round,pad=1', facecolor='white', edgecolor='#ddd')
    ax_col.text(0.5, 0.03, extra, transform=ax_col.transAxes, ha='center',
                va='center', fontsize=5.5, color='#888', bbox=bbox_t)

# ====== ROW 3: MERGE + TABLE ======
ax_bot = fig.add_subplot(gs[3, :])
ax_bot.axis('off')
ax_bot.set_xlim(0,1); ax_bot.set_ylim(0,1)

# Merge arrows symbol
ax_bot.annotate('▼', xy=(0.5, 0.97), ha='center', va='center',
                fontsize=14, color=GOLD, fontweight='bold')

# Table as text with boxes
table_text = (
    '        指标              │     方案A (主要) NSGA-II     │     方案B (次主要) 分层GA    │     枚举 (辅助验证)\n'
    '    ──────────────────────┼───────────────────────────┼───────────────────────────┼──────────────────────────\n'
    '    最高覆盖率            │     85.7%                  │     85.6%                  │     85.7% (全局最优)\n'
    '    最高满意度            │     0.986                  │     0.947                  │     0.986 (全局最优)\n'
    '    0.6C+0.4S            │     0.874                  │     0.882 (最高)           │     0.878\n'
    '    Pareto解数            │     14个                   │     1个                    │     19个 (完整前沿)\n'
    '    耗时                  │     ~68s                   │     ~385s                  │     ~89s (全局保证)\n'
)
bbox_tbl = dict(boxstyle='round,pad=6', facecolor='white', edgecolor='#c0c0d0', linewidth=1)
ax_bot.text(0.5, 0.72, table_text, transform=ax_bot.transAxes,
            ha='center', va='center', fontsize=6.5,
            color='#333', bbox=bbox_tbl, linespacing=1.4)

# Note
plain_text(ax_bot, '注: 方案A TOPSIS推荐 D(中)E(小)F(小)G(小)J(中) 5站118万  C=84.9%  S=0.947',
           fs=5.5, color='#888', y=0.08)

# ==================== SAVE ====================
for fmt, dpi in [('svg',None),('pdf',None),('png',300)]:
    kw = {} if dpi is None else {'dpi': dpi}
    fig.savefig(f'{OUT}.{fmt}', bbox_inches='tight', **kw)
print('v4 saved')
plt.close(fig)
