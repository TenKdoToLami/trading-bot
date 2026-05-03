"""
Universal Evolution Runner — Single entry point for all evolution versions.
Usage: python tests/run_evolution_universal.py --version v6_balancer --pop 100 --gen 50
"""

import argparse
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tournament.evolution_registry import get_evolution_engine, get_all_evo_versions

def main():
    parser = argparse.ArgumentParser(description="Universal Strategy Evolution Engine")
    parser.add_argument("--version", type=str, required=True, help=f"Evo version to run: {get_all_evo_versions()}")
    parser.add_argument("--pop", type=int, default=100, help="Population size")
    parser.add_argument("--gen", type=int, default=50, help="Number of generations")
    parser.add_argument("--mut", type=float, default=0.2, help="Mutation rate")
    parser.add_argument("--vault", type=str, default=None, help="Vault directory for seeding")
    parser.add_argument("--ablation", action="store_true", help="Enable ablation study during evolution")
    parser.add_argument("--cagr", type=float, default=0.0, help="Minimum CAGR filter")
    parser.add_argument("--workers", type=int, default=max(1, os.cpu_count() - 2), help="Number of worker processes")
    
    args = parser.parse_args()
    
    engine_cls = get_evolution_engine(args.version)
    if not engine_cls:
        print(f"Error: Evolution engine '{args.version}' not found.")
        print(f"Available versions: {get_all_evo_versions()}")
        sys.exit(1)
        
    print(f"Starting {args.version} Evolution...")
    print(f"Settings: pop={args.pop}, gen={args.gen}, mut={args.mut}, vault={args.vault}, workers={args.workers}")
    
    # Initialize engine
    # We pass args as a dict to the engine, adapting to its expected signature
    engine = engine_cls(
        population_size=args.pop,
        generations=args.gen,
        mutation_rate=args.mut,
        seed_vault=args.vault,
        use_ablation=args.ablation,
        min_cagr=args.cagr,
        workers=args.workers
    )
    
    try:
        engine.run()
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Evolution stopped by user.")
    except Exception as e:
        print(f"\n[ERROR] Evolution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
