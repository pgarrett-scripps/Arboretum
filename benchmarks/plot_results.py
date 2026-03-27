#!/usr/bin/env python
"""
Arboretum Benchmark Plotter

Reads benchmark_results.json and generates publication-quality charts.
"""

import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def load_results(results_dir):
    json_path = os.path.join(results_dir, 'benchmark_results.json')
    with open(json_path) as f:
        return json.load(f)


def plot_scaling(summary, results_dir):
    """Generate a 2x3 panel figure showing scaling behavior for each metric."""
    metrics = [
        ('add_time_per_op', 'Add Time per Op', 'Time (us)'),
        ('search_time_per_op', 'Search Time per Op', 'Time (us)'),
        ('remove_time_per_op', 'Remove Time per Op', 'Time (us)'),
        ('save_time_per_op', 'Save Time per Op', 'Time (us)'),
        ('load_time_per_op', 'Load Time per Op', 'Time (us)'),
        ('memory_mb', 'Peak Memory', 'Memory (MB)'),
    ]

    # Group summary by tree type
    tree_data = {}
    for row in summary:
        tt = row['tree_type']
        tree_data.setdefault(tt, {'sizes': [], 'metrics': {}})
        tree_data[tt]['sizes'].append(row['target_size'])
        for m, _, _ in metrics:
            tree_data[tt]['metrics'].setdefault(m, {'mean': [], 'std': []})
            scale = 1e6 if 'time' in m else 1.0
            tree_data[tt]['metrics'][m]['mean'].append(row[f'{m}_mean'] * scale)
            tree_data[tt]['metrics'][m]['std'].append(row[f'{m}_std'] * scale)

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Arboretum PSM Tree Benchmark Results', fontsize=16, fontweight='bold')
    axes = axes.flatten()

    colors = plt.cm.tab10(np.linspace(0, 1, len(tree_data)))

    for idx, (metric_key, title, ylabel) in enumerate(metrics):
        ax = axes[idx]
        for color_idx, (tt, data) in enumerate(sorted(tree_data.items())):
            sizes = data['sizes']
            means = data['metrics'][metric_key]['mean']
            stds = data['metrics'][metric_key]['std']
            color = colors[color_idx]
            ax.plot(sizes, means, marker='o', markersize=3, label=tt,
                    color=color, linewidth=1.5)
            ax.fill_between(
                sizes,
                [m - s for m, s in zip(means, stds)],
                [m + s for m, s in zip(means, stds)],
                alpha=0.15, color=color
            )
        ax.set_title(title, fontsize=12)
        ax.set_xlabel('Tree Size (PSMs)')
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)

    # Single legend below the figure
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=min(6, len(labels)),
               bbox_to_anchor=(0.5, -0.02), fontsize=9)

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    out_path = os.path.join(results_dir, 'benchmark_scaling.png')
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Scaling plot saved to: {out_path}")


def plot_summary_bars(summary, results_dir):
    """Generate a summary bar chart of average performance across all sizes."""
    from statistics import mean as stat_mean

    metrics = [
        ('add_time_per_op', 'Add'),
        ('search_time_per_op', 'Search'),
        ('remove_time_per_op', 'Remove'),
        ('save_time_per_op', 'Save'),
        ('load_time_per_op', 'Load'),
    ]

    # Compute average across all sizes for each tree type
    tree_groups = {}
    for row in summary:
        tree_groups.setdefault(row['tree_type'], []).append(row)

    tree_names = sorted(tree_groups.keys())
    metric_avgs = {}
    for m_key, m_label in metrics:
        metric_avgs[m_label] = []
        for tt in tree_names:
            rows = tree_groups[tt]
            avg = stat_mean([r[f'{m_key}_mean'] for r in rows]) * 1e6
            metric_avgs[m_label].append(avg)

    x = np.arange(len(tree_names))
    width = 0.15
    n_metrics = len(metrics)

    fig, ax = plt.subplots(figsize=(14, 7))
    for i, (_, m_label) in enumerate(metrics):
        offset = (i - n_metrics / 2 + 0.5) * width
        ax.bar(x + offset, metric_avgs[m_label], width, label=m_label)

    ax.set_xlabel('Tree Type')
    ax.set_ylabel('Average Time per Operation (us)')
    ax.set_title('Average Performance by Tree Type', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(tree_names, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()
    out_path = os.path.join(results_dir, 'benchmark_summary.png')
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Summary bar chart saved to: {out_path}")


def main():
    results_dir = sys.argv[1] if len(sys.argv) > 1 else 'benchmarks/results'
    data = load_results(results_dir)
    summary = data['summary']

    plot_scaling(summary, results_dir)
    plot_summary_bars(summary, results_dir)
    print("All plots generated.")


if __name__ == '__main__':
    main()
