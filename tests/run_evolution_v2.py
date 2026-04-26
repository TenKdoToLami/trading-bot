import argparse
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v2 import EvolutionEngineV2

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genome V2 — Multi-Brain Evolution Engine")
    parser.add_argument("--pop", type=int, default=50, help="Population size")
    parser.add_argument("--gen", type=int, default=20, help="Generations")
    parser.add_argument("--mut", type=float, default=0.15, help="Mutation rate")
    parser.add_argument("--no-ablation", action="store_true", help="Disable indicator ablation (force all active)")
    parser.add_argument("--seed", type=str, default=None, help="Directory to load seed genomes from")
    parser.add_argument("--push-mid", action="store_true", help="Reward residency in 1x and 2x tiers")
    args = parser.parse_args()

    engine = EvolutionEngineV2(
        population_size=args.pop, 
        generations=args.gen, 
        mutation_rate=args.mut,
        use_ablation=not args.no_ablation,
        seed_vault=args.seed,
        push_mid_tiers=args.push_mid
    )
    engine.run()
