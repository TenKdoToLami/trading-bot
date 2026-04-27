"""
Champion V4 — The best Chameleon strategy found by the Evolution Engine.
Automatically loads the sibling 'genome.json'.
"""
import json
import os
from strategies.gene_v4_chameleon import ChameleonV4

class ChampionV4(ChameleonV4):
    NAME = "Champion V4 (AI Chameleon)"

    def __init__(self, **kwargs):
        # We prefer the passed genome if provided, otherwise load from file
        genome = kwargs.get('genome')
        if not genome:
            genome_path = os.path.join(os.path.dirname(__file__), "genome.json")
            if os.path.exists(genome_path):
                with open(genome_path, "r") as f:
                    genome = json.load(f)
        
        super().__init__(genome=genome)
