"""
Portfolio tracker for a single strategy simulation.

Tracks holdings, applies daily leveraged returns, and computes
performance metrics (CAGR, Sharpe, Max Drawdown).
"""

import numpy as np


class Portfolio:
    """
    Simulates a portfolio that holds a weighted mix of
    SPY, 2xSPY, 3xSPY, and CASH.

    The control unit calls rebalance() when a strategy changes
    its allocation, and apply_daily_return() every trading day.
    """

    # Annualized cost/yield assumptions
    EXPENSE_2X = 0.0120   # 2x leveraged ETF expense ratio
    EXPENSE_3X = 0.0150   # 3x leveraged ETF expense ratio
    CASH_YIELD = 0.03     # Risk-free rate (cash/bonds)
    SPY_EXPENSE = 0.0     # SPY itself (negligible)

    def __init__(self, initial_equity: float = 1.0):
        self.initial_equity = initial_equity
        self.reset()

    def reset(self, initial_equity: float = None):
        """Clear all state for a fresh simulation."""
        if initial_equity is not None:
            self.initial_equity = initial_equity
        self.equity = self.initial_equity
        self.holdings = {"CASH": 1.0}
        self.is_liquidated = False

        self.equity_curve = []     # [(date_str, equity), ...]
        self.holdings_log = []     # [(date_str, holdings_dict), ...]
        self.rebalance_log = []    # [(date_str, new_holdings), ...]

    def rebalance(self, date: str, new_holdings: dict):
        """
        Update allocation weights.
        """
        if new_holdings == self.holdings:
            return
            
        self.holdings = dict(new_holdings)
        self.rebalance_log.append((date, dict(new_holdings)))

    def apply_daily_return(self, date: str, spy_daily_return: float):
        """
        Apply one day of returns based on current holdings.

        Args:
            date:             ISO date string.
            spy_daily_return: SPY's percentage return for this day
                              (e.g. 0.01 = +1%).
        """
        asset_returns = {
            "SPY":   spy_daily_return,
            "2xSPY": (spy_daily_return * 2.0) - (self.EXPENSE_2X / 252),
            "3xSPY": (spy_daily_return * 3.0) - (self.EXPENSE_3X / 252),
            "CASH":  self.CASH_YIELD / 252,
        }

        if self.is_liquidated:
            self.equity_curve.append((date, 0.0))
            return

        portfolio_return = sum(
            self.holdings.get(asset, 0.0) * ret
            for asset, ret in asset_returns.items()
        )

        self.equity *= (1.0 + portfolio_return)
        
        if self.equity <= 0:
            self.equity = 0.0
            self.is_liquidated = True

        self.equity_curve.append((date, self.equity))
        self.holdings_log.append((date, dict(self.holdings)))

    def get_metrics(self) -> dict:
        """
        Compute summary performance metrics from the equity curve.

        Returns:
            dict with keys: cagr, sharpe, max_dd, total_return, volatility,
                            num_rebalances.
        """
        if len(self.equity_curve) < 2:
            return {
                "cagr": 0.0, "sharpe": 0.0, "max_dd": 0.0,
                "total_return": 0.0, "volatility": 0.0,
                "num_rebalances": 0, "trades_per_year": 0.0,
                "avg_leverage": 0.0,
                "allocation_pct": {a: 0.0 for a in ("SPY", "2xSPY", "3xSPY", "CASH")},
            }

        equities = np.array([e for _, e in self.equity_curve])

        # Total return
        total_return = (equities[-1] / equities[0]) - 1.0

        # CAGR
        years = len(equities) / 252.0
        if equities[-1] > 0 and years > 0:
            cagr = (equities[-1] / equities[0]) ** (1.0 / years) - 1.0
        else:
            cagr = -1.0

        # Daily returns
        daily_rets = np.diff(equities) / equities[:-1]

        # Annualized volatility
        ann_vol = np.std(daily_rets) * np.sqrt(252)

        # Sharpe ratio (excess return over risk-free rate)
        ann_ret = np.mean(daily_rets) * 252
        sharpe = (ann_ret - 0.03) / ann_vol if ann_vol > 0 else 0.0

        # Max drawdown
        peak = np.maximum.accumulate(equities)
        dd = (equities - peak) / peak
        max_dd = float(np.min(dd))

        # Trades per year
        num_rebalances = len(self.rebalance_log)
        trades_per_year = num_rebalances / years if years > 0 else 0.0

        # Average leverage and per-asset allocation from holdings log
        leverage_map = {"SPY": 1.0, "2xSPY": 2.0, "3xSPY": 3.0, "CASH": 0.0}
        all_assets = ("SPY", "2xSPY", "3xSPY", "CASH")
        asset_weight_sums = {a: 0.0 for a in all_assets}
        leverage_sum = 0.0
        n_days = len(self.holdings_log)

        for _, holdings in self.holdings_log:
            for asset in all_assets:
                w = holdings.get(asset, 0.0)
                asset_weight_sums[asset] += w
                leverage_sum += w * leverage_map[asset]

        if n_days > 0:
            avg_leverage = leverage_sum / n_days
            allocation_pct = {a: asset_weight_sums[a] / n_days for a in all_assets}
        else:
            avg_leverage = 0.0
            allocation_pct = {a: 0.0 for a in all_assets}

        return {
            "cagr": cagr,
            "sharpe": sharpe,
            "max_dd": max_dd,
            "total_return": total_return,
            "volatility": ann_vol,
            "num_rebalances": num_rebalances,
            "trades_per_year": trades_per_year,
            "avg_leverage": avg_leverage,
            "allocation_pct": allocation_pct,
        }

