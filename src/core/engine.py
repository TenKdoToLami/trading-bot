import numpy as np
import json

class StrategyEngine:
    def __init__(self, dna_path="strategy.json"):
        with open(dna_path, "r") as f:
            self.dna = json.load(f)
            
    def calculate_indicators(self, history):
        """
        history: pd.DataFrame with 'spy_price' and 'vix'
        Returns: (sma_triggered, current_vix_tier)
        """
        spy = history['spy_price'].values
        vix = history['vix'].values
        
        # 1. SMA Trend Check
        sma_period = self.dna['sma']
        sma_val = np.mean(spy[-sma_period:]) if len(spy) >= sma_period else np.mean(spy)
        sma_triggered = spy[-1] < sma_val
        
        # 2. VIX Tier (Panic Mode Only)
        tier_p = np.digitize(vix[-1], self.dna['bounds_p'])
        
        return {
            "sma_triggered": bool(sma_triggered),
            "tier_b": 0, # Redundant but kept for manager compatibility
            "tier_p": int(tier_p)
        }

    def get_allocation(self, regime, tier):
        """Returns [2x, 3x, Cash] weights"""
        if regime == "panic":
            return self.dna['weights_p'][min(tier, 4)]
        else:
            # Bull Mode is always 100% 3x Leverage
            return [0.0, 1.0, 0.0]
