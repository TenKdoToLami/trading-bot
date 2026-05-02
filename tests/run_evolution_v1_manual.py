import os
import sys
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v1_manual import EvolutionEngineV1Manual

def main():
    parser = argparse.ArgumentParser(description='Unified Evolution Runner: V1 Manual')
    parser.add_argument('--pop', type=int, default=100, help='Population size')
    parser.add_argument('--gen', type=int, default=50, help='Number of generations')
    parser.add_argument('--mut', type=float, default=0.2, help='Mutation rate')
    parser.add_argument('--vault', type=str, default='champions/v1_manual/vault', help='Seed vault path')
    args = parser.parse_args()

    engine = EvolutionEngineV1Manual(
        population_size=args.pop, 
        generations=args.gen, 
        mutation_rate=args.mut, 
        seed_vault=args.vault
    )
    
    try:
        engine.run()
    except KeyboardInterrupt:
        print('\n[INTERRUPTED]')

if __name__ == '__main__':
    main()
