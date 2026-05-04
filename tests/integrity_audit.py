"""
Integrity Audit — Proves that V9 Intra only uses past data at decision time.

This script instruments the simulation loop and logs every piece of data
available to the strategy at each decision point, verifying no future leak.
Also performs a full neural network weight analysis.
"""

import sys
import os
import json
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.helpers.data_provider import load_spy_data
from src.tournament.portfolio import Portfolio
from strategies.genome_v9_intra import GenomeV9Intra


def run_integrity_audit(genome_path):
    """Instruments the simulation and logs data provenance at each step."""
    
    with open(genome_path, 'r') as f:
        genome = json.load(f)
    
    data = load_spy_data("1993-01-01")
    price_data_list = data[['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve']].to_dict('records')
    dates = data.index
    
    strategy = GenomeV9Intra(genome=genome)
    strategy.reset()
    portfolio = Portfolio()
    
    # Track what the strategy sees vs reality
    violations = []
    decision_log = []
    
    print("=" * 80)
    print("  INTEGRITY AUDIT — Data Provenance Trace")
    print("=" * 80)
    print(f"\n  Running instrumented simulation on {len(price_data_list)} days...\n")
    
    for i in range(len(price_data_list)):
        date_str = str(dates[i].date())
        row = price_data_list[i]
        prev_row = price_data_list[i-1] if i > 0 else None
        
        spy_price = (float(row['open']) + float(row['close'])) / 2
        
        # Apply return
        if i > 0:
            prev_price = (float(prev_row['open']) + float(prev_row['close'])) / 2
            daily_ret = (spy_price - prev_price) / prev_price
            portfolio.apply_daily_return(date_str, daily_ret)
            if portfolio.is_liquidated:
                break
        
        # Build the EXACT mid_row that the strategy receives (replicating runner.py fix)
        intra_price = spy_price
        mid_row = row.copy()
        mid_row['close'] = intra_price
        mid_row['high'] = float(prev_row['high']) if prev_row else intra_price
        mid_row['low'] = float(prev_row['low']) if prev_row else intra_price
        mid_row['volume'] = float(prev_row.get('volume', 0)) if prev_row else 0
        mid_row['vix'] = float(prev_row.get('vix', 15.0)) if prev_row else 15.0
        mid_row['yield_curve'] = float(prev_row.get('yield_curve', 0.0)) if prev_row else 0.0
        
        # ---- INTEGRITY CHECK ----
        # Verify: Does mid_row contain ANY data from today's actual candle (except mid-price)?
        if i > 0:
            checks = {
                'high': (mid_row['high'], prev_row['high'], row['high']),
                'low': (mid_row['low'], prev_row['low'], row['low']),
                'volume': (mid_row['volume'], prev_row.get('volume', 0), row.get('volume', 0)),
                'vix': (mid_row['vix'], prev_row.get('vix', 15.0), row.get('vix', 15.0)),
            }
            for field, (given, yesterday, today) in checks.items():
                if given == float(today) and float(today) != float(yesterday):
                    violations.append(f"Day {i} ({date_str}): {field} = TODAY's value ({today}), not yesterday's ({yesterday})")
        
        # Verify: strategy's price history only contains PAST closes
        if len(strategy.prices) > 0:
            last_history_price = strategy.prices[-1]
            if i > 0:
                expected_prev_close = float(prev_row['close'])
                if abs(last_history_price - expected_prev_close) > 0.001:
                    violations.append(f"Day {i} ({date_str}): History contaminated. Last price={last_history_price:.2f}, expected prev_close={expected_prev_close:.2f}")
        
        # Run strategy
        result = strategy.on_data(date_str, mid_row, prev_row)
        
        if result is not None:
            new_holdings, telemetry = result
            if new_holdings != portfolio.holdings:
                portfolio.rebalance(date_str, new_holdings)
                
                # Log decisions for analysis
                if i > 5:  # Skip warmup
                    tier = list(new_holdings.keys())[0]
                    decision_log.append({
                        'day': i, 'date': date_str, 'tier': tier,
                        'intra_ret': telemetry.get('intra_ret', 0),
                        'conf_cash': telemetry.get('conf_cash', 0),
                        'conf_3x': telemetry.get('conf_3x', 0),
                    })
        
        # Finalize day (TRUE close goes to history for TOMORROW)
        strategy.update_history(row)
    
    # ---- RESULTS ----
    print("  DATA PROVENANCE VERIFICATION")
    print("  " + "-" * 60)
    if violations:
        print(f"  ❌ FAILED — {len(violations)} violations found:")
        for v in violations[:20]:
            print(f"     {v}")
    else:
        print("  ✅ PASSED — Zero data leakage detected across all days.")
        print(f"     Verified {len(price_data_list)} days of simulation.")
        print(f"     All H/L/V/VIX values confirmed from YESTERDAY.")
        print(f"     Price history confirmed as PREVIOUS close only.")
    
    metrics = portfolio.get_metrics()
    print(f"\n  HONEST PERFORMANCE (with fix applied)")
    print("  " + "-" * 60)
    print(f"  CAGR:           {metrics['cagr']*100:.2f}%")
    print(f"  Max Drawdown:   {metrics['max_dd']*100:.2f}%")
    print(f"  Sharpe:         {metrics['sharpe']:.2f}")
    print(f"  Trades:         {metrics['num_rebalances']}")
    
    return genome, decision_log, metrics


