"""
Genome V9 Confidence Spread Strategy — Hysteresis-based Leverage Control.
Analyses signals to produce confidence scores for 0x, 1x, 2x, and 3x.
Uses a stickiness/hysteresis mechanism to maintain positions and reduce slippage.
"""

import numpy as np
from strategies.base import BaseStrategy
from src.tournament.registry import register_strategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility, mfi, bollinger_bands
)

@register_strategy(["v9_confidence", 9.0])
class GenomeV9Confidence(BaseStrategy):
    NAME = "Genome V9 (Confidence Spread)"
    version = 9

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.reset()
        
        # Pre-cache layers
        self.w1 = np.array(self.genome['layers'][0]['w'])
        self.b1 = np.array(self.genome['layers'][0]['b'])
        self.w2 = np.array(self.genome['layers'][1]['w'])
        self.b2 = np.array(self.genome['layers'][1]['b'])
        
        # Mapping for output indices to asset sets
        self.state_map = {
            0: {"CASH": 1.0},
            1: {"SPY": 1.0},
            2: {"2xSPY": 1.0},
            3: {"3xSPY": 1.0}
        }

    def _default_genome(self):
        # 13 Inputs -> 24 Hidden -> 4 Outputs (Confidence for CASH, 1x, 2x, 3x)
        return {
            'version': 9.0,
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
            'hysteresis': 0.15,       # Confidence lead required to switch states
            'lock_days': 3.0,         # Minimum hold after switch
            'smoothing': 0.5          # Signal smoothing (1.0 = no smoothing)
        }

    def reset(self):
        self.prices = []
        self.highs = []
        self.lows = []
        self.volumes = []
        self.prev_ema = None
        self.prev_atr = None
        self.indicator_state = {}
        
        self.current_state_idx = 0     # Start in CASH
        self.current_holdings = {"CASH": 1.0}
        self.lock_counter = 0
        self.smoothed_scores = np.zeros(4)

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

        # 3. Neural Inference
        h1 = self._relu(np.dot(inputs, self.w1) + self.b1)
        raw_scores = np.dot(h1, self.w2) + self.b2
        probs = self._softmax(raw_scores)
        
        # 4. Signal Smoothing (Low pass filter on confidence)
        alpha = self.genome.get('smoothing', 0.5)
        self.smoothed_scores = alpha * probs + (1 - alpha) * self.smoothed_scores
        
        # 5. Hysteresis Decision Engine
        best_state_idx = np.argmax(self.smoothed_scores)
        current_conf = self.smoothed_scores[self.current_state_idx]
        best_conf = self.smoothed_scores[best_state_idx]
        
        hysteresis = self.genome.get('hysteresis', 0.15)
        
        # 6. Prepare Telemetry
        features = [
            ('SMA Dist', 'sma'), ('EMA Dist', 'ema'), ('RSI', 'rsi'), ('MACD', 'macd_f'),
            ('ADX', 'adx'), ('TRIX', 'trix'), ('Slope', 'slope'), ('Vol', 'vol'),
            ('ATR', 'atr'), ('VIX', None), ('Yield Curve', None), ('MFI', 'mfi'), ('BBW', 'bb')
        ]
        
        importance = {}
        for i, (feat_name, lb_key) in enumerate(features):
            w_imp = float(np.mean(np.abs(self.w1[i, :])))
            period = int(round(lb.get(lb_key, 0))) if lb_key else 0
            importance[feat_name] = {"weight": w_imp, "period": period}

        telemetry = {
            "conf_cash": float(self.smoothed_scores[0]),
            "conf_1x": float(self.smoothed_scores[1]),
            "conf_2x": float(self.smoothed_scores[2]),
            "conf_3x": float(self.smoothed_scores[3]),
            "importance": importance
        }

        # Only switch if the best state is significantly better than current state
        # AND we are not locked
        if best_state_idx != self.current_state_idx:
            if best_conf > current_conf + hysteresis and self.lock_counter == 0:
                self.current_state_idx = best_state_idx
                self.current_holdings = self.state_map[best_state_idx]
                self.lock_counter = int(round(self.genome.get('lock_days', 3.0)))
                return self.current_holdings, telemetry
                
        return self.current_holdings, telemetry # Return current even if no change to keep telemetry flowing
