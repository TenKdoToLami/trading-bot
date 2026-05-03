from strategies.base import BaseStrategy
from src.tournament.registry import register_strategy
from src.tournament.market_state import MarketState

@register_strategy(["v1_classic", 1.1])
class GenomeV1(BaseStrategy):
    """
    Weighted Indicator Strategy for V1 Classic.
    Uses linear combination of indicators to determine leverage tiers.
    """
    NAME = "V1 Classic (Weighted Indicators)"

    def __init__(self, genome=None, precalculated_features=None):
        self.genome = genome
        self.features = precalculated_features or {}
        self.market = MarketState()
        self.reset()

    def reset(self):
        self.last_signal = None
        self.market = MarketState()

    def on_data(self, date, price_data, prev_data):
        m = self.market
        m.update(date, price_data)

        # 0. Feature Extraction (Priority: Precalculated -> On-the-fly)
        if date in self.features:
            feat = self.features[date]
        else:
            # Indicator Pipeline via MarketState
            p = m.last_price
            v_sma = m.get_indicator('sma', 200)
            v_ema = m.get_indicator('ema', 50)
            v_rsi = m.get_indicator('rsi', 14)
            v_macd = m.get_indicator('macd', 12, slow=26)
            v_adx = m.get_indicator('adx', 14)
            v_trix = m.get_indicator('trix', 15)
            v_slope = m.get_indicator('slope', 20)
            v_vol = m.get_indicator('vol', 20)
            v_atr = m.get_indicator('atr', 14)

            feat = {
                'sma': ((p - v_sma) / v_sma * 5) if v_sma else 0.0,
                'ema': ((p - v_ema) / v_ema * 10) if v_ema else 0.0,
                'rsi': ((v_rsi or 50) - 50) / 50.0,
                'macd': (v_macd / p * 100) if v_macd else 0.0,
                'adx': ((v_adx or 25) - 25) / 25.0,
                'trix': v_trix or 0.0,
                'slope': (v_slope or 0.0) / p * 1000,
                'vol': (v_vol or 0.15) * 5,
                'atr': ((v_atr or 0.0) / p) * 50
            }
        
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
