# 问题2：固定轮廓线长优化 - 技术设计文档 v2.1

> **For agentic workers:** 本文档为v2审核后修正版，已补充FastSA集成方案  
> **日期**: 2026-08-08  
> **状态**: READY FOR IMPLEMENTATION  
> **版本**: v2.1 (修正FastSA集成缺失问题)

---

## [v2.1修正] 改进摘要

**v2.1相比v2的关键修正**：
1. ✅ **[新增]** 补充3.5节"FastSA集成策略"（ConstrainedSAWrapper完整实现）
2. ✅ **[修正]** q2_main.py的SA调用逻辑（第929-947行改为完整实现）
3. ✅ **[调整]** 时间估算（3小时→3.5小时，含FastSA集成调试）
4. ✅ **[优化]** 简化成本函数惩罚项（提升可读性）
5. ✅ **[增强]** Phase1失败检查（可行率<1%时终止）

**v2审核发现的关键缺陷**（已修正）：
- ❌ FastSA接口不兼容（cost_func返回float，Q2返回三元组）
- ❌ best_so_far过滤逻辑缺失（FastSA不知道is_feasible）
- ❌ SA主循环只有"简化版"注释，无具体实现

---

## 改进摘要（v2版本）

**审核发现的3个关键风险**：
1. ❌ 相对import可能失效（不同运行目录）
2. ❌ 自适应λ参数（0.4/0.8阈值）未针对HPWL场景调优
3. ❌ warm_start策略不明确（问题1窄长型 vs 问题2正方形）

**本版本的3个改进**：
1. ✅ [改进] 增加成本诊断函数（每1000次输出成本分布）
2. ✅ [改进] 分阶段SA（Phase1高λ找可行解 → Phase2低λ优化HPWL）
3. ✅ [改进] 调整实施优先级（random+ffd先行，warm_start后补）

**关键修正**：
- 修正import逻辑（pathlib绝对路径 + 异常处理）
- 设计λ敏感性测试方案（5×3实验矩阵）
- 明确warm_start三种策略并推荐最优

---

## 1. 目标

在**固定正方形轮廓S×S**约束下，优化VLSI模块布局使得**总线长(HPWL)最小化**。

**核心差异 vs 问题1**：
- 问题1：最小化芯片面积（自由轮廓）
- 问题2：固定轮廓，最小化线网互连线长

**成功标准**（扩展版）：
- ✅ **可行性红线**: 所有解满足 M=max(W,H) ≤ S
- ✅ **性能区间**: HPWL落在合理区间（n100: 150k~295k之间）
- ✅ **机制有效性**: 自适应λ实验优于固定λ（HPWL改善≥5%）
- ✅ **收敛性**: 收敛曲线呈平台期（最后500次HPWL标准差<1%均值）
- ✅ **鲁棒性**: 5个随机种子的HPWL相对标准差<10%
- ✅ **效率**: n100单次运行<5分钟，n300<30分钟

---

## 2. 架构设计

### 2.1 总体架构

**方案A：最小改动架构（推荐）**

```
问题2/题代码/
├── q2_main.py              # 主程序入口
├── q2_cost.py              # HPWL成本函数 + 成本诊断
├── q2_adaptive_lambda.py   # 自适应λ机制 + 分阶段SA
├── q2_warmstart.py         # 初始化策略（可选）
└── [复用问题1 via 绝对路径import]
    ├── from btree import BTree
    ├── from operators import random_perturbation
    ├── from fast_sa import FastSA
    └── from data_loader import Block
```

**设计原则**（不变）：
1. **零改动问题1代码**：避免破坏运行中的实验
2. **4个新模块<600行**：核心改动集中在成本函数和包装层
3. **渐进式开发**：random初始化立即可用，warm_start后补

### 2.2 [改进] 修正Import逻辑

**问题**：原设计使用相对路径 `sys.path.insert`，在不同运行目录下会失效。

**解决方案**：使用pathlib绝对路径 + 异常处理

```python
# q2_main.py 头部（完整可执行版本）
from pathlib import Path
import sys

def setup_imports():
    """
    健壮的import配置：自动定位问题1代码目录
    
    支持3种运行场景：
    1. 从 问题2/题代码/ 运行
    2. 从 华数杯/ 根目录运行
    3. 从任意位置运行（通过环境变量）
    """
    # 当前文件所在目录
    current_file = Path(__file__).resolve()
    q2_code_dir = current_file.parent  # 问题2/题代码/
    
    # 方法1: 相对路径定位问题1代码
    q1_code_dir = q2_code_dir.parent.parent / "问题1" / "题代码"
    
    # 方法2: 环境变量覆盖（用于非标准目录结构）
    import os
    if 'Q1_CODE_PATH' in os.environ:
        q1_code_dir = Path(os.environ['Q1_CODE_PATH'])
    
    # 验证路径存在性
    if not q1_code_dir.exists():
        raise FileNotFoundError(
            f"问题1代码目录不存在: {q1_code_dir}\n"
            f"请检查目录结构或设置环境变量 Q1_CODE_PATH"
        )
    
    # 验证关键模块存在
    required_modules = ['btree.py', 'operators.py', 'fast_sa.py']
    missing = [m for m in required_modules if not (q1_code_dir / m).exists()]
    if missing:
        raise FileNotFoundError(
            f"问题1代码目录缺少模块: {missing}\n"
            f"目录: {q1_code_dir}"
        )
    
    # 添加到sys.path（去重）
    q1_path_str = str(q1_code_dir)
    if q1_path_str not in sys.path:
        sys.path.insert(0, q1_path_str)
        print(f"✅ 成功加载问题1代码: {q1_code_dir}")
    
    return q1_code_dir

# 在任何import之前调用
try:
    Q1_CODE_DIR = setup_imports()
except FileNotFoundError as e:
    print(f"❌ Import配置失败:\n{e}")
    sys.exit(1)

# 现在可以安全import
from btree import BTree
from operators import random_perturbation
from fast_sa import FastSA
```

