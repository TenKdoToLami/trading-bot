"""
Champion V2 — The best Multi-Brain strategy found by the V2 Evolution Engine.
Automatically loads 'best_genome_v2.json'.
"""

import json
import os
from strategies.genome_v2_strategy import GenomeV2Strategy

class ChampionV2(GenomeV2Strategy):
    NAME = "Champion V2 (AI Multi-Brain)"

    def __init__(self, **kwargs):
        # We prefer the passed genome if provided, otherwise load from file
        genome = kwargs.get('genome')
        if not genome:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            genome_path = os.path.join(project_root, "best_genome_v2.json")
            
            if os.path.exists(genome_path):
                with open(genome_path, "r") as f:
                    genome = json.load(f)
        
        super().__init__(genome=genome)
