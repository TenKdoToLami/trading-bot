"""
Genome V3 Strategy — Precision Binary Architecture.
Focuses entirely on 3x vs Cash.
Evolves both the indicator weights AND the indicator lookback periods.
"""

import numpy as np
from strategies.base import BaseStrategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility
)

class GenomeV3Strategy(BaseStrategy):
    NAME = "Genome V3 (Precision Binary)"
    version = 3

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.reset()

    def _default_genome(self):
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
        self.prices = []
        self.highs = []
        self.lows = []
        
        # Isolated state per brain
        self.brain_states = {
            'panic': {},
            'bull': {}
        }
        
        self.last_holdings = None
        self.lock_counter = 0

    def _get_brain_score(self, brain_key, price_data, shared_cache):
        spy_price = self.prices[-1]
        brain = self.genome[brain_key]
        lb = brain.get('lookbacks', {})
        state = self.brain_states[brain_key]

        # Use a local function to fetch or calculate (with shared cache)
        def _fetch(key, func, *args, **kwargs):
            lookback = int(round(lb.get(key, 200)))
            cache_key = (key, lookback)
            if cache_key in shared_cache:
                return shared_cache[cache_key]
            
            # Use specific state for stateful indicators
            if 'state' in kwargs:
                # We can't easily share cache for stateful indicators 
                # because each brain has its own EMA trail
                res = func(*args, **kwargs)
            else:
                res = func(*args, period=lookback)
                shared_cache[cache_key] = res
            return res

        # 1. Calculate Indicators
        val_sma = _fetch('sma', sma, self.prices)
        val_ema = ema(self.prices, max(2, int(round(lb.get('ema', 50)))), prev_ema=state.get('prev_ema'))
        state['prev_ema'] = val_ema
        
        val_rsi = rsi(self.prices, max(2, int(round(lb.get('rsi', 14)))), state=state)
        
        m_f = max(2, int(round(lb.get('macd_f', 12))))
        m_s = max(m_f + 1, int(round(lb.get('macd_s', 26))))
        val_macd_tuple = macd(self.prices, m_f, m_s, state=state)
        val_macd = val_macd_tuple[0] if val_macd_tuple[0] is not None else 0.0
        
        val_adx = adx(self.highs, self.lows, self.prices, max(2, int(round(lb.get('adx', 14)))), state=state)
        val_trix = trix(self.prices, max(2, int(round(lb.get('trix', 15)))), state=state)
        val_slope = _fetch('slope', linear_regression_slope, self.prices)
        val_vol = _fetch('vol', realized_volatility, self.prices)
        
        val_atr = atr(self.highs, self.lows, self.prices, max(2, int(round(lb.get('atr', 14)))), prev_atr=state.get('prev_atr'))
        state['prev_atr'] = val_atr

        # 2. Normalize and Score
        macro_vix = float(price_data.get('vix', 15.0))
        macro_yc = float(price_data.get('yield_curve', 0.0))
        
        # Inlining the sum for speed
        total_score = 0
        w = brain['w']
        a = brain['a']
        
        if a.get('sma', True) and val_sma: total_score += w['sma'] * ((spy_price - val_sma) / val_sma * 5)
        if a.get('ema', True) and val_ema: total_score += w['ema'] * ((spy_price - val_ema) / val_ema * 10)
        if a.get('rsi', True) and val_rsi: total_score += w['rsi'] * ((val_rsi - 50) / 50.0)
        if a.get('macd', True): total_score += w['macd'] * (val_macd / spy_price * 100)
        if a.get('adx', True) and val_adx: total_score += w['adx'] * ((val_adx - 25) / 25.0)
        if a.get('trix', True) and val_trix: total_score += w['trix'] * val_trix
        if a.get('slope', True) and val_slope: total_score += w['slope'] * (val_slope / spy_price * 1000)
        if a.get('vol', True) and val_vol: total_score += w['vol'] * (val_vol * 5)
        if a.get('atr', True) and val_atr: total_score += w['atr'] * ((val_atr / spy_price) * 50)
        if a.get('vix', True): total_score += w['vix'] * ((macro_vix - 20) / 10.0)
        if a.get('yc', True): total_score += w['yc'] * macro_yc
        
        return total_score


    def on_data(self, date, price_data, prev_data):
        self.prices.append(price_data['close'])
        self.highs.append(price_data['high'])
        self.lows.append(price_data['low'])

        if self.lock_counter > 0:
            self.lock_counter -= 1

        shared_cache = {}
        score_panic = self._get_brain_score('panic', price_data, shared_cache)
        score_bull = self._get_brain_score('bull', price_data, shared_cache)

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
