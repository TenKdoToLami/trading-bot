import pandas as pd
import numpy as np
import yfinance as yf
import json
import os
import random

def calculate_metrics(equity_history, daily_returns, risk_free=0.03):
    years = len(equity_history) / 252
    cagr = (equity_history[-1] ** (1/years)) - 1 if equity_history[-1] > 0 else -1
    ann_ret = np.mean(daily_returns) * 252
    ann_vol = np.std(daily_returns) * np.sqrt(252)
    sharpe = (ann_ret - risk_free) / ann_vol if ann_vol > 0 else 0
    peak = np.maximum.accumulate(equity_history)
    dd = (equity_history - peak) / peak
    max_dd = np.min(dd)
    return cagr, sharpe, max_dd

def run_simulation(df, dna, weights_p, start_idx, end_idx):
    subset = df.iloc[start_idx:end_idx].copy()
    spy_returns = subset['spy'].pct_change().fillna(0).values
    vix = subset['vix'].values
    spy = subset['spy'].values
    
    eq_bot = 1.0; eq_1x = 1.0; eq_2x = 1.0; eq_3x = 1.0
    hist_bot = [1.0]; hist_1x = [1.0]; hist_2x = [1.0]; hist_3x = [1.0]
    rets_bot = []; rets_1x = []; rets_2x = []; rets_3x = []
    
    panic_mode = False; days_in_regime = 0; current_tier = 0; base_lockout = 0
    sma_period = dna['sma']; min_b_days = dna['min_b_days']; bounds_p = dna['bounds_p']
    
    for i in range(1, len(subset)):
        prev_spy = spy[i-1]; prev_vix = vix[i-1]; daily_ret = spy_returns[i]
        sma_val = np.mean(spy[:i]) if i <= sma_period else np.mean(spy[i-sma_period:i])
        sma_triggered = prev_spy < sma_val
        days_in_regime += 1
        if panic_mode:
            if not sma_triggered: panic_mode = False; days_in_regime = 0
        else:
            if sma_triggered and days_in_regime >= min_b_days: panic_mode = True; days_in_regime = 0
        
        target_tier = np.digitize(prev_vix, bounds_p) if panic_mode else 0
        if base_lockout > 0:
            base_lockout -= 1; target_tier = current_tier
        if target_tier != current_tier:
            if not panic_mode and target_tier == 0: base_lockout = 10
            current_tier = target_tier
            
        w = weights_p[min(current_tier, len(weights_p)-1)] if panic_mode else [0.0, 1.0, 0.0]
        r_2x = (daily_ret * 2.0) - (0.0120 / 252); r_3x = (daily_ret * 3.0) - (0.0150 / 252); r_cash = (0.03 / 252)
        
        step_bot = (w[0] * r_2x) + (w[1] * r_3x) + (w[2] * r_cash)
        eq_bot *= (1 + step_bot); hist_bot.append(eq_bot); rets_bot.append(step_bot)
        eq_1x *= (1 + daily_ret); hist_1x.append(eq_1x); rets_1x.append(daily_ret)
        eq_2x *= (1 + r_2x); hist_2x.append(eq_2x); rets_2x.append(r_2x)
        eq_3x *= (1 + r_3x); hist_3x.append(eq_3x); rets_3x.append(r_3x)
        
    return {
        "bot": calculate_metrics(np.array(hist_bot), np.array(rets_bot)),
        "1x": calculate_metrics(np.array(hist_1x), np.array(rets_1x)),
        "2x": calculate_metrics(np.array(hist_2x), np.array(rets_2x)),
        "3x": calculate_metrics(np.array(hist_3x), np.array(rets_3x))
    }

def print_table(title, results_list):
    metrics = ['cagr', 'sharpe', 'max_dd']
    assets = ['bot', '1x', '2x', '3x']
    final_data = {asset: {m: [] for m in metrics} for asset in assets}
    for res in results_list:
        for asset in assets:
            final_data[asset]['cagr'].append(res[asset][0])
            final_data[asset]['sharpe'].append(res[asset][1])
            final_data[asset]['max_dd'].append(res[asset][2])
            
    print(f"\n{title}")
    print("="*70)
    print(f"{'Metric':<18} | {'BOT':>10} | {'1x SPY':>10} | {'2x SSO':>10} | {'3x UPRO':>10}")
    print("-" * 70)
    for m in metrics:
        for stat in ['Mean', 'Median']:
            label = f"{stat} {m.upper()}"
            row = f"{label:<18} | "
            for asset in assets:
                val = np.mean(final_data[asset][m]) if stat == 'Mean' else np.median(final_data[asset][m])
                if m in ['cagr', 'max_dd']: row += f"{val*100:>9.2f}% | "
                else: row += f"{val:>10.2f} | "
            print(row)
        if m != metrics[-1]: print("-" * 70)
    print("="*70)

def run_resilience_test():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, "..", "config", "strategy.json"), "r") as f: dna = json.load(f)
    
    spy_df = yf.download("SPY", start="1993-01-01")
    vix_df = yf.download("^VIX", start="1993-01-01")
    if isinstance(spy_df.columns, pd.MultiIndex): spy_df.columns = spy_df.columns.get_level_values(0)
    if isinstance(vix_df.columns, pd.MultiIndex): vix_df.columns = vix_df.columns.get_level_values(0)
    df = pd.DataFrame({'spy': spy_df['Close'], 'vix': vix_df['Close']}).dropna()
    
    buckets = [(5,10), (10,15), (15,20), (20,25), (25,30), (30,34)]
    all_results = []
    bucket_results = {b: [] for b in buckets}
    
    total_iters = 2000
    print(f"--- STARTING SUPER-MATRIX ({total_iters} Iterations) ---")
    
    for _ in range(total_iters):
        bucket = random.choice(buckets)
        duration = int(random.uniform(bucket[0], bucket[1]) * 252)
        
        # Ensure duration doesn't exceed total data
        if duration >= len(df) - 10:
            duration = len(df) - 50
            
        start = random.randint(0, len(df) - duration - 1)
        res = run_simulation(df, dna, dna['weights_p'], start, start + duration)
        all_results.append(res)
        bucket_results[bucket].append(res)
    
    print_table("OVERALL PERFORMANCE (ALL REGIMES)", all_results)
    
    for b in buckets:
        if bucket_results[b]:
            print_table(f"TIME HORIZON: {b[0]}-{b[1]} YEARS", bucket_results[b])

if __name__ == "__main__":
    run_resilience_test()