**验证方法**：
```python
# 单元测试
def test_import_from_different_dirs():
    """测试从不同目录运行时import是否成功"""
    import subprocess
    
    # 测试场景1: 从q2代码目录运行
    result1 = subprocess.run(
        ['python', 'q2_main.py', '--test-import'],
        cwd='问题2/题代码',
        capture_output=True
    )
    assert result1.returncode == 0
    
    # 测试场景2: 从根目录运行
    result2 = subprocess.run(
        ['python', '问题2/题代码/q2_main.py', '--test-import'],
        cwd='.',
        capture_output=True
    )
    assert result2.returncode == 0
```

### 2.3 数据流（不变）

```
[输入] .blocks + .nets + .pl
    ↓
[hpwl.py] 解析 → {blocks, nets, term_pos, S}
    ↓
[初始化] random/ffd/warm_start → BTree
    ↓
[ConstrainedSAWrapper] 包装Q2CostFunction
    ↓
[Fast-SA] 
    ├─ 扰动: operators.random_perturbation
    ├─ 解码: btree.decode() → (W, H, A, positions)
    ├─ 评估: wrapper.evaluate() → float
    │    └─ 内部: q2_cost(HPWL + λ·penalty)
    └─ 接受: Metropolis准则
    ↓
[wrapper.best_feasible] 只记可行解(M≤S)
    ↓
[输出] 布局图 + HPWL + 收敛曲线
```

---

## 3. 核心组件设计

### 3.1 成本函数 (q2_cost.py)

#### 3.1.1 [v2.1优化] 公式

$$
\Phi = \frac{W}{W_{norm}} + \lambda \cdot \max\left(0, \frac{M - S}{S}\right)
$$

**符号说明**：
- $W$: 总HPWL = $\sum_{net} (x_{max}-x_{min}) + (y_{max}-y_{min})$
- $W_{norm}$: 归一化因子（SA前试扰动500次的平均HPWL）
- $M$: 轮廓最大边长 = max(W, H)
- $S$: 轮廓边长 = $\sqrt{1.15 \times A_{total}}$
- $\lambda$: 自适应惩罚权重

**[v2.1修正说明]**：
- 原公式：$(A \cdot R - S^2)/S^2$ 其中 $R = M/\min(W,H)$
- 简化后：$(M - S)/S$（更直观，两者等价当优化收敛后）
- 等价性：$A \cdot R = W \cdot H \cdot \frac{M}{\min(W,H)} \approx M^2$（当W≈H时）

#### 3.1.2 [改进] 成本诊断函数

**目的**：每1000次迭代输出成本分布，帮助调优λ参数。

