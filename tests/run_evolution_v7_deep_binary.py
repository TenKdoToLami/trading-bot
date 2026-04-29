import argparse
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v7_deep_binary import EvolutionEngineV7DeepBinary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genome V7 — Deep Binary Evolution Engine")
    parser.add_argument("--pop", type=int, default=100, help="Population size")
    parser.add_argument("--gen", type=int, default=50, help="Generations")
    parser.add_argument("--mut", type=float, default=0.20, help="Mutation rate")
    parser.add_argument("--seed", type=str, default=None, help="Directory to load seed genomes from")
    parser.add_argument("--min-cagr", type=float, default=0.30, help="Minimum CAGR to save to vault")
    
    args = parser.parse_args()

    engine = EvolutionEngineV7DeepBinary(
        population_size=args.pop, 
        generations=args.gen, 
        mutation_rate=args.mut,
        seed_vault=args.seed,
        min_cagr=args.min_cagr
    )
    engine.run()
