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

def dominant_holding(holdings: dict, leverage_map: dict) -> str:
    if not holdings: return "CASH"
    # Prioritize higher leverage tiers if weights are equal
    return max(holdings, key=lambda k: (holdings[k], abs(leverage_map.get(k, 0.0))))

def run_audit(identifier: str, slippage_bps: float = 0.0005, commission_bps: float = 0.0001):
    try:
        strategy = resolve_strategy(identifier)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print("Loading market data...")
    data = load_spy_data("1993-01-01")
    
    cols = ['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve', 
            'credit_spread', 'month_sin', 'month_cos', 'is_tom', 
            'tlt_proxy', 'shy_proxy', 'gold']
            
    # Ensure columns exist before converting
    existing_cols = [c for c in cols if c in data.columns]
    price_data_list = data[existing_cols].to_dict('records')
    dates = data.index

    print(f"Auditing {strategy.NAME}...")
    res = _execute_simulation(
        strategy_type=strategy.__class__,
        price_data_list=price_data_list,
        dates=dates,
        strategy_kwargs={'genome': getattr(strategy, 'genome', None)} if hasattr(strategy, 'genome') else {},
        slippage_bps=slippage_bps,
        commission_bps=commission_bps
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
    
    # ── Effective Leverage Distribution ──
    LEVERAGE_MAP = {
        "SPY": 1.0, "2xSPY": 2.0, "3xSPY": 3.0, "CASH": 0.0,
        "TLT": 1.0, "SHY": 1.0, "GOLD": 1.0, 
        "SHORT_SPY": -1.0, "2xSHORT_SPY": -2.0, "3xSHORT_SPY": -3.0
    }
    TIER_ORDER = ["3xSPY", "2xSPY", "SPY", "CASH", "GOLD", "TLT", "SHY", "SHORT_SPY", "2xSHORT_SPY", "3xSHORT_SPY"]
    
    daily_levs = []
    symbol_days = {t: 0 for t in TIER_ORDER}
    symbol_exposure = {t: 0.0 for t in TIER_ORDER}
    
    for _, holdings in holdings_log:
        day_lev = sum(holdings.get(a, 0.0) * LEVERAGE_MAP.get(a, 0.0) for a in LEVERAGE_MAP)
        daily_levs.append(day_lev)
        
        dom = dominant_holding(holdings, LEVERAGE_MAP)
        if dom in symbol_days:
            symbol_days[dom] += 1
        else:
            symbol_days[dom] = symbol_days.get(dom, 0) + 1
            
        for asset, weight in holdings.items():
            if asset in symbol_exposure:
                symbol_exposure[asset] += weight
    
    lev_arr = np.array(daily_levs)
    lev_residency = {
        "3x+ (UPRO)":  np.sum(lev_arr > 2.1),
        "2x (SSO)":    np.sum((lev_arr > 1.1) & (lev_arr <= 2.1)),
        "1x (SPY)":    np.sum((lev_arr > 0.01) & (lev_arr <= 1.1)),
        "0x (Cash)":   np.sum((lev_arr >= -0.01) & (lev_arr <= 0.01)),
        "Defensive":   np.sum(lev_arr < -0.01),
    }
    
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
    print(f"  LEVERAGE RESIDENCY (By Net Exposure)")
    print("  " + "-"*66)
    for label, days in lev_residency.items():
        pct = (days / total_days) * 100
        bar = "#" * int(pct / 2)
        print(f"  {label:<15}: {days:>8,} days | {pct:>6.1f}%  {bar}")
        
    # Symbol Residency Table
    print("\n  " + "-"*66)
    print(f"  SYMBOL RESIDENCY (By Dominant Asset)")
    print("  " + "-"*66)
    for tier in TIER_ORDER:
        days = symbol_days.get(tier, 0)
        if days == 0: continue
        pct = (days / total_days) * 100
        bar = "#" * int(pct / 2)
        print(f"  {tier:<15}: {days:>8,} days | {pct:>6.1f}%  {bar}")
        
    # Exposure Summary (Average Weights)
    print("\n  " + "-"*66)
    print(f"  EXPOSURE SUMMARY (Average Weights)")
    print("  " + "-"*66)
    for tier in TIER_ORDER:
        total_weight = symbol_exposure.get(tier, 0.0)
        avg_weight_pct = (total_weight / total_days) * 100
        if avg_weight_pct < 0.1: continue
        bar = "█" * int(avg_weight_pct / 2)
        print(f"  {tier:<15}: {avg_weight_pct:>15.1f}%  {bar}")
    
    # Yearly Returns Table
    print("\n  " + "-"*66)
    print(f"  YEARLY PERFORMANCE")
    print("  " + "-"*66)
    
    V9_FEATURES = ['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve', 'credit_spread', 'month_sin', 'month_cos', 'is_tom', 'tlt_proxy', 'shy_proxy', 'gold']
    importance = {}
    if hasattr(strategy, 'genome') and strategy.genome:
        genome = strategy.genome
        v_num = float(genome.get('version', 1.0))
        if v_num >= 13.0: # V13 MOE Pro
            for brain_key in ['sentinel', 'bull_expert', 'bear_expert']:
                if brain_key in genome:
                    w = np.array(genome[brain_key]['w'])
                    scores = np.sum(np.abs(w), axis=1)
                    for i, score in enumerate(scores):
                        name = V9_FEATURES[i] if i < len(V9_FEATURES) else f"Input_{i}"
                        importance[name] = importance.get(name, 0) + score
        elif v_num >= 7.0: # Neural (V7, V9)
            w1 = np.array(genome['layers'][0]['w'])
            scores = np.sum(np.abs(w1), axis=1)
            for i, score in enumerate(scores):
                name = V9_FEATURES[i] if i < len(V9_FEATURES) else f"Input_{i}"
                importance[name] = score
    
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
    parser.add_argument("--slippage", type=float, default=0.0005, help="Slippage bps (e.g. 0.0005 = 5bps)")
    parser.add_argument("--commission", type=float, default=0.0001, help="Commission bps (e.g. 0.0001 = 1bps)")
    args = parser.parse_args()

    run_audit(args.strategy, slippage_bps=args.slippage, commission_bps=args.commission)
