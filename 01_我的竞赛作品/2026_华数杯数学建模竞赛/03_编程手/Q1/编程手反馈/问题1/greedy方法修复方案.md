# Greedy Baseline 修复方案

> 生成时间: 2026-08-08  
> 决策依据: SA论文标准实践 + 当前实验数据分析

---

## 📊 核心结论

**greedy = FFD构造解（不跑SA），time应记录构造时间**

### 推荐方案：记录真实构造时间

**理由**：
1. 学术完整性：对比"构造 vs 构造+优化"需要真实时间
2. 当前time=0会误导读者
3. FFD构造不是瞬时完成（n100约0.5-1秒）

---

## 🔧 代码修复

### 关键问题：时间计算的一致性

**当前问题**：
- greedy: time=0（构造时间未记录）
- twophase: time=8s（SA时间，但**不包含构造时间**）

**修复策略**：
```python
# 在construct_initial_tree前后计时
construct_start = time.time()
tree = construct_initial_tree(blocks, method=initial_method, seed=seed)
construct_time = time.time() - construct_start

# greedy分支
else:  # greedy
    W, H, _ = tree.pack()
    result = {
        ...
        'time': construct_time,  # 修改这里
        'iterations': 0,
    }
```

### ⚠️ 重要：所有方法time定义要一致

**选项1**（推荐）：所有方法都包含构造时间
```python
total_time = construct_time + sa_time
```

**选项2**：区分构造和优化时间（需要修改CSV结构）

**推荐选项1**，因为论文关心"总成本"。

---

## 📋 实施步骤

### 步骤1：修改代码（15分钟）
1. 在`experiment_runner.py`第53行前添加计时
2. 修改greedy分支的time字段
3. **决策点**：twophase/weighted是否也加construct_time？

### 步骤2：重跑实验（1小时）
- **最小方案**：只重跑greedy（30次，n100很快）
- **完整方案**：重跑所有90次（保证一致性）

---

## 🤔 需要立即决策的模糊点

### 模糊点3：twophase的time是否也要修正？

**当前情况**：
- twophase的time只包含SA时间（start_time在构造后）
- 如果greedy包含构造时间，twophase也应该包含

**选择**：
- A. 只修greedy（成本低，但不一致）
- B. 全部修正（一致但需重跑90次）
- C. 接受不一致，在论文注明定义差异

**您的决定？**
