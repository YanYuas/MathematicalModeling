#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""运行完整90次实验"""
import sys
sys.path.insert(0, 'q1_code')

# 直接导入并运行
try:
    from experiment_runner import run_full_experiments
    print("Starting 90 experiments...")
    print("This will take approximately 45-60 minutes")
    run_full_experiments()
    print("\nAll experiments completed!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
