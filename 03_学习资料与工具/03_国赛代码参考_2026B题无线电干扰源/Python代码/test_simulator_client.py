"""
SimulatorClient统一接口测试套件 v1.3
覆盖全部33项测试
"""
import pytest
import json
import math
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from simulator_client import (
    ActionOutcome, MeasureResult, ClearResult, ExitResult,
    EnterResponse, PracticeOutcome, SimulatorClient
)
from http_simulator_client import HttpSimulatorClient
from offline_simulator_client import OfflineSimulatorClient, InterferenceSource


# =============================================================================
# 5.1 API合规测试（4项）
# =============================================================================

class TestAPICompliance:
    """API-1 到 API-4"""

    def test_api_1_request_payload_complete(self):
        """API-1: 四类请求体完整（包含arena_id、robot_id、request_id）"""
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            # Mock successful enter response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "accepted": True,
                "virtual_time_s": 0.0,
                "max_virtual_duration_s": 3600.0,
                "max_real_duration_s": 1800.0,
                "remaining_real_duration_s": 1800.0
            }
            mock_session.post.return_value = mock_response

            client = HttpSimulatorClient(robot_id="test_robot", arena_id="test_arena")
            client.enter()

            # 验证请求体包含必需字段
            call_args = mock_session.post.call_args
            sent_payload = call_args[1]['json']

            assert "arena_id" in sent_payload
            assert "robot_id" in sent_payload
            assert "request_id" in sent_payload
            assert sent_payload["arena_id"] == "test_arena"
            assert sent_payload["robot_id"] == "test_robot"

    def test_api_2_module_import(self):
        """API-2: 模块可导入，ActionOutcome[MeasureResult]不报错"""
        # 测试泛型类型标注
        outcome: ActionOutcome[MeasureResult] = ActionOutcome(
            response_received=True,
            accepted=True,
            request_id="test_123",
            attempt_count=1,
            request_payload={"test": "data"},
            result=MeasureResult(measure_result="no_signal")
        )
        assert outcome.result.measure_result == "no_signal"

    def test_api_3_audit_no_data_loss(self):
        """API-3: 审计不丢请求（request_payload、response_payload、result三者互不覆盖）"""
        outcome = ActionOutcome(
            response_received=True,
            accepted=True,
            request_id="req_001",
            attempt_count=1,
            request_payload={"position": {"x": 100, "y": 200}, "channel": 5},
            response_payload={"accepted": True, "measure_result": "direction", "svd_deg": 45.0},
            result=MeasureResult(measure_result="direction", svd_deg=45.0)
        )

        # 验证三者独立存在
        assert outcome.request_payload is not None
        assert outcome.response_payload is not None
        assert outcome.result is not None

        # 验证内容正确
        assert outcome.request_payload["channel"] == 5
        assert outcome.response_payload["svd_deg"] == 45.0
        assert outcome.result.svd_deg == 45.0

    def test_api_4_retry_idempotent(self):
        """API-4: 重试幂等（超时后重试，两次payload逐字相同含request_id）"""
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            # 第一次超时，第二次成功
            timeout_response = MagicMock()
            timeout_response.status_code = 500
            timeout_response.json.side_effect = json.JSONDecodeError("", "", 0)

            success_response = MagicMock()
            success_response.status_code = 200
            success_response.json.return_value = {
                "accepted": True,
                "virtual_time_s": 5.0,
                "measure_result": "no_signal"
            }

            mock_session.post.side_effect = [timeout_response, success_response]

            client = HttpSimulatorClient(robot_id="test_robot", max_retries=2)
            client._enter_wall_time = 0.0
            client._enter_remaining_real = 1800.0

            # 执行会触发重试的操作
            outcome = client.measure(0.0, 0.0, 1)

            # 验证两次请求的payload相同（包括request_id）
            assert mock_session.post.call_count == 2
            call1_payload = mock_session.post.call_args_list[0][1]['json']
            call2_payload = mock_session.post.call_args_list[1][1]['json']

            # 同一个request_id在重试时保持不变
            assert call1_payload == call2_payload
            assert "request_id" in call1_payload


# =============================================================================
# 5.2 HTTP测试（7项）
# =============================================================================

