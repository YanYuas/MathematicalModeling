# -*- coding: utf-8 -*-
"""
整数规划 · 算法对比实验
========================
六层钻研法 · 第6层：对比创新

对比三种算法在0-1背包问题上的性能：
1. 分支定界法（深度优先 DFS）
2. 分支定界法（最佳优先 Best-First）
3. 割平面法（Gomory Cut）
4. 暴力枚举（仅小规模）

测试指标：最优值、运行时间、搜索节点数/割平面数
"""

import numpy as np
import time
import sys
import os

# 导入我们自己实现的算法（在02_算法实现手札目录）
code_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '02_算法实现手札', '00_手动实现详解')
sys.path.insert(0, os.path.normpath(code_dir))
from importlib import import_module

bb_module = import_module('03_分支定界法_手动实现')
cp_module = import_module('04_割平面法_手动实现')


# ============================================================
# 第一部分：生成测试问题
# ============================================================
def generate_knapsack(n, seed=42):
    """
    生成随机0-1背包问题
    
    参数：
        n: 物品数
        seed: 随机种子
    
    返回：
        (v, w, W): 价值、重量、容量
    """
    np.random.seed(seed)
    v = np.random.randint(5, 25, n)    # 价值5-24
    w = np.random.randint(2, 10, n)    # 重量2-9
    W = int(sum(w) * 0.4)               # 容量约为总重量的40%
    return v, w, W


# ============================================================
# 第二部分：各算法求解函数
# ============================================================
def solve_branch_and_bound(v, w, W, method='best_first'):
    """分支定界法求解背包问题"""
    n = len(v)
    c = -v  # 最大化转最小化
    A_ub = w.reshape(1, -1)
    b_ub = np.array([W])
    lb = np.zeros(n)
    ub = np.ones(n)
    
    start = time.time()
    result = bb_module.branch_and_bound(
        c, A_ub=A_ub, b_ub=b_ub, lb=lb, ub=ub,
        method=method, max_nodes=50000, verbose=False)
    elapsed = time.time() - start
    
    return {
        'obj': -result['obj'] if result['obj'] is not None else None,
        'time': elapsed,
        'nodes': result['nodes_explored'],
        'status': result['status']
    }


def solve_cutting_plane(v, w, W):
    """割平面法求解背包问题"""
    n = len(v)
    # 0-1约束需要显式写出 x_i ≤ 1
    A = [w.tolist()] + [[1 if j == i else 0 for j in range(n)] for i in range(n)]
    b = [W] + [1] * n
    c = v.tolist()
    
    start = time.time()
    result = cp_module.cutting_plane_method(A, b, c, max_cuts=100, verbose=False)
    elapsed = time.time() - start
    
    return {
        'obj': result['obj'],
        'time': elapsed,
        'cuts': result['num_cuts'],
        'status': result['status']
    }


def solve_brute_force(v, w, W):
    """暴力枚举求解背包问题（仅小规模）"""
    n = len(v)
    best_obj = 0
    best_x = None
    
    start = time.time()
    # 枚举所有2^n种组合
    for mask in range(1 << n):
        total_w = 0
        total_v = 0
        for i in range(n):
            if mask & (1 << i):
                total_w += w[i]
                total_v += v[i]
        if total_w <= W and total_v > best_obj:
            best_obj = total_v
            best_x = mask
    elapsed = time.time() - start
    
    return {
        'obj': best_obj,
        'time': elapsed,
        'combos': 1 << n,
        'status': 'optimal'
    }


