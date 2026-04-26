"""
Simple 3x SPY strategies that exit to CASH based on technical indicators.
"""

from strategies.base import BaseStrategy
from src.helpers.indicators import (
    ema, rsi, macd, bollinger_bands, momentum
)

class _IndicatorExitStrategy(BaseStrategy):
    """Base for binary 3x/CASH strategies."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.prices = []
        self.last_holdings = None

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        self.prices.append(spy_price)
        
        # Determine if we should be in CASH (True) or 3x (False)
        in_cash = self.check_exit_condition()
        
        if in_cash is None: # Not enough data
            new_holdings = {"3xSPY": 1.0}
        elif in_cash:
            new_holdings = {"CASH": 1.0}
        else:
            new_holdings = {"3xSPY": 1.0}

        if new_holdings != self.last_holdings:
            self.last_holdings = new_holdings
            return new_holdings
        return None

    def check_exit_condition(self) -> bool:
        """Returns True if indicator triggers CASH exit."""
        raise NotImplementedError

class RSI_Exit(_IndicatorExitStrategy):
    NAME = "3x SPY (Exit RSI < 50)"
    def reset(self):
        super().reset()
        self.rsi_state = {}

    def check_exit_condition(self):
        val = rsi(self.prices, 14, state=self.rsi_state)
        return val < 50 if val is not None else None

class MACD_Exit(_IndicatorExitStrategy):
    NAME = "3x SPY (Exit MACD < 0)"
    def reset(self):
        super().reset()
        self.macd_state = {}

    def check_exit_condition(self):
        _, _, hist = macd(self.prices, state=self.macd_state)
        return hist < 0 if hist is not None else None

class EMA_Exit(_IndicatorExitStrategy):
    NAME = "3x SPY (Exit < EMA 200)"
    def reset(self):
        super().reset()
        self.prev_ema = None

    def check_exit_condition(self):
        self.prev_ema = ema(self.prices, 200, prev_ema=self.prev_ema)
        return self.prices[-1] < self.prev_ema if self.prev_ema is not None else None

class Bollinger_Exit(_IndicatorExitStrategy):
    NAME = "3x SPY (Exit < Lower Band)"
    def check_exit_condition(self):
        upper, mid, lower = bollinger_bands(self.prices, 20, 2)
        return self.prices[-1] < lower if lower is not None else None

class Momentum_Exit(_IndicatorExitStrategy):
    NAME = "3x SPY (Exit Momentum < 0)"
    def check_exit_condition(self):
        val = momentum(self.prices, 10)
        return val < 0 if val is not None else None
