#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""后台运行90次实验 - 使用绝对路径"""
import sys
import os

# 使用绝对路径
base_dir = r'C:\Users\29845\Desktop\华数杯'
code_dir = os.path.join(base_dir, '问题1', '题代码')

# 切换工作目录和添加路径
os.chdir(code_dir)
sys.path.insert(0, code_dir)

print(f"Working directory: {os.getcwd()}")
print(f"Python path: {code_dir}")
print("-" * 70)

from experiment_runner import run_experiments

print("Starting 90 experiments...")
print("Estimated time: 45-60 minutes")
print("=" * 70)

try:
    run_experiments()
    print("\n" + "=" * 70)
    print("All experiments completed successfully!")
except Exception as e:
    print(f"\nError occurred: {e}")
    import traceback
    traceback.print_exc()
