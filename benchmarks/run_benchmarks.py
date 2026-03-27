#!/usr/bin/env python
"""
Arboretum Benchmark Runner

Benchmarks all working data structure implementations with multiple iterations,
memory profiling, and structured output (JSON + CSV).
"""

import argparse
import csv
import json
import os
import sys
import tempfile
import time
import tracemalloc
from statistics import mean, stdev

# Add the arboretum source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'arboretum'))

from benchmark_utils import generate_psm_dataset
from boundary import get_mz_bounds, get_rt_bounds, get_ook0_bounds
from forest import TreeType, psm_tree_constructor

# Tree types that are fully implemented and benchmarkable
BENCHMARKABLE_TREES = [
    TreeType.SORTED_LIST,
    TreeType.HASHTABLE,
    TreeType.HASHTABLE_MED,
    TreeType.HASHTABLE_LARGE,
    TreeType.BINARY,
    TreeType.AVL,
    TreeType.RB,
    TreeType.FAST_BINARY,
    TreeType.FAST_AVL,
    TreeType.FAST_RB,
    TreeType.LIST,
    TreeType.INTERVAL,
]

# Search tolerance parameters
PPM = 50
RT_OFFSET = 100
OOK0_TOL = 0.05


def benchmark_tree(tree_type, num_records, num_points, num_iterations, ops, seed):
    """Run all benchmarks for a single tree type."""
    print(f"\n{'='*60}")
    print(f"  Benchmarking: {tree_type.name}")
    print(f"{'='*60}")

    results = []

    for point_idx in range(num_points):
        target_size = (point_idx + 1) * num_records
        print(f"  Size point {point_idx + 1}/{num_points}: {target_size:,} records")

        for iteration in range(num_iterations):
            tree = psm_tree_constructor(tree_type)
            point_seed = seed + point_idx * 1000 + iteration

            # Pre-generate all data needed for this size point
            all_psms = generate_psm_dataset(target_size, seed=point_seed)
            test_psms = all_psms[:ops]
            remaining_psms = all_psms[ops:]

            # --- Warmup (first iteration only) ---
            if point_idx == 0 and iteration == 0:
                warmup_tree = psm_tree_constructor(tree_type)
                warmup_psms = generate_psm_dataset(min(500, ops), seed=seed + 999999)
                for psm in warmup_psms:
                    warmup_tree.add(psm)
                for psm in warmup_psms[:min(100, len(warmup_psms))]:
                    warmup_tree._search(
                        get_mz_bounds(psm.mz, PPM),
                        get_rt_bounds(psm.rt, RT_OFFSET),
                        get_ook0_bounds(psm.ook0, OOK0_TOL)
                    )
                del warmup_tree, warmup_psms

            # Start memory tracking before adding to tree
            tracemalloc.start()
            mem_before = tracemalloc.get_traced_memory()[0]

            # --- Add benchmark ---
            add_start = time.perf_counter()
            for psm in test_psms:
                tree.add(psm)
            add_time = time.perf_counter() - add_start

            # Add remaining PSMs (untimed) to reach target size
            for psm in remaining_psms:
                tree.add(psm)

            # --- Memory snapshot ---
            mem_after, mem_peak = tracemalloc.get_traced_memory()
            memory_bytes = mem_after - mem_before
            tracemalloc.stop()

            # --- Search benchmark ---
            search_start = time.perf_counter()
            for psm in test_psms:
                tree._search(
                    get_mz_bounds(psm.mz, PPM),
                    get_rt_bounds(psm.rt, RT_OFFSET),
                    get_ook0_bounds(psm.ook0, OOK0_TOL)
                )
            search_time = time.perf_counter() - search_start

            # --- Remove benchmark ---
            remove_start = time.perf_counter()
            for psm in test_psms:
                tree.remove(psm)
            remove_time = time.perf_counter() - remove_start

            # Re-add removed PSMs for save/load
            for psm in test_psms:
                tree.add(psm)

            # --- Save benchmark ---
            tmp_file = tempfile.NamedTemporaryFile(
                mode='w', suffix='.txt', delete=False
            )
            tmp_path = tmp_file.name
            tmp_file.close()
            try:
                save_start = time.perf_counter()
                tree.save(tmp_path)
                save_time = time.perf_counter() - save_start

                # --- Load benchmark ---
                tree.clear()
                load_start = time.perf_counter()
                tree.load(tmp_path)
                load_time = time.perf_counter() - load_start
            finally:
                os.unlink(tmp_path)

            results.append({
                'tree_type': tree_type.name,
                'target_size': target_size,
                'iteration': iteration + 1,
                'ops': ops,
                'add_time': add_time,
                'add_time_per_op': add_time / ops,
                'search_time': search_time,
                'search_time_per_op': search_time / ops,
                'remove_time': remove_time,
                'remove_time_per_op': remove_time / ops,
                'save_time': save_time,
                'save_time_per_op': save_time / target_size,
                'load_time': load_time,
                'load_time_per_op': load_time / target_size,
                'memory_mb': memory_bytes / (1024 * 1024),
            })

            del tree

    return results


