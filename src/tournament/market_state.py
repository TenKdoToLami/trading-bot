"""
MarketState — Unified Indicator & Data Management.
Handles history tracking, stateful indicator persistence, and result caching.
"""

import numpy as np
from typing import Dict, Any, List, Optional
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, 
    realized_volatility, mfi, bollinger_width, bollinger_bands
)

class MarketState:
    def __init__(self, warmup_period: int = 300):
        self.warmup_period = warmup_period
        
        # Raw Data History
        self.prices: List[float] = []
        self.highs: List[float] = []
        self.lows: List[float] = []
        self.volumes: List[float] = []
        self.dates: List[Any] = []
        
        # Extra Macro Data (VIX, etc.)
        self.macro: Dict[str, float] = {}
        
        # Stateful Indicator Persistence
        # { (name, period): state_object }
        self._states: Dict[tuple, Any] = {}
        
        # Per-Bar Result Cache
        # Cleared every time on_data is called
        self._cache: Dict[tuple, Any] = {}

    def update(self, date: Any, price_data: Dict[str, Any]):
        """Inject new bar of data and clear the per-bar cache."""
        self.dates.append(date)
        self.prices.append(float(price_data['close']))
        self.highs.append(float(price_data['high']))
        self.lows.append(float(price_data['low']))
        self.volumes.append(float(price_data.get('volume', 0)))
        
        # Store all other fields as macro data
        self.macro = {k: float(v) for k, v in price_data.items() if k not in ['close', 'high', 'low', 'volume']}
        
        # Clear per-bar cache
        self._cache = {}
        
        # Limit history size to prevent memory bloat if necessary
        if len(self.prices) > 1000:
            # We keep enough for long SMAs (e.g., 200-500)
            pass

    def get_indicator(self, name: str, period: int, **kwargs) -> Any:
        """
        Request an indicator. Handles caching and state automatically.
        """
        period = int(round(period))
        cache_key = (name, period, tuple(sorted(kwargs.items())))
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = self._calculate(name, period, **kwargs)
        self._cache[cache_key] = result
        return result

    def _calculate(self, name: str, period: int, **kwargs) -> Any:
        """Internal routing to indicator functions."""
        if len(self.prices) < period:
            return None

        # SMA
        if name == "sma":
            return sma(self.prices, period)
        
        # EMA (Stateful)
        if name == "ema":
            state_key = ("ema", period)
            val = ema(self.prices, period, prev_ema=self._states.get(state_key))
            self._states[state_key] = val
            return val
            
        # RSI (Stateful)
        if name == "rsi":
            state_key = ("rsi", period)
            if state_key not in self._states: self._states[state_key] = {}
            return rsi(self.prices, period, state=self._states[state_key])
            
        # MACD (Stateful)
        if name == "macd":
            fast = period
            slow = kwargs.get('slow', int(period * 2.16)) # Default 12/26 ratio
            state_key = ("macd", fast, slow)
            if state_key not in self._states: self._states[state_key] = {}
            res = macd(self.prices, fast, slow, state=self._states[state_key])
            return res[0] if res else None # Usually we want the histogram or line
            
        # ADX (Stateful)
        if name == "adx":
            state_key = ("adx", period)
            if state_key not in self._states: self._states[state_key] = {}
            return adx(self.highs, self.lows, self.prices, period, state=self._states[state_key])
            
        # ATR (Stateful)
        if name == "atr":
            state_key = ("atr", period)
            val = atr(self.highs, self.lows, self.prices, period, prev_atr=self._states.get(state_key))
            self._states[state_key] = val
            return val
            
        # TRIX (Stateful)
        if name == "trix":
            state_key = ("trix", period)
            if state_key not in self._states: self._states[state_key] = {}
            return trix(self.prices, period, state=self._states[state_key])

        # Non-stateful ones
        if name == "slope":
            return linear_regression_slope(self.prices, period)
        
        if name == "vol":
            return realized_volatility(self.prices, period)
            
        if name == "mfi":
            return mfi(self.highs, self.lows, self.prices, self.volumes, period)
            
        if name == "bbw":
            return bollinger_width(self.prices, period)
            
        if name == "bb":
            return bollinger_bands(self.prices, period)

        return None

    @property
    def last_price(self) -> float:
        return self.prices[-1] if self.prices else 0.0

    def get_macro(self, key: str, default: float = 0.0) -> float:
        return self.macro.get(key, default)
