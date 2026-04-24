import pandas as pd
import numpy as np
import yfinance as yf
import json
import os
from datetime import datetime

def run_audit():
    print("\n" + "="*60)
    print("       STRATEGY PERFORMANCE AUDIT (30-YEAR HIGH FIDELITY)")
    print("="*60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dna_path = os.path.join(script_dir, "..", "config", "strategy.json")
    with open(dna_path, "r") as f: dna = json.load(f)
    
    # Data Fetching
    print("Fetching historical data...")
    spy_df = yf.download("SPY", start="1993-01-01", progress=False)
    vix_df = yf.download("^VIX", start="1993-01-01", progress=False)
    
    if isinstance(spy_df.columns, pd.MultiIndex): spy_df.columns = spy_df.columns.get_level_values(0)
    if isinstance(vix_df.columns, pd.MultiIndex): vix_df.columns = vix_df.columns.get_level_values(0)
    
    # EXACT SAME CLEANING AS VISUALIZER
    df = pd.DataFrame({'spy': spy_df['Close'], 'vix': vix_df['Close']}).dropna()
    
    returns = df['spy'].pct_change().fillna(0).values
    spy_prices = df['spy'].values
    vix = df['vix'].values
    dates = df.index
    n = len(df)
    # Strategy Parameters
    sma_period = dna['sma']
    min_b_days = dna['min_b_days']
    bounds_p = dna['bounds_p']
    weights_p = dna['weights_p']
    
    results = {
        'Bot': np.ones(n),
        '1x (VOO)': np.ones(n),
        '2x (SSO)': np.ones(n),
        '3x (UPRO)': np.ones(n)
    }
    
    panic_mode = False; days_in_regime = 0; current_tier = 0; base_lockout = 0
    active_weights = [0.0, 1.0, 0.0] # Start in Bull (3x)

    # Simulation Loop (1-Day Execution Lag)
    for i in range(1, n):
        # A. Apply returns based on YESTERDAY'S decision
        daily_ret = returns[i]
        r_2x = (daily_ret * 2.0) - (0.0120/252)
        r_3x = (daily_ret * 3.0) - (0.0150/252)
        r_cash = (0.03/252)
        
        # Update Benchmarks
        results['1x (VOO)'][i] = results['1x (VOO)'][i-1] * (1 + daily_ret)
        results['2x (SSO)'][i] = results['2x (SSO)'][i-1] * (1 + r_2x)
        results['3x (UPRO)'][i] = results['3x (UPRO)'][i-1] * (1 + r_3x)
        
        # Update Bot
        step_bot = (active_weights[0] * r_2x) + (active_weights[1] * r_3x) + (active_weights[2] * r_cash)
        results['Bot'][i] = results['Bot'][i-1] * (1 + step_bot)

        # B. Calculate Signal for TOMORROW
        sma_val = np.mean(spy_prices[max(0, i-sma_period+1):i+1])
        sma_triggered = spy_prices[i] < sma_val
        
        days_in_regime += 1
        if panic_mode:
            if not sma_triggered: panic_mode = False; days_in_regime = 0
        else:
            if sma_triggered and days_in_regime >= min_b_days: panic_mode = True; days_in_regime = 0
            
        target_tier = np.digitize(vix[i], bounds_p) if panic_mode else 0
        if base_lockout > 0:
            base_lockout -= 1; target_tier = current_tier
        if target_tier != current_tier:
            if not panic_mode and target_tier == 0: base_lockout = 10
            current_tier = target_tier
            
        active_weights = weights_p[min(current_tier, len(weights_p)-1)] if panic_mode else [0.0, 1.0, 0.0]

    # Metrics Calculation
    audit_data = []
    years = (dates[-1] - dates[0]).days / 365.25

    for name, equity in results.items():
        total_ret = (equity[-1] / equity[0]) - 1
        cagr = (equity[-1] / equity[0])**(1/years) - 1
        
        daily_returns = pd.Series(equity).pct_change().dropna()
        vol = daily_returns.std() * np.sqrt(252)
        sharpe = (cagr - 0.03) / vol if vol != 0 else 0
        
        # Max Drawdown
        peaks = pd.Series(equity).expanding().max()
        dd = (pd.Series(equity) - peaks) / peaks
        max_dd = dd.min()
        
        audit_data.append({
            "Asset": name,
            "Total Ret": f"{total_ret*100:,.0f}%",
            "CAGR": f"{cagr*100:.2f}%",
            "Max DD": f"{max_dd*100:.1f}%",
            "Sharpe": f"{sharpe:.2f}",
            "Vol": f"{vol*100:.1f}%",
            "Daily Avg": f"{daily_returns.mean()*100:.3f}%",
            "Daily Med": f"{daily_returns.median()*100:.3f}%"
        })

    # Display Table
    df_audit = pd.DataFrame(audit_data)
    print("\nAudit Results (1993 - Present):")
    print("-" * 110)
    print(f"{'Asset':<12} | {'Total':>10} | {'CAGR':>8} | {'Max DD':>8} | {'Sharpe':>7} | {'Vol':>7} | {'Avg Day':>8} | {'Med Day':>8}")
    print("-" * 110)
    for row in audit_data:
        print(f"{row['Asset']:<12} | {row['Total Ret']:>10} | {row['CAGR']:>8} | {row['Max DD']:>8} | {row['Sharpe']:>7} | {row['Vol']:>7} | {row['Daily Avg']:>8} | {row['Daily Med']:>8}")
    print("-" * 110)
    
    # Calculate Alpha
    bot_cagr = float(audit_data[0]['CAGR'].replace('%',''))
    spy_cagr = float(audit_data[1]['CAGR'].replace('%',''))
    print(f"\nNet Excess Alpha vs 1x: {bot_cagr - spy_cagr:+.2f}% per year")
    print(f"Risk-Adjusted Outperformance: Bot Sharpe ({audit_data[0]['Sharpe']}) vs 3x Sharpe ({audit_data[3]['Sharpe']})")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_audit()
