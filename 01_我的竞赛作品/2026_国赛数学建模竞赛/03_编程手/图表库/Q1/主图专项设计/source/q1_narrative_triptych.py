# -*- coding: utf-8 -*-
"""问题一三帧连续叙事图：测角 → 求交 → 覆盖验证。"""
from __future__ import annotations
import sys
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Circle, Rectangle, ConnectionPatch
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import q1_main as model
OUT = ROOT.parent / "05_连续叙事主图"
OUT.mkdir(exist_ok=True)
BLUE, OCHRE, RED, GREEN, GREY, INK = "#26466D", "#C47B2B", "#8C3A2A", "#3D6B52", "#6B7B83", "#1A1A1A"
mpl.rcParams.update({"font.family":"sans-serif", "font.sans-serif":["Microsoft YaHei","SimHei","Arial","DejaVu Sans"], "font.size":8.5, "axes.unicode_minus":False, "svg.fonttype":"none", "pdf.fonttype":42, "mathtext.fontset":"stix", "savefig.dpi":600})
def geometry():
    G=np.array([300.,500.]); S=[np.array([0.,0.]),np.array([600.,0.])]
    th=[np.degrees(np.arctan2(*(G-s)[::-1])) for s in S]
    W=model.build_wedges(S,th,1.0); P=model.convex_hull(model.candidate_vertices(W))
    D,PQ=model.diameter_bruteforce(P); C,R=model.mec_bruteforce(P.vertices); L=np.array(P.vertices)
    assert len(L)==4 and abs(D-39.5983)<.01 and abs(R-19.7992)<.01 and np.isclose(R,D/2)
    return G,S,W,L,D,np.array(PQ),C,R,D/np.sqrt(3)
def style(ax):
    ax.set_aspect('equal'); ax.spines[['top','right']].set_visible(False)
    ax.spines[['left','bottom']].set_color(GREY); ax.tick_params(labelsize=7,colors=GREY,length=2)
def title(ax,n,s):
    ax.text(0,1.06,n,transform=ax.transAxes,fontsize=12,weight='bold',color=INK,va='bottom')
    ax.annotate(s,(0,1.06),xycoords='axes fraction',xytext=(17,0),textcoords='offset points',fontsize=9,color=INK,va='bottom')
def poly(ax,L,alpha=.25,lw=1.8):
    ax.add_patch(Polygon(L,closed=True,fc=OCHRE,ec=OCHRE,alpha=alpha,lw=lw,zorder=3))
    loop=np.vstack([L,L[0]]); ax.plot(*loop.T,color=OCHRE,lw=lw,zorder=4)
def local_rays(ax,W,G):
    for w in W:
        origin=w.apex-G
        for ray in (w.ray_minus,w.ray_plus):
            u=ray.direction; t=np.dot(-origin,u)
            a=origin+(t-40)*u; b=origin+(t+40)*u
            ax.plot([a[0],b[0]],[a[1],b[1]],color=BLUE,lw=1.15,alpha=.8,zorder=1)
