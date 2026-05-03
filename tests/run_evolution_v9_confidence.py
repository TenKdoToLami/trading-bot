import os
import sys
import argparse

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v9_confidence import EvolutionEngineV9Confidence

def main():
    parser = argparse.ArgumentParser(description="Institutional Evolution: Model V9 Confidence")
    parser.add_argument("--pop", type=int, default=100, help="Population size")
    parser.add_argument("--gen", type=int, default=50, help="Number of generations")
    parser.add_argument("--mut", type=float, default=0.2, help="Mutation rate")
    parser.add_argument("--vault", type=str, default=None, help="Path to seed vault")
    parser.add_argument("--min-cagr", type=float, default=0.0, help="Minimum CAGR threshold for saving results")
    args = parser.parse_args()

    engine = EvolutionEngineV9Confidence(
        population_size=args.pop,
        generations=args.gen,
        mutation_rate=args.mut,
        seed_vault=args.vault,
        min_cagr=args.min_cagr
    )
    
    try:
        engine.run()
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Evolution halted by user. Best results saved to vault.")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")

if __name__ == "__main__":
    main()
