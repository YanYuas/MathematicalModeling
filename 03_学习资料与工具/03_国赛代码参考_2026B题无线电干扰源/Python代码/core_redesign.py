"""Publication-sized Q1 mechanism plates, computed from the reference geometry."""
from pathlib import Path
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Arc, FancyBboxPatch
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'source'))
import q1_main as model

INK, BLUE, TEAL, ORANGE = '#203044', '#355F9D', '#168D98', '#D77B36'
MUTED, GRID, FILL = '#677788', '#DFE6ED', '#E6F0F3'
WIDTH = 183 / 25.4
RESULTS = {}


def canvas(height, widths):
    fig, axes = plt.subplots(1, len(widths), figsize=(WIDTH, height),
                             gridspec_kw={'width_ratios': widths})
    fig.subplots_adjust(left=.075, right=.985, bottom=.22, top=.83, wspace=.38)
    return fig, np.atleast_1d(axes)


def panel(ax, letter, title):
    ax.text(0, 1.12, letter, transform=ax.transAxes, fontsize=11, weight='bold', color=INK)
    ax.annotate(title, (0, 1.12), xycoords='axes fraction', xytext=(15,0), textcoords='offset points', fontsize=8, color=INK)


def axes_style(ax, x='x (m)', y='y (m)', equal=True):
    ax.set_xlabel(x, fontsize=8); ax.set_ylabel(y, fontsize=8)
    ax.tick_params(labelsize=7, length=3, colors=MUTED)
    ax.spines[['top','right']].set_visible(False)
    ax.spines[['bottom','left']].set_color(GRID)
    if equal: ax.set_aspect('equal')
    ax.set_axisbelow(True)


def note(fig, text):
    fig.text(.075, .055, text, fontsize=7.5, color=MUTED)


def geometry(stations=None, eps=1.):
    target = np.array([300., 500.])
    if stations is None: stations = np.array([[0.,0.],[600.,0.]])
    bearings = [np.degrees(np.arctan2(*(target-s)[::-1])) for s in stations]
    wedges = model.build_wedges(list(stations), bearings, eps)
    vertices = model.candidate_vertices(wedges)
    poly = model.convex_hull(vertices)
    d, ends = model.diameter_bruteforce(poly)
    dc, _ = model.diameter_rotating_calipers(poly)
    centre, r = model.mec_bruteforce(poly.vertices)
    _, rw = model.welzl_mec(poly.vertices)
    assert np.isclose(d, dc) and np.isclose(r, rw)
    assert d/2-1e-8 <= r <= d/np.sqrt(3)+1e-8
    return target, wedges, np.array(poly.vertices), d, np.array(ends), centre, r


def filled(ax, vertices, color=TEAL, alpha=.15):
    ax.add_patch(Polygon(vertices, closed=True, fc=color, ec=color, alpha=alpha, lw=1))
    vv = np.vstack([vertices, vertices[0]])
    ax.plot(*vv.T, color=color, lw=1.25)


def figure1(save):
    fig, axs = canvas(3.3, [1.2,1])
    ax, zoom = axs
    theta, display_eps = 38., 12.
    u = model.unit_vector(theta)
    # Abstract schematic, deliberately without metric axes; true 1-degree view at right.
    for ang, color, ls in [(theta-display_eps,BLUE,'--'),(theta,ORANGE,'-'),(theta+display_eps,BLUE,'--')]:
        end=3.1*model.unit_vector(ang)
        ax.annotate('',xy=end,xytext=(0,0),arrowprops=dict(arrowstyle='->',color=color,lw=1.25,linestyle=ls))
    ax.add_patch(Polygon(np.array([[0,0],3*model.unit_vector(theta-display_eps),3*model.unit_vector(theta+display_eps)]),fc=BLUE,ec='none',alpha=.08))
    ax.add_patch(Arc((0,0),1.6,1.6,theta1=theta-display_eps,theta2=theta+display_eps,color=TEAL,lw=1))
    ax.text(.6,.62,r'$2\varepsilon$',color=TEAL,fontsize=10)
    ax.scatter(0,0,s=40,color=INK,zorder=5); ax.text(-.16,-.25,r'$S_i$',fontsize=10)
    ax.text(2.1,2.5,r'$\theta_i+\varepsilon$',color=BLUE,fontsize=9)
    ax.text(2.83,1.21,r'$\theta_i-\varepsilon$',color=BLUE,fontsize=9)
    ax.text(2.68,1.95,r'$\theta_i$',color=ORANGE,fontsize=9)
    ax.set(xlim=(-.3,3.6),ylim=(-.35,2.8)); ax.set_aspect('equal'); ax.axis('off')
    panel(ax,'a','角域机制 · 开角夸张示意')
    distance=np.linspace(0,600,200); width=distance*np.tan(np.deg2rad(1))
    zoom.fill_between(distance,-width,width,color=BLUE,alpha=.12)
    zoom.plot(distance,width,color=BLUE,lw=1.3); zoom.plot(distance,-width,color=BLUE,lw=1.3)
    zoom.axhline(0,color=ORANGE,lw=1,ls='--')
    zoom.set(xlim=(0,620),ylim=(-14,14),xticks=[0,300,600],yticks=[-10,0,10])
    axes_style(zoom,'沿示向轴距离 (m)','横向偏差 (m)',False)
    panel(zoom,'b',r'真实误差尺度 · $\varepsilon=1^\circ$')
    note(fig,'方向约束随距离扩展；单站角域沿射线方向无界。')
    save(fig,'fig5_1_1_single_station_wedge')