**完整实现**：
```python
class CostDiagnostics:
    """
    成本诊断工具：追踪HPWL、penalty、λ的分布
    
    每1000次迭代输出：
    - HPWL范围和均值
    - penalty激活率（多少比例>0）
    - 当前λ值和可行率
    - 成本项比例（HPWL项 vs penalty项）
    """
    def __init__(self, report_interval=1000):
        self.interval = report_interval
        self.hpwl_window = []
        self.penalty_window = []
        self.lambda_window = []
        self.feasible_window = []
        self.iteration = 0
    
    def record(self, metrics: dict):
        """记录一次迭代的成本指标"""
        self.iteration += 1
        self.hpwl_window.append(metrics['hpwl'])
        self.penalty_window.append(metrics['penalty'])
        self.lambda_window.append(metrics['lambda'])
        self.feasible_window.append(1 if metrics['M'] <= metrics['S'] else 0)
        
        if self.iteration % self.interval == 0:
            self._report()
            self._reset_window()
    
    def _report(self):
        """输出诊断报告"""
        import numpy as np
        
        hpwl_arr = np.array(self.hpwl_window)
        penalty_arr = np.array(self.penalty_window)
        lambda_val = self.lambda_window[-1]
        feasible_rate = np.mean(self.feasible_window)
        
        hpwl_mean = np.mean(hpwl_arr)
        hpwl_std = np.std(hpwl_arr)
        penalty_active_rate = np.mean(penalty_arr > 0)
        
        # 成本项比例
        hpwl_contribution = 1.0  # 归一化后
        penalty_contribution = lambda_val * np.mean(penalty_arr)
        total_cost = hpwl_contribution + penalty_contribution
        hpwl_ratio = hpwl_contribution / total_cost if total_cost > 0 else 0
        penalty_ratio = penalty_contribution / total_cost if total_cost > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"📊 成本诊断 [Iter {self.iteration}]")
        print(f"{'='*60}")
        print(f"HPWL: {hpwl_mean:,.0f} ± {hpwl_std:,.0f}")
        print(f"可行率: {feasible_rate:.1%}  λ={lambda_val:.3f}")
        print(f"Penalty激活: {penalty_active_rate:.1%}")
        print(f"成本组成: HPWL={hpwl_ratio:.1%} Penalty={penalty_ratio:.1%}")
        
        # 健康检查
        if feasible_rate < 0.3:
            print("⚠️  可行率过低 → 增大λ")
        elif feasible_rate > 0.9:
            print("⚠️  可行率过高 → 减小λ")
        if penalty_ratio > 0.7:
            print("⚠️  Penalty占比过大 → 减小λ")
        
        print(f"{'='*60}\n")
    
    def _reset_window(self):
        self.hpwl_window = []
        self.penalty_window = []
        self.lambda_window = []
        self.feasible_window = []


class Q2CostFunction:
    """问题2成本函数：HPWL + 软约束惩罚"""
    
    def __init__(self, data: dict, lambda_manager, enable_diagnostics=True):
        self.data = data
        self.lambda_mgr = lambda_manager
        self.S = data['side']
        self.W_norm = None
        self.diagnostics = CostDiagnostics() if enable_diagnostics else None
    
    def __call__(self, tree) -> tuple:
        """
        计算成本
        
        Returns:
            (cost, is_feasible, metrics_dict)
        """
        # 1. 解码
        W, H, A = tree.get_dimensions()
        positions = tree.get_positions()
        rotations = tree.get_rotations()
        
        # 2. 计算HPWL
        from hpwl import evaluate
        total_hpwl, _ = evaluate(self.data, positions, rotations)
        
        # 3. 首次计算归一化因子
        if self.W_norm is None:
            self.W_norm = self._compute_norm(tree)
            print(f"✅ W_norm = {self.W_norm:,.0f}")
        
        # 4. 可行性
        M = max(W, H)
        is_feasible = (M <= self.S)
        
        # 5. [v2.1优化] 简化惩罚项
        penalty_raw = max(0, (M - self.S) / self.S)
        
        # 6. 总成本
        lambda_val = self.lambda_mgr.get_lambda()
        cost = total_hpwl / self.W_norm + lambda_val * penalty_raw
        
        # 7. Metrics
        metrics = {
            'W': W, 'H': H, 'A': A, 'M': M, 'S': self.S,
            'hpwl': total_hpwl,
            'penalty': penalty_raw,
            'lambda': lambda_val,
            'cost': cost
        }
        
        # 8. 诊断
        if self.diagnostics:
            self.diagnostics.record(metrics)
        
        return cost, is_feasible, metrics
    
    def _compute_norm(self, initial_tree, n_samples=500) -> float:
        """计算归一化因子"""
        from operators import random_perturbation
        from hpwl import evaluate
        import copy
        
        hpwl_samples = []
        tree_copy = copy.deepcopy(initial_tree)
        
        for _ in range(n_samples):
            random_perturbation(tree_copy)
            pos = tree_copy.get_positions()
            rot = tree_copy.get_rotations()
            hpwl, _ = evaluate(self.data, pos, rot)
            hpwl_samples.append(hpwl)
        
        return sum(hpwl_samples) / len(hpwl_samples)
```

---

### 3.2 [改进] 分阶段SA与自适应λ (q2_adaptive_lambda.py)

#### 3.2.1 问题诊断

**原设计问题**：
- 单一λ参数（0.4/0.8阈值）未针对HPWL场景调优
- 可能导致：前期困在不可行区域，或后期过早放松约束

**改进方案**：两阶段SA
- **Phase 1 (高λ)**: 快速找到可行解（λ=2.0~5.0）
- **Phase 2 (低λ)**: 细化优化HPWL（λ=0.1~1.0，自适应调整）

#### 3.2.2 分阶段策略

