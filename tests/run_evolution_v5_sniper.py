import os
import sys
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_v5_sniper import EvolutionEngineV5Sniper

def main():
    parser = argparse.ArgumentParser(description='Unified Evolution Runner')
    parser.add_argument('--pop', type=int, default=100)
    parser.add_argument('--gen', type=int, default=50)
    parser.add_argument('--mut', type=float, default=0.2)
    parser.add_argument('--vault', type=str, default='champions/v5_sniper/vault')
    args = parser.parse_args()

    engine = EvolutionEngineV5Sniper(population_size=args.pop, generations=args.gen, mutation_rate=args.mut, seed_vault=args.vault)
    try: engine.run()
    except KeyboardInterrupt: print('\n[INTERRUPTED]')

if __name__ == '__main__': main()
