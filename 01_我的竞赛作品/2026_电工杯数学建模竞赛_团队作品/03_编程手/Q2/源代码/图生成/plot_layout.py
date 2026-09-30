"""
最优服务站布局全景图 v2 — 美化版
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np, os

mpl.rcParams.update({
    "font.family":"sans-serif",
    "font.sans-serif":["Microsoft YaHei","SimHei","Arial"],
    "axes.unicode_minus":False,
    "svg.fonttype":"none","pdf.fonttype":42,
    "font.size":7,
})

out_dir = os.path.dirname(os.path.abspath(__file__))

# ====== DATA ======
comm = list('ABCDEFGHIJ'); n=10

dist = np.array([
    [0,600,1200,900,1500,1800,1300,700,1100,500],
    [600,0,800,500,1100,1400,900,400,700,300],
    [1200,800,0,700,600,900,500,900,600,700],
    [900,500,700,0,800,1100,600,300,500,400],
    [1500,1100,600,800,0,500,400,1000,500,800],
    [1800,1400,900,1100,500,0,500,1200,700,1100],
    [1300,900,500,600,400,500,0,800,400,600],
    [700,400,900,300,1000,1200,800,0,600,300],
    [1100,700,600,500,500,700,400,600,0,400],
    [500,300,700,400,800,1100,600,300,400,0],
])

daily = np.array([863.4,714.8,1155.3,616.1,960.4,511.7,1068.3,647.2,886.2,772.9])
elderly = np.array([785,672,1018,600,864,520,953,627,812,726])

# Optimal: D(中)E(小)F(小)G(小)J(中) 5站118万
stations = [3,4,5,6,9]
station_scale = ['中型','小型','小型','小型','中型']
station_util = [0.822,0.828,0.793,0.890,0.864]
coverage = {3:[3,7,8], 4:[4], 5:[5,6], 6:[2], 9:[0,1,9]}
comm_st = {}
for s,cs in coverage.items():
    for c in cs: comm_st[c]=s

# Sophisticated palette
COLORS = ['#2E5090','#C05A10','#C05A10','#C05A10','#2E5090']
BG_GRAY = '#D5D5D8'
ARROW_ALPHA = 0.50

# ====== MDS ======
D2 = dist.astype(float)**2
J = np.eye(n)-np.ones((n,n))/n
B = -0.5*J@D2@J
ev,evec = np.linalg.eigh(B)
idx = np.argsort(ev)[::-1]
pos = evec[:,idx[:2]]@np.diag(np.sqrt(np.maximum(ev[idx[:2]],0)))
pos[:,1] = -pos[:,1]

# Scale positions for better spacing
pos = pos * 1.3

# ====== FIGURE ======
fig,ax = plt.subplots(figsize=(10.5,9.5))
plt.subplots_adjust(left=0.08,right=0.92,top=0.90,bottom=0.10)

# 1. Background edges (within 1000m)
for i in range(n):
    for j in range(i+1,n):
        if dist[i,j]<=1000:
            ax.plot([pos[i,0],pos[j,0]],[pos[i,1],pos[j,1]],
                    '-',color=BG_GRAY,lw=0.25,alpha=0.5,zorder=0)

# 2. Service radius circles (dashed)
for si,s in enumerate(stations):
    c=plt.Circle((pos[s,0],pos[s,1]),0.68,fill=False,
                 color=COLORS[si],ls='--',lw=0.6,alpha=0.25)
    ax.add_patch(c)

# 3. Coverage arrows (only label distance once per pair)
for si,s in enumerate(stations):
    for c in coverage[s]:
        if c!=s:
            dx=pos[c,0]-pos[s,0]; dy=pos[c,1]-pos[s,1]
            ln=np.sqrt(dx**2+dy**2)
            ux,uy=dx/ln,dy/ln
            # Start arrow from edge of station marker
            sx=pos[s,0]+ux*0.38; sy=pos[s,1]+uy*0.38
            ex=pos[c,0]-ux*0.38; ey=pos[c,1]-uy*0.38
            ax.annotate('',xy=(ex,ey),xytext=(sx,sy),
                        arrowprops=dict(arrowstyle='->',color=COLORS[si],
                                       lw=2.0,alpha=0.45,
                                       connectionstyle='arc3,rad=0.05'),
                        zorder=3)
            # Distance label at midpoint
            mx=(sx+ex)/2; my=(sy+ey)/2
            ax.text(mx,my,f'{dist[s,c]}m',fontsize=5.8,
                    color='#666',ha='center',va='center',
                    bbox=dict(boxstyle='round,pad=0.06',fc='white',
                              alpha=0.85,ec='none'))

# 4. Community nodes
for i in range(n):
    s = comm_st.get(i,3)
    si = stations.index(s) if s in stations else 0
    is_st = i in stations
    node_sz = 55 + daily[i]/6

    if is_st:
        ax.scatter(pos[i,0],pos[i,1],s=node_sz,c=COLORS[stations.index(i)],
                   marker='D',edgecolors='white',lw=2,zorder=5,alpha=0.95)
    else:
        ax.scatter(pos[i,0],pos[i,1],s=node_sz,c=COLORS[si],
                   marker='o',edgecolors='white',lw=1.5,zorder=4,alpha=0.82)

# 5. Labels
for i in range(n):
    s = comm_st.get(i,3)
    si = stations.index(s) if s in stations else 0
    is_st = i in stations

    if is_st:
        idx = stations.index(i)
        # Station info ABOVE station (visible, not hidden by diamond)
        ax.text(pos[i,0],pos[i,1]+0.50,
                f'{station_scale[idx]}站  u={station_util[idx]:.0%}',
                ha='center',va='bottom',fontsize=6,color='#1a1a2e',
                fontweight='bold',zorder=7)
        # Station letter inside diamond
        ax.text(pos[i,0],pos[i,1],comm[i],ha='center',va='center',
                fontsize=9,fontweight='bold',color='white',zorder=8)
    else:
        # Community letter below node
        ax.text(pos[i,0],pos[i,1]-0.22,comm[i],ha='center',va='top',
                fontsize=9,fontweight='bold',color='#1a1a2e')

# 6. Legend
leg_items=[]
for si,s in enumerate(stations):
    cov_str=','.join(comm[c] for c in coverage[s])
    leg_items.append(Patch(facecolor=COLORS[si],edgecolor='white',lw=0.5,
                     label=f'站{comm[s]}({station_scale[si]}) → {cov_str}'))
legend = ax.legend(handles=leg_items,fontsize=6.2,loc='lower left',
                   ncol=2,title='覆盖关系',title_fontsize=7,
                   columnspacing=0.5,handlelength=1.2,handleheight=0.7,
                   borderpad=0.5,labelspacing=0.3)
legend.get_frame().set_linewidth(0.3)
legend.get_frame().set_alpha(0.85)

# 7. Title & info box
ax.set_title('最优服务站布局方案',fontsize=14,fontweight='bold',
             color='#1a1a2e',pad=15)
info_text = f'D(中)·E(小)·F(小)·G(小)·J(中) | 5站117万 | 覆盖率84.9% | 满意度0.947'
ax.text(0.5,1.01,info_text,transform=ax.transAxes,ha='center',va='bottom',
        fontsize=8.5,color='#555',fontweight='bold')

ax.set_aspect('equal')
ax.set_xticks([]); ax.set_yticks([])
for spine in ax.spines.values(): spine.set_visible(False)

# ====== SAVE ======
out=os.path.join(out_dir,'layout_panorama')
for fmt,dpi in [('svg',None),('pdf',None),('png',300)]:
    kw={} if dpi is None else {'dpi':dpi}
    fig.savefig(f'{out}.{fmt}',bbox_inches='tight',**kw)
print('Layout v2 saved')
plt.close(fig)
