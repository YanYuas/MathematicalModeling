# -*- coding: utf-8 -*-
"""
鲁棒优化与随机优化 · 入门
============================
六层钻研法 · 第3-5层：原理推导 + 手动实现 + 应用案例

现实中的优化问题往往有不确定性：
- 需求不确定（客户要多少？）
- 成本不确定（原材料价格波动？）
- 时间不确定（运输要多久？）

处理不确定性的两种主要方法：
1. 随机优化（Stochastic Optimization）：假设不确定性服从概率分布，优化期望
2. 鲁棒优化（Robust Optimization）：不假设分布，优化最坏情况

还有机会约束规划（Chance-Constrained Programming）：约束以一定概率满足。
"""

import numpy as np
from scipy.optimize import linprog, minimize


# ============================================================
# 1. 为什么需要处理不确定性？
# ============================================================
"""
确定性优化的问题：
  min c^T x
  s.t. A x <= b
       x >= 0

如果c、A、b中有不确定参数，确定性优化的解可能在实际中不可行或很差。

例子：工厂生产
  产品A利润10元，产品B利润20元
  原料限制：A用1单位，B用2单位，共100单位
  确定性最优：全生产B，50单位，利润1000元
  
  但如果B的实际利润只有5元（市场变化），
  确定性解的利润只有250元！
  而如果生产A和B各一些，最坏情况也有不错的利润。

这就是鲁棒优化的思想：不要把鸡蛋放在一个篮子里。
"""


# ============================================================
# 2. 随机优化：期望优化
# ============================================================
def stochastic_optimization_example():
    """
    随机优化示例：新闻供应商问题（Newsvendor Problem）
    
    报童每天早上买报纸，每份成本c，售价p，没卖完的残值s。
    每天需求D是随机的（服从某种分布）。
    问：买多少份报纸，期望利润最大？
    
    解析解：临界分位数（Critical Fractile）
      F(Q*) = (p - c) / (p - s)
      其中F是需求的累积分布函数
    
    这里用数值方法（枚举）求解。
    """
    print("=" * 60)
    print("案例1：新闻供应商问题（随机优化）")
    print("=" * 60)
    
    # 参数
    c = 5.0   # 成本
    p = 12.0  # 售价
    s = 2.0   # 残值
    
    # 需求：正态分布，均值100，标准差20
    np.random.seed(42)
    demand_samples = np.random.normal(100, 20, 10000)
    demand_samples = np.maximum(demand_samples, 0)  # 需求非负
    
    # 枚举订货量，计算期望利润
    best_q = 0
    best_profit = -float('inf')
    
    for q in range(50, 151):
        # 对每个需求样本计算利润
        profits = []
        for d in demand_samples:
            sales = min(q, d)
            leftover = max(q - d, 0)
            profit = p * sales + s * leftover - c * q
            profits.append(profit)
        
        expected_profit = np.mean(profits)
        if expected_profit > best_profit:
            best_profit = expected_profit
            best_q = q
    
    # 理论解
    from scipy.stats import norm
    critical_fractile = (p - c) / (p - s)
    theoretical_q = norm.ppf(critical_fractile, 100, 20)
    
    print(f"参数：成本c={c}, 售价p={p}, 残值s={s}")
    print(f"需求：正态分布(均值100, 标准差20)")
    print(f"\n数值解：最优订货量={best_q}, 期望利润={best_profit:.2f}")
    print(f"理论解：临界分位数={critical_fractile:.3f}, 最优订货量={theoretical_q:.1f}")
    print(f"\n分析：")
    print(f"  欠储成本（少卖一份损失）= p - c = {p-c}")
    print(f"  超储成本（多买一份损失）= c - s = {c-s}")
    print(f"  临界分位数 = 欠储/(欠储+超储) = {critical_fractile:.3f}")
    print(f"  即：有{critical_fractile*100:.1f}%的概率不会缺货")
    print()


