"""
Genome V12 SMT — Seasonal Macro Tactical.
Hierarchical Mixture of Experts (MoE) Architecture:
1. Primary Regime Brain (Bull vs Bear)
2. Bullish Sub-Brain (1x, 2x, 3x SPY)
3. Bearish Sub-Brain (TLT, SHY, GOLD, 2x Short SPY)
"""

import numpy as np
import pandas as pd
from strategies.base import BaseStrategy
from src.tournament.registry import register_strategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility, mfi, bollinger_bands
)

@register_strategy(["v12_moe", 12.0])
class GenomeV12MOE(BaseStrategy):
    NAME = "Genome V12 (Fluid MOE)"
    version = 12.0
    IS_INTRA = True

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.reset()
        
        # 1. Regime Brain Weights
        self.w_reg = np.array(self.genome['regime']['w'])
        self.b_reg = np.array(self.genome['regime']['b'])
        
        # 2. Bull Brain Weights
        self.w_bull = np.array(self.genome['bull']['w'])
        self.b_bull = np.array(self.genome['bull']['b'])
        
        # 3. Bear Brain Weights
        self.w_bear = np.array(self.genome['bear']['w'])
        self.b_bear = np.array(self.genome['bear']['b'])

    def _default_genome(self):
        # All brains use 18 inputs for simplicity, but different hidden/output sizes
        return {
            'version': 12.0,
            'regime': {
                'w': np.random.uniform(-0.5, 0.5, (18, 16)).tolist(),
                'b': np.zeros(16).tolist(),
                'out_w': np.random.uniform(-1, 1, (16, 2)).tolist(),
                'out_b': np.zeros(2).tolist()
            },
            'bull': {
                'w': np.random.uniform(-0.5, 0.5, (18, 16)).tolist(),
                'b': np.zeros(16).tolist(),
                'out_w': np.random.uniform(-1, 1, (16, 3)).tolist(),
                'out_b': np.zeros(3).tolist()
            },
            'bear': {
                'w': np.random.uniform(-0.5, 0.5, (18, 16)).tolist(),
                'b': np.zeros(16).tolist(),
                'out_w': np.random.uniform(-1, 1, (16, 4)).tolist(),
                'out_b': np.zeros(4).tolist()
            },
            'lookbacks': {
                'sma': 200, 'ema': 50, 'rsi': 14, 'macd_f': 12, 'macd_s': 26,
                'adx': 14, 'trix': 15, 'slope': 20, 'vol': 20, 'atr': 14,
                'mfi': 14, 'bb': 20
            },
            'smoothing': 0.3, # Faster for Regime, Slower for Allocation
            'regime_hysteresis': 0.1
        }

    def reset(self):
        self.prices = []
        self.highs = []
        self.lows = []
        self.volumes = []
        
        self.prev_ema = None
        self.prev_atr = None
        self.indicator_state = {}
        
        # State tracking
        self.current_weights = {"CASH": 1.0}
        self.smoothed_regime = 0.5 # 0=Bear, 1=Bull
        self.smoothed_bull_alloc = np.zeros(3)
        self.smoothed_bear_alloc = np.zeros(4)

    def _softmax(self, x):
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()

    def _relu(self, x):
        return np.maximum(0, x)

    def _forward(self, inputs, w_hidden, b_hidden, w_out, b_out):
        h = self._relu(np.dot(inputs, w_hidden) + b_hidden)
        scores = np.dot(h, w_out) + b_out
        return self._softmax(scores)

    def on_data(self, date, price_data, prev_data):
        spy_mid = price_data['close']
        if not self.prices: return self.current_weights, {}

        prev_close = self.prices[-1]
        lb = self.genome['lookbacks']
        
        # 1. Indicators (Standard 13)
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
            (macro_cs - 2.0) / 1.0,
            m_sin, m_cos, tom_flag,
            intra_ret * 20
        ])

        # 4. Neural Inference (Hierarchical)
        # Brain 1: Regime
        reg_probs = self._forward(inputs, self.w_reg, self.b_reg, 
                                 np.array(self.genome['regime']['out_w']), 
                                 np.array(self.genome['regime']['out_b']))
        
        # Brain 2: Bull Allocation
        bull_probs = self._forward(inputs, self.w_bull, self.b_bull,
                                  np.array(self.genome['bull']['out_w']),
                                  np.array(self.genome['bull']['out_b']))
        
        # Brain 3: Bear Allocation
        bear_probs = self._forward(inputs, self.w_bear, self.b_bear,
                                  np.array(self.genome['bear']['out_w']),
                                  np.array(self.genome['bear']['out_b']))

        # 5. Smoothing & Blending
        alpha = self.genome.get('smoothing', 0.3)
        self.smoothed_regime = alpha * reg_probs[1] + (1 - alpha) * self.smoothed_regime
        self.smoothed_bull_alloc = alpha * bull_probs + (1 - alpha) * self.smoothed_bull_alloc
        self.smoothed_bear_alloc = alpha * bear_probs + (1 - alpha) * self.smoothed_bear_alloc

        # 6. Final Weight Assembly
        # Pool A (Bull): 1xSPY, 2xSPY, 3xSPY
        # Pool B (Bear): TLT, SHY, GOLD, 2x SHORT SPY
        
        weights = {}
        bull_factor = self.smoothed_regime
        bear_factor = 1.0 - bull_factor
        
        # Bullish components
        weights["SPY"] = round(float(self.smoothed_bull_alloc[0] * bull_factor), 2)
        weights["2xSPY"] = round(float(self.smoothed_bull_alloc[1] * bull_factor), 2)
        weights["3xSPY"] = round(float(self.smoothed_bull_alloc[2] * bull_factor), 2)
        
        # Bearish components
        weights["TLT"] = round(float(self.smoothed_bear_alloc[0] * bear_factor), 2)
        weights["SHY"] = round(float(self.smoothed_bear_alloc[1] * bear_factor), 2)
        weights["GOLD"] = round(float(self.smoothed_bear_alloc[2] * bear_factor), 2)
        weights["2xSHORT_SPY"] = round(float(self.smoothed_bear_alloc[3] * bear_factor), 2)
        
        self.current_weights = weights
        
        telemetry = {
            "regime": float(bull_factor),
            "bull_split": [round(x, 2) for x in self.smoothed_bull_alloc],
            "bear_split": [round(x, 2) for x in self.smoothed_bear_alloc],
            "top_asset": max(weights, key=weights.get)
        }

        return weights, telemetry

    def update_history(self, price_data):
        self.prices.append(price_data['close'])
        self.highs.append(price_data['high'])
        self.lows.append(price_data['low'])
        self.volumes.append(price_data.get('volume', 0))
