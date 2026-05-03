"""
Legacy Manual V1 Strategy.
Processes the original manual bounds and weights structure.
"""

from strategies.base import BaseStrategy
from src.tournament.registry import register_strategy
from src.helpers.indicators import sma

from src.tournament.market_state import MarketState

@register_strategy(["v1_manual", 1.0])
class ManualV1(BaseStrategy):
    NAME = "Champion V1 (Manual Baseline)"

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.market = MarketState()
        self.reset()

    def _default_genome(self):
        # ... (keep same)
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
        self.market = MarketState()

    def on_data(self, date, price_data, prev_data):
        self.market.update(date, price_data)
        
        # 1. Trend Filter
        val_sma = self.market.get_indicator('sma', self.genome.get('sma', 200))
        if not val_sma:
            return {"CASH": 1.0}
            
        is_uptrend = self.market.last_price > val_sma
        
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
