"""
Visualization Module for Floorplanning Results

Functions:
1. plot_layout: Draw block layout with dimensions
2. plot_convergence: Show cost convergence curves
3. generate_summary_table: Create LaTeX table for paper
"""
import os
import csv
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Dict
from data_loader import Block
from btree import BTree
from config import OUTPUT_DIR, VIS_PARAMS


def plot_layout(tree: BTree, blocks: List[Block],
                title: str = "Layout",
                filename: str = None):
    """
    Plot block layout from B*-Tree.

    Args:
        tree: B*-Tree structure
        blocks: List of Block objects
        title: Plot title
        filename: Output filename (PNG)
    """
    W, H, coords = tree.pack()

    fig, ax = plt.subplots(figsize=VIS_PARAMS['figsize'], dpi=VIS_PARAMS['dpi'])

    # Draw each block
    cmap = plt.cm.get_cmap(VIS_PARAMS['colors'])
    n_blocks = len(coords)

    for i, (x, y, w, h) in enumerate(coords):
        color = cmap(i / max(n_blocks, 1))
        rect = patches.Rectangle((x, y), w, h,
                                 linewidth=1,
                                 edgecolor='black',
                                 facecolor=color,
                                 alpha=0.7)
        ax.add_patch(rect)

        # Add block label (center)
        cx, cy = x + w/2, y + h/2
        ax.text(cx, cy, blocks[i].name,
               ha='center', va='center',
               fontsize=6, color='white', weight='bold')

    # Set axis
    ax.set_xlim(0, W * 1.05)
    ax.set_ylim(0, H * 1.05)
    ax.set_aspect('equal')
    ax.set_xlabel('Width')
    ax.set_ylabel('Height')

    # Add metrics
    R = max(W, H) / min(W, H)
    A = W * H
    A_total = sum(b.area for b in blocks)
    deadspace = (A - A_total) / A_total * 100

    metrics_text = (f"W={W:.1f}, H={H:.1f}, R={R:.3f}\n"
                   f"Area={A:.0f}, Deadspace={deadspace:.2f}%")
    ax.text(0.02, 0.98, metrics_text,
           transform=ax.transAxes,
           fontsize=10,
           verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    ax.set_title(title, fontsize=14, weight='bold')
    ax.grid(True, alpha=0.3)

    if filename:
        plt.savefig(filename, bbox_inches='tight')
        print(f"Layout saved: {filename}")
    else:
        plt.show()

    plt.close()


def plot_convergence_from_csv(csv_path: str,
                               dataset: str = 'n100',
                               filename: str = None):
    """
    Plot convergence curves comparing different methods.

    Args:
        csv_path: Path to results CSV
        dataset: Dataset to plot
        filename: Output filename (PNG)
    """
    # Read results
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        results = list(reader)

    # Filter by dataset
    filtered = [r for r in results if r['dataset'] == dataset]

    if not filtered:
        print(f"No data for {dataset}")
        return

    # Group by method
    methods = {}
    for r in filtered:
        key = f"{r['cost_method']}_{r['initial_method']}"
        if key not in methods:
            methods[key] = []
        methods[key].append(float(r['gap']))

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6), dpi=VIS_PARAMS['dpi'])

    for method, gaps in methods.items():
        # Sort gaps (simulating convergence)
        sorted_gaps = sorted(gaps, reverse=True)
        ax.plot(range(len(sorted_gaps)), sorted_gaps,
               marker='o', label=method, linewidth=2)

    ax.set_xlabel('Iteration (seed)', fontsize=12)
    ax.set_ylabel('Gap (%)', fontsize=12)
    ax.set_title(f'Convergence Comparison - {dataset}', fontsize=14, weight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    if filename:
        plt.savefig(filename, bbox_inches='tight')
        print(f"Convergence plot saved: {filename}")
    else:
        plt.show()

    plt.close()


def generate_summary_table(csv_path: str, output_tex: str = None):
    """
    Generate LaTeX summary table from results CSV.

    Args:
        csv_path: Path to results CSV
        output_tex: Output LaTeX file
    """
    # Read results
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        results = list(reader)

    # Group by dataset and method
    groups = {}
    for r in results:
        key = (r['dataset'], r['cost_method'], r['initial_method'])
        if key not in groups:
            groups[key] = []
        groups[key].append({
            'max_side': float(r['max_side']),
            'aspect_ratio': float(r['aspect_ratio']),
            'deadspace': float(r['deadspace']),
            'gap': float(r['gap']),
            'time': float(r['time']),
        })

    # Compute statistics
    stats = {}
    for key, values in groups.items():
        dataset, cost, initial = key
        n = len(values)
        if n == 0:
            continue

        stats[key] = {
            'max_side_mean': sum(v['max_side'] for v in values) / n,
            'max_side_std': (sum((v['max_side'] - sum(v['max_side'] for v in values)/n)**2 for v in values) / n)**0.5,
            'R_mean': sum(v['aspect_ratio'] for v in values) / n,
            'gap_mean': sum(v['gap'] for v in values) / n,
            'time_mean': sum(v['time'] for v in values) / n,
        }

    # Generate LaTeX
    latex = []
    latex.append(r"\begin{table}[htbp]")
    latex.append(r"\centering")
    latex.append(r"\caption{Experimental Results Summary}")
    latex.append(r"\begin{tabular}{llrrrr}")
    latex.append(r"\hline")
    latex.append(r"Dataset & Method & max(W,H) & R & Gap(\%) & Time(s) \\")
    latex.append(r"\hline")

    for key in sorted(stats.keys()):
        dataset, cost, initial = key
        s = stats[key]
        method = f"{cost}/{initial}"
        latex.append(f"{dataset} & {method} & "
                    f"{s['max_side_mean']:.1f} $\\pm$ {s['max_side_std']:.1f} & "
                    f"{s['R_mean']:.3f} & "
                    f"{s['gap_mean']:.2f} & "
                    f"{s['time_mean']:.1f} \\\\")

    latex.append(r"\hline")
    latex.append(r"\end{tabular}")
    latex.append(r"\end{table}")

    latex_text = "\n".join(latex)

    if output_tex:
        with open(output_tex, 'w') as f:
            f.write(latex_text)
        print(f"LaTeX table saved: {output_tex}")
    else:
        print(latex_text)

    return latex_text


def visualize_all(csv_path: str):
    """
    Generate all visualizations from results CSV.

    Args:
        csv_path: Path to results CSV
    """
    print("=" * 70)
    print("Generating Visualizations")
    print("=" * 70)
    print()

    # Convergence plots for each dataset
    for dataset in ['n100', 'n200', 'n300']:
        filename = os.path.join(OUTPUT_DIR, f'convergence_{dataset}.png')
        plot_convergence_from_csv(csv_path, dataset, filename)

    # Summary table
    tex_file = os.path.join(OUTPUT_DIR, 'summary_table.tex')
    generate_summary_table(csv_path, tex_file)

    print()
    print("=" * 70)
    print("Visualization Complete")
    print("=" * 70)


if __name__ == '__main__':
    from config import LOG_DIR
    csv_path = os.path.join(LOG_DIR, 'results.csv')

    if os.path.exists(csv_path):
        visualize_all(csv_path)
    else:
        print(f"Results file not found: {csv_path}")
        print("Run experiment_runner.py first")
