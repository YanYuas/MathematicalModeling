# -*- coding: utf-8 -*-
"""把 Q4 专属脚本从共享目录 `核验脚本/` 外迁到 `核验脚本_Q4/`。

为什么：`核验脚本/` 现在有三个写入方（Q3 窗口、Q4 窗口、总控）。共享目录被多方写，
迟早出现静默覆盖。把 Q4 专属件挪走，共享目录只留双方都读、或经双方同意增量扩展的文件。

为什么带闸门：Q4 窗口在活跃迭代中。文件被挪走时它的下一次调用会报"找不到"，
然后可能**在旧路径重建一份** ⇒ 反而制造出两份分叉副本，比不挪更糟。
⇒ 本脚本只在"近 N 分钟无写入、且没有 Q4 驱动在跑"时才动手。

**刻意不挪**（这几个是双方共用的、Q4 窗口做的增量扩展，挪走会破坏共享）：
  _mock_simulator.py       Q4 加了 sector 模式（定向源/盲区）
  _run_client_selftest.py  Q4 加了 SECTOR_TEST
  以及 Q3 侧的一切。

用法：
    py -3.11 _migrate_q4_scripts.py            # 只体检，不动作
    py -3.11 _migrate_q4_scripts.py --apply    # 安静则执行迁移

退出码：0 = 已就绪/已完成；2 = 窗口活跃，跳过（属正常，不是错误）。
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
DEST = os.path.join(REPO, '03_编程手', '核验脚本_Q4')

# Q4 专属 —— 全部是 UNTRACKED，移动纯属文件系统操作，不涉及 git
# 【2026-09-13 改】原先是固定清单，结果第一次迁移刚做完，Q4 窗口又新造了 8 个 Q4 文件
# （_collect_q4_runs.py、_q4_offline_runs_{std,extreme,seed8,allomni}.csv、_q4_summary_table.md …）
# ⇒ 改为**通配**：文件名含 `q4` 就归 Q4 侧。自愈，不用每次追加清单。
# 只收 .py/.bat/.txt/.csv/.md —— 不含 .m（.m 是 MATLAB 源码，归 v2.0 目录，不归这里）。
Q4_GLOBS = ['*q4*.py', '*q4*.bat', '*q4*.txt', '*q4*.csv', '*q4*.md']
# 刻意留在共享目录
KEEP_SHARED = ['_mock_simulator.py', '_run_client_selftest.py', '_mini_sim_q3.py', '_run_mini_sim.py']


def q4_files(root):
    """共享目录里**当前还在**的 Q4 专属文件（按 Q4_GLOBS 通配）。

    排除两类：
      · KEEP_SHARED —— 刻意留在共享目录的共用件
      · 本脚本自身 —— 它的名字里就含 "q4"（migrate_**q4**_scripts），
        不排除的话第一次跑就会把自己搬走。
    """
    hits = set()
    for pat in Q4_GLOBS:
        for p in glob.glob(os.path.join(root, pat)):
            if os.path.isfile(p):
                hits.add(os.path.basename(p))
    return sorted(hits - set(KEEP_SHARED) - {os.path.basename(__file__)})


def quiet_seconds(root):
    """共享目录里最近一次写入距今多少秒。"""
    newest = 0.0
    for fn in os.listdir(root):
        p = os.path.join(root, fn)
        if os.path.isfile(p):
            newest = max(newest, os.path.getmtime(p))
    return time.time() - newest if newest else 1e9


def q4_running():
    """有没有 Q4 驱动/模拟器进程在跑。tasklist 在无进程时返回非零，属正常。"""
    try:
        out = subprocess.run(['wmic', 'process', 'get', 'CommandLine'],
                             capture_output=True, text=True, encoding='mbcs',
                             errors='replace', timeout=20).stdout or ''
    except Exception:
        return []
    hits = []
    for ln in out.splitlines():
        low = ln.lower()
        if ('_mini_sim_q4' in low or '_run_mini_sim_q4' in low) and 'wmic' not in low:
            hits.append(ln.strip()[:100])
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='安静则真正执行迁移')
    ap.add_argument('--quiet-min', type=float, default=8.0, help='安静判据：近 N 分钟无写入')
    a = ap.parse_args()

    print('共享目录: %s' % HERE)
    print('目标目录: %s' % DEST)
    print('-' * 68)

    # 先算候选 —— 即使这轮要跳过，也要让人看见"还剩哪些没迁"，否则无从判断闸门值不值得等
    present = q4_files(HERE)
    if not present:
        print('\n[完成] 共享目录里已无 Q4 专属文件，无需动作。')
        return 0
    print('\n待迁移 %d 个：' % len(present))
    for f in present:
        print('   %s' % f)

    qs = quiet_seconds(HERE)
    procs = q4_running()
    print('\n最近写入距今 %.1f 分钟（阈值 %.1f）' % (qs / 60.0, a.quiet_min))
    print('Q4 相关进程: %s' % (procs if procs else '无'))

    busy = (qs < a.quiet_min * 60) or bool(procs)
    if busy:
        why = []
        if qs < a.quiet_min * 60:
            why.append('近 %.1f 分钟内有写入' % (qs / 60.0))
        if procs:
            why.append('%d 个 Q4 进程在跑' % len(procs))
        print('\n[跳过] Q4 窗口活跃（%s）—— 此时挪文件会让它在旧路径重建副本。' % '；'.join(why))
        print('      下次巡查再试。')
        return 2

    print('窗口已安静。')

    if not a.apply:
        print('\n体检模式：未动作。加 --apply 执行。')
        return 0

    os.makedirs(DEST, exist_ok=True)
    moved = []
    for f in present:
        src, dst = os.path.join(HERE, f), os.path.join(DEST, f)
        shutil.move(src, dst)
        moved.append(f)
    print('\n已移动 %d 个文件到 核验脚本_Q4/' % len(moved))

    # 迁移说明留在旧位置 —— 那边的窗口若来找不到文件，一眼看到去向
    with open(os.path.join(HERE, '迁移说明.md'), 'w', encoding='utf-8', newline='') as f:
        f.write(
            '# 迁移说明：Q4 专属脚本已外迁\n\n'
            '> 2026-09-13 ｜ 执行者：总控\n\n'
            '`核验脚本/` 有三个写入方（Q3 窗口、Q4 窗口、总控），共享目录被多方写会静默覆盖。\n'
            '因此把 **Q4 专属**件挪到了同级的 `03_编程手/核验脚本_Q4/`：\n\n' +
            ''.join('- `%s`\n' % f for f in moved) +
            '\n## 路径不变\n\n'
            '`核验脚本_Q4/` 与 `核验脚本/` **同深度**，所以脚本里 `HERE/../..` 仍解析到仓库根，\n'
            '`HERE/xxx` 仍解析到自己所在目录。**相对路径数学一个字没改，脚本里的路径不用动。**\n\n'
            '## 仍留在共享目录（刻意）\n\n' +
            ''.join('- `%s`\n' % f for f in KEEP_SHARED) +
            '\n这几个是**双方共用的**，Q4 窗口对它们做的是**增量扩展**（`_mock_simulator.py` 加 `sector` 模式、\n'
            '`_run_client_selftest.py` 加 `SECTOR_TEST`），挪走会破坏共享。共享文件请只做**向后兼容的追加**，\n'
            '不要重写他人已写的分支。\n'
        )

    with open(os.path.join(DEST, 'README.md'), 'w', encoding='utf-8', newline='') as f:
        f.write(
            '# 核验脚本_Q4 —— Q4 专属工具\n\n'
            '> 从 `../核验脚本/` 外迁而来（2026-09-13）。原因：共享目录三方共写，会静默覆盖。\n\n'
            '## 这里放什么\n\n'
            '只属于 Q4 的东西：Q4 迷你模拟器、Q4 离线驱动、Q4 一键入口、Q4 离线结果。\n\n'
            '## 这里不放什么\n\n'
            '**共享件留在 `../核验脚本/`**，不要复制过来：\n' +
            ''.join('- `%s`\n' % f for f in KEEP_SHARED) +
            '\n需要改共享件时，改原位、且只做**向后兼容的追加**。复制一份 = 制造分叉。\n\n'
            '## 跑法\n\n'
            '```bat\npy -3.11 _run_mini_sim_q4.py --seeds 2026,7,99 --n 13\n```\n\n'
            '一键入口：`一键_跑Q4离线.bat`（双击）。\n'
        )
    print('已写 核验脚本/迁移说明.md 与 核验脚本_Q4/README.md')

    # 验证路径数学没坏：--help 会走完 argparse 的全部路径拼装后立即退出，安全
    r = subprocess.run([sys.executable, os.path.join(DEST, '_run_mini_sim_q4.py'), '--help'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
    ok = r.returncode == 0
    print('迁移后自检（--help，退码 %d）: %s' % (r.returncode, '通过' if ok else '失败'))
    if not ok:
        print((r.stderr or '')[:400])
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
