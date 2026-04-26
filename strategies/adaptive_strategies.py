"""
Adaptive strategies using KAMA and HMA.
"""

from strategies.base import BaseStrategy
from src.helpers.indicators import kama, hma

class _AdaptiveExitStrategy(BaseStrategy):
    """Base for binary 3x/CASH strategies using adaptive indicators."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.prices = []
        self.last_holdings = None

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        self.prices.append(spy_price)
        
        in_cash = self.check_exit_condition()
        
        if in_cash is None:
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
        raise NotImplementedError

class KAMA_Exit(_AdaptiveExitStrategy):
    NAME = "3x SPY (Exit < KAMA)"
    def reset(self):
        super().reset()
        self.prev_kama = None

    def check_exit_condition(self):
        self.prev_kama = kama(self.prices, 10, 2, 30, prev_kama=self.prev_kama)
        return self.prices[-1] < self.prev_kama if self.prev_kama is not None else None

class HMA_Exit(_AdaptiveExitStrategy):
    NAME = "3x SPY (Exit < HMA)"
    def check_exit_condition(self):
        val = hma(self.prices, 200)
        return self.prices[-1] < val if val is not None else None
