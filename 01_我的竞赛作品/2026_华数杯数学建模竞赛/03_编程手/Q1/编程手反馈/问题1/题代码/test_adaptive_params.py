#!/usr/bin/env python3
"""测试分层参数功能"""
import sys
sys.path.insert(0, '问题1/题代码')

from experiment_runner import run_single_experiment

print("="*70)
print("测试分层参数 - FFD vs Random初始化")
print("="*70)

# 测试1：FFD初始化（应该用CONSERVATIVE参数）
print("\n测试1: FFD初始化（gap < 10%）")
print("-"*70)
result_ffd = run_single_experiment('n100', 'ffd', False, 0, 'twophase')
print(f"结果: W={result_ffd['W']:.0f}, H={result_ffd['H']:.0f}")
print(f"时间: {result_ffd['time']:.2f}s")
print(f"迭代次数: {result_ffd['iterations']} (应该 > 11)")

# 测试2：Random初始化（应该用AGGRESSIVE参数）
print("\n测试2: Random初始化（gap > 100%）")
print("-"*70)
result_random = run_single_experiment('n100', 'random', False, 0, 'twophase')
print(f"结果: W={result_random['W']:.0f}, H={result_random['H']:.0f}")
print(f"时间: {result_random['time']:.2f}s")
print(f"迭代次数: {result_random['iterations']}")

print("\n" + "="*70)
print("验证结果")
print("="*70)

if result_ffd['iterations'] > 11:
    print("✓ PASS: FFD使用了保守参数（迭代次数增加）")
else:
    print("✗ FAIL: FFD仍使用旧参数（迭代次数=11）")

print(f"\nFFD迭代次数: {result_ffd['iterations']}")
print(f"Random迭代次数: {result_random['iterations']}")
