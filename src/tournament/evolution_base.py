import os
import json
import random
import time
import concurrent.futures
from abc import ABC, abstractmethod
from tqdm import tqdm
from contextlib import redirect_stdout

class EvolutionEngineBase(ABC):
    """
    Unified Base Class for all Model Evolutions (V1-V10).
    Handles Parallelization, Table Formatting, and Smart Vaulting.
    """
    
    def __init__(self, version, population_size=100, generations=50, mutation_rate=0.2):
        self.version = version
        self.pop_size = population_size
        self.generations = generations
        self.mut_rate = mutation_rate
        self.population = []
        self._best_seen = {"fitness": -float('inf'), "cagr": 0, "dd": 100}
        self.vault_dir = f"champions/v{version}/vault" if version < 10 else "champions/v10_alpha/vault"
        os.makedirs(self.vault_dir, exist_ok=True)

    @abstractmethod
    def _create_random_genome(self): pass

    @abstractmethod
    def _mutate(self, genome): pass

    @abstractmethod
    def _evaluate_genome(self, genome, price_data, dates): pass

    def run(self):
        from src.helpers.data_provider import load_spy_data, CACHE_FILE
        print(f"\n--- Unified Evolution Engine [Model V{self.version}] ---")
        print(f"Population: {self.pop_size} | Generations: {self.generations}")
        print(f"{'Gen':<4} | {'Fit':<7} | {'CAGR':<8} | {'DD':<7} | {'Trades':<6} | {'Time':<5}")
        print("-" * 60)

        # Initialize Population
        if not self.population:
            self.population = [self._create_random_genome() for _ in range(self.pop_size)]

        for gen in range(self.generations):
            start_time = time.time()
            
            # Parallel Evaluation using the specific engine's evaluate method
            # Note: Workers must be initialized by the subclass or handled globally
            scored_pop = self._run_parallel_evaluation(gen)
            
            scored_pop.sort(key=lambda x: x[0], reverse=True)
            best_fit, best_stats, best_genome = scored_pop[0]
            elapsed = time.time() - start_time

            # Print Table Row
            print(f"{gen+1:02d}  | {best_fit:7.1f} | {best_stats['cagr']*100:7.2f}% | {abs(best_stats['max_dd'])*100:6.1f}% | {best_stats['num_rebalances']:6.0f} | {elapsed:4.1f}s")

            # Smart Vaulting
            self._handle_vaulting(best_fit, best_stats, best_genome)

            # Selection (Top 20%)
            elites = [x[2] for x in scored_pop[:max(2, self.pop_size // 5)]]
            new_pop = list(elites)
            while len(new_pop) < self.pop_size:
                new_pop.append(self._mutate(random.choice(elites)))
            self.population = new_pop

    def _handle_vaulting(self, fitness, stats, genome):
        cagr, dd = stats['cagr'] * 100, abs(stats['max_dd']) * 100
        is_record = False
        if cagr > (self._best_seen["cagr"] + 0.1):
            self._best_seen["cagr"] = cagr
            is_record = True
        if dd < (self._best_seen["dd"] - 0.5) and cagr > 10: # Only reward DD improvement if profitable
            self._best_seen["dd"] = dd
            is_record = True
            
        if is_record:
            filename = f"v{self.version}_cagr_{cagr:.1f}_dd_{dd:.1f}.json"
            with open(os.path.join(self.vault_dir, filename), 'w') as f:
                json.dump(genome, f, indent=4)
            # Update main genome
            main_path = os.path.join(os.path.dirname(self.vault_dir), "genome.json")
            with open(main_path, 'w') as f:
                json.dump(genome, f, indent=4)

    @abstractmethod
    def _run_parallel_evaluation(self, gen_idx):
        """Must implement ProcessPoolExecutor logic here."""
        pass
