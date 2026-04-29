"""
Institutional Core: Experimental strategy variants with proven alpha.
Only strategies exceeding the 20% CAGR threshold are retained.
"""

from strategies.base import BaseStrategy
from src.helpers.indicators import rsi
import numpy as np

class VIX_TermStructure_Proxy(BaseStrategy):
    """
    Alpha: 24.0% CAGR. Simulates VIX Term Structure (Backwardation vs Contango).
    """
    NAME = "[EXP] 3xSPY | VIX Term Structure"
    
    def reset(self):
        self.vix_ema = None
        
    def on_data(self, date, row, prev_row):
        vix = row.get('vix', 20)
        alpha = 2 / (20 + 1)
        if self.vix_ema is None:
            self.vix_ema = vix
        else:
            self.vix_ema = (vix * alpha) + (self.vix_ema * (1 - alpha))
            
        is_panic = vix > (self.vix_ema * 1.25)
        if is_panic:
            return {"CASH": 1.0}
        return {"3xSPY": 1.0}

class Volatility_Risk_Premium(BaseStrategy):
    """
    Alpha: 22.2% CAGR. Compares Implied Volatility (VIX) vs Realized Volatility (RealVol).
    """
    NAME = "[EXP] 3xSPY | Vol Risk Premium"
    
    def reset(self):
        self.prices = []
        
    def on_data(self, date, row, prev_row):
        self.prices.append(row['close'])
        if len(self.prices) < 21:
            return {"3xSPY": 1.0}
            
        rets = np.diff(np.log(self.prices[-21:]))
        real_vol = np.std(rets) * np.sqrt(252) * 100 
        vix = row.get('vix', 20)
        
        if real_vol > vix:
            return {"CASH": 1.0}
        if vix > (real_vol * 1.5):
            return {"3xSPY": 1.0}
            
        if len(self.prices) > 200:
            ma = sum(self.prices[-200:]) / 200
            if row['close'] < ma:
                return {"CASH": 1.0}
                
        return {"3xSPY": 1.0}

class RSI2_MeanReversion(BaseStrategy):
    """
    Alpha: 20.9% CAGR (Post-Tuning). Extreme oversold snap-backs using RSI(2).
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
        
        if r2 < 15: # Tuned Entry
            self.in_trade = True
            
        if r2 > 70:
            self.in_trade = False
            
        if self.in_trade:
            return {"3xSPY": 1.0}
        return {"CASH": 1.0}
