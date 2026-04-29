import argparse
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v5_sniper import EvolutionEngineV5Sniper

def main():
    parser = argparse.ArgumentParser(description="Run Genetic Evolution for V5 Sniper")
    parser.add_argument("--pop", type=int, default=300, help="Population size")
    parser.add_argument("--gen", type=int, default=100, help="Number of generations")
    parser.add_argument("--mut", type=float, default=0.2, help="Mutation rate")
    parser.add_argument("--seed", type=str, default=None, help="Path to seed vault")
    parser.add_argument("--ablation", action="store_true", help="Enable indicator ablation")
    parser.add_argument("--min-cagr", type=float, default=30.0, help="Minimum CAGR threshold for vault saving")
    
    args = parser.parse_args()
    
    engine = EvolutionEngineV5Sniper(
        population_size=args.pop,
        generations=args.gen,
        mutation_rate=args.mut,
        seed_vault=args.seed,
        use_ablation=args.ablation,
        min_cagr=args.min_cagr
    )
    
    engine.run()

if __name__ == "__main__":
    main()
