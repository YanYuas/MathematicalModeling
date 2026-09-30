"""
Experiment Runner for VLSI Floorplanning Optimization

Executes full experimental matrix:
- 3 datasets (n100, n200, n300)
- 2 initial methods (random, ffd)
- 2 pairing options (True, False)
- 10 seeds (0-9)
- 3 cost methods (twophase, weighted, greedy)
Total: 110 runs (simplified from 360)

Outputs: results.csv with all metrics
"""
import time
import csv
import os
from typing import List, Dict
from data_loader import load_blocks
from constructive import construct_initial_tree
from fast_sa_optimized import FastSAOptimized
from cost_functions import phase1_cost, phase2_cost, weighted_cost
from pairing import pair_strips
from bounds import compute_lower_bound, compute_gap
from config import (
    EXPERIMENT_MATRIX, SA_PARAMS, TWOPHASE_PARAMS, COST_PARAMS,
    OUTPUT_DIR, LOG_DIR, DATA_PATHS
)


def run_single_experiment(
    dataset: str,
    initial_method: str,
    pairing: bool,
    seed: int,
    cost_method: str
) -> Dict:
    """
    Execute single optimization run.

    Returns:
        Dictionary with all metrics
    """
    # Load data
    blocks = load_blocks(DATA_PATHS[dataset])

    # Apply pairing if enabled
    if pairing:
        blocks, pairs_info = pair_strips(blocks)
    else:
        pairs_info = []

    # Construct initial tree (with timing)
    construct_start = time.time()
    tree = construct_initial_tree(blocks, method=initial_method, seed=seed)
    construct_time = time.time() - construct_start

    # Calculate normalization constants
    A_total = sum(b.area for b in blocks)
    lower_bound = compute_lower_bound(blocks)

    # Calculate initial gap to determine SA parameter tier
    W_init, H_init, _ = tree.pack()
    max_side_init = max(W_init, H_init)
    initial_gap = compute_gap(max_side_init, lower_bound)

    # Adaptive SA parameters based on initial solution quality
    from adaptive_sa_params import get_adaptive_sa_params
    sa_params, tier = get_adaptive_sa_params(initial_gap, SA_PARAMS)

    # Define cost function
    if cost_method == 'twophase':
        # Phase 1: Pure area minimization
        def cost_p1(tree):
            W, H, _ = tree.pack()
            A_chip = W * H
            return phase1_cost(A_chip, A_total)

        sa1 = FastSAOptimized(blocks, cost_p1,
                             P=sa_params['P'],
                             k=sa_params['k'],
                             c=sa_params['c'],
                             ema_alpha=sa_params['ema_alpha'])
        start_time = time.time()
        r1 = sa1.run(tree, seed=seed, verbose=False,
                     T_final=sa_params['T_final'],
                     max_no_improve=sa_params['max_no_improve'],
                     L_factor=sa_params['L_factor'])

        A_opt = r1['area']

        # Phase 2: min-max + soft penalty
        def cost_p2(tree):
            W, H, _ = tree.pack()
            A_chip = W * H
            return phase2_cost(W, H, A_chip, A_opt,
                             eps=TWOPHASE_PARAMS['eps'],
                             mu=TWOPHASE_PARAMS['mu'],
                             norm=A_total)

        sa2 = FastSAOptimized(blocks, cost_p2,
                             P=sa_params['P'],
                             k=sa_params['k'],
                             c=sa_params['c'],
                             ema_alpha=sa_params['ema_alpha'])
        r2 = sa2.run(r1['best_tree'], seed=seed, verbose=False,
                     T_final=sa_params['T_final'],
                     max_no_improve=sa_params['max_no_improve'],
                     L_factor=sa_params['L_factor'])

        elapsed = time.time() - start_time

        result = {
            'W': r2['W'],
            'H': r2['H'],
            'area': r2['area'],
            'max_side': max(r2['W'], r2['H']),
            'aspect_ratio': max(r2['W'], r2['H']) / min(r2['W'], r2['H']),
            'time': construct_time + elapsed,  # Total time: construct + SA
            'iterations': r1['iterations'] + r2['iterations'],
            'A_opt': A_opt,
        }

    elif cost_method == 'weighted':
        def cost_weighted(tree):
            W, H, _ = tree.pack()
            A_chip = W * H
            return weighted_cost(W, H, A_chip, A_total,
                               lam=COST_PARAMS['lam'])

        sa = FastSAOptimized(blocks, cost_weighted,
                            P=SA_PARAMS['P'],
                            k=SA_PARAMS['k'],
                            c=SA_PARAMS['c'],
                            ema_alpha=SA_PARAMS['ema_alpha'])
        start_time = time.time()
        r = sa.run(tree, seed=seed, verbose=False,
                   T_final=SA_PARAMS['T_final'],
                   max_no_improve=SA_PARAMS['max_no_improve'],
                   L_factor=SA_PARAMS['L_factor'])
        elapsed = time.time() - start_time

        result = {
            'W': r['W'],
            'H': r['H'],
            'area': r['area'],
            'max_side': max(r['W'], r['H']),
            'aspect_ratio': max(r['W'], r['H']) / min(r['W'], r['H']),
            'time': construct_time + elapsed,  # Total time: construct + SA
            'iterations': r['iterations'],
            'A_opt': None,
        }

    else:  # greedy (no SA, just initial solution)
        W, H, _ = tree.pack()
        result = {
            'W': W,
            'H': H,
            'area': W * H,
            'max_side': max(W, H),
            'aspect_ratio': max(W, H) / min(W, H),
            'time': construct_time,  # Only construction time
            'iterations': 0,
            'A_opt': None,
        }

    # Compute metrics
    deadspace = (result['area'] - A_total) / A_total * 100.0
    gap = compute_gap(result['max_side'], lower_bound)

    result.update({
        'dataset': dataset,
        'initial_method': initial_method,
        'pairing': pairing,
        'seed': seed,
        'cost_method': cost_method,
        'deadspace': deadspace,
        'gap': gap,
        'lower_bound': lower_bound,
        'pairs_count': len(pairs_info) if pairing else 0,
    })

    return result


