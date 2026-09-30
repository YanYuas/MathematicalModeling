# -*- coding: utf-8 -*-
"""
网络优化 · 算法对比实验
========================
六层钻研法 · 第6层：对比创新

对比内容：
1. Dijkstra朴素版 vs 堆优化版（不同节点数/边数）
2. Prim vs Kruskal（稠密图 vs 稀疏图）
3. Floyd vs Dijkstra（全源最短路：Floyd vs 多次Dijkstra）
4. 不同规模下的性能对比
"""

import numpy as np
import time
import sys
import os

# 导入手动实现
code_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '02_算法实现手札', '00_手动实现详解')
sys.path.insert(0, os.path.normpath(code_dir))
from importlib import import_module
net = import_module('11_网络优化经典算法_手动实现')


def generate_random_graph(n, density=0.3, weighted=True):
    """生成随机无向图"""
    g = net.Graph(n)
    for i in range(n):
        for j in range(i+1, n):
            if np.random.random() < density:
                w = np.random.randint(1, 100) if weighted else 1
                g.add_edge(i, j, w)
    return g


def experiment_dijkstra():
    print("=" * 80)
    print("实验1：Dijkstra 朴素版 vs 堆优化版")
    print("=" * 80)
    
    sizes = [50, 100, 200, 500]
    density = 0.3
    
    print(f"\n{'节点数':>8} {'边数(约)':>10} {'朴素版(ms)':>12} {'堆优化(ms)':>12} {'速度比':>10} {'结果一致':>8}")
    print("-" * 65)
    
    np.random.seed(42)
    for n in sizes:
        g = generate_random_graph(n, density)
        m = sum(len(adj) for adj in g.adj) // 2
        
        start = time.time()
        dist1, _ = net.dijkstra_naive(g, 0)
        t_naive = (time.time() - start) * 1000
        
        start = time.time()
        dist2, _ = net.dijkstra_heap(g, 0)
        t_heap = (time.time() - start) * 1000
        
        consistent = all(abs(a - b) < 1e-6 for a, b in zip(dist1, dist2))
        ratio = t_naive / t_heap if t_heap > 0 else float('inf')
        
        print(f"{n:>8} {m:>10} {t_naive:>12.3f} {t_heap:>12.3f} {ratio:>10.1f}x {'✓' if consistent else '✗':>8}")
    
    print("\n💡 结论：稀疏图上堆优化版更快，稠密图上朴素版可能更快（常数小）。")
    print("   节点数越多，堆优化优势越明显。")


def experiment_mst():
    print("\n" + "=" * 80)
    print("实验2：Prim vs Kruskal（稠密图 vs 稀疏图）")
    print("=" * 80)
    
    configs = [
        (100, 0.1, "稀疏图"),
        (100, 0.5, "中等图"),
        (100, 0.9, "稠密图"),
        (200, 0.1, "稀疏图"),
        (200, 0.5, "中等图"),
        (200, 0.9, "稠密图"),
    ]
    
    print(f"\n{'节点数':>8} {'密度':>6} {'类型':>8} {'Prim(ms)':>10} {'Kruskal(ms)':>12} {'结果一致':>8}")
    print("-" * 60)
    
    np.random.seed(42)
    for n, density, label in configs:
        g = generate_random_graph(n, density)
        
        start = time.time()
        w1, _ = net.prim(g)
        t_prim = (time.time() - start) * 1000
        
        start = time.time()
        w2, _ = net.kruskal(g)
        t_kruskal = (time.time() - start) * 1000
        
        consistent = abs(w1 - w2) < 1e-6
        print(f"{n:>8} {density:>6.1f} {label:>8} {t_prim:>10.3f} {t_kruskal:>12.3f} {'✓' if consistent else '✗':>8}")
    
    print("\n💡 结论：稀疏图上Kruskal更快（排序+并查集），稠密图上Prim更快（O(n²)）。")


def experiment_floyd_vs_dijkstra():
    print("\n" + "=" * 80)
    print("实验3：全源最短路 —— Floyd vs 多次Dijkstra")
    print("=" * 80)
    
    sizes = [20, 50, 100]
    density = 0.3
    
    print(f"\n{'节点数':>8} {'Floyd(ms)':>12} {'多次Dijkstra(ms)':>18} {'速度比':>10}")
    print("-" * 55)
    
    np.random.seed(42)
    for n in sizes:
        g = generate_random_graph(n, density)
        
        # Floyd
        INF = float('inf')
        adj = [[INF]*n for _ in range(n)]
        for i in range(n):
            adj[i][i] = 0
        for u in range(n):
            for v, w in g.adj[u]:
                adj[u][v] = w
        
        start = time.time()
        dist_floyd = net.floyd_warshall(adj)
        t_floyd = (time.time() - start) * 1000
        
        # 多次Dijkstra
        start = time.time()
        dist_dijk = []
        for s in range(n):
            d, _ = net.dijkstra_heap(g, s)
            dist_dijk.append(d)
        t_dijk = (time.time() - start) * 1000
        
        ratio = t_floyd / t_dijk if t_dijk > 0 else float('inf')
        print(f"{n:>8} {t_floyd:>12.3f} {t_dijk:>18.3f} {ratio:>10.2f}x")
    
    print("\n💡 结论：稀疏图上多次Dijkstra更快（O(nm log n) vs O(n³)）。")
    print("   稠密图上Floyd可能更快（常数小，实现简单）。")
    print("   Floyd的优势是实现简单，适合n<100的情况。")


def experiment_max_flow():
    print("\n" + "=" * 80)
    print("实验4：Dinic最大流 —— 不同规模")
    print("=" * 80)
    
    configs = [
        (20, 0.2),
        (50, 0.1),
        (100, 0.05),
        (200, 0.02),
    ]
    
    print(f"\n{'节点数':>8} {'密度':>6} {'最大流':>10} {'时间(ms)':>10}")
    print("-" * 40)
    
    np.random.seed(42)
    for n, density in configs:
        dinic = net.Dinic(n)
        for i in range(n):
            for j in range(i+1, n):
                if np.random.random() < density:
                    cap = np.random.randint(1, 50)
                    dinic.add_edge(i, j, cap)
                    dinic.add_edge(j, i, cap)  # 双向
        
        start = time.time()
        flow = dinic.max_flow(0, n-1)
        t = (time.time() - start) * 1000
        
        print(f"{n:>8} {density:>6.2f} {flow:>10} {t:>10.3f}")
    
    print("\n💡 结论：Dinic在实际中运行很快，远好于理论上界O(n²m)。")


if __name__ == '__main__':
    experiment_dijkstra()
    experiment_mst()
    experiment_floyd_vs_dijkstra()
    experiment_max_flow()
    
    print("\n" + "=" * 80)
    print("全部实验完成！")
    print("=" * 80)
