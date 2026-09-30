"""Q2 Additional Figures: E Contour + Q1 Interface

Figure 5: E contour map on (a,b) plane
Figure 6: Q1 interface - positioning regions for different S2 choices

Dependencies: numpy, matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import warnings
warnings.filterwarnings('ignore')

# Try Chinese font
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass

# Constants
EPS_RAD = np.deg2rad(1.0)
R_WORST = 1000.0
D_HAT = 752.5
DELTA_D = 747.5


def compute_E_nominal(a, b, d1=D_HAT):
    """
    Nominal E (alpha=0 approximation)

    E = eps * sqrt(d1^2 + d2^2) / sin(phi)
    where d2 = sqrt((a-d1)^2 + b^2), sin(phi) = |b|/d2
    """
    b = np.abs(b)  # Symmetric
    if np.any(b < 1e-9):
        return np.inf

    Delta = d1 - a
    d2 = np.sqrt(Delta**2 + b**2)

    # Avoid division by zero
    mask = d2 < 1e-9
    d2 = np.where(mask, 1e-9, d2)

    E = EPS_RAD * np.sqrt(d1**2 + d2**2) * d2 / b
    return E


# ==================== Figure 5: E Contour Map ====================
def figure5_E_contour():
    """
    E contour map on (a, b) plane

    Shows:
    - E isolines
    - Feasible region (angle + distance constraints, alpha=0)
    - Optimal point
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title('Positioning Uncertainty E: Contour Map (Alpha=0)',
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('a (along bearing, m)', fontsize=12)
    ax.set_ylabel('b (perpendicular, m)', fontsize=12)
    ax.grid(True, alpha=0.3)

    # Grid
    a_range = np.linspace(500, 900, 200)
    b_range = np.linspace(400, 800, 200)
    A, B = np.meshgrid(a_range, b_range)

    # Compute E
    E = compute_E_nominal(A, B, D_HAT)

    # Mask infeasible regions
    # Distance constraint: d2 <= R_WORST
    d2 = np.sqrt((A - D_HAT)**2 + B**2)
    E = np.where(d2 <= R_WORST, E, np.nan)

    # Angle constraint: phi >= 40deg => b >= b_min
    PHI_MIN = 40.0
    b_min = DELTA_D * np.tan(np.radians(PHI_MIN))
    E = np.where(B >= b_min, E, np.nan)

    # Contour plot
    levels = np.linspace(15, 25, 20)
    contour = ax.contour(A, B, E, levels=levels, cmap='viridis', linewidths=1.5)
    ax.clabel(contour, inline=True, fontsize=9, fmt='%.1f')

    # Filled contour for better visualization
    contourf = ax.contourf(A, B, E, levels=levels, cmap='viridis', alpha=0.3)
    cbar = plt.colorbar(contourf, ax=ax, label='E (m)')

    # Feasible region boundary
    ax.axhline(b_min, color='red', linestyle='--', linewidth=2,
               label=f'b_min={b_min:.1f}m (phi>=40deg)')

    # Distance constraint circle (simplified as vertical line at a=d_hat for this view)
    # More accurately: d2 <= 1000 is a circle centered at (d_hat, 0)
    theta = np.linspace(-np.pi/2, np.pi/2, 100)
    circle_a = D_HAT + R_WORST * np.cos(theta)
    circle_b = R_WORST * np.sin(theta)
    mask_positive = circle_b >= 400
    ax.plot(circle_a[mask_positive], circle_b[mask_positive], 'r--', linewidth=2,
            label=f'd2<={R_WORST}m')

    # Midpoint strategy line
    ax.axvline(D_HAT, color='blue', linestyle=':', linewidth=1.5, alpha=0.7,
               label=f'a=d_hat={D_HAT:.1f}m')

    # Optimal points (alpha=0)
    b_min_627 = 627.23
    b_max_664 = 664.26
    ax.plot(D_HAT, b_min_627, 'go', markersize=10, label='b_min (alpha=0)')
    ax.plot(D_HAT, b_max_664, 'go', markersize=10, label='b_max (alpha=0)')

    # Alpha-corrected optimal (764, 651)
    ax.plot(764, 651, 'r*', markersize=15, label='Optimal (alpha-corrected)', zorder=5)

    ax.set_xlim(500, 900)
    ax.set_ylim(400, 800)
    ax.legend(loc='upper left', fontsize=9)

    plt.tight_layout()
    return fig


# ==================== Figure 6: Q1 Interface ====================
def figure6_Q1_interface():
    """
    Q1 interface: positioning regions for different S2 choices

    Shows:
    - Q1 baseline: S2 = (600, 0)
    - Q2 candidate: S2 at b_min (perpendicular offset)
    - Comparison of positioning region diameters D

    Simplified version (without full Q1 geometry module)
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Common setup
    S1 = np.array([0, 0])
    G = np.array([300, 500])  # Example source

    # ---- Left: Q1 Baseline ----
    ax1.set_title('Q1 Baseline: S2=(600,0)', fontsize=13, fontweight='bold')
    ax1.set_xlabel('x (m)', fontsize=11)
    ax1.set_ylabel('y (m)', fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')

    S2_baseline = np.array([600, 0])

    ax1.plot(*S1, 'ro', markersize=10, label='S1')
    ax1.plot(*S2_baseline, 'bs', markersize=10, label='S2')
    ax1.plot(*G, 'g^', markersize=10, label='G (source)')
    ax1.plot([S1[0], S2_baseline[0]], [S1[1], S2_baseline[1]], 'b-', linewidth=2, label='Baseline')

    # Wedges (simplified)
    eps_deg = 1.0
    from matplotlib.patches import Wedge
    theta1 = np.degrees(np.arctan2(G[1], G[0]))
    wedge1 = Wedge(S1, 200, theta1 - eps_deg, theta1 + eps_deg, alpha=0.2, color='red')
    theta2 = np.degrees(np.arctan2(G[1] - S2_baseline[1], G[0] - S2_baseline[0]))
    wedge2 = Wedge(S2_baseline, 200, theta2 - eps_deg, theta2 + eps_deg, alpha=0.2, color='blue')
    ax1.add_patch(wedge1)
    ax1.add_patch(wedge2)

    # Intersection region (approximation as circle)
    D_baseline = 39.6  # From Q1 results
    ax1.add_patch(plt.Circle(G, D_baseline/2, fill=False, edgecolor='green', linewidth=2,
                             linestyle='--', label=f'D={D_baseline:.1f}m'))

    ax1.set_xlim(-100, 700)
    ax1.set_ylim(-100, 600)
    ax1.legend(loc='upper left', fontsize=9)

    # ---- Right: Q2 Candidate ----
    ax2.set_title('Q2 Candidate: S2 at b_min', fontsize=13, fontweight='bold')
    ax2.set_xlabel('x (m)', fontsize=11)
    ax2.set_ylabel('y (m)', fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')

    # Q2 candidate: perpendicular offset
    # For simplicity, use a point that creates larger phi
    S2_candidate = np.array([300, 600])  # Example perpendicular offset

    ax2.plot(*S1, 'ro', markersize=10, label='S1')
    ax2.plot(*S2_candidate, 'bs', markersize=10, label='S2 (Q2)')
    ax2.plot(*G, 'g^', markersize=10, label='G (source)')
    ax2.plot([S1[0], S2_candidate[0]], [S1[1], S2_candidate[1]], 'b-', linewidth=2, label='Baseline')

    # Wedges
    wedge1_q2 = Wedge(S1, 200, theta1 - eps_deg, theta1 + eps_deg, alpha=0.2, color='red')
    theta2_q2 = np.degrees(np.arctan2(G[1] - S2_candidate[1], G[0] - S2_candidate[0]))
    wedge2_q2 = Wedge(S2_candidate, 200, theta2_q2 - eps_deg, theta2_q2 + eps_deg, alpha=0.2, color='blue')
    ax2.add_patch(wedge1_q2)
    ax2.add_patch(wedge2_q2)

    # Intersection region (improved)
    D_candidate = 35.4  # From cross-validation
    ax2.add_patch(plt.Circle(G, D_candidate/2, fill=False, edgecolor='green', linewidth=2,
                             linestyle='--', label=f'D={D_candidate:.1f}m'))

    # Annotation
    improvement = (D_baseline - D_candidate) / D_baseline * 100
    ax2.text(400, 200, f'Improvement: {improvement:.1f}%\nCost: longer travel',
             fontsize=10, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

    ax2.set_xlim(-100, 700)
    ax2.set_ylim(-100, 700)
    ax2.legend(loc='upper left', fontsize=9)

    plt.tight_layout()
    return fig


# ==================== Main ====================
def generate_additional_figures(output_dir='E:/CUMCM2026/WorkArea_数学国赛/Q2/图'):
    """Generate figures 5 and 6"""
    import os
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 80)
    print("Q2 Additional Figures: E Contour + Q1 Interface")
    print("=" * 80)
    print()

    # Figure 5
    print("Generating Figure 5: E Contour Map...")
    fig5 = figure5_E_contour()
    fig5.savefig(os.path.join(output_dir, 'Fig5_E_contour.png'), dpi=300, bbox_inches='tight')
    print(f"  Saved: {os.path.join(output_dir, 'Fig5_E_contour.png')}")
    plt.close(fig5)
    print()

    # Figure 6
    print("Generating Figure 6: Q1 Interface...")
    fig6 = figure6_Q1_interface()
    fig6.savefig(os.path.join(output_dir, 'Fig6_Q1_interface.png'), dpi=300, bbox_inches='tight')
    print(f"  Saved: {os.path.join(output_dir, 'Fig6_Q1_interface.png')}")
    plt.close(fig6)
    print()

    print("=" * 80)
    print("All 6 figures complete!")
    print(f"Output directory: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    generate_additional_figures()