# ============================================================
# 3. 两阶段随机规划
# ============================================================
def two_stage_stochastic_example():
    """
    两阶段随机规划示例
    
    第一阶段（here-and-now）：现在做决策，不确定参数未知
    第二阶段（wait-and-see）：不确定参数实现后，做补救决策
    
    标准形式：
      min c^T x + E[min d^T y(ξ)]
      s.t. A x <= b
           T(ξ) x + W y(ξ) <= h(ξ)
           x >= 0, y(ξ) >= 0
    
    示例：工厂产能投资
    第一阶段：决定建多大产能（成本高，但不确定需求）
    第二阶段：需求实现后，决定生产多少（产能限制）
    """
    print("=" * 60)
    print("案例2：两阶段随机规划（产能投资）")
    print("=" * 60)
    
    # 第一阶段：产能投资
    capacity_cost = 10  # 每单位产能成本
    
    # 第二阶段：生产
    profit_per_unit = 25  # 每单位产品利润
    production_cost = 5   # 每单位生产成本
    
    # 需求场景（3种场景，等概率）
    scenarios = [
        {'demand': 80, 'prob': 1/3},
        {'demand': 100, 'prob': 1/3},
        {'demand': 120, 'prob': 1/3},
    ]
    
    # 枚举产能，计算期望总成本
    best_capacity = 0
    best_cost = float('inf')
    
    for capacity in range(60, 141, 2):
        # 第一阶段成本
        first_stage_cost = capacity_cost * capacity
        
        # 第二阶段期望成本（利润为负成本）
        second_stage_expected = 0
        for s in scenarios:
            demand = s['demand']
            prob = s['prob']
            production = min(capacity, demand)
            second_stage_profit = (profit_per_unit - production_cost) * production
            second_stage_expected += prob * (-second_stage_profit)
        
        total_cost = first_stage_cost + second_stage_expected
        
        if total_cost < best_cost:
            best_cost = total_cost
            best_capacity = capacity
    
    print(f"参数：产能成本={capacity_cost}/单位, 净利润={profit_per_unit-production_cost}/单位")
    print(f"需求场景：80(1/3), 100(1/3), 120(1/3)")
    print(f"\n最优产能：{best_capacity}")
    print(f"最小期望总成本：{best_cost:.2f}（即最大期望利润={-best_cost:.2f}）")
    print(f"\n分析：")
    print(f"  确定性优化（需求=均值100）：产能=100")
    print(f"  随机优化：产能={best_capacity}（考虑了需求波动）")
    print(f"  随机优化的产能更保守，因为产能过剩有成本")
    print()


# ============================================================
# 4. 鲁棒优化：最坏情况优化
# ============================================================
def robust_optimization_example():
    """
    鲁棒优化示例：最坏情况优化
    
    不确定参数在一个集合U中，优化最坏情况：
      min_x max_{ξ∈U} f(x, ξ)
      s.t. g(x, ξ) <= 0 对所有ξ∈U
    
    示例：投资组合
    两只股票，收益率不确定，在[min, max]区间内。
    求投资比例，使最坏情况下的收益最大。
    """
    print("=" * 60)
    print("案例3：鲁棒优化（最坏情况投资组合）")
    print("=" * 60)
    
    # 两只股票的收益率范围
    stock1_min, stock1_max = 0.05, 0.15  # 5%~15%
    stock2_min, stock2_max = -0.05, 0.25  # -5%~25%
    
    # 枚举投资比例（投股票1的比例）
    best_ratio = 0
    best_worst_return = -float('inf')
    
    for r in np.arange(0, 1.01, 0.01):
        # 投资比例：r投股票1，1-r投股票2
        # 最坏情况：股票1取最低，股票2取最低（因为都是正权重）
        worst_return = r * stock1_min + (1 - r) * stock2_min
        
        if worst_return > best_worst_return:
            best_worst_return = worst_return
            best_ratio = r
    
    print(f"股票1收益率：[{stock1_min*100:.0f}%, {stock1_max*100:.0f}%]")
    print(f"股票2收益率：[{stock2_min*100:.0f}%, {stock2_max*100:.0f}%]")
    print(f"\n鲁棒最优：股票1={best_ratio*100:.0f}%, 股票2={(1-best_ratio)*100:.0f}%")
    print(f"最坏情况收益：{best_worst_return*100:.2f}%")
    
    # 对比：期望优化（假设均匀分布）
    expected1 = (stock1_min + stock1_max) / 2
    expected2 = (stock2_min + stock2_max) / 2
    print(f"\n对比：期望优化（均匀分布假设）")
    print(f"  股票1期望收益：{expected1*100:.1f}%")
    print(f"  股票2期望收益：{expected2*100:.1f}%")
    print(f"  期望最优：全投股票2（期望收益更高）")
    print(f"  但最坏情况：股票2亏5%！")
    
    print(f"\n分析：")
    print(f"  鲁棒优化保守但安全，最坏情况也有正收益")
    print(f"  期望优化激进但有风险，可能亏损")
    print(f"  选择哪种取决于风险偏好")
    print()


