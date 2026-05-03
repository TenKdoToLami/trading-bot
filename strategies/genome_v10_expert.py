"""
Genome V10 Expert Strategy — Triple Brain Architecture.
Uses pre-calculated indicator profiles to feed three specialized neural networks:
1. Bullish Expert (Precision-focused Long signals)
2. Bearish Expert (Precision-focused Short/Cash signals)
3. MixMaster (The Allocator / Portfolio Manager)

The Bearish Expert has 'Priority Override' — if it detects a crash, it vetoes the Bullish Expert.
"""

import os
import json
import numpy as np
from strategies.base import BaseStrategy
from src.tournament.registry import register_strategy
from src.tournament.market_state import MarketState

@register_strategy(["v10_expert", 10.0])
class GenomeV10Expert(BaseStrategy):
    NAME = "Genome V10 (Expert Ensemble)"
    version = 10

    def __init__(self, genome=None, profile_path="champions/v10_alpha/indicator_profiles.json"):
        self.profile_path = profile_path
        self.genome = genome or self._default_genome()
        
        # Load Brain Weights & Profiles
        # PRIORITY: 1. Profiles embedded in genome | 2. Profile path
        self.profile_data = self.genome.get('indicator_profiles', self._load_profile(profile_path))
        self.expert_keys = sorted(list(self.profile_data.keys()))
        input_size = len(self.expert_keys)
        
        self.reset()
        self.wa = np.array(self.genome['brain_a']['w'])
        self.ba = np.array(self.genome['brain_a']['b'])
        self.wb = np.array(self.genome['brain_b']['w'])
        self.bb = np.array(self.genome['brain_b']['b'])
        self.wc = np.array(self.genome['brain_c']['w'])
        self.bc = np.array(self.genome['brain_c']['b'])

    def _load_profile(self, path):
        if path and os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                return data.get('profiles', data) # Handle both raw profiles and full meta
        return {}

    def _default_genome(self):
        # We assume 8-10 experts for initialization
        input_size = len(self.expert_keys) if hasattr(self, 'expert_keys') else 10
        return {
            'brain_a': {
                'w': np.random.uniform(-1, 1, (input_size, 1)).tolist(),
                'b': [0.0]
            },
            'brain_b': {
                'w': np.random.uniform(-1, 1, (input_size, 1)).tolist(),
                'b': [0.0]
            },
            'brain_c': {
                'w': np.random.uniform(-1, 1, (3, 4)).tolist(), # (Bull, Bear, Vol) -> (0x, 1x, 2x, 3x)
                'b': [0, 0, 0, 0]
            },
            'overrides': {
                'bear_veto_threshold': 0.8
            }
        }

    def reset(self):
        self.market = MarketState()
        self.current_holdings = {"CASH": 1.0}
        
    def _relu(self, x): return np.maximum(0, x)
    def _sigmoid(self, x): 
        # Clip to prevent overflow
        return 1 / (1 + np.exp(-np.clip(x, -20, 20)))
    def _softmax(self, x):
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()

    def _get_indicator_val(self, key, lb):
        """Helper to fetch indicator values matching the Profiler logic."""
        m = self.market
        lb = int(round(lb))
        p = m.last_price
        
        if key == "SMA_DIST":
            val = m.get_indicator('sma', lb)
            return (p - val) / val if val else 0
        elif key == "EMA_DIST":
            val = m.get_indicator('ema', lb)
            return (p - val) / val if val else 0
        elif key == "RSI":
            val = m.get_indicator('rsi', lb)
            return val if val is not None else 50
        elif key == "MFI":
            val = m.get_indicator('mfi', lb)
            return val if val is not None else 50
        elif key == "TRIX":
            val = m.get_indicator('trix', lb)
            return val if val is not None else 0
        elif key == "ADX":
            val = m.get_indicator('adx', lb)
            return val if val is not None else 20
        elif key == "SLOPE":
            val = m.get_indicator('slope', lb)
            return val if val is not None else 0
        elif key == "VOL":
            val = m.get_indicator('vol', lb)
            return val if val is not None else 0.15
        elif key == "ATR":
            val = m.get_indicator('atr', lb)
            return val if val is not None else 1.0
        elif key == "VIX":
            return m.get_macro('vix', 20.0)
        return 0
    def on_data(self, date, price_data, prev_data):
        self.market.update(date, price_data)
        
        if len(self.market.prices) < 10: return self.current_holdings, {}

        # 1. Expert Layer (Weighted Pre-calculation)
        expert_bull = []
        expert_bear = []
        
        for key in self.expert_keys:
            p = self.profile_data[key]
            
            # Bull Expert Input
            if p['bullish']:
                val = self._get_indicator_val(key, p['bullish']['lookback'])
                # If the profiler said "Greater Than" is bull, check that
                # (Profiler logic: bull is always 'greater than' unless it's RSI/MFI/Oversold)
                # We'll use a simple threshold check based on the profiler's found threshold
                is_bull = False
                if key in ["RSI", "MFI"]: # Oversold logic
                    is_bull = (val < p['bullish']['thresh'])
                else:
                    is_bull = (val > p['bullish']['thresh'])
                expert_bull.append(1.0 if is_bull else 0.0)
            else:
                expert_bull.append(0.0)
                
            # Bear Expert Input
            if p['bearish']:
                val = self._get_indicator_val(key, p['bearish']['lookback'])
                is_bear = False
                if key in ["TRIX", "SLOPE", "VOL"]: # Greater than logic for bear/panic
                    is_bear = (val > p['bearish']['thresh'])
                elif key == "VOL":
                    is_bear = (val > p['bearish']['thresh'])
                else: # Default: Less than is bearish (Price below MA, etc)
                    is_bear = (val < p['bearish']['thresh'])
                expert_bear.append(1.0 if is_bear else 0.0)
            else:
                expert_bear.append(0.0)
        
        # 2. Expert Brain Inference
        conf_bull = self._sigmoid(np.dot(expert_bull, self.wa) + self.ba)[0]
        conf_bear = self._sigmoid(np.dot(expert_bear, self.wb) + self.bb)[0]
        
        # 3. Priority Override (Veto Logic)
        veto_thresh = self.genome['overrides']['bear_veto_threshold']
        effective_bull = conf_bull if conf_bear < veto_thresh else 0.0
        
        # 4. MixMaster Allocation
        vix = float(price_data.get('vix', 20.0))
        vol_norm = (vix - 15) / 20.0
        mix_inputs = np.array([effective_bull, conf_bear, vol_norm])
        
        raw_alloc = np.dot(mix_inputs, self.wc) + self.bc
        probs = self._softmax(raw_alloc)
        
        # 5. Result
        best_state_idx = np.argmax(probs)
        state_map = {0: {"CASH": 1.0}, 1: {"SPY": 1.0}, 2: {"2xSPY": 1.0}, 3: {"3xSPY": 1.0}}
        self.current_holdings = state_map[best_state_idx]
        
        telemetry = {
            "conf_bull": float(conf_bull),
            "conf_bear": float(conf_bear),
            "veto": bool(conf_bear >= veto_thresh),
            "probs": probs.tolist()
        }
        
        return self.current_holdings, telemetry
