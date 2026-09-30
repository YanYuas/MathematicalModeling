"""
动态SA参数调整 - 根据初始解质量分层设置

解决问题：
- Ultra-fast参数针对random初始化（gap=445%）优化
- 对FFD初始化（gap=4.78%）过激，导致11次迭代即停止
- 结果：10个seed完全相同，失去探索性

分层策略：
- gap < 10%（FFD类）：保守参数，允许精细搜索
- gap 10-100%（greedy_random类）：标准Ultra-fast参数
- gap > 100%（random类）：激进参数，快速下降
"""

def get_adaptive_sa_params(initial_gap, base_params):
    """
    根据初始解gap动态调整SA参数

    Args:
        initial_gap: 初始解的gap百分比（如4.78表示4.78%）
        base_params: 基础SA参数字典

    Returns:
        调整后的SA参数字典
    """
    params = base_params.copy()

    if initial_gap < 10:
        # FFD类：gap<10%，已经很好的初始解
        # 需要更多迭代来精细搜索
        params['L_factor'] = 50          # 10 → 50（5倍迭代）
        params['max_no_improve'] = 20    # 8 → 20（更多容忍）
        params['T_final'] = 0.01         # 0.1 → 0.01（允许更低温度）
        params['k'] = 7                  # 5 → 7（恢复原始快冷阶段）
        tier = "CONSERVATIVE (FFD-like)"

    elif initial_gap < 100:
        # greedy_random类：gap 10-100%，中等质量
        # 使用标准Ultra-fast参数
        tier = "STANDARD (Ultra-fast)"
        # 保持base_params不变

    else:
        # random类：gap>100%，较差初始解
        # 需要激进快速下降
        params['L_factor'] = 5           # 10 → 5（减少迭代）
        params['max_no_improve'] = 3     # 8 → 3（快速停止）
        params['T_final'] = 1.0          # 0.1 → 1.0（提前终止）
        tier = "AGGRESSIVE (random-like)"

    return params, tier


# 使用示例
if __name__ == "__main__":
    from config import SA_PARAMS

    # 测试三种场景
    test_cases = [
        (4.78, "FFD初始化"),
        (50.0, "greedy_random初始化"),
        (445.0, "random初始化"),
    ]

    print("="*70)
    print("动态参数调整测试")
    print("="*70)

    for gap, desc in test_cases:
        params, tier = get_adaptive_sa_params(gap, SA_PARAMS)
        print(f"\n{desc} (gap={gap:.2f}%) → {tier}")
        print(f"  L_factor: {SA_PARAMS['L_factor']} → {params['L_factor']}")
        print(f"  max_no_improve: {SA_PARAMS['max_no_improve']} → {params['max_no_improve']}")
        print(f"  T_final: {SA_PARAMS['T_final']} → {params['T_final']}")
        print(f"  k: {SA_PARAMS['k']} → {params['k']}")
