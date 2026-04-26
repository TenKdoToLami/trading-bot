"""
Technical indicator helpers for strategies.

These are pure functions that operate on data the strategy has
already accumulated. They never access external data sources.
Strategies import and call these with their own price history.
"""

import math


def sma(prices: list, period: int):
    """
    Simple Moving Average over the last `period` values.

    Args:
        prices: List of prices accumulated by the strategy.
        period: Lookback window length.

    Returns:
        float — the SMA value, or None if len(prices) < period.
    """
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def realized_volatility(prices: list, window: int = 20):
    """
    Annualized realized volatility from a price series.

    Computes the standard deviation of daily log-returns over
    the last `window` days and annualizes it (× √252).

    This is the strategy-local proxy for VIX — it measures
    historical (realized) volatility rather than implied.

    Args:
        prices: List of prices accumulated by the strategy.
        window: Number of trading days for the lookback.

    Returns:
        float — annualized volatility (e.g. 0.15 = 15%), or None
                if insufficient data (need window + 1 prices).
    """
    if len(prices) < window + 1:
        return None

    # Log returns for the trailing window
    log_returns = []
    for i in range(-window, 0):
        log_returns.append(math.log(prices[i] / prices[i - 1]))

    # Sample standard deviation
    mean = sum(log_returns) / len(log_returns)
    variance = sum((r - mean) ** 2 for r in log_returns) / (len(log_returns) - 1)
    daily_vol = math.sqrt(variance)

    return daily_vol * math.sqrt(252)


def drawdown_from_peak(prices: list):
    """
    Current drawdown from the running peak of a price series.

    Args:
        prices: List of prices.

    Returns:
        float — drawdown as a negative fraction (e.g. -0.10 = 10% below peak),
                or 0.0 if at peak. Returns None if prices is empty.
    """
    if not prices:
        return None
    peak = prices[0]
    for p in prices:
        if p > peak:
            peak = p
    return (prices[-1] - peak) / peak if peak > 0 else 0.0
