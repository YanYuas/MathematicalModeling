#!/usr/bin/env python3
"""测试时间计算修改"""
import sys
sys.path.insert(0, '问题1/题代码')

from experiment_runner import run_single_experiment
import time

print("="*60)
print("Test 1: greedy method")
print("="*60)
result = run_single_experiment('n100', 'ffd', False, 0, 'greedy')
print(f"greedy time: {result['time']:.4f}s (should > 0)")
print(f"iterations: {result['iterations']} (should = 0)")
print(f"result: {result['W']:.0f}x{result['H']:.0f}")

print("\n" + "="*60)
print("Test 2: twophase method")
print("="*60)
start = time.time()
result = run_single_experiment('n100', 'ffd', False, 0, 'twophase')
total_wall_time = time.time() - start

print(f"twophase recorded time: {result['time']:.4f}s")
print(f"wall clock time: {total_wall_time:.4f}s")
print(f"difference: {abs(result['time'] - total_wall_time):.4f}s (should < 2s)")
print(f"iterations: {result['iterations']}")

print("\n" + "="*60)
print("Verification: time should include construct time")
print("="*60)
if result['time'] > 0.1:
    print("PASS: twophase time includes construct time")
else:
    print("FAIL: twophase time abnormal")
