"""
Genome V2 Strategy — Multi-Brain Architecture.
Each leverage tier (3x, 2x, 1x) has its own independent indicator weighting
and decision gate, allowing for high-expressive "specialization."
"""

from strategies.base import BaseStrategy
from src.tournament.registry import register_strategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility
)

from src.tournament.market_state import MarketState

@register_strategy(["v2_multi", 2.0])
class GenomeV2Strategy(BaseStrategy):
    NAME = "Genome V2 (Multi-Brain)"

    def __init__(self, genome=None, precalculated_features=None):
        self.genome = genome or self._default_genome()
        self.nitro_features = precalculated_features
        self.market = MarketState()
        self.reset()

    def _default_genome(self):
        # ... (keep same)
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
        self.market = MarketState()
        self.last_holdings = None
        self.lock_counter = 0

    def on_data(self, date, price_data, prev_data):
        m = self.market
        m.update(date, price_data)
        
        if self.lock_counter > 0:
            self.lock_counter -= 1

        if self.nitro_features and date in self.nitro_features:
            inputs = self.nitro_features[date]
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
            
            inputs = {
                'sma': ((p - v_sma) / v_sma * 5) if v_sma else 0.0,
                'ema': ((p - v_ema) / v_ema * 10) if v_ema else 0.0,
                'rsi': ((v_rsi or 50) - 50) / 50.0,
                'macd': (v_macd / p * 100) if v_macd else 0.0,
                'adx': ((v_adx or 25) - 25) / 25.0,
                'trix': v_trix or 0.0,
                'slope': (v_slope or 0.0) / p * 1000,
                'vol': (v_vol or 0.15) * 5,
                'atr': ((v_atr or 0.0) / p) * 50,
                'vix': (m.get_macro('vix', 15.0) - 20) / 10.0,
                'yc': m.get_macro('yield_curve', 0.0)
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

