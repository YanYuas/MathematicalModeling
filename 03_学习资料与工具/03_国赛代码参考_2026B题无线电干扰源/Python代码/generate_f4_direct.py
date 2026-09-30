"""Recompute the four registered robust searches and render F4 from the log."""
from __future__ import annotations
import csv, json, math
from pathlib import Path
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT=Path(__file__).resolve().parent; OUT=ROOT/"图集_v1"; OUT.mkdir(exist_ok=True)
EPS=math.radians(1); ALPHA=np.linspace(-EPS,EPS,801); R=(5.,1500.); LIMIT=1000.
STAGES=[("coarse",-400,1800,0,1200,20), ("fine",700,820,580,700,2), ("ultra",758,770,644,656,.25), ("wide",-800,2400,0,1400,40)]
EXPECTED={"coarse":(39.283466,760,640,6771),"fine":(39.572590,764,650,3721),"ultra":(39.616116,764,651,2401),"wide":(39.283466,760,640,2916)}

def score(a,b):
    c=np.cos(ALPHA); s=np.sin(ALPHA); d0=np.sqrt(a*a+b*b+R[0]*R[0]-2*R[0]*(a*c+b*s)); d1=np.sqrt(a*a+b*b+R[1]*R[1]-2*R[1]*(a*c+b*s)); d=np.maximum(d0,d1)
    if d.max()>LIMIT:return 0.
    q=np.abs(a*s-b*c)/d
    return math.degrees(math.asin(float(np.clip(q.min(),0,1))))
def scan(name,al,ah,bl,bh,step):
    aa=np.arange(al,ah+1e-9,step); bb=np.arange(bl,bh+1e-9,step); best=-1.; at=(None,None); hits=0
    for a in aa:
        for b in bb:
            g=score(float(a),float(b)); hits+=g>=40
            if g>best: best,at=g,(float(a),float(b))
    row={"stage":name,"a_lo_m":al,"a_hi_m":ah,"b_lo_m":bl,"b_hi_m":bh,"step_m":step,"a_grid_count":len(aa),"b_grid_count":len(bb),"candidate_count":len(aa)*len(bb),"alpha_grid_points":801,"hit_ge_40_count":hits,"best_a_m":at[0],"best_b_m":at[1],"best_guaranteed_phi_deg":best}
    e=EXPECTED[name]; assert row["candidate_count"]==e[3] and hits==0 and abs(best-e[0])<2e-6 and at==(e[1],e[2]),row
    return row
def main():
    rows=[scan(*x) for x in STAGES]
    p=ROOT/"f4_search_hierarchy.csv"
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    mpl.rcParams.update({"font.family":["Microsoft YaHei","SimHei","sans-serif"],"axes.unicode_minus":False,"svg.fonttype":"none","pdf.fonttype":42,"font.size":9})
    navy,teal,orange,gray,ink="#233B72","#147B7E","#B26028","#9AA4AD","#20252B"
    fig,axs=plt.subplots(1,2,figsize=(7.2,3.3),gridspec_kw={"width_ratios":[1.25,1]},facecolor="white");fig.subplots_adjust(left=.09,right=.97,bottom=.20,top=.88,wspace=.28)
    ax=axs[0]; colors=[gray,teal,navy,"#6F7E89"]
    for row,col in zip(rows,colors):
        rect=Rectangle((row["a_lo_m"],row["b_lo_m"]),row["a_hi_m"]-row["a_lo_m"],row["b_hi_m"]-row["b_lo_m"],fill=False,ec=col,lw=1.3,ls="--" if row["stage"]=="wide" else "-");ax.add_patch(rect)
        ax.scatter(row["best_a_m"],row["best_b_m"],s=20,color=col,zorder=4)
    ax.annotate("wide",(-760,1320),color="#6F7E89",fontsize=7);ax.annotate("coarse",(-330,1160),color=gray,fontsize=7);ax.annotate("fine",(680,710),color=teal,fontsize=7);ax.annotate("ultra",(773,650),color=navy,fontsize=7)
    ax.set(xlabel="沿测向位移 a（m）",ylabel="横向偏移 b（m）",xlim=(-900,2500),ylim=(-40,1460));ax.spines[["top","right"]].set_visible(False);ax.grid(color="#E3E7EA",lw=.6);ax.text(-.12,1.03,"(a) 分层搜索范围",transform=ax.transAxes,fontweight="bold")
    ax=axs[1]; names=[r["stage"] for r in rows];val=[r["best_guaranteed_phi_deg"] for r in rows]; y=np.arange(4)
    ax.hlines(y,39.0,val,color="#D9DEE2",lw=2);ax.scatter(val,y,s=46,c=colors,zorder=3);ax.axvline(40,color=orange,lw=1.2,ls=(0,(3,2)));ax.text(40.03,3.35,"40° 目标",color=orange,fontsize=8);ax.set(yticks=y,yticklabels=["coarse  6,771 点","fine  3,721 点","ultra  2,401 点","wide  2,916 点"],xlim=(39.0,40.12),ylim=(-.55,3.75),xlabel="各层最高观测交会角 φ（°）")
    for yy,v in zip(y,val):ax.text(v+.025,yy,f"{v:.4f}°",va="center",fontsize=8,color=ink)
    ax.text(39.02,-.43,"所有层：≥40° 点数 = 0",color=orange,fontsize=8,fontweight="bold");ax.spines[["top","right","left"]].set_visible(False);ax.grid(axis="x",color="#E3E7EA",lw=.6);ax.tick_params(axis="y",length=0);ax.text(-.15,1.03,"(b) 最高观测值",transform=ax.transAxes,fontweight="bold")
    for ext,kw in (("png",{"dpi":600}),("svg",{}),("pdf",{})):fig.savefig(OUT/f"F4_全域数值上界.{ext}",bbox_inches="tight",facecolor="white",**kw)
    (ROOT/"f4_manifest.json").write_text(json.dumps({"alpha_grid_points":801,"r_endpoints_m":[5,1500],"candidate_evaluations":sum(r["candidate_count"] for r in rows),"status":"external_ai_review_candidate","rows":rows},ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__":main()
