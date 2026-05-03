import os
import sys
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v5_sniper import EvolutionEngineV5Sniper

def main():
    parser = argparse.ArgumentParser(description='Unified Evolution Runner: V5 Sniper')
    parser.add_argument('--pop', type=int, default=100, help='Population size')
    parser.add_argument('--gen', type=int, default=50, help='Number of generations')
    parser.add_argument('--mut', type=float, default=0.2, help='Mutation rate')
    parser.add_argument('--vault', type=str, default=None, help='Seed vault path')
    parser.add_argument('--min-cagr', type=float, default=0.0, help='Minimum CAGR threshold for saving results')
    parser.add_argument('--no-ablation', action='store_false', dest='use_ablation', default=True, help='Disable indicator ablation')
    args = parser.parse_args()

    engine = EvolutionEngineV5Sniper(
        population_size=args.pop, 
        generations=args.gen, 
        mutation_rate=args.mut, 
        seed_vault=args.vault,
        min_cagr=args.min_cagr,
        use_ablation=args.use_ablation
    )
    
    try:
        engine.run()
    except KeyboardInterrupt:
        print('\n[INTERRUPTED]')

if __name__ == '__main__':
    main()
