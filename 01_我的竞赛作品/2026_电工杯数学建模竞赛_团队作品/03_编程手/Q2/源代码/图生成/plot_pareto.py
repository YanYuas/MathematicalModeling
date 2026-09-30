"""
Pareto前沿图 — MATLAB风格复刻 + 新数据
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np, csv, os

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei","SimHei","Arial"],
    "axes.unicode_minus": False,
    "svg.fonttype": "none", "pdf.fonttype": 42,
})

out_dir = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(out_dir)

# ====== Load data ======
# GA Pareto
ga_C,ga_S,ga_labels=[],[],[]
with open(os.path.join(parent,'q2_pareto_results.csv'),encoding='utf-8') as f:
    for r in csv.DictReader(f):
        ga_C.append(float(r['覆盖率'])*100)
        ga_S.append(float(r['满意度']))
        ga_labels.append(r['方案'])

ga_C=np.array(ga_C); ga_S=np.array(ga_S)

# Enum Pareto (more complete)
enum_C,enum_S=[],[]
with open(os.path.join(parent,'enum_pareto_results.csv'),encoding='utf-8') as f:
    for r in csv.DictReader(f):
        enum_C.append(float(r['覆盖率'])*100)
        enum_S.append(float(r['满意度']))
enum_C=np.array(enum_C); enum_S=np.array(enum_S)

# ====== FIGURE (MATLAB style) ======
fig,ax=plt.subplots(figsize=(10,7))
ax.set_position([0.10, 0.12, 0.85, 0.82])

# Hot colormap
hot_cmap = plt.cm.hot_r  # reversed hot

# Pareto curve
o=np.argsort(enum_C)
ax.plot(enum_C[o],enum_S[o],'-',color=[0.55,0.55,0.55],lw=1.5,zorder=1)

# GA points with hot colors + labels
sat_min,sat_max = ga_S.min(),ga_S.max()
for i in range(len(ga_C)):
    t = (ga_S[i]-sat_min)/(sat_max-sat_min) if sat_max>sat_min else 0.5
    t = max(0,min(1,t))
    color = hot_cmap(0.2 + 0.7*t)  # skip coldest colors

    ax.scatter(ga_C[i],ga_S[i],s=160,c=[color],edgecolors=[0.25,0.25,0.25],lw=1,zorder=3)

    # Label: alternate left/right to avoid overlap
    if ga_C[i] > 80 and i%2==1:
        dx,ha = -2.5,'right'
    else:
        dx,ha = 2.5,'left'
    ax.text(ga_C[i]+dx,ga_S[i],ga_labels[i],
            fontsize=8,fontweight='bold',color=[0.05,0.05,0.05],
            ha=ha,va='center',zorder=4)

# TOPSIS (red pentagram) — P9 or highest fitness
tops_idx = np.argmax(0.6*ga_C/100 + 0.4*ga_S)
ax.scatter(ga_C[tops_idx],ga_S[tops_idx],s=280,
           c='red',marker='p',lw=2.2,zorder=5,label='TOPSIS推荐')

# Enum backdrop (lighter)
for i in range(len(enum_C)):
    is_ga = any(abs(enum_C[i]-gc)<0.01 and abs(enum_S[i]-gs)<0.005 for gc,gs in zip(ga_C,ga_S))
    if not is_ga:
        ax.scatter(enum_C[i],enum_S[i],s=40,color='#cccccc',
                   edgecolors='none',zorder=0)

# Formatting (MATLAB style)
ax.set_xlabel('覆盖率 (%)',fontsize=13,fontweight='bold')
ax.set_ylabel('满意度',fontsize=13,fontweight='bold')
ax.set_title('Pareto 前沿：覆盖率 vs 满意度',fontsize=15,fontweight='bold')
ax.set_xlim(35,92); ax.set_ylim(0.894,0.992)
ax.grid(True,alpha=0.2); ax.set_axisbelow(True)
ax.tick_params(labelsize=11)

# Legend
ax.legend(loc='lower left',fontsize=10,frameon=False)

# Info box (bottom-left)
info = f'Pareto解: {len(enum_C)}个(枚举) / {len(ga_C)}个(GA)\n覆盖率: {enum_C.min():.1f}% – {enum_C.max():.1f}%\n满意度: {enum_S.min():.4f} – {enum_S.max():.4f}'
ax.text(0.02,0.08,info,transform=ax.transAxes,fontsize=9,color=[0.35,0.35,0.35],
        bbox=dict(boxstyle='round',facecolor='white',alpha=0.7,edgecolor=[0.7,0.7,0.7]),
        va='bottom')

# ====== SAVE ======
out_base = os.path.join(out_dir,'pareto_front')
for fmt,dpi in [('svg',None),('pdf',None),('png',300)]:
    kw={} if dpi is None else {'dpi':dpi}
    fig.savefig(f'{out_base}.{fmt}',bbox_inches='tight',**kw)
print('Pareto MATLAB-style saved')
plt.close(fig)
