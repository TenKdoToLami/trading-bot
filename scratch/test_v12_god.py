import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from src.tournament.runner import TournamentRunner

def test_god_guided_genome():
    print("=== TESTING GOD-GUIDED V12 GENOME ===")
    
    # Initialize runner
    runner = TournamentRunner(start_date="1993-01-01")
    runner.load_data()
    
    # The runner automatically discovers all .json files in champions/
    # But we want to make sure we're testing the one we just made.
    strategies = runner.discover_strategies()
    
    # Filter for our specific genome
    target_name = "[GENE] genome god guided"
    match = next((s for s in strategies if target_name.lower() in s.NAME.lower()), None)
    
    if not match:
        print(f"Error: Could not find strategy for genome_god_guided.json")
        print(f"Found strategies: {[s.NAME for s in strategies]}")
        return

    print(f"Found Target Strategy: {match.NAME}")
    
    # Run the simulation
    results = runner._run_set([match])
    
    if match.NAME in results:
        res = results[match.NAME]
        m = res['metrics']
        
        print("\n" + "="*50)
        print(f" RESULTS: {match.NAME}")
        print("="*50)
        print(f" CAGR:          {m['cagr']*100:.2f}%")
        print(f" Max Drawdown:  {abs(m['max_dd'])*100:.1f}%")
        print(f" Sharpe Ratio:  {m['sharpe']:.2f}")
        print(f" Volatility:    {m['volatility']*100:.1f}%")
        print(f" Total Trades:  {m['num_rebalances']}")
        print(f" Win Rate:      {m.get('win_rate', 0)*100:.1f}%")
        print("="*50)
        
        # Benchmark comparison (if SPY is in the list)
        spy_bh = next((s for s in strategies if "B&H SPY" in s.NAME), None)
        if spy_bh:
            spy_res = runner._run_set([spy_bh])
            spy_m = spy_res[spy_bh.NAME]['metrics']
            print(f"\n VS SPY B&H:")
            print(f" SPY CAGR:      {spy_m['cagr']*100:.2f}%")
            print(f" Alpha:         {(m['cagr'] - spy_m['cagr'])*100:+.2f}%")
            print(f" Outperformance: {(m['cagr'] / spy_m['cagr'] - 1)*100:.1f}%")
    else:
        print("Error: No results returned.")

if __name__ == "__main__":
    test_god_guided_genome()
