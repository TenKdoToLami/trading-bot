import os
import sys
import json

# Add src to path
sys.path.append(os.getcwd())

from src.tournament.evolution_v13_lite import EvolutionEngineV13Lite

def train_v13_lite_dual_brain():
    print("=== V13 DUAL-BRAIN LITE TRAINING ===")
    
    # Phase 1: Train the Sentinel (Regime identification)
    # This phase focuses on matching the God-Mode path.
    print("\n[PHASE 1] Training the Sentinel (Regime Brain)...")
    engine_sent = EvolutionEngineV13Lite(
        target='sentinel',
        population_size=100,
        generations=50
    )
    best_sentinel_genome = engine_sent.run()
    
    # Phase 2: Train the Pilot (Allocation logic)
    # This phase freezes the Sentinel and optimizes the 1x/2x/3x split.
    print("\n[PHASE 2] Training the Pilot (Allocation Brain)...")
    engine_pilot = EvolutionEngineV13Lite(
        target='pilot',
        population_size=100,
        generations=50
    )
    # Inject the best sentinel from Phase 1
    engine_pilot.population[0] = best_sentinel_genome
    final_genome = engine_pilot.run()
    
    # Save final champion
    output_path = "champions/v13_lite/genome.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(final_genome, f, indent=4)
    
    print(f"\n[SUCCESS] V13 Dual-Brain Lite training complete!")
    print(f"Final genome saved to: {output_path}")

if __name__ == "__main__":
    train_v13_lite_dual_brain()