def compute_summary(all_results):
    """Compute mean/std statistics grouped by tree_type and target_size."""
    groups = {}
    for r in all_results:
        key = (r['tree_type'], r['target_size'])
        groups.setdefault(key, []).append(r)

    summary = []
    metrics = [
        'add_time_per_op', 'search_time_per_op', 'remove_time_per_op',
        'save_time_per_op', 'load_time_per_op', 'memory_mb'
    ]
    for (tree_type, target_size), rows in sorted(groups.items()):
        entry = {'tree_type': tree_type, 'target_size': target_size}
        for m in metrics:
            values = [r[m] for r in rows]
            entry[f'{m}_mean'] = mean(values)
            entry[f'{m}_std'] = stdev(values) if len(values) > 1 else 0.0
            entry[f'{m}_min'] = min(values)
            entry[f'{m}_max'] = max(values)
        summary.append(entry)
    return summary


def main():
    parser = argparse.ArgumentParser(description='Arboretum Benchmark Runner')
    parser.add_argument('--num-records', type=int, default=10000,
                        help='Records per size point (default: 10000)')
    parser.add_argument('--num-points', type=int, default=10,
                        help='Number of size points (default: 10)')
    parser.add_argument('--num-iterations', type=int, default=3,
                        help='Iterations per measurement (default: 3)')
    parser.add_argument('--ops', type=int, default=1000,
                        help='Operations per measurement (default: 1000)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed (default: 42)')
    parser.add_argument('--output-dir', type=str, default='benchmarks/results',
                        help='Output directory (default: benchmarks/results)')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("Arboretum Benchmark Runner")
    print(f"  Records per point: {args.num_records:,}")
    print(f"  Size points: {args.num_points}")
    print(f"  Iterations: {args.num_iterations}")
    print(f"  Ops per measurement: {args.ops:,}")
    print(f"  Seed: {args.seed}")
    print(f"  Tree types: {len(BENCHMARKABLE_TREES)}")

    all_results = []
    for tree_type in BENCHMARKABLE_TREES:
        try:
            results = benchmark_tree(
                tree_type, args.num_records, args.num_points,
                args.num_iterations, args.ops, args.seed
            )
            all_results.extend(results)
        except Exception as e:
            print(f"  ERROR benchmarking {tree_type.name}: {e}")
            continue

    if not all_results:
        print("No benchmark results collected!")
        sys.exit(1)

    # Compute summary statistics
    summary = compute_summary(all_results)

    # --- Write JSON ---
    output = {
        'config': {
            'num_records': args.num_records,
            'num_points': args.num_points,
            'num_iterations': args.num_iterations,
            'ops': args.ops,
            'seed': args.seed,
            'ppm': PPM,
            'rt_offset': RT_OFFSET,
            'ook0_tol': OOK0_TOL,
        },
        'raw_results': all_results,
        'summary': summary,
    }
    json_path = os.path.join(args.output_dir, 'benchmark_results.json')
    with open(json_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nJSON results written to: {json_path}")

    # --- Write CSV ---
    csv_path = os.path.join(args.output_dir, 'benchmark_results.csv')
    fieldnames = list(all_results[0].keys())
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    print(f"CSV results written to: {csv_path}")

    # --- Console summary ---
    print(f"\n{'='*80}")
    print("SUMMARY (mean time per operation in microseconds)")
    print(f"{'='*80}")
    header = f"{'Tree Type':<18} {'Add':>10} {'Search':>10} {'Remove':>10} {'Save':>10} {'Load':>10} {'Mem(MB)':>10}"
    print(header)
    print('-' * len(header))

    # Aggregate across all sizes for a quick overview
    tree_groups = {}
    for s in summary:
        tree_groups.setdefault(s['tree_type'], []).append(s)

    for tree_type, rows in sorted(tree_groups.items()):
        avg_add = mean([r['add_time_per_op_mean'] for r in rows]) * 1e6
        avg_search = mean([r['search_time_per_op_mean'] for r in rows]) * 1e6
        avg_remove = mean([r['remove_time_per_op_mean'] for r in rows]) * 1e6
        avg_save = mean([r['save_time_per_op_mean'] for r in rows]) * 1e6
        avg_load = mean([r['load_time_per_op_mean'] for r in rows]) * 1e6
        avg_mem = mean([r['memory_mb_mean'] for r in rows])
        print(f"{tree_type:<18} {avg_add:>10.2f} {avg_search:>10.2f} {avg_remove:>10.2f} {avg_save:>10.2f} {avg_load:>10.2f} {avg_mem:>10.2f}")

    print(f"\nDone! Results in {args.output_dir}/")


if __name__ == '__main__':
    main()
