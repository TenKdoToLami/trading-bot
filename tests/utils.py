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
            
        from src.tournament.registry import get_strategy_class
        version = genome.get('version')
        strat_cls = get_strategy_class(version, genome=genome)
        
        if strat_cls:
            return strat_cls(genome=genome)
        
        # Final fallback to V1 if all else fails
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
