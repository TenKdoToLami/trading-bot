"""
Full Cash Panic strategy variant.

Same SMA-based regime detection as BEAST, but when panic is triggered,
the entire portfolio goes to 100% CASH regardless of volatility level.
No tiered allocation — binary bull/panic switch.
"""

from strategies.base import BaseStrategy
from src.helpers.indicators import sma


class FullCashPanic(BaseStrategy):
    NAME = "Full Cash Panic"

    SMA_PERIOD = 291
    MIN_B_DAYS = 7

    def __init__(self):
        self.reset()

    def reset(self):
        self.prices = []
        self.panic_mode = False
        self.days_in_regime = 0
        self.last_holdings = None

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        self.prices.append(spy_price)

        sma_val = sma(self.prices, self.SMA_PERIOD)
        if sma_val is None:
            # Not enough data — default to bull (3x)
            if self.last_holdings is None:
                self.last_holdings = {"3xSPY": 1.0}
                return {"3xSPY": 1.0}
            return None

        sma_triggered = spy_price < sma_val

        # Regime transitions (identical to BEAST)
        self.days_in_regime += 1

        if self.panic_mode:
            if not sma_triggered:
                self.panic_mode = False
                self.days_in_regime = 0
        else:
            if sma_triggered and self.days_in_regime >= self.MIN_B_DAYS:
                self.panic_mode = True
                self.days_in_regime = 0

        # Binary decision: 3x in bull, 100% cash in panic
        if self.panic_mode:
            new_holdings = {"CASH": 1.0}
        else:
            new_holdings = {"3xSPY": 1.0}

        if new_holdings != self.last_holdings:
            self.last_holdings = new_holdings
            return new_holdings

        return None
