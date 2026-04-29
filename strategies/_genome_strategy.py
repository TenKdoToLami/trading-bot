"""
Universal Genome Strategy (Dual-State).
Evaluates a Panic Score (to trigger a cash circuit breaker) and a Base Score
(to allocate across growth tiers), with support for rebalance lockouts.
"""

from strategies.base import BaseStrategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility
)

class GenomeStrategy(BaseStrategy):
    NAME = "Genome Strategy"

    def __init__(self, genome=None, precalculated_features=None):
        self.genome = genome or self._default_genome()
        self.nitro_features = precalculated_features
        self.reset()

    def _default_genome(self):
        w = {
            'sma': 0.0, 'ema': 0.0, 'rsi': 0.0, 'macd': 0.0,
            'adx': 0.0, 'trix': 0.0, 'slope': 0.0, 'vol': 0.0, 'atr': 0.0
        }
        active = {k: True for k in w}
        return {
            'panic_weights': dict(w),
            'panic_active': dict(active),
            'panic_threshold': 999.0,
            'base_weights': dict(w),
            'base_active': dict(active),
            'base_thresholds': {
                'tier_3x': 0.0,
                'tier_2x': -999.0,
                'tier_1x': -999.0
            },
            'lock_days': 0
        }

    def reset(self):
        self.prices = []
        self.highs = []
        self.lows = []
        
        self.prev_ema = None
        self.prev_atr = None
        self.indicator_state = {}
        self.last_holdings = None
        self.lock_counter = 0

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        
        # Lockout countdown
        if self.lock_counter > 0:
            self.lock_counter -= 1

        if self.nitro_features and date in self.nitro_features:
            # NITRO MODE: Fast lookup
            inputs = self.nitro_features[date]
        else:
            # LEGACY MODE: Calculate indicators on the fly
            self.prices.append(spy_price)
            self.highs.append(price_data['high'])
            self.lows.append(price_data['low'])

            # 1. Calculate Indicators
            val_sma = sma(self.prices, 200)
            val_ema = ema(self.prices, 50, prev_ema=self.prev_ema)
            self.prev_ema = val_ema
            val_rsi = rsi(self.prices, 14, state=self.indicator_state)
            val_macd_tuple = macd(self.prices, 12, 26, state=self.indicator_state)
            val_macd = val_macd_tuple[0] if val_macd_tuple[0] is not None else 0.0
            val_adx = adx(self.highs, self.lows, self.prices, 14, state=self.indicator_state)
            val_trix = trix(self.prices, 15, state=self.indicator_state)
            val_slope = linear_regression_slope(self.prices, 20)
            val_vol = realized_volatility(self.prices, 20)
            val_atr = atr(self.highs, self.lows, self.prices, 14, prev_atr=self.prev_atr)
            self.prev_atr = val_atr

            # 2. Normalize Indicators [-1.0, 1.0] roughly
            norm_sma = ((spy_price - val_sma) / val_sma * 5) if val_sma else 0.0
            norm_ema = ((spy_price - val_ema) / val_ema * 10) if val_ema else 0.0
            norm_rsi = ((val_rsi or 50) - 50) / 50.0
            norm_macd = val_macd / spy_price * 100
            norm_adx = ((val_adx or 25) - 25) / 25.0
            norm_trix = val_trix or 0.0
            norm_slope = (val_slope or 0.0) / spy_price * 1000
            norm_vol = (val_vol or 0.15) * 5
            norm_atr = ((val_atr or 0.0) / spy_price) * 50

            inputs = {
                'sma': norm_sma, 'ema': norm_ema, 'rsi': norm_rsi, 'macd': norm_macd,
                'adx': norm_adx, 'trix': norm_trix, 'slope': norm_slope,
                'vol': norm_vol, 'atr': norm_atr
            }

        # 3. Calculate Panic Score (with ablation)
        pw = self.genome['panic_weights']
        pa = self.genome.get('panic_active', {k: True for k in pw})
        panic_score = sum(pw[k] * inputs[k] for k in pw if pa.get(k, True))

        # 4. Check Circuit Breaker
        if panic_score > self.genome['panic_threshold']:
            new_holdings = {"CASH": 1.0}
        else:
            # 5. Calculate Base Score (with ablation)
            bw = self.genome['base_weights']
            ba = self.genome.get('base_active', {k: True for k in bw})
            base_score = sum(bw[k] * inputs[k] for k in bw if ba.get(k, True))
            
            t = self.genome['base_thresholds']
            if base_score > t['tier_3x']:
                new_holdings = {"3xSPY": 1.0}
            elif base_score > t['tier_2x']:
                new_holdings = {"2xSPY": 1.0}
            elif base_score > t['tier_1x']:
                new_holdings = {"SPY": 1.0}
            else:
                new_holdings = {"CASH": 1.0}

        # 6. Apply holdings and lockout
        if new_holdings != self.last_holdings:
            is_panic = (new_holdings.get("CASH") == 1.0 and panic_score > self.genome['panic_threshold'])
            if self.lock_counter == 0 or is_panic:
                self.last_holdings = new_holdings
                self.lock_counter = max(0, int(round(self.genome.get('lock_days', 0))))
                return new_holdings
            
        return None

