"""
Buy & Hold SPY (1x) benchmark strategy.

Allocates 100% to SPY on day one and never rebalances.
Serves as the baseline benchmark — plain index holding.
"""

from strategies.base import BaseStrategy


class BuyAndHoldSpy(BaseStrategy):
    NAME = "Buy & Hold SPY"

    def __init__(self):
        self._first_day = True

    def on_data(self, date, spy_price):
        if self._first_day:
            self._first_day = False
            return {"SPY": 1.0}
        return None

    def reset(self):
        self._first_day = True
