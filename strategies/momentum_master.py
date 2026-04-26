"""
The Momentum Master strategy.
Uses a multi-factor approach to capture upward momentum while
using volatility and trend filters to protect 3x leverage.
"""

from strategies.base import BaseStrategy
from src.helpers.indicators import ema, macd, realized_volatility, rsi

class MomentumMaster(BaseStrategy):
    NAME = "Momentum Master (3x/1x/CASH)"

    EMA_LONG = 200
    VOL_LIMIT = 0.30  # 30% annualized vol limit for 3x
    RSI_MIN = 50      # Momentum confirmation
    
    def __init__(self):
        self.reset()

    def reset(self):
        self.prices = []
        self.last_holdings = None
        self.rsi_state = {}
        self.macd_state = {}
        self.prev_ema = None

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        self.prices.append(spy_price)
        
        # 1. Get all indicators
        current_ema = ema(self.prices, self.EMA_LONG, prev_ema=self.prev_ema)
        self.prev_ema = current_ema # Store for next time
        
        _, _, macd_hist = macd(self.prices, state=self.macd_state)
        current_rsi = rsi(self.prices, 14, state=self.rsi_state)
        current_vol = realized_volatility(self.prices, 20)
        
        # Check if we have enough data
        if any(v is None for v in [current_ema, macd_hist, current_rsi, current_vol]):
            return self._set_holdings({"SPY": 1.0})

        # 2. Decision Logic
        
        # REGIME: Is the long term trend up?
        is_bull = spy_price > current_ema
        
        # MOMENTUM: Is the short term momentum up?
        is_momentum = macd_hist > 0 and current_rsi > self.RSI_MIN
        
        # RISK: Is volatility low enough for leverage?
        is_safe = current_vol < self.VOL_LIMIT

        if not is_bull:
            # Bear market regime -> Pure CASH
            new_holdings = {"CASH": 1.0}
        elif is_momentum and is_safe:
            # Optimal conditions -> Full 3x
            new_holdings = {"3xSPY": 1.0}
        elif is_momentum or is_safe:
            # One factor is weak -> De-leverage to 1x
            new_holdings = {"SPY": 1.0}
        else:
            # Bull market but weak momentum and high risk -> Safety
            new_holdings = {"CASH": 1.0}

        return self._set_holdings(new_holdings)

    def _set_holdings(self, holdings):
        if holdings != self.last_holdings:
            self.last_holdings = holdings
            return holdings
        return None
