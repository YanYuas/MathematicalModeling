# -*- coding: utf-8 -*-
"""visualize_q4.py - 问题四结果可视化
绘制最优布局方案、模块分布、死区分析图
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 最优解数据（从 q4_solve2.py 输出提取）
OPTIMAL_AREA = 24.0
TOTAL_MODULE_AREA = 24.0
DEAD_ZONE_RATIO = 0.0

# 模块定义（原始顶点）
MODULES_ORIGINAL = {
    "b1": {"type": "T", "area": 12, "verts": [(1,0),(3,0),(3,2),(4,2),(4,4),(0,4),(0,2),(1,2)]},
    "b2": {"type": "L", "area": 6,  "verts": [(0,0),(2,0),(2,2),(1,2),(1,4),(0,4)]},
    "b3": {"type": "rect", "area": 2, "verts": [(0,0),(2,0),(2,1),(0,1)]},
    "b4": {"type": "rect", "area": 4, "verts": [(0,0),(1,0),(1,4),(0,4)]},
}

# 最优布局方案（24解，完美平铺，0%死区）
# b1 (rot 0°): off(0,0) WxH=4x4
# b2 (rot 0°): off(-1,0) WxH=2x4
# b3 (rot 90°): off(3,0) WxH=1x2
# b4 (rot 0°): off(4,0) WxH=1x4

def rotate_verts(verts, deg):
    """旋转顶点"""
    if deg == 0:
        return [(float(x), float(y)) for x, y in verts]
    out = []
    for x, y in verts:
        if deg == 90:
            nx, ny = -y, x
        elif deg == 180:
            nx, ny = -x, -y
        elif deg == 270:
            nx, ny = y, -x
        out.append((nx, ny))
    minx = min(v[0] for v in out)
    miny = min(v[1] for v in out)
    return [(x - minx, y - miny) for x, y in out]

def apply_offset(verts, offset):
    """应用偏移"""
    return [(v[0] + offset[0], v[1] + offset[1]) for v in verts]

# 计算放置后的顶点
solution = [
    ("b1", 0, (0, 0)),
    ("b2", 0, (-1, 0)),
    ("b3", 90, (3, 0)),
    ("b4", 0, (4, 0)),
]

placed_modules = []
for mod_id, deg, offset in solution:
    verts_rot = rotate_verts(MODULES_ORIGINAL[mod_id]["verts"], deg)
    verts_final = apply_offset(verts_rot, offset)
    placed_modules.append({
        "id": mod_id,
        "type": MODULES_ORIGINAL[mod_id]["type"],
        "area": MODULES_ORIGINAL[mod_id]["area"],
        "rotation": deg,
        "offset": offset,
        "vertices": verts_final
    })

# 图1：最优布局方案
fig, ax = plt.subplots(1, 1, figsize=(8, 8))

colors = {"b1": "#FF6B6B", "b2": "#4ECDC4", "b3": "#45B7D1", "b4": "#FFA07A"}
labels = {"b1": "模块1 (T型, 12)", "b2": "模块2 (L型, 6)",
          "b3": "模块3 (矩形, 2)", "b4": "模块4 (矩形, 4)"}

for mod in placed_modules:
    poly = Polygon(mod["vertices"], closed=True,
                   facecolor=colors[mod["id"]], edgecolor='black',
                   linewidth=2, alpha=0.7)
    ax.add_patch(poly)

    # 添加标签（质心位置）
    centroid_x = np.mean([v[0] for v in mod["vertices"]])
    centroid_y = np.mean([v[1] for v in mod["vertices"]])
    ax.text(centroid_x, centroid_y, labels[mod["id"]],
            ha='center', va='center', fontsize=10, fontweight='bold')

# 绘制包络矩形（动态计算）
all_verts = []
for mod in placed_modules:
    all_verts.extend(mod["vertices"])
minx = min(v[0] for v in all_verts)
miny = min(v[1] for v in all_verts)
maxx = max(v[0] for v in all_verts)
maxy = max(v[1] for v in all_verts)
W = maxx - minx
H = maxy - miny
ax.add_patch(patches.Rectangle((minx, miny), W, H,
                                linewidth=3, edgecolor='red',
                                facecolor='none', linestyle='--',
                                label=f'包络矩形 ({W:.0f}×{H:.0f}={W*H:.0f})'))

ax.set_xlim(-2, 6)
ax.set_ylim(-1, 5)
ax.set_aspect('equal')
ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
ax.set_xlabel('X 坐标', fontsize=12)
ax.set_ylabel('Y 坐标', fontsize=12)
ax.legend(loc='upper right', fontsize=10)
ax.set_title('', fontsize=14, fontweight='bold')  # 标题留空，由论文caption提供

plt.tight_layout()
plt.savefig('figures/Q4_optimal_layout.pdf', dpi=300, bbox_inches='tight')
print("[OK] 已生成: figures/Q4_optimal_layout.pdf")
plt.close()

# 图2：面积对比
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# 左图：面积堆叠柱状图
categories = ['模块总面积', '包络面积']
module_areas = [TOTAL_MODULE_AREA, TOTAL_MODULE_AREA]
dead_zones = [0, OPTIMAL_AREA - TOTAL_MODULE_AREA]

x = np.arange(len(categories))
width = 0.5

bars1 = ax1.bar(x, module_areas, width, label='有效面积', color='#4ECDC4')
bars2 = ax1.bar(x, dead_zones, width, bottom=module_areas,
                label='死区', color='#FFB6B9')

ax1.set_ylabel('面积', fontsize=12)
ax1.set_xticks(x)
ax1.set_xticklabels(categories, fontsize=11)
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3, axis='y')

# 添加数值标签
for i, (m, d) in enumerate(zip(module_areas, dead_zones)):
    if m > 0:
        ax1.text(i, m/2, f'{m:.0f}', ha='center', va='center',
                fontsize=11, fontweight='bold', color='white')
    if d > 0:
        ax1.text(i, m + d/2, f'{d:.0f}', ha='center', va='center',
                fontsize=11, fontweight='bold', color='white')

# 右图：饼图显示死区占比
sizes = [TOTAL_MODULE_AREA, OPTIMAL_AREA - TOTAL_MODULE_AREA]
labels_pie = [f'有效面积\n{TOTAL_MODULE_AREA:.0f} ({100-DEAD_ZONE_RATIO:.0f}%)',
              f'死区\n{OPTIMAL_AREA - TOTAL_MODULE_AREA:.0f} ({DEAD_ZONE_RATIO:.0f}%)']
colors_pie = ['#4ECDC4', '#FFB6B9']
explode = (0, 0.1)

ax2.pie(sizes, explode=explode, labels=labels_pie, colors=colors_pie,
        autopct='', shadow=True, startangle=90)
ax2.axis('equal')

plt.tight_layout()
plt.savefig('figures/Q4_area_comparison.pdf', dpi=300, bbox_inches='tight')
print("[OK] 已生成: figures/Q4_area_comparison.pdf")
plt.close()

# 图3：模块尺寸与朝向
fig, ax = plt.subplots(1, 1, figsize=(10, 6))

module_names = ['模块1 (T型)', '模块2 (L型)', '模块3 (矩形)', '模块4 (矩形)']
module_areas_list = [12, 6, 2, 4]
rotations = [0, 0, 0, 90]

x = np.arange(len(module_names))
bars = ax.bar(x, module_areas_list, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'],
              edgecolor='black', linewidth=1.5)

# 添加旋转角度标注
for i, (bar, rot) in enumerate(zip(bars, rotations)):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
            f'面积: {module_areas_list[i]}\n旋转: {rot}°',
            ha='center', va='bottom', fontsize=10)

ax.set_ylabel('面积', fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(module_names, fontsize=11)
ax.set_ylim(0, 14)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('figures/Q4_module_properties.pdf', dpi=300, bbox_inches='tight')
print("[OK] 已生成: figures/Q4_module_properties.pdf")
plt.close()

print(f"\n=== 问题四结果摘要 ===")
print(f"最小包络面积: {OPTIMAL_AREA:.1f}")
print(f"模块总面积: {TOTAL_MODULE_AREA:.1f}")
print(f"死区面积: {OPTIMAL_AREA - TOTAL_MODULE_AREA:.1f}")
print(f"死区占比: {DEAD_ZONE_RATIO:.1f}%")
print(f"包络尺寸: 6×4 (完美平铺)")
