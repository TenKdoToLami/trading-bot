import os
import time
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

load_dotenv()

class AlpacaClient:
    def __init__(self):
        self.api = tradeapi.REST(
            os.getenv('ALPACA_KEY'),
            os.getenv('ALPACA_SECRET'),
            os.getenv('ALPACA_BASE_URL'),
            api_version='v2'
        )
        # Mapping assets from environment
        self.tickers = [
            os.getenv('TICKER_2X', 'SSO'),
            os.getenv('TICKER_3X', 'SPXL'),
            os.getenv('TICKER_CASH', 'SGOV')
        ]

    def get_equity(self):
        account = self.api.get_account()
        return float(account.equity)

    def rebalance(self, target_weights):
        """
        target_weights: [1x, 2x, 3x, Cash] e.g. [0.0, 0.5, 0.5, 0.0]
        """
        equity = self.get_equity()
        print(f"Current Equity: ${equity:.2f}")
        
        # 1. Liquidate current holdings of our tickers
        for ticker in self.tickers:
            try:
                self.api.close_position(ticker)
                print(f"Closing position: {ticker}")
            except: pass # No position
        
        # Wait for liquidation to settle in paper
        time.sleep(5)
        
        # 2. Get fresh prices and Buy
        min_order = float(os.getenv('MIN_ORDER_VALUE', 100))
        
        for i, weight in enumerate(target_weights):
            if weight <= 0: continue
            
            ticker = self.tickers[i]
            price = float(self.api.get_latest_trade(ticker).price)
            
            # Use 98% of target to allow for slippage/price movement
            dollar_amount = (equity * weight) * 0.98
            
            if dollar_amount < min_order:
                print(f"Skipping {ticker}: Amount ${dollar_amount:.2f} is below minimum ${min_order}")
                continue
                
            qty = int(dollar_amount / price)
            if qty > 0:
                print(f"Buying {qty} shares of {ticker} (${dollar_amount:.2f})")
                self.api.submit_order(
                    symbol=ticker,
                    qty=qty,
                    side='buy',
                    type='market',
                    time_in_force='day'
                )
