"""
Vault Sweep — Cross-Regime Resilience Audit.
Supports V1, V2, V3, V4, V5 (Sniper), and V6 (Balancer).
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

from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data

# Strategy Imports
from strategies._genome_strategy import GenomeStrategy
from strategies.genome_v2_multi import GenomeV2Strategy
from strategies.genome_v3_precision import GenomeV3Strategy
from strategies.genome_v4_chameleon import ChameleonV4
from strategies.genome_v5_sniper import GenomeV5Sniper
from strategies.genome_v6_balancer import GenomeV6
from strategies.genome_v7_deep import GenomeV7Deep
from strategies.genome_v7_deep_binary import GenomeV7DeepBinary
from strategies.genome_v7_deep_fluid import GenomeV7DeepFluid

# ──────────────────────────────────────────────────────
# Genome Identification
# ──────────────────────────────────────────────────────

V1_KEYS = {'panic_weights', 'base_weights', 'base_thresholds', 'panic_threshold', 'lock_days'}
V2_BRAINS = {'panic', '3x', '2x', '1x'}
V3_BRAINS = {'panic', 'bull'}
V4_KEYS = {'vix_ema', 'vol_stretch', 'mom_period'}
V5_KEYS = {'sniper'}
V6_BRAINS = {'cash', '1x', '2x', '3x'}

def get_genome_version(genome: dict) -> int:
    """Detect genome version based on keys."""
    if 'layers' in genome:
        return 7
    if V6_BRAINS.issubset(genome.get('brains', {}).keys()):
        return 6
    if V5_KEYS.issubset(genome.keys()):
        return 5
    if V4_KEYS.issubset(genome.keys()):
        return 4
    if V3_BRAINS.issubset(genome.keys()) and all('lookbacks' in genome[b] for b in V3_BRAINS):
        return 3
    if V2_BRAINS.issubset(genome.keys()):
        return 2
    if V1_KEYS.issubset(genome.keys()):
        return 1
    return 0

def validate_genome(genome: dict) -> bool:
    """Check if a dict has a known genome structure."""
    ver = get_genome_version(genome)
    if ver == 7:
        return 'layers' in genome and len(genome['layers']) > 0
    if ver == 6:
        return 'brains' in genome and all('w' in genome['brains'][b] for b in V6_BRAINS)
    if ver == 5:
        return 'sniper' in genome and 'w' in genome['sniper'] and 't_low' in genome['sniper']
    if ver == 4:
        return all(k in genome for k in V4_KEYS)
    if ver == 3:
        return all('w' in genome[b] and 't' in genome[b] and 'lookbacks' in genome[b] for b in V3_BRAINS)
    if ver == 2:
        return all('w' in genome[b] and 't' in genome[b] for b in V2_BRAINS)
    if ver == 1:
        return True
    return False

def evaluate_genome_on_slice(genome, price_data_slice, dates_slice):
    """Run simulation on a slice using the correct strategy class."""
    ver = get_genome_version(genome)
    if ver == 7:
        # Check sub-version for V7
        v = genome.get('version', 7.0)
        if v == 7.2: strat_type = GenomeV7DeepFluid
        elif v == 7.1: strat_type = GenomeV7DeepBinary
        else: strat_type = GenomeV7Deep
    elif ver == 6: strat_type = GenomeV6
    elif ver == 5: strat_type = GenomeV5Sniper
    elif ver == 4: strat_type = ChameleonV4
    elif ver == 3: strat_type = GenomeV3Strategy
    elif ver == 2: strat_type = GenomeV2Strategy
    else: strat_type = GenomeStrategy
    
    res = _execute_simulation(
        strategy_type=strat_type,
        price_data_list=price_data_slice,
        dates=dates_slice,
        strategy_kwargs={'genome': genome}
    )
    return res['metrics']

# ──────────────────────────────────────────────────────
# Main Logic
# ──────────────────────────────────────────────────────

def run_sweep(genomes, data, samples_per_bucket=10):
    price_data_list = data[['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve']].to_dict('records')
    dates = data.index
    total_days = len(data)

    buckets = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, 30)]
    all_periods = []
    bucket_labels = []
    for lo_yr, hi_yr in buckets:
        lo_days, hi_days = lo_yr * 252, hi_yr * 252
        if lo_days >= total_days - 50: continue
        for _ in range(samples_per_bucket):
            actual_hi = min(hi_days, total_days - 50)
            actual_lo = max(lo_days, 252)
            duration = random.randint(actual_lo, actual_hi) if actual_lo < actual_hi else actual_lo
            max_start = total_days - duration - 1
            start = random.randint(0, max(0, max_start))
            all_periods.append((start, start + duration))
            bucket_labels.append(f"{lo_yr}-{hi_yr}yr")

    print(f"\n  Testing {len(genomes)} genomes across {len(all_periods)} periods...")
    results = {name: [] for name, _ in genomes}

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for period_idx, (start_idx, end_idx) in enumerate(all_periods):
            p_slice = price_data_list[start_idx:end_idx]
            d_slice = dates[start_idx:end_idx]
            label = bucket_labels[period_idx]

            futures = {
                executor.submit(evaluate_genome_on_slice, g, p_slice, d_slice): name
                for name, g in genomes
            }
            for future in concurrent.futures.as_completed(futures):
                fname = futures[future]
                try:
                    m = future.result()
                    m['bucket'] = label
                    results[fname].append(m)
                except Exception as e:
                    print(f"  Error: {fname} on period {period_idx}: {e}")

            pct = (period_idx + 1) / len(all_periods) * 100
            print(f"\r  Progress: {pct:.0f}% ({period_idx + 1}/{len(all_periods)})", end="", flush=True)
    print()
    return results

def print_leaderboard(results, top_n=3):
    leaderboard = []
    for filename, metrics in results.items():
        if not metrics: continue
        cagrs = [m['cagr'] * 100 for m in metrics]
        leaderboard.append({
            'name': filename,
            'avg_cagr': np.mean(cagrs),
            'med_cagr': np.median(cagrs),
            'avg_sharpe': np.mean([m['sharpe'] for m in metrics]),
            'avg_dd': np.mean([m['max_dd'] * 100 for m in metrics]),
            'worst_dd': np.min([m['max_dd'] * 100 for m in metrics]),
            'n': len(metrics)
        })
    leaderboard.sort(key=lambda x: x['avg_cagr'], reverse=True)
    
    print("\n" + "="*110)
    print(f"  {'#':<3} {'Genome':<40} | {'AvgCAGR':>8} | {'MedCAGR':>8} | {'AvgShp':>7} | {'AvgDD':>8} | {'WorstDD':>8} | {'N':>3}")
    print("-" * 110)
    for i, row in enumerate(leaderboard):
        m = "★" if i < top_n else " "
        print(f"{m}{i+1:<3} {row['name']:<40} | {row['avg_cagr']:>7.2f}% | {row['med_cagr']:>7.2f}% | {row['avg_sharpe']:>7.2f} | {row['avg_dd']:>7.1f}% | {row['worst_dd']:>7.1f}% | {row['n']:>3}")
    print("="*110)
    return leaderboard

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=10, help="Number of random periods to test per duration bucket")
    parser.add_argument("--vault", type=str, default="vault", help="Path to the vault directory containing genomes")
    parser.add_argument("--promote", action="store_true", help="Replace genome.json in parent directory with the best performer")
    args = parser.parse_args()

    print("=" * 60)
    print("  VAULT SWEEP — Cross-Regime Resilience Audit")
    print("=" * 60)

    vault_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', args.vault))
    genomes = []
    if os.path.exists(vault_dir):
        for f in sorted(os.listdir(vault_dir)):
            if f.endswith('.json'):
                with open(os.path.join(vault_dir, f), 'r') as jf:
                    try:
                        g = json.load(jf)
                        if validate_genome(g): genomes.append((f, g))
                        else: print(f"  SKIP (invalid): {f}")
                    except Exception as e:
                        print(f"  ERROR loading {f}: {e}")
    
    if not genomes:
        print("  No valid genomes found.")
        sys.exit(1)

    data = load_spy_data("1993-01-01")
    results = run_sweep(genomes, data, samples_per_bucket=args.samples)
    leaderboard = print_leaderboard(results)

    if args.promote and leaderboard:
        best_genome_name = leaderboard[0]['name']
        best_genome_path = os.path.join(vault_dir, best_genome_name)
        target_path = os.path.join(os.path.dirname(vault_dir), "genome.json")
        
        print(f"\n  [PROMOTE] Replacing {os.path.basename(target_path)} with {best_genome_name}...")
        
        try:
            with open(best_genome_path, 'r') as src:
                best_data = json.load(src)
            with open(target_path, 'w') as dst:
                json.dump(best_data, dst, indent=4)
            print(f"  SUCCESS: {target_path} updated.")
        except Exception as e:
            print(f"  FAILED to promote genome: {e}")

