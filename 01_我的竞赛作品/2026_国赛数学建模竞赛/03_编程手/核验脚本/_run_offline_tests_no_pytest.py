# -*- coding: utf-8 -*-
"""无 pytest 环境下运行 `Q3/SimulatorClient_v1.3.1/tests/test_simulator_client.py` 的 36 项离线测试。

为什么需要它：本机 **未安装 pytest**（且本项目规则不允许从终端下载依赖），
而该测试文件对 pytest 的依赖面**只有 `pytest.raises`（7 处）+ 一个 `pytest.main`**，
无 fixture / mark / parametrize / unittest.TestCase ⇒ 注入一个极小 shim 即可用标准库跑完，
从而**不依赖任何下载**就能得到真实的通过/失败证据。

解释器：**必须用装有 requests + numpy 的那个**（本机是 Python 3.11.9；`py -3` 会解析到 3.13，缺依赖）。
控制台编码：**不强制 UTF-8**（本机控制台是 cp936，强设会乱码）；用 `errors='replace'` 防崩，
完整报告另以 **UTF-8** 写入 `_offline_tests_result.txt`（供工具/审阅稳定读取）。

用法：
    py -3.11 _run_offline_tests_no_pytest.py

退出码：0 = 全部通过；1 = 有测试失败；2 = 环境缺依赖（requests/numpy）。
"""
import importlib.util
import inspect
import os
import sys
import traceback
import types

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, '..', 'Q3', 'SimulatorClient_v1.3.1'))
SRC = os.path.join(PKG, 'src')
TESTS = os.path.join(PKG, 'tests', 'test_simulator_client.py')
RESULT = os.path.join(HERE, '_offline_tests_result.txt')

_buf = []


def out(line=''):
    _buf.append(line)
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode(sys.stdout.encoding or 'utf-8', 'replace').decode(
            sys.stdout.encoding or 'utf-8', 'replace'))


# ---- 极小 pytest shim（只实现测试文件真正用到的那两个符号）----
class _Raises:
    def __init__(self, expected):
        self.expected = expected

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            raise AssertionError('DID NOT RAISE %r' % (self.expected,))
        return issubclass(exc_type, self.expected)


_shim = types.ModuleType('pytest')
_shim.raises = lambda expected, *a, **k: _Raises(expected)
_shim.main = lambda *a, **k: 0
sys.modules.setdefault('pytest', _shim)


def main():
    out('运行器解释器: %s' % sys.executable)
    out('Python: %s' % sys.version.split()[0])

    # ---- 环境预检：给缺依赖一个干净的报错，而不是甩 traceback ----
    missing = []
    for name in ('requests', 'numpy'):
        try:
            __import__(name)
        except ImportError:
            missing.append(name)
    if missing:
        out('')
        out('[环境不足] 该解释器缺: %s' % ', '.join(missing))
        out('本机装有依赖的解释器是 **Python 3.11.9**（`py -3.11` 或 `python`）。')
        out('注意：`py -3` 会解析到 Python 3.13，那个环境**没有** requests/numpy。')
        return 2

    if not os.path.exists(TESTS):
        out('找不到测试文件：%s' % TESTS)
        return 2

    sys.path.insert(0, SRC)
    spec = importlib.util.spec_from_file_location('test_simulator_client', TESTS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    passed, failed = 0, 0
    failures = []
    for cname, cls in sorted(vars(mod).items()):
        if not (cname.startswith('Test') and inspect.isclass(cls)):
            continue
        if cls.__module__ != mod.__name__:
            continue
        for mname, meth in sorted(vars(cls).items()):
            if not mname.startswith('test_'):
                continue
            label = '%s::%s' % (cname, mname)
            try:
                meth(cls())
                passed += 1
                out('  [PASS] %s' % label)
            except Exception as exc:
                failed += 1
                failures.append((label, exc))
                out('  [FAIL] %s  --  %s: %s' % (label, type(exc).__name__, exc))

    out('')
    out('=' * 72)
    for label, exc in failures:
        out('失败详情: %s' % label)
        out(''.join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
        out('-' * 72)
    out('通过 %d ｜ 失败 %d ｜ 总计 %d' % (passed, failed, passed + failed))
    out('=' * 72)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    rc = main()
    # 报告另存 UTF-8（控制台可能是 cp936，重定向后编码不稳）
    try:
        with open(RESULT, 'w', encoding='utf-8', newline='') as f:
            f.write('\n'.join(_buf) + '\n')
        print('报告已写入: %s' % RESULT)
    except Exception as exc:
        print('报告写入失败: %s' % exc)
    sys.exit(rc)
