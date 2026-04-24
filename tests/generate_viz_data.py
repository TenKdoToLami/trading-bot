import pandas as pd
import numpy as np
import yfinance as yf
import json
import os

def run_realistic_backtest():
    print("Generating Realistic Backtest (1-Day Execution Lag)...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dna_path = os.path.join(script_dir, "..", "config", "strategy.json")
    with open(dna_path, "r") as f: dna = json.load(f)
    
    # Fetch Data
    spy_df = yf.download("SPY", start="1993-01-01", progress=False)
    vix_df = yf.download("^VIX", start="1993-01-01", progress=False)
    if isinstance(spy_df.columns, pd.MultiIndex): spy_df.columns = spy_df.columns.get_level_values(0)
    if isinstance(vix_df.columns, pd.MultiIndex): vix_df.columns = vix_df.columns.get_level_values(0)
    df = pd.DataFrame({'spy': spy_df['Close'], 'vix': vix_df['Close']}).dropna()
    
    spy = df['spy'].values
    vix = df['vix'].values
    returns = df['spy'].pct_change().fillna(0).values
    dates = df.index.strftime('%Y-%m-%d').tolist()
    
    # Sim State
    eq_bot = 1.0; eq_s1 = 1.0; eq_s2 = 1.0; eq_s3 = 1.0; eq_k = 1.0
    hist = []
    
    panic_mode = False; days_in_regime = 0; current_tier = 0; base_lockout = 0
    sma_period = dna['sma']; min_b_days = dna['min_b_days']; bounds_p = dna['bounds_p']
    weights_p = dna['weights_p']
    
    # STARTING WEIGHTS (Bull Mode)
    active_weights = [0.0, 1.0, 0.0] 
    ath_bot = 1.0

    for i in range(len(df)):
        # 1. APPLY RETURNS (Using weights decided YESTERDAY)
        daily_ret = returns[i]
        r_2x = (daily_ret * 2.0) - (0.0120/252)
        r_3x = (daily_ret * 3.0) - (0.0150/252)
        r_cash = (0.03/252)
        
        step_bot = (active_weights[0] * r_2x) + (active_weights[1] * r_3x) + (active_weights[2] * r_cash)
        eq_bot *= (1 + step_bot)
        eq_s1 *= (1 + daily_ret); eq_s2 *= (1 + r_2x); eq_s3 *= (1 + r_3x); eq_k *= (1 + r_cash)
        
        if eq_bot > ath_bot: ath_bot = eq_bot
        drawdown = (eq_bot - ath_bot) / ath_bot
        
        # 2. CALCULATE NEW SIGNAL (At the end of today)
        curr_spy = spy[i]; curr_vix = vix[i]
        sma_val = np.mean(spy[max(0, i-sma_period+1):i+1])
        sma_triggered = curr_spy < sma_val
        
        days_in_regime += 1
        if panic_mode:
            if not sma_triggered: panic_mode = False; days_in_regime = 0
        else:
            if sma_triggered and days_in_regime >= min_b_days: panic_mode = True; days_in_regime = 0
            
        target_tier = np.digitize(curr_vix, bounds_p) if panic_mode else 0
        if base_lockout > 0:
            base_lockout -= 1; target_tier = current_tier
        if target_tier != current_tier:
            if not panic_mode and target_tier == 0: base_lockout = 10
            current_tier = target_tier
            
        # 3. SET WEIGHTS FOR TOMORROW
        active_weights = weights_p[min(current_tier, len(weights_p)-1)] if panic_mode else [0.0, 1.0, 0.0]
        
        hist.append({
            "Date": dates[i],
            "bE": round(eq_bot, 4), "s1E": round(eq_s1, 4), "s2E": round(eq_s2, 4), "s3E": round(eq_s3, 4), "kE": round(eq_k, 4),
            "R": "P" if panic_mode else "B", "T": int(current_tier), "DD": round(drawdown, 4),
            "Price": round(float(curr_spy), 2), "SMA": round(float(sma_val), 2), "VIX": round(float(curr_vix), 2),
            "Reason": "SMA_BELOW" if sma_triggered else "STABLE"
        })

    # Export
    viz_dir = os.path.join(script_dir, "..", "visualizer")
    os.makedirs(viz_dir, exist_ok=True)
    with open(os.path.join(viz_dir, "data.js"), "w") as f:
        f.write("const MARKET_DATA = " + json.dumps(hist) + ";")
        
    print(f"Realistic data exported to visualizer/data.js")

if __name__ == "__main__":
    run_realistic_backtest()
