"""
Classic indicator-based binary strategies (3x SPY / CASH).
"""

from strategies.base import _IndicatorExitStrategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, bollinger_bands, momentum
)

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

class GoldenCross_Exit(_IndicatorExitStrategy):
    NAME = "3x SPY (Golden Cross 50/200)"
    def check_exit_condition(self):
        sma50 = sma(self.prices, 50)
        sma200 = sma(self.prices, 200)
        if sma50 is None or sma200 is None:
            return None
        return sma50 <= sma200
