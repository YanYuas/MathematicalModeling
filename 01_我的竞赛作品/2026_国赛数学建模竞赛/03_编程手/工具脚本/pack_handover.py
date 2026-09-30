# -*- coding: utf-8 -*-
"""打包「Q3 策略转交件」—— 供经 QQ 发送给编程手。

为什么用 Python 而不是纯 .bat：本项目目录名是中文（`03_编程手`），
而 .bat 内容若不是纯 ASCII，cmd 在 cp936 控制台下会**把 echo 行拆断**
（2026-09-12 已实际踩过两次）。.bat 只留一行 ASCII 调用本脚本。

打包内容（**不含** `logs/`、`__pycache__`、临时 json）：
  · `03_编程手/MATLAB_Framework/`   —— 策略代码 + 测试 + 操作手册 + 一键入口
  · `03_编程手/核验脚本/`            —— 离线迷你模拟器 + 11 项自测 + 运行器 + 日志分析
  · `03_编程手/核验往来/`            —— 断言核验报告 / 回执 / 自记录日志样例
  · `03_编程手/Q3策略_转交编程手_*.md` —— 转交说明
  · `00_任务总控/` 的四个控制文档     —— 成果数字 + 改动历史（只读参考）

⚠️ **刻意排除** `MATLAB_Framework/logs/`：机器人自记录日志的**文件名与内容含真实队号**，
    赛题要求支撑材料中隐去队号 ⇒ 不随包发送（需要时单独脱敏）。

用法（由 `一键_打包转交.bat` 调用，或直接 `py -3.11 打包转交件.py`）：
输出：桌面 `Q3策略_转交编程手_<日期>.zip`
"""
import os
import sys
import zipfile
from datetime import datetime

try:
    sys.stdout.reconfigure(errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..'))
DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')

# (相对仓库根的路径, 是否是目录)
ITEMS = [
    ('03_编程手/MATLAB_Framework', True),
    ('03_编程手/核验脚本', True),
    ('03_编程手/核验往来', True),
    ('00_任务总控/进度看板.md', False),
    ('00_任务总控/CHANGELOG.md', False),
    ('00_任务总控/权威数字表.md', False),
    ('00_任务总控/版本管理规范.md', False),
]

SKIP_DIRS = {'logs', '__pycache__', '.git', '文档_历史'}
SKIP_SUFFIX = ('_原版.py', )
SKIP_NAMES = {'_crossval_cases.json', '_crossval_matlab.json',
              '_crossval_python.json', '_crossval_console.txt',
              '_mini_sim_result.txt', '_selftest_result.txt',
              '_offline_tests_result.txt', '_real_runs_analysis.txt'}


def skip_file(name):
    if name in SKIP_NAMES:
        return True
    if any(name.endswith(s) for s in SKIP_SUFFIX):
        return True
    return False


def main():
    stamp = datetime.now().strftime('%Y-%m-%d')
    zip_name = 'Q3策略_转交编程手_%s.zip' % stamp
    zip_path = os.path.join(DESKTOP, zip_name)
    if not os.path.isdir(DESKTOP):
        zip_path = os.path.join(REPO, zip_name)

    n_file = 0
    total = 0
    skipped_logs = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel, is_dir in ITEMS:
            src = os.path.join(REPO, rel.replace('/', os.sep))
            if not os.path.exists(src):
                print('⚠️ 缺件，跳过：%s' % rel)
                continue
            if not is_dir:
                z.write(src, rel)
                n_file += 1
                total += os.path.getsize(src)
                continue
            for root, dirs, files in os.walk(src):
                # 先统计再剪枝：logs/ 含真实队号，必须排除
                for d in list(dirs):
                    if d == 'logs':
                        lp = os.path.join(root, d)
                        skipped_logs += sum(len(fs) for _, _, fs in os.walk(lp))
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for f in files:
                    if skip_file(f):
                        continue
                    fp = os.path.join(root, f)
                    arc = os.path.relpath(fp, REPO).replace(os.sep, '/')
                    z.write(fp, arc)
                    n_file += 1
                    total += os.path.getsize(fp)
        # 转交件单独找（文件名带日期，用通配）：策略论证 + 行动清单
        for f in sorted(os.listdir(os.path.join(REPO, '03_编程手'))):
            if not f.endswith('.md'):
                continue
            if not (f.startswith('Q3策略_转交编程手') or f.startswith('转交清单_')):
                continue
            fp = os.path.join(REPO, '03_编程手', f)
            z.write(fp, '03_编程手/%s' % f)
            n_file += 1
            total += os.path.getsize(fp)

    size_mb = total / 1024 / 1024
    print('=' * 68)
    print('打包完成：%s' % zip_path)
    print('  文件数 %d ｜ 原始大小 %.2f MB ｜ zip 大小 %.2f MB'
          % (n_file, size_mb, os.path.getsize(zip_path) / 1024 / 1024))
    print('  （已排除 logs/ 共 %d 个文件 —— 含真实队号，不随包发送）' % skipped_logs)
    print('=' * 68)
    return 0


if __name__ == '__main__':
    sys.exit(main())
