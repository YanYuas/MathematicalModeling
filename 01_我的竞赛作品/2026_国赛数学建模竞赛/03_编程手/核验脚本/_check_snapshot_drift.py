# -*- coding: utf-8 -*-
"""快照漂移检测：`MATLAB_Framework_v2.0/参考文档/` 与各自原位是否仍然一致。

为什么需要：v2.0 的参考文档是**快照**（只读副本），权威仍在原位。原位一旦更新，
快照就悄悄过期 —— 而 Q4 的算法推导恰恰要拿这些文档当依据，过期的依据比没有依据更危险。

用法：
    py -3.11 _check_snapshot_drift.py            # 默认查 v2.0
    py -3.11 _check_snapshot_drift.py --snap <别的快照根目录>

退出码：0 = 全部一致；1 = 有漂移或缺失（此时**以原位为准**，重新同步快照）。
"""
import argparse
import hashlib
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
DEFAULT_SNAP = os.path.join(REPO, '03_编程手', 'MATLAB_Framework_v2.0', '参考文档')

# (快照子目录, 快照文件名, 权威原位相对仓库根的路径)
# 与 `参考文档/README_快照说明.md` §一 的索引表一一对应；改索引表时这里同步。
PAIRS = [
    ('Q4_建模文档_快照', '00-移交说明.md', '02_建模手/Q4/00-移交说明.md'),
    ('Q4_建模文档_快照', 'Q4全解总览.md', '02_建模手/Q4/Q4全解总览.md'),
    ('Q4_建模文档_快照', 'Q4公式表.md', '02_建模手/Q4/Q4公式表.md'),
    ('Q4_建模文档_快照', 'Q4建模数学化.md', '02_建模手/Q4/Q4建模数学化.md'),
    ('Q4_建模文档_快照', 'Q4数学原理总理顺.md', '02_建模手/Q4/Q4数学原理总理顺.md'),
    ('Q4_建模文档_快照', 'Q4模型假设与陷阱深挖.md', '02_建模手/Q4/Q4模型假设与陷阱深挖.md'),
    ('Q4_建模文档_快照', 'Q4深度分析.md', '02_建模手/Q4/Q4深度分析.md'),
    ('Q4_建模文档_快照', 'Q4陷阱与几何拓展.md', '02_建模手/Q4/Q4陷阱与几何拓展.md'),
    ('Q4_建模文档_快照', '经验总结.md', '02_建模手/Q4/经验总结.md'),
    ('论文侧', '论文组织方案.md', '04_论文手/Q4/论文组织方案.md'),
    ('Q3_交接文档_快照', '交接文档_编程手_2026-09-13.md', '03_编程手/Q3/交接文档_编程手_2026-09-13.md'),
    ('Q3_交接文档_快照', 'Q3调优经验与补丁记录.md', '03_编程手/Q3调优经验与补丁记录.md'),
    ('Q3_交接文档_快照', 'Q3演练数据汇总_2026-09-13.md', '03_编程手/Q3演练数据汇总_2026-09-13.md'),
    ('Q3_交接文档_快照', '交接文档_程序运行原理与调试过程.md', '04_论文手/Q3/交接文档_程序运行原理与调试过程.md'),
    ('Q3_交接文档_快照', '演练数据集_2026-09-13.md', '04_论文手/Q3/演练数据集_2026-09-13.md'),
]


def _norm_md5(path):
    """先归一 `\\r\\n` 再算 —— 与 `代码库/自检_副本一致性.py` 同法，
    免得 CRLF/LF 的差别被误报成内容漂移。"""
    with open(path, 'rb') as f:
        return hashlib.md5(f.read().replace(b'\r\n', b'\n')).hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--snap', default=DEFAULT_SNAP, help='快照根目录（默认 v2.0 的 参考文档/）')
    a = ap.parse_args()

    snap = os.path.abspath(a.snap)
    if not os.path.isdir(snap):
        sys.exit('快照目录不存在: %s' % snap)
    print('快照根: %s' % snap)
    print('权威根: %s\n' % REPO)

    ok, bad = 0, []
    for sub, name, orig in PAIRS:
        sp = os.path.join(snap, sub, name)
        op = os.path.join(REPO, orig)
        if not os.path.exists(sp):
            bad.append((name, '快照缺失', sp))
            continue
        if not os.path.exists(op):
            bad.append((name, '原位缺失', op))
            continue
        ms, mo = _norm_md5(sp), _norm_md5(op)
        if ms == mo:
            ok += 1
        else:
            bad.append((name, '%s vs %s' % (ms, mo), orig))

    for name, why, where in bad:
        print('  DRIFT  %-40s %s  (%s)' % (name, why, where))
    print('=' * 72)
    print('快照核对: %d/%d 一致，%d 异常' % (ok, len(PAIRS), len(bad)))
    if bad:
        print('处置：以**原位**为准，把漂移的文件重新复制过来，并刷新 README 的 md5 表。')
    print('=' * 72)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
