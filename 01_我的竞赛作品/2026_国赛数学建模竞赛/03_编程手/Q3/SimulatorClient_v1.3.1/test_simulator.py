#!/usr/bin/env python3
"""
HTTP模拟器测试脚本
使用命令行参数传入队号，避免硬编码
"""
import sys
import argparse
from pathlib import Path

# 添加src目录到路径
# 【2026-09-12 修正】原写 `Path(__file__).parent / "01_修改区_WorkInProgress" / "去AI化代码库" / "Q3" / "src"`
# —— 那是**队友本机的目录层级**，本包 `src/` 就在根目录下 ⇒ 该路径不存在，
# `from http_simulator_client import ...` 必然 ModuleNotFoundError（README 教的命令跑不起来）。
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from http_simulator_client import HttpSimulatorClient

def test_simulator(robot_id: str, arena_id: str = "default", base_url: str = "http://127.0.0.1:2026"):
    """完整测试流程"""
    print("=" * 60)
    print("HTTP模拟器测试")
    print(f"Robot ID: {robot_id}")
    print(f"Arena ID: {arena_id}")
    print(f"Base URL: {base_url}")
    print("=" * 60)

    client = HttpSimulatorClient(
        robot_id=robot_id,
        arena_id=arena_id,
        base_url=base_url
    )

    # 测试1: Enter
    print("\n[1] 测试 enter()")
    enter_outcome = client.enter()
    print(f"  accepted: {enter_outcome.accepted}")

    if not enter_outcome.accepted:
        print(f"  [FAIL] 进入失败")
        if enter_outcome.error:
            print(f"  error: {enter_outcome.error}")
        return

    print(f"  virtual_time_s: {enter_outcome.virtual_time_s}")
    print(f"  max_virtual_duration_s: {enter_outcome.max_virtual_duration_s}")
    print(f"  [PASS] 进入成功")

    # 测试2: Measure
    print("\n[2] 测试 measure()")
    measure_outcome = client.measure(0, 0, 1)
    print(f"  response_received: {measure_outcome.response_received}")
    print(f"  accepted: {measure_outcome.accepted}")

    if measure_outcome.accepted:
        print(f"  virtual_time_s: {measure_outcome.virtual_time_s}")
        print(f"  measure_result: {measure_outcome.result.measure_result}")
        if measure_outcome.result.svd_deg is not None:
            print(f"  svd_deg: {measure_outcome.result.svd_deg}")
        print(f"  [PASS] 测量成功")
    else:
        print(f"  [FAIL] 测量失败")

    # 测试3: Clear
    print("\n[3] 测试 clear()")
    clear_outcome = client.clear(1000, 1000, 1)
    print(f"  response_received: {clear_outcome.response_received}")
    print(f"  accepted: {clear_outcome.accepted}")

    if clear_outcome.accepted:
        print(f"  virtual_time_s: {clear_outcome.virtual_time_s}")
        print(f"  clear_result: {clear_outcome.result.clear_result}")
        print(f"  [PASS] 清除成功")
    else:
        print(f"  [FAIL] 清除失败")

    # 测试4: Exit
    print("\n[4] 测试 exit()")
    exit_outcome = client.exit()
    print(f"  response_received: {exit_outcome.response_received}")
    print(f"  accepted: {exit_outcome.accepted}")

    if exit_outcome.accepted:
        print(f"  virtual_time_s: {exit_outcome.virtual_time_s}")
        print(f"  exit_reason: {exit_outcome.result.exit_reason}")
        print(f"  [PASS] 退出成功")
    else:
        print(f"  [FAIL] 退出失败")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='HTTP模拟器测试脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python test_simulator.py --robot-id YOUR_ROBOT_ID
  python test_simulator.py --robot-id YOUR_ROBOT_ID --base-url http://localhost:2026
        """
    )

    parser.add_argument(
        '--robot-id',
        type=str,
        required=True,
        help='参赛队机器人ID (必填)'
    )
    parser.add_argument(
        '--arena-id',
        type=str,
        default='default',
        help='场地ID (默认: default)'
    )
    parser.add_argument(
        '--base-url',
        type=str,
        default='http://127.0.0.1:2026',
        help='模拟器URL (默认: http://127.0.0.1:2026)'
    )

    args = parser.parse_args()

    try:
        test_simulator(args.robot_id, args.arena_id, args.base_url)
    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
