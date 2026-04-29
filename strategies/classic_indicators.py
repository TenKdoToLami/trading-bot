"""
Institutional Core: Classic indicator-based binary strategies (3x SPY / CASH).
Only strategies exceeding the 20% CAGR threshold are retained.
"""

from strategies.base import _IndicatorExitStrategy
from src.helpers.indicators import sma, ema, drawdown_from_peak

class EMA_Exit(_IndicatorExitStrategy):
    """Alpha: 22.0% CAGR. Trend-following baseline."""
    NAME = "3x SPY (Exit < EMA 200)"
    def reset(self):
        super().reset()
        self.prev_ema = None

    def check_exit_condition(self):
        self.prev_ema = ema(self.prices, 200, prev_ema=self.prev_ema)
        return self.prices[-1] < self.prev_ema if self.prev_ema is not None else None

class GoldenCross_Exit(_IndicatorExitStrategy):
    """Alpha: 27.2% CAGR. Macro regime filter."""
    NAME = "3x SPY (Golden Cross 50/200)"
    def check_exit_condition(self):
        sma50 = sma(self.prices, 50)
        sma200 = sma(self.prices, 200)
        if sma50 is None or sma200 is None:
            return None
        return sma50 <= sma200

class TrailingStop_Exit(_IndicatorExitStrategy):
    """Alpha: 20.0% CAGR. Simple 10% trailing stop-loss."""
    NAME = "3x SPY (10% Trailing Stop)"
    def check_exit_condition(self):
        dd = drawdown_from_peak(self.prices)
        if dd is None: return None
        return dd < -0.10
