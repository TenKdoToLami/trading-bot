"""
Genome V13 Lite — "Dual-Brain" Neural Strategy.
Architecture: 
1. Sentinel Brain (18 -> 10 -> 2): Determines Bull vs Bear regime.
2. Pilot Brain (18 -> 10 -> 3): Determines 1x, 2x, 3x SPY allocation.
"""

import numpy as np
from strategies.base import BaseStrategy
from src.tournament.registry import register_strategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility, mfi, bollinger_bands
)

@register_strategy(["v13_lite", 13.0])
class GenomeV13Lite(BaseStrategy):
    NAME = "Genome V13 (Dual-Brain Lite)"
    version = 13.0

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.reset()
        
        # Sentinel Brain (Regime)
        self.w_sent = np.array(self.genome['sentinel']['w'])
        self.b_sent = np.array(self.genome['sentinel']['b'])
        self.out_w_sent = np.array(self.genome['sentinel']['out_w'])
        self.out_b_sent = np.array(self.genome['sentinel']['out_b'])
        
        # Pilot Brain (Allocation)
        self.w_pilot = np.array(self.genome['pilot']['w'])
        self.b_pilot = np.array(self.genome['pilot']['b'])
        self.out_w_pilot = np.array(self.genome['pilot']['out_w'])
        self.out_b_pilot = np.array(self.genome['pilot']['out_b'])

    def _default_genome(self):
        def rand_brain(in_dim, hid_dim, out_dim):
            return {
                'w': np.random.uniform(-0.5, 0.5, (in_dim, hid_dim)).tolist(),
                'b': np.zeros(hid_dim).tolist(),
                'out_w': np.random.uniform(-1, 1, (hid_dim, out_dim)).tolist(),
                'out_b': np.zeros(out_dim).tolist()
            }

        return {
            'version': 13.0,
            'sentinel': rand_brain(18, 10, 2),
            'pilot': rand_brain(18, 10, 3),
            'lookbacks': {
                'sma': 200, 'ema': 50, 'rsi': 14, 'macd_f': 12, 'macd_s': 26,
                'adx': 14, 'trix': 15, 'slope': 20, 'vol': 20, 'atr': 14,
                'mfi': 14, 'bb': 20
            },
            'hysteresis': 0.15,
            'smoothing': 0.4
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
        self.smoothed_regime = 0.5

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

        # 2. V12 Macro Features
        macro_vix = float(price_data.get('vix', 15.0))
        macro_yc = float(price_data.get('yield_curve', 0.0))
        macro_cs = float(price_data.get('credit_spread', 2.0))
        m_sin = float(price_data.get('month_sin', 0.0))
        m_cos = float(price_data.get('month_cos', 1.0))
        tom_flag = float(price_data.get('is_tom', 0.0))
        intra_ret = (spy_price - prev_close) / prev_close if prev_close else 0

        # 3. Assemble Input Vector (18 Features)
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
            val_bbw * 10,
            (macro_cs - 2.0) / 1.0,
            m_sin, m_cos, tom_flag,
            intra_ret * 20
        ])

        # 4. Neural Inference
        sent_probs = self._forward(inputs, self.w_sent, self.b_sent, self.out_w_sent, self.out_b_sent)
        
        # Smoothing for regime
        alpha = self.genome.get('smoothing', 0.4)
        self.smoothed_regime = alpha * sent_probs[1] + (1 - alpha) * self.smoothed_regime
        
        # 5. Decision Engine
        hysteresis = self.genome.get('hysteresis', 0.15)
        
        if self.smoothed_regime < (0.5 - hysteresis):
            new_holdings = {"CASH": 1.0}
        elif self.smoothed_regime > (0.5 + hysteresis):
            # Bullish: Consult the Pilot
            pilot_probs = self._forward(inputs, self.w_pilot, self.b_pilot, self.out_w_pilot, self.out_b_pilot)
            winner = np.argmax(pilot_probs)
            if winner == 0: new_holdings = {"SPY": 1.0}
            elif winner == 1: new_holdings = {"2xSPY": 1.0}
            else: new_holdings = {"3xSPY": 1.0}
        else:
            new_holdings = self.current_holdings # Stay

        self.current_holdings = new_holdings
        telemetry = {
            "p_bull": float(self.smoothed_regime),
            "regime": float(self.smoothed_regime)
        }
        
        return self.current_holdings, telemetry
