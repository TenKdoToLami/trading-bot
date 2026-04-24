import pandas as pd
import numpy as np
import yfinance as yf
import json
import os
import random

def calculate_sharpe(returns, risk_free=0.03):
    ann_ret = np.mean(returns) * 252
    ann_vol = np.std(returns) * np.sqrt(252)
    if ann_vol == 0: return 0
    return (ann_ret - risk_free) / ann_vol

def run_simulation(df, dna, weights_p, start_idx, end_idx):
    # Slice Data
    subset = df.iloc[start_idx:end_idx].copy()
    returns = subset['spy'].pct_change().fillna(0).values
    vix = subset['vix'].values
    spy = subset['spy'].values
    
    equity = 1.0
    eq_1x = 1.0; eq_2x = 1.0; eq_3x = 1.0
    
    strat_returns = []
    
    panic_mode = False
    days_in_regime = 0
    current_tier = 0
    base_lockout = 0
    
    sma_period = dna['sma']
    min_b_days = dna['min_b_days']
    bounds_p = dna['bounds_p']
    
    for i in range(1, len(subset)):
        prev_spy = spy[i-1]
        prev_vix = vix[i-1]
        daily_ret = returns[i]
        
        # A. Indicators
        if i <= sma_period:
            sma_val = np.mean(spy[:i])
        else:
            sma_val = np.mean(spy[i-sma_period:i])
        sma_triggered = prev_spy < sma_val
        
        # B. Regime
        days_in_regime += 1
        if panic_mode:
            if not sma_triggered:
                panic_mode = False; days_in_regime = 0
        else:
            if sma_triggered and days_in_regime >= min_b_days:
                panic_mode = True; days_in_regime = 0
        
        # C. Tier & Lockout
        target_tier = np.digitize(prev_vix, bounds_p) if panic_mode else 0
        if base_lockout > 0:
            base_lockout -= 1
            target_tier = current_tier
        if target_tier != current_tier:
            if not panic_mode and target_tier == 0: base_lockout = 10
            current_tier = target_tier
            
        # D. Weights & Returns
        w = weights_p[min(current_tier, 4)] if panic_mode else [0.0, 1.0, 0.0]
        
        r_2x = (daily_ret * 2.0) - (0.0120 / 252)
        r_3x = (daily_ret * 3.0) - (0.0150 / 252)
        r_cash = (0.03 / 252)
        
        step_ret = (w[0] * r_2x) + (w[1] * r_3x) + (w[2] * r_cash)
        equity *= (1 + step_ret)
        strat_returns.append(step_ret)
        
        # Benchmarks
        eq_1x *= (1 + daily_ret)
        eq_2x *= (1 + r_2x)
        eq_3x *= (1 + r_3x)
        
    # Metrics
    years = len(subset) / 252
    cagr = (equity ** (1/years)) - 1
    sharpe = calculate_sharpe(strat_returns)
    
    return {
        "cagr": cagr, "sharpe": sharpe, 
        "cagr_1x": (eq_1x ** (1/years)) - 1,
        "cagr_2x": (eq_2x ** (1/years)) - 1,
        "cagr_3x": (eq_3x ** (1/years)) - 1
    }

def run_resilience_test():
    print("--- STARTING MULTI-REGIME RESILIENCE TEST ---")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dna_path = os.path.join(script_dir, "..", "config", "strategy.json")
    with open(dna_path, "r") as f:
        dna = json.load(f)
    
    spy_df = yf.download("SPY", start="1993-01-01")
    vix_df = yf.download("^VIX", start="1993-01-01")
    if isinstance(spy_df.columns, pd.MultiIndex): spy_df.columns = spy_df.columns.get_level_values(0)
    if isinstance(vix_df.columns, pd.MultiIndex): vix_df.columns = vix_df.columns.get_level_values(0)
    df = pd.DataFrame({'spy': spy_df['Close'], 'vix': vix_df['Close']}).dropna()
    
    results = []
    iterations = 400
    
    print(f"Simulating {iterations} random regimes (5-15 years)...")
    for _ in range(iterations):
        duration_years = random.uniform(5, 15)
        duration_days = int(duration_years * 252)
        start_idx = random.randint(0, len(df) - duration_days - 1)
        res = run_simulation(df, dna, dna['weights_p'], start_idx, start_idx + duration_days)
        results.append(res)
    
    rdf = pd.DataFrame(results)
    
    print("\n" + "="*50)
    print("      RESILIENCE MATRIX: THE BOT VS THE MARKET")
    print("="*50)
    print(f"{'Metric':<15} | {'THE BOT':<10} | {'1x SPY':<8} | {'2x SSO':<8} | {'3x UPRO':<8}")
    print("-" * 50)
    print(f"{'Mean CAGR':<15} | {rdf['cagr'].mean()*100:>9.2f}% | {rdf['cagr_1x'].mean()*100:>7.2f}% | {rdf['cagr_2x'].mean()*100:>7.2f}% | {rdf['cagr_3x'].mean()*100:>7.2f}%")
    print(f"{'Median CAGR':<15} | {rdf['cagr'].median()*100:>9.2f}% | {rdf['cagr_1x'].median()*100:>7.2f}% | {rdf['cagr_2x'].median()*100:>7.2f}% | {rdf['cagr_3x'].median()*100:>7.2f}%")
    print(f"{'Mean Sharpe':<15} | {rdf['sharpe'].mean():>10.2f} | {'-':>8} | {'-':>8} | {'-':>8}")
    print(f"{'Median Sharpe':<15} | {rdf['sharpe'].median():>10.2f} | {'-':>8} | {'-':>8} | {'-':>8}")
    print("="*50)

if __name__ == "__main__":
    run_resilience_test()
