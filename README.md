# Arboretum

[![Benchmarks](https://github.com/pgarrett-scripps/Arboretum/actions/workflows/benchmarks.yml/badge.svg)](https://github.com/pgarrett-scripps/Arboretum/actions/workflows/benchmarks.yml)

**[View Benchmark Results](https://pgarrett-scripps.github.io/Arboretum/)**

Arboretum is a Python package for benchmarking data structure implementations for storing and querying records with range-based and multi-dimensional filtering. Originally designed for Peptide Sequence Matches (PSMs) from mass spectrometry, the benchmark suite generalizes to any interval/range query workload.

## Tree Types

| Type | Description |
|------|-------------|
| `SORTED_LIST` | SortedDict-backed sorted list with binary search range queries |
| `HASHTABLE` | Hash table with configurable decimal precision (2, 3, or 4) |
| `BINARY` | Binary search tree (1D on m/z) |
| `AVL` | Self-balancing AVL tree |
| `RB` | Red-black tree |
| `FAST_BINARY` / `FAST_AVL` / `FAST_RB` | C-optimized variants of the above |
| `LIST` | Simple unsorted list (baseline) |
| `INTERVAL` | Interval tree (Python `intervaltree` library) |

## Quick Start

```python
from arborist import PSMArborist
from forest import TreeType

arb = PSMArborist(TreeType.SORTED_LIST)
arb.add(charge=2, mz=500.25, rt=1200.0, ook0=0.85, data={"sequence": "PEPTIDE"})
results = arb.search(charge=2, mz=500.25, rt=1200.0, ook0=0.85,
                     ppm=50, rt_offset=100, ook0_tolerance=0.05)
```

## Benchmarks

Arboretum includes a comprehensive benchmark suite that compares all tree implementations across add, search, remove, save, and load operations with memory profiling.

**[View latest results on GitHub Pages](https://pgarrett-scripps.github.io/Arboretum/)**

### Run locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run benchmarks (small, ~2 min)
python benchmarks/run_benchmarks.py --num-records 5000 --num-points 5 --num-iterations 2

# Generate plots
python benchmarks/plot_results.py benchmarks/results

# Generate GitHub Pages site
python benchmarks/generate_site.py benchmarks/results docs
```

Results are saved to `benchmarks/results/` as JSON and CSV, with PNG charts.

### CI/CD

A GitHub Actions workflow runs benchmarks weekly and on push, automatically deploying results to GitHub Pages.

## Installation

```bash
pip install -e .
```

## Authors

- Ty Garrett (pgarrett@scripps.edu) — The Scripps Research Institute
- Jeff Lane (jlane@scripps.edu) — The Scripps Research Institute

## License

MIT
