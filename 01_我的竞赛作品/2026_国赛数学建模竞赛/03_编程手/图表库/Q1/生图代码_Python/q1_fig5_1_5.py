# -*- coding: utf-8 -*-
"""
Q1 图5.1-5：顶点过滤示意图
展示角域求交过程中，假交点被过滤、真顶点被保留的过程
基于Q1基准算例：S1=(0,0), S2=(600,0), G=(300,500), ε=1°
"""
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Wedge, FancyArrowPatch
from matplotlib.collections import PatchCollection

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Q1基准算例
S1 = (0, 0)
S2 = (600, 0)
G = (300, 500)
EPS_DEG = 1.0
EPS_RAD = math.radians(EPS_DEG)

# 精确示向度
theta1 = math.degrees(math.atan2(G[1]-S1[1], G[0]-S1[0]))  # 59.036°
theta2 = math.degrees(math.atan2(G[1]-S2[1], G[0]-S2[0]))  # 120.964°

# 角域边界（4条射线）
# S1的角域：[theta1-ε, theta1+ε]
ray1_low = (S1, theta1 - EPS_DEG)   # 58.036°
ray1_high = (S1, theta1 + EPS_DEG)  # 60.036°
# S2的角域：[theta2-ε, theta2+ε]
ray2_low = (S2, theta2 - EPS_DEG)   # 119.964°
ray2_high = (S2, theta2 + EPS_DEG)  # 121.964°

def ray_intersection(p1, deg1, p2, deg2):
    """两条射线的交点"""
    d1 = (math.cos(math.radians(deg1)), math.sin(math.radians(deg1)))
    d2 = (math.cos(math.radians(deg2)), math.sin(math.radians(deg2)))
    det = d1[0]*d2[1] - d1[1]*d2[0]
    if abs(det) < 1e-10:
        return None
    t = ((p2[0]-p1[0])*d2[1] - (p2[1]-p1[1])*d2[0]) / det
    return (p1[0] + t*d1[0], p1[1] + t*d1[1])

def point_in_wedge(p, station, theta_deg, eps_deg):
    """点是否在角域内（带1e-6度容差处理边界）"""
    angle = math.degrees(math.atan2(p[1]-station[1], p[0]-station[0]))
    angle = angle % 360
    tol = 1e-6
    low = ((theta_deg - eps_deg) - tol) % 360
    high = ((theta_deg + eps_deg) + tol) % 360
    if low <= high:
        return low <= angle <= high
    else:
        return angle >= low or angle <= high

# 计算所有4条射线两两的交点（共6个候选交点）
rays = [
    ('S1_low', ray1_low[0], ray1_low[1]),
    ('S1_high', ray1_high[0], ray1_high[1]),
    ('S2_low', ray2_low[0], ray2_low[1]),
    ('S2_high', ray2_high[0], ray2_high[1]),
]

candidates = []
for i in range(len(rays)):
    for j in range(i+1, len(rays)):
        name1, p1, d1 = rays[i]
        name2, p2, d2 = rays[j]
        pt = ray_intersection(p1, d1, p2, d2)
        if pt:
            # 检查是否在两个角域内
            in_w1 = point_in_wedge(pt, S1, theta1, EPS_DEG)
            in_w2 = point_in_wedge(pt, S2, theta2, EPS_DEG)
            is_vertex = in_w1 and in_w2
            candidates.append({
                'name': f'{name1}×{name2}',
                'point': pt,
                'in_wedge1': in_w1,
                'in_wedge2': in_w2,
                'is_vertex': is_vertex
            })

print("=== 6个候选交点 ===")
for c in candidates:
    status = "✅ 真顶点" if c['is_vertex'] else "❌ 假交点（被过滤）"
    print(f"  {c['name']}: ({c['point'][0]:.2f}, {c['point'][1]:.2f}) "
          f"w1={c['in_wedge1']}, w2={c['in_wedge2']} → {status}")

# 真顶点（4个）
true_vertices = [c['point'] for c in candidates if c['is_vertex']]
# 按极角排序
center = (sum(p[0] for p in true_vertices)/len(true_vertices),
          sum(p[1] for p in true_vertices)/len(true_vertices))
true_vertices.sort(key=lambda p: math.atan2(p[1]-center[1], p[0]-center[0]))

print(f"\n=== 真顶点（{len(true_vertices)}个，按极角排序）===")
for i, v in enumerate(true_vertices):
    print(f"  V{i+1}: ({v[0]:.3f}, {v[1]:.3f})")

# ============ 绘图 ============
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