def main():
    G,S,W,L,D,PQ,C,R,J=geometry(); Lz=L-G; PQz=PQ-G; Cz=C-G
    fig,(a,b,c)=plt.subplots(1,3,figsize=(10.6,3.75),gridspec_kw={'width_ratios':[1.28,1,1]},facecolor='white')
    fig.subplots_adjust(left=.045,right=.985,bottom=.19,top=.83,wspace=.32)
    # ① 同比例全景：角域、真源与将进入后续帧的放大框
    for i,w in enumerate(W):
        s=w.apex; ends=[]
        for ray in (w.ray_minus,w.ray_plus):
            e=s+760*ray.direction; ends.append(e); a.plot([s[0],e[0]],[s[1],e[1]],color=BLUE,lw=1.1)
        a.add_patch(Polygon([s,*ends],closed=True,fc=BLUE,ec='none',alpha=.08,zorder=0))
        a.scatter(*s,s=32,marker='s',color=BLUE,zorder=6); a.annotate(rf'$S_{i+1}$',s,xytext=(0,-12),textcoords='offset points',ha='center',color=BLUE)
    a.plot([0,600],[0,0],ls='--',lw=.8,color=GREY,alpha=.65); a.text(300,-35,r'$|S_1S_2|=600\ \mathrm{m}$',ha='center',fontsize=7,color=GREY)
    poly(a,L,.28,1.2); a.scatter(*G,marker='*',s=62,color=BLUE,zorder=7); a.annotate('G（真源）',G,xytext=(8,7),textcoords='offset points',color=BLUE)
    mn=L.min(0)-16; mx=L.max(0)+16; a.add_patch(Rectangle(mn,*(mx-mn),fill=False,ec=OCHRE,lw=1.1,zorder=8)); a.text(mx[0]+5,mx[1]+2,'×14 放大',fontsize=7,color=OCHRE)
    a.set(xlim=(-55,655),ylim=(-65,650),xlabel='$x$ (m)',ylabel='$y$ (m)'); a.set_xticks([0,300,600]); a.set_yticks([0,300,500]); style(a); title(a,'①','测角：两站角域约束')
    # ② 同一边界在局部闭合；顶点是第三帧唯一输入
    local_rays(b,W,G); poly(b,Lz,.30,2.0)
    for i,p in enumerate(Lz,1): b.scatter(*p,s=26,color=RED,zorder=7); b.annotate(rf'$P_{i}$',p,xytext=(4,4),textcoords='offset points',fontsize=8,color=RED)
    b.text(.04,.96,r'$L=W_1\cap W_2$',transform=b.transAxes,va='top',fontsize=9)
    b.text(.04,.06,'边界射线求交 → 4 个顶点',transform=b.transAxes,color=GREY,fontsize=7.2)
    b.set(xlim=(-29,29),ylim=(-29,29),xlabel='$x-300$ (m)',ylabel='$y-500$ (m)'); style(b); title(b,'②','求交：闭合可行域 $L$')
    # ③ 完全复用②的四顶点，突出直径端点和正确的夹逼关系
    poly(c,Lz,.18,1.7); c.add_patch(Circle(Cz,J,fill=False,ec=GREEN,lw=1.0,ls=':',zorder=3)); c.add_patch(Circle(Cz,R,fill=False,ec=BLUE,lw=2.0,zorder=4))
    c.plot(*PQz.T,color=RED,lw=2.3,zorder=5); c.scatter(*Lz.T,s=20,color=RED,zorder=6); c.scatter(*Cz,marker='+',s=65,color=GREEN,zorder=7,linewidths=1.5)
    for label,p in zip(('P','Q'),PQz): c.annotate(label,p,xytext=(5,4),textcoords='offset points',color=RED,fontsize=9)
    c.annotate(r'$C^*$',Cz,xytext=(5,-12),textcoords='offset points',color=GREEN,fontsize=8)
    c.text(.04,.96,r'$R_{\mathrm{MEC}}=D/2$',transform=c.transAxes,va='top',fontsize=9)
    c.text(.04,.06,rf'$D/2={R:.3f}\;=R_{{\rm MEC}}<{J:.3f}=D/\sqrt{{3}}$',transform=c.transAxes,color=GREY,fontsize=7.0)
    c.set(xlim=(-29,29),ylim=(-29,29),xlabel='$x-300$ (m)',ylabel='$y-500$ (m)'); style(c); title(c,'③','覆盖：直径与最小包围圆')
    # 连接必须从产出对象指向下一阶段
    for y, dst in ((0,0),(1,1)):
        fig.add_artist(ConnectionPatch(xyA=(mx[0],mn[1] if y==0 else mx[1]),coordsA=a.transData,xyB=(0,dst),coordsB=b.transAxes,ls=(0,(3,2)),lw=.7,color=GREY,alpha=.7))
    fig.add_artist(ConnectionPatch(xyA=(1,.5),coordsA=b.transAxes,xyB=(0,.5),coordsB=c.transAxes,arrowstyle='-|>',lw=1.3,color=OCHRE))
    fig.text(.045,.07,rf'基准算例：$\varepsilon=1^\circ$；$D={D:.3f}$ m，$R_{{\mathrm{{MEC}}}}={R:.3f}$ m，$\gamma=2R_{{\mathrm{{MEC}}}}/D=1.000$。',fontsize=7.7,color=GREY)
    fig.text(.045,.028,'同一组边界射线 → 同一组顶点 → 同一最小包围圆；局部面板仅改变显示尺度。',fontsize=7.4,color=GREY)
    stem=OUT/'Q1_连续叙事_三帧演化_v2'
    for ext in ('png','svg','pdf'): fig.savefig(stem.with_suffix('.'+ext),dpi=600,bbox_inches='tight',pad_inches=.04,facecolor='white')
    plt.close(fig); print(f'D={D:.4f}, R={R:.4f}, gamma={2*R/D:.4f}; saved {stem}')
if __name__=='__main__': main()

