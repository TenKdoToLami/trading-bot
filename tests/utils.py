import json
import os
import sys
from strategies.base import BaseStrategy
from strategies._genome_strategy import GenomeStrategy
from strategies.genome_v2_strategy import GenomeV2Strategy
from strategies.genome_v3_strategy import GenomeV3Strategy
from strategies.genome_v4_precision import GenomeV4Precision
from strategies.gene_v4_chameleon import ChameleonV4
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
            
        # Detect version
        if "bounds_p" in genome or "weights_p" in genome:
            # Legacy Manual or V1 structure
            from champions.v1_manual.strategy import ManualV1
            return ManualV1(genome=genome)
        elif "vix_ema" in genome and "vol_stretch" in genome:
            return ChameleonV4(genome=genome)
        elif "panic" in genome and "bull" in genome and "lookbacks" in genome['panic']:
            # Distinguish V3 (Binary) from V4 (3-State)
            if genome.get('version') == 4.0 or "v4_precision" in identifier.lower():
                return GenomeV4Precision(genome=genome)
            else:
                return GenomeV3Strategy(genome=genome)
        elif "panic" in genome and "3x" in genome:
            return GenomeV2Strategy(genome=genome)
        else:
            # Fallback to V1
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