def figure2(save):
    g, wedges, v, d, ends, c, r = geometry()
    RESULTS['baseline'] = dict(vertices=v.tolist(),D=d,R=r,gamma=2*r/d)
    fig,(ax,zoom)=canvas(3.5,[1,1.22])
    for idx,(w,col) in enumerate(zip(wedges,[BLUE,TEAL])):
        s=w.apex; rr=[s+730*q.direction for q in [w.ray_minus,w.ray_plus]]
        filled(ax,np.array([s,*rr]),col,.1)
        ax.plot([s[0],g[0]],[s[1],g[1]],color=col,lw=.8,ls='--')
        ax.scatter(*s,marker='s',s=25,color=col)
        ax.annotate(rf'$S_{idx+1}$',s,xytext=(0,-14),textcoords='offset points',ha='center',color=col)
    ax.scatter(*g,s=30,color=ORANGE,zorder=5)
    ax.annotate('G',g,xytext=(8,3),textcoords='offset points',color=ORANGE)
    ax.set(xlim=(-80,680),ylim=(-70,670),xticks=[0,300,600],yticks=[0,300,600]); axes_style(ax)
    panel(ax,'a','两站角域交会')
    vv=v-g; ee=ends-g; cc=c-g
    filled(zoom,vv)
    zoom.add_patch(Circle(cc,r,fill=False,ec=BLUE,lw=1.2,ls=(0,(4,2))))
    zoom.plot(*ee.T,color=ORANGE,lw=2)
    zoom.scatter(*vv.T,color=TEAL,s=18,zorder=4)
    zoom.scatter(0,0,s=20,marker='+',color=INK,zorder=5)
    for i,p in enumerate(vv):
        zoom.annotate(rf'$V_{i+1}$',p,xytext=(6 if p[0]>=0 else -16,5),textcoords='offset points',fontsize=7)
    zoom.set(xlim=(-28,28),ylim=(-25,27),xticks=[-20,0,20],yticks=[-20,0,20])
    axes_style(zoom,r'$x-300$ (m)',r'$y-500$ (m)'); panel(zoom,'b','交集放大 · 直径与最小包围圆')
    fig.legend(handles=[Line2D([],[],color=TEAL,label='可行区域边界'),Line2D([],[],color=ORANGE,lw=2,label='直径'),Line2D([],[],color=BLUE,ls='--',label='最小包围圆')],loc='lower center',bbox_to_anchor=(.53,.10),ncol=3,fontsize=7,frameon=False)
    note(fig,rf'$D={d:.3f}$ m   |   $R_{{\mathrm{{MEC}}}}={r:.3f}$ m   |   $\gamma=2R_{{\mathrm{{MEC}}}}/D={2*r/d:.3f}$')
    save(fig,'fig5_1_10_geometry_construction')


