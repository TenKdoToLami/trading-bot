"""
Strategies focused on risk management (VIX, ADX, Drawdown).
"""

from strategies.base import _IndicatorExitStrategy
from src.helpers.indicators import adx, drawdown_from_peak

class VIX_Exit(_IndicatorExitStrategy):
    NAME = "3x SPY (Exit VIX > 30)"
    def check_exit_condition(self):
        vix = float(self.current_data.get('vix', 0))
        return vix > 30

class Drawdown_Exit(_IndicatorExitStrategy):
    NAME = "3x SPY (10% Trailing Stop)"
    def check_exit_condition(self):
        dd = drawdown_from_peak(self.prices)
        if dd is None: return None
        return dd < -0.10

class ADX_Exit(_IndicatorExitStrategy):
    NAME = "3x SPY (Exit ADX < 25)"
    def reset(self):
        super().reset()
        self.adx_state = {}
    def check_exit_condition(self):
        val = adx(self.highs, self.lows, self.prices, 14, state=self.adx_state)
        if val is None: return None
        return val < 25
