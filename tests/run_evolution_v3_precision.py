import os
import sys
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v3_precision import EvolutionEngineV3

def main():
    parser = argparse.ArgumentParser(description='Unified Evolution Runner: V3 Precision')
    parser.add_argument('--pop', type=int, default=100, help='Population size')
    parser.add_argument('--gen', type=int, default=50, help='Number of generations')
    parser.add_argument('--mut', type=float, default=0.2, help='Mutation rate')
    parser.add_argument('--vault', type=str, default=None, help='Seed vault path')
    parser.add_argument('--min-cagr', type=float, default=0.0, help='Minimum CAGR threshold for saving results')
    parser.add_argument('--ablation', action='store_true', help='Enable indicator ablation (GA can disable indicators)')
    args = parser.parse_args()

    engine = EvolutionEngineV3(
        population_size=args.pop, 
        generations=args.gen, 
        mutation_rate=args.mut, 
        seed_vault=args.vault,
        min_cagr=args.min_cagr,
        use_ablation=args.ablation
    )
    
    try:
        engine.run()
    except KeyboardInterrupt:
        print('\n[INTERRUPTED]')

if __name__ == '__main__':
    main()
