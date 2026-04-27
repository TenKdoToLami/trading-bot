"""
Institutional Performance Audit.
Produces a bit-perfect terminal table of monthly/yearly returns
and core risk metrics for any specific strategy or genome.
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.dirname(__file__))

from utils import resolve_strategy
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data

def run_audit(identifier: str):
    try:
        strategy = resolve_strategy(identifier)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Loading market data...")
    data = load_spy_data("1993-01-01")
    price_data_list = data[['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve']].to_dict('records')
    dates = data.index

    print(f"Auditing {strategy.NAME}...")
    res = _execute_simulation(
        strategy_type=strategy.__class__,
        price_data_list=price_data_list,
        dates=dates,
        strategy_kwargs={'genome': getattr(strategy, 'genome', None)} if hasattr(strategy, 'genome') else {}
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
    LEV_MAP = {"SPY": 1.0, "2xSPY": 2.0, "3xSPY": 3.0, "CASH": 0.0}
    residency = {0.0: 0, 1.0: 0, 2.0: 0, 3.0: 0}
    for _, holdings in holdings_log:
        dom = max(holdings, key=holdings.get)
        lev = LEV_MAP.get(dom, 0.0)
        residency[lev] += 1
    
    total_days = len(holdings_log)
    
    # ── Yearly Returns ──
    yearly = df['equity'].resample('YE').last().pct_change()
    
    print("\n" + "="*70)
    print(f"  INSTITUTIONAL AUDIT: {strategy.NAME}")
    print(f"  Class: {strategy.__class__.__name__}")
    print("="*70)
    
    # Core Stats
    print(f"  CAGR:          {metrics['cagr']*100:>12.2f}%")
    print(f"  Max Drawdown:  {metrics['max_dd']*100:>12.2f}%")
    print(f"  Sharpe Ratio:  {metrics['sharpe']:>12.2f}")
    print(f"  Volatility:    {metrics['volatility']*100:>12.2f}%")
    print(f"  Avg Leverage:  {metrics['avg_leverage']:>12.2f}x")
    
    # Leverage Residency Table
    print("\n  " + "-"*66)
    print(f"  LEVERAGE RESIDENCY")
    print("  " + "-"*66)
    for lev, days in residency.items():
        pct = (days / total_days) * 100
        bar = "#" * int(pct / 2)
        print(f"  {lev:>3.0f}x Leverage:  {days:>8,} days | {pct:>6.1f}%  {bar}")
    
    # Yearly Returns Table
    print("\n  " + "-"*66)
    print(f"  YEARLY PERFORMANCE")
    print("  " + "-"*66)
    
    yearly_items = list(yearly.items())
    for i in range(0, len(yearly_items), 3):
        chunk = yearly_items[i:i+3]
        line = ""
        for yr, ret in chunk:
            if not np.isnan(ret):
                line += f"  {yr.year}: {ret*100:>8.2f}%   |"
        print(line)
        
    print("="*70 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("strategy", type=str, help="Path to genome JSON or Strategy Name")
    args = parser.parse_args()

    run_audit(args.strategy)
