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
        
        # 1. SMA Check
        sma_period = self.dna['sma']
        if len(spy) < sma_period:
            # Not enough data yet
            sma_val = np.mean(spy)
        else:
            sma_val = np.mean(spy[-sma_period:])
        
        # Decision: Current Price vs SMA
        # Note: In the bot, we use the CURRENT price for calculation
        sma_triggered = spy[-1] < sma_val
        
        # 2. VIX Tier
        # We need to know if we are in Bull or Panic to pick the right bounds
        # But this engine is stateless, so we return both possible tiers
        # and let the Manager decide based on regime history.
        tier_b = np.digitize(vix[-1], self.dna['bounds_b'])
        tier_p = np.digitize(vix[-1], self.dna['bounds_p'])
        
        return {
            "sma_triggered": bool(sma_triggered),
            "tier_b": int(tier_b),
            "tier_p": int(tier_p),
            "weights_b": self.dna['weights_b'],
            "weights_p": self.dna['weights_p']
        }

    def get_allocation(self, regime, tier):
        """Returns [1x, 2x, 3x, Cash] weights"""
        if regime == "panic":
            return self.dna['weights_p'][min(tier, 4)]
        else:
            return self.dna['weights_b'][min(tier, 4)]
