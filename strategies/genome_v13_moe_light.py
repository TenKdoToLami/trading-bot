"""
Genome V13 MOE Light — "Sparse Expert" Strategy.
Optimized for robustness and reduced overfitting:
1. Sentinel (Regime): Sees all features, uses fluid blending (No hard thresholds).
2. Bull Expert: Focuses on Momentum/Trend features.
3. Bear Expert: Focuses on Macro/Seasonality/Volatility features.
"""

import numpy as np
from strategies.base import BaseStrategy
from src.tournament.registry import register_strategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility, mfi, bollinger_bands
)

@register_strategy(["v13_moe_light", 13.6])
class GenomeV13MOELight(BaseStrategy):
    NAME = "Genome V13 (MOE Light)"
    version = 13.6

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.reset()
        
        # Hidden dimension is smaller in Light version
        self.w_sent = np.array(self.genome['sentinel']['w'])
        self.b_sent = np.array(self.genome['sentinel']['b'])
        self.out_w_sent = np.array(self.genome['sentinel']['out_w'])
        self.out_b_sent = np.array(self.genome['sentinel']['out_b'])
        
        self.w_bull = np.array(self.genome['bull_expert']['w'])
        self.b_bull = np.array(self.genome['bull_expert']['b'])
        self.out_w_bull = np.array(self.genome['bull_expert']['out_w'])
        self.out_b_bull = np.array(self.genome['bull_expert']['out_b'])

        self.w_bear = np.array(self.genome['bear_expert']['w'])
        self.b_bear = np.array(self.genome['bear_expert']['b'])
        self.out_w_bear = np.array(self.genome['bear_expert']['out_w'])
        self.out_b_bear = np.array(self.genome['bear_expert']['out_b'])

    def _default_genome(self):
        def rand_brain(in_dim, hid_dim, out_dim):
            return {
                'w': np.random.uniform(-0.5, 0.5, (in_dim, hid_dim)).tolist(),
                'b': np.zeros(hid_dim).tolist(),
                'out_w': np.random.uniform(-1, 1, (hid_dim, out_dim)).tolist(),
                'out_b': np.zeros(out_dim).tolist()
            }
        # Bull/Bear experts now have only 10 inputs instead of 18
        return {
            'version': 13.6,
            'sentinel': rand_brain(18, 6, 2),
            'bull_expert': rand_brain(10, 6, 3), 
            'bear_expert': rand_brain(10, 6, 5), 
            'lookbacks': {
                'sma': 200, 'ema': 50, 'rsi': 14, 'macd_f': 12, 'macd_s': 26,
                'adx': 14, 'trix': 15, 'slope': 20, 'vol': 20, 'atr': 14,
                'mfi': 14, 'bb': 20
            },
            'hysteresis': 0.1,
            'smoothing': 0.3
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
        self.smoothed_regime = np.array([0.5, 0.5]) 

    def _softmax(self, x):
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()

    def _relu(self, x):
        return np.maximum(0, x)

    def _forward(self, inputs, w_hid, b_hid, w_out, b_out):
        h = self._relu(np.dot(inputs, w_hid) + b_hid)
        return self._softmax(np.dot(h, w_out) + b_out)

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        prev_close = self.prices[-1] if self.prices else spy_price
        self.prices.append(spy_price)
        self.highs.append(price_data['high'])
        self.lows.append(price_data['low'])
        self.volumes.append(price_data.get('volume', 0))

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

        # 2. Macro Features
        macro_vix = float(price_data.get('vix', 15.0))
        macro_yc = float(price_data.get('yield_curve', 0.0))
        macro_cs = float(price_data.get('credit_spread', 2.0))
        m_sin = float(price_data.get('month_sin', 0.0))
        m_cos = float(price_data.get('month_cos', 1.0))
        tom_flag = float(price_data.get('is_tom', 0.0))
        intra_ret = (spy_price - prev_close) / prev_close if prev_close else 0

        # 3. Assemble Full Input Vector (18 Features)
        all_features = np.array([
            ((spy_price - val_sma) / val_sma * 5) if val_sma else 0.0, # 0
            ((spy_price - val_ema) / val_ema * 10) if val_ema else 0.0, # 1
            ((val_rsi or 50) - 50) / 50.0, # 2
            val_macd / spy_price * 100, # 3
            ((val_adx or 25) - 25) / 25.0, # 4
            val_trix or 0.0, # 5
            (val_slope or 0.0) / spy_price * 1000, # 6
            (val_vol or 0.15) * 5, # 7
            ((val_atr or 0.0) / spy_price) * 50, # 8
            (macro_vix - 20) / 10.0, # 9
            macro_yc, # 10
            ((val_mfi or 50) - 50) / 50.0, # 11
            val_bbw * 10, # 12
            (macro_cs - 2.0) / 1.0, # 13
            m_sin, m_cos, tom_flag, # 14, 15, 16
            intra_ret * 20 # 17
        ])

        # 4. Neural Inference
        # Sentinel sees everything
        sent_probs = self._forward(all_features, self.w_sent, self.b_sent, self.out_w_sent, self.out_b_sent)
        
        alpha = self.genome.get('smoothing', 0.3)
        self.smoothed_regime = alpha * sent_probs + (1 - alpha) * self.smoothed_regime
        p_bear, p_bull = self.smoothed_regime
        
        # 5. Sparse Expert Consultations
        # Bull Expert: Features 0, 1, 2, 3, 4, 5, 6, 11, 12, 17 (Technicals/Momentum/Vol/Intra)
        bull_idx = [0, 1, 2, 3, 4, 5, 6, 11, 12, 17]
        bull_inputs = all_features[bull_idx]
        bull_weights = self._forward(bull_inputs, self.w_bull, self.b_bull, self.out_w_bull, self.out_b_bull)
        
        # Bear Expert: Features 7, 8, 9, 10, 13, 14, 15, 16, 17, 0 (Macro/Vol/Seasonality/Intra/Trend)
        bear_idx = [7, 8, 9, 10, 13, 14, 15, 16, 17, 0]
        bear_inputs = all_features[bear_idx]
        bear_weights = self._forward(bear_inputs, self.w_bear, self.b_bear, self.out_w_bear, self.out_b_bear)
        
        # 6. Final Allocation (PURE FLUID - NO CLIFFS)
        holdings = {}
        # Bull components
        holdings["SPY"] = float(p_bull * bull_weights[0])
        holdings["2xSPY"] = float(p_bull * bull_weights[1])
        holdings["3xSPY"] = float(p_bull * bull_weights[2])
        
        # Bear components
        holdings["TLT"] = float(p_bear * bear_weights[0])
        holdings["SHY"] = float(p_bear * bear_weights[1])
        holdings["GOLD"] = float(p_bear * bear_weights[2])
        holdings["SHORT_SPY"] = float(p_bear * bear_weights[3])
        holdings["2xSHORT_SPY"] = float(p_bear * bear_weights[4])
        
        new_holdings = {k: v for k, v in holdings.items() if v > 0.01}
        
        # 7. Hysteresis (Stickiness) Logic
        # Only update if the total change in weights exceeds the hysteresis threshold
        h_threshold = self.genome.get('hysteresis', 0.1)
        all_assets = set(list(self.current_holdings.keys()) + list(new_holdings.keys()))
        turnover = sum(abs(new_holdings.get(a, 0.0) - self.current_holdings.get(a, 0.0)) for a in all_assets)
        
        if turnover > h_threshold:
            self.current_holdings = new_holdings

        telemetry = {
            "p_bull": float(p_bull),
            "regime": float(p_bull),
            "turnover": float(turnover),
            "bull_split": bull_weights.tolist(),
            "bear_split": bear_weights.tolist()
        }
        
        return self.current_holdings, telemetry
