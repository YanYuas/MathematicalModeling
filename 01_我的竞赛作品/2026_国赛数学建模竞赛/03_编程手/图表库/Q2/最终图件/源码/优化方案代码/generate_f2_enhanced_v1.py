'''F2 优化方案A：渐变填充+圆角矩形'''
from pathlib import Path
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import csv

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent.parent / '图集_v1_enhanced'
OUT.mkdir(exist_ok=True)
CSV = ROOT.parent.parent / '数据' / 'r1_r2_boundary_contract.csv'

NAVY, TEAL, OCHRE, GRAY, INK = '#233B72', '#147B7E', '#B26028', '#909AA3', '#20252B'

mpl.rcParams.update({
    'font.family': ['Microsoft YaHei', 'SimHei', 'sans-serif'],
    'axes.unicode_minus': False,
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
    'font.size': 9,
    'savefig.dpi': 300
})

with CSV.open(encoding='utf-8', newline='') as f:
    rows = list(csv.DictReader(f))
lo = np.array([float(r['b_angle_boundary_m']) for r in rows])
hi = np.array([float(r['b_distance_boundary_m']) for r in rows])

nominal_lo, nominal_hi = lo[2000], hi[2000]
rlo, rhi = lo.max(), hi.min()
gap = rlo - rhi

fig, ax = plt.subplots(figsize=(7.5, 3.0), facecolor='white')
fig.subplots_adjust(left=.14, right=.96, bottom=.22, top=.90)

ax.set(xlim=(618, 672), ylim=(-.3, 2.7), xlabel='横向偏移 b（m）')
ax.set_yticks([])
ax.set_xticks(np.arange(620, 671, 10))
ax.grid(axis='x', color='#E1E5E8', lw=.7, alpha=0.6)
ax.spines[['top', 'right', 'left']].set_visible(False)

# 圆角矩形（名义带）
nominal_rect = FancyBboxPatch(
    (nominal_lo, 1.70), nominal_hi - nominal_lo, 0.32,
    boxstyle='round,pad=0.01,rounding_size=0.12',
    facecolor=GRAY, edgecolor='#68727A', linewidth=1.2, alpha=0.85
)
ax.add_patch(nominal_rect)

# 渐变鲁棒边界
n_seg = 30
for i, b in enumerate(np.linspace(620, rhi, n_seg)[:-1]):
    alpha_val = 0.3 + 0.7 * (i / n_seg)
    ax.hlines(0.72, b, np.linspace(620, rhi, n_seg)[i+1], color=TEAL, lw=5, alpha=alpha_val)

for ext in ['png', 'svg', 'pdf']:
    fig.savefig(OUT/f'F2_enhanced.{ext}', bbox_inches='tight', facecolor='white', dpi=600 if ext=='png' else None)
print('✅ F2优化版已生成')
plt.close()
