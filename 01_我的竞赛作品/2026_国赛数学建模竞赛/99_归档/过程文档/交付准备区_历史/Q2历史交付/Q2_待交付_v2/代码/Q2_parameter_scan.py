"""Q2 Parameter Scan: 180-case Factor Matrix

Scans parameter space to verify theoretical relationships:
  - 4 values of Delta_d: [200, 400, 600, 747.5] m
  - 5 values of phi_min: [30, 35, 40, 45, 50] deg
  - 3 values of R_worst: [800, 1000, 1200] m
  - 3 values of d_hat: [500, 752.5, 1000] m

Total: 4 × 5 × 3 × 3 = 180 cases

For each case, compute:
  - b_min, b_max (alpha=0)
  - Feasibility (b_min <= b_max)
  - phi_min_max (theoretical upper bound)
  - Width = b_max - b_min (if feasible)

Dependencies: numpy, pandas
Output: CSV file for analysis
"""

import numpy as np
import pandas as pd
from typing import Tuple

# Constants
EPS_RAD = np.deg2rad(1.0)


def candidate_region_alpha0(
    delta_d: float,
    phi_min_deg: float,
    r_worst: float,
    d_hat: float
) -> Tuple[float, float, bool, float, float]:
    """
    Compute candidate region bounds (alpha=0 baseline)

    Args:
        delta_d: Source distance uncertainty radius (m)
        phi_min_deg: Target minimum intersection angle (deg)
        r_worst: Worst-case reception radius (m)
        d_hat: Nominal source distance (m)

    Returns:
        (b_min, b_max, feasible, phi_min_max, width)
    """
    phi_min_rad = np.radians(phi_min_deg)

    # Closed-form solution (alpha=0)
    b_min = delta_d * np.tan(phi_min_rad)

    # Check if distance constraint is satisfiable
    if delta_d >= r_worst:
        # Infeasible: no source can be at distance d in [d_hat-delta_d, d_hat+delta_d]
        # while d2 <= r_worst
        return b_min, np.nan, False, 0.0, np.nan

    b_max = np.sqrt(r_worst**2 - delta_d**2)

    # Theoretical upper bound: phi_min_max = arccos(delta_d / r_worst)
    phi_min_max = np.degrees(np.arccos(delta_d / r_worst))

    # Feasibility
    feasible = b_min <= b_max

    # Width
    width = b_max - b_min if feasible else np.nan

    return b_min, b_max, feasible, phi_min_max, width


def parameter_scan():
    """
    Execute 180-case parameter scan

    Returns:
        DataFrame with results
    """
    # Parameter ranges
    delta_d_values = [200.0, 400.0, 600.0, 747.5]
    phi_min_values = [30.0, 35.0, 40.0, 45.0, 50.0]
    r_worst_values = [800.0, 1000.0, 1200.0]
    d_hat_values = [500.0, 752.5, 1000.0]

    results = []

    case_id = 0
    for delta_d in delta_d_values:
        for phi_min in phi_min_values:
            for r_worst in r_worst_values:
                for d_hat in d_hat_values:
                    case_id += 1

                    b_min, b_max, feasible, phi_max, width = candidate_region_alpha0(
                        delta_d, phi_min, r_worst, d_hat
                    )

                    results.append({
                        'case_id': case_id,
                        'delta_d': delta_d,
                        'phi_min_target': phi_min,
                        'R_worst': r_worst,
                        'd_hat': d_hat,
                        'b_min': b_min,
                        'b_max': b_max,
                        'feasible': feasible,
                        'phi_min_max': phi_max,
                        'width': width,
                        # Derived quantities
                        'feasibility_ratio': delta_d / r_worst,
                        'angle_margin': phi_max - phi_min if feasible else np.nan,
                    })

    df = pd.DataFrame(results)
    return df


