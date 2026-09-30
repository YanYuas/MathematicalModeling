# -*- coding: utf-8 -*-
"""Q1 visual redesign: one integrated Thales coverage dial (Python/matplotlib)."""
from pathlib import Path
import math
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Arc, FancyBboxPatch, Wedge

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '08_Thales判别盘'; OUT.mkdir(exist_ok=True)
BLUE, RED, TEAL, GREY, INK = '#0F4D92', '#B64342', '#42949E', '#767676', '#202020'
mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Microsoft YaHei','SimHei','DejaVu Sans'],
                     'axes.unicode_minus':False,'svg.fonttype':'none','pdf.fonttype':42})

def text(ax, x, y, s, **kw):
    return ax.text(x, y, s, **kw)

def main():
    fig = plt.figure(figsize=(6.2992, 5.3150), facecolor='white')
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.set_aspect('equal'); ax.axis('off')

    # Claim: quiet, single line; the geometry bears the proof.
    text(ax, 50, 96, '直径圆并不保证覆盖定位区域', ha='center', va='center', fontsize=12, fontweight='bold', color=INK)
    text(ax, 50, 92.7, '覆盖判别由同一条直径边界给出', ha='center', va='center', fontsize=7.5, color=GREY)

    # Faint origin of L: a trace, not a separate flow-chart.
    for a, o in [(28, (12, 24)), (54, (16, 20)), (78, (21, 23))]:
        ax.add_patch(Wedge(o, 18, a-8, a+8, facecolor=BLUE, edgecolor='none', alpha=.035))
        for s in (-8, 8):
            r = math.radians(a+s); ax.plot([o[0], o[0]+18*math.cos(r)], [o[1], o[1]+18*math.sin(r)], color=GREY, lw=.55, alpha=.55)
    L = [(18,31),(24,25),(31,29),(28,37),(21,38)]
    ax.add_patch(Polygon(L, closed=True, facecolor=BLUE, edgecolor=BLUE, lw=.9, alpha=.10))
    text(ax, 12, 43, 'L = ∩Wi', fontsize=7.5, color=BLUE, fontweight='bold')
    text(ax, 12, 40.3, '非空、有界凸集', fontsize=6.2, color=GREY)
    ax.plot([31, 32.8], [31, 36], color=GREY, lw=.7, ls=(0,(2,2)))

    # One central geometry: PQ is both diameter and decision boundary.
    P, Q, O = (25, 44), (77, 44), (51, 44)
    r = 26; side = 52; apex = (51, 44 + side * math.sqrt(3)/2)
    mec_c = (51, 44 + side*math.sqrt(3)/6); mec_r = side/math.sqrt(3)
    ax.add_patch(Circle(O, r, facecolor=BLUE, edgecolor='none', alpha=.055))
    ax.add_patch(Circle(O, r, fill=False, ec=BLUE, lw=1.55, ls=(0,(2.0,2.5))))
    ax.add_patch(Circle(mec_c, mec_r, fill=False, ec=TEAL, lw=1.55))
    ax.add_patch(Polygon([P,Q,apex], closed=True, fill=False, ec=RED, lw=2.25, joinstyle='round'))
    ax.plot([P[0],Q[0]],[P[1],Q[1]],color=BLUE,lw=2.0)
    ax.scatter([P[0],Q[0]],[P[1],Q[1]],s=24,c=BLUE,marker='s',zorder=6)
    ax.scatter(*apex,s=42,c=RED,marker='^',zorder=6)
    text(ax, P[0]-2.3, P[1]-3.5, 'P', fontsize=7.5, color=BLUE, fontweight='bold')
    text(ax, Q[0]+1.3, Q[1]-3.5, 'Q', fontsize=7.5, color=BLUE, fontweight='bold')
    text(ax, 51, 40.4, 'D', ha='center', fontsize=8, color=BLUE, fontweight='bold')

    # The same circle carries the Thales threshold: its top point is 90 degrees.
    ax.add_patch(Arc(apex, 10, 7, angle=0, theta1=210, theta2=330, ec=RED, lw=1.25))
    text(ax, 58.0, 84.0, '60°', fontsize=8.5, color=RED, fontweight='bold')
    ax.plot([51,51],[70,73], color=GREY, lw=.7, ls=(0,(1,1.5)))
    ax.plot([49.7,49.7,51],[70,71.3,71.3], color=BLUE, lw=.8)
    text(ax, 52.6, 71.2, '90° 阈值', fontsize=6.7, color=BLUE)

    # Two direct labels on the only decisive boundary.
    text(ax, 76.5, 61.5, '圆内：覆盖', fontsize=7.5, color=BLUE, rotation=-28, ha='left')
    text(ax, 70.5, 80.0, '圆外：不覆盖', fontsize=8.2, color=RED, fontweight='bold', rotation=-23)
    text(ax, 51, 16.0, '等边三角形反例（n ≥ 3，归一化 D = 1）', ha='center', fontsize=8.1, color=RED, fontweight='bold')
    text(ax, 51, 12.7, '顶点越出直径圆；R_MEC = D/√3，γ = 2/√3', ha='center', fontsize=7.1, color=TEAL)

    # Restrained radial ruler, attached to the MEC ring rather than a separate panel.
    ax.plot([83.8,88.8],[62.5,68.7], color=GREY, lw=.75)
    ax.plot([83.0,87.1],[61.5,66.5], color=TEAL, lw=2.6)
    text(ax, 89.4, 69.0, 'MEC', fontsize=6.8, color=TEAL, fontweight='bold')
    text(ax, 89.4, 65.9, 'γ: 1 → 1.1547', fontsize=6.4, color=TEAL)

    # Tiny baseline stamp: evidence only, visually subordinate.
    stamp = FancyBboxPatch((72, 3.5), 23, 10.0, boxstyle='round,pad=.8,rounding_size=1.4', fc='#F3F3F3', ec='#B6B6B6', lw=.65, ls=(0,(2,2)))
    ax.add_patch(stamp)
    ax.add_patch(Circle((78.5,8.5),3.0, fill=False, ec=BLUE, lw=.65, ls=(0,(1,1.5))))
    ax.plot([75.5,81.5],[8.5,8.5],color=BLUE,lw=.7); ax.plot([78.5,78.5],[5.5,11.5],color=BLUE,lw=.7)
    text(ax, 83, 10.2, '两站基准特例', fontsize=6.4, color=GREY, fontweight='bold')
    text(ax, 83, 7.6, 'γ = 1，覆盖', fontsize=6.4, color=BLUE)
    text(ax, 83, 5.3, '仅作验证', fontsize=5.8, color=GREY)

    stem = OUT / 'Q1_主图_Thales判别盘_v1'
    for ext in ('png','svg','pdf'):
        fig.savefig(stem.with_suffix('.'+ext), dpi=600, bbox_inches='tight', pad_inches=.03)
    plt.close(fig)
    print(stem)

if __name__ == '__main__': main()
