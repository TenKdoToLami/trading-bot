"""
Head-to-Head Resilience Showdown: V1 vs V2.
Runs 100+ random historical periods and counts how often each champion wins.
"""

import json
import os
import sys
import random
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from strategies._genome_strategy import GenomeStrategy
from strategies.genome_v2_multi import GenomeV2Strategy
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data

def run_showdown(v1_path, v2_path, num_matches=100):
    # 1. Load Genomes
    with open(v1_path, 'r') as f: v1_genome = json.load(f)
    with open(v2_path, 'r') as f: v2_genome = json.load(f)

    # 2. Load Data
    data = load_spy_data("1993-01-01")
    price_data_list = data[['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve']].to_dict('records')
    dates = data.index
    total_days = len(data)

    # 3. Matches
    v1_wins = 0
    v2_wins = 0
    results = []

    print(f"\n--- 🥊 CHAMPION SHOWDOWN: {num_matches} MATCHES ---")
    print(f"V1: {os.path.basename(v1_path)}")
    print(f"V2: {os.path.basename(v2_path)}\n")

    for i in range(num_matches):
        # Pick a random duration (1 to 10 years)
        duration_yrs = random.uniform(1, 10)
        duration_days = int(duration_yrs * 252)
        
        start_idx = random.randint(0, total_days - duration_days - 1)
        end_idx = start_idx + duration_days
        
        p_slice = price_data_list[start_idx:end_idx]
        d_slice = dates[start_idx:end_idx]

        # Run V1
        res1 = _execute_simulation(GenomeStrategy, p_slice, d_slice, {'genome': v1_genome})
        cagr1 = res1['metrics']['cagr']

        # Run V2
        res2 = _execute_simulation(GenomeV2Strategy, p_slice, d_slice, {'genome': v2_genome})
        cagr2 = res2['metrics']['cagr']

        winner = "V2" if cagr2 > cagr1 else "V1"
        if winner == "V2": v2_wins += 1
        else: v1_wins += 1

        results.append({
            'start': d_slice[0].date(),
            'end': d_slice[-1].date(),
            'v1_cagr': cagr1,
            'v2_cagr': cagr2,
            'winner': winner
        })

        if (i+1) % 10 == 0:
            print(f"  Match {i+1:>3}: V2 Win Rate so far: {v2_wins/(i+1)*100:.1f}%")

    # Final Stats
    df = pd.DataFrame(results)
    
    print("\n" + "="*60)
    print(f"  🏁 FINAL SHOWDOWN RESULTS ({num_matches} Matches)")
    print("="*60)
    print(f"  V2 Win Rate:      {v2_wins/num_matches*100:>10.1f}%")
    print(f"  V1 Win Rate:      {v1_wins/num_matches*100:>10.1f}%")
    print("-" * 60)
    print(f"  V2 Avg CAGR:      {df['v2_cagr'].mean()*100:>10.2f}%")
    print(f"  V1 Avg CAGR:      {df['v1_cagr'].mean()*100:>10.2f}%")
    print("-" * 60)
    print(f"  V2 Median CAGR:   {df['v2_cagr'].median()*100:>10.2f}%")
    print(f"  V1 Median CAGR:   {df['v1_cagr'].median()*100:>10.2f}%")
    print("="*60 + "\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Head-to-Head Resilience Showdown: V1 vs V2")
    parser.add_argument("v1", type=str, help="Path to V1 genome JSON")
    parser.add_argument("v2", type=str, help="Path to V2 genome JSON")
    parser.add_argument("--matches", type=int, default=100, help="Number of matches (default: 100)")
    args = parser.parse_args()

    # Resolve paths relative to root
    v1_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', args.v1))
    v2_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', args.v2))
    
    if not os.path.exists(v1_path):
        print(f"ERROR: V1 file not found: {v1_path}")
        sys.exit(1)
    if not os.path.exists(v2_path):
        print(f"ERROR: V2 file not found: {v2_path}")
        sys.exit(1)

    run_showdown(v1_path, v2_path, args.matches)

