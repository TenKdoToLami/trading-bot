"""
Tournament CLI — single entry point for running strategy backtests.

Usage:
    # Run all discovered strategies (full backtest)
    python tests/run_tournament.py

    # Run a single strategy
    python tests/run_tournament.py --strategy "BEAST (SMA + RealVol)"

    # Custom date range
    python tests/run_tournament.py --start 2008-01-01 --end 2012-12-31

    # Resilience test — random periods across duration buckets
    python tests/run_tournament.py --resilience

    # Resilience with custom sample count per bucket
    python tests/run_tournament.py --resilience --samples 20

    # Force refresh cached SPY data
    python tests/run_tournament.py --refresh
"""

import os
import sys
import argparse

# Ensure project root is on the import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.tournament.runner import TournamentRunner


def main():
    parser = argparse.ArgumentParser(
        description="Strategy Tournament — backtest and compare strategies."
    )
    parser.add_argument(
        "--strategy", type=str, default=None,
        help="Run a single strategy by name (case-insensitive). "
             "If omitted, runs all discovered strategies.",
    )
    parser.add_argument(
        "--start", type=str, default="1993-01-01",
        help="Backtest start date (default: 1993-01-01).",
    )
    parser.add_argument(
        "--end", type=str, default=None,
        help="Backtest end date (default: latest available).",
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help="Force re-download of SPY data from yfinance.",
    )
    parser.add_argument(
        "--no-chart", action="store_true",
        help="Skip chart generation.",
    )
    parser.add_argument(
        "--resilience", action="store_true",
        help="Run resilience stress test with random period sampling "
             "across duration buckets (0-5yr, 5-10yr, ... 25-30yr).",
    )
    parser.add_argument(
        "--samples", type=int, default=10,
        help="Number of random periods per bucket in resilience mode (default: 10).",
    )
    args = parser.parse_args()

    runner = TournamentRunner(start_date=args.start, end_date=args.end)
    runner.load_data(force_refresh=args.refresh)

    if args.resilience:
        # Resilience mode — random period stress test
        target_strats = None
        if args.strategy:
            target_names = [s.strip() for s in args.strategy.split(",")]
            all_strats = runner.discover_strategies()
            target_strats = []
            for t in target_names:
                match = next((s for s in all_strats if s.NAME.lower() == t.lower()), None)
                if match: target_strats.append(match)
        
        runner.run_resilience(samples_per_bucket=args.samples, target_strategies=target_strats)
    elif args.strategy:
        # Run specific strategies (comma-separated support)
        target_names = [s.strip() for s in args.strategy.split(",")]
        
        # If multiple strategies, we use run_all logic but filtered
        if len(target_names) > 1:
            all_strats = runner.discover_strategies()
            to_run = []
            for t in target_names:
                match = next((s for s in all_strats if s.NAME.lower() == t.lower()), None)
                if match: to_run.append(match)
            
            # Run the filtered set
            runner.data = runner.data if runner.data is not None else runner.load_data()
            results = {}
            for s in to_run:
                print(f"  Running: {s.NAME}...", end="", flush=True)
                res = runner.run_strategy(s)
                results[s.NAME] = res
                print(f" CAGR: {res['metrics']['cagr']*100:.2f}%")
            runner.results = results
        else:
            # Single strategy (existing logic)
            runner.run_single(target_names[0])
            
        runner.print_results()
        if not args.no_chart:
            runner.generate_chart()
    else:
        runner.run_all()
        runner.print_results()
        if not args.no_chart:
            runner.generate_chart()


if __name__ == "__main__":
    main()