def figure3(save):
    v=np.array([[0.,0.],[100.,0.],[50.,50*np.sqrt(3)]])
    fig,axs=canvas(3.45,[1,1])
    for ax,letter,title,centre,r,col in [(axs[0],'a','直径圆不能覆盖',(50,0),50,ORANGE),(axs[1],'b','最小包围圆覆盖全部顶点',(50,50/np.sqrt(3)),100/np.sqrt(3),TEAL)]:
        filled(ax,v,BLUE,.08)
        ax.add_patch(Circle(centre,r,fc='none',ec=col,lw=1.5,ls='--' if letter=='a' else '-'))
        ax.plot([0,100],[0,0],color=ORANGE,lw=2)
        ax.scatter(*v.T,color=INK,s=20,zorder=5)
        for p,label,off in zip(v,['A','B','C'],[(-10,-12),(6,-12),(0,8)]):
            ax.annotate(label,p,xytext=off,textcoords='offset points',fontsize=8)
        ax.set(xlim=(-17,117),ylim=(-73,105)); ax.set_aspect('equal'); ax.axis('off'); panel(ax,letter,title)
        ax.text(50,-68,rf'$R={r:.3f}$ m',ha='center',fontsize=9,color=col)
    axs[0].annotate('未覆盖的顶点',v[2],xytext=(75,64),fontsize=7,color=ORANGE,arrowprops={'arrowstyle':'->','color':ORANGE,'lw':.8})
    note(fig,r'等边三角形：$D=100$ m，$R_{\mathrm{MEC}}=D/\sqrt{3}>D/2$；直径圆覆盖不是一般性质。')
    save(fig,'fig5_1_3_jung_counterexample')


def figure4(save):
    fig,(geo,ax)=canvas(3.25,[1,1.3])
    g,_,v,d,ends,c,r=geometry()
    filled(geo,v-c); geo.add_patch(Circle((0,0),r,fc='none',ec=TEAL,lw=1.2))
    geo.add_patch(Circle((0,0),d/np.sqrt(3),fc='none',ec=MUTED,ls=':',lw=1))
    geo.plot(*(ends-c).T,color=ORANGE,lw=2)
    geo.set(xlim=(-27,27),ylim=(-27,27));geo.set_aspect('equal');geo.axis('off');panel(geo,'a','基准区域与覆盖半径')
    lo,hi=1,2/np.sqrt(3)
    ax.plot([lo,hi],[0,0],color=GRID,lw=15,solid_capstyle='butt')
    ax.scatter([lo,hi],[0,0],s=[85,70],c=[TEAL,BLUE],zorder=3,marker='o')
    ax.text(lo,.25,'基准区域\n下界取等',ha='center',fontsize=8,color=TEAL,linespacing=1.5)
    ax.text(hi,.25,'等边三角形\n上界取等',ha='center',fontsize=8,color=BLUE,linespacing=1.5)
    ax.text(lo,-.24,r'$1$',ha='center',fontsize=10)
    ax.text(hi,-.24,r'$2/\sqrt{3}$',ha='center',fontsize=10)
    ax.text((lo+hi)/2,-.52,r'$\gamma=2R_{\mathrm{MEC}}/D$',ha='center',fontsize=11,color=INK)
    ax.set(xlim=(.965,1.19),ylim=(-.65,.8));ax.axis('off');panel(ax,'b','用无量纲覆盖比连接两个极端')
    note(fig,r'Jung 夹逼：$D/2\leq R_{\mathrm{MEC}}\leq D/\sqrt{3}$。左图同心上界圆仅用于半径比较。')
    save(fig,'fig5_1_4_jung_sandwich')


def figure5(save):
    stations=np.array([[0.,0.],[600.,0.],[300.,-100.]])
    g,wedges,v,d,ends,c,r=geometry(stations,eps=2)
    raw=[]
    for i,w in enumerate(wedges):
        for z in wedges[i+1:]:
            for a in [w.ray_minus,w.ray_plus]:
                for b in [z.ray_minus,z.ray_plus]:
                    p=model.intersect_rays(a,b)
                    if p is not None:raw.append(p)
    raw=np.array(raw);valid=np.array([all(w.contains(p) for w in wedges) for p in raw])
    lower=(raw-g).min(axis=0); upper=(raw-g).max(axis=0); margin=.15*(upper-lower)
    RESULTS['filtering']=dict(raw=len(raw),accepted=int(valid.sum()),rejected=int((~valid).sum()),vertices=v.tolist())
    fig,axs=canvas(3.35,[1,1])
    for ax,letter,title in zip(axs,['a','b'],['12 个候选交点 · 全景','全角域过滤 · 局部放大']):
        for w,col in zip(wedges,[BLUE,TEAL,MUTED]):
            for ray in [w.ray_minus,w.ray_plus]:
                pp=np.array([ray.origin,ray.origin+1000*ray.direction])-g
                ax.plot(*pp.T,color=col,lw=.7,alpha=.65)
        if letter=='a': ax.scatter(*(raw-g).T,s=25,facecolors='white',edgecolors=BLUE,zorder=5)
        else:
            filled(ax,v-g)
            ax.scatter(*(raw[~valid]-g).T,marker='x',color=ORANGE,s=25,lw=1,zorder=5)
            ax.scatter(*(raw[valid]-g).T,color=TEAL,s=24,zorder=5)
        if letter=='a':
            ax.set(xlim=(-90,90),ylim=(lower[1]-margin[1],upper[1]+margin[1]),xticks=[-50,0,50],yticks=[-50,0,50,100])
        else:
            ax.set(xlim=(-42,42),ylim=(-48,48),xticks=[-40,0,40],yticks=[-40,0,40])
        axes_style(ax,r'$x-300$ (m)',r'$y-500$ (m)');panel(ax,letter,title)
    fig.legend(handles=[Line2D([],[],marker='o',color=TEAL,ls='',label='保留'),Line2D([],[],marker='x',color=ORANGE,ls='',label='剔除')],loc='lower center',bbox_to_anchor=(.53,.10),ncol=2,frameon=False,fontsize=7)
    note(fig,rf'三站示例 · $\varepsilon=2^\circ$：{len(raw)} 个候选交点 → {valid.sum()} 个可行顶点；逐点检验 $P\in\bigcap_i W_i$。')
    save(fig,'fig5_1_5_vertex_filtering')


