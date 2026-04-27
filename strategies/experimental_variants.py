"""
Experimental strategy variants exploring institutional alphas.
"""

from strategies.base import BaseStrategy
from src.helpers.indicators import rsi, sma
import numpy as np

class VIX_TermStructure_Proxy(BaseStrategy):
    """
    Simulates VIX Term Structure (Backwardation vs Contango) using VIX vs its EMA.
    Alpha: VIX spiking above its trend indicates structural panic.
    """
    NAME = "[EXP] 3xSPY | VIX Term Structure"
    
    def reset(self):
        self.vix_ema = None
        
    def on_data(self, date, row, prev_row):
        vix = row.get('vix', 20)
        # Calculate EMA of VIX
        alpha = 2 / (20 + 1)
        if self.vix_ema is None:
            self.vix_ema = vix
        else:
            self.vix_ema = (vix * alpha) + (self.vix_ema * (1 - alpha))
            
        # If VIX is significantly higher than its 20-day trend, it's backwardation
        is_panic = vix > (self.vix_ema * 1.25)
        
        if is_panic:
            return {"CASH": 1.0}
        return {"3xSPY": 1.0}

class Volatility_Risk_Premium(BaseStrategy):
    """
    Compares Implied Volatility (VIX) vs Realized Volatility (RealVol).
    Alpha: If VIX >> RealVol, fear is overpriced (Buying opportunity).
           If RealVol > VIX, complacency is dangerous (Exit).
    """
    NAME = "[EXP] 3xSPY | Vol Risk Premium"
    
    def reset(self):
        self.prices = []
        
    def on_data(self, date, row, prev_row):
        self.prices.append(row['close'])
        if len(self.prices) < 21:
            return {"3xSPY": 1.0}
            
        # Calculate 20-day Realized Vol (Annualized)
        rets = np.diff(np.log(self.prices[-21:]))
        real_vol = np.std(rets) * np.sqrt(252) * 100 # In VIX units
        
        vix = row.get('vix', 20)
        
        # Danger: Reality is scarier than what the market expects
        if real_vol > vix:
            return {"CASH": 1.0}
        # Edge: Market is panicked but reality is calm (Fear > Risk)
        if vix > (real_vol * 1.5):
            return {"3xSPY": 1.0}
            
        # Neutral: Follow 200-day Trend
        if len(self.prices) > 200:
            ma = sum(self.prices[-200:]) / 200
            if row['close'] < ma:
                return {"CASH": 1.0}
                
        return {"3xSPY": 1.0}

class YieldCurve_UnInversion(BaseStrategy):
    """
    Focuses on the Yield Curve un-inversion signal.
    Alpha: The crash usually happens when the curve cross BACK above 0.
    """
    NAME = "[EXP] 3xSPY | Macro Un-Inversion"
    
    def reset(self):
        pass

    def on_data(self, date, row, prev_row):
        yc = row.get('yield_curve', 1.0)
        
        # If curve was inverted and is now rapidly returning to 0 (Un-inverting)
        # We use a tight threshold around 0 to detect the 'danger zone'
        if yc > 0 and yc < 0.2:
            return {"CASH": 1.0}
        
        # Otherwise stay 3x (even if inverted - usually a melt-up phase)
        return {"3xSPY": 1.0}

class RSI2_MeanReversion(BaseStrategy):
    """
    Mean Reversion 'Spring' strategy using RSI(2).
    Alpha: Extreme oversold snap-backs.
    """
    NAME = "[EXP] 3xSPY | RSI(2) Snapback"
    
    def reset(self):
        self.prices = []
        self.in_trade = False
        
    def on_data(self, date, row, prev_row):
        self.prices.append(row['close'])
        if len(self.prices) < 10:
            return {"CASH": 1.0}
            
        r2 = rsi(self.prices, 2)
        if r2 is None: return {"CASH": 1.0}
        
        # Entry: Extreme oversold
        if r2 < 10:
            self.in_trade = True
            
        # Exit: Neutral/Overbought
        if r2 > 70:
            self.in_trade = False
            
        if self.in_trade:
            return {"3xSPY": 1.0}
        return {"CASH": 1.0}
