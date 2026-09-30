#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""运行5次测试实验验证时间修复"""
import sys
import os

# 修复路径
current_dir = os.path.dirname(os.path.abspath(__file__))
code_dir = os.path.join(current_dir, '问题1', '题代码')
sys.path.insert(0, code_dir)
os.chdir(code_dir)

from experiment_runner import run_single_experiment
import csv

print("="*70)
print("验证时间修复 - 5次快速测试")
print("="*70)

test_cases = [
    ('n100', 'ffd', False, 0, 'greedy'),
    ('n100', 'ffd', False, 0, 'twophase'),
    ('n100', 'ffd', False, 0, 'weighted'),
    ('n100', 'ffd', False, 1, 'greedy'),
    ('n100', 'ffd', False, 1, 'twophase'),
]

results = []
for i, (dataset, init, pair, seed, cost) in enumerate(test_cases, 1):
    print(f"\n[{i}/5] {dataset} | {init} | {cost} | seed={seed}")
    result = run_single_experiment(dataset, init, pair, seed, cost)
    results.append(result)
    print(f"  time={result['time']:.4f}s, iter={result['iterations']}, "
          f"W={result['W']:.0f}, H={result['H']:.0f}")

print("\n" + "="*70)
print("验证结果")
print("="*70)

greedy_times = [r['time'] for r in results if r['cost_method'] == 'greedy']
twophase_times = [r['time'] for r in results if r['cost_method'] == 'twophase']

print(f"greedy平均时间: {sum(greedy_times)/len(greedy_times):.4f}s")
print(f"twophase平均时间: {sum(twophase_times)/len(twophase_times):.4f}s")

if all(t > 0 for t in greedy_times):
    print("✓ PASS: greedy的time > 0")
else:
    print("✗ FAIL: greedy的time仍为0")

if all(t > g for t, g in zip(twophase_times, greedy_times)):
    print("✓ PASS: twophase的time > greedy的time")
else:
    print("✗ FAIL: 时间关系异常")

# 保存测试结果
output_path = os.path.join(current_dir, '问题1', '实验日志', 'test_results.csv')
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    if results:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

print(f"\n测试结果已保存: {output_path}")
