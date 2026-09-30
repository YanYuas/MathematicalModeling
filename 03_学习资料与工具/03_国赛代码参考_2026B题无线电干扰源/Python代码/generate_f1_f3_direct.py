"""F1–F3 direct review figures. Reads only the frozen Phase-1 contract."""
from __future__ import annotations

import csv
from pathlib import Path
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, FancyArrowPatch, Wedge

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "图集_v1"
OUT.mkdir(exist_ok=True)
CSV = ROOT.parent / "data" / "r1_r2_boundary_contract.csv"

NAVY, TEAL, OCHRE, GRAY, PALE, INK = "#233B72", "#147B7E", "#B26028", "#909AA3", "#E9EDF0", "#20252B"
mpl.rcParams.update({"font.family": ["Microsoft YaHei", "SimHei", "sans-serif"], "axes.unicode_minus": False,
                     "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 9, "axes.linewidth": .8})

def data():
    with CSV.open(encoding="utf-8", newline="") as f: rows = list(csv.DictReader(f))
    a = np.array([float(r["alpha_deg"]) for r in rows]); lo = np.array([float(r["b_angle_boundary_m"]) for r in rows]); hi = np.array([float(r["b_distance_boundary_m"]) for r in rows])
    assert len(rows)==4001 and np.isclose(a[0],-1) and np.isclose(a[-1],1)
    assert np.isclose(lo.max(),649.8797605327188,atol=1e-9) and np.isclose(hi.min(),638.3401947575173,atol=1e-9)
    return a,lo,hi

def save(fig,name):
    for ext,kw in (("png",{"dpi":600}),("svg",{}),("pdf",{})):
        fig.savefig(OUT/f"{name}.{ext}",bbox_inches="tight",facecolor="white",**kw)
    plt.close(fig)

def f1():
    fig=plt.figure(figsize=(7.2,4.25),facecolor="white")
    ax=fig.add_axes([.07,.14,.56,.78]); ax.set_aspect("equal"); ax.axis("off")
    p1=np.array([0.,0.]); g=np.array([5.0,0.]); p2=np.array([3.45,2.25])
    ax.add_patch(Wedge(p1,5.45,-8,8,facecolor=NAVY,alpha=.10,edgecolor="none"))
    for ang in (-8,8): ax.plot([0,5.35*np.cos(np.deg2rad(ang))],[0,5.35*np.sin(np.deg2rad(ang))],color=NAVY,lw=1,ls=(0,(3,2)))
    ax.plot([0,g[0]],[0,0],color=GRAY,lw=1.2,ls=(0,(3,2)))
    ax.plot([0,p2[0]],[0,p2[1]],color=INK,lw=1.7)
    ax.plot([g[0],p2[0]],[0,p2[1]],color=OCHRE,lw=1.8)
    ax.plot([p2[0],p2[0]],[0,p2[1]],color=TEAL,lw=1,ls=(0,(2,2)))
    ax.plot([0,p2[0]],[0,0],color=TEAL,lw=1,ls=(0,(2,2)))
    ax.add_patch(Arc(g,.95,.95,theta1=125,theta2=180,color=OCHRE,lw=1.2)); ax.text(4.52,.27,"φ",color=OCHRE,fontsize=11)
    ax.add_patch(Arc(p1,1.25,1.25,theta1=-8,theta2=8,color=NAVY,lw=1.1)); ax.text(1.08,.23,"α",color=NAVY,fontsize=10)
    ax.scatter(*p1,s=34,color=INK,zorder=3);ax.scatter(*g,s=38,color=NAVY,zorder=3);ax.scatter(*p2,s=45,color=OCHRE,zorder=3)
    ax.text(-.18,-.43,"P₁",ha="center",fontsize=10); ax.text(5.02,-.43,"G(r, α)",ha="center",color=NAVY,fontsize=10); ax.text(3.56,2.42,"P₂(a, b)",color=OCHRE,fontsize=10)
    ax.text(1.72,-.42,"a",color=TEAL,fontsize=10); ax.text(3.58,1.08,"b",color=TEAL,fontsize=10); ax.text(1.55,1.32,"d₂",color=INK,fontsize=10)
    ax.text(1.75,.72,"示向偏差范围\nα ∈ [−1°, 1°]",color=NAVY,ha="center",fontsize=8)
    ax.set_xlim(-.6,6.0);ax.set_ylim(-.8,3.3)
    bx=fig.add_axes([.69,.22,.27,.58]); bx.axis("off")
    bx.text(0,.92,"鲁棒判据",fontsize=13,fontweight="bold",color=INK)
    bx.text(0,.68,"同一个 P₂(a, b)",fontsize=11,color=OCHRE,fontweight="bold")
    bx.text(0,.50,"覆盖全部源状态",fontsize=10,color=INK)
    bx.text(0,.32,"∀ α ∈ [−1°, 1°]\n∀ r ∈ [5, 1500] m",fontsize=10,color=NAVY,linespacing=1.55)
    bx.text(0,.06,"φ ≥ φₜₐᵣ₉ₑₜ\nd₂ ≤ 1000 m",fontsize=10,color=TEAL,linespacing=1.55)
    save(fig,"F1_鲁棒判据定义")

def f2(lo,hi):
    nominal_lo,nominal_hi=lo[2000],hi[2000]; rlo,rhi=lo.max(),hi.min(); gap=rlo-rhi
    fig,ax=plt.subplots(figsize=(7.2,2.65),facecolor="white"); fig.subplots_adjust(left=.14,right=.96,bottom=.25,top=.90)
    ax.set(xlim=(620,670),ylim=(-.25,2.55),xlabel="横向偏移 b（m）");ax.set_yticks([]);ax.set_xticks(np.arange(620,671,10));ax.grid(axis="x",color="#E1E5E8",lw=.7)
    ax.spines[["top","right","left"]].set_visible(False)
    ax.text(619.3,1.86,"名义\nα = 0",ha="right",va="center",fontsize=9,color=INK,fontweight="bold")
    ax.hlines(1.86,nominal_lo,nominal_hi,color=GRAY,lw=13,capstyle="butt");ax.vlines([nominal_lo,nominal_hi],1.68,2.04,color="#68727A",lw=1)
    ax.text((nominal_lo+nominal_hi)/2,2.18,"名义候选带  627.23–664.26 m",ha="center",fontsize=9,color="#66717A")
    ax.text(619.3,.70,"鲁棒\n∀ α",ha="right",va="center",fontsize=9,color=INK,fontweight="bold")
    ax.hlines(.70,620,rhi,color=TEAL,lw=5,ls=(0,(5,2.5)));ax.add_patch(FancyArrowPatch((622,.70),(620,.70),arrowstyle="-|>",mutation_scale=10,color=TEAL,lw=0))
    ax.hlines(.70,rlo,670,color=NAVY,lw=5);ax.add_patch(FancyArrowPatch((668,.70),(670,.70),arrowstyle="-|>",mutation_scale=10,color=NAVY,lw=0))
    ax.text(rhi-.25,1.08,"距离约束：b ≤ 638.34",ha="right",color=TEAL,fontsize=8.5);ax.text(rlo+.25,1.08,"角度约束：b ≥ 649.88",ha="left",color=NAVY,fontsize=8.5)
    ax.axvspan(rhi,rlo,ymin=.13,ymax=.50,facecolor="#F2E8DE",hatch="///",edgecolor=OCHRE,linewidth=0,zorder=0)
    ax.add_patch(FancyArrowPatch((rhi,.25),(rlo,.25),arrowstyle="<->",mutation_scale=12,color=OCHRE,lw=1.8));ax.text((rlo+rhi)/2,-.12,f"共同区间为空  ·  缺口 {gap:.2f} m",ha="center",color=OCHRE,fontsize=10,fontweight="bold")
    save(fig,"F2_共同约束夹逼")

def f3(a,lo,hi):
    rlo,rhi=lo.max(),hi.min(); fig,axs=plt.subplots(1,2,figsize=(7.2,3.25),gridspec_kw={"width_ratios":[1.5,1]},facecolor="white");fig.subplots_adjust(left=.10,right=.97,bottom=.20,top=.88,wspace=.25)
    ax=axs[0];ax.fill_between(a,lo,hi,color=PALE,zorder=0);ax.plot(a,lo,color=NAVY,lw=2);ax.plot(a,hi,color=TEAL,lw=2,ls=(0,(5,3)));ax.axhline(rlo,color=NAVY,lw=.9,ls=(0,(1,2)));ax.axhline(rhi,color=TEAL,lw=.9,ls=(0,(1,2)))
    ax.scatter([1,-1],[rlo,rhi],s=30,color=[NAVY,TEAL],zorder=5);ax.annotate("角度最严\n+1°",(1,rlo),xytext=(.67,660),color=NAVY,fontsize=7,arrowprops={"arrowstyle":"-","color":NAVY});ax.annotate("距离最严\n−1°",(-1,rhi),xytext=(-.82,618),color=TEAL,fontsize=7,arrowprops={"arrowstyle":"-","color":TEAL})
    ax.text(0,645,"固定 α 下\n局部可选区间",ha="center",va="center",fontsize=8,color=INK);ax.set(xlim=(-1.05,1.05),ylim=(610,675),xlabel="示向偏差 α（°）",ylabel="横向偏移 b（m）",xticks=[-1,0,1]);ax.grid(axis="y",color="#E1E5E8",lw=.7);ax.spines[["top","right"]].set_visible(False);ax.text(-.12,1.03,"(a)",transform=ax.transAxes,fontweight="bold")
    ax=axs[1];ax.set(xlim=(620,670),ylim=(0,1),xlabel="共同 b（m）",yticks=[]);ax.grid(axis="x",color="#E1E5E8",lw=.7);ax.spines[["top","right","left"]].set_visible(False);ax.vlines(rhi,.20,.70,color=TEAL,lw=2.4,ls=(0,(5,3)));ax.vlines(rlo,.20,.70,color=NAVY,lw=2.4);ax.add_patch(FancyArrowPatch((rhi,.35),(rlo,.35),arrowstyle="<->",mutation_scale=12,color=OCHRE,lw=1.5));ax.text((rlo+rhi)/2,.12,"全 α 的共同条件\n不存在共同 b",ha="center",fontsize=8,color=OCHRE,fontweight="bold");ax.text(-.15,1.03,"(b)",transform=ax.transAxes,fontweight="bold")
    save(fig,"F3_逐方向边界与共同包络")

if __name__=="__main__":
    a,lo,hi=data();f1();f2(lo,hi);f3(a,lo,hi)
