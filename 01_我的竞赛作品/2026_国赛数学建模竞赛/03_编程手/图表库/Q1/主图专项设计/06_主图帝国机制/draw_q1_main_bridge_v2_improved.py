# -*- coding: utf-8 -*-
"""Q1主图：覆盖判决桥（改进版v2）
改进点：
1. 统一配色规范（math-modeling-figures）
2. 修复dpi配置
3. 添加图表元数据
4. 优化字号层级
5. 添加数学验证断言
"""
from pathlib import Path
import sys, math, json
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Arc, FancyArrowPatch, FancyBboxPatch
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import q1_geometry_core as q

OUT = ROOT / '07_最终主图'
OUT.mkdir(exist_ok=True)

# ========== 配色规范（统一为math-modeling-figures标准） ==========
BLUE = '#1565C0'    # 主数据、模型、实际值
RED = '#E53935'     # 反例、警示、不覆盖
GREEN = '#2E7D32'   # MEC、覆盖、正向指标
GREY = '#6B7B83'    # 辅助信息、网格
INK = '#202020'     # 主文字

# ========== 字号层级（academic-figure规范） ==========
TITLE_SIZE = 9.2
SUBTITLE_SIZE = 7.8
BODY_SIZE = 7.2
CAPTION_SIZE = 6.3
ANNOTATION_SIZE = 5.9

# ========== 中文字体配置（完整版） ==========
mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
    'font.size': BODY_SIZE,
    'axes.unicode_minus': False,  # 负号显示
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
    'mathtext.fontset': 'stix',
    'figure.dpi': 150,            # 屏幕显示
    'savefig.dpi': 300            # 论文保存（关键！）
})

def off(ax):
    ax.set_axis_off()

def ax(fig, b):
    return fig.add_axes(b)

def txt(ax, x, y, s, **kw):
    return ax.text(x, y, s, **kw)

