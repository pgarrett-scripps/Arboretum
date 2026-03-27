#!/usr/bin/env python
"""
Arboretum GitHub Pages Site Generator

Reads benchmark results and generates a static HTML page with charts and tables.
"""

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from statistics import mean as stat_mean


def load_results(results_dir):
    json_path = os.path.join(results_dir, 'benchmark_results.json')
    with open(json_path) as f:
        return json.load(f)


def build_summary_table(summary):
    """Build an HTML table summarizing average performance per tree type."""
    metrics = [
        ('add_time_per_op', 'Add (us)'),
        ('search_time_per_op', 'Search (us)'),
        ('remove_time_per_op', 'Remove (us)'),
        ('save_time_per_op', 'Save (us)'),
        ('load_time_per_op', 'Load (us)'),
        ('memory_mb', 'Memory (MB)'),
    ]

    tree_groups = {}
    for row in summary:
        tree_groups.setdefault(row['tree_type'], []).append(row)

    rows_html = []
    for tt in sorted(tree_groups.keys()):
        group = tree_groups[tt]
        cells = [f'<td class="tree-name">{tt}</td>']
        for m_key, _ in metrics:
            scale = 1e6 if 'time' in m_key else 1.0
            avg = stat_mean([r[f'{m_key}_mean'] for r in group]) * scale
            std = stat_mean([r[f'{m_key}_std'] for r in group]) * scale
            if 'time' in m_key:
                cells.append(f'<td>{avg:.2f} <span class="std">&plusmn; {std:.2f}</span></td>')
            else:
                cells.append(f'<td>{avg:.2f} <span class="std">&plusmn; {std:.2f}</span></td>')
        rows_html.append(f'    <tr>{"".join(cells)}</tr>')

    header_cells = '<th>Tree Type</th>' + ''.join(f'<th>{label}</th>' for _, label in metrics)
    nl = '\n'
    return f"""<table>
  <thead><tr>{header_cells}</tr></thead>
  <tbody>
{nl.join(rows_html)}
  </tbody>
</table>"""


def generate_html(summary, config, docs_dir):
    """Generate the full index.html page."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    table_html = build_summary_table(summary)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Arboretum - Data Structure Benchmarks</title>
  <style>
    :root {{
      --bg: #0d1117;
      --surface: #161b22;
      --border: #30363d;
      --text: #c9d1d9;
      --text-muted: #8b949e;
      --accent: #58a6ff;
      --green: #3fb950;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding: 2rem;
      max-width: 1200px;
      margin: 0 auto;
    }}
    h1 {{
      font-size: 2rem;
      margin-bottom: 0.5rem;
      color: #f0f6fc;
    }}
    h1 span {{ color: var(--green); }}
    .subtitle {{
      color: var(--text-muted);
      margin-bottom: 2rem;
      font-size: 1.1rem;
    }}
    .meta {{
      display: flex;
      gap: 2rem;
      margin-bottom: 2rem;
      flex-wrap: wrap;
    }}
    .meta-item {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.75rem 1.25rem;
      font-size: 0.9rem;
    }}
    .meta-item strong {{ color: var(--accent); }}
    .chart-container {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem;
      margin-bottom: 2rem;
    }}
    .chart-container img {{
      width: 100%;
      height: auto;
      border-radius: 4px;
    }}
    .chart-container h2 {{
      font-size: 1.2rem;
      margin-bottom: 0.75rem;
      color: #f0f6fc;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 2rem;
      font-size: 0.9rem;
    }}
    th, td {{
      padding: 0.6rem 0.8rem;
      text-align: right;
      border-bottom: 1px solid var(--border);
    }}
    th {{
      background: var(--surface);
      color: var(--accent);
      font-weight: 600;
      position: sticky;
      top: 0;
    }}
    td.tree-name {{
      text-align: left;
      font-weight: 600;
      color: var(--green);
    }}
    th:first-child {{ text-align: left; }}
    tr:hover td {{ background: rgba(88, 166, 255, 0.05); }}
    .std {{ color: var(--text-muted); font-size: 0.8rem; }}
    footer {{
      color: var(--text-muted);
      font-size: 0.85rem;
      margin-top: 3rem;
      padding-top: 1rem;
      border-top: 1px solid var(--border);
    }}
    footer a {{ color: var(--accent); text-decoration: none; }}
    footer a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <h1><span>Arboretum</span> Data Structure Benchmarks</h1>
  <p class="subtitle">
    Comparing data structure implementations for storing and querying
    records with range-based and multi-dimensional filtering.
  </p>

  <div class="meta">
    <div class="meta-item">Last updated: <strong>{now}</strong></div>
    <div class="meta-item">Records per point: <strong>{config.get('num_records', config.get('num_psms', 'N/A')):,}</strong></div>
    <div class="meta-item">Size points: <strong>{config.get('num_points', 'N/A')}</strong></div>
    <div class="meta-item">Iterations: <strong>{config.get('num_iterations', 'N/A')}</strong></div>
    <div class="meta-item">Query tolerances: <strong>ppm={config.get('ppm', 50)}, rt_offset={config.get('rt_offset', 100)}, ook0_tol={config.get('ook0_tol', 0.05)}</strong></div>
  </div>

  <div class="chart-container">
    <h2>Scaling Performance</h2>
    <img src="benchmark_scaling.png" alt="Benchmark scaling plot showing time per operation vs tree size">
  </div>

  <div class="chart-container">
    <h2>Average Performance Comparison</h2>
    <img src="benchmark_summary.png" alt="Bar chart comparing average operation times across tree types">
  </div>

  <div class="chart-container">
    <h2>Summary Table</h2>
    <p style="color: var(--text-muted); margin-bottom: 1rem; font-size: 0.9rem;">
      Average across all size points. Times in microseconds. &plusmn; shows standard deviation.
    </p>
    {table_html}
  </div>

  <footer>
    <p>
      Generated by <a href="https://github.com/pgarrett-scripps/Arboretum">Arboretum</a> benchmark suite.
      Data structures benchmarked: sorted lists, hash tables, binary trees, AVL trees, red-black trees, and more.
    </p>
  </footer>
</body>
</html>"""
    return html


def main():
    results_dir = sys.argv[1] if len(sys.argv) > 1 else 'benchmarks/results'
    docs_dir = sys.argv[2] if len(sys.argv) > 2 else 'docs'

    os.makedirs(docs_dir, exist_ok=True)

    data = load_results(results_dir)
    summary = data['summary']
    config = data['config']

    # Copy chart PNGs to docs
    for fname in ['benchmark_scaling.png', 'benchmark_summary.png']:
        src = os.path.join(results_dir, fname)
        dst = os.path.join(docs_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Copied {fname} to {docs_dir}/")

    # Generate HTML
    html = generate_html(summary, config, docs_dir)
    html_path = os.path.join(docs_dir, 'index.html')
    with open(html_path, 'w') as f:
        f.write(html)
    print(f"Generated {html_path}")

    # Create .nojekyll
    nojekyll_path = os.path.join(docs_dir, '.nojekyll')
    if not os.path.exists(nojekyll_path):
        open(nojekyll_path, 'w').close()
        print(f"Created {nojekyll_path}")


if __name__ == '__main__':
    main()
