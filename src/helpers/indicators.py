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


def ema(prices: list, period: int, prev_ema: float = None):
    """
    Exponential Moving Average.
    Formula: EMA = Price(today) * k + EMA(yesterday) * (1 - k)
    where k = 2 / (period + 1)
    
    If prev_ema is provided, calculation is O(1).
    """
    if len(prices) < period:
        return None

    k = 2 / (period + 1)
    
    if prev_ema is not None:
        return (prices[-1] * k) + (prev_ema * (1 - k))

    # Full calculation path
    current_ema = sum(prices[:period]) / period
    for i in range(period, len(prices)):
        current_ema = (prices[i] * k) + (current_ema * (1 - k))
    return current_ema


def rsi(prices: list, period: int = 14, state: dict = None):
    """
    Relative Strength Index (RSI).
    Uses Wilder's smoothing method.
    
    If state={'avg_gain': f, 'avg_loss': f} is provided, calculation is O(1).
    State is modified in-place.
    """
    if len(prices) < period + 1:
        return None

    if state and "avg_gain" in state and "avg_loss" in state:
        # Incremental path
        delta = prices[-1] - prices[-2]
        gain = delta if delta > 0 else 0
        loss = -delta if delta < 0 else 0
        
        state["avg_gain"] = (state["avg_gain"] * (period - 1) + gain) / period
        state["avg_loss"] = (state["avg_loss"] * (period - 1) + loss) / period
        
        if state["avg_loss"] == 0: return 100
        rs = state["avg_gain"] / state["avg_loss"]
        return 100 - (100 / (1 + rs))

    # Full calculation path
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas[:period]]
    losses = [-d if d < 0 else 0 for d in deltas[:period]]
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    for i in range(period, len(deltas)):
        gain = deltas[i] if deltas[i] > 0 else 0
        loss = -deltas[i] if deltas[i] < 0 else 0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if state is not None:
        state["avg_gain"] = avg_gain
        state["avg_loss"] = avg_loss

    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(prices: list, fast: int = 12, slow: int = 26, signal: int = 9, state: dict = None):
    """
    Moving Average Convergence Divergence.
    Returns (macd_line, signal_line, histogram).
    
    If state={'fast_ema': f, 'slow_ema': f, 'signal_ema': f} is provided, 
    calculation is O(1). State is modified in-place.
    """
    if len(prices) < slow + signal:
        return None, None, None

    if state and "fast_ema" in state and "slow_ema" in state:
        # Incremental path
        state["fast_ema"] = ema(prices, fast, prev_ema=state["fast_ema"])
        state["slow_ema"] = ema(prices, slow, prev_ema=state["slow_ema"])
        macd_line = state["fast_ema"] - state["slow_ema"]
        
        # Signal line is an EMA of the MACD line
        # We use a temporary list of 1 value to use the ema() helper or just do it manually
        if "signal_ema" in state and state["signal_ema"] is not None:
            k = 2 / (signal + 1)
            state["signal_ema"] = (macd_line * k) + (state["signal_ema"] * (1 - k))
        else:
            # Need to seed signal_ema? Usually we'd need 'signal' macd values.
            # For simplicity, if not yet seeded, we fall back to full.
            pass
        
        if "signal_ema" in state and state["signal_ema"] is not None:
            return macd_line, state["signal_ema"], macd_line - state["signal_ema"]

    # Full calculation path
    # 1. Calculate all MACD values up to now
    macd_history = []
    f_ema = sum(prices[:fast]) / fast
    s_ema = sum(prices[:slow]) / slow
    
    # We need to iterate to get the history of MACD values to calculate the signal EMA
    for i in range(len(prices)):
        # Update EMAs
        if i >= fast:
            k_f = 2 / (fast + 1)
            f_ema = (prices[i] * k_f) + (f_ema * (1 - k_f))
        if i >= slow:
            k_s = 2 / (slow + 1)
            s_ema = (prices[i] * k_s) + (s_ema * (1 - k_s))
        
        if i >= slow:
            macd_history.append(f_ema - s_ema)

    macd_line = macd_history[-1]
    signal_line = ema(macd_history, signal)
    histogram = macd_line - signal_line

    if state is not None:
        state["fast_ema"] = f_ema
        state["slow_ema"] = s_ema
        state["signal_ema"] = signal_line

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


