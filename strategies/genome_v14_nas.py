"""
Genome V14 NAS "Elastic Brain"
Version 14.0 - Neural Architecture Search 
Based on V13.10 Conviction Aggressive.
1. Sentinel (The Decider): Elastic Hidden Dimension (2-32).
2. Bear Commander (Defense): Elastic Hidden Dimension (2-16).
3. Active Slicing: Uses only a subset of the master weight matrix.
4. Conviction: Power Skew + Kill Switch.
"""

import numpy as np
from strategies.base import BaseStrategy
from src.tournament.registry import register_strategy
from src.helpers.indicators import (
    sma, ema, rsi, macd, realized_volatility, atr, mfi, bollinger_bands
)

@register_strategy(["v14_nas", 14.0])
class GenomeV14NAS(BaseStrategy):
    NAME = "Genome V14.0 (NAS - Elastic Brain)"
    version = 14.0

    def __init__(self, genome=None):
        self.genome = genome or self._default_genome()
        self.reset()
        
        # Load Master Weights
        self.sent_dim = int(self.genome.get('sentinel_dim', 10))
        self.comm_dim = int(self.genome.get('commander_dim', 6))
        
        # 1. Sentinel (Decider) - Slicing Master Weights
        self.w_sent_full = np.array(self.genome['sentinel']['w'])
        self.b_sent_full = np.array(self.genome['sentinel']['b'])
        self.out_w_sent_full = np.array(self.genome['sentinel']['out_w'])
        self.out_b_sent = np.array(self.genome['sentinel']['out_b'])
        
        # 2. Bear Commander (Defense) - Slicing Master Weights
        self.w_comm_full = np.array(self.genome['bear_commander']['w'])
        self.b_comm_full = np.array(self.genome['bear_commander']['b'])
        self.out_w_comm_full = np.array(self.genome['bear_commander']['out_w'])
        self.out_b_comm = np.array(self.genome['bear_commander']['out_b'])

    def _default_genome(self):
        def master_brain(in_dim, max_hid, out_dim):
            return {
                'w': np.random.uniform(-0.5, 0.5, (in_dim, max_hid)).tolist(),
                'b': np.zeros(max_hid).tolist(),
                'out_w': np.random.uniform(-1, 1, (max_hid, out_dim)).tolist(),
                'out_b': np.zeros(out_dim).tolist()
            }
        return {
            'version': 14.0,
            'sentinel_dim': 10,
            'commander_dim': 6,
            'sentinel': master_brain(28, 32, 2), # Max 32 neurons
            'bear_commander': master_brain(10, 16, 3), # Max 16 neurons
            'lookbacks': {
                'sma': 200, 'ema': 50, 'rsi': 14, 'macd_f': 12, 'macd_s': 26,
                'vol': 20, 'atr': 14, 'mfi': 14, 'bb': 20
            },
            'hysteresis': 0.1,
            'smoothing': 0.3,
            'temp': 1.0,
            'skew_power': 2.0,
            'conviction_cap': 0.90
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
        self.regime_history = [np.array([0.5, 0.5]) for _ in range(5)]

    def _softmax(self, x, temp=1.0):
        x = x / max(temp, 0.01)
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()

    def _forward_nas(self, inputs, w_hid, b_hid, w_out, b_out):
        temp = self.genome.get('temp', 1.0)
        h = np.maximum(0, np.dot(inputs, w_hid) + b_hid) # ReLU
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

        # 4. NAS SLICING INFERENCE
        memory_vector = np.concatenate(self.regime_history)
        sentinel_inputs = np.concatenate([all_features, memory_vector])
        
        # Slicing Sentinel
        s_dim = self.sent_dim
        w_sent = self.w_sent_full[:, :s_dim]
        b_sent = self.b_sent_full[:s_dim]
        out_w_sent = self.out_w_sent_full[:s_dim, :]
        sent_probs = self._forward_nas(sentinel_inputs, w_sent, b_sent, out_w_sent, self.out_b_sent)
        
        # Power Skew
        skew = self.genome.get('skew_power', 1.0)
        if skew != 1.0:
            sent_probs = np.power(sent_probs, skew)
            sent_probs /= np.sum(sent_probs)

        # Update history
        self.regime_history.pop(0)
        self.regime_history.append(sent_probs)

        # Smoothing
        alpha = self.genome.get('smoothing', 0.3)
        self.smoothed_regime = alpha * sent_probs + (1 - alpha) * self.smoothed_regime
        
        # Kill Switch
        cap = self.genome.get('conviction_cap', 1.0)
        final_probs = self.smoothed_regime.copy()
        if np.max(final_probs) > cap:
            max_idx = np.argmax(final_probs)
            final_probs = np.zeros_like(final_probs)
            final_probs[max_idx] = 1.0
            
        p_bull, p_bear = final_probs
        
        # Slicing Bear Commander
        c_dim = self.comm_dim
        w_comm = self.w_comm_full[:, :c_dim]
        b_comm = self.b_comm_full[:c_dim]
        out_w_comm = self.out_w_comm_full[:c_dim, :]
        bear_weights = self._forward_nas(all_features[5:15], w_comm, b_comm, out_w_comm, self.out_b_comm)
        
        # 5. Final Allocation
        holdings = {}
        holdings["3xSPY"] = float(p_bull)
        holdings["CASH"] = float(p_bear * bear_weights[0])
        holdings["GOLD"] = float(p_bear * bear_weights[1])
        holdings["TLT"] = float(p_bear * bear_weights[2])
        
        new_holdings = {k: v for k, v in holdings.items() if v > 0.01}
        
        # Hysteresis
        h_threshold = self.genome.get('hysteresis', 0.1)
        all_assets = set(list(self.current_holdings.keys()) + list(new_holdings.keys()))
        turnover = sum(abs(new_holdings.get(a, 0.0) - self.current_holdings.get(a, 0.0)) for a in all_assets)
        
        if turnover > h_threshold:
            self.current_holdings = new_holdings

        telemetry = {
            "p_bull": float(p_bull),
            "p_bear": float(p_bear),
            "s_neurons": int(s_dim),
            "c_neurons": int(c_dim)
        }
        
        return self.current_holdings, telemetry
