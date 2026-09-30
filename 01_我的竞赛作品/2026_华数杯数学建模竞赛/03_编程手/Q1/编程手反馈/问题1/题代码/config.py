"""
配置文件 - 所有参数集中管理
"""
import os

# ==================== 数据文件路径 ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "2026年第七届华数杯数学建模竞赛赛题", "B题 VLSI布图规划设计", "附件")

DATA_PATHS = {
    'n100': os.path.join(DATA_DIR, 'n100.blocks'),
    'n200': os.path.join(DATA_DIR, 'n200.blocks'),
    'n300': os.path.join(DATA_DIR, 'n300.blocks'),
}

# ==================== 已知总面积（用于校验） ====================
EXPECTED_AREAS = {
    'n100': 179501,
    'n200': 175696,
    'n300': 273170,
}

# ==================== 理论下界（方形边长√A） ====================
LOWER_BOUNDS = {
    'n100': 424,  # √179501 ≈ 423.67
    'n200': 420,  # √175696 ≈ 419.16
    'n300': 523,  # √273170 ≈ 522.65
}

# ==================== 构造上界（FFD可行边长） ====================
UPPER_BOUNDS = {
    'n100': 443,
    'n200': 440,
    'n300': 538,
}

# ==================== Fast-SA参数（Ultra-fast优化版）====================
# 优化日期：2026-08-08
# 性能提升：10.67x 加速（12.08s → 1.13s），质量无损失
# 详见：性能优化完成报告.md
SA_PARAMS = {
    'P': 0.9,              # 初始接受率
    'k': 5,                # 快冷阶段数（7 → 5）
    'c': 100,              # 快冷系数
    'T_final': 0.1,        # 终止温度（0.001 → 0.1，提前终止）
    'max_no_improve': 8,   # 早停（50 → 8，FFD初始化质量高）
    'L_factor': 10,        # 每温度级迭代次数 = L_factor × n（100 → 10）
    'ema_alpha': 0.3,      # C3: Δcost的EMA平滑系数
}

# ==================== 扰动算子概率 (C2: Op1旋转/Op2删插/Op3交换) ====================
PERTURBATION_PROBS = {
    'rotate': 0.1,         # Op1-旋转
    'move': 0.5,           # Op2-删除插入（最高概率，最大探索）
    'swap': 0.4,           # Op3-交换
}

# ==================== 两阶段参数 (M2) ====================
TWOPHASE_PARAMS = {
    'eps': 0.01,           # 面积容忍度 1%
    'mu': 1e6,             # 软惩罚系数（远大于主项）
}

# ==================== 代价函数参数 ====================
COST_PARAMS = {
    'lam': 0.05,           # 加权和系数（无量纲，归一化后）
}

# ==================== 实验矩阵（调整后） ====================
# 主实验：2组合 × 3数据集 × 10种子 × min-max两阶段 = 60次
# 对照：  两阶段 / 加权 / 贪心 baseline × n100 × 10种子 = 30次
# 配对消融：有/无配对 × n100 × 10种子 = 20次
# 合计 ≈ 110次
EXPERIMENT_MATRIX = {
    'datasets': ['n100', 'n200', 'n300'],
    'initial_methods': ['greedy_random', 'ffd'],  # 主实验初始化方法（greedy_random替代random）
    'pairing': [False, True],                   # 配对开关（n100重点）
    'seeds': list(range(10)),                   # 10个随机种子
    'cost_methods': ['twophase', 'weighted', 'greedy'],  # 3种目标方法
    'pairing_focus_dataset': 'n100',            # 配对实验聚焦数据集
    'compare_dataset': 'n100',                  # 对照实验数据集
}

# ==================== 长条识别阈值 ====================
STRIP_THRESHOLD = 2.5  # 纵横比≥2.5认为是长条

# ==================== 可视化参数 ====================
VIS_PARAMS = {
    'dpi': 150,
    'figsize': (12, 8),
    'colors': 'tab20',
}

# ==================== 输出目录 ====================
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '输出')
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '实验日志')

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
