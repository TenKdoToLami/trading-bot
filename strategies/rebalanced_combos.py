"""
Rebalanced combination strategies.
These strategies maintain equal weight across a set of assets,
rebalancing every 20 trading days.
"""

from strategies.base import BaseStrategy

class _RebalancedEqualWeight(BaseStrategy):
    """Base class for rebalanced equal-weight strategies."""
    ASSETS = []
    REBALANCE_PERIOD = 20

    def __init__(self):
        self.reset()

    def reset(self):
        self.days_since_rebalance = 0
        self.first_day = True

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        if self.first_day or self.days_since_rebalance >= self.REBALANCE_PERIOD:
            self.first_day = False
            self.days_since_rebalance = 1
            weight = 1.0 / len(self.ASSETS)
            return {asset: weight for asset in self.ASSETS}
        
        self.days_since_rebalance += 1
        return None

class Combo123(_RebalancedEqualWeight):
    NAME = "Equal 1/2/3x SPY (20d Rebal)"
    ASSETS = ["SPY", "2xSPY", "3xSPY"]

class Combo123Cash(_RebalancedEqualWeight):
    NAME = "Equal 1/2/3x SPY + CASH (20d Rebal)"
    ASSETS = ["SPY", "2xSPY", "3xSPY", "CASH"]

class Combo23(_RebalancedEqualWeight):
    NAME = "Equal 2/3x SPY (20d Rebal)"
    ASSETS = ["2xSPY", "3xSPY"]

class Combo23Cash(_RebalancedEqualWeight):
    NAME = "Equal 2/3x SPY + CASH (20d Rebal)"
    ASSETS = ["2xSPY", "3xSPY", "CASH"]

class Combo3Cash(_RebalancedEqualWeight):
    NAME = "Equal 3x SPY + CASH (20d Rebal)"
    ASSETS = ["3xSPY", "CASH"]

class Combo2Cash(_RebalancedEqualWeight):
    NAME = "Equal 2x SPY + CASH (20d Rebal)"
    ASSETS = ["2xSPY", "CASH"]

class Combo13(_RebalancedEqualWeight):
    NAME = "Equal 1/3x SPY (20d Rebal)"
    ASSETS = ["SPY", "3xSPY"]

class Combo12(_RebalancedEqualWeight):
    NAME = "Equal 1/2x SPY (20d Rebal)"
    ASSETS = ["SPY", "2xSPY"]
