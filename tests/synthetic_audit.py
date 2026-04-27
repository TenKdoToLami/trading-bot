"""
Synthetic Data Tester — Anti-Overfitting Audit.
Generates synthetic price series via Block Bootstrapping of historical data
and evaluates strategy consistency across these parallel universes.
"""

import argparse
import os
import sys
import random
import numpy as np
import pandas as pd
import concurrent.futures

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.dirname(__file__))

from utils import resolve_strategy
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data

def generate_synthetic_series(df, chunk_size=252):
    """
    Creates a synthetic series by stitching together random blocks of historical data.
    Ensures relative returns are preserved.
    """
    total_len = len(df)
    num_chunks = total_len // chunk_size
    
    indices = []
    for _ in range(num_chunks + 1):
        start = random.randint(0, total_len - chunk_size)
        indices.extend(range(start, start + chunk_size))
        
    # Trim to match original length
    indices = indices[:total_len]
    
    synthetic = df.iloc[indices].copy()
    # Regenerate continuous price from stitched returns to avoid massive price gaps
    returns = synthetic['close'].pct_change().fillna(0)
    
    # We need to preserve the relationship between open/high/low/close
    # Calculate daily ratios relative to previous close
    synthetic['ret_close'] = df['close'] / df['close'].shift(1)
    synthetic['ratio_open'] = df['open'] / df['close'].shift(1)
    synthetic['ratio_high'] = df['high'] / df['close'].shift(1)
    synthetic['ratio_low'] = df['low'] / df['close'].shift(1)
    
    # Reconstruct
    new_close = [df['close'].iloc[0]]
    for r in returns[1:]:
        new_close.append(new_close[-1] * (1 + r))
    
    synthetic['close'] = new_close
    # Note: Open/High/Low reconstruction is complex for synthetic data, 
    # but for these strategies mostly 'close' and indicators are used.
    # We'll use a simplified reconstruction for indicators.
    
    return synthetic

def evaluate_on_synthetic(strategy_type, strategy_kwargs, data_list, dates):
    res = _execute_simulation(
        strategy_type=strategy_type,
        price_data_list=data_list,
        dates=dates,
        strategy_kwargs=strategy_kwargs
    )
    return res['metrics']

def run_synthetic_audit(identifier: str, iterations=50, chunk_size=252):
    try:
        strategy = resolve_strategy(identifier)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Loading market data...")
    data = load_spy_data("1993-01-01")
    
    print(f"Running Synthetic Audit for {strategy.NAME} ({iterations} iterations)...")
    
    strat_type = strategy.__class__
    strat_kwargs = {'genome': getattr(strategy, 'genome', None)} if hasattr(strategy, 'genome') else {}
    
    results = []
    
    # Use ProcessPoolExecutor for parallel simulations
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        for i in range(iterations):
            # Create synthetic data
            synth_df = generate_synthetic_series(data, chunk_size=chunk_size)
            data_list = synth_df[['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve']].to_dict('records')
            dates = data.index
            
            futures.append(executor.submit(evaluate_on_synthetic, strat_type, strat_kwargs, data_list, dates))
            
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            try:
                metrics = future.result()
                results.append(metrics)
                print(f"\r  Progress: {(i+1)/iterations*100:.0f}%", end="", flush=True)
            except Exception as e:
                print(f"\n  ERROR in iteration {i}: {e}")
    
    print("\n")
    
    # Analyze results
    cagrs = [m['cagr'] * 100 for m in results]
    drawdowns = [m['max_dd'] * 100 for m in results]
    sharpes = [m['sharpe'] for m in results]
    
    # Historical performance for comparison
    print("Running original baseline...")
    orig_res = _execute_simulation(
        strategy_type=strat_type,
        price_data_list=data[['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve']].to_dict('records'),
        dates=data.index,
        strategy_kwargs=strat_kwargs
    )
    orig_m = orig_res['metrics']
    
    W = 70
    print(f"\n{'=' * W}")
    print(f"  SYNTHETIC ROBUSTNESS AUDIT: {strategy.NAME}")
    print(f"  {'Method':<20} Block Bootstrapping (Chunk: {chunk_size}d)")
    print(f"  {'Iterations':<20} {iterations}")
    print(f"{'=' * W}")
    
    print(f"\n  {'METRIC':<20} | {'BASELINE':>12} | {'SYNTH AVG':>12} | {'SYNTH STD':>12}")
    print(f"  {'-' * (W - 4)}")
    print(f"  {'CAGR (%)':<20} | {orig_m['cagr']*100:>11.2f}% | {np.mean(cagrs):>11.2f}% | {np.std(cagrs):>11.2f}%")
    print(f"  {'Max DD (%)':<20} | {orig_m['max_dd']*100:>11.2f}% | {np.mean(drawdowns):>11.2f}% | {np.std(drawdowns):>11.2f}%")
    print(f"  {'Sharpe':<20} | {orig_m['sharpe']:>12.2f} | {np.mean(sharpes):>12.2f} | {np.std(sharpes):>12.2f}")
    
    print(f"\n  {'DISTRIBUTION':-<{W-4}}")
    print(f"  {'Percentile':<20} | {'CAGR':>12} | {'Max DD':>12}")
    print(f"  {'-' * (W - 4)}")
    for p in [5, 25, 50, 75, 95]:
        print(f"  {p:>2d}th Percentile      | {np.percentile(cagrs, p):>11.2f}% | {np.percentile(drawdowns, p):>11.2f}%")
        
    print(f"\n{'=' * W}\n")
    
    # Verdict
    cagr_drop = (np.mean(cagrs) / (orig_m['cagr'] * 100)) - 1 if orig_m['cagr'] != 0 else 0
    if cagr_drop < -0.5:
        print("  WARNING: High Overfitting Risk! Synthetic performance is < 50% of baseline.")
    elif cagr_drop < -0.2:
        print("  NOTICE: Moderate Overfitting. Strategy relies significantly on specific historical sequencing.")
    else:
        print("  VERDICT: Robust. Strategy performs consistently across reshuffled market regimes.")
    print("")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("strategy", type=str, help="Path to genome JSON or Strategy Name")
    parser.add_argument("--iters", type=int, default=50, help="Number of synthetic iterations")
    parser.add_argument("--chunk", type=int, default=252, help="Block size in trading days (default 252)")
    args = parser.parse_args()
    
    run_synthetic_audit(args.strategy, iterations=args.iters, chunk_size=args.chunk)