def kama(prices: list, period: int = 10, fast: int = 2, slow: int = 30, prev_kama: float = None):
    """
    Kaufman's Adaptive Moving Average (KAMA).
    If prev_kama is provided, calculation is O(period) instead of O(N).
    """
    if len(prices) < period + 1:
        return None

    fast_sc = 2 / (fast + 1)
    slow_sc = 2 / (slow + 1)

    if prev_kama is not None:
        # Incremental path
        change = abs(prices[-1] - prices[-period])
        volatility = sum(abs(prices[i] - prices[i - 1]) for i in range(-period + 1, 0))
        # Note: sum is O(period), but much faster than O(N)
        er = change / volatility if volatility != 0 else 0
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        return prev_kama + sc * (prices[-1] - prev_kama)

    # Full calculation path
    current_kama = prices[0]
    for i in range(1, len(prices)):
        if i >= period:
            c = abs(prices[i] - prices[i - period])
            v = sum(abs(prices[j] - prices[j-1]) for j in range(i - period + 1, i + 1))
            er_i = c / v if v != 0 else 0
            sc_i = (er_i * (fast_sc - slow_sc) + slow_sc) ** 2
            current_kama = current_kama + sc_i * (prices[i] - current_kama)
        else:
            current_kama = current_kama + slow_sc * (prices[i] - current_kama)
            
    return current_kama


def wma(prices: list, period: int):
    """
    Weighted Moving Average (WMA).
    Gives linearly increasing weights to recent prices.
    """
    if len(prices) < period:
        return None
    
    subset = prices[-period:]
    weights = range(1, period + 1)
    weighted_sum = sum(p * w for p, w in zip(subset, weights))
    return weighted_sum / sum(weights)


def hma(prices: list, period: int):
    """
    Hull Moving Average (HMA).
    Formula: WMA(2*WMA(n/2) - WMA(n), sqrt(n))
    Extremely fast and eliminates lag.
    """
    if len(prices) < period:
        return None

    half_period = period // 2
    sqrt_period = int(math.sqrt(period))
    
    # We need a series of the inner WMA calculation to compute the outer WMA
    # (2 * WMA(n/2) - WMA(n))
    inner_values = []
    # Loop back to get enough values for the final WMA
    for i in range(len(prices) - sqrt_period, len(prices)):
        p_slice = prices[:i+1]
        wma_half = wma(p_slice, half_period)
        wma_full = wma(p_slice, period)
        if wma_half is not None and wma_full is not None:
            inner_values.append(2 * wma_half - wma_full)
    
    if len(inner_values) < sqrt_period:
        return None
        
    return wma(inner_values, sqrt_period)


def linear_regression_slope(prices: list, period: int = 20):
    """
    Calculates the slope of the linear regression line over the last N days.
    Positive slope = Uptrend, Negative slope = Downtrend.
    """
    if len(prices) < period:
        return None
    
    y = prices[-period:]
    x = list(range(period))
    
    n = period
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi**2 for xi in x)
    
    denominator = (n * sum_x2 - sum_x**2)
    if denominator == 0: return 0
    
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    return slope


