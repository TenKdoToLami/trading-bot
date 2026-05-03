"""
Genome V6 Balancer — Probabilistic Allocator.
4-State Softmax: CASH (0x), SPY (1x), 2x SPY, 3x SPY.
Smooth transitions based on brain confidence levels.
Shared lookbacks for unified market perception.
"""

import math
import numpy as np
from strategies.base import BaseStrategy
from src.tournament.registry import register_strategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility,
    mfi, bollinger_width
)

def softmax(x, temp=1.0):
    """Numerically stable softmax."""
    x = np.array(x) / temp
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

from src.tournament.market_state import MarketState

@register_strategy(["v6_balancer", 6.0])
class GenomeV6(BaseStrategy):
    NAME = "[GENE] V6 | (Balancer)"
    version = 6

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.market = MarketState()
        self.reset()

    def _default_genome(self):
        # ... (keep same)
        indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc', 'mfi', 'bbw']
        return {
            'brains': {
                'cash': {'w': {k: 0.0 for k in indicators}, 'a': {k: True for k in indicators}},
                '1x':    {'w': {k: 0.0 for k in indicators}, 'a': {k: True for k in indicators}},
                '2x':    {'w': {k: 0.0 for k in indicators}, 'a': {k: True for k in indicators}},
                '3x':    {'w': {k: 0.0 for k in indicators}, 'a': {k: True for k in indicators}}
            },
            'lookbacks': {
                'sma': 200, 'ema': 50, 'rsi': 14, 'macd_f': 12, 'macd_s': 26,
                'adx': 14, 'trix': 15, 'slope': 20, 'vol': 20, 'atr': 14,
                'mfi': 14, 'bbw': 20
            },
            'temp': 1.0,
            'lock_days': 2,
            'version': 6.0
        }

    def reset(self):
        self.market = MarketState()
        self.last_holdings = None
        self.lock_counter = 0

    def _get_brain_scores(self, price_data):
        lb = self.genome.get('lookbacks', {})
        m = self.market
        
        if not m.prices: return [0.0, 0.0, 0.0, 0.0]
        
        # Unified Feature Pipeline
        p = m.last_price
        v = {}
        v['sma'] = m.get_indicator('sma', lb.get('sma', 200))
        v['ema'] = m.get_indicator('ema', lb.get('ema', 50))
        v['rsi'] = m.get_indicator('rsi', lb.get('rsi', 14))
        v['macd'] = m.get_indicator('macd', lb.get('macd_f', 12), slow=lb.get('macd_s', 26))
        v['adx'] = m.get_indicator('adx', lb.get('adx', 14))
        v['trix'] = m.get_indicator('trix', lb.get('trix', 15))
        v['slope'] = m.get_indicator('slope', lb.get('slope', 20))
        v['vol'] = m.get_indicator('vol', lb.get('vol', 20))
        v['atr'] = m.get_indicator('atr', lb.get('atr', 14))
        v['mfi'] = m.get_indicator('mfi', lb.get('mfi', 14))
        v['bbw'] = m.get_indicator('bbw', lb.get('bbw', 20))
        
        feat = {
            'sma': ((p - v['sma']) / v['sma'] * 5) if v['sma'] else 0.0,
            'ema': ((p - v['ema']) / v['ema'] * 10) if v['ema'] else 0.0,
            'rsi': ((v['rsi'] or 50) - 50) / 50.0,
            'macd': (v['macd'] / p * 100) if v['macd'] else 0.0,
            'adx': ((v['adx'] or 25) - 25) / 25.0,
            'trix': v['trix'] or 0.0,
            'slope': (v['slope'] or 0.0) / p * 1000,
            'vol': (v['vol'] or 0.15) * 5,
            'atr': ((v['atr'] or 0.0) / p) * 50,
            'mfi': ((v['mfi'] or 50) - 50) / 50.0,
            'bbw': (v['bbw'] or 0.05) * 10,
            'vix': (m.get_macro('vix', 15.0) - 20) / 10.0,
            'yc': m.get_macro('yield_curve', 0.0)
        }
        
        scores = []
        for key in ['cash', '1x', '2x', '3x']:
            brain = self.genome['brains'][key]
            score = sum(brain['w'][k] * feat[k] for k in brain['w'] if brain['a'].get(k, True))
            score += brain.get('t', 0.0)
            scores.append(score)
        return scores

    def on_data(self, date, price_data, prev_data):
        self.market.update(date, price_data)

        if self.lock_counter > 0: self.lock_counter -= 1

        probs = softmax(self._get_brain_scores(price_data), temp=self.genome.get('temp', 1.0))
        
        new_holdings = {
            "CASH": float(probs[0]),
            "SPY": float(probs[1]),
            "2xSPY": float(probs[2]),
            "3xSPY": float(probs[3])
        }

        # 4. Telemetry (Confidence & Importance)
        telemetry = {
            "conf_cash": float(probs[0]),
            "conf_1x": float(probs[1]),
            "conf_2x": float(probs[2]),
            "conf_3x": float(probs[3])
        }
        
        # Calculate Feature Importance for "Decision Engine Anatomy"
        importance = {}
        indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc', 'mfi', 'bbw']
        lb = self.genome.get('lookbacks', {})
        for ind in indicators:
            imp = 0
            for b_name in ['cash', '1x', '2x', '3x']:
                imp += abs(self.genome['brains'][b_name]['w'].get(ind, 0))
            
            # Map simple indicator names to lookback keys
            lb_key = 'macd_f' if ind == 'macd' else ind
            lookback = lb.get(lb_key, 0)
            
            importance[ind] = {
                "weight": imp / 4.0,
                "period": int(round(lookback)) if isinstance(lookback, (int, float)) else 0
            }
        telemetry["importance"] = importance

        # 5. Threshold to avoid tiny rebalances (slippage protection)
        max_diff = 0
        if self.last_holdings:
            for k in new_holdings:
                diff = abs(new_holdings[k] - self.last_holdings.get(k, 0))
                if diff > max_diff: max_diff = diff
            
            if max_diff < 0.05 and self.lock_counter > 0:
                return self.last_holdings, telemetry

        if self.lock_counter == 0 or max_diff > 0.15: # Force if big move
            self.last_holdings = new_holdings
            self.lock_counter = max(0, int(round(self.genome.get('lock_days', 0))))
            return new_holdings, telemetry
            
        return self.last_holdings, telemetry