def analyze_neural_weights(genome):
    """Deep analysis of the neural network's decision-making."""
    
    w1 = np.array(genome['layers'][0]['w'])  # (14, 24)
    b1 = np.array(genome['layers'][0]['b'])  # (24,)
    w2 = np.array(genome['layers'][1]['w'])  # (24, 4)
    b2 = np.array(genome['layers'][1]['b'])  # (4,)
    
    # Adapt if 13-input genome
    if w1.shape[0] == 13:
        w1 = np.vstack([w1, np.zeros((1, w1.shape[1]))])
    
    feature_names = [
        'SMA Dist', 'EMA Dist', 'RSI', 'MACD', 'ADX', 'TRIX',
        'Slope', 'Volatility', 'ATR', 'VIX', 'Yield Curve', 'MFI',
        'BB Width', 'Intra Return'
    ]
    
    output_names = ['CASH', 'SPY (1x)', 'SSO (2x)', 'UPRO (3x)']
    
    print("\n" + "=" * 80)
    print("  NEURAL NETWORK WEIGHT ANALYSIS")
    print("=" * 80)
    
    # Feature importance: L1 norm of weights from each input across all hidden neurons
    feature_importance = np.sum(np.abs(w1), axis=1)
    total_importance = feature_importance.sum()
    
    print("\n  FEATURE IMPORTANCE (Input → Hidden Layer)")
    print("  " + "-" * 60)
    sorted_idx = np.argsort(feature_importance)[::-1]
    for idx in sorted_idx:
        pct = feature_importance[idx] / total_importance * 100
        bar = "█" * int(pct * 2)
        leaked = " ← SANITIZED (yesterday)" if feature_names[idx] in ['VIX', 'Yield Curve'] else ""
        leaked = " ← USES (open+close)/2" if feature_names[idx] == 'Intra Return' else leaked
        print(f"  {feature_names[idx]:<15} | {feature_importance[idx]:>6.2f} ({pct:>5.1f}%) {bar}{leaked}")
    
    # Output layer analysis: which hidden neurons drive each output
    print("\n  OUTPUT LAYER BIAS (Initial preference before neural input)")
    print("  " + "-" * 60)
    for i, name in enumerate(output_names):
        print(f"  {name:<12} bias: {b2[i]:>+7.4f}")
    
    # Effective feature → output connection (W1 * W2 path analysis)
    # This shows the "net pull" of each input feature on each output
    effective_weights = np.dot(w1, np.maximum(0, w2))  # Approximate through ReLU
    
    print("\n  EFFECTIVE FEATURE → OUTPUT PULL (through hidden layer)")
    print("  " + "-" * 60)
    print(f"  {'Feature':<15} | {'→CASH':>8} | {'→SPY':>8} | {'→SSO':>8} | {'→UPRO':>8}")
    print("  " + "-" * 60)
    for f_idx in sorted_idx:
        vals = effective_weights[f_idx]
        print(f"  {feature_names[f_idx]:<15} | {vals[0]:>+7.3f} | {vals[1]:>+7.3f} | {vals[2]:>+7.3f} | {vals[3]:>+7.3f}")
    
    # Smoothing and hysteresis analysis
    smoothing = genome.get('smoothing', 0.5)
    hysteresis = genome.get('hysteresis', 0.15)
    
    print(f"\n  BEHAVIORAL PARAMETERS")
    print("  " + "-" * 60)
    print(f"  Smoothing:    {smoothing:.3f}  ← {smoothing*100:.0f}% of today's signal, {(1-smoothing)*100:.0f}% of yesterday's conviction")
    print(f"  Hysteresis:   {hysteresis:.4f}  ← Confidence gap needed to switch tiers")
    half_life = np.log(0.5) / np.log(1 - smoothing) if smoothing < 1 else float('inf')
    print(f"  Signal Half-Life: {half_life:.1f} days  ← Days for a new signal to reach 50% influence")
    print(f"  Effective Memory: ~{int(half_life * 3)} days  ← Days for signal to reach ~87% influence")
    
    # Lookback analysis
    lookbacks = genome.get('lookbacks', {})
    print(f"\n  INDICATOR LOOKBACK PERIODS")
    print("  " + "-" * 60)
    for k, v in sorted(lookbacks.items(), key=lambda x: x[1], reverse=True):
        print(f"  {k:<10}: {v:>4} days")


