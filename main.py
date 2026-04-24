import os
import sys
import datetime
import argparse
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

def run_daily_sync(dry_run=False):
    print(f"\n--- BOT SYNC: {datetime.date.today()} {'[DRY RUN]' if dry_run else ''} ---")
    
    # 0. Initialize Clients
    db = BotDB()
    alpaca = AlpacaClient()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dna_path = os.path.join(script_dir, "config", "strategy.json")
    engine = StrategyEngine(dna_path=dna_path)
    manager = BotManager(db, engine)
    
    # 1. Fetch Latest Data
    signal_ticker = alpaca.signal_ticker
    print(f"Fetching data for signal: {signal_ticker} and VIX...")
    
    spy_data = yf.download(signal_ticker, period="5d", interval="1d")
    vix_data = yf.download("^VIX", period="5d", interval="1d")
    
    if spy_data.empty or vix_data.empty:
        print("Error: Could not fetch market data.")
        return

    last_date = spy_data.index[-1].strftime('%Y-%m-%d')
    last_price = float(spy_data['Close'].iloc[-1])
    last_vix = float(vix_data['Close'].iloc[-1])
    
    db.add_daily_data(last_date, last_price, last_vix)
    print(f"Market Close Data: {signal_ticker} ${last_price:.2f}, VIX {last_vix:.2f}")

    # 2. Run Strategy Logic
    history = db.get_history(limit=1000)
    result = manager.process_day(history)
    
    print(f"Target State: {result['regime'].upper()} Tier {result['tier']}")
    print(f"Target Weights: {result['weights']}")

    # 3. Execution
    if result['changed']:
        print("ALERT: Tier Change Detected.")
        
        if dry_run:
            print("[DRY RUN] Would orchestrate rebalance now.")
            return

        # Market Open Check
        if not alpaca.is_market_open():
            print("WARNING: Market is currently CLOSED. Rebalance deferred until market open.")
            return
            
        # Safety Check: Min Balance
        min_balance = float(os.getenv('MIN_REMAINING_BALANCE', 500))
        current_equity = alpaca.get_equity()
        
        if current_equity < min_balance:
            print(f"CRITICAL: Equity (${current_equity:.2f}) below minimum (${min_balance:.2f}). Aborted.")
            return
            
        print("Orchestrating Rebalance...")
        alpaca.rebalance(result['weights'])
        print("Rebalance Cycle Complete.")
    else:
        print("Status: Equilibrium. No trades required.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Tactical Bot Sync')
    parser.add_argument('--dry-run', action='store_true', help='Preview logic without trading')
    args = parser.parse_args()
    
    run_daily_sync(dry_run=args.dry_run)
