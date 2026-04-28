"""
Genome V5 Sniper — Tiered Entry Specialist.
Binary State: Always 1x SPY (Baseline), fades into 2x and 3x based on brain score.
No CASH state. No Panic brain.
"""

from strategies.base import BaseStrategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility
)

class GenomeV5Sniper(BaseStrategy):
    NAME = "[GENE] V5 | (Tiered Sniper)"

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.reset()

    def _default_genome(self):
        return {
            'sniper': {
                'w': {k: 0.0 for k in ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']},
                'a': {k: True for k in ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']},
                't_low': 1.0,
                't_high': 2.5,
                'lookbacks': {
                    'sma': 200, 'ema': 50, 'rsi': 14, 'macd_f': 12, 'macd_s': 26,
                    'adx': 14, 'trix': 15, 'slope': 20, 'vol': 20, 'atr': 14
                }
            },
            'lock_days': 3,
            'version': 5.0
        }

    def reset(self):
        self.prices = []
        self.highs = []
        self.lows = []
        self.brain_state = {}
        self.last_holdings = None
        self.lock_counter = 0

    def _get_brain_score(self, price_data, shared_cache):
        spy_price = self.prices[-1]
        brain = self.genome['sniper']
        lb = brain.get('lookbacks', {})
        state = self.brain_state

        def _fetch(key, func, *args, **kwargs):
            lookback = int(round(lb.get(key, 200)))
            cache_key = (key, lookback)
            if cache_key in shared_cache: return shared_cache[cache_key]
            if 'state' in kwargs: res = func(*args, **kwargs)
            else: res = func(*args, period=lookback)
            shared_cache[cache_key] = res
            return res

        # Indicators
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

        # Normalize and Score
        macro_vix = float(price_data.get('vix', 15.0))
        macro_yc = float(price_data.get('yield_curve', 0.0))
        
        total_score = 0
        w, a = brain['w'], brain['a']
        
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

        if self.lock_counter > 0: self.lock_counter -= 1

        shared_cache = {}
        score = self._get_brain_score(price_data, shared_cache)
        brain = self.genome['sniper']

        # Tiered Sniper Logic
        if score > brain['t_high']:
            new_holdings = {"3xSPY": 1.0}
        elif score > brain['t_low']:
            new_holdings = {"2xSPY": 1.0}
        else:
            new_holdings = {"SPY": 1.0}

        # Lockout logic
        if new_holdings != self.last_holdings:
            if self.lock_counter == 0:
                self.last_holdings = new_holdings
                self.lock_counter = max(0, int(round(self.genome.get('lock_days', 0))))
                return new_holdings
            
        return None