```python
class TwoPhaseAdaptiveLambda:
    """
    两阶段自适应λ管理器
    
    Phase 1 (前30%迭代): 高λ强约束，快速找可行解
    Phase 2 (后70%迭代): 低λ自适应，优化HPWL
    """
    
    def __init__(self, 
                 total_iterations,
                 phase1_ratio=0.3,
                 # Phase 1参数
                 lambda_phase1=3.0,
                 # Phase 2参数
                 lambda_init_phase2=0.5,
                 window_size=500,
                 threshold_high=0.8,
                 threshold_low=0.4,
                 lambda_min=0.1,
                 lambda_max=2.0):
        """
        Args:
            total_iterations: 总迭代次数
            phase1_ratio: Phase1占比（默认30%）
            lambda_phase1: Phase1的固定λ（高值强约束）
            lambda_init_phase2: Phase2的初始λ
            其他参数: Phase2自适应调整参数
        """
        self.total_iters = total_iterations
        self.phase1_end = int(total_iterations * phase1_ratio)
        
        # Phase 1
        self.lambda_p1 = lambda_phase1
        
        # Phase 2
        self.lambda_p2 = lambda_init_phase2
        self.window = []
        self.window_size = window_size
        self.th_high = threshold_high
        self.th_low = threshold_low
        self.lam_min = lambda_min
        self.lam_max = lambda_max
        
        # 状态
        self.current_iter = 0
        self.current_phase = 1
        self.history = []  # [(iter, phase, lambda, feasible_rate)]
    
    def get_lambda(self) -> float:
        """获取当前λ"""
        if self.current_phase == 1:
            return self.lambda_p1
        else:
            return self.lambda_p2
    
    def record(self, is_feasible: bool):
        """记录一次迭代"""
        self.current_iter += 1
        
        # 检查是否切换阶段
        if self.current_iter == self.phase1_end and self.current_phase == 1:
            self._switch_to_phase2()
        
        # Phase 2才记录窗口
        if self.current_phase == 2:
            self.window.append(1 if is_feasible else 0)
            if len(self.window) > self.window_size:
                self.window.pop(0)
    
    def update(self):
        """
        更新λ（每个温度级调用）
        
        Returns:
            (lambda, feasible_rate, action, phase)
        """
        if self.current_phase == 1:
            # Phase 1不调整
            return self.lambda_p1, None, 'hold', 1
        
        # Phase 2自适应调整
        if len(self.window) < self.window_size:
            return self.lambda_p2, None, 'hold', 2
        
        feasible_rate = sum(self.window) / len(self.window)
        action = 'hold'
        
        if feasible_rate > self.th_high:
            # 可行率高 → 减小λ → 更关注HPWL
            self.lambda_p2 = max(self.lam_min, self.lambda_p2 / 1.5)
            action = 'decrease'
        elif feasible_rate < self.th_low:
            # 可行率低 → 增大λ → 拉回轮廓
            self.lambda_p2 = min(self.lam_max, self.lambda_p2 * 1.5)
            action = 'increase'
        
        self.history.append((self.current_iter, self.current_phase, 
                            self.get_lambda(), feasible_rate))
        
        return self.lambda_p2, feasible_rate, action, 2
    
    def _switch_to_phase2(self):
        """[v2.1增强] 切换到Phase 2"""
        self.current_phase = 2
        # 计算Phase 1的可行率
        p1_feasible = [h[3] for h in self.history if h[1] == 1 and h[3] is not None]
        p1_rate = sum(p1_feasible) / len(p1_feasible) if p1_feasible else 0
        
        # [v2.1新增] Phase1失败检查
        if p1_rate < 0.01:
            raise RuntimeError(
                f"Phase1失败：可行率仅{p1_rate:.1%}，无法找到可行解。\n"
                f"建议：1) 提高lambda_phase1至10.0  2) 延长phase1_ratio至0.5"
            )
        
        print(f"\n{'='*60}")
        print(f"🔄 切换到Phase 2")
        print(f"{'='*60}")
        print(f"Phase 1总结:")
        print(f"  迭代数: {self.phase1_end}")
        print(f"  λ (固定): {self.lambda_p1:.2f}")
        print(f"  可行率: {p1_rate:.1%}")
        print(f"\nPhase 2配置:")
        print(f"  初始λ: {self.lambda_p2:.2f}")
        print(f"  调整范围: [{self.lam_min}, {self.lam_max}]")
        print(f"  目标可行率: [{self.th_low:.0%}, {self.th_high:.0%}]")
        print(f"{'='*60}\n")
    
    def get_history(self):
        """返回λ调整历史"""
        return self.history
```

**切换判据说明**：
- **迭代数判据**（已采用）：Phase1固定占30%总迭代
  - 优点：简单可控，时间可预测
  - 适用场景：大多数问题
  
- **可行率判据**（备选）：Phase1可行率>80%时切换
  - 优点：自适应，困难问题Phase1更长
  - 缺点：可能过早切换（局部可行）



---

### 3.5 [v2.1新增] FastSA集成策略

#### 3.5.1 问题诊断

**接口不兼容问题**：
- **FastSA期望**：`cost_func(tree: BTree) -> float`
- **Q2CostFunction返回**：`(cost: float, is_feasible: bool, metrics: dict)`

**核心挑战**：
1. FastSA只认识单值成本，不知道可行性约束
2. FastSA内部维护best_so_far，但可能记录不可行解
3. λ需要在SA循环中动态调整，但FastSA不支持回调

#### 3.5.2 解决方案：包装层模式

**方案A：ConstrainedSAWrapper（推荐）**

```python
import copy
from typing import Optional, Tuple

class ConstrainedSAWrapper:
    """
    FastSA的约束优化包装器
    
    功能：
    1. 接口转换：三元组 → 单值
    2. 可行性过滤：只记录可行解为best
    3. λ管理：自动调用lambda_mgr.record()
    4. 统计追踪：记录探索过程中的可行率
    
    Usage:
        wrapper = ConstrainedSAWrapper(q2_cost_func, lambda_mgr)
        sa = FastSA(blocks, wrapper.evaluate)
        sa.run()
        best_tree, best_hpwl = wrapper.get_best()
    """
    
    def __init__(self, q2_cost_func, lambda_manager):
        """
        Args:
            q2_cost_func: Q2CostFunction实例
            lambda_manager: TwoPhaseAdaptiveLambda实例
        """
        self.cost_func = q2_cost_func
        self.lambda_mgr = lambda_manager
        
        # Best tracking (仅可行解)
        self.best_feasible_tree = None
        self.best_hpwl = float('inf')
        self.best_M = float('inf')
        
        # Statistics
        self.total_evals = 0
        self.feasible_count = 0
        self.infeasible_count = 0
        
        # 最近的metrics（用于调试）
        self.last_metrics = None
    
    def evaluate(self, tree) -> float:
        """
        FastSA调用的接口
        
        Args:
            tree: BTree实例
        
        Returns:
            float: 归一化成本（HPWL + λ·penalty）
        """
        # 1. 调用Q2成本函数（返回三元组）
        cost, is_feasible, metrics = self.cost_func(tree)
        
        # 2. 记录可行性（供λ管理器调整）
        self.lambda_mgr.record(is_feasible)
        
        # 3. 统计
        self.total_evals += 1
        if is_feasible:
            self.feasible_count += 1
        else:
            self.infeasible_count += 1
        
        # 4. 更新最优可行解
        if is_feasible and metrics['hpwl'] < self.best_hpwl:
            self.best_hpwl = metrics['hpwl']
            self.best_M = metrics['M']
            self.best_feasible_tree = copy.deepcopy(tree)
            
            # 可选：打印改进信息
            if self.total_evals % 1000 == 0:
                print(f"[Eval {self.total_evals}] 新最优: HPWL={self.best_hpwl:,.0f} "
                      f"M={self.best_M:.1f} 可行率={self.get_feasible_rate():.1%}")
        
        # 5. 保存最近的metrics（用于外部查询）
        self.last_metrics = metrics
        
        # 6. 返回单值成本（FastSA期望的接口）
        return cost
    
    def get_best(self) -> Tuple[Optional[object], float]:
        """
        返回最优可行解
        
        Returns:
            (best_tree, best_hpwl) 或 (None, inf) 如果无可行解
        """
        return self.best_feasible_tree, self.best_hpwl
    
    def get_feasible_rate(self) -> float:
        """返回当前可行率"""
        if self.total_evals == 0:
            return 0.0
        return self.feasible_count / self.total_evals
    
    def get_stats(self) -> dict:
        """返回统计信息"""
        return {
            'total_evals': self.total_evals,
            'feasible_count': self.feasible_count,
            'infeasible_count': self.infeasible_count,
            'feasible_rate': self.get_feasible_rate(),
            'best_hpwl': self.best_hpwl,
            'best_M': self.best_M
        }
```

