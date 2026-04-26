"""
Genome X-Ray — Deep Behavioral Audit.

Runs a single genome over the full inception period and produces
a detailed breakdown of allocation behavior, switching frequency,
leverage distribution, and tier residency.

Usage:
    python tests/genome_xray.py vault/genome_cagr_41.15_dd_-73.82.json
    python tests/genome_xray.py best_genome.json
"""

import argparse
import json
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from strategies._genome_strategy import GenomeStrategy
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data


LEVERAGE_MAP = {"SPY": 1.0, "2xSPY": 2.0, "3xSPY": 3.0, "CASH": 0.0}
TIER_ORDER = ["3xSPY", "2xSPY", "SPY", "CASH"]


def dominant_holding(holdings: dict) -> str:
    """Return the asset with the highest weight."""
    return max(holdings, key=holdings.get)


def run_xray(genome_path: str):
    # ── Load Genome ──
    with open(genome_path, 'r') as f:
        genome = json.load(f)

    genome_name = os.path.basename(genome_path)

    # ── Load Data & Run Simulation ──
    print("Loading market data...")
    data = load_spy_data("1993-01-01", force_refresh=False)
    price_data_list = data[['open', 'high', 'low', 'close', 'volume']].to_dict('records')
    dates = data.index

    print(f"Running simulation on {len(data)} trading days...")
    res = _execute_simulation(
        strategy_type=GenomeStrategy,
        price_data_list=price_data_list,
        dates=dates,
        strategy_kwargs={'genome': genome}
    )

    portfolio = res['portfolio']
    metrics = res['metrics']
    holdings_log = portfolio.holdings_log      # [(date, {asset: weight}), ...]
    rebalance_log = portfolio.rebalance_log    # [(date, {asset: weight}), ...]
    equity_curve = portfolio.equity_curve      # [(date, equity), ...]

    total_days = len(holdings_log)
    total_years = total_days / 252.0

    # ── 1. Tier Residency ──
    tier_days = Counter()
    daily_leverages = []

    for _, holdings in holdings_log:
        dom = dominant_holding(holdings)
        tier_days[dom] += 1

        day_leverage = sum(
            holdings.get(asset, 0.0) * LEVERAGE_MAP[asset]
            for asset in LEVERAGE_MAP
        )
        daily_leverages.append(day_leverage)

    # ── 2. Switching Analysis ──
    num_switches = len(rebalance_log)
    switches_per_year = num_switches / total_years if total_years > 0 else 0

    # Transition matrix: from -> to
    transitions = Counter()
    if len(rebalance_log) > 1:
        for i in range(1, len(rebalance_log)):
            prev_dom = dominant_holding(rebalance_log[i - 1][1])
            curr_dom = dominant_holding(rebalance_log[i][1])
            transitions[(prev_dom, curr_dom)] += 1

    # ── 3. Streak Analysis ──
    streaks = {t: [] for t in TIER_ORDER}
    current_tier = None
    current_streak = 0
    for _, holdings in holdings_log:
        dom = dominant_holding(holdings)
        if dom == current_tier:
            current_streak += 1
        else:
            if current_tier is not None:
                streaks[current_tier].append(current_streak)
            current_tier = dom
            current_streak = 1
    if current_tier is not None:
        streaks[current_tier].append(current_streak)

    # ── 4. Leverage Distribution ──
    lev_array = np.array(daily_leverages)
    lev_buckets = {
        "0x (Cash)": np.sum(lev_array == 0.0),
        "1x (SPY)": np.sum((lev_array > 0) & (lev_array <= 1.0)),
        "2x (SSO)": np.sum((lev_array > 1.0) & (lev_array <= 2.0)),
        "3x (UPRO)": np.sum((lev_array > 2.0) & (lev_array <= 3.0)),
    }

    # ── PRINT REPORT ──
    W = 70
    print(f"\n{'=' * W}")
    print(f"  GENOME X-RAY — {genome_name}")
    print(f"{'=' * W}")

    # Performance Summary
    print(f"\n  {'PERFORMANCE SUMMARY':─<{W-4}}")
    print(f"  {'Total Return':<25} {metrics['total_return']*100:>12,.0f}%")
    print(f"  {'CAGR':<25} {metrics['cagr']*100:>12.2f}%")
    print(f"  {'Max Drawdown':<25} {metrics['max_dd']*100:>12.1f}%")
    print(f"  {'Sharpe Ratio':<25} {metrics['sharpe']:>12.2f}")
    print(f"  {'Volatility':<25} {metrics['volatility']*100:>12.1f}%")
    print(f"  {'Average Leverage':<25} {metrics['avg_leverage']:>12.2f}x")
    print(f"  {'Period':<25} {str(dates[0].date()):>12} → {str(dates[-1].date())}")
    print(f"  {'Trading Days':<25} {total_days:>12,}")
    print(f"  {'Years':<25} {total_years:>12.1f}")

    # Tier Residency
    print(f"\n  {'TIER RESIDENCY':─<{W-4}}")
    print(f"  {'Tier':<15} {'Days':>8} {'% of Time':>10} {'Avg Streak':>12} {'Max Streak':>12}")
    print(f"  {'-' * (W - 4)}")
    for tier in TIER_ORDER:
        days = tier_days.get(tier, 0)
        pct = days / total_days * 100 if total_days > 0 else 0
        tier_streaks = streaks.get(tier, [])
        avg_streak = np.mean(tier_streaks) if tier_streaks else 0
        max_streak = max(tier_streaks) if tier_streaks else 0
        print(f"  {tier:<15} {days:>8,} {pct:>9.1f}% {avg_streak:>11.1f}d {max_streak:>11,}d")

    # Leverage Distribution
    print(f"\n  {'LEVERAGE DISTRIBUTION':─<{W-4}}")
    print(f"  {'Bucket':<15} {'Days':>8} {'% of Time':>10}")
    print(f"  {'-' * (W - 4)}")
    for bucket, days in lev_buckets.items():
        pct = days / total_days * 100 if total_days > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"  {bucket:<15} {days:>8,} {pct:>9.1f}%  {bar}")

    # Leverage Statistics
    print(f"\n  {'LEVERAGE STATISTICS':─<{W-4}}")
    print(f"  {'Average':<25} {np.mean(lev_array):>12.2f}x")
    print(f"  {'Median':<25} {np.median(lev_array):>12.2f}x")
    print(f"  {'Std Dev':<25} {np.std(lev_array):>12.2f}x")

    # Switching Behavior
    print(f"\n  {'SWITCHING BEHAVIOR':─<{W-4}}")
    print(f"  {'Total Rebalances':<25} {num_switches:>12,}")
    print(f"  {'Switches per Year':<25} {switches_per_year:>12.1f}")

    if transitions:
        print(f"\n  {'TRANSITION MATRIX (Top 10)':─<{W-4}}")
        print(f"  {'From → To':<30} {'Count':>8} {'% of Switches':>15}")
        print(f"  {'-' * (W - 4)}")
        for (frm, to), count in transitions.most_common(10):
            pct = count / sum(transitions.values()) * 100
            print(f"  {frm:<12} → {to:<15} {count:>8,} {pct:>14.1f}%")

    # Genome DNA Summary
    print(f"\n  {'GENOME DNA':─<{W-4}}")
    print(f"  Panic Threshold: {genome['panic_threshold']:.4f}")
    print(f"  Lock Days:       {genome['lock_days']:.1f}")
    t = genome['base_thresholds']
    print(f"  Base Tiers:      3x > {t['tier_3x']:.4f} | 2x > {t['tier_2x']:.4f} | 1x > {t['tier_1x']:.4f}")

    # Active indicators
    for group in ['panic', 'base']:
        active_key = f'{group}_active'
        weight_key = f'{group}_weights'
        if active_key in genome:
            active = [k for k, v in genome[active_key].items() if v]
            weights = {k: f"{genome[weight_key][k]:+.3f}" for k in active}
            print(f"  {group.capitalize()} Active:   {', '.join(active)}")
            print(f"  {group.capitalize()} Weights:  {weights}")

    print(f"\n{'=' * W}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genome X-Ray — Deep Behavioral Audit")
    parser.add_argument("genome", type=str, help="Path to genome JSON file")
    args = parser.parse_args()

    genome_path = os.path.join(os.path.dirname(__file__), '..', args.genome)
    genome_path = os.path.abspath(genome_path)

    if not os.path.exists(genome_path):
        print(f"ERROR: File not found: {genome_path}")
        sys.exit(1)

    run_xray(genome_path)
