import os
import sys

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.tournament.runner import TournamentRunner

if __name__ == "__main__":
    runner = TournamentRunner(start_date="1993-01-01")
    runner.load_data()
    
    print("\n" + "="*60)
    print("FLEET AUDIT — TARGET: 20% CAGR")
    print("="*60)
    
    # Discover all
    strats = runner.discover_strategies()
    print(f"Found {len(strats)} strategies.")
    
    results_list = []
    for s in strats:
        # Avoid genetic ones unless they are champions
        if "Genome" in s.__class__.__name__ and "CHAMP" not in getattr(s, "NAME", ""):
            continue
            
        print(f"  Auditing: {s.NAME:35}...", end="", flush=True)
        try:
            # run_single returns the results dict for that strategy
            res_dict = runner.run_single(s.NAME)
            res = res_dict[s.NAME]
            cagr = res['metrics']['cagr'] * 100
            dd = res['metrics']['max_dd'] * 100
            print(f" CAGR: {cagr:6.2f}% | DD: {dd:6.2f}%")
            results_list.append((s.NAME, cagr, dd))
        except Exception as e:
            print(f" FAILED: {e}")

    print("\n" + "="*60)
    print("PRUNING LIST (CAGR < 20%)")
    print("="*60)
    results_list.sort(key=lambda x: x[1], reverse=True)
    for name, cagr, dd in results_list:
        status = "[KEEP]" if cagr >= 20 else "[PRUNE]"
        if "B&H" in name: status = "[SAFE]"
        print(f"{status} {name:40} | CAGR: {cagr:6.2f}%")
