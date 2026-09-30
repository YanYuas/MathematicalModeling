# -*- coding: utf-8 -*-
"""Q1 main figure: Forked Coverage Verdict Bridge."""
from pathlib import Path
import sys, math, json
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Arc, FancyArrowPatch, FancyBboxPatch
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import q1_geometry_core as q
OUT=ROOT/'07_最终主图'; OUT.mkdir(exist_ok=True)
BLUE,RED,TEAL,GREY,INK='#0F4D92','#B64342','#42949E','#767676','#202020'
mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Microsoft YaHei','SimHei','DejaVu Sans'],'font.size':8,'axes.unicode_minus':False,'svg.fonttype':'none','pdf.fonttype':42,'mathtext.fontset':'stix'})
def off(ax): ax.set_axis_off()
def ax(fig,b): return fig.add_axes(b)
def txt(ax,x,y,s,**kw): return ax.text(x,y,s,**kw)
def main():
 b=q.baseline(); e=q.equilateral(1); V=np.array(b['V']); P,Q=np.array(b['ends']); C=np.array(b['C']); D,R=b['D'],b['R_MEC']
 assert len(V)==4 and abs(D-39.598327)<1e-5 and abs(R-D/2)<1e-7 and not e['covers']
 fig=plt.figure(figsize=(6.2992,5.3150),facecolor='white')
 head=ax(fig,[.03,.945,.94,.042]); chain=ax(fig,[.04,.695,.92,.20]); cex=ax(fig,[.03,.30,.535,.375]); crit=ax(fig,[.605,.30,.365,.375]); mec=ax(fig,[.04,.135,.92,.14]); pocket=ax(fig,[.62,.02,.34,.09])
 for a in [head,chain,mec,pocket]: off(a)
 # conclusion
 txt(head,.5,.5,'以 D 为直径的圆不保证覆盖定位区域 L；覆盖当且仅当 γ = 1',ha='center',va='center',fontsize=9.2,fontweight='bold',color=INK)
 # chain: conceptual symbols only
 chain.set(xlim=(0,100),ylim=(0,20)); off(chain)
 txt(chain,2,18,'输入构造：带误差的示向度 → 有界凸定位区域 → 候选直径圆',fontsize=8.0,fontweight='bold',color=INK)
 for origin,ang,col,label in [((8,5),25,GREY,'W1'),((15,5),70,GREY,'W2')]:
  o=np.array(origin); u1=np.array([math.cos(math.radians(ang-10)),math.sin(math.radians(ang-10))]);u2=np.array([math.cos(math.radians(ang+10)),math.sin(math.radians(ang+10))])
  chain.add_patch(Polygon([o,o+8*u1,o+8*u2],fc=GREY,ec='none',alpha=.12)); chain.plot([o[0],o[0]+8*u1[0]],[o[1],o[1]+8*u1[1]],color=GREY,lw=.8);chain.plot([o[0],o[0]+8*u2[0]],[o[1],o[1]+8*u2[1]],color=GREY,lw=.8); txt(chain,o[0],o[1]-2,label,ha='center',color=GREY)
 chain.add_patch(FancyArrowPatch((25,10),(34,10),arrowstyle='-|>',mutation_scale=9,lw=.8,color=GREY)); txt(chain,29.5,12,'∩',ha='center',fontsize=12)
 lv=np.array([[38,7],[43,4],[48,7],[43,11]]) ; chain.add_patch(Polygon(lv,fc=BLUE,alpha=.15,ec=BLUE,lw=1.1));txt(chain,43,13,'L（凸）',ha='center',color=BLUE)
 chain.add_patch(FancyArrowPatch((51,10),(61,10),arrowstyle='-|>',mutation_scale=9,lw=.8,color=GREY)); chain.plot([65,65],[5,14],color=BLUE,lw=1.5); txt(chain,65,3,'P,Q  给出 D',ha='center',color=BLUE)
 chain.add_patch(Circle((78,10),5,fill=False,ec=BLUE,lw=1,ls=(0,(2,2))));chain.plot([73,83],[10,10],color=BLUE,lw=1);txt(chain,78,17,'候选直径圆',ha='center',color=BLUE)
 txt(chain,2,.4,'前提：L 非空且有界；各站误差半角 ε 相同。无界时 D 无定义。',fontsize=7.3,color=GREY)
 # counterexample: deliberately the largest visual field; no coordinate axes
 cex.set(xlim=(-.14,1.14),ylim=(-.03,1.15));cex.set_aspect('equal');cex.set_xticks([]);cex.set_yticks([]);cex.spines[:].set_visible(False)
 txt(cex,.5,1.105,'存在性证否：等边三角形反例（n ≥ 3，归一化 D = 1）',ha='center',fontsize=7.8,fontweight='bold',color=RED)
 T=np.array(e['V']); ce=np.array([.5,math.sqrt(3)/6]); cex.add_patch(Circle(ce,1/math.sqrt(3),fill=False,ec=TEAL,lw=1.45));cex.add_patch(Circle((.5,0),.5,fill=False,ec=GREY,lw=1.0,ls=(0,(1,2))));cex.add_patch(Polygon(T,fill=False,ec=RED,lw=1.8));cex.plot([0,1],[0,0],color=GREY,lw=1.15)
 for p,l,dx in zip(T,['A','B','C'],[-.02,.02,0]): cex.scatter(*p,s=28,c=RED,marker='^');txt(cex,p[0]+dx,p[1]+.045,l,ha='center',color=RED,fontsize=7.2)
 cex.add_patch(Arc((.5,math.sqrt(3)/2),.30,.22,angle=0,theta1=220,theta2=320,ec=RED,lw=1.2));txt(cex,.67,.78,'60° < 90°',color=RED,fontsize=7.2)
 txt(cex,.5,.015,'直径圆不覆盖   |   R_MEC = D/√3   |   γ = 1.1547',ha='center',color=RED,fontweight='bold',fontsize=7.1)
 # criterion
 crit.set(xlim=(279,321),ylim=(477,528));crit.set_aspect('equal');crit.set_xticks([]);crit.set_yticks([]);crit.spines[:].set_visible(False)
 txt(crit,300,526.5,'全称充要判定：Thales 顶点角',ha='center',fontsize=7.8,fontweight='bold',color=INK)
 vv=np.vstack([V,V[0]]);crit.add_patch(Polygon(V,fc=BLUE,alpha=.13,ec=BLUE,lw=1.4));crit.plot(*vv.T,color=BLUE,lw=1.4);crit.add_patch(Circle(C,R,fill=False,ec=BLUE,lw=1,ls=(0,(2,2))));crit.plot([P[0],Q[0]],[P[1],Q[1]],color=BLUE,lw=1.4)
 for i,x in enumerate(V):
  if np.linalg.norm(x-P)<1e-6 or np.linalg.norm(x-Q)<1e-6: crit.scatter(*x,marker='s',s=24,c=BLUE)
  else:
   crit.scatter(*x,s=20,c=BLUE);crit.plot([x[0],P[0]],[x[1],P[1]],color=GREY,lw=.55);crit.plot([x[0],Q[0]],[x[1],Q[1]],color=GREY,lw=.55);txt(crit,x[0]+(2 if x[0]>300 else -12),x[1]+2,'118.07°',fontsize=5.9,color=RED)
 txt(crit,300,478.5,'非端点顶点：角 ≥ 90°  → 覆盖',ha='center',fontsize=6.3,color=TEAL)
 # MEC gamma axis
 mec.set(xlim=(.99,1.18),ylim=(0,1));off(mec);mec.plot([1,2/math.sqrt(3)],[.52,.52],color=GREY,lw=8,alpha=.22,solid_capstyle='butt');mec.axvline(1,ymin=.23,ymax=.8,color=BLUE,lw=2);mec.axvline(2/math.sqrt(3),ymin=.23,ymax=.8,color=TEAL,lw=1.5,ls='--')
 txt(mec,1,.84,'γ = 1：覆盖',ha='center',color=BLUE,fontweight='bold',fontsize=7.1);txt(mec,2/math.sqrt(3),.84,'2/√3\n等边上界',ha='center',color=TEAL,fontsize=6.3);txt(mec,1.077,.12,'最小覆盖圆：1 ≤ γ = R_MEC/(D/2) ≤ 2/√3',ha='center',color=INK,fontsize=7.2)
 # pocket
 pocket.set(xlim=(0,1),ylim=(0,1));off(pocket);pocket.add_patch(FancyBboxPatch((.01,.02),.98,.96,boxstyle='round,pad=.02',fc='#eeeeee',ec=GREY,lw=.7,ls='--',alpha=.8));txt(pocket,.03,.76,'特例验证 · 非一般结论',fontweight='bold',color=RED,fontsize=6.0);txt(pocket,.03,.53,'两站，ε=1°；L 为凸四边形',fontsize=5.4);txt(pocket,.03,.30,'D=39.598 m；R_MEC=19.799 m；γ=1.000',fontsize=5.1);txt(pocket,.03,.08,'Thales：P1、P3 均为 118.07° → 覆盖',fontsize=4.8)
 # connectors in figure coords
 for a,bp,ls,label in [((.30,.695),(.30,.675),(0,(3,2)),'证否（存在性）'),((.77,.695),(.77,.675),'solid','充要判定（全称）')]: fig.add_artist(FancyArrowPatch(a,bp,transform=fig.transFigure,arrowstyle='-|>',mutation_scale=8,lw=.8,ls=ls,color=GREY))
 for a,bp in [((.30,.30),(.48,.275)),((.77,.30),(.58,.275))]:fig.add_artist(FancyArrowPatch(a,bp,transform=fig.transFigure,arrowstyle='-|>',mutation_scale=8,lw=.8,color=GREY))
 stem=OUT/'Q1_主图_覆盖判决桥';
 for ext in ['png','svg','pdf']:fig.savefig(stem.with_suffix('.'+ext),dpi=600,bbox_inches='tight',pad_inches=.03)
 plt.close(fig);print(stem)
if __name__=='__main__':main()