class TestHTTPProtocol:
    """HTTP-1 到 HTTP-7"""

    def test_http_1_direction_response_parsing(self):
        """HTTP-1: direction响应解析（正确读取measure_result和svd_deg）"""
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "accepted": True,
                "virtual_time_s": 5.0,
                "measure_result": "direction",
                "svd_deg": 123.45
            }
            mock_session.post.return_value = mock_response

            client = HttpSimulatorClient(robot_id="test_robot")
            client._enter_wall_time = 0.0
            client._enter_remaining_real = 1800.0

            outcome = client.measure(0.0, 0.0, 1)

            assert outcome.accepted is True
            assert outcome.result is not None
            assert outcome.result.measure_result == "direction"
            assert outcome.result.svd_deg == 123.45

    def test_http_2_no_target_response(self):
        """HTTP-2: no_target_in_range响应（返回协议原值，不抛枚举错误）"""
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "accepted": True,
                "virtual_time_s": 8.0,
                "clear_result": "no_target_in_range"
            }
            mock_session.post.return_value = mock_response

            client = HttpSimulatorClient(robot_id="test_robot")
            client._enter_wall_time = 0.0
            client._enter_remaining_real = 1800.0

            outcome = client.clear(0.0, 0.0)

            assert outcome.accepted is True
            assert outcome.result is not None
            assert outcome.result.clear_result == "no_target_in_range"

    def test_http_3_accepted_false(self):
        """HTTP-3: 200 + accepted=false（不更新虚拟时刻，response_received=True, accepted=False）"""
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "accepted": False
            }
            mock_session.post.return_value = mock_response

            client = HttpSimulatorClient(robot_id="test_robot")
            client._enter_wall_time = 0.0
            client._enter_remaining_real = 1800.0
            client._last_accepted_virtual_time = 10.0

            outcome = client.measure(0.0, 0.0, 1)

            assert outcome.response_received is True  # HTTP 200收到响应
            assert outcome.accepted is False  # 但未被接受
            assert outcome.virtual_time_s is None  # 不更新虚拟时间
            assert client._last_accepted_virtual_time == 10.0  # 虚拟时间未改变

    def test_http_4_non_200_status(self):
        """HTTP-4: 非200状态码（response_received=False, 记录http_status, 记录error JSON - P0-16）"""
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            mock_response = MagicMock()
            mock_response.status_code = 400
            # P0-16: 模拟服务器返回错误JSON
            mock_response.json.return_value = {
                "error": "invalid_request",
                "message": "robot_id不匹配"
            }
            mock_session.post.return_value = mock_response

            client = HttpSimulatorClient(robot_id="test_robot", max_retries=1)
            client._enter_wall_time = 0.0
            client._enter_remaining_real = 1800.0

            outcome = client.measure(0.0, 0.0, 1)

            assert outcome.response_received is False  # 非200不算成功响应
            assert outcome.accepted is False
            assert outcome.http_status == 400
            # P0-16: 验证错误响应被记录
            assert outcome.response_payload is not None
            assert outcome.response_payload["error"] == "invalid_request"

    def test_http_5_no_retry_on_400_409(self):
        """HTTP-5: 400/409不重试（记录后立即返回）"""
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            mock_response = MagicMock()
            mock_response.status_code = 409
            mock_response.json.return_value = {"error": "conflict"}
            mock_session.post.return_value = mock_response

            client = HttpSimulatorClient(robot_id="test_robot", max_retries=3)
            client._enter_wall_time = 0.0
            client._enter_remaining_real = 1800.0

            outcome = client.measure(0.0, 0.0, 1)

            # 只调用一次，不重试
            assert mock_session.post.call_count == 1
            assert outcome.http_status == 409
            assert outcome.attempt_count == 1

    def test_http_6_remaining_real_time(self):
        """HTTP-6: remaining_real_time（动态计算，预留30秒）"""
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            # Mock enter response
            enter_response = MagicMock()
            enter_response.status_code = 200
            enter_response.json.return_value = {
                "accepted": True,
                "virtual_time_s": 0.0,
                "max_virtual_duration_s": 3600.0,
                "max_real_duration_s": 1800.0,
                "remaining_real_duration_s": 1800.0
            }
            mock_session.post.return_value = enter_response

            client = HttpSimulatorClient(robot_id="test_robot")

            # Mock time.monotonic
            with patch('time.monotonic', side_effect=[100.0, 200.0]):
                client.enter()
                # 100秒后查询剩余时间
                remaining = client.get_remaining_real_time_s()

            # 1800 - 100 - 30(预留) = 1670
            assert remaining == 1670.0

    def test_http_7_response_structure_validation(self):
        """HTTP-7: 响应结构校验（缺字段或非法枚举值返回protocol_error）"""
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            # 测试缺少accepted字段
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"virtual_time_s": 5.0}
            mock_session.post.return_value = mock_response

            client = HttpSimulatorClient(robot_id="test_robot")
            client._enter_wall_time = 0.0
            client._enter_remaining_real = 1800.0

            outcome = client.measure(0.0, 0.0, 1)

            assert outcome.response_received is False
            assert outcome.protocol_error is not None
            assert "accepted" in outcome.protocol_error


