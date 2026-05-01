"""
Genome V7 Deep Fluid Strategy — Neural Portfolio Distribution.
Instead of discrete switching, it uses a Softmax layer to distribute 
capital across all 4 tiers (CASH, 1x, 2x, 3x) simultaneously.
"""

import numpy as np
from strategies.base import BaseStrategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility, mfi, bollinger_bands
)

class GenomeV7DeepFluid(BaseStrategy):
    NAME = "Genome V7 (Deep Fluid)"

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.reset()
        
        # Pre-cache matrices
        self.w1 = np.array(self.genome['layers'][0]['w'])
        self.b1 = np.array(self.genome['layers'][0]['b'])
        self.w2 = np.array(self.genome['layers'][1]['w'])
        self.b2 = np.array(self.genome['layers'][1]['b'])

    def _default_genome(self):
        # 13 Inputs -> 24 Hidden -> 4 Outputs (CASH, 1x, 2x, 3x)
        return {
            'version': 7.2,
            'layers': [
                {
                    'w': np.random.uniform(-1, 1, (13, 24)).tolist(),
                    'b': np.zeros(24).tolist()
                },
                {
                    'w': np.random.uniform(-1, 1, (24, 4)).tolist(),
                    'b': np.zeros(4).tolist()
                }
            ],
            'lookbacks': {
                'sma': 200, 'ema': 50, 'rsi': 14, 'macd_f': 12, 'macd_s': 26,
                'adx': 14, 'trix': 15, 'slope': 20, 'vol': 20, 'atr': 14,
                'mfi': 14, 'bb': 20
            },
            'lock_days': 2.0,
            'rebalance_threshold': 0.05 # Only trade if > 5% weight change (friction protection)
        }

    def reset(self):
        self.prices = []
        self.highs = []
        self.lows = []
        self.volumes = []
        self.prev_ema = None
        self.prev_atr = None
        self.indicator_state = {}
        self.current_holdings = {"CASH": 1.0}
        self.lock_counter = 0

    def _softmax(self, x):
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()

    def _relu(self, x):
        return np.maximum(0, x)

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        self.prices.append(spy_price)
        self.highs.append(price_data['high'])
        self.lows.append(price_data['low'])
        self.volumes.append(price_data.get('volume', 0))

        if self.lock_counter > 0:
            self.lock_counter -= 1

        lb = self.genome['lookbacks']
        
        # 1. Indicators
        val_sma = sma(self.prices, lb['sma'])
        val_ema = ema(self.prices, lb['ema'], prev_ema=self.prev_ema)
        self.prev_ema = val_ema
        val_rsi = rsi(self.prices, lb['rsi'], state=self.indicator_state)
        val_macd_tuple = macd(self.prices, lb['macd_f'], lb['macd_s'], state=self.indicator_state)
        val_macd = val_macd_tuple[0] if val_macd_tuple[0] is not None else 0.0
        val_adx = adx(self.highs, self.lows, self.prices, lb['adx'], state=self.indicator_state)
        val_trix = trix(self.prices, lb['trix'], state=self.indicator_state)
        val_slope = linear_regression_slope(self.prices, lb['slope'])
        val_vol = realized_volatility(self.prices, lb['vol'])
        val_atr = atr(self.highs, self.lows, self.prices, lb['atr'], prev_atr=self.prev_atr)
        self.prev_atr = val_atr
        val_mfi = mfi(self.highs, self.lows, self.prices, self.volumes, lb['mfi'])
        bb_res = bollinger_bands(self.prices, lb['bb'])
        val_bbw = (bb_res[0] - bb_res[2]) / bb_res[1] if bb_res[1] else 0.0

        # 2. Normalize Inputs
        macro_vix = float(price_data.get('vix', 15.0))
        macro_yc = float(price_data.get('yield_curve', 0.0))
        
        inputs = np.array([
            ((spy_price - val_sma) / val_sma * 5) if val_sma else 0.0,
            ((spy_price - val_ema) / val_ema * 10) if val_ema else 0.0,
            ((val_rsi or 50) - 50) / 50.0,
            val_macd / spy_price * 100,
            ((val_adx or 25) - 25) / 25.0,
            val_trix or 0.0,
            (val_slope or 0.0) / spy_price * 1000,
            (val_vol or 0.15) * 5,
            ((val_atr or 0.0) / spy_price) * 50,
            (macro_vix - 20) / 10.0,
            macro_yc,
            ((val_mfi or 50) - 50) / 50.0,
            val_bbw * 10
        ])

        # 3. Inference
        h1 = self._relu(np.dot(inputs, self.w1) + self.b1)
        scores = np.dot(h1, self.w2) + self.b2
        
        # 4. Distribution (Softmax)
        probs = self._softmax(scores)
        
        # Mapping: 0=CASH, 1=1x, 2=2x, 3=3x
        target_holdings = {}
        if probs[0] > 0.01: target_holdings["CASH"] = probs[0]
        if probs[1] > 0.01: target_holdings["SPY"] = probs[1]
        if probs[2] > 0.01: target_holdings["2xSPY"] = probs[2]
        if probs[3] > 0.01: target_holdings["3xSPY"] = probs[3]
        
        # Normalize in case we clipped tiny positions
        total = sum(target_holdings.values())
        target_holdings = {k: v/total for k, v in target_holdings.items()}

        # 5. Telemetry
        telemetry = {
            "conf_cash": float(probs[0]),
            "conf_1x": float(probs[1]),
            "conf_2x": float(probs[2]),
            "conf_3x": float(probs[3])
        }

        # 6. Friction Protection: Rebalance Threshold
        # Calculate total difference (L1 norm) between current and target
        diff = 0
        all_keys = set(target_holdings.keys()) | set(self.current_holdings.keys())
        for k in all_keys:
            diff += abs(target_holdings.get(k, 0) - self.current_holdings.get(k, 0))
            
        threshold = self.genome.get('rebalance_threshold', 0.05)
        if diff >= threshold and self.lock_counter == 0:
            self.current_holdings = target_holdings
            self.lock_counter = max(0, int(round(self.genome.get('lock_days', 2.0))))
            return target_holdings, telemetry
            
        return self.current_holdings, telemetry