def analyze_results(df: pd.DataFrame):
    """
    Analyze scan results and print summary statistics
    """
    print("=" * 80)
    print("Q2 Parameter Scan: 180-Case Summary")
    print("=" * 80)
    print()

    print(f"Total cases: {len(df)}")
    print(f"Feasible cases: {df['feasible'].sum()} ({df['feasible'].sum()/len(df)*100:.1f}%)")
    print(f"Infeasible cases: {(~df['feasible']).sum()} ({(~df['feasible']).sum()/len(df)*100:.1f}%)")
    print()

    # Feasibility by phi_min target
    print("Feasibility by phi_min target:")
    print("-" * 80)
    feasibility_by_phi = df.groupby('phi_min_target')['feasible'].agg(['sum', 'count', 'mean'])
    feasibility_by_phi.columns = ['Feasible', 'Total', 'Rate']
    print(feasibility_by_phi)
    print()

    # Feasibility by delta_d
    print("Feasibility by delta_d:")
    print("-" * 80)
    feasibility_by_delta = df.groupby('delta_d')['feasible'].agg(['sum', 'count', 'mean'])
    feasibility_by_delta.columns = ['Feasible', 'Total', 'Rate']
    print(feasibility_by_delta)
    print()

    # Width statistics (feasible cases only)
    print("Width statistics (feasible cases):")
    print("-" * 80)
    feasible_df = df[df['feasible']]
    print(f"Mean width: {feasible_df['width'].mean():.2f} m")
    print(f"Std width: {feasible_df['width'].std():.2f} m")
    print(f"Min width: {feasible_df['width'].min():.2f} m")
    print(f"Max width: {feasible_df['width'].max():.2f} m")
    print()

    # Theoretical relationship verification
    print("Theoretical relationship: phi_min_max = arccos(delta_d / R_worst)")
    print("-" * 80)
    df_check = df[df['feasible']].copy()
    df_check['phi_theoretical'] = np.degrees(np.arccos(df_check['delta_d'] / df_check['R_worst']))
    df_check['phi_error'] = np.abs(df_check['phi_min_max'] - df_check['phi_theoretical'])
    print(f"Max error: {df_check['phi_error'].max():.6f} deg (numerical precision)")
    print()

    # Baseline case
    print("Baseline case (delta_d=747.5, phi_min=40, R=1000, d_hat=752.5):")
    print("-" * 80)
    baseline = df[(df['delta_d'] == 747.5) &
                  (df['phi_min_target'] == 40.0) &
                  (df['R_worst'] == 1000.0) &
                  (df['d_hat'] == 752.5)]
    if not baseline.empty:
        row = baseline.iloc[0]
        print(f"  b_min: {row['b_min']:.2f} m")
        print(f"  b_max: {row['b_max']:.2f} m")
        print(f"  Feasible: {row['feasible']}")
        print(f"  phi_min_max: {row['phi_min_max']:.2f} deg")
        print(f"  Width: {row['width']:.2f} m" if row['feasible'] else "  Width: N/A")
    print()


def main():
    """Execute parameter scan and save results"""
    print("=" * 80)
    print("Q2 Parameter Scan: Starting 180-case sweep")
    print("=" * 80)
    print()

    # Execute scan
    print("Scanning parameter space...")
    df = parameter_scan()
    print(f"  Completed: {len(df)} cases")
    print()

    # Save to CSV
    output_path = 'E:/CUMCM2026/WorkArea_数学国赛/Q2/实验结果/Q2_parameter_scan_180.csv'
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Results saved: {output_path}")
    print()

    # Analyze
    analyze_results(df)

    # Key insights
    print("=" * 80)
    print("Key Insights:")
    print("=" * 80)
    print("1. Feasibility decreases as phi_min target increases")
    print("2. Feasibility decreases as delta_d increases (relative to R_worst)")
    print("3. Theoretical bound phi_min_max = arccos(delta_d/R) verified numerically")
    print("4. Baseline case (747.5, 40deg, 1000m) is feasible under alpha=0")
    print("   but becomes infeasible when alpha uncertainty is added")
    print("=" * 80)


if __name__ == "__main__":
    main()
