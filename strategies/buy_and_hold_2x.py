"""
Buy & Hold 3x SPY benchmark strategy.

Allocates 100% to 2xSPY on day one and never rebalances.
Serves as the aggressive benchmark — pure leveraged buy-and-hold.
"""

from strategies.base import BaseStrategy


class BuyAndHold2x(BaseStrategy):
    NAME = "Buy & Hold 2x"

    def __init__(self):
        self._first_day = True

    def on_data(self, date, spy_price):
        if self._first_day:
            self._first_day = False
            return {"2xSPY": 1.0}
        return None

    def reset(self):
        self._first_day = True
