"""
Genome V6 Balancer — Probabilistic Allocator.
4-State Softmax: CASH (0x), SPY (1x), 2x SPY, 3x SPY.
Smooth transitions based on brain confidence levels.
Shared lookbacks for unified market perception.
"""

import math
import numpy as np
from strategies.base import BaseStrategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility
)

def softmax(x, temp=1.0):
    """Numerically stable softmax."""
    x = np.array(x) / temp
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

class GenomeV6(BaseStrategy):
    NAME = "[GENE] V6 | (Balancer)"

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.reset()

    def _default_genome(self):
        indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']
        return {
            'brains': {
                'cash': {'w': {k: 0.0 for k in indicators}, 'a': {k: True for k in indicators}},
                '1x':    {'w': {k: 0.0 for k in indicators}, 'a': {k: True for k in indicators}},
                '2x':    {'w': {k: 0.0 for k in indicators}, 'a': {k: True for k in indicators}},
                '3x':    {'w': {k: 0.0 for k in indicators}, 'a': {k: True for k in indicators}}
            },
            'lookbacks': {
                'sma': 200, 'ema': 50, 'rsi': 14, 'macd_f': 12, 'macd_s': 26,
                'adx': 14, 'trix': 15, 'slope': 20, 'vol': 20, 'atr': 14
            },
            'temp': 1.0,
            'lock_days': 2,
            'version': 6.0
        }

    def reset(self):
        self.prices = []
        self.highs = []
        self.lows = []
        self.brain_state = {}
        self.last_holdings = None
        self.lock_counter = 0

    def _get_brain_scores(self, price_data, shared_cache):
        spy_price = self.prices[-1]
        lb = self.genome.get('lookbacks', {})
        state = self.brain_state

        def _fetch(key, func, *args, **kwargs):
            lookback = int(round(lb.get(key, 200)))
            cache_key = (key, lookback)
            if cache_key in shared_cache: return shared_cache[cache_key]
            if 'state' in kwargs: res = func(*args, **kwargs)
            else: res = func(*args, period=lookback)
            shared_cache[cache_key] = res
            return res

        # 1. Fetch Shared Indicators
        val_sma = _fetch('sma', sma, self.prices)
        val_ema = ema(self.prices, max(2, int(round(lb.get('ema', 50)))), prev_ema=state.get('prev_ema'))
        state['prev_ema'] = val_ema
        val_rsi = rsi(self.prices, max(2, int(round(lb.get('rsi', 14)))), state=state)
        
        m_f, m_s = max(2, int(round(lb.get('macd_f', 12)))), max(3, int(round(lb.get('macd_s', 26))))
        val_macd_tuple = macd(self.prices, m_f, m_s, state=state)
        val_macd = val_macd_tuple[0] if val_macd_tuple[0] is not None else 0.0

        val_adx = adx(self.highs, self.lows, self.prices, max(2, int(round(lb.get('adx', 14)))), state=state)
        val_trix = trix(self.prices, max(2, int(round(lb.get('trix', 15)))), state=state)
        val_slope = _fetch('slope', linear_regression_slope, self.prices)
        val_vol = _fetch('vol', realized_volatility, self.prices)
        val_atr = atr(self.highs, self.lows, self.prices, max(2, int(round(lb.get('atr', 14)))), prev_atr=state.get('prev_atr'))
        state['prev_atr'] = val_atr

        macro_vix = float(price_data.get('vix', 15.0))
        macro_yc = float(price_data.get('yield_curve', 0.0))
        
        # 2. Calculate scores for each brain
        scores = {}
        for b_name, b_data in self.genome['brains'].items():
            total = 0
            w, a = b_data['w'], b_data['a']
            if a.get('sma', True) and val_sma: total += w['sma'] * ((spy_price - val_sma) / val_sma * 5)
            if a.get('ema', True) and val_ema: total += w['ema'] * ((spy_price - val_ema) / val_ema * 10)
            if a.get('rsi', True) and val_rsi: total += w['rsi'] * ((val_rsi - 50) / 50.0)
            if a.get('macd', True): total += w['macd'] * (val_macd / spy_price * 100)
            if a.get('adx', True) and val_adx: total += w['adx'] * ((val_adx - 25) / 25.0)
            if a.get('trix', True) and val_trix: total += w['trix'] * val_trix
            if a.get('slope', True) and val_slope: total += w['slope'] * (val_slope / spy_price * 1000)
            if a.get('vol', True) and val_vol: total += w['vol'] * (val_vol * 5)
            if a.get('atr', True) and val_atr: total += w['atr'] * ((val_atr / spy_price) * 50)
            if a.get('vix', True): total += w['vix'] * ((macro_vix - 20) / 10.0)
            if a.get('yc', True): total += w['yc'] * macro_yc
            scores[b_name] = total
            
        return scores

    def on_data(self, date, price_data, prev_data):
        self.prices.append(price_data['close'])
        self.highs.append(price_data['high'])
        self.lows.append(price_data['low'])

        if self.lock_counter > 0: self.lock_counter -= 1

        shared_cache = {}
        scores = self._get_brain_scores(price_data, shared_cache)
        
        # Softmax to probabilities
        brain_order = ['cash', '1x', '2x', '3x']
        raw_vals = [scores[b] for b in brain_order]
        probs = softmax(raw_vals, temp=self.genome.get('temp', 1.0))
        
        new_holdings = {
            "CASH": float(probs[0]),
            "SPY": float(probs[1]),
            "2xSPY": float(probs[2]),
            "3xSPY": float(probs[3])
        }

        # Threshold to avoid tiny rebalances (slippage protection)
        # We only rebalance if the largest change in weight is > 5%
        if self.last_holdings:
            max_diff = 0
            for k in new_holdings:
                diff = abs(new_holdings[k] - self.last_holdings.get(k, 0))
                if diff > max_diff: max_diff = diff
            
            if max_diff < 0.05 and self.lock_counter > 0:
                return None

        if self.lock_counter == 0 or (self.last_holdings and max_diff > 0.15): # Force if big move
            self.last_holdings = new_holdings
            self.lock_counter = max(0, int(round(self.genome.get('lock_days', 0))))
            return new_holdings
            
        return None
