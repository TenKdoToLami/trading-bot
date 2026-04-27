import random
import json
import concurrent.futures
import time
import os
import numpy as np

from strategies.gene_v4_chameleon import ChameleonV4
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data

# ──────────────────────────────────────────────────────
# Worker-Local Data
# ──────────────────────────────────────────────────────

_worker_price_data = None
_worker_dates = None

def _init_worker(cache_file):
    global _worker_price_data, _worker_dates
    import pandas as pd
    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_price_data = df.to_dict('records')
    _worker_dates = df.index

def _evaluate_genome_worker(genome):
    res = _execute_simulation(
        strategy_type=ChameleonV4,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome}
    )
    metrics = res['metrics']
    cagr = metrics['cagr']
    max_dd = abs(metrics['max_dd'])
    
    # ── High Alpha / Resilience Balance ──
    # ── High Alpha Focus (Matching V3 Standards) ──
    # Penalty of 10.0 means 1% of CAGR is worth 1% of MaxDD.
    fitness = (cagr * 100) - (max_dd * 10)

    # Absolute floor: avoid total liquidation (-95%)
    if metrics['max_dd'] < -0.95: fitness = -9999
    
    return fitness, genome, metrics

class EvolutionEngineV4:
    """
    Genetic Algorithm Engine for Chameleon V4 (Adaptive Volatility).
    """
    def __init__(self, population_size=50, generations=20, mutation_rate=0.20, seed_vault=None):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.seed_vault = seed_vault or "champions/v4_chameleon/vault"
        
        self.bounds = {
            "vix_ema": (10, 200),
            "vol_stretch": (0.8, 2.2),
            "mom_period": (50, 300),
            "rsi_period": (2, 20),
            "rsi_entry": (5, 40),
            "lev_calm": (1.0, 3.0),   # Capped at 3x Max
            "lev_stress": (0.0, 1.5),  # Defensive when VIX spikes
            "lev_panic": (0.0, 0.5)    # Cash-heavy during trend breaks
        }

        print("Loading master data for evolution v4...")
        self.data = load_spy_data("1993-01-01", force_refresh=False)
        from src.helpers.data_provider import CACHE_FILE
        self.cache_file = CACHE_FILE
        
        self.population = []
        
        # ── Seed Injection ──
        if self.seed_vault and os.path.exists(self.seed_vault):
            print(f"Injecting seeds from: {self.seed_vault}...")
            seeds = []
            for f in os.listdir(self.seed_vault):
                if f.endswith(".json"):
                    with open(os.path.join(self.seed_vault, f), "r") as jf:
                        try:
                            genome = json.load(jf)
                            # Basic structure check
                            if "vix_ema" in genome and "vol_stretch" in genome:
                                seeds.append(genome)
                        except: continue
            
            # Use seeds to fill initial population
            self.population.extend(seeds[:self.population_size])
            print(f"  Successfully injected {len(seeds)} V4 seeds.")

        # Fill the rest with random genomes
        while len(self.population) < self.population_size:
            self.population.append(self._random_genome())

    def _random_genome(self):
        genome = {}
        for key, (low, high) in self.bounds.items():
            if isinstance(low, int):
                genome[key] = random.randint(low, high)
            else:
                genome[key] = round(random.uniform(low, high), 2)
        return genome

    def _mutate(self, genome):
        new_genome = genome.copy()
        for key, (low, high) in self.bounds.items():
            if random.random() < self.mutation_rate:
                if isinstance(low, int):
                    # Relative mutation for integers
                    delta = random.randint(-10, 10)
                    new_genome[key] = max(low, min(high, genome[key] + delta))
                else:
                    # Relative mutation for floats
                    delta = random.uniform(-0.2, 0.2)
                    new_genome[key] = round(max(low, min(high, genome[key] + delta)), 2)
        return new_genome

    def _crossover(self, parent1, parent2):
        child = {}
        for key in self.bounds:
            child[key] = random.choice([parent1[key], parent2[key]])
        return child

    def run(self):
        print(f"\n[EVO] Starting Evolution for Chameleon V4")
        print(f"  Pop Size: {self.population_size} | Gens: {self.generations} | Mut Rate: {self.mutation_rate}")
        
        best_overall_fitness = -float('inf')
        best_overall_genome = None

        os.makedirs("champions/V4_CHAMELEON", exist_ok=True)
        os.makedirs(self.seed_vault, exist_ok=True)

        for gen in range(self.generations):
            t0 = time.time()
            results = []
            
            # Parallel evaluation
            workers = max(1, (os.cpu_count() or 2) // 2)
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=workers, 
                initializer=_init_worker, 
                initargs=(self.cache_file,)
            ) as executor:
                futures = [executor.submit(_evaluate_genome_worker, g) for g in self.population]
                for f in concurrent.futures.as_completed(futures):
                    results.append(f.result())

            # Sort by fitness
            results.sort(key=lambda x: x[0], reverse=True)
            
            gen_best_fitness, gen_best_genome, gen_best_metrics = results[0]
            
            # Check if this is a new overall leader
            if gen_best_fitness > best_overall_fitness:
                best_overall_fitness = gen_best_fitness
                best_overall_genome = gen_best_genome
                
                # Save as primary champion
                with open("champions/V4_CHAMELEON/genome.json", "w") as f:
                    json.dump(gen_best_genome, f, indent=4)
                
                # Save to Vault for future seeding
                c, d = gen_best_metrics['cagr']*100, abs(gen_best_metrics['max_dd']*100)
                vault_name = f"v4_cagr_{c:.2f}_dd_{d:.2f}.json"
                with open(os.path.join(self.seed_vault, vault_name), "w") as f:
                    json.dump(gen_best_genome, f, indent=4)
                
            duration = time.time() - t0
            print(f"Gen {gen+1:02d}: Best Fitness {gen_best_fitness:.2f} | CAGR {gen_best_metrics['cagr']*100:.1f}% | DD {gen_best_metrics['max_dd']*100:.1f}% | Time: {duration:.1f}s")

            # Selection (Top 30%)
            elites = [r[1] for r in results[:int(self.population_size * 0.3)]]
            
            # Next generation
            next_pop = elites[:2] # Keep top 2 survivors (Elitism)
            while len(next_pop) < self.population_size:
                if random.random() < 0.7:
                    p1, p2 = random.sample(elites, 2)
                    child = self._crossover(p1, p2)
                else:
                    child = self._random_genome()
                next_pop.append(self._mutate(child))
            
            self.population = next_pop

        print(f"\n[DONE] Best Overall Fitness: {best_overall_fitness:.2f}")
        print(f"Best Genome saved to champions/V4_CHAMELEON/genome.json")
        print(f"Top performers archived in {self.seed_vault}")
