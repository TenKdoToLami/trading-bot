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
        """
        Called once per trading day with today's price data and yesterday's finalized data.

        Args:
            date:       ISO date string "YYYY-MM-DD".
            price_data: Today's OHLCV dict.
            prev_data:  Yesterday's OHLCV dict (None on the first day).

        Returns:
            None  — hold current allocation (no rebalance).
            dict  — new target allocation (e.g. {"3xSPY": 1.0}).
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset all internal state for a fresh simulation run."""
        pass
