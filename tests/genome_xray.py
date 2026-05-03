"""
Strategy X-Ray — Deep Behavioral Audit.
Runs any strategy or genome over the full history and produces
a detailed breakdown of behavior.
"""

import argparse
import os
import sys
import numpy as np
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.dirname(__file__))

from utils import resolve_strategy
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data

LEVERAGE_MAP = {"SPY": 1.0, "2xSPY": 2.0, "3xSPY": 3.0, "CASH": 0.0}
TIER_ORDER = ["3xSPY", "2xSPY", "SPY", "CASH"]

def dominant_holding(holdings: dict) -> str:
    # Prioritize higher leverage tiers if weights are equal
    return max(holdings, key=lambda k: (holdings[k], LEVERAGE_MAP.get(k, 0.0)))

def run_xray(identifier: str):
    try:
        strategy = resolve_strategy(identifier)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print("Loading market data...")
    data = load_spy_data("1993-01-01")
    price_data_list = data[['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve']].to_dict('records')
    dates = data.index

    print(f"Running simulation using {strategy.NAME}...")
    res = _execute_simulation(
        strategy_type=strategy.__class__,
        price_data_list=price_data_list,
        dates=dates,
        strategy_kwargs={'genome': getattr(strategy, 'genome', None)} if hasattr(strategy, 'genome') else {}
    )

    portfolio = res['portfolio']
    metrics = res['metrics']
    holdings_log = portfolio.holdings_log
    rebalance_log = portfolio.rebalance_log

    total_days = len(holdings_log)
    total_years = total_days / 252.0

    # ── 1. Tier Residency ──
    tier_days = Counter()
    daily_leverages = []

    for _, holdings in holdings_log:
        dom = dominant_holding(holdings)
        tier_days[dom] += 1
        day_leverage = sum(holdings.get(asset, 0.0) * LEVERAGE_MAP.get(asset, 0.0) for asset in LEVERAGE_MAP)
        daily_leverages.append(day_leverage)

    # ── 2. Switching Analysis ──
    num_switches = len(rebalance_log)
    switches_per_year = num_switches / total_years if total_years > 0 else 0

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
            if current_tier is not None and current_tier in streaks:
                streaks[current_tier].append(current_streak)
            current_tier = dom
            current_streak = 1
    if current_tier is not None and current_tier in streaks:
        streaks[current_tier].append(current_streak)

    # ── 4. Leverage Distribution ──
    lev_array = np.array(daily_leverages)
    lev_buckets = {
        "0x (Cash)": np.sum(lev_array <= 0.01),
        "1x (SPY)": np.sum((lev_array > 0.01) & (lev_array <= 1.1)),
        "2x (SSO)": np.sum((lev_array > 1.1) & (lev_array <= 2.1)),
        "3x+ (UPRO)": np.sum(lev_array > 2.1),
    }

    # ── PRINT REPORT ──
    W = 70
    print(f"\n{'=' * W}")
    print(f"  STRATEGY X-RAY - {strategy.NAME}")
    print(f"{'=' * W}")

    # Performance Summary
    print(f"\n  {'PERFORMANCE SUMMARY':-<{W-4}}")
    print(f"  {'CAGR':<25} {metrics['cagr']*100:>12.2f}%")
    print(f"  {'Max Drawdown':<25} {metrics['max_dd']*100:>12.1f}%")
    print(f"  {'Sharpe Ratio':<25} {metrics['sharpe']:>12.2f}")
    print(f"  {'Average Leverage':<25} {metrics['avg_leverage']:>12.2f}x")
    print(f"  {'Period':<25} {str(dates[0].date()):>12} -> {str(dates[-1].date())}")

    # Tier Residency
    print(f"\n  {'TIER RESIDENCY':-<{W-4}}")
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
    print(f"\n  {'LEVERAGE DISTRIBUTION':-<{W-4}}")
    print(f"  {'Bucket':<15} {'Days':>8} {'% of Time':>10}")
    print(f"  {'-' * (W - 4)}")
    for bucket, days in lev_buckets.items():
        pct = days / total_days * 100 if total_days > 0 else 0
        bar = "#" * int(pct / 2)
        print(f"  {bucket:<15} {days:>8,} {pct:>9.1f}%  {bar}")

    # Switching Behavior
    print(f"\n  {'SWITCHING BEHAVIOR':-<{W-4}}")
    print(f"  {'Total Rebalances':<25} {num_switches:>12,}")
    print(f"  {'Switches per Year':<25} {switches_per_year:>12.1f}")

    if transitions:
        print(f"\n  {'TRANSITION MATRIX (Top 10)':-<{W-4}}")
        print(f"  {'From -> To':<30} {'Count':>8} {'% of Switches':>15}")
        print(f"  {'-' * (W - 4)}")
        for (frm, to), count in transitions.most_common(10):
            pct = count / sum(transitions.values()) * 100
            print(f"  {frm:<12} -> {to:<15} {count:>8,} {pct:>14.1f}%")

    # ── 5. DNA X-Ray (Feature Importance) ──
    if hasattr(strategy, 'genome') and strategy.genome:
        print(f"\n  {'DNA X-RAY (FEATURE IMPORTANCE)':-<{W-4}}")
        genome = strategy.genome
        version = genome.get('version', 1.0)
        
        # Structural Detection (for legacy genomes missing version keys)
        if 'bull' in genome and 'panic' in genome:
            version = 4.0
        elif 'brains' in genome:
            version = 6.0
        elif 'panic' in genome and ('3x' in genome or '2x' in genome):
            version = 2.0
        elif 'base_weights' in genome or 'panic_weights' in genome:
            version = 1.1
        elif 'bounds_p' in genome:
            version = 1.0 # V1 Manual

        importance = {}
        
        # FEATURE LISTS
        V1_FEATURES = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr']
        V9_FEATURES = ['SMA Dist', 'EMA Dist', 'RSI', 'MACD', 'ADX', 'TRIX', 'Slope', 'Vol', 'ATR', 'VIX', 'Yield Curve', 'MFI', 'BBW']
        
        try:
            v_num = float(version) if isinstance(version, (int, float, str)) and str(version).replace('.','',1).isdigit() else 0.0

            if v_num >= 7.0: # Neural (V7, V9)
                w1 = np.array(genome['layers'][0]['w'])
                # Sum absolute weights connecting each input to all hidden neurons
                scores = np.sum(np.abs(w1), axis=1)
                for i, score in enumerate(scores):
                    name = V9_FEATURES[i] if i < len(V9_FEATURES) else f"Input_{i}"
                    importance[name] = score
            
            elif v_num == 6.0: # Balancer
                for brain_name in ['cash', '1x', '2x', '3x']:
                    if brain_name in genome['brains']:
                        w = genome['brains'][brain_name].get('w', {})
                        for feature, val in w.items():
                            importance[feature] = importance.get(feature, 0) + abs(val)

            elif v_num == 2.0: # V2 Multi-Brain
                for module in ['panic', '1x', '2x', '3x']:
                    if module in genome:
                        w = genome[module].get('w', {})
                        for feature, val in w.items():
                            importance[feature] = importance.get(feature, 0) + abs(val)

            elif v_num in [3.0, 4.0]: # Precision
                for module in ['bull', 'panic']:
                    if module in genome:
                        w = genome[module].get('w', {})
                        for feature, val in w.items():
                            importance[feature] = importance.get(feature, 0) + abs(val)

            elif v_num == 5.0: # Sniper
                if 'sniper' in genome:
                    w = genome['sniper'].get('w', {})
                    for feature, val in w.items():
                        importance[feature] = importance.get(feature, 0) + abs(val)
                    
            elif v_num == 1.1: # V1 Classic
                for key in ['base_weights', 'panic_weights']:
                    if key in genome:
                        w = genome[key]
                        for k, v in w.items():
                            importance[k] = importance.get(k, 0) + abs(v)
            
            elif v_num == 1.0: # V1 Manual
                print(f"  {'SMA Lookback':<15} {genome.get('sma', 'N/A'):>10}d")
                print(f"  {'Min Bond Days':<15} {genome.get('min_b_days', 'N/A'):>10}d")
                print(f"  {'-' * (W - 4)}")
                print(f"  {'VIX Brackets (Bounds)':<15}")
                bounds = genome.get('bounds_p', [])
                for i, b in enumerate(bounds):
                    print(f"    Bracket {i+1}: VIX > {b:.1f}")

            if importance:
                sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
                max_score = sorted_imp[0][1] if sorted_imp else 1
                for name, score in sorted_imp[:8]:
                    pct = (score / max_score) * 100
                    bar = "█" * int(pct / 5)
                    print(f"  {name:<15} {score:>10.2f}  {bar}")
                
                # Show key hyperparameters
                print(f"  {'-' * (W - 4)}")
                if 'hysteresis' in genome: print(f"  {'Hysteresis':<15} {genome['hysteresis']:>10.3f}")
                if 'lock_days' in genome: print(f"  {'Lock Days':<15} {genome['lock_days']:>10.1f}")
                if 'smoothing' in genome: print(f"  {'Smoothing':<15} {genome['smoothing']:>10.3f}")
                if 'temp' in genome: print(f"  {'Softmax Temp':<15} {genome['temp']:>10.3f}")

        except Exception as e:
            print(f"  [DNA Error] Could not parse weights: {e}")

    print(f"\n{'=' * W}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("strategy", type=str, help="Path to genome JSON or Strategy Name")
    args = parser.parse_args()
    run_xray(args.strategy)
