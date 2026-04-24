import os
import sys
import datetime
import argparse
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from src.utils.db import BotDB
from src.core.engine import StrategyEngine
from src.core.manager import BotManager
from src.execution.alpaca import AlpacaClient

# Load configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, "config", ".env")
load_dotenv(dotenv_path=env_path)

def backfill_data(db, ticker, required_days):
    """Downloads and stores historical data if DB is empty/insufficient."""
    print(f"Insufficent local data. Backfilling {required_days} days for {ticker}...")
    try:
        # Fetch slightly more to be safe
        df = yf.download(ticker, period="2y", interval="1d")
        if df.empty:
            if ticker != "SPY":
                return backfill_data(db, "SPY", required_days)
            return
            
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        count = 0
        for date, row in df.iterrows():
            date_str = date.strftime('%Y-%m-%d')
            # VIX isn't in this DF, we'll fetch it separately or just use 20.0 as filler for historicals
            db.add_daily_data(date_str, float(row['Close']), 20.0)
            count += 1
        print(f"Backfilled {count} historical days.")
    except Exception as e:
        print(f"Backfill failed: {e}")

def run_daily_sync(dry_run=False):
    print(f"\n--- BOT SYNC: {datetime.datetime.now()} {'[DRY RUN]' if dry_run else ''} ---")
    
    db = BotDB()
    alpaca = AlpacaClient()
    
    if not dry_run and not alpaca.is_market_open():
        print("ABORTED: Market is currently CLOSED.")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    dna_path = os.path.join(script_dir, "config", "strategy.json")
    engine = StrategyEngine(dna_path=dna_path)
    manager = BotManager(db, engine)
    
    # 0. Data Readiness Check (SMA Backfill)
    history_count = len(db.get_history(limit=2000))
    required = engine.dna.get('sma', 291) + 10
    if history_count < required:
        backfill_data(db, alpaca.signal_ticker, required)

    # 1. Fetch Latest Data
    signal_ticker = alpaca.signal_ticker
    print(f"Fetching data for signal: {signal_ticker} and VIX...")
    
    spy_data = yf.download(signal_ticker, period="5d", interval="1d")
    vix_data = yf.download("^VIX", period="5d", interval="1d")
    
    if spy_data.empty or vix_data.empty:
        print("Error: Could not fetch market data.")
        return

    if isinstance(spy_data.columns, pd.MultiIndex): spy_data.columns = spy_data.columns.get_level_values(0)
    if isinstance(vix_data.columns, pd.MultiIndex): vix_data.columns = vix_data.columns.get_level_values(0)

    last_date = spy_data.index[-1].strftime('%Y-%m-%d')
    last_price = float(spy_data['Close'].iloc[-1])
    last_vix = float(vix_data['Close'].iloc[-1])
    
    db.add_daily_data(last_date, last_price, last_vix)
    print(f"Market Close Data: {signal_ticker} ${last_price:.2f}, VIX {last_vix:.2f}")

    # 2. Run Strategy Logic
    history = db.get_history(limit=1000)
    result = manager.process_day(history)
    
    print(f"Calculated State: {result['regime'].upper()} Tier {result['tier']}")
    print(f"Target Weights: {result['weights']}")

    if dry_run:
        print("[DRY RUN] Finished.")
        return

    # 3. Execution
    if result['changed']:
        print(">>> STATE CHANGE: Rebalancing...")
        alpaca.rebalance(result['weights'])
        alpaca.verify_rebalance()
    else:
        print(">>> STATE UNCHANGED: Checking cash...")
        alpaca.invest_excess_cash(result['weights'])
        print("Sync complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Tactical Bot Sync')
    parser.add_argument('--dry-run', action='store_true', help='Preview logic without trading')
    args = parser.parse_args()
    run_daily_sync(dry_run=args.dry_run)
