"""
Base Evolution Engine — Core evolution logic for all engine versions.
Provides a standard framework for multiprocessing, population management, and vaulting.
"""

import os
import json
import random
import time
import concurrent.futures
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Callable
from tqdm import tqdm

class BaseEvolutionEngine(ABC):
    """
    Abstract base class for all evolution engines.
    Encapsulates the evolution loop, multiprocessing, and champion saving.
    """
    
    def __init__(
        self, 
        version_id: str,
        population_size: int = 100, 
        generations: int = 50, 
        mutation_rate: float = 0.2, 
        seed_vault: Optional[str] = None, 
        use_ablation: bool = True, 
        min_cagr: float = 0.0, 
        workers: Optional[int] = None,
        **kwargs
    ):
        self.version_id = version_id
        self.pop_size = population_size
        self.generations = generations
        self.mut_rate = mutation_rate
        self.seed_vault = seed_vault
        self.use_ablation = use_ablation
        self.min_cagr = min_cagr
        self.workers = workers or max(1, os.cpu_count() - 2)
        
        self.population = []
        self._best_seen = {"cagr": -100.0, "dd": 100.0}
        self._best_seen_fitness = -1e9
        self.stagnation_counter = 0
        self.base_mut_rate = mutation_rate
        self.vault_dir = f"champions/{version_id}/vault"
        self.use_tournament = kwargs.get("use_tournament", False)
        
        # Initialize population (MUST be at the end so subclasses can set attributes)
        self._initialize_population()

    def _initialize_population(self):
        """Loads seeds if available, then fills the rest with random genomes."""
        # Seeding ONLY occurs if seed_vault is provided
        if self.seed_vault and os.path.exists(self.seed_vault):
            self._load_seeds()

        while len(self.population) < self.pop_size:
            self.population.append(self._random_genome())
        
        self.population = self.population[:self.pop_size]

    def _load_seeds(self):
        """Standard seed loading logic."""
        # 1. Try parent genome
        parent_genome = os.path.join(os.path.dirname(self.seed_vault), "genome.json")
        if os.path.exists(parent_genome):
            try:
                with open(parent_genome, "r") as f:
                    self.population.append(json.load(f))
            except: pass

        # 2. Load vault seeds sorted by CAGR
        seeds = []
        for f in os.listdir(self.seed_vault):
            if f.endswith(".json"):
                try:
                    # Expecting format like ...cagr_25.1_dd_12.2.json
                    parts = f.split("cagr_")
                    if len(parts) > 1:
                        cagr = float(parts[1].split("_")[0])
                        seeds.append((cagr, f))
                    else:
                        seeds.append((0, f))
                except:
                    seeds.append((0, f))
        
        seeds.sort(key=lambda x: x[0], reverse=True)
        for _, f in seeds:
            if len(self.population) >= self.pop_size: break
            try:
                with open(os.path.join(self.seed_vault, f), "r") as jf:
                    self.population.append(json.load(jf))
            except: pass
        
        if self.population:
            print(f"  [SEED] Injected {len(self.population)} seeds for {self.version_id}")

    @abstractmethod
    def _random_genome(self) -> Dict[str, Any]:
        """Generate a single random genome."""
        pass

    @abstractmethod
    def _mutate(self, genome: Dict[str, Any]) -> Dict[str, Any]:
        """Apply mutations to a genome."""
        pass

    def _get_worker_config(self) -> Tuple[Callable, Tuple]:
        """
        Returns the worker function and its initialization arguments.
        Defaults to standard evolution worker structure.
        """
        # This must be implemented or provided by the subclass if it uses custom workers
        raise NotImplementedError("Subclasses must implement _get_worker_config or override run()")

    def run(self):
        """Main evolution loop."""
        os.makedirs(self.vault_dir, exist_ok=True)
        
        worker_func, init_args = self._get_worker_config()
        
        print(f"Starting {self.version_id} Evolution: {self.generations} gens, pop {self.pop_size}, mut {self.mut_rate:.2f}")
        self._print_header()

        with concurrent.futures.ProcessPoolExecutor(max_workers=self.workers, initializer=init_args[0], initargs=init_args[1]) as executor:
            for gen in range(self.generations):
                start_time = time.time()
                
                # Submit all genomes for evaluation
                futures = [executor.submit(worker_func, g) for g in self.population]
                
                scored = []
                # Use tqdm for progress tracking within the generation
                pbar = tqdm(concurrent.futures.as_completed(futures), total=self.pop_size, desc=f"G{gen+1}", leave=False)
                for f in pbar:
                    try:
                        scored.append(f.result())
                    except Exception as e:
                        print(f"\nWorker Error: {e}")
                
                # Sort by fitness (descending)
                scored.sort(key=lambda x: x[0], reverse=True)
                
                # Update stats and save best
                best_fit, best_stats, best_genome = scored[0]
                elapsed = time.time() - start_time
                
                # --- STAGNATION RECOVERY ---
                if best_fit > (self._best_seen_fitness + 0.001):
                    if self.stagnation_counter >= 5:
                        print(f"  [RECOVERY] Improvement found! Resetting mutation rate to {self.base_mut_rate:.2f}")
                    self._best_seen_fitness = best_fit
                    self.stagnation_counter = 0
                    self.mut_rate = self.base_mut_rate
                else:
                    self.stagnation_counter += 1
                    if self.stagnation_counter > 0 and self.stagnation_counter % 5 == 0:
                        new_mut = min(0.8, self.mut_rate * 2.0)
                        if new_mut > self.mut_rate:
                            self.mut_rate = new_mut
                            print(f"  [STAGNATION] No improvement for {self.stagnation_counter} gens. Boosting mutation rate to {self.mut_rate:.2f}")

                self._print_generation_summary(gen + 1, best_fit, best_stats, best_genome, elapsed)
                self._save_champion(best_stats, best_genome)
                
                # Natural Selection & Reproduction
                self._evolve_population(scored)
                
        return self.population[0] # Return the final best

    def _print_header(self):
        """Prints the summary table header."""
        print(f"{'Gen':<4} | {'Fit':<7} | {'CAGR':<8} | {'DD':<7} | {'Trades':<6} | {'Time':<5}")
        print("-" * 60)

    def _print_generation_summary(self, gen, fit, stats, genome, elapsed):
        """Prints the summary for a single generation."""
        cagr = stats.get('cagr', 0) * 100
        dd = abs(stats.get('max_dd', 0)) * 100
        trades = stats.get('num_rebalances', 0)
        print(f"{gen:02d}  | {fit:7.1f} | {cagr:7.2f}% | {dd:6.1f}% | {trades:6.0f} | {elapsed:4.1f}s")

    def _save_champion(self, stats, genome):
        """Saves the genome to the vault if it outperforms historical bests."""
        cagr, dd = stats['cagr'] * 100, abs(stats['max_dd']) * 100
        
        # Improvement criteria: higher CAGR or lower DD
        is_better = (cagr > (self._best_seen["cagr"] + 0.1)) or (dd < (self._best_seen["dd"] - 0.5))
        
        if cagr >= self.min_cagr and is_better:
            self._best_seen["cagr"] = max(cagr, self._best_seen["cagr"])
            self._best_seen["dd"] = min(dd, self._best_seen["dd"])
            
            # Filename includes metrics for easy browsing
            filename = f"{self.version_id}_cagr_{cagr:.1f}_dd_{dd:.1f}.json"
            v_path = os.path.join(self.vault_dir, filename)
            with open(v_path, 'w') as f:
                json.dump(genome, f, indent=4)

    def _tournament_select(self, scored_population: List[Tuple[float, Dict, Dict]], k: int = 3) -> Dict[str, Any]:
        """
        Selects the best genome out of a random sample of k.
        Provides better diversity than strict elitism.
        """
        sample = random.sample(scored_population, k)
        sample.sort(key=lambda x: x[0], reverse=True)
        return sample[0][2]

    def _evolve_population(self, scored_population: List[Tuple[float, Dict, Dict]]):
        """Handles elitism and mutation for the next generation."""
        # 1. Elitism: Keep absolute top 2 genomes safe
        num_elites = 2
        elites = [x[2] for x in scored_population[:num_elites]]
        
        # 2. Reproduction pool: top 20% if not using tournament
        repro_pool = [x[2] for x in scored_population[:max(2, self.pop_size // 5)]]
        
        new_population = list(elites)
        has_crossover = hasattr(self, '_crossover')
        
        while len(new_population) < self.pop_size:
            if self.use_tournament:
                p1 = self._tournament_select(scored_population, k=3)
            else:
                p1 = random.choice(repro_pool)
                
            if has_crossover and random.random() < 0.4:
                if self.use_tournament:
                    p2 = self._tournament_select(scored_population, k=3)
                else:
                    p2 = random.choice(repro_pool)
                child = self._crossover(p1, p2)
            else:
                child = self._mutate(p1)
            
            # Apply a final mutation pass to crossover children
            if has_crossover and len(new_population) >= num_elites:
                if random.random() < self.mut_rate:
                    child = self._mutate(child)
                
            new_population.append(child)
            
        self.population = new_population