#### 3.5.3 λ更新机制

**挑战**：FastSA不支持每个温度级的回调（无法调用lambda_mgr.update()）

**解决方案**：两种策略

**策略1：外部轮询（推荐，无需修改FastSA）**

```python
# 在FastSA.run()之前启动后台线程
import threading
import time

def lambda_update_daemon(lambda_mgr, interval=1.0, stop_event=None):
    """
    后台定期更新λ
    
    Args:
        lambda_mgr: TwoPhaseAdaptiveLambda实例
        interval: 更新间隔（秒）
        stop_event: threading.Event用于停止
    """
    while not (stop_event and stop_event.is_set()):
        time.sleep(interval)
        lam, feas_rate, action, phase = lambda_mgr.update()
        
        if action != 'hold':
            print(f"[λ更新] Phase{phase} λ={lam:.3f} "
                  f"可行率={feas_rate:.1%} 动作={action}")

# 使用方法
stop_event = threading.Event()
daemon_thread = threading.Thread(
    target=lambda_update_daemon,
    args=(lambda_mgr, 1.0, stop_event),
    daemon=True
)
daemon_thread.start()

# 运行SA
sa.run()

# 停止后台线程
stop_event.set()
daemon_thread.join()
```

**策略2：Monkey Patch FastSA（侵入性更强）**

```python
# 给FastSA注入回调钩子
original_run_level = sa._run_temperature_level

def patched_run_level(*args, **kwargs):
    result = original_run_level(*args, **kwargs)
    lambda_mgr.update()  # 每个温度级后调用
    return result

sa._run_temperature_level = patched_run_level
sa.run()
```

**推荐**：使用策略1（后台轮询），避免修改FastSA代码。

#### 3.5.4 完整集成示例

```python
def solve_with_fastsa(blocks, data, lambda_mgr, init_tree, verbose=True):
    """
    使用FastSA + 包装层求解问题2
    
    Args:
        blocks: Block列表
        data: hpwl数据字典
        lambda_mgr: TwoPhaseAdaptiveLambda实例
        init_tree: 初始BTree
        verbose: 是否打印过程
    
    Returns:
        result_dict
    """
    import threading
    import time
    
    # 1. 构造成本函数
    cost_func = Q2CostFunction(data, lambda_mgr, enable_diagnostics=verbose)
    
    # 2. 包装层
    wrapper = ConstrainedSAWrapper(cost_func, lambda_mgr)
    
    # 3. 创建FastSA实例
    from fast_sa import FastSA
    sa = FastSA(blocks, wrapper.evaluate, P=0.9, k=7, c=100)
    
    # 4. 启动λ更新守护线程
    stop_event = threading.Event()
    if verbose:
        daemon = threading.Thread(
            target=lambda_update_daemon,
            args=(lambda_mgr, 2.0, stop_event),  # 每2秒更新一次
            daemon=True
        )
        daemon.start()
    
    # 5. 运行SA
    start_time = time.time()
    sa.run(init_tree)  # FastSA会返回它认为的best，但我们不用
    elapsed = time.time() - start_time
    
    # 6. 停止守护线程
    if verbose:
        stop_event.set()
        daemon.join(timeout=1.0)
    
    # 7. 从包装层获取真正的best（可行解）
    best_tree, best_hpwl = wrapper.get_best()
    stats = wrapper.get_stats()
    
    # 8. 返回结果
    result = {
        'best_tree': best_tree,
        'best_hpwl': best_hpwl,
        'best_M': stats['best_M'],
        'is_feasible': best_tree is not None,
        'time': elapsed,
        'total_evals': stats['total_evals'],
        'feasible_rate': stats['feasible_rate'],
        'lambda_history': lambda_mgr.get_history()
    }
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"求解完成")
        print(f"{'='*60}")
        print(f"最优HPWL: {best_hpwl:,.0f}")
        print(f"最优M: {stats['best_M']:.1f} (轮廓S={data['side']:.1f})")
        print(f"可行性: {'✅' if result['is_feasible'] else '❌'}")
        print(f"总评估: {stats['total_evals']:,}次")
        print(f"可行率: {stats['feasible_rate']:.1%}")
        print(f"耗时: {elapsed:.2f}s")
        print(f"{'='*60}\n")
    
    return result
```

