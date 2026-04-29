import argparse
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v1_classic import EvolutionEngineV1Classic

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="V1 Classic — Genetic Algorithm evolution.")
    parser.add_argument("--pop", type=int, default=30, help="Population size")
    parser.add_argument("--gen", type=int, default=10, help="Number of generations")
    parser.add_argument("--mut", type=float, default=0.15, help="Mutation rate")
    parser.add_argument("--seed", type=str, default=None, help="Path to vault dir to seed population")
    parser.add_argument("--ablation", action="store_true", help="Enable feature ablation (dropping indicators)")
    args = parser.parse_args()

    engine = EvolutionEngineV1Classic(
        population_size=args.pop, 
        generations=args.gen, 
        mutation_rate=args.mut,
        seed_vault=args.seed,
        use_ablation=args.ablation
    )
    engine.run()
