import os
import sys
import datetime
import argparse
import pandas as pd
import yfinance as yf
import logging
from dotenv import load_dotenv
from src.utils.db import BotDB
from src.core.engine import StrategyEngine
from src.core.manager import BotManager
from src.execution.alpaca import AlpacaClient

# 1. Setup Logging
script_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(script_dir, "logs")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "sync.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load configuration
env_path = os.path.join(script_dir, "config", ".env")
load_dotenv(dotenv_path=env_path)

def backfill_data(db, ticker, required_days):
    logger.info(f"Insufficent local data. Backfilling {required_days} days for {ticker}...")
    try:
        df = yf.download(ticker, period="2y", interval="1d", progress=False)
        if df.empty:
            if ticker != "SPY": return backfill_data(db, "SPY", required_days)
            return
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        count = 0
        for date, row in df.iterrows():
            db.add_daily_data(date.strftime('%Y-%m-%d'), float(row['Close']), 20.0)
            count += 1
        logger.info(f"Backfilled {count} historical days.")
    except Exception as e:
        logger.error(f"Backfill failed: {e}")

def run_daily_sync(dry_run=False):
    logger.info("=" * 80) # Start of new entry
    logger.info(f"--- BOT SYNC START {'[DRY RUN]' if dry_run else ''} ---")
    
    db = BotDB()
    alpaca = AlpacaClient()
    
    if not dry_run and not alpaca.is_market_open():
        logger.warning("ABORTED: Market is currently CLOSED.")
        return

    dna_path = os.path.join(script_dir, "config", "strategy.json")
    engine = StrategyEngine(dna_path=dna_path)
    manager = BotManager(db, engine)
    
    # 0. Data Readiness Check
    history_count = len(db.get_history(limit=2000))
    required = engine.dna.get('sma', 291) + 10
    if history_count < required:
        backfill_data(db, alpaca.signal_ticker, required)

    # 1. Fetch Latest Data
    signal_ticker = alpaca.signal_ticker
    logger.info(f"Fetching market data for {signal_ticker} and ^VIX...")
    
    spy_data = yf.download(signal_ticker, period="5d", interval="1d", progress=False)
    vix_data = yf.download("^VIX", period="5d", interval="1d", progress=False)
    
    if spy_data.empty or vix_data.empty:
        logger.error("Could not fetch market data from yfinance.")
        return

    if isinstance(spy_data.columns, pd.MultiIndex): spy_data.columns = spy_data.columns.get_level_values(0)
    if isinstance(vix_data.columns, pd.MultiIndex): vix_data.columns = vix_data.columns.get_level_values(0)

    last_date = spy_data.index[-1].strftime('%Y-%m-%d')
    last_price = float(spy_data['Close'].iloc[-1])
    last_vix = float(vix_data['Close'].iloc[-1])
    
    db.add_daily_data(last_date, last_price, last_vix)
    logger.info(f"Market Close: {signal_ticker} @ ${last_price:.2f}, VIX @ {last_vix:.2f}")

    # 2. Run Strategy Logic
    history = db.get_history(limit=1000)
    result = manager.process_day(history)
    
    logger.info(f"Strategy Result: {result['regime'].upper()} | Tier {result['tier']} | Weights {result['weights']}")

    if dry_run:
        logger.info("[DRY RUN] Simulation complete. No trades placed.")
        return

    # 3. Execution
    if result['changed']:
        logger.info(">>> STATE CHANGE DETECTED. Starting rebalance...")
        min_balance = float(os.getenv('MIN_REMAINING_BALANCE', 20))
        if alpaca.get_equity() < min_balance:
            logger.error(f"Equity below minimum (${min_balance}). Trade Aborted.")
            return
            
        alpaca.rebalance(result['weights'])
        alpaca.verify_rebalance()
        logger.info("Rebalance verified and complete.")
    else:
        logger.info(">>> STATE UNCHANGED. Running excess cash sweep...")
        alpaca.invest_excess_cash(result['weights'])
        logger.info("Sync complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Tactical Bot Sync')
    parser.add_argument('--dry-run', action='store_true', help='Preview logic without trading')
    args = parser.parse_args()
    
    try:
        run_daily_sync(dry_run=args.dry_run)
    except Exception as e:
        logger.exception(f"FATAL ERROR during sync: {e}")