#### 3.5.5 与问题1 FastSA的差异

| 维度 | 问题1 | 问题2 |
|------|-------|-------|
| 优化目标 | 词典序(M优先, A次要) | 单目标(HPWL + λ·penalty) |
| 成本函数返回 | float | (float, bool, dict) → 包装为float |
| Best更新 | FastSA内部 | 包装层过滤可行解 |
| λ调整 | 无（固定惩罚） | 动态调整（两阶段） |
| 温度调度 | FastSA标准 | **复用**FastSA标准 |
| 扰动算子 | operators.random_perturbation | **复用** |

**关键设计决策**：
- ✅ **复用**：FastSA的温度调度（T1计算、三阶段冷却）
- ✅ **复用**：operators.random_perturbation（无需改动）
- ✅ **新增**：ConstrainedSAWrapper（接口适配层）
- ✅ **新增**：后台λ更新守护线程（非侵入式）

---

### 3.6 [改进] Warm Start策略明确化 (q2_warmstart.py)

#### 3.6.1 问题分析

**挑战**：问题1最优解是窄长型（W≫H或H≫W），问题2需要正方形（W≈H）。

**三种策略对比**：

| 策略 | 原理 | 优点 | 缺点 | 推荐度 |
|------|------|------|------|--------|
| **拓扑继承** | 直接使用问题1的B*-Tree结构 | 实现简单 | 可能不适应正方形约束 | ⭐⭐⭐ |
| **比例缩放** | 调整树结构使W≈H | 适应正方形 | 算法复杂，可能破坏拓扑 | ⭐⭐ |
| **Hybrid** | 拓扑继承+Phase1高λ强制调整 | 兼顾简单性和适应性 | 需要Phase1足够长 | ⭐⭐⭐⭐⭐ |

**推荐**：Hybrid策略（最小实现成本，依赖分阶段SA）



#### 3.6.2 完整实现

```python
# q2_warmstart.py
from pathlib import Path
from btree import BTree
from typing import List
import pickle

def initialize_tree(blocks, mode='random', warm_file=None, data=None):
    """
    初始化B*-Tree
    
    Args:
        blocks: 模块列表
        mode: 'random' | 'ffd' | 'warm'
        warm_file: 问题1解文件路径
        data: hpwl数据（用于验证）
    
    Returns:
        BTree实例
    """
    if mode == 'warm':
        if warm_file is None:
            print("⚠️  warm_file未提供，回退到random")
            mode = 'random'
        else:
            try:
                tree = load_warm_start(warm_file, strategy='hybrid')
                
                # 验证可行性
                if data:
                    W, H, _ = tree.get_dimensions()
                    M = max(W, H)
                    S = data['side']
                    R = M / min(W, H)
                    
                    print(f"✅ Warm start加载成功:")
                    print(f"   尺寸: {W:.1f}×{H:.1f}  M={M:.1f}")
                    print(f"   长宽比: {R:.2f}")
                    print(f"   轮廓: S={S:.1f}")
                    
                    if M <= S:
                        print(f"   状态: 可行 (M<S)")
                        return tree
                    else:
                        print(f"   状态: 超轮廓 (M>S)，将由Phase1调整")
                        return tree  # Hybrid策略：Phase1会调整
                        
            except Exception as e:
                print(f"⚠️  Warm start加载失败: {e}")
                print("   回退到random")
                mode = 'random'
    
    if mode == 'ffd':
        from constructive import ffd_initial_solution
        return ffd_initial_solution(blocks)
    
    # mode == 'random'
    return random_initial_tree(blocks)

def random_initial_tree(blocks):
    """随机初始化"""
    import random
    shuffled = blocks.copy()
    random.shuffle(shuffled)
    return BTree.from_sequence(shuffled)

def load_warm_start(filepath: str, strategy='hybrid'):
    """
    加载问题1的最优解
    
    Args:
        filepath: pickle文件路径
        strategy: 'topology' | 'scaling' | 'hybrid'
    
    Returns:
        BTree实例
    """
    with open(filepath, 'rb') as f:
        tree = pickle.load(f)
    
    if strategy == 'topology':
        # 策略1: 直接使用拓扑
        return tree
    
    elif strategy == 'scaling':
        # 策略2: 比例缩放（复杂，暂不实现）
        print("⚠️  scaling策略未实现，回退到topology")
        return tree
    
    elif strategy == 'hybrid':
        # 策略3: 拓扑继承 + 依赖Phase1调整
        # 不做额外处理，Phase1的高λ会强制调整成正方形
        return tree
    
    else:
        raise ValueError(f"未知策略: {strategy}")
```

---

## 4. [v2.1修正] 主程序完整实现 (q2_main.py)

**关键改进点**：
1. 修正import逻辑（已在2.2节实现）
2. [v2.1新增] 使用ConstrainedSAWrapper集成FastSA
3. 集成分阶段SA和成本诊断
4. 改进输出和日志

