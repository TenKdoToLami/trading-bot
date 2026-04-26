"""
The ADX Breakout strategy.
Uses ADX to confirm trend strength and Linear Regression to confirm direction.
Uses ATR (Average True Range) for a dynamic trailing stop.
"""

from strategies.base import BaseStrategy
from src.helpers.indicators import ema, adx, linear_regression_slope, atr

class ADXBreakout(BaseStrategy):
    NAME = "ADX Breakout (3x/CASH)"

    def __init__(self):
        self.reset()

    def reset(self):
        self.prices = []
        self.highs = []
        self.lows = []
        self.last_holdings = None
        self.peak_price = 0
        self.prev_ema = None
        self.prev_atr = None
        self.adx_state = {}

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        self.prices.append(spy_price)
        self.highs.append(price_data['high'])
        self.lows.append(price_data['low'])
        
        # 1. Indicators
        current_ema = ema(self.prices, 200, prev_ema=self.prev_ema)
        self.prev_ema = current_ema
        
        current_adx = adx(self.highs, self.lows, self.prices, 14, state=self.adx_state)
        slope = linear_regression_slope(self.prices, 20)
        current_atr = atr(self.highs, self.lows, self.prices, 14, prev_atr=self.prev_atr)
        self.prev_atr = current_atr

        if any(v is None for v in [current_ema, current_adx, slope, current_atr]):
            return self._set_holdings({"3xSPY": 1.0})

        # 2. Strategy Logic
        
        # Are we trending strongly?
        is_trending = current_adx > 25
        # Is the trend upwards?
        is_upwards = slope > 0 and spy_price > current_ema
        
        # Trailing stop logic using ATR
        if spy_price > self.peak_price:
            self.peak_price = spy_price
        
        stop_loss = self.peak_price - (2.5 * current_atr)
        is_stopped_out = spy_price < stop_loss

        if is_trending and is_upwards and not is_stopped_out:
            new_holdings = {"3xSPY": 1.0}
        else:
            # If trend weakens or we hit the ATR stop, go to CASH
            new_holdings = {"CASH": 1.0}
            if is_stopped_out:
                # Reset peak on stop out to allow re-entry later
                self.peak_price = 0

        return self._set_holdings(new_holdings)

    def _set_holdings(self, holdings):
        if holdings != self.last_holdings:
            self.last_holdings = holdings
            return holdings
        return None
