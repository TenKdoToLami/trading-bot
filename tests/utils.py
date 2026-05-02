import json
import os
import sys
from strategies.base import BaseStrategy
from src.tournament.runner import TournamentRunner

def resolve_strategy(identifier: str) -> BaseStrategy:
    """
    Resolves an identifier (file path to JSON or Strategy Name) to a strategy instance.
    """
    # 1. Check if it's a JSON file
    if identifier.lower().endswith(".json"):
        if not os.path.exists(identifier):
            # Try relative to project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            identifier = os.path.join(project_root, identifier)
        
        if not os.path.exists(identifier):
            raise FileNotFoundError(f"Genome file not found: {identifier}")
            
        with open(identifier, "r") as f:
            genome = json.load(f)
            
        # --- PRIORITY 1: Modern Champions (V10, V9, V7, V6, V5) ---
        if "brain_a" in genome and "brain_b" in genome:
            from strategies.genome_v10_expert import GenomeV10Expert
            return GenomeV10Expert(genome=genome)
            
        elif genome.get('version') == 9.0 or "hysteresis" in genome or "smoothing" in genome:
            from strategies.genome_v9_confidence import GenomeV9Confidence
            return GenomeV9Confidence(genome=genome)
            
        elif "layers" in genome or genome.get('version') in [7.0, 7.1, 7.2]:
            from strategies.genome_v7_deep import GenomeV7Deep
            from strategies.genome_v7_deep_binary import GenomeV7DeepBinary
            from strategies.genome_v7_deep_fluid import GenomeV7DeepFluid
            
            v = genome.get('version', 7.0)
            if v == 7.2: return GenomeV7DeepFluid(genome=genome)
            if v == 7.1: return GenomeV7DeepBinary(genome=genome)
            return GenomeV7Deep(genome=genome)
            
        elif "brains" in genome and ("cash" in genome["brains"] or "1x" in genome["brains"]) or genome.get('version') == 6.0:
            from strategies.genome_v6_balancer import GenomeV6
            return GenomeV6(genome=genome)
            
        elif "sniper" in genome or genome.get('version') == 5.0:
            from strategies.genome_v5_sniper import GenomeV5Sniper
            return GenomeV5Sniper(genome=genome)
            
        # --- PRIORITY 2: Elite Versions (V4, V3) ---
        elif "vix_ema" in genome and "vol_stretch" in genome:
            from strategies.genome_v4_chameleon import ChameleonV4
            return ChameleonV4(genome=genome)
        
        elif "panic" in genome and "bull" in genome:
            # Distinguish V3 (Binary) from V4 (3-State)
            if genome.get('version') == 4.0 or "v4_precision" in identifier.lower():
                from strategies.genome_v4_precision import GenomeV4Precision
                return GenomeV4Precision(genome=genome)
            else:
                from strategies.genome_v3_precision import GenomeV3Strategy
                return GenomeV3Strategy(genome=genome)
                
        # --- PRIORITY 3: Legacy Versions (V2, V1) ---
        elif "panic" in genome and "3x" in genome:
            from strategies.genome_v2_multi import GenomeV2Strategy
            return GenomeV2Strategy(genome=genome)
            
        elif "panic_weights" in genome:
            from strategies._genome_strategy import GenomeStrategy
            return GenomeStrategy(genome=genome)
            
        else:
            # Final fallback
            from strategies._genome_strategy import GenomeStrategy
            return GenomeStrategy(genome=genome)

    # 2. Treat as strategy name
    runner = TournamentRunner()
    discovered = runner.discover_strategies()
    for strat in discovered:
        if strat.NAME == identifier or strat.__class__.__name__ == identifier:
            return strat
            
    # Try case-insensitive name match
    for strat in discovered:
        if strat.NAME.lower() == identifier.lower():
            return strat

    raise ValueError(f"Could not resolve strategy identifier: {identifier}. Try a .json path or a valid strategy name.")
