"""
Champion V3 — The best Precision Binary strategy found by the V3 Evolution Engine.
Automatically loads the sibling 'genome.json'.
"""

import json
import os
from strategies.genome_v3_strategy import GenomeV3Strategy

class ChampionV3(GenomeV3Strategy):
    NAME = "Champion V3 (AI Precision)"

    def __init__(self, **kwargs):
        # We prefer the passed genome if provided, otherwise load from file
        genome = kwargs.get('genome')
        if not genome:
            genome_path = os.path.join(os.path.dirname(__file__), "genome.json")
            if os.path.exists(genome_path):
                with open(genome_path, "r") as f:
                    genome = json.load(f)
        
        super().__init__(genome=genome)