# ---- 左图：全部6个候选交点（含假交点）----
ax = ax1
# 绘制角域（扇形）
w1 = Wedge(S1, 700, theta1-EPS_DEG, theta1+EPS_DEG, alpha=0.15, color='blue', label='S₁角域 (2°)')
w2 = Wedge(S2, 700, theta2-EPS_DEG, theta2+EPS_DEG, alpha=0.15, color='red', label='S₂角域 (2°)')
ax.add_patch(w1)
ax.add_patch(w2)

# 绘制4条边界射线
for name, p, d in rays:
    end = (p[0] + 700*math.cos(math.radians(d)), p[1] + 700*math.sin(math.radians(d)))
    ax.plot([p[0], end[0]], [p[1], end[1]], 'k-', alpha=0.4, linewidth=0.8)

# 绘制检测点和源
ax.plot(*S1, 'bo', markersize=12, label='S₁')
ax.plot(*S2, 'ro', markersize=12, label='S₂')
ax.plot(*G, 'g*', markersize=18, label='G (源)')

# 绘制全部6个候选交点
for c in candidates:
    if c['is_vertex']:
        ax.plot(*c['point'], 'ko', markersize=10, zorder=5)
    else:
        ax.plot(*c['point'], 'x', color='gray', markersize=12, markeredgewidth=2, zorder=5)
        # 标注假交点
        ax.annotate('假交点', xy=c['point'], xytext=(c['point'][0]+20, c['point'][1]-30),
                   fontsize=9, color='gray', fontstyle='italic')

ax.set_xlim(-100, 700)
ax.set_ylim(300, 650)
ax.set_xlabel('x (m)', fontsize=12)
ax.set_ylabel('y (m)', fontsize=12)
ax.set_title('(a) 4条边界射线两两求交 → 6个候选交点', fontsize=13)
ax.legend(loc='lower left', fontsize=9)
ax.set_aspect('equal')
ax.grid(True, alpha=0.2)

# ---- 右图：过滤后4个真顶点 + 定位区域 ----
ax = ax2
# 绘制角域
w1 = Wedge(S1, 700, theta1-EPS_DEG, theta1+EPS_DEG, alpha=0.1, color='blue')
w2 = Wedge(S2, 700, theta2-EPS_DEG, theta2+EPS_DEG, alpha=0.1, color='red')
ax.add_patch(w1)
ax.add_patch(w2)

# 绘制定位区域（凸多边形）
poly = Polygon(true_vertices, closed=True, alpha=0.4, color='steelblue',
               edgecolor='navy', linewidth=2, label='定位区域 L (凸四边形)')
ax.add_patch(poly)

# 绘制检测点和源
ax.plot(*S1, 'bo', markersize=12, label='S₁')
ax.plot(*S2, 'ro', markersize=12, label='S₂')
ax.plot(*G, 'g*', markersize=18, label='G (源)')

# 标注4个真顶点
for i, v in enumerate(true_vertices):
    ax.plot(*v, 'ko', markersize=10, zorder=5)
    offset = [(15, 15), (15, -25), (-60, -25), (-60, 15)][i]
    ax.annotate(f'V{i+1}\n({v[0]:.1f},{v[1]:.1f})', xy=v,
               xytext=(v[0]+offset[0], v[1]+offset[1]), fontsize=9,
               fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.8))

# 标注过滤规则
ax.text(0.02, 0.98, '过滤规则：\n交点必须同时落在\nS₁和S₂的角域内\n（6个候选→4个真顶点）',
        transform=ax.transAxes, fontsize=10, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

ax.set_xlim(-100, 700)
ax.set_ylim(300, 650)
ax.set_xlabel('x (m)', fontsize=12)
ax.set_ylabel('y (m)', fontsize=12)
ax.set_title('(b) 落在所有角域内 → 4个真顶点构成定位区域', fontsize=13)
ax.legend(loc='lower left', fontsize=9)
ax.set_aspect('equal')
ax.grid(True, alpha=0.2)

fig.suptitle('图5.1-5 顶点过滤：边界射线两两求交 → 角域内过滤 → 凸多边形定位区域',
             fontsize=14, y=1.02)
plt.tight_layout()

savepath = r'D:\YanYuas\MathematicalModeling\HelloMathModeling\03_编程手\Q1\实验结果\figs\fig5_1_5_vertex_filtering.png'
plt.savefig(savepath, dpi=300, bbox_inches='tight')
plt.close()
print(f"\n✅ 图5.1-5已保存: {savepath}")
