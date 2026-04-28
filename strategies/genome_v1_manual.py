"""
Legacy Manual V1 Strategy.
Processes the original manual bounds and weights structure.
"""

from strategies.base import BaseStrategy
from src.helpers.indicators import sma

class ManualV1(BaseStrategy):
    NAME = "Champion V1 (Manual Baseline)"

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.reset()

    def _default_genome(self):
        return {
            "sma": 200,
            "min_b_days": 5,
            "bounds_p": [15, 30, 45],
            "weights_p": [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 1.0]
            ]
        }

    def reset(self):
        self.prices = []

    def on_data(self, date, price_data, prev_data):
        self.prices.append(price_data['close'])
        
        # 1. Trend Filter
        val_sma = sma(self.prices, self.genome.get('sma', 200))
        if not val_sma:
            return {"CASH": 1.0}
            
        is_uptrend = price_data['close'] > val_sma
        
        # 2. VIX-Based State Selection
        vix = float(price_data.get('vix', 20.0))
        bounds = self.genome['bounds_p']
        
        # Determine state index based on VIX bounds
        state_idx = 0
        for b in bounds:
            if vix > b:
                state_idx += 1
            else:
                break
        
        # Clamp state index to available weights
        state_idx = min(state_idx, len(self.genome['weights_p']) - 1)
        
        # 3. Apply Weights
        w = self.genome['weights_p'][state_idx]
        
        # If not in uptrend, override to CASH (Legacy V1 behavior)
        if not is_uptrend:
            return {"CASH": 1.0}
            
        return {
            "CASH": w[0],
            "SPY": w[1],
            "3xSPY": w[2]
        }
