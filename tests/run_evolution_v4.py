import argparse
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v4 import EvolutionEngineV4

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chameleon V4 — Adaptive Volatility Evolution")
    parser.add_argument("--pop", type=int, default=40, help="Population size")
    parser.add_argument("--gen", type=int, default=15, help="Generations")
    parser.add_argument("--mut", type=float, default=0.20, help="Mutation rate")
    parser.add_argument("--seed", type=str, default="champions/v4_chameleon/vault", help="Path to seed vault")
    args = parser.parse_args()

    engine = EvolutionEngineV4(
        population_size=args.pop, 
        generations=args.gen, 
        mutation_rate=args.mut,
        seed_vault=args.seed
    )
    engine.run()