def trix(prices: list, period: int = 15, state: dict = None):
    """
    Triple Exponential Average (TRIX).
    Good for filtering out market noise.
    """
    if len(prices) < period * 3:
        return None

    # TRIX is 1-period ROC of triple-smoothed EMA
    if state is None: state = {}
    
    ema1 = ema(prices, period, prev_ema=state.get("ema1"))
    if ema1 is None: return None
    state["ema1"] = ema1
    
    if "ema1_history" not in state: state["ema1_history"] = []
    state["ema1_history"].append(ema1)
    
    ema2 = ema(state["ema1_history"], period, prev_ema=state.get("ema2"))
    if ema2 is None: return None
    state["ema2"] = ema2
    
    if "ema2_history" not in state: state["ema2_history"] = []
    state["ema2_history"].append(ema2)
    
    ema3 = ema(state["ema2_history"], period, prev_ema=state.get("ema3"))
    if ema3 is None: return None
    state["ema3"] = ema3
    
    if "prev_ema3" in state and state["prev_ema3"] != 0 and state["prev_ema3"] is not None:
        trix_val = (ema3 - state["prev_ema3"]) / state["prev_ema3"] * 100
    else:
        trix_val = 0
    
    state["prev_ema3"] = ema3
    return trix_val


def atr(highs: list, lows: list, closes: list, period: int = 14, prev_atr: float = None):
    """
    Average True Range (ATR).
    Measures market volatility based on the high-low range.
    """
    if len(highs) < period + 1:
        return None

    # TR = max(high - low, abs(high - prev_close), abs(low - prev_close))
    tr = max(
        highs[-1] - lows[-1],
        abs(highs[-1] - closes[-2]),
        abs(lows[-1] - closes[-2])
    )

    if prev_atr is not None:
        # Wilder's Smoothing
        return (prev_atr * (period - 1) + tr) / period

    # Full path (initial SMA of TRs)
    tr_history = []
    for i in range(1, len(highs)):
        curr_tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i-1]),
            abs(lows[i] - closes[i-1])
        )
        tr_history.append(curr_tr)
    
    return sum(tr_history[-period:]) / period


def adx(highs: list, lows: list, closes: list, period: int = 14, state: dict = None):
    """
    Average Directional Index (ADX).
    Measures trend strength (0-100).
    Uses state for O(1) incremental calculation.
    """
    if len(highs) < period * 2:
        return None

    if state is None: state = {}
    
    # 1. Initialize or Update True Range and Directional Movement
    up = highs[-1] - highs[-2]
    down = lows[-2] - lows[-1]
    
    tr = max(highs[-1] - lows[-1], abs(highs[-1] - closes[-2]), abs(lows[-1] - closes[-2]))
    dm_plus = up if up > down and up > 0 else 0
    dm_minus = down if down > up and down > 0 else 0

    if "smooth_tr" not in state:
        # Full path for initialization
        tr_hist = []
        plus_hist = []
        minus_hist = []
        for i in range(1, len(highs)):
            curr_tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
            u = highs[i] - highs[i-1]
            d = lows[i-1] - lows[i]
            tr_hist.append(curr_tr)
            plus_hist.append(u if u > d and u > 0 else 0)
            minus_hist.append(d if d > u and d > 0 else 0)
        
        # Wilder's Smoothing Initial Value (SMA)
        state["smooth_tr"] = sum(tr_hist[-period:]) / period
        state["smooth_plus"] = sum(plus_hist[-period:]) / period
        state["smooth_minus"] = sum(minus_hist[-period:]) / period
        
        # We need to calculate the DX series to get the ADX
        dx_hist = []
        # (This part is still O(N) during init, but O(1) thereafter)
        # ... simplified for briefness ...
    else:
        # Incremental path
        state["smooth_tr"] = (state["smooth_tr"] * (period - 1) + tr) / period
        state["smooth_plus"] = (state["smooth_plus"] * (period - 1) + dm_plus) / period
        state["smooth_minus"] = (state["smooth_minus"] * (period - 1) + dm_minus) / period

    if state["smooth_tr"] == 0: return 0
    
    di_plus = 100 * state["smooth_plus"] / state["smooth_tr"]
    di_minus = 100 * state["smooth_minus"] / state["smooth_tr"]
    
    dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus) if (di_plus + di_minus) != 0 else 0
    
    if "adx" not in state or state["adx"] is None:
        state["adx"] = dx # Seed
    else:
        state["adx"] = (state["adx"] * (period - 1) + dx) / period
        
    return state["adx"]
