"""
Base strategy interface for the tournament framework.

Every strategy must subclass BaseStrategy and implement:
  - on_data(date, spy_price) -> Optional[dict]
  - reset()

The control unit feeds one day of SPY data at a time.
Strategies must derive all indicators (SMA, volatility, etc.)
from the SPY prices they accumulate internally.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict


class BaseStrategy(ABC):
    """Abstract base class that all tournament strategies must implement."""

    # Human-readable name shown in tables and charts.
    NAME: str = "Unnamed Strategy"

    # The only assets a strategy may hold.
    ALLOWED_ASSETS = ("SPY", "2xSPY", "3xSPY", "CASH")

    @abstractmethod
    def on_data(self, date: str, price_data: dict, prev_data: Optional[dict]) -> Optional[Dict[str, float]]:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

class _IndicatorExitStrategy(BaseStrategy):
    version = 1
    """Base for binary 3x/CASH strategies."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.prices = []
        self.highs = []
        self.lows = []
        self.current_data = None
        self.last_holdings = None

    def on_data(self, date, price_data, prev_data):
        self.prices.append(price_data['close'])
        self.highs.append(price_data['high'])
        self.lows.append(price_data['low'])
        self.current_data = price_data
        
        in_cash = self.check_exit_condition()
        
        if in_cash is None: # Not enough data
            new_holdings = {"3xSPY": 1.0}
        elif in_cash:
            new_holdings = {"CASH": 1.0}
        else:
            new_holdings = {"3xSPY": 1.0}

        if new_holdings != self.last_holdings:
            self.last_holdings = new_holdings
            return new_holdings
        return None

    @abstractmethod
    def check_exit_condition(self) -> bool:
        """Returns True if indicator triggers CASH exit."""
        pass