```python
#!/usr/bin/env python3
"""问题2主程序：固定轮廓线长优化"""

# 1. Import配置（使用2.2节的setup_imports）
from pathlib import Path
import sys

# [使用2.2节的setup_imports函数]
try:
    Q1_CODE_DIR = setup_imports()
except FileNotFoundError as e:
    print(f"❌ Import失败:\n{e}")
    sys.exit(1)

# 2. 导入模块
from btree import BTree
from operators import random_perturbation
from fast_sa import FastSA
from data_loader import Block

from q2_cost import Q2CostFunction
from q2_adaptive_lambda import TwoPhaseAdaptiveLambda
from q2_warmstart import initialize_tree

# [v2.1新增] 导入包装层
import sys
sys.path.insert(0, str(Path(__file__).parent))
from q2_fastsa_wrapper import ConstrainedSAWrapper, lambda_update_daemon

sys.path.insert(0, str(Path(__file__).parent.parent))
from hpwl import load, evaluate


def solve_q2(dataset='n100', 
             init_mode='random',
             warm_file=None,
             strategy=None,
             seed=42,
             max_iter=10000,
             verbose=True):
    """
    求解问题2
    
    Args:
        dataset: 'n100' | 'n200' | 'n300'
        init_mode: 'random' | 'ffd' | 'warm'
        warm_file: 问题1解文件
        strategy: λ策略配置（None使用默认两阶段）
        seed: 随机种子
        max_iter: 最大迭代次数
        verbose: 是否打印过程
    
    Returns:
        result_dict
    """
    import random
    import time
    import threading
    random.seed(seed)
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"问题2求解: {dataset}")
        print(f"初始化: {init_mode}  种子: {seed}")
        print(f"{'='*60}\n")
    
    # 1. 加载数据
    data = load(dataset)
    blocks = [Block(name, w, h) for name, (w, h) in data['blocks'].items()]
    S = data['side']
    
    if verbose:
        print(f"模块数: {len(blocks)}")
        print(f"轮廓: {S:.2f}×{S:.2f}")
        print(f"总面积: {sum(b.w*b.h for b in blocks):,.0f}\n")
    
    # 2. 初始化树
    init_tree = initialize_tree(blocks, mode=init_mode, 
                               warm_file=warm_file, data=data)
    
    # 3. 配置λ管理器
    if strategy is None:
        # 默认：两阶段
        lambda_mgr = TwoPhaseAdaptiveLambda(
            total_iterations=max_iter,
            phase1_ratio=0.3,
            lambda_phase1=3.0,
            lambda_init_phase2=0.5
        )
    elif strategy.get('mode') == 'fixed':
        # 固定λ（用于对照实验）
        class FixedLambda:
            def __init__(self, val):
                self.val = val
            def get_lambda(self):
                return self.val
            def record(self, _):
                pass
            def update(self):
                return self.val, None, 'hold', 1
            def get_history(self):
                return []
        
        lambda_mgr = FixedLambda(strategy['lambda'])
    else:
        # 自定义两阶段
        lambda_mgr = TwoPhaseAdaptiveLambda(
            total_iterations=max_iter,
            lambda_phase1=strategy.get('p1_lambda', 3.0),
            lambda_init_phase2=strategy.get('p2_init', 0.5),
            threshold_high=strategy.get('th', (0.4, 0.8))[1],
            threshold_low=strategy.get('th', (0.4, 0.8))[0]
        )
    
    # 4. 构造成本函数
    cost_func = Q2CostFunction(data, lambda_mgr, enable_diagnostics=verbose)
    
    # 5. [v2.1修正] 使用包装层 + FastSA
    wrapper = ConstrainedSAWrapper(cost_func, lambda_mgr)
    sa = FastSA(blocks, wrapper.evaluate, P=0.9, k=7, c=100)
    
    # 6. [v2.1新增] 启动λ更新守护线程
    stop_event = threading.Event()
    if verbose:
        daemon = threading.Thread(
            target=lambda_update_daemon,
            args=(lambda_mgr, 2.0, stop_event),
            daemon=True
        )
        daemon.start()
    
    # 7. 运行SA
    start_time = time.time()
    sa.run(init_tree)
    elapsed = time.time() - start_time
    
    # 8. 停止守护线程
    if verbose:
        stop_event.set()
        daemon.join(timeout=1.0)
    
    # 9. 从包装层获取真正的best
    best_tree, best_hpwl = wrapper.get_best()
    stats = wrapper.get_stats()
    
    # 10. 返回结果
    result = {
        'best_tree': best_tree,
        'best_hpwl': best_hpwl,
        'best_M': stats['best_M'],
        'is_feasible': best_tree is not None,
        'iterations': max_iter,
        'convergence_iter': max_iter,  # 简化，实际需从wrapper获取
        'time': elapsed,
        'lambda_history': lambda_mgr.get_history(),
        'total_evals': stats['total_evals'],
        'feasible_rate': stats['feasible_rate']
    }
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"求解完成")
        print(f"{'='*60}")
        print(f"最优HPWL: {best_hpwl:,.0f}")
        print(f"最优M: {stats['best_M']:.1f} (轮廓S={S:.1f})")
        print(f"可行性: {'✅' if result['is_feasible'] else '❌'}")
        print(f"总评估: {stats['total_evals']:,}次")
        print(f"可行率: {stats['feasible_rate']:.1%}")
        print(f"耗时: {elapsed:.2f}s")
        print(f"{'='*60}\n")
    
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='问题2求解')
    parser.add_argument('--dataset', default='n100', choices=['n100','n200','n300'])
    parser.add_argument('--init', default='random', choices=['random','ffd','warm'])
    parser.add_argument('--warm-file', type=str, help='问题1解文件路径')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--max-iter', type=int, default=10000)
    parser.add_argument('--test-import', action='store_true', help='测试import配置')
    
    args = parser.parse_args()
    
    if args.test_import:
        print("✅ Import测试通过")
        sys.exit(0)
    
    result = solve_q2(
        dataset=args.dataset,
        init_mode=args.init,
        warm_file=args.warm_file,
        seed=args.seed,
        max_iter=args.max_iter
    )
```

