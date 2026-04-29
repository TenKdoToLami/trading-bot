"""
Adaptive Volatility & Momentum (V4.1 Chameleon Hunter)
V4.1 Nitro Matrix Optimized: Uses precalculated indicators for maximum evolution speed.
"""
from strategies.base import BaseStrategy
from src.helpers.indicators import rsi, sma, linear_regression_slope

class ChameleonV4(BaseStrategy):
    NAME = "[GENE] V4.1_CHAMELEON_HUNTER_NITRO"
    
    def __init__(self, genome=None, precalculated_features=None, index_offset=0):
        self.genome = genome or {
            "vix_ema": 50, "vol_stretch": 1.5, "mom_period": 200,
            "slope_period": 20, "slope_threshold": 0.0,
            "rsi_period": 2, "rsi_entry": 15, "rsi_exit": 85,
            "lev_bull": 3.0, "lev_calm": 2.0, "lev_stress": 1.0, "lev_panic": 0.0,
            "a": {"vix": True, "mom": True, "rsi": True, "slope": True}
        }
        self.precalculated_features = precalculated_features
        self.index_offset = index_offset
        self.reset()

    def reset(self):
        self.closes = []
        self.vix = []
        self.rsi_state = {"avg_gain": 0, "avg_loss": 0}
        self.idx = 0 # Track current simulation step

    def on_data(self, date: str, price_data: dict, prev_data=None) -> dict:
        curr_idx = self.idx + self.index_offset
        self.idx += 1
        
        ab = self.genome.get('a', {})
        curr_price = price_data['close']

        # 1. FAST EXIT (Nitro Matrix)
        slp_p = int(self.genome.get("slope_period", 20))
        # Snap to nearest even period if stepping by 2 in Nitro Matrix
        slp_p = (slp_p // 2) * 2
        
        if self.precalculated_features and f"slope_{slp_p}" in self.precalculated_features:
            val = self.precalculated_features[f"slope_{slp_p}"][curr_idx]
            norm_slope = (val / curr_price) * 1000 if val is not None else 0.0
        else:
            self.closes.append(curr_price)
            slp = linear_regression_slope(self.closes, slp_p)
            norm_slope = (slp / curr_price) * 1000 if slp is not None else 0.0

        if ab.get('slope', True) and norm_slope < self.genome.get("slope_threshold", 0.0):
            return {"CASH": 1.0}

        # 2. CORE REGIMES (Nitro Matrix)
        v_ema_p = int(self.genome["vix_ema"])
        if self.precalculated_features and f"vix_ema_{v_ema_p}" in self.precalculated_features:
            vix_ema = self.precalculated_features[f"vix_ema_{v_ema_p}"][curr_idx]
        else:
            self.vix.append(price_data['vix'])
            vix_ema = sum(self.vix[-v_ema_p:]) / v_ema_p # Fallback to SMA for speed if matrix missing
            
        vol_panic = (price_data['vix'] > (vix_ema * self.genome["vol_stretch"])) if ab.get('vix', True) else False
        
        mom_p = int(self.genome["mom_period"])
        if self.precalculated_features and f"sma_{mom_p}" in self.precalculated_features:
            mom_sma = self.precalculated_features[f"sma_{mom_p}"][curr_idx]
        else:
            mom_sma = sum(self.closes[-mom_p:]) / mom_p if len(self.closes) >= mom_p else curr_price
            
        trend_up = (curr_price > mom_sma) if ab.get('mom', True) else True

        # 3. RSI ADAPTIVE DIPS (Nitro Matrix)
        rsi_p = int(self.genome["rsi_period"])
        if self.precalculated_features and f"rsi_{rsi_p}" in self.precalculated_features:
            r_val = self.precalculated_features[f"rsi_{rsi_p}"][curr_idx]
        else:
            r_val = rsi(self.closes, rsi_p, state=self.rsi_state) or 50

        # 4. DECISION TREE
        if trend_up:
            if ab.get('rsi', True) and r_val < self.genome["rsi_entry"]:
                lev = self.genome["lev_bull"]
            elif ab.get('rsi', True) and r_val > self.genome.get("rsi_exit", 90):
                lev = 1.0
            else:
                lev = self.genome["lev_calm"]
        else:
            if vol_panic:
                lev = self.genome["lev_panic"]
            else:
                lev = self.genome["lev_stress"]

        # Map to assets
        if lev >= 3.0: return {"3xSPY": 1.0}
        if lev >= 2.0: return {"2xSPY": 1.0}
        if lev >= 1.0: return {"SPY": 1.0}
        return {"CASH": 1.0}
