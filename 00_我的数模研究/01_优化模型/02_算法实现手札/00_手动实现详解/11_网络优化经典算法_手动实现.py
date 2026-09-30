# -*- coding: utf-8 -*-
"""
网络优化 · 经典算法手动实现
============================
六层钻研法 · 第4层：手动实现

包含7个经典图论算法：
1. Dijkstra（单源最短路，朴素版+优先队列版）
2. Floyd-Warshall（全源最短路）
3. Prim（最小生成树）
4. Kruskal（最小生成树，含并查集）
5. Dinic（最大流）
6. 匈牙利算法（二分图最大匹配）
7. SPFA+连续最短路（最小费用最大流）

每个算法都有详细中文注释和测试用例。
"""

import heapq
from collections import deque


# ============================================================
# 图的表示：邻接表
# ============================================================
class Graph:
    """图的邻接表表示"""
    def __init__(self, n):
        self.n = n  # 节点数
        self.adj = [[] for _ in range(n)]  # adj[u] = [(v, weight), ...]
    
    def add_edge(self, u, v, w=1, directed=False):
        """添加边"""
        self.adj[u].append((v, w))
        if not directed:
            self.adj[v].append((u, w))


# ============================================================
# 算法1：Dijkstra单源最短路
# ============================================================
def dijkstra_naive(graph, start):
    """
    Dijkstra算法（朴素版，O(n²)）
    
    核心：每次选距离最小的未访问节点，用它更新其他节点。
    
    参数：
        graph: Graph对象
        start: 源点
    
    返回：
        dist: 从start到各点的最短距离
        prev: 最短路径上各点的前驱（用于回溯路径）
    """
    n = graph.n
    INF = float('inf')
    dist = [INF] * n
    prev = [-1] * n
    visited = [False] * n
    
    dist[start] = 0
    
    for _ in range(n):
        # 第一步：找未访问中dist最小的节点u
        u = -1
        min_dist = INF
        for i in range(n):
            if not visited[i] and dist[i] < min_dist:
                min_dist = dist[i]
                u = i
        
        if u == -1:
            break  # 剩余节点不可达
        
        visited[u] = True
        
        # 第二步：用u更新邻居
        for v, w in graph.adj[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
    
    return dist, prev


def dijkstra_heap(graph, start):
    """
    Dijkstra算法（优先队列优化，O(m log n)）
    
    用最小堆快速找到dist最小的节点。
    """
    n = graph.n
    INF = float('inf')
    dist = [INF] * n
    prev = [-1] * n
    
    dist[start] = 0
    heap = [(0, start)]  # (距离, 节点)
    
    while heap:
        d, u = heapq.heappop(heap)
        
        if d > dist[u]:
            continue  # 旧的记录，跳过
        
        for v, w in graph.adj[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                heapq.heappush(heap, (dist[v], v))
    
    return dist, prev


def get_path(prev, start, end):
    """根据prev数组回溯最短路径"""
    path = []
    cur = end
    while cur != -1:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    if path[0] != start:
        return None  # 不可达
    return path


# ============================================================
# 算法2：Floyd-Warshall全源最短路
# ============================================================
def floyd_warshall(adj_matrix):
    """
    Floyd-Warshall算法（全源最短路，O(n³)）
    
    核心：动态规划，考虑中间节点k。
    dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
    
    注意：k必须在最外层循环！
    
    参数：
        adj_matrix: 邻接矩阵，INF表示无边
    
    返回：
        dist: 全源最短距离矩阵
    """
    n = len(adj_matrix)
    # 复制一份，不修改原矩阵
    dist = [row[:] for row in adj_matrix]
    
    # k是中间节点，必须在最外层！
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    
    return dist


# ============================================================
# 算法3：Prim最小生成树
# ============================================================
def prim(graph, start=0):
    """
    Prim算法（最小生成树，O(n²)）
    
    核心：从一个节点出发，每次选连接已选集合和未选集合的最小边。
    
    返回：
        total_weight: 最小生成树总权重
        edges: 生成树的边列表 [(u, v, w), ...]
    """
    n = graph.n
    INF = float('inf')
    
    # lowcost[i] = 从已选集合到i的最小边权
    lowcost = [INF] * n
    # closest[i] = 那条最小边在已选集合中的端点
    closest = [-1] * n
    visited = [False] * n
    
    lowcost[start] = 0
    total_weight = 0
    edges = []
    
    for _ in range(n):
        # 找lowcost最小的未访问节点
        u = -1
        min_w = INF
        for i in range(n):
            if not visited[i] and lowcost[i] < min_w:
                min_w = lowcost[i]
                u = i
        
        if u == -1:
            break  # 图不连通
        
        visited[u] = True
        total_weight += lowcost[u]
        if closest[u] != -1:
            edges.append((closest[u], u, lowcost[u]))
        
        # 用u更新lowcost
        for v, w in graph.adj[u]:
            if not visited[v] and w < lowcost[v]:
                lowcost[v] = w
                closest[v] = u
    
    return total_weight, edges


# ============================================================
# 算法4：Kruskal最小生成树（含并查集）
# ============================================================
class UnionFind:
    """并查集（路径压缩+按秩合并）"""
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x):
        """找根节点（带路径压缩）"""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # 路径压缩
        return self.parent[x]
    
    def union(self, x, y):
        """合并x和y所在集合，返回是否成功（原本不连通）"""
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        # 按秩合并：小树合并到大树
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return True


def kruskal(graph):
    """
    Kruskal算法（最小生成树，O(m log m)）
    
    核心：把所有边按权重排序，从小到大选，不形成环就加入。
    用并查集判断是否形成环。
    
    返回：
        total_weight: 总权重
        edges: 生成树的边
    """
    n = graph.n
    # 收集所有边（无向图只取一次）
    all_edges = []
    for u in range(n):
        for v, w in graph.adj[u]:
            if u < v:  # 避免重复
                all_edges.append((w, u, v))
    
    # 按权重排序
    all_edges.sort()
    
    uf = UnionFind(n)
    total_weight = 0
    edges = []
    
    for w, u, v in all_edges:
        if uf.union(u, v):  # 不连通就合并
            total_weight += w
            edges.append((u, v, w))
            if len(edges) == n - 1:
                break  # 选够n-1条边了
    
    return total_weight, edges


# ============================================================
# 算法5：Dinic最大流
# ============================================================
class Dinic:
    """
    Dinic最大流算法
    
    核心：BFS分层 + DFS多路增广 + 当前弧优化
    """
    def __init__(self, n):
        self.n = n
        self.graph = [[] for _ in range(n)]  # 存边的索引
    
    class Edge:
        def __init__(self, to, cap, rev):
            self.to = to
            self.cap = cap
            self.rev = rev  # 反向边在graph[to]中的索引
    
    def add_edge(self, u, v, cap):
        """添加有向边u→v，容量cap"""
        # 正向边
        self.graph[u].append(self.Edge(v, cap, len(self.graph[v])))
        # 反向边（残量为0，用于退流）
        self.graph[v].append(self.Edge(u, 0, len(self.graph[u]) - 1))
    
    def bfs(self, s, t):
        """BFS分层，返回是否能到达t"""
        self.level = [-1] * self.n
        self.level[s] = 0
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for edge in self.graph[u]:
                if edge.cap > 0 and self.level[edge.to] == -1:
                    self.level[edge.to] = self.level[u] + 1
                    queue.append(edge.to)
        return self.level[t] != -1
    
    def dfs(self, u, t, flow):
        """DFS增广，返回实际增广的流量"""
        if u == t:
            return flow
        # 当前弧优化：从上次搜到的位置继续
        while self.it[u] < len(self.graph[u]):
            edge = self.graph[u][self.it[u]]
            if edge.cap > 0 and self.level[edge.to] == self.level[u] + 1:
                pushed = self.dfs(edge.to, t, min(flow, edge.cap))
                if pushed > 0:
                    edge.cap -= pushed
                    self.graph[edge.to][edge.rev].cap += pushed
                    return pushed
            self.it[u] += 1
        return 0
    
    def max_flow(self, s, t):
        """计算从s到t的最大流"""
        flow = 0
        while self.bfs(s, t):
            self.it = [0] * self.n  # 当前弧
            while True:
                pushed = self.dfs(s, t, float('inf'))
                if pushed == 0:
                    break
                flow += pushed
        return flow


# ============================================================
# 算法6：匈牙利算法（二分图最大匹配）
# ============================================================
def hungarian_bipartite_matching(graph_left, n_right):
    """
    匈牙利算法（二分图最大匹配）
    
    参数：
        graph_left: graph_left[u] = [v1, v2, ...] 左边节点u能匹配的右边节点
        n_right: 右边节点数
    
    返回：
        matching: matching[v] = u，表示右边节点v匹配到左边节点u
        max_matching: 最大匹配数
    """
    n_left = len(graph_left)
    matching = [-1] * n_right  # matching[v] = 左边匹配到v的节点
    
    def try_match(u, visited):
        """尝试给左边节点u找匹配，visited记录本次尝试中访问过的右边节点"""
        for v in graph_left[u]:
            if not visited[v]:
                visited[v] = True
                # 如果v没被匹配，或者匹配v的左边节点能找到新匹配
                if matching[v] == -1 or try_match(matching[v], visited):
                    matching[v] = u
                    return True
        return False
    
    max_matching = 0
    for u in range(n_left):
        visited = [False] * n_right
        if try_match(u, visited):
            max_matching += 1
    
    return matching, max_matching


# ============================================================
# 算法7：最小费用最大流（SPFA + 连续最短路）
# ============================================================
class MinCostMaxFlow:
    """
    最小费用最大流
    
    核心：每次用SPFA找费用最小的增广路，沿其增广。
    """
    def __init__(self, n):
        self.n = n
        self.graph = [[] for _ in range(n)]
    
    class Edge:
        def __init__(self, to, cap, cost, rev):
            self.to = to
            self.cap = cap
            self.cost = cost
            self.rev = rev
    
    def add_edge(self, u, v, cap, cost):
        self.graph[u].append(self.Edge(v, cap, cost, len(self.graph[v])))
        self.graph[v].append(self.Edge(u, 0, -cost, len(self.graph[u]) - 1))
    
    def spfa(self, s, t):
        """SPFA找最短路（可处理负权），返回是否可达"""
        INF = float('inf')
        self.dist = [INF] * self.n
        self.prev_v = [-1] * self.n
        self.prev_e = [-1] * self.n
        in_queue = [False] * self.n
        
        self.dist[s] = 0
        queue = deque([s])
        in_queue[s] = True
        
        while queue:
            u = queue.popleft()
            in_queue[u] = False
            for i, edge in enumerate(self.graph[u]):
                if edge.cap > 0 and self.dist[u] + edge.cost < self.dist[edge.to]:
                    self.dist[edge.to] = self.dist[u] + edge.cost
                    self.prev_v[edge.to] = u
                    self.prev_e[edge.to] = i
                    if not in_queue[edge.to]:
                        queue.append(edge.to)
                        in_queue[edge.to] = True
        
        return self.dist[t] != INF
    
    def min_cost_flow(self, s, t, maxf=None):
        """计算最小费用最大流"""
        flow = 0
        cost = 0
        
        while self.spfa(s, t):
            # 找这条路上的最大可增广流量
            add = float('inf')
            v = t
            while v != s:
                u = self.prev_v[v]
                e = self.prev_e[v]
                add = min(add, self.graph[u][e].cap)
                v = u
            
            if maxf is not None:
                add = min(add, maxf - flow)
            
            # 增广
            v = t
            while v != s:
                u = self.prev_v[v]
                e = self.prev_e[v]
                self.graph[u][e].cap -= add
                self.graph[v][self.graph[u][e].rev].cap += add
                v = u
            
            flow += add
            cost += add * self.dist[t]
            
            if maxf is not None and flow >= maxf:
                break
        
        return flow, cost


# ============================================================
# 测试用例
# ============================================================
def test_shortest_path():
    print("=" * 60)
    print("测试1：最短路径（Dijkstra + Floyd）")
    print("=" * 60)
    
    # 经典测试图
    g = Graph(5)
    g.add_edge(0, 1, 10)
    g.add_edge(0, 3, 30)
    g.add_edge(0, 4, 100)
    g.add_edge(1, 2, 50)
    g.add_edge(2, 4, 10)
    g.add_edge(3, 2, 20)
    g.add_edge(3, 4, 60)
    
    dist, prev = dijkstra_heap(g, 0)
    print(f"从节点0出发的最短距离：{dist}")
    print(f"到节点4的最短路径：{get_path(prev, 0, 4)}，距离={dist[4]}")
    
    # Floyd测试
    INF = float('inf')
    adj = [[INF]*5 for _ in range(5)]
    for i in range(5):
        adj[i][i] = 0
    edges = [(0,1,10),(0,3,30),(0,4,100),(1,2,50),(2,4,10),(3,2,20),(3,4,60)]
    for u,v,w in edges:
        adj[u][v] = w
        adj[v][u] = w
    
    dist_all = floyd_warshall(adj)
    print(f"Floyd全源最短路，0→4 = {dist_all[0][4]}")
    assert dist[4] == dist_all[0][4] == 60
    print("✓ 测试通过！\n")


def test_mst():
    print("=" * 60)
    print("测试2：最小生成树（Prim + Kruskal）")
    print("=" * 60)
    
    g = Graph(4)
    g.add_edge(0, 1, 1)
    g.add_edge(0, 2, 4)
    g.add_edge(0, 3, 3)
    g.add_edge(1, 2, 2)
    g.add_edge(2, 3, 5)
    
    w1, e1 = prim(g)
    w2, e2 = kruskal(g)
    print(f"Prim: 总权重={w1}, 边={e1}")
    print(f"Kruskal: 总权重={w2}, 边={e2}")
    assert w1 == w2 == 6
    print("✓ 测试通过！\n")


def test_max_flow():
    print("=" * 60)
    print("测试3：最大流（Dinic）")
    print("=" * 60)
    
    dinic = Dinic(4)
    dinic.add_edge(0, 1, 3)
    dinic.add_edge(0, 2, 2)
    dinic.add_edge(1, 2, 1)
    dinic.add_edge(1, 3, 2)
    dinic.add_edge(2, 3, 3)
    
    flow = dinic.max_flow(0, 3)
    print(f"最大流：{flow}")
    assert flow == 5
    print("✓ 测试通过！\n")


def test_bipartite_matching():
    print("=" * 60)
    print("测试4：二分图匹配（匈牙利算法）")
    print("=" * 60)
    
    # 左边3个工人，右边3个任务
    graph_left = [
        [0, 1],     # 工人0能做任务0,1
        [0, 2],     # 工人1能做任务0,2
        [1, 2],     # 工人2能做任务1,2
    ]
    
    matching, max_match = hungarian_bipartite_matching(graph_left, 3)
    print(f"最大匹配数：{max_match}")
    print(f"匹配结果（任务→工人）：{matching}")
    assert max_match == 3
    print("✓ 测试通过！\n")


def test_min_cost_flow():
    print("=" * 60)
    print("测试5：最小费用最大流")
    print("=" * 60)
    
    mcmf = MinCostMaxFlow(4)
    mcmf.add_edge(0, 1, 3, 1)  # 0→1，容量3，费用1
    mcmf.add_edge(0, 2, 2, 5)  # 0→2，容量2，费用5
    mcmf.add_edge(1, 2, 1, 1)  # 1→2，容量1，费用1
    mcmf.add_edge(1, 3, 2, 2)  # 1→3，容量2，费用2
    mcmf.add_edge(2, 3, 3, 1)  # 2→3，容量3，费用1
    
    flow, cost = mcmf.min_cost_flow(0, 3)
    print(f"最大流：{flow}，最小费用：{cost}")
    assert flow == 5
    print("✓ 测试通过！\n")


if __name__ == '__main__':
    test_shortest_path()
    test_mst()
    test_max_flow()
    test_bipartite_matching()
    test_min_cost_flow()
    print("=" * 60)
    print("全部测试通过！")
    print("=" * 60)
