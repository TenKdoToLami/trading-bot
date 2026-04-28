"""
Champion V4 Precision — The best 3-State AI strategy found by the V4 Precision Evolution Engine.
Automatically loads the sibling 'genome.json'.
"""

import json
import os
from strategies.genome_v4_precision import GenomeV4Precision

class ChampionV4Precision(GenomeV4Precision):
    NAME = "Champion V4 (AI Precision)"

    def __init__(self, **kwargs):
        # We prefer the passed genome if provided, otherwise load from file
        genome = kwargs.get('genome')
        if not genome:
            genome_path = os.path.join(os.path.dirname(__file__), "genome.json")
            if os.path.exists(genome_path):
                with open(genome_path, "r") as f:
                    try:
                        genome = json.load(f)
                    except:
                        genome = None
        
        super().__init__(genome=genome)
