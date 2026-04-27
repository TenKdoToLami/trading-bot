"""
Manual V1 Strategy — A legacy configuration loader for the original BEAST model.
Loads parameters from 'genome.json' in the same directory.
"""

import json
import os
from strategies.base import BaseStrategy
from src.helpers.indicators import sma

class ManualV1(BaseStrategy):
    NAME = "V1 Manual Configuration"

    def __init__(self, **kwargs):
        self.reset()
        
        genome = kwargs.get('genome')
        if not genome:
            genome_path = os.path.join(os.path.dirname(__file__), "genome.json")
            if os.path.exists(genome_path):
                with open(genome_path, "r") as f:
                    genome = json.load(f)
        
        if genome:
            self.sma_period = genome.get("sma", 291)
            self.min_b_days = genome.get("min_b_days", 7)
            # original strategy.json used whole numbers for VIX bounds
            self.vol_bounds = genome.get("bounds_p", [15, 62, 73])
            
            # Map weights_p list to tier dictionaries
            weights_p = genome.get("weights_p", [])
            self.panic_tiers = []
            assets = ["2xSPY", "3xSPY", "CASH"]
            for row in weights_p:
                tier_weights = {}
                for asset, weight in zip(assets, row):
                    if weight > 0:
                        tier_weights[asset] = weight
                self.panic_tiers.append(tier_weights)
        else:
            # Defaults
            self.sma_period = 291
            self.min_b_days = 7
            self.vol_bounds = [15, 62, 73]
            self.panic_tiers = [{"3xSPY": 1.0}]

    def reset(self):
        self.prices = []
        self.panic_mode = False
        self.days_in_regime = 0
        self.current_tier = 0
        self.last_holdings = None

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        vix = price_data.get('vix', 20.0)
        self.prices.append(spy_price)

        sma_val = sma(self.prices, self.sma_period)
        if sma_val is None:
            if self.last_holdings is None:
                self.last_holdings = {"3xSPY": 1.0}
                return self.last_holdings
            return None

        sma_triggered = spy_price < sma_val
        self.days_in_regime += 1

        if self.panic_mode:
            if not sma_triggered:
                self.panic_mode = False
                self.days_in_regime = 0
        else:
            if sma_triggered and self.days_in_regime >= self.min_b_days:
                self.panic_mode = True
                self.days_in_regime = 0

        if self.panic_mode:
            target_tier = sum(1 for b in self.vol_bounds if vix >= b)
        else:
            target_tier = 0

        self.current_tier = target_tier
        
        if not self.panic_mode:
            new_holdings = {"3xSPY": 1.0}
        else:
            idx = min(self.current_tier, len(self.panic_tiers) - 1)
            new_holdings = self.panic_tiers[idx]

        if new_holdings != self.last_holdings:
            self.last_holdings = new_holdings
            return new_holdings

        return None
