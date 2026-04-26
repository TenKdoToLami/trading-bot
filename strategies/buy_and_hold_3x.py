"""
Buy & Hold 3x SPY benchmark strategy.

Allocates 100% to 3xSPY on day one and never rebalances.
Serves as the aggressive benchmark — pure leveraged buy-and-hold.
"""

from strategies.base import BaseStrategy


class BuyAndHold3x(BaseStrategy):
    NAME = "Buy & Hold 3x"

    def __init__(self):
        self._first_day = True

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        if self._first_day:
            self._first_day = False
            return {"3xSPY": 1.0}
        return None

    def reset(self):
        self._first_day = True
