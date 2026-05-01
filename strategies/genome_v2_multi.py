"""
Genome V2 Strategy — Multi-Brain Architecture.
Each leverage tier (3x, 2x, 1x) has its own independent indicator weighting
and decision gate, allowing for high-expressive "specialization."
"""

from strategies.base import BaseStrategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility
)

class GenomeV2Strategy(BaseStrategy):
    NAME = "Genome V2 (Multi-Brain)"

    def __init__(self, genome=None, precalculated_features=None):
        self.genome = genome or self._default_genome()
        self.nitro_features = precalculated_features
        self.reset()

    def _default_genome(self):
        # Every tier gets its own set of weights
        def _brain():
            return {
                'w': {k: 0.0 for k in ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']},
                'a': {k: True for k in ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']},
                't': 0.0
            }
        
        return {
            'panic': _brain(),
            '3x': _brain(),
            '2x': _brain(),
            '1x': _brain(),
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
        self.prev_macro = {'vix': 15.0, 'yc': 0.0}

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        
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

            # 2. Normalize
            macro_vix = float(price_data.get('vix', 15.0))
            macro_yc = float(price_data.get('yield_curve', 0.0))
            
            inputs = {
                'sma': ((spy_price - val_sma) / val_sma * 5) if val_sma else 0.0,
                'ema': ((spy_price - val_ema) / val_ema * 10) if val_ema else 0.0,
                'rsi': ((val_rsi or 50) - 50) / 50.0,
                'macd': val_macd / spy_price * 100,
                'adx': ((val_adx or 25) - 25) / 25.0,
                'trix': val_trix or 0.0,
                'slope': (val_slope or 0.0) / spy_price * 1000,
                'vol': (val_vol or 0.15) * 5,
                'atr': ((val_atr or 0.0) / spy_price) * 50,
                'vix': (macro_vix - 20) / 10.0,
                'yc': macro_yc
            }

        # 3. Decision Pipeline (Each tier has its own weighted score and threshold)
        def _get_score(brain_key):
            brain = self.genome[brain_key]
            return sum(brain['w'][k] * inputs[k] for k in brain['w'] if brain['a'].get(k, True))

        score_panic = _get_score('panic')
        score_3x = _get_score('3x')
        score_2x = _get_score('2x')
        score_1x = _get_score('1x')

        # Logic Branching
        if score_panic > self.genome['panic']['t']:
            new_holdings = {"CASH": 1.0}
        elif score_3x > self.genome['3x']['t']:
            new_holdings = {"3xSPY": 1.0}
        elif score_2x > self.genome['2x']['t']:
            new_holdings = {"2xSPY": 1.0}
        elif score_1x > self.genome['1x']['t']:
            new_holdings = {"SPY": 1.0}
        else:
            new_holdings = {"CASH": 1.0}

        # 4. Telemetry (Softmax Conviction Fight)
        import numpy as np
        m_panic = score_panic - self.genome['panic']['t']
        m_3x = score_3x - self.genome['3x']['t']
        m_2x = score_2x - self.genome['2x']['t']
        m_1x = score_1x - self.genome['1x']['t']
        
        e_p = np.exp(m_panic)
        e_3 = np.exp(m_3x)
        e_2 = np.exp(m_2x)
        e_1 = np.exp(m_1x)
        e_n = np.exp(0) # Neutral Baseline
        denom = e_p + e_3 + e_2 + e_1 + e_n

        telemetry = {
            "conf_cash": float(e_p / denom),
            "conf_3x": float(e_3 / denom),
            "conf_2x": float(e_2 / denom),
            "conf_1x": float(e_1 / denom),
            "score_panic": float(score_panic),
            "score_3x": float(score_3x),
            "score_2x": float(score_2x),
            "score_1x": float(score_1x),
            "threshold_panic": float(self.genome['panic']['t']),
            "threshold_3x": float(self.genome['3x']['t']),
            "threshold_2x": float(self.genome['2x']['t']),
            "threshold_1x": float(self.genome['1x']['t'])
        }

        # Feature Importance for Anatomy
        importance = {}
        for k in ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']:
            importance[k] = {
                "panic": float(abs(self.genome['panic']['w'].get(k, 0))),
                "3x": float(abs(self.genome['3x']['w'].get(k, 0))),
                "2x": float(abs(self.genome['2x']['w'].get(k, 0))),
                "1x": float(abs(self.genome['1x']['w'].get(k, 0)))
            }
        telemetry["importance"] = importance

        # 5. Apply lockout
        if new_holdings != self.last_holdings:
            is_panic = (new_holdings.get("CASH") == 1.0 and score_panic > self.genome['panic']['t'])
            if self.lock_counter == 0 or is_panic:
                self.last_holdings = new_holdings
                self.lock_counter = max(0, int(round(self.genome.get('lock_days', 0))))
                return new_holdings, telemetry
            
        return self.last_holdings, telemetry

