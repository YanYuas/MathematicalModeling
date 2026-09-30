#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""运行10次快速验证实验 - 验证修复效果"""
import sys
import os

base_dir = r'C:\Users\29845\Desktop\华数杯'
code_dir = os.path.join(base_dir, '问题1', '题代码')
os.chdir(code_dir)
sys.path.insert(0, code_dir)

from experiment_runner import run_single_experiment
import csv
import time

print("="*70)
print("快速验证实验 - 10次测试")
print("="*70)
print(f"目的: 验证时间修复和分层参数效果")
print()

test_plan = [
    # FFD初始化 - 验证分层参数（应该有不同结果）
    ('n100', 'ffd', False, 0, 'twophase', 'FFD seed=0'),
    ('n100', 'ffd', False, 1, 'twophase', 'FFD seed=1'),
    ('n100', 'ffd', False, 2, 'twophase', 'FFD seed=2'),

    # Greedy - 验证时间修复
    ('n100', 'ffd', False, 0, 'greedy', 'Greedy baseline'),
    ('n100', 'ffd', False, 1, 'weighted', 'Weighted cost'),

    # Random - 验证激进参数
    ('n100', 'random', False, 0, 'twophase', 'Random seed=0'),
    ('n100', 'random', False, 1, 'twophase', 'Random seed=1'),

    # n200快速测试
    ('n200', 'ffd', False, 0, 'twophase', 'n200 FFD'),
    ('n200', 'random', False, 0, 'twophase', 'n200 Random'),

    # n300快速测试
    ('n300', 'ffd', False, 0, 'twophase', 'n300 FFD'),
]

results = []
start_total = time.time()

for i, (dataset, init, pair, seed, cost, desc) in enumerate(test_plan, 1):
    print(f"[{i}/10] {desc}...")
    try:
        result = run_single_experiment(dataset, init, pair, seed, cost)
        results.append(result)
        print(f"  OK time={result['time']:.2f}s, iter={result['iterations']}, "
              f"W={result['W']:.0f}, H={result['H']:.0f}, gap={result['gap']:.1f}%")
    except Exception as e:
        print(f"  ERROR: {e}")

total_time = time.time() - start_total

print("\n" + "="*70)
print("验证结果")
print("="*70)

# 分析FFD的seed有效性
ffd_results = [r for r in results if r['initial_method'] == 'ffd' and r['cost_method'] == 'twophase' and r['dataset'] == 'n100']
if len(ffd_results) >= 3:
    ffd_areas = [r['area'] for r in ffd_results]
    ffd_iters = [r['iterations'] for r in ffd_results]
    print(f"\nFFD seed有效性检查:")
    print(f"  Area: {ffd_areas}")
    print(f"  Iterations: {ffd_iters}")
    if len(set(ffd_areas)) > 1 or len(set(ffd_iters)) > 1:
        print("  PASS: Different seeds have different results")
    else:
        print("  FAIL: All seeds have same results")

# 检查greedy时间
greedy_results = [r for r in results if r['cost_method'] == 'greedy']
if greedy_results:
    greedy_time = greedy_results[0]['time']
    print(f"\nGreedy时间检查:")
    print(f"  time = {greedy_time:.4f}s")
    if greedy_time > 0:
        print("  PASS: time > 0")
    else:
        print("  FAIL: time = 0")

# 保存结果
output_path = os.path.join(base_dir, '问题1', '实验日志', 'quick_验证_results.csv')
if results:
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\n结果已保存: {output_path}")

print(f"\n总耗时: {total_time/60:.1f} 分钟")
print("="*70)
