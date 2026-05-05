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

    # Annualized Institutional Cost/Yield assumptions
    EXPENSE_SPY = 0.0003  # 0.03% (VOO/SPY standard)
    EXPENSE_2X  = 0.0091  # 0.91% (SSO standard)
    EXPENSE_3X  = 0.0091  # 0.91% (UPRO standard)
    EXPENSE_TLT = 0.0015  # 0.15% (TLT standard)
    EXPENSE_SHY = 0.0015  # 0.15% (SHY standard)
    EXPENSE_GOLD = 0.0040 # 0.40% (GLD standard)
    EXPENSE_SHORT = 0.0095 # 0.95% (SH/SDS short cost)
    CASH_YIELD  = 0.0350  # 3.50% (Conservative historical avg risk-free rate)
    
    # Execution Friction
    SLIPPAGE_BPS = 0.0005 # 5 bps (0.05%) per trade
    COMMISSION   = 0.0001 # 1 bps (0.01%) or flat fee equivalent
    
    # Minimal turnover required to trigger a trade (1%)
    REBALANCE_THRESHOLD = 0.01

    def __init__(self, initial_equity: float = 1.0, slippage_bps: float = 0.0005, commission_bps: float = 0.0001):
        self.initial_equity = initial_equity
        self.slippage_bps = slippage_bps
        self.commission_bps = commission_bps
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
        Update allocation weights. Applies slippage and commission to turnover.
        Ensures total holdings always normalize to 1.0.
        """
        # --- NORMALIZATION LAYER ---
        # 1. Handle empty or zeroed holdings
        total_w = sum(new_holdings.values())
        if total_w <= 0:
            normalized = {"CASH": 1.0}
        else:
            # 2. Proportionally scale to 1.0
            normalized = {k: v / total_w for k, v in new_holdings.items()}

        # Calculate turnover based on normalized weights
        all_assets = set(list(self.holdings.keys()) + list(normalized.keys()))
        turnover = sum(abs(normalized.get(a, 0.0) - self.holdings.get(a, 0.0)) for a in all_assets)
        
        # 3. ONLY rebalance if turnover exceeds threshold to prevent high-frequency noise
        if turnover > self.REBALANCE_THRESHOLD:
            friction_cost = turnover * (self.slippage_bps + self.commission_bps)
            self.equity *= (1.0 - friction_cost)
            self.holdings = normalized
            self.rebalance_log.append((date, dict(normalized)))
        # If turnover is below threshold, we keep the OLD holdings in self.holdings
        # so that tomorrow's turnover calculation includes today's drift.

    def apply_daily_return(self, date: str, returns_dict: dict):
        """
        Apply one day of returns based on current holdings.
        'returns_dict' should contain: spy, tlt, shy, gold
        """
        spy_ret = returns_dict.get("spy", 0.0)
        tlt_ret = returns_dict.get("tlt", 0.0)
        shy_ret = returns_dict.get("shy", 0.0)
        gold_ret = returns_dict.get("gold", 0.0)

        # Compounded internal expense ratios (Annual -> Daily)
        asset_returns = {
            "SPY":   spy_ret - (self.EXPENSE_SPY / 252),
            "2xSPY": (spy_ret * 2.0) - (self.EXPENSE_2X / 252),
            "3xSPY": (spy_ret * 3.0) - (self.EXPENSE_3X / 252),
            "CASH":  self.CASH_YIELD / 252,
            "TLT":   tlt_ret - (self.EXPENSE_TLT / 252),
            "SHY":   shy_ret - (self.EXPENSE_SHY / 252),
            "GOLD":  gold_ret - (self.EXPENSE_GOLD / 252),
            "2xSHORT_SPY": (spy_ret * -2.0) - (self.EXPENSE_SHORT / 252)
        }

        if self.is_liquidated:
            self.equity_curve.append((date, 0.0))
            return

        portfolio_return = sum(
            self.holdings.get(asset, 0.0) * asset_returns.get(asset, 0.0)
            for asset in self.holdings
        )

        self.equity *= (1.0 + portfolio_return)
        
        if self.equity <= 0:
            self.equity = 0.0
            self.is_liquidated = True

        self.equity_curve.append((date, self.equity))
        self.holdings_log.append((date, dict(self.holdings)))

    def get_metrics(self) -> dict:
        if len(self.equity_curve) < 2:
            return {
                "cagr": 0.0, "sharpe": 0.0, "max_dd": 0.0,
                "total_return": 0.0, "volatility": 0.0,
                "num_rebalances": 0, "trades_per_year": 0.0,
                "avg_leverage": 0.0,
                "allocation_pct": {a: 0.0 for a in ("SPY", "2xSPY", "3xSPY", "CASH", "TLT", "SHY", "GOLD", "2xSHORT_SPY")},
            }

        equities = np.array([e for _, e in self.equity_curve])
        
        # 1. CAGR
        years = len(equities) / 252.0
        cagr = (equities[-1] / equities[0]) ** (1.0 / years) - 1.0 if equities[-1] > 0 else -1.0
        total_return = (equities[-1] / equities[0]) - 1.0

        # 2. Daily returns (The basis for Vol and Sharpe)
        daily_rets = np.diff(equities) / equities[:-1]
        
        # 3. Volatility (Annualized)
        vol = np.std(daily_rets) * np.sqrt(252)
        if vol < 0.000000001: vol = 0.000000001 # Prevent infinite Sharpe

        # 4. Sharpe (Risk-free rate assumed at 3%)
        ann_ret = np.mean(daily_rets) * 252
        sharpe = (ann_ret - 0.03) / vol

        # Max drawdown
        peak = np.maximum.accumulate(equities)
        dd = (equities - peak) / peak
        max_dd = float(np.min(dd))
        
        num_rebalances = len(self.rebalance_log)
        trades_per_year = num_rebalances / years if years > 0 else 0.0

        # Average leverage and per-asset allocation from holdings log
        leverage_map = {
            "SPY": 1.0, "2xSPY": 2.0, "3xSPY": 3.0, "CASH": 0.0,
            "TLT": 1.0, "SHY": 1.0, "GOLD": 1.0, "2xSHORT_SPY": -2.0
        }
        all_assets = ("SPY", "2xSPY", "3xSPY", "CASH", "TLT", "SHY", "GOLD", "2xSHORT_SPY")
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

        # Win Rate and Profit Factor
        wins = daily_rets[daily_rets > 0]
        losses = daily_rets[daily_rets < 0]
        
        win_rate = len(wins) / len(daily_rets) if len(daily_rets) > 0 else 0.0
        
        gross_wins = np.sum(wins)
        gross_losses = np.sum(np.abs(losses))
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else (99.0 if gross_wins > 0 else 0.0)
        
        # Calmar Ratio
        calmar = cagr / abs(max_dd) if max_dd != 0 else 0.0
        
        # Sortino Ratio (Downside volatility)
        downside_rets = daily_rets[daily_rets < 0]
        downside_vol = np.std(downside_rets) * np.sqrt(252) if len(downside_rets) > 0 else 0.0
        sortino = (ann_ret - 0.03) / downside_vol if downside_vol > 0 else 0.0
        
        # Omega Ratio (threshold 0%)
        gains = np.sum(daily_rets[daily_rets > 0])
        losses_sum = np.sum(np.abs(daily_rets[daily_rets < 0]))
        omega = (gains / losses_sum) if losses_sum > 0 else 1.0
        
        # Expectancy (Average return per day)
        expectancy = np.mean(daily_rets)
        
        # Multiplier (Total Return + 1, e.g. 1445.5x)
        multiplier = equities[-1] / equities[0]
        
        return {
            "cagr": cagr,
            "sharpe": sharpe,
            "max_dd": max_dd,
            "total_return": total_return,
            "volatility": vol,
            "num_rebalances": num_rebalances,
            "trades_per_year": trades_per_year,
            "avg_leverage": avg_leverage,
            "allocation_pct": allocation_pct,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "calmar": calmar,
            "sortino": sortino,
            "omega": omega,
            "expectancy": expectancy,
            "multiplier": multiplier,
            "drawdowns": dd.tolist()
        }

    def get_history(self) -> dict:
        """Returns time-series history of leverage and asset allocations."""
        leverage_map = {
            "SPY": 1.0, "2xSPY": 2.0, "3xSPY": 3.0, "CASH": 0.0,
            "TLT": 1.0, "SHY": 1.0, "GOLD": 1.0, "2xSHORT_SPY": -2.0
        }
        history = {
            "leverage": [],
            "regime": [], # The primary asset (highest weight)
            "allocations": [] # Full weighting history
        }
        for _, holdings in self.holdings_log:
            lev = sum(holdings.get(a, 0.0) * leverage_map[a] for a in leverage_map)
            history["leverage"].append(float(lev))
            
            # Find the primary asset
            primary = max(holdings.items(), key=lambda x: x[1])[0]
            history["regime"].append(primary)
            history["allocations"].append(dict(holdings))
            
        return history

    def log_telemetry(self, date: str, data: dict):
        """Logs internal strategy metrics for deep-dive auditing."""
        if not hasattr(self, 'telemetry'):
            self.telemetry = {}
        
        for k, v in data.items():
            if k not in self.telemetry:
                self.telemetry[k] = []
            self.telemetry[k].append(v)