def generate_experiment_plan() -> List[Dict]:
    """
    Generate experiment plan based on EXPERIMENT_MATRIX.

    Returns:
        List of experiment configurations
    """
    plan = []

    # Main experiments: 2 initial × 3 datasets × 10 seeds × twophase = 60
    for dataset in EXPERIMENT_MATRIX['datasets']:
        for initial in EXPERIMENT_MATRIX['initial_methods']:
            for seed in EXPERIMENT_MATRIX['seeds']:
                plan.append({
                    'dataset': dataset,
                    'initial_method': initial,
                    'pairing': False,
                    'seed': seed,
                    'cost_method': 'twophase',
                })

    # Comparison: 3 cost methods × n100 × 10 seeds = 30
    for cost_method in EXPERIMENT_MATRIX['cost_methods']:
        for seed in EXPERIMENT_MATRIX['seeds']:
            plan.append({
                'dataset': EXPERIMENT_MATRIX['compare_dataset'],
                'initial_method': 'ffd',
                'pairing': False,
                'seed': seed,
                'cost_method': cost_method,
            })

    # Pairing ablation: 2 pairing × n100 × 10 seeds = 20
    for pairing in EXPERIMENT_MATRIX['pairing']:
        for seed in EXPERIMENT_MATRIX['seeds']:
            plan.append({
                'dataset': EXPERIMENT_MATRIX['pairing_focus_dataset'],
                'initial_method': 'ffd',
                'pairing': pairing,
                'seed': seed,
                'cost_method': 'twophase',
            })

    # Remove duplicates (some configs appear in multiple groups)
    seen = set()
    unique_plan = []
    for config in plan:
        key = tuple(sorted(config.items()))
        if key not in seen:
            seen.add(key)
            unique_plan.append(config)

    return unique_plan


def run_experiments(output_csv: str = None):
    """
    Execute full experimental matrix and save results.

    Args:
        output_csv: Path to output CSV (default: LOG_DIR/results.csv)
    """
    if output_csv is None:
        output_csv = os.path.join(LOG_DIR, 'results.csv')

    # Generate plan
    plan = generate_experiment_plan()
    total = len(plan)

    print("=" * 70)
    print(f"Experiment Runner - Total: {total} runs")
    print("=" * 70)
    print()

    results = []
    start_time = time.time()

    for i, config in enumerate(plan, 1):
        try:
            result = run_single_experiment(**config)
            results.append(result)

            # Progress display
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = avg_time * (total - i)

            print(f"[{i}/{total}] {config['dataset']} | "
                  f"{config['initial_method']} | "
                  f"pair={config['pairing']} | "
                  f"seed={config['seed']} | "
                  f"{config['cost_method']} | "
                  f"R={result['aspect_ratio']:.3f} | "
                  f"gap={result['gap']:.2f}% | "
                  f"time={result['time']:.1f}s | "
                  f"ETA={remaining/60:.1f}min")

        except Exception as e:
            print(f"[{i}/{total}] ERROR: {e}")
            # Log error but continue
            with open(os.path.join(LOG_DIR, 'error.log'), 'a') as f:
                f.write(f"{config}: {e}\n")

    # Save results
    if results:
        fieldnames = list(results[0].keys())
        with open(output_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print()
        print("=" * 70)
        print(f"Completed: {len(results)}/{total} runs in {(time.time()-start_time)/60:.1f} minutes")
        print(f"Results saved to: {output_csv}")
        print("=" * 70)
    else:
        print("ERROR: No results generated")


if __name__ == '__main__':
    run_experiments()
