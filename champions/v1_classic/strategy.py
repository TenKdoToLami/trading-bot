"""
Champion V1 — The best strategy found by the Evolution Engine.
Automatically loads the sibling 'genome.json'.
"""

import json
import os
from strategies._genome_strategy import GenomeStrategy

class ChampionV1(GenomeStrategy):
    NAME = "Champion V1 (AI Classic)"

    def __init__(self, **kwargs):
        # We prefer the passed genome if provided, otherwise load from file
        genome = kwargs.get('genome')
        if not genome:
            genome_path = os.path.join(os.path.dirname(__file__), "genome.json")
            if os.path.exists(genome_path):
                with open(genome_path, "r") as f:
                    genome = json.load(f)
        
        super().__init__(genome=genome)
