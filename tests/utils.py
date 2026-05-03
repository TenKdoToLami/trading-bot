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
            
        # --- PRIORITY 0: Explicit Version Strings ---
        v_str = str(genome.get('version', ''))
        
        if v_str == "v10_expert":
            from strategies.genome_v10_expert import GenomeV10Expert
            return GenomeV10Expert(genome=genome)
        elif v_str == "v9_confidence":
            from strategies.genome_v9_confidence import GenomeV9Confidence
            return GenomeV9Confidence(genome=genome)
        elif v_str == "v7_deep":
            from strategies.genome_v7_deep import GenomeV7Deep
            return GenomeV7Deep(genome=genome)
        elif v_str == "v7_deep_binary":
            from strategies.genome_v7_deep_binary import GenomeV7DeepBinary
            return GenomeV7DeepBinary(genome=genome)
        elif v_str == "v7_deep_fluid":
            from strategies.genome_v7_deep_fluid import GenomeV7DeepFluid
            return GenomeV7DeepFluid(genome=genome)
        elif v_str == "v6_balancer":
            from strategies.genome_v6_balancer import GenomeV6
            return GenomeV6(genome=genome)
        elif v_str == "v5_sniper":
            from strategies.genome_v5_sniper import GenomeV5Sniper
            return GenomeV5Sniper(genome=genome)
        elif v_str == "v4_precision":
            from strategies.genome_v4_precision import GenomeV4Precision
            return GenomeV4Precision(genome=genome)
        elif v_str == "v3_precision":
            from strategies.genome_v3_precision import GenomeV3Strategy
            return GenomeV3Strategy(genome=genome)
        elif v_str == "v2_multi":
            from strategies.genome_v2_multi import GenomeV2Strategy
            return GenomeV2Strategy(genome=genome)
        elif v_str == "v1_manual":
            from strategies.genome_v1_manual import ManualV1
            return ManualV1(genome=genome)
        elif v_str == "v1_classic":
            from strategies.genome_v1_classic import GenomeV1
            return GenomeV1(genome=genome)

        # --- PRIORITY 1: Structural Fallbacks (Legacy/Numeric) ---
        if v_str == "9.0" or "hysteresis" in genome:
            from strategies.genome_v9_confidence import GenomeV9Confidence
            return GenomeV9Confidence(genome=genome)
            
        elif "layers" in genome or v_str in ["7.0", "7.1", "7.2"]:
            from strategies.genome_v7_deep import GenomeV7Deep
            from strategies.genome_v7_deep_binary import GenomeV7DeepBinary
            from strategies.genome_v7_deep_fluid import GenomeV7DeepFluid
            
            try: v = float(v_str) if v_str else 7.0
            except: v = 7.0
            
            if v == 7.2: return GenomeV7DeepFluid(genome=genome)
            if v == 7.1: return GenomeV7DeepBinary(genome=genome)
            return GenomeV7Deep(genome=genome)
            
        elif ("brains" in genome and ("cash" in genome["brains"] or "1x" in genome["brains"])) or v_str == "6.0":
            from strategies.genome_v6_balancer import GenomeV6
            return GenomeV6(genome=genome)
            
        elif "sniper" in genome or v_str == "5.0":
            from strategies.genome_v5_sniper import GenomeV5Sniper
            return GenomeV5Sniper(genome=genome)
            
        elif "panic" in genome and "bull" in genome:
            if v_str == "4.0" or "v4_precision" in identifier.lower():
                from strategies.genome_v4_precision import GenomeV4Precision
                return GenomeV4Precision(genome=genome)
            else:
                from strategies.genome_v3_precision import GenomeV3Strategy
                return GenomeV3Strategy(genome=genome)
                
        elif "panic" in genome and "3x" in genome:
            from strategies.genome_v2_multi import GenomeV2Strategy
            return GenomeV2Strategy(genome=genome)
            
        elif "panic_weights" in genome:
            from strategies.genome_v1_classic import GenomeV1
            return GenomeV1(genome=genome)
            
        elif "bounds_p" in genome and "weights_p" in genome:
            from strategies.genome_v1_manual import ManualV1
            return ManualV1(genome=genome)
            
        else:
            from strategies.genome_v1_classic import GenomeV1
            return GenomeV1(genome=genome)

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
