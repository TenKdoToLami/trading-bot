"""
Multi-indicator tactical strategies (e.g., RSI + EMA).
"""

from strategies.base import _IndicatorExitStrategy
from src.helpers.indicators import rsi, ema

class RSI_EMA_3xSPY(_IndicatorExitStrategy):
    NAME = "3x SPY (RSI 50 + EMA 30)"
    def reset(self):
        super().reset()
        self.rsi_state = {}
        self.prev_ema = None

    def check_exit_condition(self):
        r = rsi(self.prices, 14, state=self.rsi_state)
        e = ema(self.prices, 30, prev_ema=self.prev_ema)
        self.prev_ema = e
        
        if r is None or e is None:
            return None
            
        return not (r > 50 and self.prices[-1] > e)

class RSI_EMA_Split(RSI_EMA_3xSPY):
    NAME = "3xSPY/VOO (RSI 50 + EMA 30)"
    def on_data(self, date, price_data, prev_data):
        self.prices.append(price_data['close'])
        self.highs.append(price_data['high'])
        self.lows.append(price_data['low'])
        self.current_data = price_data
        
        in_cash = self.check_exit_condition()
        
        if in_cash is None:
            new_holdings = {"3xSPY": 0.5, "SPY": 0.5}
        elif in_cash:
            new_holdings = {"CASH": 1.0}
        else:
            new_holdings = {"3xSPY": 0.5, "SPY": 0.5}

        if new_holdings != self.last_holdings:
            self.last_holdings = new_holdings
            return new_holdings
        return None
