import argparse
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v2 import EvolutionEngineV2

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genome V2 — Multi-Brain Evolution Engine")
    parser.add_argument("--pop", type=int, default=30, help="Population size (default 30)")
    parser.add_argument("--gen", type=int, default=10, help="Number of generations (default 10)")
    parser.add_argument("--mut", type=float, default=0.15, help="Mutation rate (default 0.15)")
    args = parser.parse_args()

    engine = EvolutionEngineV2(
        population_size=args.pop, 
        generations=args.gen, 
        mutation_rate=args.mut
    )
    engine.run()
