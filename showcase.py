"""
Showcase Generator — one-command entry point for the visualizer dashboard.

Reuses the existing TournamentRunner pipeline to ensure the visualizer
receives data in the exact format it expects (metrics as fractions,
all computed fields like signal traces, rolling vol, etc.).

Usage:
    # Full run: backtest all champions, generate data, start dev server
    ./venv/bin/python3 showcase.py

    # Generate data only (no dev server)
    ./venv/bin/python3 showcase.py --no-server

    # Include robustness & synthetic audits (slower, ~10min)
    ./venv/bin/python3 showcase.py --audit

    # Skip server, skip audits (fastest — data only)
    ./venv/bin/python3 showcase.py --no-server
"""

import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
VIS_DIR = os.path.join(ROOT, "visualizer")

sys.path.insert(0, ROOT)
from src.tournament.runner import TournamentRunner


def main():
    parser = argparse.ArgumentParser(
        description="Showcase Generator — backtest champions and launch the dashboard."
    )
    parser.add_argument(
        "--no-server", action="store_true",
        help="Skip starting the Vite dev server after data generation.",
    )
    parser.add_argument(
        "--audit", action="store_true",
        help="Include robustness & synthetic audits (slower, ~10min).",
    )
    parser.add_argument(
        "--start", type=str, default="1993-01-01",
        help="Backtest start date (default: 1993-01-01).",
    )
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  🏆 TACTICAL BOT SHOWCASE GENERATOR")
    print("=" * 70)

    # 1. Run the existing tournament pipeline
    runner = TournamentRunner(start_date=args.start)
    runner.load_data()
    runner.run_all()
    runner.print_results()

    # 2. Generate report + export to visualizer/public/data.json
    #    This calls dashboard_exporter.export_to_dashboard() internally,
    #    which computes monthly/yearly returns, rolling vol, signal traces,
    #    alpha/beta, and all other derived fields the visualizer needs.
    skip_audits = not args.audit
    runner.generate_report(skip_audits=skip_audits)

    print("\n✅ Dashboard data ready in visualizer/public/data.json")

    # 3. Optionally start the dev server
    if not args.no_server:
        start_server()


def start_server():
    """Start the Vite dev server for the visualizer."""
    print("\n🌐 Starting Visualizer Server...")
    try:
        if not os.path.exists(os.path.join(VIS_DIR, "node_modules")):
            print("📦 Installing dependencies...")
            subprocess.run(["npm", "install"], cwd=VIS_DIR, check=True)

        subprocess.run(["npm", "run", "dev"], cwd=VIS_DIR)
    except KeyboardInterrupt:
        print("\n👋 Showcase closed.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed: {e}")


if __name__ == "__main__":
    main()
