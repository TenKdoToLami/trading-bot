"""
Genome V5 Sniper — Tiered Entry Specialist.
Binary State: Always 1x SPY (Baseline), fades into 2x and 3x based on brain score.
No CASH state. No Panic brain.
"""

from strategies.base import BaseStrategy
from src.tournament.registry import register_strategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility
)

from src.tournament.market_state import MarketState

@register_strategy(["v5_sniper", 5.0])
class GenomeV5Sniper(BaseStrategy):
    NAME = "[GENE] V5 | (Tiered Sniper)"

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.market = MarketState()
        self.reset()

    def _default_genome(self):
        # ... (keep same)
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
        self.market = MarketState()
        self.last_holdings = None
        self.lock_counter = 0

    def _get_brain_score(self, price_data):
        brain = self.genome['sniper']
        lb = brain.get('lookbacks', {})
        m = self.market
        
        if not m.prices: return 0.0
        
        total_score = 0.0
        w, a = brain['w'], brain['a']
        p = m.last_price
        
        if a.get('sma', True):
            v = m.get_indicator('sma', lb.get('sma', 200))
            if v: total_score += w['sma'] * ((p - v) / v * 5)
            
        if a.get('ema', True):
            v = m.get_indicator('ema', lb.get('ema', 50))
            if v: total_score += w['ema'] * ((p - v) / v * 10)
            
        if a.get('rsi', True):
            v = m.get_indicator('rsi', lb.get('rsi', 14))
            if v: total_score += w['rsi'] * ((v - 50) / 50.0)
            
        if a.get('macd', True):
            v = m.get_indicator('macd', lb.get('macd_f', 12), slow=lb.get('macd_s', 26))
            if v: total_score += w['macd'] * (v / p * 100)
            
        if a.get('adx', True):
            v = m.get_indicator('adx', lb.get('adx', 14))
            if v: total_score += w['adx'] * ((v - 25) / 25.0)
            
        if a.get('trix', True):
            v = m.get_indicator('trix', lb.get('trix', 15))
            if v: total_score += w['trix'] * v
            
        if a.get('slope', True):
            v = m.get_indicator('slope', lb.get('slope', 20))
            if v: total_score += w['slope'] * (v / p * 1000)
            
        if a.get('vol', True):
            v = m.get_indicator('vol', lb.get('vol', 20))
            if v: total_score += w['vol'] * (v * 5)
            
        if a.get('atr', True):
            v = m.get_indicator('atr', lb.get('atr', 14))
            if v: total_score += w['atr'] * ((v / p) * 50)
            
        total_score += w['vix'] * ((m.get_macro('vix', 15.0) - 20) / 10.0)
        total_score += w['yc'] * m.get_macro('yield_curve', 0.0)
        
        return total_score
    def on_data(self, date, price_data, prev_data):
        self.market.update(date, price_data)

        if self.lock_counter > 0: self.lock_counter -= 1

        score = self._get_brain_score(price_data)
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