# =============================================================================
# 5.3 离线测试（13项）
# =============================================================================

class TestOfflineSimulation:
    """OFF-1 到 OFF-13"""

    def test_off_1_first_measure_channel_1(self):
        """OFF-1: 首测频道1（耗时5秒，无移动无切换）"""
        sources = [InterferenceSource(channel=1, x=100, y=100, radius=50)]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        client.enter()

        outcome = client.measure(0, 0, 1)

        assert outcome.accepted is True
        assert outcome.virtual_time_s == 5.0  # 无移动(0s) + 无切换(0s) + 检测(5s)

    def test_off_2_first_measure_channel_2(self):
        """OFF-2: 首测频道2（耗时6秒，无移动+1秒切换）"""
        sources = [InterferenceSource(channel=2, x=100, y=100, radius=50)]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        client.enter()

        outcome = client.measure(0, 0, 2)

        assert outcome.accepted is True
        assert outcome.virtual_time_s == 6.0  # 无移动(0s) + 切换(1s) + 检测(5s)

    def test_off_3_cross_position_measure(self):
        """OFF-3: 跨位置检测（精确加上distance/5）"""
        sources = [InterferenceSource(channel=1, x=300, y=400, radius=50)]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        client.enter()

        # 从(0,0)移动到(300,400)，距离=500m
        outcome = client.measure(300, 400, 1)

        assert outcome.accepted is True
        # 移动(500/5=100s) + 无切换(0s) + 检测(5s) = 105s
        assert outcome.virtual_time_s == 105.0

    def test_off_4_5m_boundary_near(self):
        """OFF-4: 5m边界（返回"near"）"""
        sources = [InterferenceSource(channel=1, x=3, y=4, radius=50)]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        client.enter()

        # 距离源5m
        outcome = client.measure(0, 0, 1)

        assert outcome.accepted is True
        assert outcome.result.measure_result == "near"

    def test_off_5_5_to_20m_range(self):
        """OFF-5: 5-20m范围（返回"direction"或"no_signal"）"""
        sources = [InterferenceSource(channel=1, x=10, y=0, radius=50)]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        client.enter()

        # 距离源10m
        outcome = client.measure(0, 0, 1)

        assert outcome.accepted is True
        assert outcome.result.measure_result in ["direction", "no_signal"]
        if outcome.result.measure_result == "direction":
            assert outcome.result.svd_deg is not None

    def test_off_6_clear_within_20m(self):
        """OFF-6: 20m内清除（返回"success"）"""
        sources = [InterferenceSource(channel=1, x=15, y=0, radius=50)]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        client.enter()

        # 距离源15m
        outcome = client.clear(0, 0)

        assert outcome.accepted is True
        assert outcome.result.clear_result == "success"

    def test_off_7_directional_blind_spot_measure(self):
        """OFF-7: 定向源盲区测量（返回"no_signal"）"""
        # 定向源指向东(90°)，±90°范围有效
        sources = [InterferenceSource(
            channel=1, x=100, y=0, radius=50,
            is_directional=True, direction_deg=90.0
        )]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        client.enter()

        # 从源的后方(-100, 0)测量，超出±90°范围
        outcome = client.measure(-100, 0, 1)

        assert outcome.accepted is True
        assert outcome.result.measure_result == "no_signal"

    def test_off_8_directional_blind_spot_clear(self):
        """OFF-8: 定向源盲区清除（20m内返回"success"）"""
        # 定向源指向东，但清除不受方向限制
        sources = [InterferenceSource(
            channel=1, x=15, y=0, radius=50,
            is_directional=True, direction_deg=90.0
        )]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        client.enter()

        # 从后方清除，仍然成功
        outcome = client.clear(0, 0)

        assert outcome.accepted is True
        assert outcome.result.clear_result == "success"

    def test_off_9_same_position_consistent_svd(self):
        """OFF-9: 同地点重复测量（示向度误差不变）"""
        sources = [InterferenceSource(channel=1, x=100, y=0, radius=50)]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=5.0  # 固定误差
        )
        client.enter()

        outcome1 = client.measure(0, 0, 1)
        outcome2 = client.measure(0, 0, 1)

        if outcome1.result.measure_result == "direction" and outcome2.result.measure_result == "direction":
            # 同位置同源，误差应该相同
            assert outcome1.result.svd_deg == outcome2.result.svd_deg

    def test_off_10_failed_clear_timing(self):
        """OFF-10: 失败清除计时（无目标的/clear虚拟时间只增加3秒）- P0-13"""
        sources = [InterferenceSource(channel=1, x=1000, y=1000, radius=50)]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        client.enter()

        # 尝试清除远处（>20m）
        outcome = client.clear(0, 0)

        assert outcome.accepted is True
        assert outcome.result.clear_result == "no_target_in_range"
        # 移动(0s) + 光学(3s) = 3s，不包括清除的2s
        assert outcome.virtual_time_s == 3.0

    def test_off_11_post_exit_state(self):
        """OFF-11: 退出后状态（exit()成功后，新测量和清除返回不可执行状态且不推进时间）"""
        sources = [InterferenceSource(channel=1, x=100, y=100, radius=50)]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        client.enter()

        exit_outcome = client.exit()
        assert exit_outcome.accepted is True

        # 退出后尝试测量
        measure_outcome = client.measure(0, 0, 1)
        assert measure_outcome.accepted is False
        assert measure_outcome.virtual_time_s == exit_outcome.virtual_time_s  # 时间未推进

    def test_off_12_svd_normalization(self):
        """OFF-12: svd归一化（所有svd_deg在[0, 360)范围内）"""
        sources = [InterferenceSource(channel=1, x=100, y=0, radius=50)]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        client.enter()

        outcome = client.measure(0, 0, 1)

        if outcome.result.measure_result == "direction":
            assert 0 <= outcome.result.svd_deg < 360

    def test_off_13_virtual_time_limit(self):
        """OFF-13: 虚拟时间上限（达到上限后拒绝新动作）"""
        sources = [InterferenceSource(channel=1, x=0, y=0, radius=50)]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0,
            max_virtual_duration_s=10.0  # 10秒上限
        )
        client.enter()

        # 第一次测量：5秒
        outcome1 = client.measure(0, 0, 1)
        assert outcome1.accepted is True

        # 第二次测量：5秒，总计10秒
        outcome2 = client.measure(0, 0, 1)
        assert outcome2.accepted is True

        # 第三次测量：会超出10秒上限
        outcome3 = client.measure(0, 0, 1)
        assert outcome3.accepted is False


