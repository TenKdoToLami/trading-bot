import json
import os
from strategies.v5_sniper.genome import GenomeV5Sniper

class ChampionV5Sniper(GenomeV5Sniper):
    """
    Standard wrapper for the best-performing V5 Sniper genome.
    Loads from champions/v5_sniper/genome.json.
    """
    def __init__(self):
        genome_path = os.path.join(os.path.dirname(__file__), "genome.json")
        if os.path.exists(genome_path):
            with open(genome_path, "r") as f:
                genome = json.load(f)
        else:
            genome = None
            
        super().__init__(genome=genome)
        self.NAME = "V5 | Tiered Sniper"
