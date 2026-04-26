"""
Institutional Performance Audit.
Produces a bit-perfect terminal table of monthly/yearly returns
and core risk metrics for a specific genome.
"""

import argparse
import json
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from strategies._genome_strategy import GenomeStrategy
from strategies.genome_v2_strategy import GenomeV2Strategy
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data

def run_audit(genome_path: str, is_v2: bool):
    with open(genome_path, 'r') as f:
        genome = json.load(f)

    strat_type = GenomeV2Strategy if is_v2 else GenomeStrategy
    
    print(f"Loading market data...")
    data = load_spy_data("1993-01-01")
    price_data_list = data[['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve']].to_dict('records')
    dates = data.index

    print(f"Auditing {os.path.basename(genome_path)}...")
    res = _execute_simulation(
        strategy_type=strat_type,
        price_data_list=price_data_list,
        dates=dates,
        strategy_kwargs={'genome': genome}
    )

    metrics = res['metrics']
    portfolio = res['portfolio']
    equity_curve = portfolio.equity_curve
    holdings_log = portfolio.holdings_log
    
    # ── Convert to DataFrame ──
    df = pd.DataFrame(equity_curve, columns=['date', 'equity'])
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df['ret'] = df['equity'].pct_change()
    
    # ── Leverage Residency ──
    # Map assets to leverage
    LEV_MAP = {"SPY": 1.0, "2xSPY": 2.0, "3xSPY": 3.0, "CASH": 0.0}
    residency = {0.0: 0, 1.0: 0, 2.0: 0, 3.0: 0}
    for _, holdings in holdings_log:
        # Determine current leverage (dominant asset)
        dom = max(holdings, key=holdings.get)
        lev = LEV_MAP.get(dom, 0.0)
        residency[lev] += 1
    
    total_days = len(holdings_log)
    
    # ── Yearly Returns ──
    yearly = df['equity'].resample('YE').last().pct_change()
    
    print("\n" + "═"*70)
    print(f"  INSTITUTIONAL AUDIT: {os.path.basename(genome_path)}")
    print(f"  Architecture: {strat_type.NAME}")
    print("═"*70)
    
    # Core Stats
    print(f"  CAGR:          {metrics['cagr']*100:>12.2f}%")
    print(f"  Max Drawdown:  {metrics['max_dd']*100:>12.2f}%")
    print(f"  Sharpe Ratio:  {metrics['sharpe']:>12.2f}")
    print(f"  Volatility:    {metrics['volatility']*100:>12.2f}%")
    print(f"  Avg Leverage:  {metrics['avg_leverage']:>12.2f}x")
    
    # Leverage Residency Table
    print("\n  " + "─"*66)
    print(f"  LEVERAGE RESIDENCY")
    print("  " + "─"*66)
    for lev, days in residency.items():
        pct = (days / total_days) * 100
        bar = "█" * int(pct / 2)
        print(f"  {lev:>3.0f}x Leverage:  {days:>8,} days | {pct:>6.1f}%  {bar}")
    
    # Yearly Returns Table
    print("\n  " + "─"*66)
    print(f"  YEARLY PERFORMANCE")
    print("  " + "─"*66)
    
    yearly_items = list(yearly.items())
    # Print in 3 columns for compactness
    for i in range(0, len(yearly_items), 3):
        chunk = yearly_items[i:i+3]
        line = ""
        for yr, ret in chunk:
            if not np.isnan(ret):
                line += f"  {yr.year}: {ret*100:>8.2f}%   |"
        print(line)
        
    print("═"*70 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("genome", type=str, help="Path to genome JSON")
    parser.add_argument("--v2", action="store_true", help="Use Genome V2")
    args = parser.parse_args()

    genome_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', args.genome))
    run_audit(genome_path, args.v2)