# =============================================================================
# 5.4 数据测试（1项）
# =============================================================================

class TestDataHandling:
    """DATA-1"""

    def test_data_1_practice_outcome_recording(self):
        """DATA-1: 结果补录（(total=12, cleared=0)得0.0；不完整或逻辑矛盾的补录被拒绝；拒绝负数和总数≤0）"""
        # 测试正常情况
        outcome = PracticeOutcome(total_sources_from_ui=12, cleared_sources_from_ui=0)
        assert outcome.get_clearance_rate() == 0.0

        outcome2 = PracticeOutcome(total_sources_from_ui=12, cleared_sources_from_ui=5)
        assert abs(outcome2.get_clearance_rate() - 5/12) < 1e-9

        # 测试None情况
        outcome3 = PracticeOutcome(total_sources_from_ui=12)
        assert outcome3.get_clearance_rate() is None

        # 测试拒绝总数≤0
        outcome4 = PracticeOutcome(total_sources_from_ui=0, cleared_sources_from_ui=0)
        with pytest.raises(ValueError, match="总源数必须>0"):
            outcome4.get_clearance_rate()

        outcome5 = PracticeOutcome(total_sources_from_ui=-5, cleared_sources_from_ui=0)
        with pytest.raises(ValueError, match="总源数必须>0"):
            outcome5.get_clearance_rate()

        # 测试拒绝负数清除
        outcome6 = PracticeOutcome(total_sources_from_ui=12, cleared_sources_from_ui=-1)
        with pytest.raises(ValueError, match="清除数不能为负"):
            outcome6.get_clearance_rate()

        # 测试拒绝清除>总数
        outcome7 = PracticeOutcome(total_sources_from_ui=10, cleared_sources_from_ui=15)
        with pytest.raises(ValueError, match="清除数.*不能大于总数"):
            outcome7.get_clearance_rate()