# ============================================================
# 5. 机会约束规划
# ============================================================
def chance_constrained_example():
    """
    机会约束规划示例
    
    约束不要求一定满足，而是以概率α满足：
      P(g(x, ξ) <= 0) >= α
    
    示例：库存管理
    订货量Q，需求D随机。
    要求：缺货概率不超过5%（即P(D <= Q) >= 95%）
    目标：最小化库存成本
    """
    print("=" * 60)
    print("案例4：机会约束规划（库存管理）")
    print("=" * 60)
    
    from scipy.stats import norm
    
    # 需求：正态分布
    mu = 100    # 均值
    sigma = 20  # 标准差
    
    # 持有成本
    holding_cost = 2  # 每单位库存成本
    
    # 服务水平要求：缺货概率<=5%
    alpha = 0.95
    
    # 解析解：Q = mu + z_alpha * sigma
    z_alpha = norm.ppf(alpha)
    Q = mu + z_alpha * sigma
    
    print(f"需求：正态分布(均值={mu}, 标准差={sigma})")
    print(f"服务水平：{alpha*100:.0f}%（缺货概率<={1-alpha*100:.0f}%）")
    print(f"\n最优订货量：Q = μ + z_α × σ")
    print(f"  = {mu} + {z_alpha:.3f} × {sigma}")
    print(f"  = {Q:.1f}")
    print(f"  安全库存 = z_α × σ = {z_alpha*sigma:.1f}")
    
    # 验证
    np.random.seed(42)
    demands = np.random.normal(mu, sigma, 10000)
    stockout_rate = np.mean(demands > Q)
    print(f"\n模拟验证（10000次）：")
    print(f"  实际缺货率：{stockout_rate*100:.2f}%（要求<=5%）")
    
    print(f"\n分析：")
    print(f"  服务水平越高，需要的安全库存越多")
    print(f"  95%服务水平需要1.645个标准差的安全库存")
    print(f"  99%服务水平需要2.326个标准差")
    print()


# ============================================================
# 6. 三种方法的对比
# ============================================================
def comparison_summary():
    """三种不确定性处理方法的对比"""
    print("=" * 60)
    print("三种不确定性处理方法对比")
    print("=" * 60)
    
    print("""
┌──────────────┬──────────────────┬──────────────────┬──────────────────┐
│   方法       │   随机优化       │   鲁棒优化       │  机会约束规划    │
├──────────────┼──────────────────┼──────────────────┼──────────────────┤
│ 不确定性假设 │ 已知概率分布     │ 已知不确定集合   │ 已知概率分布     │
│ 优化目标     │ 期望最优         │ 最坏情况最优     │ 期望最优         │
│ 约束处理     │ 期望约束/补救    │ 所有场景都满足   │ 以概率α满足      │
│ 优点         │ 利用分布信息     │ 不需要分布       │ 允许少量违反     │
│ 缺点         │ 需要准确分布     │ 过于保守         │ 计算困难         │
│ 适用场景     │ 有历史数据       │ 高风险/灾难性    │ 服务水平要求     │
│ 代表问题     │ 新闻供应商       │ 投资组合/工程    │ 库存/排队        │
└──────────────┴──────────────────┴──────────────────┴──────────────────┘
    """)
    
    print("选择建议：")
    print("  1. 有大量历史数据，能估计分布 → 随机优化")
    print("  2. 数据少，或失败代价大 → 鲁棒优化")
    print("  3. 允许少量不满足，有服务水平要求 → 机会约束")
    print("  4. 比赛中常用：随机优化（场景法）+ 灵敏度分析")
    print()


# ============================================================
# 主函数
# ============================================================
if __name__ == '__main__':
    stochastic_optimization_example()
    two_stage_stochastic_example()
    robust_optimization_example()
    chance_constrained_example()
    comparison_summary()
    
    print("=" * 60)
    print("核心要点总结：")
    print("=" * 60)
    print("1. 确定性优化在不确定环境中可能很差")
    print("2. 随机优化：优化期望，需要概率分布")
    print("3. 鲁棒优化：优化最坏情况，不需要分布但保守")
    print("4. 机会约束：约束以概率α满足")
    print("5. 新闻供应商问题有解析解（临界分位数）")
    print("6. 两阶段随机规划：先决策，再补救")
    print("7. 比赛中常用场景法（离散化不确定性）")