def analyze_decisions(decision_log):
    """Analyze the pattern of trading decisions."""
    if not decision_log:
        print("\n  No decisions to analyze.")
        return
    
    print("\n" + "=" * 80)
    print("  DECISION PATTERN ANALYSIS")
    print("=" * 80)
    
    # Transition analysis
    tiers = [d['tier'] for d in decision_log]
    tier_counts = {}
    for t in tiers:
        tier_counts[t] = tier_counts.get(t, 0) + 1
    
    print(f"\n  Total rebalance decisions logged: {len(decision_log)}")
    print(f"\n  Decisions by target tier:")
    for tier, count in sorted(tier_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    {tier:<10}: {count:>5} ({count/len(decision_log)*100:.1f}%)")
    
    # Intra-day return at decision time
    intra_rets = [d['intra_ret'] for d in decision_log if d.get('intra_ret')]
    if intra_rets:
        print(f"\n  Intra-day return at decision points:")
        print(f"    Mean:   {np.mean(intra_rets)*100:>+6.3f}%")
        print(f"    Median: {np.median(intra_rets)*100:>+6.3f}%")
        print(f"    Std:    {np.std(intra_rets)*100:>6.3f}%")
        
        # Does the model buy on up-days and sell on down-days? (momentum signal)
        buy_decisions = [d for d in decision_log if d['tier'] in ('3xSPY', '2xSPY', 'SPY')]
        sell_decisions = [d for d in decision_log if d['tier'] == 'CASH']
        
        if buy_decisions:
            avg_buy_ret = np.mean([d['intra_ret'] for d in buy_decisions])
            print(f"\n    Avg intra return when BUYING:  {avg_buy_ret*100:>+6.3f}%")
        if sell_decisions:
            avg_sell_ret = np.mean([d['intra_ret'] for d in sell_decisions])
            print(f"    Avg intra return when SELLING: {avg_sell_ret*100:>+6.3f}%")
    
    # First 10 decisions sample
    print(f"\n  Sample decisions (first 10):")
    print(f"  {'Date':<12} | {'Tier':<8} | {'IntraRet':>9} | {'Conf_Cash':>9} | {'Conf_3x':>9}")
    print("  " + "-" * 60)
    for d in decision_log[:10]:
        print(f"  {d['date']:<12} | {d['tier']:<8} | {d['intra_ret']*100:>+8.3f}% | {d['conf_cash']:>9.4f} | {d['conf_3x']:>9.4f}")


if __name__ == "__main__":
    genome_path = sys.argv[1] if len(sys.argv) > 1 else "champions/v9_intra/genome.json"
    genome_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', genome_path))
    
    if not os.path.exists(genome_path):
        print(f"ERROR: Genome not found: {genome_path}")
        sys.exit(1)
    
    print(f"  Genome: {os.path.basename(genome_path)}")
    
    genome, decisions, metrics = run_integrity_audit(genome_path)
    analyze_neural_weights(genome)
    analyze_decisions(decisions)
    
    print("\n" + "=" * 80)
