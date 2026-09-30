"""Q2 Visualization: 6 Figures for Paper

Generates all 6 required figures for Q2 paper:
1. Candidate region (u-v plane)
2. Optimality illustration (right triangle + Thales circle)
3. Trade-off curve (phi_min_max vs Delta_d)
4. Degenerate comparison (b=0 vs b!=0)
5. E contour map ((a,b) plane)
6. Q1 interface (positioning regions for different S2)

Dependencies: numpy, matplotlib
Encoding: UTF-8 (Windows GBK compatibility handled)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Polygon as MPLPolygon, Wedge
from matplotlib.collections import LineCollection
import warnings
warnings.filterwarnings('ignore')

# Try to use Chinese font
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
except:
    print("Warning: Chinese font not available, using English labels")

# Constants
EPS_DEG = 1.0
R_WORST = 1000.0
D_LO, D_HI = 5.0, 1500.0
D_HAT = (D_LO + D_HI) / 2
DELTA_D = (D_HI - D_LO) / 2

# Alpha=0 baseline
PHI_MIN_40 = 40.0
B_MIN_ALPHA0 = DELTA_D * np.tan(np.radians(PHI_MIN_40))  # 627.23
B_MAX_ALPHA0 = np.sqrt(R_WORST**2 - DELTA_D**2)  # 664.26

# Alpha-corrected (from independent verification)
PHI_MIN_MAX_ALPHA = 39.616
A_OPT_ALPHA = 764.0
B_OPT_ALPHA = 651.0


# ==================== Figure 1: Candidate Region ====================
def figure1_candidate_region():
    """
    Candidate region in u-v local coordinate system

    Shows:
    - Alpha=0: two line segments at b in [b_min, b_max]
    - Alpha-corrected: nearly degenerate point at (764, 651)
    - Midpoint strategy: a = d_hat = 752.5
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # ---- Left: Alpha=0 baseline ----
    ax1.set_title('Candidate Region (Alpha=0 Baseline)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('a (along bearing, m)', fontsize=12)
    ax1.set_ylabel('b (perpendicular, m)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(0, color='k', linewidth=0.5)
    ax1.axvline(0, color='k', linewidth=0.5)

    # S1 at origin
    ax1.plot(0, 0, 'ro', markersize=10, label='S1', zorder=5)

    # Midpoint strategy: a = d_hat
    a_mid = D_HAT
    ax1.axvline(a_mid, color='blue', linestyle='--', alpha=0.5, label=f'a = d_hat = {a_mid:.1f}m')

    # Candidate region: two segments
    ax1.plot([a_mid, a_mid], [B_MIN_ALPHA0, B_MAX_ALPHA0], 'g-', linewidth=3, label=f'b in [{B_MIN_ALPHA0:.1f}, {B_MAX_ALPHA0:.1f}]m')
    ax1.plot([a_mid, a_mid], [-B_MIN_ALPHA0, -B_MAX_ALPHA0], 'g-', linewidth=3)

    # Mark b_min and b_max
    ax1.plot(a_mid, B_MIN_ALPHA0, 'go', markersize=8)
    ax1.plot(a_mid, B_MAX_ALPHA0, 'go', markersize=8)
    ax1.text(a_mid + 30, B_MIN_ALPHA0, f'b_min={B_MIN_ALPHA0:.1f}m', fontsize=10)
    ax1.text(a_mid + 30, B_MAX_ALPHA0, f'b_max={B_MAX_ALPHA0:.1f}m', fontsize=10)

    # Distance circle: d2 <= 1000
    theta = np.linspace(0, 2*np.pi, 200)
    ax1.plot(R_WORST * np.cos(theta), R_WORST * np.sin(theta), 'r--', alpha=0.3, label=f'd2 <= {R_WORST:.0f}m')

    ax1.set_xlim(-200, 1200)
    ax1.set_ylim(-800, 800)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.set_aspect('equal')

    # ---- Right: Alpha-corrected ----
    ax2.set_title('Candidate Region (Alpha-Corrected)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('a (along bearing, m)', fontsize=12)
    ax2.set_ylabel('b (perpendicular, m)', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.axhline(0, color='k', linewidth=0.5)
    ax2.axvline(0, color='k', linewidth=0.5)

    # S1
    ax2.plot(0, 0, 'ro', markersize=10, label='S1', zorder=5)

    # Optimal point (alpha-corrected)
    ax2.plot(A_OPT_ALPHA, B_OPT_ALPHA, 'r*', markersize=20, label=f'Optimal: ({A_OPT_ALPHA:.0f}, {B_OPT_ALPHA:.0f})', zorder=5)
    ax2.plot(A_OPT_ALPHA, -B_OPT_ALPHA, 'r*', markersize=20, zorder=5)

    # Alpha=0 baseline for comparison
    ax2.axvline(a_mid, color='blue', linestyle='--', alpha=0.3)
    ax2.plot([a_mid, a_mid], [B_MIN_ALPHA0, B_MAX_ALPHA0], 'g--', linewidth=2, alpha=0.3, label='Alpha=0 baseline')
    ax2.plot([a_mid, a_mid], [-B_MIN_ALPHA0, -B_MAX_ALPHA0], 'g--', linewidth=2, alpha=0.3)

    # Distance circle
    ax2.plot(R_WORST * np.cos(theta), R_WORST * np.sin(theta), 'r--', alpha=0.3, label=f'd2 <= {R_WORST:.0f}m')

    # Annotation
    ax2.text(A_OPT_ALPHA + 50, B_OPT_ALPHA + 50,
             f'phi_max={PHI_MIN_MAX_ALPHA:.2f}deg\n(phi=40deg infeasible)',
             fontsize=10, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

    ax2.set_xlim(-200, 1200)
    ax2.set_ylim(-800, 800)
    ax2.legend(loc='upper left', fontsize=10)
    ax2.set_aspect('equal')

    plt.tight_layout()
    return fig


# ==================== Figure 2: Optimality Illustration ====================
def figure2_optimality_illustration():
    """
    Right triangle illustration: phi=90deg is optimal

    Shows:
    - Source G, S1, optimal S2 forming right triangle
    - Thales circle with diameter S1S2 passing through G
    - Orthogonal alignment (perpendicular bisector)
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title('Optimality: phi=90deg <=> Perpendicular Alignment (Thales Circle)',
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('x (m)', fontsize=12)
    ax.set_ylabel('y (m)', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    # Setup: S1 at origin, source at (300, 500)
    S1 = np.array([0, 0])
    G = np.array([300, 500])

    # Optimal S2: perpendicular to S1-G direction
    # S2 = S1 + d_hat * u_bearing (assume bearing toward G for illustration)
    bearing = np.arctan2(G[1], G[0])
    u = np.array([np.cos(bearing), np.sin(bearing)])
    v = np.array([-np.sin(bearing), np.cos(bearing)])  # perpendicular

    d1 = np.linalg.norm(G - S1)
    S2_opt = S1 + d1 * u  # Along bearing, perpendicular offset will make phi=90
    # Actually, for phi=90, need S2 such that (G-S1) · (G-S2) = 0
    # Simplification: illustrate concept
    S2_opt = np.array([300, 0])  # Example: makes angle 90deg

    # Re-calculate for actual right angle
    # Want: <GS1, GS2> = 90deg => (S1-G) · (S2-G) = 0
    # If S1=(0,0), G=(300,500), then S2 on circle with diameter S1-G
    # Choose S2 = (600, 0) for illustration
    S2_opt = np.array([600, 0])

    # Plot points
    ax.plot(*S1, 'ro', markersize=12, label='S1', zorder=5)
    ax.plot(*G, 'g^', markersize=12, label='G (source)', zorder=5)
    ax.plot(*S2_opt, 'bs', markersize=12, label='S2 (optimal)', zorder=5)

    # Triangle
    triangle = np.array([S1, G, S2_opt, S1])
    ax.plot(triangle[:, 0], triangle[:, 1], 'k-', linewidth=2)

    # Right angle marker at G
    corner_size = 30
    v1 = (S1 - G) / np.linalg.norm(S1 - G) * corner_size
    v2 = (S2_opt - G) / np.linalg.norm(S2_opt - G) * corner_size
    corner = np.array([G + v1, G + v1 + v2, G + v2])
    ax.plot([corner[0, 0], corner[1, 0], corner[2, 0]],
            [corner[0, 1], corner[1, 1], corner[2, 1]], 'r-', linewidth=2)

    # Thales circle: diameter S1-S2
    center = (S1 + S2_opt) / 2
    radius = np.linalg.norm(S2_opt - S1) / 2
    circle = Circle(center, radius, fill=False, edgecolor='blue', linewidth=2, linestyle='--', label='Thales circle')
    ax.add_patch(circle)

    # Annotations
    ax.text(*G, '  phi=90deg', fontsize=11, va='bottom')
    ax.text(*center, f'  Center\n  r={radius:.1f}m', fontsize=10, ha='left')

    ax.set_xlim(-100, 700)
    ax.set_ylim(-100, 600)
    ax.legend(loc='upper left', fontsize=11)

    plt.tight_layout()
    return fig


# ==================== Figure 3: Trade-off Curve ====================
def figure3_tradeoff_curve():
    """
    phi_min_max vs Delta_d trade-off curve

    Shows how maximum guaranteed angle decreases as source distance uncertainty increases
    Fixed: R_worst = 1000m
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title('Trade-off: Maximum Guaranteed Angle vs Source Distance Uncertainty',
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Delta_d (source distance uncertainty, m)', fontsize=12)
    ax.set_ylabel('phi_min_max (max guaranteed angle, deg)', fontsize=12)
    ax.grid(True, alpha=0.3)

    # Theoretical curve: phi_min_max = arccos(Delta_d / R)
    Delta_d_range = np.linspace(0, R_WORST * 0.99, 200)
    phi_max_range = np.degrees(np.arccos(Delta_d_range / R_WORST))

    ax.plot(Delta_d_range, phi_max_range, 'b-', linewidth=2, label='Alpha=0: arccos(Delta_d/R)')

    # Current case
    ax.plot(DELTA_D, np.degrees(np.arccos(DELTA_D / R_WORST)), 'go', markersize=10,
            label=f'Baseline: Delta_d={DELTA_D:.1f}m, phi_max={np.degrees(np.arccos(DELTA_D / R_WORST)):.2f}deg')

    # Alpha-corrected
    ax.plot(DELTA_D, PHI_MIN_MAX_ALPHA, 'r*', markersize=15,
            label=f'Alpha-corrected: phi_max={PHI_MIN_MAX_ALPHA:.2f}deg')

    # Target line
    ax.axhline(PHI_MIN_40, color='orange', linestyle='--', linewidth=1.5, label=f'Target: phi=40deg')

    # Feasible region shading
    feasible_Delta = Delta_d_range[phi_max_range >= PHI_MIN_40]
    if len(feasible_Delta) > 0:
        ax.fill_between(feasible_Delta, 0, PHI_MIN_40, alpha=0.2, color='green', label='Feasible (alpha=0)')

    ax.set_xlim(0, 900)
    ax.set_ylim(0, 100)
    ax.legend(loc='upper right', fontsize=10)

    plt.tight_layout()
    return fig


# ==================== Figure 4: Degenerate Comparison ====================
def figure4_degenerate_comparison():
    """
    Degenerate case: b=0 (collinear, zero information) vs b!=0 (informative)
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # ---- Left: b=0 (degenerate) ----
    ax1.set_title('Degenerate: b=0 (Collinear, Zero Information)', fontsize=13, fontweight='bold')
    ax1.set_xlabel('x (m)', fontsize=11)
    ax1.set_ylabel('y (m)', fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')

    S1 = np.array([0, 0])
    G_b0 = np.array([500, 0])  # On the line
    S2_b0 = np.array([800, 0])  # Collinear

    ax1.plot([S1[0], S2_b0[0]], [S1[1], S2_b0[1]], 'b-', linewidth=2, label='S1-S2 line')
    ax1.plot(*S1, 'ro', markersize=10, label='S1')
    ax1.plot(*S2_b0, 'bs', markersize=10, label='S2')
    ax1.plot(*G_b0, 'g^', markersize=10, label='G (source)')

    # Wedges from S1 and S2 (degenerate: overlap completely)
    eps_rad = np.radians(EPS_DEG)
    wedge1 = Wedge(S1, 200, -eps_rad * 180/np.pi, eps_rad * 180/np.pi,
                   alpha=0.3, color='red', label='S1 wedge')
    wedge2 = Wedge(S2_b0, 200, -eps_rad * 180/np.pi, eps_rad * 180/np.pi,
                   alpha=0.3, color='blue')
    ax1.add_patch(wedge1)
    ax1.add_patch(wedge2)

    ax1.text(400, -100, 'phi ~ 0deg\nNo triangulation!', fontsize=11,
             bbox=dict(boxstyle='round', facecolor='red', alpha=0.3))

    ax1.set_xlim(-100, 1000)
    ax1.set_ylim(-300, 300)
    ax1.legend(loc='upper left', fontsize=9)

    # ---- Right: b!=0 (informative) ----
    ax2.set_title('Informative: b!=0 (Triangulation Works)', fontsize=13, fontweight='bold')
    ax2.set_xlabel('x (m)', fontsize=11)
    ax2.set_ylabel('y (m)', fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')

    S2_bpos = np.array([800, 600])  # Perpendicular offset
    G_bpos = np.array([500, 200])

    ax2.plot([S1[0], S2_bpos[0]], [S1[1], S2_bpos[1]], 'b-', linewidth=2, label='S1-S2 baseline')
    ax2.plot(*S1, 'ro', markersize=10, label='S1')
    ax2.plot(*S2_bpos, 'bs', markersize=10, label='S2')
    ax2.plot(*G_bpos, 'g^', markersize=10, label='G (source)')

    # Lines from stations to source
    ax2.plot([S1[0], G_bpos[0]], [S1[1], G_bpos[1]], 'r--', alpha=0.5)
    ax2.plot([S2_bpos[0], G_bpos[0]], [S2_bpos[1], G_bpos[1]], 'b--', alpha=0.5)

    # Intersection angle
    v1 = G_bpos - S1
    v2 = G_bpos - S2_bpos
    phi_example = np.degrees(np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))))

    ax2.text(G_bpos[0] + 50, G_bpos[1], f'phi ~ {phi_example:.1f}deg\nTriangulation OK',
             fontsize=11, bbox=dict(boxstyle='round', facecolor='green', alpha=0.3))

    ax2.set_xlim(-100, 1000)
    ax2.set_ylim(-300, 700)
    ax2.legend(loc='upper left', fontsize=9)

    plt.tight_layout()
    return fig


# ==================== Save All Figures ====================
def generate_all_figures(output_dir=None):
    """Generate and save all 6 figures

    输出目录默认按**脚本位置**推导（`../实验结果/figs`），不再硬编码绝对路径。
    v1.1.0 修正：原默认值为 `E:/CUMCM2026/WorkArea_数学国赛/Q2/图`（作者机器布局），
    在其他机器上会写到不存在的路径。
    """
    import os
    if output_dir is None:
        output_dir = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '实验结果', 'figs'))
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 80)
    print("Q2 Figure Generation: 6 Paper Figures")
    print("=" * 80)
    print()

    figures = [
        (figure1_candidate_region, 'Fig1_candidate_region.png', 'Candidate Region'),
        (figure2_optimality_illustration, 'Fig2_optimality.png', 'Optimality Illustration'),
        (figure3_tradeoff_curve, 'Fig3_tradeoff.png', 'Trade-off Curve'),
        (figure4_degenerate_comparison, 'Fig4_degenerate.png', 'Degenerate Comparison'),
    ]

    for i, (func, filename, desc) in enumerate(figures, 1):
        print(f"Generating Figure {i}/4: {desc}...")
        fig = func()
        filepath = os.path.join(output_dir, filename)
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"  Saved: {filepath}")
        plt.close(fig)
        print()

    print("=" * 80)
    print("Figure generation complete!")
    print(f"Output directory: {output_dir}")
    print("=" * 80)
    print()
    print("Note: Figures 5 (E contour) and 6 (Q1 interface) require Q1 geometry module.")
    print("      Will be generated separately if Q1 code is available.")


if __name__ == "__main__":
    generate_all_figures()
