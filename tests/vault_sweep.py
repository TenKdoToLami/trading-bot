"""
Vault Sweep — Cross-Regime Resilience Audit.

Loads every genome JSON from the vault/, validates format,
then stress-tests each one across rolling 5-year windows
spanning the full data history. Prints a ranked leaderboard
of the top performers by average and median CAGR, with
drawdown and Sharpe statistics.

Usage:
    python tests/vault_sweep.py
    python tests/vault_sweep.py --samples 15   # more samples per bucket
"""

import argparse
import concurrent.futures
import json
import os
import random
import sys
import time

import numpy as np

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from strategies._genome_strategy import GenomeStrategy
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data


# ──────────────────────────────────────────────────────
# Genome Validation
# ──────────────────────────────────────────────────────

REQUIRED_KEYS = {
    'panic_weights', 'base_weights', 'base_thresholds', 'panic_threshold', 'lock_days'
}
INDICATOR_KEYS = {'sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr'}
THRESHOLD_KEYS = {'tier_1x', 'tier_2x', 'tier_3x'}


def validate_genome(genome: dict) -> bool:
    """Check if a dict has the correct genome structure."""
    if not REQUIRED_KEYS.issubset(genome.keys()):
        return False
    if not INDICATOR_KEYS.issubset(genome['panic_weights'].keys()):
        return False
    if not INDICATOR_KEYS.issubset(genome['base_weights'].keys()):
        return False
    if not THRESHOLD_KEYS.issubset(genome['base_thresholds'].keys()):
        return False
    if not isinstance(genome['panic_threshold'], (int, float)):
        return False
    if not isinstance(genome['lock_days'], (int, float)):
        return False
    return True


def load_vault(vault_dir: str) -> list:
    """Load and validate all genome JSONs from the vault directory."""
    genomes = []
    for filename in sorted(os.listdir(vault_dir)):
        if not filename.endswith('.json'):
            continue
        filepath = os.path.join(vault_dir, filename)
        try:
            with open(filepath, 'r') as f:
                genome = json.load(f)
            if validate_genome(genome):
                genomes.append((filename, genome))
            else:
                print(f"  SKIP (invalid format): {filename}")
        except (json.JSONDecodeError, Exception) as e:
            print(f"  SKIP (parse error): {filename} — {e}")
    return genomes


# ──────────────────────────────────────────────────────
# Simulation
# ──────────────────────────────────────────────────────

def evaluate_genome_on_slice(genome, price_data_slice, dates_slice):
    """Run a single genome on a data slice and return metrics."""
    res = _execute_simulation(
        strategy_type=GenomeStrategy,
        price_data_list=price_data_slice,
        dates=dates_slice,
        strategy_kwargs={'genome': genome}
    )
    return res['metrics']


def run_sweep(genomes, data, samples_per_bucket=10):
    """
    Run every genome across rolling 5-year buckets.
    Returns: {filename: {'metrics_list': [...], 'name': str}}
    """
    total_days = len(data)
    price_data_list = data[['open', 'high', 'low', 'close', 'volume']].to_dict('records')
    dates = data.index

    # Define 5-year buckets
    buckets = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, 30)]

    # Pre-generate random periods for each bucket (shared across all genomes)
    all_periods = []
    bucket_labels = []
    for lo_yr, hi_yr in buckets:
        lo_days = lo_yr * 252
        hi_days = hi_yr * 252

        if lo_days >= total_days - 50:
            continue

        for _ in range(samples_per_bucket):
            actual_hi = min(hi_days, total_days - 50)
            actual_lo = max(lo_days, 252)
            if actual_lo >= actual_hi:
                actual_lo = actual_hi - 1
            duration = random.randint(actual_lo, actual_hi)
            max_start = total_days - duration - 1
            start = random.randint(0, max(0, max_start))
            all_periods.append((start, start + duration))
            bucket_labels.append(f"{lo_yr}-{hi_yr}yr")

    print(f"\n  Total test periods: {len(all_periods)}")
    print(f"  Genomes to evaluate: {len(genomes)}")
    print(f"  Total simulations: {len(all_periods) * len(genomes)}")

    # Build all tasks: (genome_idx, period_idx, genome, slice, dates)
    results = {name: [] for name, _ in genomes}

    for period_idx, (start_idx, end_idx) in enumerate(all_periods):
        p_slice = price_data_list[start_idx:end_idx]
        d_slice = dates[start_idx:end_idx]
        label = bucket_labels[period_idx]

        # Run all genomes on this period in parallel
        tasks = []
        task_names = []
        for name, genome in genomes:
            tasks.append((genome, p_slice, d_slice))
            task_names.append(name)

        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = {
                executor.submit(evaluate_genome_on_slice, *t): task_names[i]
                for i, t in enumerate(tasks)
            }
            for future in concurrent.futures.as_completed(futures):
                fname = futures[future]
                try:
                    metrics = future.result()
                    metrics['bucket'] = label
                    results[fname].append(metrics)
                except Exception as e:
                    print(f"  ERROR: {fname} on period {period_idx}: {e}")

        # Progress indicator
        pct = (period_idx + 1) / len(all_periods) * 100
        print(f"\r  Progress: {pct:.0f}% ({period_idx + 1}/{len(all_periods)} periods)", end="", flush=True)

    print()  # newline after progress
    return results


