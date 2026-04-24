import os
import time
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

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

        self.api = tradeapi.REST(
            key,
            secret,
            base_url,
            api_version='v2'
        )
        # Managed tickers [2x, 3x, Cash]
        self.tickers = [
            os.getenv('TICKER_2X', 'SSO'),
            os.getenv('TICKER_3X', 'SPXL'),
            os.getenv('TICKER_CASH', 'SGOV')
        ]
        self.signal_ticker = os.getenv('TICKER_SIGNAL', 'VOO')

    def get_equity(self):
        """Returns total portfolio equity."""
        account = self.api.get_account()
        return float(account.equity)

    def get_cash(self):
        """Returns only the available cash (buying power)."""
        account = self.api.get_account()
        return float(account.cash)

    def is_market_open(self):
        """Checks if the market is currently open."""
        return self.api.get_clock().is_open

    def get_price(self, ticker):
        """Returns the latest trade price for a ticker."""
        return float(self.api.get_latest_trade(ticker).price)

    def get_positions(self):
        """Returns current positions for managed tickers."""
        positions = self.api.list_positions()
        return {p.symbol: float(p.qty) for p in positions if p.symbol in self.tickers}

    def sell_all(self, ticker):
        """Closes the entire position for a specific ticker."""
        try:
            self.api.close_position(ticker)
            print(f"Position closed: {ticker}")
            return True
        except Exception as e:
            return False

    def buy_dollars(self, ticker, dollar_amount):
        """Calculates quantity and submits a market buy order."""
        price = self.get_price(ticker)
        qty = int(dollar_amount / price)
        
        if qty > 0:
            print(f"Ordering {qty} shares of {ticker} (~${dollar_amount:.2f})")
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
        """Liquidates only the assets managed by this strategy."""
        print("Liquidating managed assets...")
        for ticker in self.tickers:
            self.sell_all(ticker)
        time.sleep(5)

    def rebalance(self, target_weights):
        """
        High-level rebalance orchestration.
        target_weights: [2x, 3x, Cash]
        """
        equity = self.get_equity()
        min_order = float(os.getenv('MIN_ORDER_VALUE', 100))
        
        print(f"Synchronizing Portfolio. Total Equity: ${equity:.2f}")
        self.liquidate_managed_assets()
        
        for i, weight in enumerate(target_weights):
            if weight <= 0: continue
            ticker = self.tickers[i]
            dollar_amount = (equity * weight) * 0.98
            
            if dollar_amount < min_order:
                print(f"Skipped {ticker}: Target ${dollar_amount:.2f} below minimum.")
                continue
            self.buy_dollars(ticker, dollar_amount)