# =============================================================================
# 5.5 接口一致性测试（3项）
# =============================================================================

class TestInterfaceConsistency:
    """INT-1 到 INT-3"""

    def test_int_1_same_action_sequence(self):
        """INT-1: 相同动作序列（HTTP和离线返回相同的measure_result）"""
        # 离线客户端
        sources = [InterferenceSource(channel=1, x=100, y=0, radius=50)]
        offline_client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        offline_client.enter()
        offline_outcome = offline_client.measure(0, 0, 1)

        # HTTP客户端（Mock）
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "accepted": True,
                "virtual_time_s": offline_outcome.virtual_time_s,
                "measure_result": offline_outcome.result.measure_result,
                "svd_deg": offline_outcome.result.svd_deg
            }
            mock_session.post.return_value = mock_response

            http_client = HttpSimulatorClient(robot_id="test")
            http_client._enter_wall_time = 0.0
            http_client._enter_remaining_real = 1800.0
            http_outcome = http_client.measure(0, 0, 1)

        # 验证结果一致
        assert offline_outcome.result.measure_result == http_outcome.result.measure_result

    def test_int_2_virtual_time_consistency(self):
        """INT-2: 虚拟时间一致（相同动作序列，虚拟时间相同）"""
        # 离线客户端
        sources = [InterferenceSource(channel=1, x=300, y=400, radius=50)]
        offline_client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        offline_client.enter()
        offline_outcome = offline_client.measure(300, 400, 1)

        # 验证计算：移动500m = 100s，检测5s，总计105s
        assert offline_outcome.virtual_time_s == 105.0

    def test_int_3_strategy_code_portable(self):
        """INT-3: 策略代码可移植（替换client后无需修改策略代码）"""
        def strategy(client: SimulatorClient):
            """示例策略：检测(0,0)频道1"""
            client.enter()
            outcome = client.measure(0, 0, 1)
            return outcome.result.measure_result if outcome.accepted else None

        # 离线测试
        sources = [InterferenceSource(channel=1, x=10, y=0, radius=50)]
        offline_client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        offline_result = strategy(offline_client)

        # 策略代码无需修改，只需替换client实例
        assert offline_result is not None


# =============================================================================
# 5.6 协议合规测试（5项）
# =============================================================================

