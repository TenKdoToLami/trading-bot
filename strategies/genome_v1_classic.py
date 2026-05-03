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
        self.prices = []
        self.highs = []
        self.lows = []
        self.prev_ema = None
        self.prev_atr = None
        self.indicator_state = {}

    def on_data(self, date, price_data, prev_data):
        # 0. Feature Extraction (Priority: Precalculated -> On-the-fly)
        if date in self.features:
            feat = self.features[date]
        else:
            # Fallback to manual calculation (required for vault sweep)
            from src.helpers.indicators import (
                sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility
            )
            
            spy_price = price_data['close']
            self.prices.append(spy_price)
            self.highs.append(price_data['high'])
            self.lows.append(price_data['low'])
            
            v_sma = sma(self.prices, 200)
            self.prev_ema = ema(self.prices, 50, prev_ema=self.prev_ema)
            v_rsi = rsi(self.prices, 14, state=self.indicator_state)
            v_macd = macd(self.prices, 12, 26, state=self.indicator_state)[0] or 0.0
            v_adx = adx(self.highs, self.lows, self.prices, 14, state=self.indicator_state)
            v_trix = trix(self.prices, 15, state=self.indicator_state)
            v_slope = linear_regression_slope(self.prices, 20)
            v_vol = realized_volatility(self.prices, 20)
            self.prev_atr = atr(self.highs, self.lows, self.prices, 14, prev_atr=self.prev_atr)

            feat = {
                'sma': ((spy_price - v_sma) / v_sma * 5) if v_sma else 0.0,
                'ema': ((spy_price - self.prev_ema) / self.prev_ema * 10) if self.prev_ema else 0.0,
                'rsi': ((v_rsi or 50) - 50) / 50.0,
                'macd': v_macd / spy_price * 100,
                'adx': ((v_adx or 25) - 25) / 25.0,
                'trix': v_trix or 0.0,
                'slope': (v_slope or 0.0) / spy_price * 1000,
                'vol': (v_vol or 0.15) * 5,
                'atr': ((self.prev_atr or 0.0) / spy_price) * 50
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
