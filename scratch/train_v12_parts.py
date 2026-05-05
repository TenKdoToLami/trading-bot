import os
import json
import sys

# Add src to path
sys.path.append(os.getcwd())

from src.tournament.evolution_v12_phased import EvolutionEngineV12Phased

def run_god_guided_training():
    print("=== V12 SUPERVISED GOD-GUIDED TRAINING ===")
    
    # Phase 1: Bull Brain Optimization
    # Rewards 3x leverage usage during bull markets.
    print("\n[PHASE 1] Optimizing Bull Brain (Expert Leverage)...")
    engine_bull = EvolutionEngineV12Phased(
        target_brain='bull', 
        regime_filter='god_bullish',
        population_size=100,
        generations=40
    )
    best_bull_genome = engine_bull.run()
    
    # Phase 2: Bear Brain Optimization
    # Rewards tactical defense (Gold/TLT/Shorts) during crashes.
    print("\n[PHASE 2] Optimizing Bear Brain (Tactical Defense)...")
    engine_bear = EvolutionEngineV12Phased(
        target_brain='bear',
        regime_filter='god_bearish',
        population_size=100,
        generations=40
    )
    engine_bear.population[0] = best_bull_genome 
    best_bear_genome = engine_bear.run()
    
    # Phase 3: Regime Harmonization (Supervised)
    # Massively rewards matching the God's decisions and punishes jitter.
    print("\n[PHASE 3] Harmonizing Regime Brain (Supervised Mapping)...")
    engine_regime = EvolutionEngineV12Phased(
        target_brain='regime',
        regime_filter='none',
        population_size=150,
        generations=100 # Long run for supervised convergence
    )
    engine_regime.population[0] = best_bear_genome
    final_genome = engine_regime.run()
    
    # Save final champion
    output_path = "champions/v12_moe/genome_god_guided.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(final_genome, f, indent=4)
    
    print(f"\n[SUCCESS] Supervised God-Guided training complete!")
    print(f"Final genome saved to: {output_path}")

if __name__ == "__main__":
    run_god_guided_training()