**[v2.1新增] 需要创建的新文件：q2_fastsa_wrapper.py**

```python
"""FastSA包装层模块"""
import copy
import time
import threading
from typing import Optional, Tuple

class ConstrainedSAWrapper:
    """[完整实现见3.5.2节]"""
    # 代码已在3.5.2节给出，此处省略
    pass

def lambda_update_daemon(lambda_mgr, interval=1.0, stop_event=None):
    """[完整实现见3.5.3节]"""
    # 代码已在3.5.3节给出，此处省略
    pass
```

---

## 5. 关键约束与红线

### 5.1 技术红线（违反则全盘错误）

| # | 红线 | 错误后果 | 检查方法 |
|---|------|---------|---------|
| 1 | **best只记可行解** (M≤S) | 报告超轮廓解 | wrapper验证best_tree |
| 2 | **M判据**: max(W,H) 非面积 | 放行瘦长超轮廓解 | 打印M和S对比 |
| 3 | **软惩罚非硬拒绝** | SA困死无法试探 | λ=inf的解可行率=0% |
| 4 | **W_norm归一化** | 温度公式失效 | 检查delta量级~1 |
| 5 | **分阶段切换** | Phase1过短无法找到可行解 | 验证Phase1可行率>1% |
| 6 | **[v2.1新增] 包装层接口** | FastSA收到非float值 | 单元测试wrapper.evaluate |

---

## 6. [v2.1调整] 时间估算

### 6.1 开发时间

| 模块 | 估算时间 | 依赖 | 风险buffer |
|------|---------|------|-----------|
| q2_cost.py（含诊断） | 40分钟 | hpwl.py | +10分钟 |
| q2_adaptive_lambda.py | 40分钟 | 无 | +10分钟 |
| **[v2.1新增] q2_fastsa_wrapper.py** | **30分钟** | FastSA接口 | **+10分钟** |
| q2_warmstart.py | 20分钟 | 问题1代码 | +5分钟 |
| q2_main.py | 40分钟 | 上述模块 | +10分钟 |
| 单元测试 | 30分钟 | 全部模块 | +10分钟 |
| **第一阶段小计** | **3小时** | | **+55分钟** |

### 6.2 实验与调优时间

| 阶段 | 任务 | 估算时间 | 备注 |
|------|------|---------|------|
| 基础验证 | n100 random 单次运行 | 5分钟 | 检查可行性 |
| 参数调优 | λ敏感性测试（仅n100，5组×5种子） | 30分钟 | 并行运行 |
| 全量实验 | 3数据集×3初始化×5种子 | 2小时 | 可并行 |
| **第二阶段小计** | | **2.5小时** | |

### 6.3 总时间

- **第一阶段**（开发+单元测试）：**3.5小时**（含buffer，v2的3小时+30分钟包装层）
- **第二阶段**（实验+调优）：**2.5小时**
- **总计**：**6小时**

**关键路径**：
1. 开发核心模块（并行不可）：3.5小时
2. λ敏感性测试（可与全量实验并行）：30分钟
3. 全量实验（可并行）：2小时

**最短完成时间**（理想情况）：**4小时**

---

## 7. 实施优先级（不变）

### 7.1 三阶段实施计划

**第一阶段（核心功能，3小时）**：
1. ✅ q2_cost.py（含诊断）
2. ✅ q2_adaptive_lambda.py（两阶段）
3. ✅ [v2.1新增] q2_fastsa_wrapper.py（包装层）
4. ✅ q2_main.py（import修正+集成）
5. ✅ 单元测试（import+包装层+基础功能）

**第二阶段（验证与调优，1小时）**：
6. ✅ n100 random基础实验（检查可行性）
7. ✅ λ敏感性快速测试（仅n100，找最优参数）
8. ✅ 对照实验（固定λ vs 两阶段）

**第三阶段（扩展功能，2小时，可选）**：
9. ⭐ q2_warmstart.py（warm start）
10. ⭐ FFD初始化
11. ⭐ 全量实验（3数据集×5种子）

---

## 8. 总结

**本文档v2.1相比v2的关键修正**：

1. **[新增3.5节]**：FastSA集成策略
   - ✅ ConstrainedSAWrapper完整实现（70行）
   - ✅ 接口转换：三元组→单值
   - ✅ best过滤：只记可行解
   - ✅ λ更新：后台守护线程

2. **[修正4节]**：q2_main.py完整实现
   - ✅ 替换"简化版SA循环"为wrapper+FastSA调用
   - ✅ 集成守护线程管理
   - ✅ 新增q2_fastsa_wrapper.py模块

3. **[调整6节]**：时间估算
   - ✅ 3小时→3.5小时（+30分钟包装层开发）
   - ✅ 总计6小时（最短4小时）

4. **[优化3.1节]**：简化成本函数惩罚项
   - ✅ $(A·R-S²)/S²$ → $(M-S)/S$（更直观）

5. **[增强3.2节]**：Phase1失败检查
   - ✅ 可行率<1%时抛出RuntimeError并提示调优

**下一步**：
- 审核通过 → 进入plan-execute阶段
- 拆解为bite-sized任务（每个<30分钟）
- TDD开发：写测试→实现→验证→提交

---

**文档状态**: ✅ v2.1修正完成，已补充FastSA集成方案，可进入实施阶段
