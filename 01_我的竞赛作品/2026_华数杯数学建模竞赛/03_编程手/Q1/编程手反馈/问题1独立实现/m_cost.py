"""
m_cost.py — 独立实现 阶段D：代价函数（修正归一化）

修正核心（设计方案 2.2）：分项归一化，惩罚项除 A_opt（超额比例），
mu 与主项匹配。修复编程手 R1/R2：mu=1e6 未归一化惩罚 → 温度爆炸。

phase1: Φ = A_chip / A_total                              （主项 O(1)）
phase2: Φ = M / Φ_norm + μ · max(0, A − A_opt(1+ε)) / A_opt  μ=10
weighted: Φ = A_chip / A_total + λ · (R−1)²                λ=0.05
"""
from typing import Tuple


def aspect_ratio(W: float, H: float) -> float:
    return max(W, H) / max(min(W, H), 1e-9)


def deadspace(W: float, H: float, A_total: float) -> float:
    A = W * H
    return (A - A_total) / max(A, 1e-9) * 100


def phase1_cost(A_chip: float, A_total: float) -> float:
    return A_chip / max(A_total, 1e-9)


def phase2_cost(W: float, H: float, A_opt: float, A_total: float,
                Phi_norm: float, eps: float = 0.01, mu: float = 10.0) -> float:
    """Φ = M/Φ_norm + μ·max(0, A−A_opt(1+ε))/A_opt. 两项均 O(1)/O(0.01)."""
    A = W * H
    M = max(W, H)
    primary = M / max(Phi_norm, 1e-9)
    pen = mu * max(0.0, A - A_opt * (1.0 + eps)) / max(A_opt, 1e-9)
    return primary + pen


def weighted_cost(W: float, H: float, A_chip: float, A_total: float, lam: float = 0.05) -> float:
    R = aspect_ratio(W, H)
    return A_chip / max(A_total, 1e-9) + lam * (R - 1.0) ** 2


if __name__ == '__main__':
    print("=== 阶段D: 代价函数（归一化修正）===")
    A_total = 179501.0
    A_opt = 179800.0
    Phi_norm = 450.0

    # 合法解：444×444, 超面积解：500×400, 越界深: 600×600
    tests = [
        ('合法 444×444', 444, 444),
        ('瘦长 600×300', 600, 300),
        ('超面积 500×400', 500, 400),
        ('越界深 600×600', 600, 600),
    ]
    print(f"{'布局':14s} {'A_chip':>9s} {'超额%':>7s} {'主项':>7s} {'惩罚':>8s} {'Φ':>10s}")
    for name, W, H in tests:
        A = W * H
        c = phase2_cost(W, H, A_opt, A_total, Phi_norm, eps=0.01, mu=10.0)
        excess = (A - A_opt * 1.01) / A_opt * 100
        primary = max(W, H) / Phi_norm
        pen = 10.0 * max(0.0, A - A_opt * 1.01) / A_opt
        print(f"{name:14s} {A:9.0f} {max(0,excess):7.2f} {primary:7.4f} {pen:8.4f} {c:10.4f}")

    # 归一化检查：正常场景 Φ 应 O(1-2)，越界深才 O(10)；编程手 mu=1e6 同场景 O(1e6)
    print("\n[归一化量级检查]（修复 R1/R2 证据）")
    c_legit = phase2_cost(444, 444, A_opt, A_total, Phi_norm)
    c_over = phase2_cost(500, 400, A_opt, A_total, Phi_norm)
    c_deep = phase2_cost(600, 600, A_opt, A_total, Phi_norm)
    print(f"  合法~1.85 / 超面积~2.13 / 越界99%~11.26  (编程手 mu=1e6: ~1e6 爆炸)")
    assert c_legit < 5 and c_over < 5, "正常场景 Φ 应 O(1)"
    assert c_deep < 20, "越界深应 <20（软惩罚有限）"
    print("  PASS: 正常解 O(1)，无爆炸")

    # 主目标行为：面积合规前提下 min-max 偏好更小 M
    print("\n[主目标行为] 合规解中 M 小者 Φ 小")
    c_a = phase2_cost(424, 424, A_opt, A_total, Phi_norm)   # M=424 合规
    c_b = phase2_cost(600, 300, A_opt, A_total, Phi_norm)   # M=600 合规
    print(f"  424×424(M=424): Φ={c_a:.4f}  600×300(M=600): Φ={c_b:.4f}")
    assert c_a < c_b, "min-max 应偏好更小 M"
    print("  PASS: min-max 语义正确")

    # 单调性：越界深 > 超面积（软惩罚有限但递增）
    print(f"\n[单调性] 超面积={c_over:.4f} < 越界深={c_deep:.4f}")
    assert c_over < c_deep
    print("  软惩罚递增: PASS")

    # phase1 对照
    print(f"\n[phase1] A_chip=197136 → {phase1_cost(197136, A_total):.4f} (≈1.098)")
    print("阶段D: ALL PASS")
