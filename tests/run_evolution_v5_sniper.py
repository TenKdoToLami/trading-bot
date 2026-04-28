import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v5_sniper import EvolutionEngineV5Sniper

def main():
    parser = argparse.ArgumentParser(description="Evolve Genome V5 Sniper (Baseline 1x -> Snipe 3x)")
    parser.add_argument("--pop", type=int, default=50, help="Population size")
    parser.add_argument("--gen", type=int, default=20, help="Generations")
    parser.add_argument("--mut", type=float, default=0.2, help="Mutation rate")
    parser.add_argument("--seed", type=str, default=None, help="Seed vault path")
    
    args = parser.parse_args()

    engine = EvolutionEngineV5Sniper(
        population_size=args.pop,
        generations=args.gen,
        mutation_rate=args.mut,
        seed_vault=args.seed
    )
    
    engine.run()

if __name__ == "__main__":
    main()
