"""
Champion Genome — The best strategy found by the Evolution Engine.
Automatically loads 'best_genome.json' for use in the main tournament.
"""

import json
import os
from strategies._genome_strategy import GenomeStrategy

class ChampionGenome(GenomeStrategy):
    NAME = "Champion Genome (AI)"

    def __init__(self):
        # Determine the path to best_genome.json relative to the project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        genome_path = os.path.join(project_root, "best_genome.json")
        
        if os.path.exists(genome_path):
            with open(genome_path, "r") as f:
                best_genome = json.load(f)
            super().__init__(genome=best_genome)
        else:
            # Fallback to default if not found
            super().__init__()
