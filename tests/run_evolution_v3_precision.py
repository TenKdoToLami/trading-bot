import argparse
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v3_precision import EvolutionEngineV3

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genome V3 — Precision Binary Evolution Engine")
    parser.add_argument("--pop", type=int, default=50, help="Population size")
    parser.add_argument("--gen", type=int, default=20, help="Generations")
    parser.add_argument("--mut", type=float, default=0.15, help="Mutation rate")
    parser.add_argument("--ablation", action="store_true", help="Enable indicator ablation")
    parser.add_argument("--seed", type=str, default=None, help="Directory to load seed genomes from")
    parser.add_argument("--min-cagr", type=float, default=0.0, help="Minimum CAGR % to save to vault")
    
    args = parser.parse_args()

    engine = EvolutionEngineV3(
        population_size=args.pop, 
        generations=args.gen, 
        mutation_rate=args.mut,
        use_ablation=args.ablation,
        seed_vault=args.seed,
        min_cagr=args.min_cagr
    )
    engine.run()
