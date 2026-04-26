"""
Tournament runner — the central control unit.

Loads SPY data, discovers strategy plugins, feeds each strategy
one day at a time, and collects results for comparison.

Usage:
    runner = TournamentRunner()
    runner.load_data()
    results = runner.run_all()
    runner.print_results()
    runner.generate_chart()
"""

import concurrent.futures
import importlib
import os
import random
import sys

import numpy as np

from strategies.base import BaseStrategy
from src.tournament.portfolio import Portfolio
from src.helpers.data_provider import load_spy_data


def _execute_simulation(strategy_type, price_data_list, dates):
    """
    Standalone simulation function that can be picked for parallel execution.
    """
    strategy = strategy_type()
    strategy.reset()
    portfolio = Portfolio()
    pending_holdings = None

    for i in range(len(price_data_list)):
        date_str = str(dates[i].date())
        row = price_data_list[i]
        
        # Realistic Price: Avg of Open and Close
        spy_price = (float(row['open']) + float(row['close'])) / 2
        prev_row = price_data_list[i-1] if i > 0 else None

        # 1. Apply today's return using CURRENT holdings
        if i > 0:
            prev_price = (float(prev_row['open']) + float(prev_row['close'])) / 2
            daily_ret = (spy_price - prev_price) / prev_price
            portfolio.apply_daily_return(date_str, daily_ret)

        # 2. Execute yesterday's signal at today's execution price
        if pending_holdings is not None:
            portfolio.rebalance(date_str, pending_holdings)
            pending_holdings = None

        # 3. Feed TODAY'S full finalized data to strategy to generate TOMORROW'S signal
        result = strategy.on_data(date_str, row, prev_row)

        if result is not None:
            # Simple sum check
            if abs(sum(result.values()) - 1.0) > 0.001:
                raise ValueError(f"[{strategy.NAME}] Invalid weights: {result}")
            pending_holdings = result

    return {
        "strategy": strategy.NAME,
        "portfolio": portfolio,
        "metrics": portfolio.get_metrics(),
    }


