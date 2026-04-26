"""
Tournament CLI — single entry point for running strategy backtests.

Usage:
    # Run all discovered strategies
    python tests/run_tournament.py

    # Run a single strategy
    python tests/run_tournament.py --strategy "BEAST (SMA + RealVol)"

    # Custom date range
    python tests/run_tournament.py --start 2008-01-01 --end 2012-12-31

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
    args = parser.parse_args()

    runner = TournamentRunner(start_date=args.start, end_date=args.end)
    runner.load_data(force_refresh=args.refresh)

    if args.strategy:
        runner.run_single(args.strategy)
    else:
        runner.run_all()

    runner.print_results()

    if not args.no_chart:
        runner.generate_chart()


if __name__ == "__main__":
    main()
