import argparse
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v6_balancer import EvolutionEngineV6

def main():
    parser = argparse.ArgumentParser(description="Run Genetic Evolution for Balancer V6")
    parser.add_argument("--pop", type=int, default=50, help="Population size")
    parser.add_argument("--gen", type=int, default=20, help="Number of generations")
    parser.add_argument("--mutation", type=float, default=0.2, help="Mutation rate")
    parser.add_argument("--seed", type=str, default=None, help="Path to seed vault")
    parser.add_argument("--ablation", action="store_true", help="Enable indicator ablation")
    
    args = parser.parse_args()
    
    engine = EvolutionEngineV6(
        population_size=args.pop,
        generations=args.gen,
        mutation_rate=args.mutation,
        seed_vault=args.seed,
        use_ablation=args.ablation
    )
    
    engine.run()

if __name__ == "__main__":
    main()
