import os
import time
import logging
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Ensure .env is loaded from the config directory
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, "..", "..", "config", ".env")
load_dotenv(dotenv_path=env_path)

class AlpacaClient:
    def __init__(self):
        key = os.getenv('ALPACA_KEY')
        secret = os.getenv('ALPACA_SECRET')
        base_url = os.getenv('ALPACA_BASE_URL')
        
        if not key or not secret:
            raise ValueError("ALPACA_KEY and ALPACA_SECRET must be set in config/.env")

        self.api = tradeapi.REST(key, secret, base_url, api_version='v2')
        self.tickers = [
            os.getenv('TICKER_2X', 'SSO'),
            os.getenv('TICKER_3X', 'SPXL'),
            os.getenv('TICKER_CASH', 'SGOV')
        ]
        self.signal_ticker = os.getenv('TICKER_SIGNAL', 'VOO')

    def get_equity(self):
        return float(self.api.get_account().equity)

    def get_cash(self):
        return float(self.api.get_account().cash)

    def is_market_open(self):
        return self.api.get_clock().is_open

    def get_price(self, ticker):
        return float(self.api.get_latest_trade(ticker).price)

    def get_positions(self):
        positions = self.api.list_positions()
        return {p.symbol: float(p.qty) for p in positions if p.symbol in self.tickers}

    def sell_all(self, ticker):
        try:
            self.api.close_position(ticker)
            logger.info(f"Closed position for {ticker}")
            return True
        except:
            return False

    def buy_dollars(self, ticker, dollar_amount):
        min_order = float(os.getenv('MIN_ORDER_VALUE', 20))
        if dollar_amount < min_order:
            logger.warning(f"Order for {ticker} (${dollar_amount:.2f}) is below minimum (${min_order}). Skipping.")
            return False
            
        price = self.get_price(ticker)
        # Use 4 decimal places for fractional shares
        qty = round(dollar_amount / price, 4)
        
        if qty > 0:
            logger.info(f"Submitting order: BUY {qty} {ticker} (~${dollar_amount:.2f})")
            self.api.submit_order(
                symbol=ticker, 
                qty=qty, 
                side='buy',
                type='market', 
                time_in_force='day'
            )
            return True
        return False

    def liquidate_managed_assets(self):
        logger.info("Executing tactical liquidation of managed assets...")
        for ticker in self.tickers:
            self.sell_all(ticker)
        time.sleep(5)

    def verify_rebalance(self):
        logger.info("Waiting 60s for order settlement verification...")
        time.sleep(60)
        pos = self.get_positions()
        if pos:
            logger.info(f"Verification Success. Current Managed Holdings: {pos}")
        else:
            logger.warning("Verification Warning: No managed positions detected after rebalance.")

    def rebalance(self, target_weights):
        self.liquidate_managed_assets()
        equity = self.get_equity()
        logger.info(f"Managed liquidation complete. Final Deployable Equity: ${equity:.2f}")
        
        for i, weight in enumerate(target_weights):
            if weight <= 0: continue
            ticker = self.tickers[i]
            amount = (equity * weight) * 0.98
            self.buy_dollars(ticker, amount)

    def invest_excess_cash(self, target_weights):
        cash = self.get_cash()
        min_bal = float(os.getenv('MIN_REMAINING_BALANCE', 20))
        investable = cash - min_bal
        
        if investable > float(os.getenv('MIN_ORDER_VALUE', 20)):
            logger.info(f"Excess Cash Detected: ${investable:.2f}. Sweeping into current strategy state...")
            for i, weight in enumerate(target_weights):
                if weight <= 0: continue
                ticker = self.tickers[i]
                amount = (investable * weight)
                self.buy_dollars(ticker, amount)
        else:
            logger.info("Cash balance within nominal range. No excess sweep required.")
