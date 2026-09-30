# -*- coding: utf-8 -*-
"""Decision sketches only: three alternative visual architectures for Q1."""
from pathlib import Path
import math
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Circle, Polygon, FancyArrowPatch

OUT = Path(__file__).resolve().parent / '09_方案草图'; OUT.mkdir(exist_ok=True)
B, R, T, G = '#0F4D92', '#B64342', '#42949E', '#767676'
mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Microsoft YaHei','SimHei','DejaVu Sans'],
                     'axes.unicode_minus':False,'pdf.fonttype':42})

def clean(ax, title, sub):
    ax.set(xlim=(0,100), ylim=(0,100)); ax.set_aspect('equal'); ax.axis('off')
    ax.text(50,96,title,ha='center',fontsize=12,fontweight='bold')
    ax.text(50,91,sub,ha='center',fontsize=7,color=G)

def dial(ax):
    clean(ax,'A｜Thales 判别盘','一个边界同时呈现反例、阈值与 MEC')
    P,Q,O=(17,38),(83,38),(50,38); r=33; top=(50,95.2); mc=(50,57.1); mr=38.1
    ax.add_patch(Circle(O,r,fc=B,ec=B,alpha=.07,ls='--')); ax.add_patch(Circle(mc,mr,fill=False,ec=T,lw=2))
    ax.plot([P[0],Q[0]],[P[1],Q[1]],c=B,lw=2); ax.add_patch(Polygon([P,Q,top],fill=False,ec=R,lw=2.8))
    ax.text(50,34,'D',ha='center',color=B,fontweight='bold'); ax.text(55,82,'60°',color=R,fontweight='bold')
    ax.text(70,69,'圆外\n不覆盖',color=R,fontsize=8,ha='center'); ax.text(68,51,'圆内\n覆盖',color=B,fontsize=8,ha='center')
    ax.text(50,12,'γ :  1  →  2/√3',ha='center',color=T,fontsize=9)

def cutaway(ax):
    clean(ax,'B｜几何剖面','从角域切入，沿同一条直径读出两种结论')
    # translucent angular field, deliberately diagonal rather than panels
    for p in [[(9,20),(62,45),(13,80)],[(20,14),(78,54),(30,89)],[(5,42),(88,73),(55,10)]]:
        ax.add_patch(Polygon(p,fc=B,ec=B,alpha=.05,lw=.7))
    L=[(31,40),(51,29),(69,44),(59,66),(38,62)]; ax.add_patch(Polygon(L,fc=B,ec=B,alpha=.15,lw=1.4))
    ax.plot([31,69],[40,44],c=B,lw=2); ax.add_patch(Circle((50,42),19.1,fill=False,ec=B,ls='--',lw=1.5))
    ax.add_patch(Circle((50,49),22.1,fill=False,ec=T,lw=1.8))
    ax.plot([31,50,69],[40,78,44],c=R,lw=2.5); ax.scatter([50],[78],marker='^',s=48,c=R)
    ax.text(18,76,'角域交叠',color=G,fontsize=8); ax.text(50,23,'L 的直径截面',color=B,fontsize=8,ha='center')
    ax.text(77,70,'越界顶点\n→ 反例',color=R,fontsize=8); ax.text(75,32,'扩大至 MEC\n→ 覆盖',color=T,fontsize=8)

def ribbon(ax):
    clean(ax,'C｜证据折带','一条连续折带：构造 → 反例 → 判据 → 特例')
    # One continuous ribbon, deliberately not cards/grid.
    ax.plot([8,25,44,64,88],[70,54,72,47,61],c=G,lw=2.2)
    pts=[(12,70),(32,54),(52,72),(74,47),(91,61)]
    for x,y in pts: ax.add_patch(Circle((x,y),4.5,fc='white',ec=G,lw=1.3))
    ax.add_patch(Polygon([(26,50),(38,50),(32,63)],fill=False,ec=R,lw=2.3))
    ax.add_patch(Circle((32,54),7,fill=False,ec=T,lw=1.4))
    ax.add_patch(Circle((53,72),8,fill=False,ec=B,ls='--',lw=1.6)); ax.plot([45,61],[72,72],c=B,lw=1.6)
    ax.add_patch(Circle((74,47),7,fill=False,ec=T,lw=1.5)); ax.plot([67,81],[47,47],c=B,lw=1.5)
    labels=[('角域',12,81,G),('反例',32,40,R),('90° 判别',53,84,B),('MEC',74,34,T),('特例',91,71,G)]
    for s,x,y,c in labels: ax.text(x,y,s,ha='center',fontsize=8,color=c,fontweight='bold')
    ax.text(50,14,'适合做辅图组的统一视觉母题，不适合单独承担全部证明',ha='center',fontsize=7,color=G)

fig, axes = plt.subplots(1,3,figsize=(14,5),facecolor='white')
dial(axes[0]); cutaway(axes[1]); ribbon(axes[2])
fig.subplots_adjust(wspace=.06,left=.02,right=.98,top=.98,bottom=.02)
stem=OUT/'Q1_三套独立构图草图'
fig.savefig(stem.with_suffix('.png'),dpi=220)
fig.savefig(stem.with_suffix('.pdf'))
print(stem)
