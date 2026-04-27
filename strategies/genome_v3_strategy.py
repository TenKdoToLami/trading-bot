"""
Genome V3 Strategy — Precision Binary Architecture.
Focuses entirely on 3x vs Cash.
Evolves both the indicator weights AND the indicator lookback periods.
"""

from strategies.base import BaseStrategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility
)

class GenomeV3Strategy(BaseStrategy):
    NAME = "Genome V3 (Precision Binary)"

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

    def _get_brain_score(self, brain_key, price_data):
        spy_price = self.prices[-1]
        brain = self.genome[brain_key]
        lb = brain.get('lookbacks', self._default_genome()['panic']['lookbacks'])
        state = self.brain_states[brain_key]

        # 1. Calculate Indicators using brain-specific dynamic lookbacks
        val_sma = sma(self.prices, max(2, int(round(lb.get('sma', 200)))))
        
        val_ema = ema(self.prices, max(2, int(round(lb.get('ema', 50)))), prev_ema=state.get('prev_ema'))
        state['prev_ema'] = val_ema
        
        val_rsi = rsi(self.prices, max(2, int(round(lb.get('rsi', 14)))), state=state)
        
        macd_f = max(2, int(round(lb.get('macd_f', 12))))
        macd_s = max(macd_f + 1, int(round(lb.get('macd_s', 26))))
        val_macd_tuple = macd(self.prices, macd_f, macd_s, state=state)
        val_macd = val_macd_tuple[0] if val_macd_tuple[0] is not None else 0.0
        
        val_adx = adx(self.highs, self.lows, self.prices, max(2, int(round(lb.get('adx', 14)))), state=state)
        val_trix = trix(self.prices, max(2, int(round(lb.get('trix', 15)))), state=state)
        val_slope = linear_regression_slope(self.prices, max(2, int(round(lb.get('slope', 20)))))
        val_vol = realized_volatility(self.prices, max(2, int(round(lb.get('vol', 20)))))
        
        val_atr = atr(self.highs, self.lows, self.prices, max(2, int(round(lb.get('atr', 14)))), prev_atr=state.get('prev_atr'))
        state['prev_atr'] = val_atr

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

        # 3. Score
        return sum(brain['w'][k] * inputs[k] for k in brain['w'] if brain['a'].get(k, True))


    def on_data(self, date, price_data, prev_data):
        self.prices.append(price_data['close'])
        self.highs.append(price_data['high'])
        self.lows.append(price_data['low'])

        if self.lock_counter > 0:
            self.lock_counter -= 1

        # We must call _get_brain_score for BOTH brains every day 
        # so that their internal EMAs and states stay updated!
        score_panic = self._get_brain_score('panic', price_data)
        score_bull = self._get_brain_score('bull', price_data)

        # Decision Pipeline
        if score_panic > self.genome['panic']['t']:
            new_holdings = {"CASH": 1.0}
        elif score_bull > self.genome['bull']['t']:
            new_holdings = {"3xSPY": 1.0}
        else:
            new_holdings = {"CASH": 1.0}

        # Apply lockout
        if new_holdings != self.last_holdings:
            is_panic = (new_holdings.get("CASH") == 1.0 and score_panic > self.genome['panic']['t'])
            if self.lock_counter == 0 or is_panic:
                self.last_holdings = new_holdings
                self.lock_counter = max(0, int(round(self.genome.get('lock_days', 0))))
                return new_holdings
            
        return None
