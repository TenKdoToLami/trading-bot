import json
import os
from strategies.genome_v5_sniper import GenomeV5Sniper

class ChampionV5Sniper(GenomeV5Sniper):
    """
    Standard wrapper for the best-performing V5 Sniper genome.
    Loads from champions/v5_sniper/genome.json.
    """
    def __init__(self, genome=None):
        # We prefer the passed genome if provided, otherwise load from file
        if genome is None:
            genome_path = os.path.join(os.path.dirname(__file__), "genome.json")
            if os.path.exists(genome_path):
                with open(genome_path, "r") as f:
                    genome = json.load(f)
                    
        super().__init__(genome=genome)
        self.NAME = "V5 | Tiered Sniper"
