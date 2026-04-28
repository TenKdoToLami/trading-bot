import argparse
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v5_sniper import EvolutionEngineV5Sniper

def main():
    parser = argparse.ArgumentParser(description="Run Genetic Evolution for Tiered Sniper V5")
    parser.add_argument("--pop", type=int, default=50, help="Population size")
    parser.add_argument("--gen", type=int, default=20, help="Number of generations")
    parser.add_argument("--mutation", type=float, default=0.2, help="Mutation rate")
    parser.add_argument("--seed", type=str, default=None, help="Path to seed vault")
    
    args = parser.parse_args()
    
    engine = EvolutionEngineV5Sniper(
        population_size=args.pop,
        generations=args.gen,
        mutation_rate=args.mutation,
        seed_vault=args.seed
    )
    
    engine.run()

if __name__ == "__main__":
    main()