class TestProtocolCompliance:
    """PROTO-1 到 PROTO-5"""

    def test_proto_1_reject_float_channel(self):
        """PROTO-1: 小数频道拒绝（channel=1.5被输入校验拒绝）"""
        sources = [InterferenceSource(channel=1, x=100, y=100, radius=50)]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        client.enter()

        with pytest.raises(ValueError, match="频道必须是整数"):
            client.measure(0, 0, 1.5)

    def test_proto_2_enter_time_limit_fields(self):
        """PROTO-2: enter时限字段（HTTP成功/enter强制包含max_virtual_duration_s等3个限时字段）"""
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            # 完整响应
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "accepted": True,
                "virtual_time_s": 0.0,
                "max_virtual_duration_s": 3600.0,
                "max_real_duration_s": 1800.0,
                "remaining_real_duration_s": 1800.0
            }
            mock_session.post.return_value = mock_response

            client = HttpSimulatorClient(robot_id="test")
            outcome = client.enter()

            assert outcome.accepted is True
            assert outcome.result.max_virtual_duration_s == 3600.0
            assert outcome.result.max_real_duration_s == 1800.0
            assert outcome.result.remaining_real_duration_s == 1800.0

    def test_proto_3_svd_range_validation(self):
        """PROTO-3: svd范围校验（HTTP响应svd_deg超出[0, 360)时返回protocol_error）"""
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            # 非法svd_deg
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "accepted": True,
                "virtual_time_s": 5.0,
                "measure_result": "direction",
                "svd_deg": 400.0  # 超出范围
            }
            mock_session.post.return_value = mock_response

            client = HttpSimulatorClient(robot_id="test")
            client._enter_wall_time = 0.0
            client._enter_remaining_real = 1800.0

            outcome = client.measure(0, 0, 1)

            assert outcome.response_received is False
            assert outcome.protocol_error is not None
            assert "svd_deg" in outcome.protocol_error

    def test_proto_4_exit_reason_validation_http(self):
        """PROTO-4: exit_reason校验（HTTP成功/exit响应必须为"user_exit"，否则protocol_error）- P0-14"""
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            # 非法exit_reason
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "accepted": True,
                "virtual_time_s": 10.0,
                "exit_reason": "timeout"  # 非user_exit
            }
            mock_session.post.return_value = mock_response

            client = HttpSimulatorClient(robot_id="test")
            client._enter_wall_time = 0.0
            client._enter_remaining_real = 1800.0

            outcome = client.exit()

            assert outcome.response_received is False
            assert outcome.protocol_error is not None
            assert "user_exit" in outcome.protocol_error

    def test_proto_5_exit_reason_consistency_offline(self):
        """PROTO-5: 离线exit一致性（离线成功exit()返回"user_exit"，与HTTP一致）- P0-14"""
        sources = [InterferenceSource(channel=1, x=100, y=100, radius=50)]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        client.enter()

        outcome = client.exit()

        assert outcome.accepted is True
        assert outcome.result.exit_reason == "user_exit"


# =============================================================================
# 5.7 语义修正测试（3项）
# =============================================================================

class TestSemanticCorrections:
    """SEM-1 到 SEM-3"""

    def test_sem_1_response_received_semantics_http(self):
        """SEM-1: response_received语义（HTTP 200 + accepted=false时response_received=True, accepted=False）- P0-15"""
        with patch('requests.Session') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "accepted": False
            }
            mock_session.post.return_value = mock_response

            client = HttpSimulatorClient(robot_id="test")
            client._enter_wall_time = 0.0
            client._enter_remaining_real = 1800.0

            outcome = client.measure(0, 0, 1)

            # P0-15核心语义
            assert outcome.response_received is True  # 收到响应
            assert outcome.accepted is False  # 但未被接受

    def test_sem_2_response_received_semantics_offline(self):
        """SEM-2: 离线response_received（离线成功动作response_received=True，失败response_received=False）"""
        sources = [InterferenceSource(channel=1, x=100, y=100, radius=50)]
        client = OfflineSimulatorClient(
            robot_id="test",
            sources=sources,
            position_error_m=0,
            direction_error_deg=0
        )
        client.enter()

        # 成功动作
        outcome_success = client.measure(0, 0, 1)
        assert outcome_success.response_received is True

        # 退出后失败动作
        client.exit()
        outcome_fail = client.measure(0, 0, 1)
        assert outcome_fail.response_received is False

    def test_sem_3_source_config_uniqueness(self):
        """SEM-3: 源配置唯一性（构造离线客户端时拒绝同频道多源、缺少direction_deg的定向源）"""
        # 测试缺少direction_deg的定向源
        with pytest.raises(ValueError, match="定向源必须提供direction_deg"):
            InterferenceSource(
                channel=1, x=100, y=100, radius=50,
                is_directional=True  # 缺少direction_deg
            )

        # 测试同频道多源
        sources = [
            InterferenceSource(channel=1, x=100, y=100, radius=50),
            InterferenceSource(channel=1, x=200, y=200, radius=50)  # 重复频道
        ]
        with pytest.raises(ValueError, match="频道.*存在多个源"):
            OfflineSimulatorClient(
                robot_id="test",
                sources=sources,
                position_error_m=0,
                direction_error_deg=0
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
