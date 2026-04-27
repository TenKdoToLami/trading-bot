"""
Advanced VIX-based recovery strategies using state-machine logic.
"""

from strategies.base import BaseStrategy
from src.helpers.indicators import sma

class _SSORecoveryBase(BaseStrategy):
    """Abstract base for tiered SSO recovery strategies."""
    def reset(self):
        self.prices = []
        self.vix_history = []
        self.peak_price = 0.0
        self.peak_vix = 0.0
        self.state = "BULL" # BULL, PANIC, RECOVERY, WAIT_ATH
        self.last_holdings = None

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        self.prices.append(spy_price)
        vix = float(price_data.get('vix', 20.0))
        self.vix_history.append(vix)
        
        # 1. Track local peak and reset state on new ATH
        if spy_price > self.peak_price:
            self.peak_price = spy_price
            if self.state in ["RECOVERY", "WAIT_ATH", "PANIC"]:
                self.state = "BULL"
        
        # Track peak VIX during panic for crush detection
        if self.state == "PANIC":
            if vix > self.peak_vix:
                self.peak_vix = vix
        elif self.state == "BULL":
            self.peak_vix = 0.0
        
        # 2. State Machine Logic
        dd = (spy_price - self.peak_price) / self.peak_price if self.peak_price > 0 else 0
        
        if self.state == "BULL":
            if dd < -0.10:
                self.state = "PANIC"
        
        elif self.state == "PANIC":
            if self.check_panic_over(price_data):
                self.state = "RECOVERY"
        
        elif self.state == "RECOVERY":
            if vix > 25:
                self.state = "WAIT_ATH"
        
        elif self.state == "WAIT_ATH":
            pass
            
        # 3. Determine Holdings
        if self.state == "BULL":
            new_holdings = {"3xSPY": 1.0}
        elif self.state == "RECOVERY":
            new_holdings = {"2xSPY": 1.0}
        else:
            new_holdings = {"CASH": 1.0}
        
        if new_holdings != self.last_holdings:
            self.last_holdings = new_holdings
            return new_holdings
        return None

    def check_panic_over(self, price_data: dict) -> bool:
        raise NotImplementedError

class SSO_Rec_VIX_Trend(_SSORecoveryBase):
    NAME = "3x SPY (SSO Recovery: VIX Trend)"
    def check_panic_over(self, price_data):
        vix = float(price_data.get('vix', 20.0))
        vix_sma = sma(self.vix_history, 20)
        return vix < vix_sma if vix_sma else False

class SSO_Rec_Vol_Crush(_SSORecoveryBase):
    NAME = "3x SPY (SSO Recovery: Vol Crush)"
    def check_panic_over(self, price_data):
        vix = float(price_data.get('vix', 20.0))
        return vix < (self.peak_vix * 0.80) if self.peak_vix > 0 else False

class SSO_Rec_Price_Confirm(_SSORecoveryBase):
    NAME = "3x SPY (SSO Recovery: Price Confirm)"
    def check_panic_over(self, price_data):
        vix = float(price_data.get('vix', 20.0))
        spy_price = price_data['close']
        spy_sma = sma(self.prices, 20)
        return vix < 30 and (spy_price > spy_sma if spy_sma else False)

class SSO_Rec_Yield_Curve(_SSORecoveryBase):
    NAME = "3x SPY (SSO Recovery: Yield Curve)"
    def check_panic_over(self, price_data):
        yc = float(price_data.get('yield_curve', 0.0))
        return yc > 0.0
