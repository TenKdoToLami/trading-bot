import argparse
import os
from src.tournament.evolution_v10_expert import EvolutionV10Expert

def main():
    parser = argparse.ArgumentParser(description="Evolve Model V10 Expert Ensemble")
    parser.add_argument("--data", default="data/history_SPY.csv", help="Path to market data CSV")
    parser.add_argument("--profile", default="champions/v10_alpha/indicator_profiles.json", help="Path to indicator profiles")
    parser.add_argument("--pop", type=int, default=50, help="Population size")
    parser.add_argument("--gen", type=int, default=20, help="Number of generations")
    parser.add_argument("--mut", type=float, default=0.2, help="Mutation rate")
    parser.add_argument("--vault", default="champions/v10_alpha/vault", help="Directory to save champions")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.profile):
        print(f"Error: Profile not found at {args.profile}")
        print("Please run the profiler first!")
        return

    print(f"--- Model V10 Evolution Start ---")
    print(f"Data: {args.data}")
    print(f"Profile: {args.profile}")
    print(f"Population: {args.pop} | Generations: {args.gen}")
    print("--------------------------------")

    engine = EvolutionV10Expert(
        data_path=args.data,
        profile_path=args.profile,
        population_size=args.pop,
        generations=args.gen,
        mutation_rate=args.mut
    )
    
    engine.run(vault_path=args.vault)

if __name__ == "__main__":
    main()
