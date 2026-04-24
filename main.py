import os
import sys
import datetime
import yfinance as yf
from src.utils.db import BotDB
from src.core.engine import StrategyEngine
from src.core.manager import BotManager
from src.execution.alpaca import AlpacaClient

def run_daily_sync():
    print(f"\n--- BOT SYNC: {datetime.date.today()} ---")
    
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dna_path = os.path.join(script_dir, "config", "strategy.json")
    
    db = BotDB()
    engine = StrategyEngine(dna_path=dna_path)
    manager = BotManager(db, engine)
    
    # 1. Fetch Latest Data
    print("Fetching latest SPY and VIX data...")
    spy_data = yf.download("SPY", period="5d", interval="1d")
    vix_data = yf.download("^VIX", period="5d", interval="1d")
    
    if spy_data.empty or vix_data.empty:
        print("Error: Could not fetch market data.")
        return

    # Add last closed day to DB
    last_date = spy_data.index[-1].strftime('%Y-%m-%d')
    last_price = float(spy_data['Close'].iloc[-1])
    last_vix = float(vix_data['Close'].iloc[-1])
    
    db.add_daily_data(last_date, last_price, last_vix)
    print(f"Market Close Data: SPY ${last_price:.2f}, VIX {last_vix:.2f}")

    # 2. Run Strategy Logic
    history = db.get_history(limit=1000)
    result = manager.process_day(history)
    
    print(f"Target State: {result['regime'].upper()} Tier {result['tier']}")
    print(f"Target Weights: {result['weights']}")

    # 3. Execution
    if result['changed']:
        print("ALERT: Tier Change Detected. Rebalancing Portfolio...")
        alpaca = AlpacaClient()
        
        # Safety Check: Min Balance
        min_balance = float(os.getenv('MIN_REMAINING_BALANCE', 500))
        current_equity = alpaca.get_equity()
        
        if current_equity < min_balance:
            print(f"CRITICAL: Equity (${current_equity:.2f}) below minimum (${min_balance:.2f}). Rebalance aborted.")
            return
            
        alpaca.rebalance(result['weights'])
        print("Portfolio Rebalanced Successfully.")
    else:
        print("No Tier Change. Holding positions.")

if __name__ == "__main__":
    run_daily_sync()
