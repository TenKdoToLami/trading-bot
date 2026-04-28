import argparse
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v4_precision import EvolutionEngineV4Precision

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genome V4 Precision — 3-State AI Evolution")
    parser.add_argument("--pop", type=int, default=100, help="Population size")
    parser.add_argument("--gen", type=int, default=50, help="Generations")
    parser.add_argument("--mutation", type=float, default=0.2, help="Mutation rate")
    parser.add_argument("--ablation", action="store_true", help="Enable indicator ablation")
    parser.add_argument("--seed", type=str, default=None, help="Seed vault path")
    
    args = parser.parse_args()

    engine = EvolutionEngineV4Precision(
        population_size=args.pop, 
        generations=args.gen, 
        mutation_rate=args.mutation,
        use_ablation=args.ablation,
        seed_vault=args.seed
    )
    engine.run()
