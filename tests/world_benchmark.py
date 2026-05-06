import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import pandas as pd
import numpy as np
import yfinance as yf
from src.helpers.data_provider import CACHE_FILE
from src.tournament.runner import _execute_simulation
from strategies.genome_v14_nas import GenomeV14NAS
from strategies.buy_and_hold_spy import BuyAndHoldSpy
from strategies.buy_and_hold_2x import BuyAndHold2x
from strategies.buy_and_hold_3x import BuyAndHold3x

def run_world_benchmark(ticker="VT", start_date="2008-01-01"):
    print(f"\n=== WORLD BENCHMARK: {ticker} vs V14 NAS ===")
    
    # 1. Load Macro Signals from Master Cache
    if not os.path.exists(CACHE_FILE):
        print(f"Error: {CACHE_FILE} not found. Run a standard tournament first to populate signals.")
        return
    
    master_df = pd.read_csv(CACHE_FILE, index_col=0, parse_dates=True)
    
    # 2. Download World ETF Data
    print(f"Downloading {ticker} data since {start_date}...")
    world_raw = yf.download(ticker, start=start_date, progress=False)
    if isinstance(world_raw.columns, pd.MultiIndex):
        world_raw.columns = world_raw.columns.get_level_values(0)
    
    if world_raw.empty:
        print(f"Error: No data found for {ticker}")
        return
    
    # 3. Merge World Price with Master Signals
    # We replace 'open', 'high', 'low', 'close', 'volume' with World ETF data
    # but keep macro signals (vix, yield_curve, etc.) from SPX history
    df = master_df.copy()
    
    # Align dates
    df = df.loc[df.index.intersection(world_raw.index)]
    world_raw = world_raw.loc[df.index]
    
    df['open'] = world_raw['Open']
    df['high'] = world_raw['High']
    df['low'] = world_raw['Low']
    df['close'] = world_raw['Close']
    df['volume'] = world_raw['Volume']
    
    # Crucially, update 'spy_close' to be the World ETF close for the Portfolio logic
    # (The runner uses 'open'/'close' for returns, but some metrics might look at spy_close)
    df['spy_close'] = df['close']
    
    print(f"Merged {len(df)} days of aligned data.")
    
    price_data_list = df.to_dict('records')
    dates = df.index
    
    # 4. Load V14 NAS Champion
    champ_path = "champions/v14_nas/genome.json"
    if not os.path.exists(champ_path):
        print(f"Error: Champion {champ_path} not found.")
        return
    
    with open(champ_path, 'r') as f:
        genome = json.load(f)
    
    # 5. Execute Simulations
    benchmarks = [
        ("V14 NAS (World)", GenomeV14NAS, {'genome': genome}),
        (f"B&H 1x ({ticker})", BuyAndHoldSpy, {}),
        (f"B&H 2x ({ticker})", BuyAndHold2x, {}),
        (f"B&H 3x ({ticker})", BuyAndHold3x, {}),
    ]
    
    results = []
    for name, strat_cls, kwargs in benchmarks:
        print(f"  Running {name}...")
        res = _execute_simulation(
            strategy_type=strat_cls,
            price_data_list=price_data_list,
            dates=dates,
            strategy_kwargs=kwargs,
            warmup_days=500
        )
        m = res['metrics']
        results.append({
            "Name": name,
            "CAGR": m['cagr'] * 100,
            "Sharpe": m['sharpe'],
            "MaxDD": m['max_dd'] * 100,
            "Vol": m['volatility'] * 100,
            "Mult": m['multiplier']
        })
    
    # 6. Print Comparison Table
    print("\n" + "="*85)
    print(f"  WORLD BENCHMARK RESULTS: {ticker} (Period: {dates[0].date()} -> {dates[-1].date()})")
    print("="*85)
    print(f"  {'Strategy':<25} | {'CAGR':>8} | {'Sharpe':>8} | {'Max DD':>8} | {'Multiplier':>10}")
    print("-" * 85)
    for r in sorted(results, key=lambda x: x['CAGR'], reverse=True):
        print(f"  {r['Name']:<25} | {r['CAGR']:>7.2f}% | {r['Sharpe']:>8.2f} | {r['MaxDD']:>7.1f}% | {r['Mult']:>9.1f}x")
    print("="*85)
    print("\n[Note] V14 NAS used SPX-trained signals but traded World ETF prices.")
    print("[Note] 2x/3x B&H are simulated with daily rebalancing on the base ETF.")

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "VT"
    run_world_benchmark(ticker=ticker)
