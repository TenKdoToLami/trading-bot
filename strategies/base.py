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
    def on_data(self, date: str, spy_price: float) -> Optional[Dict[str, float]]:
        """
        Called once per trading day with today's SPY closing price.

        The strategy should update its internal state and decide whether
        to rebalance.

        Args:
            date:      ISO date string "YYYY-MM-DD".
            spy_price: SPY closing price for this trading day.

        Returns:
            None  — hold current allocation (no rebalance).
            dict  — new target allocation.
                    Keys must be from ALLOWED_ASSETS.
                    Values are portfolio weight fractions that sum to 1.0.
                    Omitted assets are treated as 0.0.
                    Example: {"3xSPY": 0.7, "CASH": 0.3}
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset all internal state for a fresh simulation run."""
        pass
