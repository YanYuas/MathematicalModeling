# -*- coding: utf-8 -*-
"""验证 `/enter` 的**等待窗口**：模拟器晚于程序就绪时，程序应当等待而不是死掉。

真实场景：MATLAB 启动约 40 s，而模拟器倒计时只有 5 s
⇒ 程序可能在接口开放**之前**就绪。旧版只重试 3 次（约 1.5 s）就退出。

本驱动刻意制造这个时序：
    t=0    启动 MATLAB（此时 2026 端口无监听）
    t≈40s  MATLAB 就绪，开始尝试 /enter ⇒ 连接被拒 ⇒ 应进入等待循环
    t=62s  才启动 mock 模拟器
    ⇒ 程序应当**等到** 62s 之后成功 /enter（复用同一 request_id）
"""
import os
import re
import socket
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
MATLAB_SRC = os.path.join(REPO, '03_编程手', 'MATLAB_Framework')
MOCK = os.path.join(HERE, '_mock_simulator.py')
MATLAB = r'D:\R2026a_Windows\bin\matlab.exe'
PORT = 20270  # 刻意避开 2026 —— 那是真模拟器的端口
OUT = os.path.join(HERE, '_enter_wait_result.txt')


def port_busy(port):
    try:
        with socket.create_connection(('127.0.0.1', port), 0.3):
            return True
    except OSError:
        return False


def main():
    if port_busy(PORT):
        sys.exit('端口 %d 已被占用 —— 先关掉模拟器/旧 mock' % PORT)

    # 只测客户端 /enter 的等待行为，**不跑整条策略**
    # （整条策略对本地 mock 要 ~294 s，会淹没这个测试，没必要）
    cmd = ("diary('%s'); " % OUT.replace('\\', '/') +
           "c = SimulatorClient('http://127.0.0.1:%d','TESTTEAM'); " % PORT +
           "t = tic; r = c.enter(); " +
           "fprintf('EW_OK waited=%.1f remaining=%.0f\\n', toc(t), r.remaining_real_duration_s); " +
           "c.close_log(); diary off")
    print('启动 MATLAB（无模拟器）...', flush=True)
    p = subprocess.Popen([MATLAB, '-nosplash', '-sd', MATLAB_SRC, '-batch', cmd],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding='utf-8', errors='replace')

    t0 = time.time()
    print('等 62 s（让 MATLAB 就绪并进入 /enter 等待循环）...', flush=True)
    time.sleep(62)

    print('t=%.0fs 启动 mock 模拟器' % (time.time() - t0), flush=True)
    mock = subprocess.Popen([sys.executable, MOCK, '--mode', 'ok', '--port', str(PORT)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for _ in range(60):
        if port_busy(PORT):
            break
        time.sleep(0.2)

    try:
        out, _ = p.communicate(timeout=180)
    except subprocess.TimeoutExpired:
        p.kill()
        out = ''
    rc = p.returncode
    mock.terminate()
    try:
        mock.wait(timeout=5)
    except Exception:
        mock.kill()

    # diary 是权威输出（管道在 kill 时会丢缓冲，diary 不会）
    try:
        with open(OUT, encoding='utf-8', errors='replace') as f:
            diary = f.read()
    except OSError:
        diary = ''
    text = diary + (out or '')

    # 【2026-09-13 总控修正】原模式 `接口尚未开放.*重试 /enter` 匹配的是**旧措辞**，
    # 该 fprintf 在提交 9b01124 里被改为「等待接口开放… 已等 X s / Y s」⇒ 原正则永远不匹配、
    # 断言静默失效（返回值恒 False，不报错）。改为兼容新旧两种措辞。
    waited = bool(re.search(r'(接口尚未开放|等待接口开放)', text))
    ok_enter = bool(re.search(r'/enter 等待 [\d.]+ s 后成功', text))
    done = 'EW_OK' in text

    print('=' * 72)
    print('  %-46s %s' % ('进入等待循环（接口未开放时提示并重试）', '是' if waited else '否'))
    print('  %-46s %s' % ('等待后 /enter 成功（复用同一 request_id）', '是' if ok_enter else '否'))
    print('  %-46s %s' % ('正常收尾（EW_OK）', '是' if done else '否'))
    print('  MATLAB 退出码 = %s' % rc)
    print('=' * 72)
    if not (waited and ok_enter and done):
        print('--- diary 全文 ---')
        print(text)
    allok = waited and ok_enter and done
    print('结论：%s' % ('全部通过' if allok else '有失败'))
    print('完整输出：%s' % OUT)
    return 0 if allok else 1


if __name__ == '__main__':
    sys.exit(main())