def flowchart(save):
    fig,ax=plt.subplots(figsize=(WIDTH,5.1));fig.subplots_adjust(left=.02,right=.98,top=.98,bottom=.02)
    ax.set(xlim=(0,10),ylim=(0,10));ax.axis('off')
    def box(x,y,w,h,text,fill=FILL,edge=BLUE):
        ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle='round,pad=.02,rounding_size=.08',fc=fill,ec=edge,lw=.8))
        ax.text(x,y,text,ha='center',va='center',fontsize=7.5,color=INK,linespacing=1.5)
    def arrow(a,b,label=None):
        ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'-|>','lw':.8,'color':MUTED})
        if label: ax.text((a[0]+b[0])/2+.08,(a[1]+b[1])/2+.08,label,fontsize=7,color=MUTED)
    def diamond(y,text):
        ax.add_patch(Polygon([[4,y+.43],[5.65,y],[4,y-.43],[2.35,y]],fc='#F9EDD9',ec=ORANGE,lw=.8))
        ax.text(4,y,text,ha='center',va='center',fontsize=7.5)
    ax.text(.1,9.65,'a',weight='bold',fontsize=11,color=INK)
    ax.text(.55,9.65,'问题一求解流程',fontsize=9,color=INK)
    box(4,9,4.5,.55,r'输入 $S_i,\ \theta_i,\ \varepsilon$ → 构造角域 $W_i$')
    diamond(7.9,'角域交集非空？');arrow((4,8.72),(4,8.33))
    box(8,7.9,2.4,.6,'无可行定位区域',fill='#FBF2EA',edge=ORANGE);arrow((5.65,7.9),(6.78,7.9),'否')
    diamond(6.55,'交集有界？');arrow((4,7.47),(4,6.98),'是')
    box(8,6.55,2.4,.6,'无界区域\n无有限覆盖半径',fill='#FBF2EA',edge=ORANGE);arrow((5.65,6.55),(6.78,6.55),'否')
    box(4,5.23,4.5,.66,'枚举边界射线交点与站址候选\n保留满足全部角域约束的点');arrow((4,6.12),(4,5.56),'是')
    box(4,4.15,4.5,.6,'去重与凸包构造\n识别点、线段或凸多边形');arrow((4,4.9),(4,4.45))
    box(2.1,2.9,3.1,.8,'直径 D\n旋转卡壳 / 点对枚举');box(6.5,2.9,3.4,.8,r'最小包围圆 $R_{\mathrm{MEC}}$'+'\nWelzl / 支撑点枚举')
    arrow((3,3.85),(2.1,3.3));arrow((5,3.85),(6.5,3.3))
    box(4,1.53,5.1,.9,r'交叉复核：$D/2\leq R_{\mathrm{MEC}}\leq D/\sqrt{3}$'+'\nThales 顶点检验 → 直径圆覆盖结论',fill='#E6F2EE',edge=TEAL)
    arrow((2.1,2.5),(3,1.98));arrow((6.5,2.5),(5,1.98))
    ax.text(4,.5,'输出区域、直径、最小包围圆及覆盖判定；点区域单独处理。',ha='center',fontsize=7,color=MUTED)
    save(fig,'fig5_1_9_algorithm_flowchart')


def run(save):
    for f in [figure1,figure2,figure3,figure4,figure5,flowchart]:f(save)
    (ROOT/'核心图数值核验.json').write_text(json.dumps(RESULTS,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':
    import q1_figures_v3 as shared
    run(shared.save_figure)
    shared.write_manifest()