# ============================================================
# 第三部分：主实验
# ============================================================
def run_experiment():
    """运行对比实验"""
    print("=" * 80)
    print("整数规划算法对比实验")
    print("测试问题：0-1背包问题（随机生成，容量=总重量40%）")
    print("=" * 80)
    
    # 测试规模
    sizes = [5, 8, 10, 12, 15, 18]
    
    results = []
    
    for n in sizes:
        print(f"\n{'─' * 80}")
        print(f"问题规模：n = {n} 件物品")
        print(f"{'─' * 80}")
        
        v, w, W = generate_knapsack(n)
        print(f"价值：{v.tolist()}")
        print(f"重量：{w.tolist()}")
        print(f"容量：{W}（总重量={sum(w)}）")
        
        row = {'n': n}
        
        # 1. 暴力枚举（仅n≤12）
        if n <= 12:
            r = solve_brute_force(v, w, W)
            row['brute'] = r
            print(f"\n  暴力枚举：最优值={r['obj']}, 时间={r['time']:.4f}s, 组合数={r['combos']}")
        else:
            print(f"\n  暴力枚举：跳过（组合数={1<<n}太多）")
        
        # 2. 分支定界 DFS
        r = solve_branch_and_bound(v, w, W, method='dfs')
        row['bb_dfs'] = r
        print(f"  分支定界(DFS)：最优值={r['obj']}, 时间={r['time']:.4f}s, 节点数={r['nodes']}, 状态={r['status']}")
        
        # 3. 分支定界 Best-First
        r = solve_branch_and_bound(v, w, W, method='best_first')
        row['bb_bf'] = r
        print(f"  分支定界(Best-First)：最优值={r['obj']}, 时间={r['time']:.4f}s, 节点数={r['nodes']}, 状态={r['status']}")
        
        # 4. 割平面法
        try:
            r = solve_cutting_plane(v, w, W)
            row['cutting'] = r
            print(f"  割平面法：最优值={r['obj']}, 时间={r['time']:.4f}s, 割平面数={r['cuts']}, 状态={r['status']}")
        except Exception as e:
            print(f"  割平面法：失败 - {e}")
            row['cutting'] = None
        
        results.append(row)
    
    return results


# ============================================================
# 第四部分：结果汇总与分析
# ============================================================
def print_summary(results):
    """打印汇总表格"""
    print("\n" + "=" * 80)
    print("实验结果汇总")
    print("=" * 80)
    
    # 表头
    print(f"{'n':>4} | {'暴力枚举':>16} | {'BB(DFS)':>20} | {'BB(BestFirst)':>20} | {'割平面法':>18}")
    print("-" * 90)
    
    for r in results:
        n = r['n']
        
        # 暴力枚举
        if 'brute' in r and r['brute']:
            brute_str = f"{r['brute']['obj']:>4}/{r['brute']['time']:.3f}s"
        else:
            brute_str = "N/A"
        
        # BB DFS
        dfs = r['bb_dfs']
        dfs_str = f"{dfs['obj']:>4}/{dfs['time']:.3f}s/{dfs['nodes']:>5}节点"
        
        # BB Best-First
        bf = r['bb_bf']
        bf_str = f"{bf['obj']:>4}/{bf['time']:.3f}s/{bf['nodes']:>5}节点"
        
        # 割平面
        if r['cutting']:
            cp = r['cutting']
            cp_str = f"{cp['obj']:>4}/{cp['time']:.3f}s/{cp['cuts']:>3}割"
        else:
            cp_str = "N/A"
        
        print(f"{n:>4} | {brute_str:>16} | {dfs_str:>20} | {bf_str:>20} | {cp_str:>18}")
    
    print("\n" + "=" * 80)
    print("结论分析")
    print("=" * 80)
    
    print("""
1. 暴力枚举：n=12时需要4096次组合，n=15时32768次，n=20时超过100万次，指数增长不可行。

2. 分支定界法：
   - Best-First通常比DFS少搜索一个数量级的节点（因为优先处理下界好的节点，剪枝更有效）
   - DFS的优势是内存小，能快速找到可行解（提高上界），但可能在差分支上浪费时间
   - 实际中常用混合策略：先用DFS快速找好解，再用Best-First精确求解

3. 割平面法：
   - 不需要搜索树，内存小
   - 但可能需要很多个割平面才能收敛（简单问题甚至需要10+个）
   - 数值稳定性较差，系数可能增长
   - 现代求解器很少单独使用，通常作为分支定界的辅助（Branch and Cut）

4. 最优值一致性：所有算法得到的最优值应该一致（验证正确性）。

5. 实践建议：
   - 小规模（n<20）：分支定界法足够快
   - 中规模（n<100）：分支定界+割平面（Branch and Cut）
   - 大规模（n>100）：启发式算法（GA/SA/PSO）或专业求解器（Gurobi/CPLEX）
   - 特殊结构（指派/运输）：专用算法比通用IP快几个数量级
""")


if __name__ == '__main__':
    results = run_experiment()
    print_summary(results)
