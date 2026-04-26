"""
Tactical Adaptive strategies.
Combines KAMA/HMA with trend filters, buffers, and confirmation logic
to reduce over-trading and improve performance.
"""

from strategies.base import BaseStrategy
from src.helpers.indicators import kama, hma, sma

class _TacticalAdaptiveStrategy(BaseStrategy):
    """
    Base for advanced adaptive strategies.
    Uses:
    1. Trend Guard (SMA 200)
    2. Hysteresis Buffer (Entry/Exit gap)
    3. Confirmation (Min days in regime)
    """
    MIN_DAYS = 5
    BUFFER = 0.005 # 0.5% re-entry buffer
    SMA_FILTER = 200

    def __init__(self):
        self.reset()

    def reset(self):
        self.prices = []
        self.panic_mode = False
        self.days_in_regime = 0
        self.last_holdings = None
        # State for indicators
        self.indicator_state = None 

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        self.prices.append(spy_price)
        
        # 1. Trend Guard (SMA 200)
        ma_val = sma(self.prices, self.SMA_FILTER)
        if ma_val is None:
            return self._set_holdings({"3xSPY": 1.0})

        # 2. Adaptive Indicator
        ind_val = self.get_indicator_value()
        if ind_val is None:
            return self._set_holdings({"3xSPY": 1.0})

        # 3. Decision Logic
        self.days_in_regime += 1
        
        if self.panic_mode:
            # Check for recovery: Price > Ind * (1 + BUFFER) AND Price > SMA
            if spy_price > ind_val * (1 + self.BUFFER) and spy_price > ma_val:
                if self.days_in_regime >= self.MIN_DAYS:
                    self.panic_mode = False
                    self.days_in_regime = 0
        else:
            # Check for panic: Price < Ind OR Price < SMA
            if spy_price < ind_val or spy_price < ma_val:
                if self.days_in_regime >= self.MIN_DAYS:
                    self.panic_mode = True
                    self.days_in_regime = 0

        new_holdings = {"CASH": 1.0} if self.panic_mode else {"3xSPY": 1.0}
        return self._set_holdings(new_holdings)

    def _set_holdings(self, holdings):
        if holdings != self.last_holdings:
            self.last_holdings = holdings
            return holdings
        return None

    def get_indicator_value(self):
        raise NotImplementedError

class TacticalKAMA(_TacticalAdaptiveStrategy):
    NAME = "Tactical KAMA (3x)"
    def get_indicator_value(self):
        # Store state for incremental kama
        self.indicator_state = kama(self.prices, 10, 2, 30, prev_kama=self.indicator_state)
        return self.indicator_state

class TacticalHMA(_TacticalAdaptiveStrategy):
    NAME = "Tactical HMA (3x)"
    def get_indicator_value(self):
        # HMA doesn't support state yet, but we've optimized it anyway
        return hma(self.prices, 50) # Use 50 for a more tactical medium-term feel
