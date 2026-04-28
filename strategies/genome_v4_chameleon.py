"""
Adaptive Volatility & Momentum (V4 Chameleon)
Highly tunable genome for genetic evolution.
"""
from strategies.base import BaseStrategy
from src.helpers.indicators import rsi, sma

class ChameleonV4(BaseStrategy):
    NAME = "[GENE] V4_CHAMELEON"
    
    def __init__(self, genome=None):
        self.genome = genome or {
            "vix_ema": 50,          # VIX Baseline lookback
            "vol_stretch": 1.2,      # Multiplier above baseline to panic
            "mom_period": 200,       # Momentum trend lookback
            "rsi_period": 2,         # Mean reversion lookback
            "rsi_entry": 15,         # Buy dip threshold
            "lev_calm": 3.0,         # Lev when VIX < Baseline
            "lev_stress": 1.0,       # Lev when VIX > Baseline but Trend OK
            "lev_panic": 0.0          # Lev when VIX > Baseline AND Trend Down
        }
        self.reset()

    def reset(self):
        self.closes = []
        self.vix = []
        self.rsi_state = {"avg_gain": 0, "avg_loss": 0}

    def on_data(self, date: str, price_data: dict, prev_data=None) -> dict:
        self.closes.append(price_data['close'])
        self.vix.append(price_data['vix'])
        
        # Need enough data for the largest lookback
        max_lb = max(self.genome["vix_ema"], self.genome["mom_period"])
        if len(self.closes) < max_lb:
            return {"SPY": 1.0}
            
        # 1. Volatility Regime (Relative Stretch)
        # We use a simple SMA for the VIX baseline (standard for this strategy)
        vix_baseline = sum(self.vix[-self.genome["vix_ema"]:]) / self.genome["vix_ema"]
        vol_panic = price_data['vix'] > (vix_baseline * self.genome["vol_stretch"])
        
        # 2. Momentum Filter
        mom_sma = sum(self.closes[-self.genome["mom_period"]:]) / self.genome["mom_period"]
        trend_up = price_data['close'] > mom_sma
        
        # 3. Mean Reversion (RSI)
        # Using stateful RSI for O(1) performance
        r_val = rsi(self.closes, self.genome["rsi_period"], state=self.rsi_state)
        dip_detected = (r_val or 50) < self.genome["rsi_entry"]
        
        # Determine Leverage
        lev = self.genome["lev_calm"]
        if vol_panic:
            if trend_up:
                # Stressed but trend is holding
                lev = self.genome["lev_stress"]
                if dip_detected:
                    lev = self.genome["lev_calm"] # Aggressive buy the dip
            else:
                # Stressed AND trend broken -> Panic
                lev = self.genome["lev_panic"]
        
        # Map to assets
        if lev >= 3.0: return {"3xSPY": 1.0}
        if lev >= 2.0: return {"2xSPY": 1.0}
        if lev >= 1.0: return {"SPY": 1.0}
        return {"CASH": 1.0}