def main():
    # ========== 数据加载与验证 ==========
    b = q.baseline()
    e = q.equilateral(1)
    V = np.array(b['V'])
    P, Q = np.array(b['ends'])
    C = np.array(b['C'])
    D, R = b['D'], b['R_MEC']

    # 数学验证断言（确保数据正确性）
    assert len(V) == 4, f"基准算例应有4个顶点，实际{len(V)}个"
    assert abs(D - 39.598327) < 1e-5, f"D应为39.598m，实际{D:.6f}m"
    assert abs(R - D/2) < 1e-7, f"基准算例应满足γ=1，实际R={R:.6f}, D/2={D/2:.6f}"
    assert not e['covers'], "等边三角形反例：直径圆不应覆盖"
    assert abs(e['gamma'] - 2/math.sqrt(3)) < 1e-6, f"等边三角形γ应为2/√3≈1.1547，实际{e['gamma']:.6f}"

    print(f"✅ 数学验证通过：D={D:.4f}m, R={R:.4f}m, γ={R/(D/2):.6f}")
    print(f"✅ 等边反例验证：γ={e['gamma']:.6f}, 覆盖={e['covers']}")

    # ========== 画布布局 ==========
    fig = plt.figure(figsize=(6.2992, 5.3150), facecolor='white')

    head = ax(fig, [.03, .945, .94, .042])     # 顶部：核心结论
    chain = ax(fig, [.04, .695, .92, .20])     # 概念链
    cex = ax(fig, [.03, .30, .535, .375])      # 左：等边反例（主视觉）
    crit = ax(fig, [.605, .30, .365, .375])    # 右：Thales判据
    mec = ax(fig, [.04, .135, .92, .14])       # Jung区间
    pocket = ax(fig, [.62, .02, .34, .09])     # 特例验证框

    for a in [head, chain, mec, pocket]:
        off(a)

    # ========== 1. 核心结论（顶部标题） ==========
    txt(head, .5, .5,
        '以 D 为直径的圆不保证覆盖定位区域 L；覆盖当且仅当 γ = 1',
        ha='center', va='center', fontsize=TITLE_SIZE,
        fontweight='bold', color=INK)

    # ========== 2. 概念链（输入→构造→候选圆） ==========
    chain.set(xlim=(0, 100), ylim=(0, 20))
    off(chain)

    txt(chain, 2, 18,
        '输入构造：带误差的示向度 → 有界凸定位区域 → 候选直径圆',
        fontsize=BODY_SIZE, fontweight='bold', color=INK)

    # 角域示意
    for origin, ang, col, label in [((8, 5), 25, GREY, 'W₁'), ((15, 5), 70, GREY, 'W₂')]:
        o = np.array(origin)
        u1 = np.array([math.cos(math.radians(ang-10)), math.sin(math.radians(ang-10))])
        u2 = np.array([math.cos(math.radians(ang+10)), math.sin(math.radians(ang+10))])
        chain.add_patch(Polygon([o, o+8*u1, o+8*u2], fc=GREY, ec='none', alpha=.12))
        chain.plot([o[0], o[0]+8*u1[0]], [o[1], o[1]+8*u1[1]], color=GREY, lw=.8)
        chain.plot([o[0], o[0]+8*u2[0]], [o[1], o[1]+8*u2[1]], color=GREY, lw=.8)
        txt(chain, o[0], o[1]-2, label, ha='center', color=GREY, fontsize=CAPTION_SIZE)

    # 交集箭头
    chain.add_patch(FancyArrowPatch((25, 10), (34, 10),
                                   arrowstyle='-|>', mutation_scale=9,
                                   lw=.8, color=GREY))
    txt(chain, 29.5, 12, '∩', ha='center', fontsize=12)

    # 定位区域L
    lv = np.array([[38, 7], [43, 4], [48, 7], [43, 11]])
    chain.add_patch(Polygon(lv, fc=BLUE, alpha=.15, ec=BLUE, lw=1.1))
    txt(chain, 43, 13, 'L（凸）', ha='center', color=BLUE, fontsize=BODY_SIZE)

    # 直径
    chain.add_patch(FancyArrowPatch((51, 10), (61, 10),
                                   arrowstyle='-|>', mutation_scale=9,
                                   lw=.8, color=GREY))
    chain.plot([65, 65], [5, 14], color=BLUE, lw=1.5)
    txt(chain, 65, 3, 'P,Q 给出 D', ha='center', color=BLUE, fontsize=BODY_SIZE)

    # 候选直径圆
    chain.add_patch(Circle((78, 10), 5, fill=False, ec=BLUE, lw=1, ls=(0, (2, 2))))
    chain.plot([73, 83], [10, 10], color=BLUE, lw=1)
    txt(chain, 78, 17, '候选直径圆', ha='center', color=BLUE, fontsize=BODY_SIZE)

    # 前提说明
    txt(chain, 2, .4,
        '前提：L 非空且有界；各站误差半角 ε 相同。无界时 D 无定义。',
        fontsize=CAPTION_SIZE, color=GREY)

    # ========== 3. 等边三角形反例（左侧主视觉，40%面积） ==========
    cex.set(xlim=(-.14, 1.14), ylim=(-.03, 1.15))
    cex.set_aspect('equal')
    cex.set_xticks([])
    cex.set_yticks([])
    cex.spines[:].set_visible(False)

    txt(cex, .5, 1.105,
        '存在性证否：等边三角形反例（n ≥ 3，归一化 D = 1）',
        ha='center', fontsize=SUBTITLE_SIZE, fontweight='bold', color=RED)

    # 等边三角形
    T = np.array(e['V'])
    ce = np.array([.5, math.sqrt(3)/6])  # MEC圆心

    cex.add_patch(Circle(ce, 1/math.sqrt(3), fill=False, ec=GREEN, lw=1.45))  # MEC圆
    cex.add_patch(Circle((.5, 0), .5, fill=False, ec=RED, lw=1.0, ls=(0, (1, 2))))  # 直径圆（失败）
    cex.add_patch(Polygon(T, fill=False, ec=RED, lw=1.8))  # 三角形
    cex.plot([0, 1], [0, 0], color=GREY, lw=1.15)  # 底边

    # 顶点标注
    for p, l, dx in zip(T, ['A', 'B', 'C'], [-.02, .02, 0]):
        cex.scatter(*p, s=28, c=RED, marker='^')
        txt(cex, p[0]+dx, p[1]+.045, l, ha='center', color=RED, fontsize=BODY_SIZE)

    # 60°角标注
    cex.add_patch(Arc((.5, math.sqrt(3)/2), .30, .22, angle=0,
                     theta1=220, theta2=320, ec=RED, lw=1.2))
    txt(cex, .67, .78, '60° < 90°', color=RED, fontsize=BODY_SIZE)

    # 底部结论
    txt(cex, .5, .015,
        '直径圆不覆盖   |   R_MEC = D/√3   |   γ = 1.1547',
        ha='center', color=RED, fontweight='bold', fontsize=BODY_SIZE)

    # ========== 4. Thales判据（右侧，35%面积） ==========
    crit.set(xlim=(279, 321), ylim=(477, 528))
    crit.set_aspect('equal')
    crit.set_xticks([])
    crit.set_yticks([])
    crit.spines[:].set_visible(False)

    txt(crit, 300, 526.5,
        '全称充要判定：Thales 顶点角',
        ha='center', fontsize=SUBTITLE_SIZE, fontweight='bold', color=INK)

    # 基准算例几何
    vv = np.vstack([V, V[0]])
    crit.add_patch(Polygon(V, fc=BLUE, alpha=.13, ec=BLUE, lw=1.4))
    crit.plot(*vv.T, color=BLUE, lw=1.4)
    crit.add_patch(Circle(C, R, fill=False, ec=BLUE, lw=1, ls=(0, (2, 2))))
    crit.plot([P[0], Q[0]], [P[1], Q[1]], color=BLUE, lw=1.4)

    # 顶点标注
    for i, x in enumerate(V):
        if np.linalg.norm(x-P) < 1e-6 or np.linalg.norm(x-Q) < 1e-6:
            crit.scatter(*x, marker='s', s=24, c=BLUE)
        else:
            crit.scatter(*x, s=20, c=BLUE)
            crit.plot([x[0], P[0]], [x[1], P[1]], color=GREY, lw=.55)
            crit.plot([x[0], Q[0]], [x[1], Q[1]], color=GREY, lw=.55)
            txt(crit, x[0]+(2 if x[0] > 300 else -12), x[1]+2,
               '118.07°', fontsize=ANNOTATION_SIZE, color=GREEN)

    txt(crit, 300, 478.5,
        '非端点顶点：角 ≥ 90° → 覆盖',
        ha='center', fontsize=CAPTION_SIZE, color=GREEN)

    # ========== 5. Jung区间（MEC夹逼） ==========
    mec.set(xlim=(.99, 1.18), ylim=(0, 1))
    off(mec)

    mec.plot([1, 2/math.sqrt(3)], [.52, .52], color=GREY, lw=8,
            alpha=.22, solid_capstyle='butt')
    mec.axvline(1, ymin=.23, ymax=.8, color=BLUE, lw=2)
    mec.axvline(2/math.sqrt(3), ymin=.23, ymax=.8, color=GREEN, lw=1.5, ls='--')

    txt(mec, 1, .84, 'γ = 1：覆盖', ha='center', color=BLUE,
       fontweight='bold', fontsize=BODY_SIZE)
    txt(mec, 2/math.sqrt(3), .84, '2/√3\n等边上界', ha='center',
       color=GREEN, fontsize=CAPTION_SIZE)
    txt(mec, 1.077, .12,
       '最小覆盖圆：1 ≤ γ = R_MEC/(D/2) ≤ 2/√3',
       ha='center', color=INK, fontsize=BODY_SIZE)

    # ========== 6. 特例验证框（底部右侧） ==========
    pocket.set(xlim=(0, 1), ylim=(0, 1))
    off(pocket)

    pocket.add_patch(FancyBboxPatch((.01, .02), .98, .96,
                                    boxstyle='round,pad=.02',
                                    fc='#eeeeee', ec=GREY,
                                    lw=.7, ls='--', alpha=.8))
    txt(pocket, .03, .76, '特例验证 · 非一般结论',
       fontweight='bold', color=RED, fontsize=CAPTION_SIZE)
    txt(pocket, .03, .53, '两站，ε=1°；L 为凸四边形',
       fontsize=ANNOTATION_SIZE)
    txt(pocket, .03, .30, 'D=39.598 m；R_MEC=19.799 m；γ=1.000',
       fontsize=ANNOTATION_SIZE)
    txt(pocket, .03, .08, 'Thales：P₁、P₃ 均为 118.07° → 覆盖',
       fontsize=ANNOTATION_SIZE-0.2)

    # ========== 7. 连接箭头（图内逻辑引导） ==========
    for a, bp, ls, label in [
        ((.30, .695), (.30, .675), (0, (3, 2)), '证否（存在性）'),
        ((.77, .695), (.77, .675), 'solid', '充要判定（全称）')
    ]:
        fig.add_artist(FancyArrowPatch(a, bp, transform=fig.transFigure,
                                      arrowstyle='-|>', mutation_scale=8,
                                      lw=.8, ls=ls, color=GREY))

    for a, bp in [((.30, .30), (.48, .275)), ((.77, .30), (.58, .275))]:
        fig.add_artist(FancyArrowPatch(a, bp, transform=fig.transFigure,
                                      arrowstyle='-|>', mutation_scale=8,
                                      lw=.8, color=GREY))

    # ========== 8. 保存（多格式 + 元数据） ==========
    stem = OUT / 'Q1_主图_覆盖判决桥_v2_improved'

    # 保存图片
    for ext in ['png', 'svg', 'pdf']:
        fig.savefig(stem.with_suffix(f'.{ext}'), dpi=300,
                   bbox_inches='tight', pad_inches=.03)

    # 保存元数据（供论文引用）
    metadata = {
        'figure_number': 'Fig. 1',
        'title': 'Q1主图：覆盖判决桥（改进版v2）',
        'caption': '问题一主图：直径圆覆盖判决框架。等边三角形反例证明直径圆一般不能保证覆盖；Thales判据提供逐例判定方法；Jung定理给出最小覆盖圆界；两站基准算例为γ=1特例验证。',
        'panels': {
            '等边反例': '40%面积，证明一般情况不能覆盖',
            'Thales判据': '35%面积，展示基准算例的逐顶点验证',
            'Jung区间': '15%面积，显示γ∈[1, 2/√3]界',
            '特例验证': '10%面积，明确标注非一般结论'
        },
        'math_verification': {
            'baseline_D': f'{D:.6f} m',
            'baseline_R_MEC': f'{R:.6f} m',
            'baseline_gamma': f'{R/(D/2):.6f}',
            'equilateral_gamma': f'{e["gamma"]:.6f}',
            'equilateral_covers': e['covers']
        },
        'color_scheme': {
            'BLUE': BLUE,
            'RED': RED,
            'GREEN': GREEN,
            'GREY': GREY,
            'INK': INK
        }
    }

    with open(stem.with_suffix('.json'), 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    plt.close(fig)
    print(f'\n✅ 图表保存成功：{stem}')
    print(f'✅ 元数据保存：{stem.with_suffix(".json")}')
    print('\n改进点总结：')
    print('1. 配色统一为math-modeling-figures规范')
    print('2. 修复savefig.dpi=300配置')
    print('3. 添加数学验证断言')
    print('4. 生成图表元数据JSON文件')
    print('5. 优化字号层级（TITLE/SUBTITLE/BODY/CAPTION）')

if __name__ == '__main__':
    main()
