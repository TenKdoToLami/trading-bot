"""
BEAST strategy — SMA regime detection + realized volatility tiers.

This is the tournament-compatible port of the original BEAST/SHIELD
strategy. Instead of VIX (which would require external data), it uses
realized volatility computed from accumulated SPY prices.

Regime logic:
  - BULL: SPY above its SMA → 100% 3xSPY.
  - PANIC: SPY below SMA for min_b_days → tiered allocation based
    on realized volatility level.

The volatility tier bounds are calibrated for realized vol (not VIX).
Typical realized vol ranges: 5-15% calm, 15-30% elevated, 30-50% crisis.
"""

from strategies.base import BaseStrategy
from src.helpers.indicators import sma, realized_volatility


class BeastRealVol(BaseStrategy):
    NAME = "BEAST (SMA + RealVol)"

    # ------------------------------------------------------------------
    # Strategy DNA — tweak these to create variants
    # ------------------------------------------------------------------
    SMA_PERIOD = 291          # Trend filter lookback
    MIN_B_DAYS = 7            # Minimum days before entering panic
    VOL_WINDOW = 20           # Realized vol lookback (trading days)
    BASE_LOCKOUT_DAYS = 10    # Lock into bull tier 0 for N days

    # Realized volatility tier boundaries (annualized)
    # [calm/elevated, elevated/high, high/extreme]
    VOL_BOUNDS = [0.12, 0.30, 0.45]

    # Allocation weights per panic tier [tier0, tier1, tier2, tier3]
    PANIC_WEIGHTS = [
        {"2xSPY": 0.435, "3xSPY": 0.005, "CASH": 0.56},   # Tier 0: mild
        {"CASH": 1.0},                                       # Tier 1: defensive
        {"3xSPY": 1.0},                                      # Tier 2: re-entry
        {"2xSPY": 0.3675, "3xSPY": 0.6325},                 # Tier 3: aggressive
    ]

    BULL_WEIGHTS = {"3xSPY": 1.0}

    def __init__(self):
        self.reset()

    def reset(self):
        self.prices = []
        self.panic_mode = False
        self.days_in_regime = 0
        self.current_tier = 0
        self.base_lockout = 0
        self.last_holdings = None

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        self.prices.append(spy_price)

        # ---- SMA trend filter ----
        sma_val = sma(self.prices, self.SMA_PERIOD)
        if sma_val is None:
            # Not enough data for SMA — default to bull (3x)
            if self.last_holdings is None:
                self.last_holdings = dict(self.BULL_WEIGHTS)
                return dict(self.BULL_WEIGHTS)
            return None

        sma_triggered = spy_price < sma_val

        # ---- Regime transitions ----
        self.days_in_regime += 1

        if self.panic_mode:
            # Exit panic instantly when SPY recovers above SMA
            if not sma_triggered:
                self.panic_mode = False
                self.days_in_regime = 0
        else:
            # Enter panic after sustained weakness
            if sma_triggered and self.days_in_regime >= self.MIN_B_DAYS:
                self.panic_mode = True
                self.days_in_regime = 0

        # ---- Volatility tier (panic mode only) ----
        if self.panic_mode:
            vol = realized_volatility(self.prices, self.VOL_WINDOW)
            if vol is not None:
                # Digitize: count how many bounds the vol exceeds
                target_tier = sum(1 for b in self.VOL_BOUNDS if vol >= b)
            else:
                target_tier = 0
        else:
            target_tier = 0

        # ---- Base lockout (sticky bull tier) ----
        if self.base_lockout > 0:
            self.base_lockout -= 1
            target_tier = self.current_tier

        if target_tier != self.current_tier:
            if not self.panic_mode and target_tier == 0:
                self.base_lockout = self.BASE_LOCKOUT_DAYS
            self.current_tier = target_tier

        # ---- Determine holdings ----
        if not self.panic_mode:
            new_holdings = dict(self.BULL_WEIGHTS)
        else:
            idx = min(self.current_tier, len(self.PANIC_WEIGHTS) - 1)
            new_holdings = dict(self.PANIC_WEIGHTS[idx])

        # Only signal rebalance when allocation actually changes
        if new_holdings != self.last_holdings:
            self.last_holdings = new_holdings
            return new_holdings

        return None