# ──────────────────────────────────────────────────────
# Reporting
# ──────────────────────────────────────────────────────

def print_leaderboard(results: dict, top_n: int = 3):
    """Print the top N genomes ranked by average CAGR."""

    # Aggregate metrics per genome
    leaderboard = []
    for filename, metrics_list in results.items():
        if not metrics_list:
            continue

        cagrs = [m['cagr'] * 100 for m in metrics_list]
        sharpes = [m['sharpe'] for m in metrics_list]
        max_dds = [m['max_dd'] * 100 for m in metrics_list]
        vols = [m['volatility'] * 100 for m in metrics_list]

        leaderboard.append({
            'name': filename,
            'avg_cagr': np.mean(cagrs),
            'med_cagr': np.median(cagrs),
            'max_cagr': np.max(cagrs),
            'min_cagr': np.min(cagrs),
            'avg_sharpe': np.mean(sharpes),
            'med_sharpe': np.median(sharpes),
            'avg_dd': np.mean(max_dds),
            'med_dd': np.median(max_dds),
            'worst_dd': np.min(max_dds),
            'avg_vol': np.mean(vols),
            'n_periods': len(metrics_list)
        })

    # Sort by average CAGR descending
    leaderboard.sort(key=lambda x: x['avg_cagr'], reverse=True)

    # Full Leaderboard
    w = 130
    print(f"\n{'=' * w}")
    print(f"  VAULT SWEEP — FULL LEADERBOARD (Ranked by Avg CAGR)")
    print(f"{'=' * w}")
    print(f"  {'#':<3} {'Genome':<42} | {'AvgCAGR':>8} | {'MedCAGR':>8} | {'AvgShp':>7} | {'AvgDD':>8} | {'WorstDD':>8} | {'AvgVol':>7} | {'N':>3}")
    print(f"  {'-' * (w - 4)}")

    for i, row in enumerate(leaderboard):
        marker = " ★" if i < top_n else "  "
        print(
            f"{marker}{i+1:<3} {row['name']:<42} | "
            f"{row['avg_cagr']:>7.2f}% | "
            f"{row['med_cagr']:>7.2f}% | "
            f"{row['avg_sharpe']:>7.2f} | "
            f"{row['avg_dd']:>7.1f}% | "
            f"{row['worst_dd']:>7.1f}% | "
            f"{row['avg_vol']:>6.1f}% | "
            f"{row['n_periods']:>3}"
        )
    print(f"{'=' * w}")

    # Detailed Top N
    print(f"\n{'#' * w}")
    print(f"  TOP {top_n} — DETAILED BREAKDOWN")
    print(f"{'#' * w}")

    for i, row in enumerate(leaderboard[:top_n]):
        print(f"\n  🏆 #{i+1}: {row['name']}")
        print(f"  {'─' * 60}")
        print(f"  {'CAGR':<20} | Avg: {row['avg_cagr']:>7.2f}% | Med: {row['med_cagr']:>7.2f}% | Max: {row['max_cagr']:>7.2f}% | Min: {row['min_cagr']:>7.2f}%")
        print(f"  {'Sharpe Ratio':<20} | Avg: {row['avg_sharpe']:>7.2f}  | Med: {row['med_sharpe']:>7.2f}")
        print(f"  {'Max Drawdown':<20} | Avg: {row['avg_dd']:>7.1f}% | Med: {row['med_dd']:>7.1f}% | Worst: {row['worst_dd']:>7.1f}%")
        print(f"  {'Volatility':<20} | Avg: {row['avg_vol']:>7.1f}%")
        print(f"  {'Periods Tested':<20} | {row['n_periods']}")

    print(f"\n{'#' * w}\n")


# ──────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vault Sweep — Cross-Regime Resilience Audit")
    parser.add_argument("--samples", type=int, default=10, help="Samples per 5-year bucket (default 10)")
    parser.add_argument("--top", type=int, default=3, help="Top N genomes to highlight (default 3)")
    parser.add_argument("--vault", type=str, default="vault", help="Path to vault directory (default: vault)")
    args = parser.parse_args()

    print("=" * 60)
    print("  VAULT SWEEP — Cross-Regime Resilience Audit")
    print("=" * 60)

    # 1. Load vault
    vault_dir = os.path.join(os.path.dirname(__file__), '..', args.vault)
    vault_dir = os.path.abspath(vault_dir)
    print(f"\n  Scanning vault: {vault_dir}")
    genomes = load_vault(vault_dir)
    print(f"  Valid genomes found: {len(genomes)}")

    if not genomes:
        print("  No valid genomes found. Exiting.")
        sys.exit(1)

    # 2. Load data
    print("\n  Loading market data...")
    data = load_spy_data("1993-01-01", force_refresh=False)
    total_years = len(data) / 252
    print(f"  Data span: {len(data)} trading days ({total_years:.1f} years)")

    # 3. Run sweep
    start_time = time.time()
    results = run_sweep(genomes, data, samples_per_bucket=args.samples)
    elapsed = time.time() - start_time
    print(f"\n  Sweep completed in {elapsed:.1f}s")

    # 4. Print leaderboard
    print_leaderboard(results, top_n=args.top)
