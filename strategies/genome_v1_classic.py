from strategies.base import BaseStrategy

class GenomeV1(BaseStrategy):
    """
    Weighted Indicator Strategy for V1 Classic.
    Uses linear combination of indicators to determine leverage tiers.
    """
    NAME = "V1 Classic (Weighted Indicators)"

    def __init__(self, genome=None, precalculated_features=None):
        self.genome = genome
        self.features = precalculated_features or {}
        self.reset()

    def reset(self):
        self.last_signal = None

    def on_data(self, date, price_data, prev_data):
        if date not in self.features:
            return None
        
        feat = self.features[date]
        pw = self.genome['panic_weights']
        pa = self.genome['panic_active']
        bw = self.genome['base_weights']
        ba = self.genome['base_active']
        
        # 1. Panic Check
        panic_score = sum(feat[k] * pw[k] for k in pw if pa[k])
        if panic_score > self.genome['panic_threshold']:
            return {"CASH": 1.0}
            
        # 2. Base Score
        base_score = sum(feat[k] * bw[k] for k in bw if ba[k])
        
        # 3. Tier Logic
        tiers = self.genome['base_thresholds']
        if base_score > tiers['tier_3x']:
            signal = {"3xSPY": 1.0}
        elif base_score > tiers['tier_2x']:
            signal = {"2xSPY": 1.0}
        elif base_score > tiers['tier_1x']:
            signal = {"SPY": 1.0}
        else:
            signal = {"CASH": 1.0}
            
        return signal
