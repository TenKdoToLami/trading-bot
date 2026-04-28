import json
import os
from strategies.genome_v4_precision import GenomeV4Precision

class ChampionV4Precision(GenomeV4Precision):
    """
    Standard wrapper for the best-performing V4 Precision genome.
    """
    NAME = "V4 | AI Precision"

    def __init__(self, genome=None):
        # We prefer the passed genome if provided, otherwise load from file
        if genome is None:
            genome_path = os.path.join(os.path.dirname(__file__), "genome.json")
            if os.path.exists(genome_path):
                with open(genome_path, "r") as f:
                    genome = json.load(f)
                    
        super().__init__(genome=genome)
