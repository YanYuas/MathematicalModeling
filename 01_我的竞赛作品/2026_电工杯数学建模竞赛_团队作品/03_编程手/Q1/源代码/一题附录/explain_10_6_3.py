"""
展示 10×6×3 需求矩阵的推导过程
demand[i, k, j] = N5[i, j] × demand_pp[k, j]
即：第j类老人，第i个小区的人数 × 第j类老人第k种服务的月均需求
"""
import numpy as np

# ====== 输入矩阵 ======
# N5: 10个小区的三类老人人数 [10 × 3]
N5 = np.array([
    [521, 150, 114],  # A
    [436, 130, 106],  # B
    [669, 199, 150],  # C
    [391, 115,  94],  # D
    [567, 168, 129],  # E
    [345, 101,  74],  # F
    [626, 185, 142],  # G
    [413, 123,  91],  # H
    [533, 159, 120],  # I
    [480, 141, 105],  # J
])

types = ['自理', '半失能', '失能']
services = ['助餐', '日间照料', '康复护理', '健康管理', '助浴', '精神慰藉']

# demand_pp: 6种服务每人月均需求 [6 × 3]
# 行=服务, 列=老人类型(自理/半失能/失能)
demand_pp = np.array([
    [14,    20,  22],    # 助餐
    [ 8,    14,  18],    # 日间照料
    [ 0,     6,  12],    # 康复护理
    [ 2,     4,   6],    # 健康管理
    [ 0,     2,   4],    # 助浴
    [ 0.15,  1,   3],    # 精神慰藉
])

print("=" * 70)
print("N5 (10×3)：每行=小区，每列=老人类型")
print("=" * 70)
print(f"{'小区':>6} {'自理':>6} {'半失能':>6} {'失能':>6}")
for i in range(10):
    print(f"{chr(65+i):>6} {N5[i,0]:>6} {N5[i,1]:>6} {N5[i,2]:>6}")
print(f"合计: 自理={N5[:,0].sum()}, 半失能={N5[:,1].sum()}, 失能={N5[:,2].sum()}")

print()
print("=" * 70)
print("demand_pp (6×3)：每行=服务，每列=老人类型")
print("=" * 70)
print(f"{'服务':>8} {'自理':>8} {'半失能':>8} {'失能':>8}")
for k in range(6):
    print(f"{services[k]:>8} {demand_pp[k,0]:>8.1f} {demand_pp[k,1]:>8.1f} {demand_pp[k,2]:>8.1f}")

# ====== 方法：逐列(逐老人类型)做外积 ======
# 对于老人类型 j:
#   N5[:, j]  → 列向量 (10×1)
#   demand_pp[:, j] → 列向量 (6×1)
#   外积: (10×1) @ (1×6) = (10×6)  或直接 (10×1) * (6×1)^T
#   这给出了第j类老人，所有小区×所有服务的需求矩阵

print()
print("=" * 70)
print("推导过程：逐类型做外积，然后堆叠成 10×6×3")
print("=" * 70)

# 初始化 (10, 6, 3)
demand = np.zeros((10, 6, 3))

for j in range(3):
    col_N = N5[:, j]          # (10,)  → 第j类老人各小区人数
    col_D = demand_pp[:, j]   # (6,)   → 第j类老人各服务月均需求

    # 外积: (10,) × (6,)^T → (10, 6)
    slice_j = np.outer(col_N, col_D)

    demand[:, :, j] = slice_j

    print(f"\n类型{j} ({types[j]})：")
    print(f"  N5[:,{j}] = {col_N}")       # 10个数
    print(f"  demand_pp[:,{j}] = {col_D}")  # 6个数
    print(f"  → 外积得 10×6 矩阵:")
    print(f"  {'服务':>8}", end="")
    for k in range(6):
        print(f" {services[k]:>6}", end="")
    print()
    for i in range(10):
        print(f"  {'小区 '+chr(65+i):>8}", end="")
        for k in range(6):
            print(f" {slice_j[i, k]:>6.0f}", end="")
        print()

# ====== 三页汇总 (按老人类型区分) ======
print()
print("=" * 70)
print("完整 10×6×3 张量：demand[小区, 服务, 老人类型]")
print("=" * 70)

for j in range(3):
    print(f"\n--- 第{j+1}页: {types[j]}老人的需求 (10×6) ---")
    print(f"    {'服务':>8}", end="")
    for k in range(6):
        print(f" {services[k]:>8}", end="")
    print(f" {'行合计':>8}")
    for i in range(10):
        row_sum = demand[i, :, j].sum()
        print(f"    {'小区 '+chr(65+i):>8}", end="")
        for k in range(6):
            print(f" {demand[i, k, j]:>8.1f}", end="")
        print(f" {row_sum:>8.1f}")

# ====== 汇总 (加总三类) ======
print()
print("=" * 70)
print("汇总：demand.sum(axis=2) → 10×6 (加总三类老人)")
print("=" * 70)
demand_2d = demand.sum(axis=2)
print(f"    {'服务':>8}", end="")
for k in range(6):
    print(f" {services[k]:>8}", end="")
print(f" {'行合计':>8}")
for i in range(10):
    row_sum = demand_2d[i, :].sum()
    print(f"    {'小区 '+chr(65+i):>8}", end="")
    for k in range(6):
        print(f" {demand_2d[i, k]:>8.1f}", end="")
    print(f" {row_sum:>8.1f}")

print(f"\n全区域总需求: {demand_2d.sum():.0f} 次/月")

# ====== 对比：广播一次性计算 ======
demand_broadcast = N5[:, np.newaxis, :] * demand_pp[np.newaxis, :, :]
print(f"\n广播法与逐列外积结果一致: {np.allclose(demand, demand_broadcast)}")