class TournamentRunner:
    """
    Control unit that orchestrates strategy simulations.

    For each trading day it:
      1. Applies yesterday-to-today return using current holdings.
      2. Feeds today's SPY close to the strategy.
      3. If the strategy returns new holdings, validates and applies them.
    """

    def __init__(self, start_date: str = "1993-01-01", end_date: str = None):
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.results = {}

    def load_data(self, force_refresh: bool = False):
        """Load SPY data (from cache or yfinance)."""
        self.data = load_spy_data(
            start_date=self.start_date,
            force_refresh=force_refresh,
        )
        if self.end_date:
            self.data = self.data[:self.end_date]

    def discover_strategies(self) -> list:
        """
        Auto-discover all BaseStrategy subclasses in the strategies/ package.

        Scans every .py file in strategies/ (except base.py and __init__.py),
        imports it, and collects any class that subclasses BaseStrategy.
        """
        strategies_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "strategies"
        )
        strategies_dir = os.path.abspath(strategies_dir)
        strategies = []

        for filename in sorted(os.listdir(strategies_dir)):
            if filename.startswith("_") or filename == "base.py":
                continue
            if not filename.endswith(".py"):
                continue

            module_name = f"strategies.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
            except Exception as e:
                print(f"  Warning: could not import {module_name}: {e}")
                continue

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseStrategy)
                    and attr is not BaseStrategy
                    and not attr.__name__.startswith("_")
                ):
                    strategies.append(attr())

        return strategies

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    def run_strategy(self, strategy: BaseStrategy) -> dict:
        """Run a single strategy through the full dataset."""
        price_data_list = self.data[['open', 'high', 'low', 'close', 'volume']].to_dict('records')
        dates = self.data.index
        return _execute_simulation(type(strategy), price_data_list, dates)

    def run_all(self) -> dict:
        """Run every discovered strategy and collect results (Parallel)."""
        if self.data is None:
            self.load_data()

        strategies = self.discover_strategies()
        print(f"\nDiscovered {len(strategies)} strategies. Running in parallel...")

        price_data_list = self.data[['open', 'high', 'low', 'close', 'volume']].to_dict('records')
        dates = self.data.index

        results = {}
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future_to_strat = {
                executor.submit(_execute_simulation, type(s), price_data_list, dates): s.NAME
                for s in strategies
            }
            for future in concurrent.futures.as_completed(future_to_strat):
                name = future_to_strat[future]
                try:
                    res = future.result()
                    results[name] = res
                    cagr = res["metrics"]["cagr"] * 100
                    print(f"  Completed: {name:<35} | CAGR: {cagr:.2f}%")
                except Exception as e:
                    print(f"  Error running {name}: {e}")

        self.results = results
        return results

    def run_single(self, strategy_name: str) -> dict:
        """Run a single strategy by name."""
        if self.data is None:
            self.load_data()

        strategies = self.discover_strategies()
        for s in strategies:
            if s.NAME.lower() == strategy_name.lower():
                print(f"  Running: {s.NAME}...")
                result = self.run_strategy(s)
                self.results = {s.NAME: result}
                return result

        available = [s.NAME for s in strategies]
        raise ValueError(
            f"Strategy '{strategy_name}' not found. Available: {available}"
        )

    def run_strategy_on_slice(self, strategy: BaseStrategy,
                              start_idx: int, end_idx: int) -> dict:
        """Run a strategy on a sub-range of the loaded data."""
        price_data_list = self.data[['open', 'high', 'low', 'close', 'volume']].iloc[start_idx:end_idx].to_dict('records')
        dates = self.data.index[start_idx:end_idx]
        return _execute_simulation(type(strategy), price_data_list, dates)

    def run_resilience(self, samples_per_bucket: int = 10):
        """
        Resilience stress test — run all strategies on random periods
        across multiple duration buckets.

        Buckets (in years): 0-5, 5-10, 10-15, 15-20, 20-25, 25-30.
        For each bucket, N random start points are sampled and a random
        duration within that bucket's range is selected.

        Prints a per-bucket table and a final overall aggregate table.

        Args:
            samples_per_bucket: Number of random periods per bucket (default 10).
        """
        if self.data is None:
            self.load_data()

        strategies = self.discover_strategies()
        total_days = len(self.data)

        print(f"\n{'#' * 70}")
        print(f"  RESILIENCE TEST — {samples_per_bucket} samples per bucket")
        print(f"  Strategies: {[s.NAME for s in strategies]}")
        print(f"  Data span: {total_days} trading days")
        print(f"{'#' * 70}")

        # Duration buckets in years
        buckets = [
            (0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, 30),
        ]

        # Generate random periods for each bucket
        bucket_periods = {}
        for lo_yr, hi_yr in buckets:
            lo_days = lo_yr * 252
            hi_days = hi_yr * 252

            # Skip buckets that exceed available data
            if lo_days >= total_days - 50:
                continue

            periods = []
            for _ in range(samples_per_bucket):
                # Clamp duration to what's available
                actual_hi = min(hi_days, total_days - 50)
                actual_lo = max(lo_days, 252)  # Minimum 1 year
                if actual_lo >= actual_hi:
                    actual_lo = actual_hi - 1

                duration = random.randint(actual_lo, actual_hi)
                max_start = total_days - duration - 1
                start = random.randint(0, max(0, max_start))
                periods.append((start, start + duration))

            bucket_periods[(lo_yr, hi_yr)] = periods

        # Run all strategies on all periods, collecting metrics per bucket
        # Structure: {bucket: {strategy_name: [metrics_dict, ...]}}
        all_bucket_results = {}
        overall_results = {s.NAME: [] for s in strategies}

        for (lo_yr, hi_yr), periods in bucket_periods.items():
            label = f"{lo_yr}-{hi_yr} Years"
            print(f"\n  Bucket: {label} ({len(periods)} periods)...", end="", flush=True)

            bucket_data = {s.NAME: [] for s in strategies}
            
            # Prepare all tasks for this bucket: (strategy_type, prices_slice, dates_slice)
            tasks = []
            for start_idx, end_idx in periods:
                price_data_slice = self.data[['open', 'high', 'low', 'close', 'volume']].iloc[start_idx:end_idx].to_dict('records')
                dates_slice = self.data.index[start_idx:end_idx]
                for s in strategies:
                    tasks.append((type(s), price_data_slice, dates_slice))

            # Run in parallel
            with concurrent.futures.ProcessPoolExecutor() as executor:
                # We submit all tasks and collect as they complete
                futures = [executor.submit(_execute_simulation, *t) for t in tasks]
                for f in concurrent.futures.as_completed(futures):
                    res = f.result()
                    bucket_data[res["strategy"]].append(res["metrics"])
                    overall_results[res["strategy"]].append(res["metrics"])

            print(" Done.")
            all_bucket_results[(lo_yr, hi_yr)] = bucket_data
            self._print_resilience_table(label, bucket_data)

        # Overall aggregate
        self._print_resilience_table(
            f"OVERALL ({sum(len(p) for p in bucket_periods.values())} periods)",
            overall_results,
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_holdings(self, holdings: dict, strategy_name: str, date: str):
        """Ensure returned holdings obey tournament rules."""
        for asset in holdings:
            if asset not in BaseStrategy.ALLOWED_ASSETS:
                raise ValueError(
                    f"[{strategy_name} @ {date}] Invalid asset: '{asset}'. "
                    f"Allowed: {BaseStrategy.ALLOWED_ASSETS}"
                )

        total = sum(holdings.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"[{strategy_name} @ {date}] Holdings must sum to 1.0, "
                f"got {total:.4f}: {holdings}"
            )

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def _print_resilience_table(self, title: str, strategy_metrics: dict):
        """
        Print an aggregated resilience table for one bucket or overall.
        Strategies are displayed as rows, metrics as columns.
        """
        metrics_keys = ["cagr", "sharpe", "max_dd", "trades_per_year", "avg_leverage"]
        metric_labels = {
            "cagr": "CAGR",
            "sharpe": "Sharpe",
            "max_dd": "Max DD",
            "trades_per_year": "Trd/Yr",
            "avg_leverage": "Lev",
        }

        names = sorted(strategy_metrics.keys())
        
        # Calculate total width
        col_width = 11  # Width for each Mean/Med column
        strat_width = 38
        total_width = strat_width + (len(metrics_keys) * 2 * (col_width + 3))

        # Header
        print(f"\n  {'=' * total_width}")
        print(f"  {title}")
        print(f"  {'=' * total_width}")

        header = f"  {'Strategy':<{strat_width}}"
        for key in metrics_keys:
            label = metric_labels[key]
            header += f" | {label+'(Mn)':>{col_width}} | {label+'(Md)':>{col_width}}"
        print(header)
        print(f"  {'-' * total_width}")

        for name in names:
            row = f"  {name:<{strat_width}}"
            for key in metrics_keys:
                values = [m[key] for m in strategy_metrics[name]]
                mn = np.mean(values)
                md = np.median(values)

                for val in [mn, md]:
                    if key in ("cagr", "max_dd"):
                        row += f" | {val * 100:>{col_width - 1}.2f}%"
                    elif key == "trades_per_year":
                        row += f" | {val:>{col_width}.1f}"
                    elif key == "avg_leverage":
                        row += f" | {val:>{col_width - 1}.2f}x"
                    else:
                        row += f" | {val:>{col_width}.2f}"
            print(row)
        print(f"  {'=' * total_width}")


    def print_results(self):
        """Print a formatted comparison table sorted by CAGR."""
        if not self.results:
            print("No results. Run a tournament first.")
            return

        # Header
        print("\n" + "=" * 95)
        print("  STRATEGY TOURNAMENT RESULTS")
        print("=" * 95)
        header = (
            f"  {'Strategy':<30} | {'CAGR':>8} | {'Sharpe':>8} | "
            f"{'Max DD':>9} | {'Vol':>8} | {'Trades':>7}"
        )
        print(header)
        print("-" * 95)

        # Rows sorted by CAGR descending
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: x[1]["metrics"]["cagr"],
            reverse=True,
        )
        for name, res in sorted_results:
            m = res["metrics"]
            print(
                f"  {name:<30} | {m['cagr']*100:>7.2f}% | "
                f"{m['sharpe']:>8.2f} | {m['max_dd']*100:>8.1f}% | "
                f"{m['volatility']*100:>7.1f}% | {m['num_rebalances']:>7}"
            )

        print("=" * 95)

        # Allocation breakdown table
        print("\n" + "=" * 95)
        print("  ALLOCATION BREAKDOWN (Average Weight %)")
        print("=" * 95)
        header = (
            f"  {'Strategy':<30} | {'Avg Lev':>8} | "
            f"{'SPY':>8} | {'2xSPY':>8} | {'3xSPY':>8} | {'CASH':>8}"
        )
        print(header)
        print("-" * 95)

        for name, res in sorted_results:
            m = res["metrics"]
            a = m["allocation_pct"]
            print(
                f"  {name:<30} | {m['avg_leverage']:>7.2f}x | "
                f"{a['SPY']*100:>7.1f}% | {a['2xSPY']*100:>7.1f}% | "
                f"{a['3xSPY']*100:>7.1f}% | {a['CASH']*100:>7.1f}%"
            )

        print("=" * 95)

    def generate_chart(self, output_path: str = "results/tournament_chart.png"):
        """Generate an equity curve comparison chart (log scale)."""
        import matplotlib.pyplot as plt

        if not self.results:
            print("No results. Run a tournament first.")
            return

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        plt.style.use("dark_background")
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["axes.facecolor"] = "#121212"
        plt.rcParams["figure.facecolor"] = "#121212"

        fig, ax = plt.subplots(figsize=(16, 9))

        colors = [
            "#ff4757", "#2ecc71", "#3498db", "#f39c12",
            "#9b59b6", "#1abc9c", "#e74c3c", "#00cec9",
        ]

        for i, (name, res) in enumerate(self.results.items()):
            portfolio = res["portfolio"]
            dates = [d for d, _ in portfolio.equity_curve]
            equities = [e for _, e in portfolio.equity_curve]

            color = colors[i % len(colors)]
            ax.plot(dates, equities, label=name, color=color, linewidth=2)

        ax.set_yscale("log")
        ax.set_title(
            "Strategy Tournament — Equity Curves (Log Scale)",
            fontsize=18, fontweight="bold", pad=20,
        )
        ax.set_ylabel("Growth of $1", fontsize=14)
        ax.grid(True, which="both", ls="-", alpha=0.1)
        ax.legend(loc="upper left", fontsize=11)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        print(f"\nChart saved to {output_path}")
