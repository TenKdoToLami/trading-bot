"""
Genome V3 Strategy — Precision Binary Architecture.
Focuses entirely on 3x vs Cash.
Evolves both the indicator weights AND the indicator lookback periods.
"""

import numpy as np
from strategies.base import BaseStrategy
from src.tournament.registry import register_strategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility
)

from src.tournament.market_state import MarketState

@register_strategy(["v3_precision", 3.0])
class GenomeV3Strategy(BaseStrategy):
    NAME = "Genome V3 (Precision Binary)"
    version = 3

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.market = MarketState()
        self.reset()

    def _default_genome(self):
        # ... (keep same)
        def _brain():
            return {
                'w': {k: 0.0 for k in ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']},
                'a': {k: True for k in ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']},
                't': 0.0,
                'lookbacks': {
                    'sma': 200, 'ema': 50, 'rsi': 14, 'macd_f': 12, 'macd_s': 26,
                    'adx': 14, 'trix': 15, 'slope': 20, 'vol': 20, 'atr': 14
                }
            }
        
        return {
            'panic': _brain(),
            'bull': _brain(),
            'lock_days': 0
        }

    def reset(self):
        self.market = MarketState()
        self.last_holdings = None
        self.lock_counter = 0

    def _get_brain_score(self, brain_key, price_data):
        brain = self.genome[brain_key]
        lb = brain.get('lookbacks', {})
        
        total_score = 0.0
        w, a = brain['w'], brain['a']
        m = self.market
        
        # Guard: If history is too short for lookbacks, return 0
        if not m.prices: return 0.0
        
        if a.get('sma', True):
            v = m.get_indicator('sma', lb.get('sma', 200))
            if v: total_score += w['sma'] * ((m.last_price - v) / v * 5)
            
        if a.get('ema', True):
            v = m.get_indicator('ema', lb.get('ema', 50))
            if v: total_score += w['ema'] * ((m.last_price - v) / v * 10)
            
        if a.get('rsi', True):
            v = m.get_indicator('rsi', lb.get('rsi', 14))
            if v: total_score += w['rsi'] * ((v - 50) / 50.0)
            
        if a.get('macd', True):
            v = m.get_indicator('macd', lb.get('macd_f', 12), slow=lb.get('macd_s', 26))
            if v: total_score += w['macd'] * (v / m.last_price * 100)
            
        if a.get('adx', True):
            v = m.get_indicator('adx', lb.get('adx', 14))
            if v: total_score += w['adx'] * ((v - 25) / 25.0)
            
        if a.get('trix', True):
            v = m.get_indicator('trix', lb.get('trix', 15))
            if v: total_score += w['trix'] * v
            
        if a.get('slope', True):
            v = m.get_indicator('slope', lb.get('slope', 20))
            if v: total_score += w['slope'] * (v / m.last_price * 1000)
            
        if a.get('vol', True):
            v = m.get_indicator('vol', lb.get('vol', 20))
            if v: total_score += w['vol'] * (v * 5)
            
        if a.get('atr', True):
            v = m.get_indicator('atr', lb.get('atr', 14))
            if v: total_score += w['atr'] * ((v / m.last_price) * 50)
            
        if a.get('vix', True):
            v = m.get_macro('vix', 15.0)
            total_score += w['vix'] * ((v - 20) / 10.0)
            
        if a.get('yc', True):
            v = m.get_macro('yield_curve', 0.0)
            total_score += w['yc'] * v
            
        return total_score

    def on_data(self, date, price_data, prev_data):
        self.market.update(date, price_data)

        if self.lock_counter > 0:
            self.lock_counter -= 1

        score_panic = self._get_brain_score('panic', price_data)
        score_bull = self._get_brain_score('bull', price_data)

        # Decision Pipeline
        if score_panic > self.genome['panic']['t']:
            new_holdings = {"CASH": 1.0}
        elif score_bull > self.genome['bull']['t']:
            new_holdings = {"3xSPY": 1.0}
        else:
            new_holdings = {"CASH": 1.0}

        # Calculate Conviction "Fight" (Softmax between brain leads)
        margin_panic = score_panic - self.genome['panic']['t']
        margin_bull = score_bull - self.genome['bull']['t']
        
        e_p = np.exp(margin_panic)
        e_b = np.exp(margin_bull)
        e_n = np.exp(0)
        denom = e_p + e_b + e_n
        
        telemetry = {
            "conf_cash": float(e_p / denom),
            "conf_1x": float(e_n / denom),
            "conf_2x": 0.0,
            "conf_3x": float(e_b / denom),
            "score_panic": float(score_panic),
            "score_bull": float(score_bull),
            "threshold_panic": float(self.genome['panic']['t']),
            "threshold_bull": float(self.genome['bull']['t'])
        }

        # Calculate Feature Importance for "Decision Engine Anatomy"
        importance = {}
        indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']
        for ind in indicators:
            active = self.genome['panic']['a'].get(ind, True) or self.genome['bull']['a'].get(ind, True)
            if not active: continue

            w_p = abs(self.genome['panic']['w'].get(ind, 0))
            w_b = abs(self.genome['bull']['w'].get(ind, 0))
            
            # Pick lookback from the brain with the higher weight for this feature
            lb_key = 'macd_f' if ind == 'macd' else ind
            if w_p > w_b:
                lookback = self.genome['panic']['lookbacks'].get(lb_key, 0)
            else:
                lookback = self.genome['bull']['lookbacks'].get(lb_key, 0)
            
            importance[ind] = {
                "panic": float(w_p),
                "bull": float(w_b),
                "period": int(round(lookback)) if isinstance(lookback, (int, float)) else 0
            }
        telemetry["importance"] = importance

        # Apply lockout
        if new_holdings != self.last_holdings:
            is_panic = (new_holdings.get("CASH") == 1.0 and score_panic > self.genome['panic']['t'])
            if self.lock_counter == 0 or is_panic:
                self.last_holdings = new_holdings
                self.lock_counter = max(0, int(round(self.genome.get('lock_days', 0))))
                return new_holdings, telemetry
            
        return self.last_holdings, telemetry
