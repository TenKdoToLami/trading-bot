"""
Genome V11 Seasonal & Macro Strategy.
Expanded input layer with:
- Seasonality (Month Sin/Cos)
- Turn-of-the-Month awareness
- Credit Spread (BAA10Y)
- Intraday Trigger (Confidence)
"""

import numpy as np
import pandas as pd
from strategies.base import BaseStrategy
from src.tournament.registry import register_strategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility, mfi, bollinger_bands
)

@register_strategy(["v11_seasonal", 11.0])
class GenomeV11Seasonal(BaseStrategy):
    NAME = "Genome V11 (Seasonal & Macro)"
    version = 11.0
    IS_INTRA = True

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.reset()
        
        # Neural Weights
        self.w1 = np.array(self.genome['layers'][0]['w'])
        self.b1 = np.array(self.genome['layers'][0]['b'])
        self.w2 = np.array(self.genome['layers'][1]['w'])
        self.b2 = np.array(self.genome['layers'][1]['b'])
        
        self.state_map = {
            0: {"CASH": 1.0},
            1: {"SPY": 1.0},
            2: {"2xSPY": 1.0},
            3: {"3xSPY": 1.0}
        }

    def _default_genome(self):
        # 18 Inputs -> 32 Hidden -> 4 Outputs
        return {
            'version': 11.0,
            'layers': [
                {
                    'w': np.random.uniform(-0.5, 0.5, (18, 32)).tolist(),
                    'b': np.zeros(32).tolist()
                },
                {
                    'w': np.random.uniform(-1, 1, (32, 4)).tolist(),
                    'b': np.zeros(4).tolist()
                }
            ],
            'lookbacks': {
                'sma': 200, 'ema': 50, 'rsi': 14, 'macd_f': 12, 'macd_s': 26,
                'adx': 14, 'trix': 15, 'slope': 20, 'vol': 20, 'atr': 14,
                'mfi': 14, 'bb': 20
            },
            'hysteresis': 0.15,
            'smoothing': 0.5
        }
    def reset(self):
        self.prices = []
        self.highs = []
        self.lows = []
        self.volumes = []
        
        self.prev_ema = None
        self.prev_atr = None
        self.indicator_state = {}
        
        self.current_state_idx = 0
        self.current_holdings = {"CASH": 1.0}
        self.smoothed_scores = np.zeros(4)

    def _softmax(self, x):
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()

    def _relu(self, x):
        return np.maximum(0, x)

    def on_data(self, date, price_data, prev_data):
        spy_mid = price_data['close']
        
        if not self.prices:
            return self.current_holdings, {}

        prev_close = self.prices[-1]
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

        # 2. Macro & Temporal
        macro_vix = float(price_data.get('vix', 15.0))
        macro_yc = float(price_data.get('yield_curve', 0.0))
        macro_cs = float(price_data.get('credit_spread', 2.0))
        
        m_sin = float(price_data.get('month_sin', 0.0))
        m_cos = float(price_data.get('month_cos', 1.0))
        tom_flag = float(price_data.get('is_tom', 0.0))
        intra_ret = (spy_mid - prev_close) / prev_close

        # 3. Assemble Input Vector (18 Features)
        inputs = np.array([
            ((spy_mid - val_sma) / val_sma * 5) if val_sma else 0.0,
            ((spy_mid - val_ema) / val_ema * 10) if val_ema else 0.0,
            ((val_rsi or 50) - 50) / 50.0,
            val_macd / spy_mid * 100,
            ((val_adx or 25) - 25) / 25.0,
            val_trix or 0.0,
            (val_slope or 0.0) / spy_mid * 1000,
            (val_vol or 0.15) * 5,
            ((val_atr or 0.0) / spy_mid) * 50,
            (macro_vix - 20) / 10.0,
            macro_yc,
            ((val_mfi or 50) - 50) / 50.0,
            val_bbw * 10,
            (macro_cs - 2.0) / 1.0,  # [NEW] Credit Spread
            m_sin,                   # [NEW] Month Sin
            m_cos,                   # [NEW] Month Cos
            tom_flag,                # [NEW] Turn-of-Month
            intra_ret * 20           # Intraday Return
        ])

        # 4. Neural Inference
        h1 = self._relu(np.dot(inputs, self.w1) + self.b1)
        raw_scores = np.dot(h1, self.w2) + self.b2
        probs = self._softmax(raw_scores)
        
        alpha = self.genome.get('smoothing', 0.5)
        self.smoothed_scores = alpha * probs + (1 - alpha) * self.smoothed_scores
        
        best_state_idx = np.argmax(self.smoothed_scores)
        current_conf = self.smoothed_scores[self.current_state_idx]
        best_conf = self.smoothed_scores[best_state_idx]
        hysteresis = self.genome.get('hysteresis', 0.15)

        if best_state_idx != self.current_state_idx:
            if best_conf > current_conf + hysteresis:
                self.current_state_idx = best_state_idx
                self.current_holdings = self.state_map[best_state_idx]

        telemetry = {
            "conf_cash": float(self.smoothed_scores[0]),
            "conf_3x": float(self.smoothed_scores[3]),
            "credit_spread": float(macro_cs),
            "tom_flag": float(tom_flag)
        }

        return self.current_holdings, telemetry

    def update_history(self, price_data):
        self.prices.append(price_data['close'])
        self.highs.append(price_data['high'])
        self.lows.append(price_data['low'])
        self.volumes.append(price_data.get('volume', 0))
