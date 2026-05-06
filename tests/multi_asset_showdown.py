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

def run_showdown(tickers=["VT", "ACWI", "VGK", "DBC", "EEM"]):
    print(f"\n=== MULTI-ASSET SHOWDOWN: V14 NAS PORTABILITY ===\n")
    
    if not os.path.exists(CACHE_FILE):
        print(f"Error: {CACHE_FILE} not found.")
        return
    
    master_df = pd.read_csv(CACHE_FILE, index_col=0, parse_dates=True)
    
    # Load V14 NAS Champion
    champ_path = "champions/v14_nas/genome.json"
    with open(champ_path, 'r') as f:
        genome = json.load(f)
    
    summary_results = []
    
    for ticker in tickers:
        print(f"Testing {ticker}...")
        try:
            # 1. Download Ticker Data
            raw = yf.download(ticker, start="2008-01-01", progress=False)
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)
            
            if raw.empty:
                print(f"  [SKIP] No data for {ticker}")
                continue
            
            # 2. Merge with Signals
            df = master_df.copy()
            df = df.loc[df.index.intersection(raw.index)]
            raw = raw.loc[df.index]
            
            df['open'] = raw['Open']
            df['high'] = raw['High']
            df['low'] = raw['Low']
            df['close'] = raw['Close']
            df['volume'] = raw['Volume']
            df['spy_close'] = df['close']
            
            price_list = df.to_dict('records')
            dates = df.index
            
            # 3. Run V14 NAS
            res_nas = _execute_simulation(GenomeV14NAS, price_list, dates, {'genome': genome}, warmup_days=500)
            m_nas = res_nas['metrics']
            
            # 4. Run B&H 1x Baseline
            res_bh = _execute_simulation(BuyAndHoldSpy, price_list, dates, {}, warmup_days=500)
            m_bh = res_bh['metrics']
            
            summary_results.append({
                "Ticker": ticker,
                "Period": f"{dates[0].year}-{dates[-1].year}",
                "V14_CAGR": m_nas['cagr'] * 100,
                "V14_Sharpe": m_nas['sharpe'],
                "V14_MaxDD": m_nas['max_dd'] * 100,
                "BH_CAGR": m_bh['cagr'] * 100,
                "BH_MaxDD": m_bh['max_dd'] * 100,
                "Alpha": (m_nas['cagr'] - m_bh['cagr']) * 100
            })
            print(f"  Done: Alpha vs B&H: {summary_results[-1]['Alpha']:+.2f}%")
            
        except Exception as e:
            print(f"  [ERROR] {ticker}: {e}")
            
    # 5. Output Summary Table
    print("\n" + "="*105)
    print(f"  FINAL SHOWDOWN: V14 NAS vs BUY & HOLD (CROSS-ASSET)")
    print("="*105)
    header = f"{'Asset':<8} | {'Period':<10} | {'V14 CAGR':>10} | {'V14 Shrp':>10} | {'V14 DD':>10} | {'B&H CAGR':>10} | {'B&H DD':>10} | {'Alpha':>8}"
    print(header)
    print("-" * 105)
    
    for r in summary_results:
        print(f"{r['Ticker']:<8} | {r['Period']:<10} | {r['V14_CAGR']:>9.2f}% | {r['V14_Sharpe']:>10.2f} | {r['V14_MaxDD']:>9.1f}% | {r['BH_CAGR']:>9.2f}% | {r['BH_MaxDD']:>9.1f}% | {r['Alpha']:>7.2f}%")
    
    print("="*105)
    print("\n[Audit] V14 NAS utilizes SPX-trained macro signals. Alpha represents strategy value-add on the target asset.")

if __name__ == "__main__":
    run_showdown()
