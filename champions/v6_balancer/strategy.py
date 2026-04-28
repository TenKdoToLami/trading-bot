import json
import os
from strategies.genome_v6_balancer import GenomeV6

class ChampionV6(GenomeV6):
    """
    Standard wrapper for the best-performing V6 Balancer genome.
    Loads from champions/v6_balancer/genome.json.
    """
    def __init__(self, genome=None):
        # We prefer the passed genome if provided, otherwise load from file
        if genome is None:
            genome_path = os.path.join(os.path.dirname(__file__), "genome.json")
            if os.path.exists(genome_path):
                with open(genome_path, "r") as f:
                    genome = json.load(f)
                    
        super().__init__(genome=genome)
        self.NAME = "V6 | Probabilistic Balancer"
