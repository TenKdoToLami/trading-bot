import argparse
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v9_confidence import EvolutionEngineV9Confidence

def main():
    parser = argparse.ArgumentParser(description="Run Evolution for V9 Confidence")
    parser.add_argument("--pop", type=int, default=300, help="Population size")
    parser.add_argument("--gen", type=int, default=100, help="Number of generations")
    parser.add_argument("--mut", type=float, default=0.2, help="Mutation rate")
    parser.add_argument("--seed", type=str, default=None, help="Path to seed vault")
    parser.add_argument("--min-cagr", type=float, default=40.0, help="Minimum CAGR threshold for vault saving")
    
    args = parser.parse_args()
    
    engine = EvolutionEngineV9Confidence(
        population_size=args.pop,
        generations=args.gen,
        mutation_rate=args.mut,
        seed_vault=args.seed,
        min_cagr=args.min_cagr
    )
    
    engine.run()

if __name__ == "__main__":
    main()
