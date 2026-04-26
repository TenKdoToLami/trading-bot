import argparse
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution import EvolutionEngine

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Genetic Algorithm to breed trading strategies.")
    parser.add_argument("--pop", type=int, default=30, help="Population size (default 30)")
    parser.add_argument("--gen", type=int, default=10, help="Number of generations (default 10)")
    parser.add_argument("--mut", type=float, default=0.15, help="Mutation rate (default 0.15)")
    parser.add_argument("--seed", type=str, default=None, help="Path to vault dir to seed population with top performers")
    args = parser.parse_args()

    engine = EvolutionEngine(
        population_size=args.pop, 
        generations=args.gen, 
        mutation_rate=args.mut,
        seed_vault=args.seed
    )
    engine.run()
