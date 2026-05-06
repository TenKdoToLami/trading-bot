"""
Genome V13 MOE Full — "The Grand Commander" Strategy.
Hierarchical Mixture of Experts (HMOE) Architecture:
1. Sentinel (The Decider): (Bear, Bull, Cash) - Fluidly blends 3 primary regimes.
2. Bull Expert: (1x, 2x, 3x) - Focuses on SPY leverage.
3. Bear Commander: (Banker, Alchemist, Assassin) - Allocates across defensive clusters.
4. Assassin Expert: (-1x, -2x, -3x) - Focuses on high-beta inverse playbooks.
"""

import numpy as np
from strategies.base import BaseStrategy
from src.tournament.registry import register_strategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility, mfi, bollinger_bands
)

@register_strategy(["v13_moe_full", 13.9])
class GenomeV13MOEFull(BaseStrategy):
    NAME = "Genome V13 (MOE Full - Long Aggressive)"
    version = 13.9

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.reset()
        
        # 1. Sentinel (Decider)
        self.w_sent = np.array(self.genome['sentinel']['w'])
        self.b_sent = np.array(self.genome['sentinel']['b'])
        self.out_w_sent = np.array(self.genome['sentinel']['out_w'])
        self.out_b_sent = np.array(self.genome['sentinel']['out_b'])
        
        # 2. Bear Commander (Defense)
        self.w_commander = np.array(self.genome['bear_commander']['w'])
        self.b_commander = np.array(self.genome['bear_commander']['b'])
        self.out_w_commander = np.array(self.genome['bear_commander']['out_w'])
        self.out_b_commander = np.array(self.genome['bear_commander']['out_b'])

    def _default_genome(self):
        def rand_brain(in_dim, hid_dim, out_dim):
            return {
                'w': np.random.uniform(-0.5, 0.5, (in_dim, hid_dim)).tolist(),
                'b': np.zeros(hid_dim).tolist(),
                'out_w': np.random.uniform(-1, 1, (hid_dim, out_dim)).tolist(),
                'out_b': np.zeros(out_dim).tolist()
            }
        return {
            'version': 13.9,
            'sentinel': rand_brain(28, 10, 2), # 18 Features + 10 Memory
            'bear_commander': rand_brain(10, 6, 3), # CASH, GOLD, TLT
            'lookbacks': {
                'sma': 200, 'ema': 50, 'rsi': 14, 'macd_f': 12, 'macd_s': 26,
                'adx': 14, 'trix': 15, 'slope': 20, 'vol': 20, 'atr': 14,
                'mfi': 14, 'bb': 20
            },
            'hysteresis': 0.1,
            'smoothing': 0.3,
            'temp': 1.0
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
        self.smoothed_regime = np.array([0.5, 0.5]) # Bull, Bear
        self.regime_history = [np.array([0.5, 0.5]) for _ in range(5)] # 5-day memory

    def _softmax(self, x, temp=1.0):
        x = x / max(temp, 0.01)
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()

    def _relu(self, x):
        return np.maximum(0, x)

    def _forward(self, inputs, w_hid, b_hid, w_out, b_out):
        temp = self.genome.get('temp', 1.0)
        h = self._relu(np.dot(inputs, w_hid) + b_hid)
        return self._softmax(np.dot(h, w_out) + b_out, temp=temp)

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

        # 3. Assemble Full Input Vector
        all_features = np.array([
            ((spy_price - val_sma) / val_sma * 5) if val_sma else 0.0,
            ((spy_price - val_ema) / val_ema * 10) if val_ema else 0.0,
            ((val_rsi or 50) - 50) / 50.0,
            val_macd / spy_price * 100,
            (val_vol or 0.15) * 5,
            ((val_atr or 0.0) / spy_price) * 50,
            (macro_vix - 20) / 10.0,
            macro_yc,
            ((val_mfi or 50) - 50) / 50.0,
            val_bbw * 10,
            (macro_cs - 2.0) / 1.0,
            m_sin, m_cos, tom_flag,
            intra_ret * 20,
            0.0, 0.0, 0.0 # Padding
        ])

        # 4. Neural Inference with Regime Memory
        memory_vector = np.concatenate(self.regime_history)
        sentinel_inputs = np.concatenate([all_features, memory_vector])
        
        sent_probs = self._forward(sentinel_inputs, self.w_sent, self.b_sent, self.out_w_sent, self.out_b_sent)
        
        # Update history
        self.regime_history.pop(0)
        self.regime_history.append(sent_probs)

        alpha = self.genome.get('smoothing', 0.3)
        self.smoothed_regime = alpha * sent_probs + (1 - alpha) * self.smoothed_regime
        p_bull, p_bear = self.smoothed_regime
        
        # 5. Expert Consultations
        # Bear Commander (CASH, GOLD, TLT)
        bear_weights = self._forward(all_features[5:15], self.w_commander, self.b_commander, self.out_w_commander, self.out_b_commander)
        
        # 6. Final Allocation
        holdings = {}
        # Bull side (100% 3xSPY)
        holdings["3xSPY"] = float(p_bull)
        
        # Bear side
        holdings["CASH"] = float(p_bear * bear_weights[0])
        holdings["GOLD"] = float(p_bear * bear_weights[1])
        holdings["TLT"] = float(p_bear * bear_weights[2])
        
        new_holdings = {k: v for k, v in holdings.items() if v > 0.01}
        
        # 7. Hysteresis
        h_threshold = self.genome.get('hysteresis', 0.1)
        all_assets = set(list(self.current_holdings.keys()) + list(new_holdings.keys()))
        turnover = sum(abs(new_holdings.get(a, 0.0) - self.current_holdings.get(a, 0.0)) for a in all_assets)
        
        if turnover > h_threshold:
            self.current_holdings = new_holdings

        telemetry = {
            "p_bull": float(p_bull),
            "p_bear": float(p_bear),
            "turnover": float(turnover),
            "bear_split": bear_weights.tolist(),
            "temp": float(self.genome.get('temp', 1.0))
        }
        
        return self.current_holdings, telemetry
