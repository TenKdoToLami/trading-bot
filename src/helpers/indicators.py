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


def ema(prices: list, period: int):
    """
    Exponential Moving Average.
    Formula: EMA = Price(today) * k + EMA(yesterday) * (1 - k)
    where k = 2 / (period + 1)
    """
    if len(prices) < period:
        return None

    k = 2 / (period + 1)
    # Seed EMA with SMA of the first window
    current_ema = sum(prices[:period]) / period

    for i in range(period, len(prices)):
        current_ema = (prices[i] * k) + (current_ema * (1 - k))

    return current_ema


def rsi(prices: list, period: int = 14):
    """
    Relative Strength Index (RSI).
    Uses Wilder's smoothing method.
    """
    if len(prices) < period + 1:
        return None

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    
    # Initial averages
    gains = [d if d > 0 else 0 for d in deltas[:period]]
    losses = [-d if d < 0 else 0 for d in deltas[:period]]
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    # Smoothed averages
    for i in range(period, len(deltas)):
        gain = deltas[i] if deltas[i] > 0 else 0
        loss = -deltas[i] if deltas[i] < 0 else 0
        
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(prices: list, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Moving Average Convergence Divergence.
    Returns (macd_line, signal_line, histogram).
    """
    if len(prices) < slow + signal:
        return None, None, None

    # We need a series of MACD values to calculate the Signal line (which is an EMA of MACD)
    macd_values = []
    # To be efficient and accurate, we'd ideally calculate EMAs incrementally.
    # For this helper, we'll calculate the window of MACD values needed for the signal.
    
    # Note: This is O(N*M) where M is signal period. Acceptable for daily data.
    for i in range(len(prices) - signal, len(prices)):
        p_slice = prices[:i+1]
        fast_ema = ema(p_slice, fast)
        slow_ema = ema(p_slice, slow)
        macd_values.append(fast_ema - slow_ema)
    
    macd_line = macd_values[-1]
    # Signal line is EMA of MACD values
    signal_line = ema(macd_values, signal)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def standard_deviation(prices: list, period: int):
    """Rolling standard deviation."""
    if len(prices) < period:
        return None
    
    subset = prices[-period:]
    mean = sum(subset) / period
    variance = sum((x - mean) ** 2 for x in subset) / period
    return math.sqrt(variance)


def bollinger_bands(prices: list, period: int = 20, std_dev: float = 2.0):
    """
    Bollinger Bands.
    Returns (upper, middle, lower).
    """
    mid = sma(prices, period)
    if mid is None:
        return None, None, None
    
    sd = standard_deviation(prices, period)
    upper = mid + (std_dev * sd)
    lower = mid - (std_dev * sd)
    
    return upper, mid, lower


def momentum(prices: list, period: int = 10):
    """Rate of Change (ROC) / Momentum."""
    if len(prices) < period + 1:
        return None
    return (prices[-1] / prices[-period-1]) - 1.0


def crossed_above(series1: list, series2: list):
    """
    Returns True if series1 just crossed above series2.
    
    Args:
        series1: List of values (e.g. Price or Fast SMA)
        series2: List of values (e.g. Slow SMA)
    """
    if len(series1) < 2 or len(series2) < 2:
        return False
    return series1[-2] <= series2[-2] and series1[-1] > series2[-1]


def crossed_below(series1: list, series2: list):
    """
    Returns True if series1 just crossed below series2.
    """
    if len(series1) < 2 or len(series2) < 2:
        return False
    return series1[-2] >= series2[-2] and series1[-1] < series2[-1]
