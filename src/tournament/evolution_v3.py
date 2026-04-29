import random
import json
import concurrent.futures
import time
import os

from strategies.genome_v3_precision import GenomeV3Strategy
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
        strategy_type=GenomeV3Strategy,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome}
    )
    metrics = res['metrics']
    cagr = metrics['cagr']
    max_dd = abs(metrics['max_dd'])
    
    # ── High Alpha Focus ──
    # Penalty of 10.0 means 1% of CAGR is worth 1% of MaxDD.
    fitness = (cagr * 100) - (max_dd * 10)

    # Absolute floor: avoid total liquidation (-95%)
    if metrics['max_dd'] < -0.95: fitness = -9999
    
    return fitness, genome, metrics


class EvolutionEngineV3:
    """
    Genetic Algorithm Engine for Genome V3 (Precision Binary Architecture).
    """
    def __init__(self, population_size=50, generations=20, mutation_rate=0.15, seed_vault=None, use_ablation=True):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.use_ablation = use_ablation
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']
        self.brains = ['panic', 'bull']
        
        # Define bounds for evolving indicator parameters (lookbacks)
        self.lb_bounds = {
            'sma': (20, 300),
            'ema': (10, 200),
            'rsi': (5, 50),
            'macd_f': (5, 30),
            'macd_s': (15, 60),
            'adx': (5, 50),
            'trix': (5, 50),
            'slope': (5, 50),
            'vol': (5, 60),
            'atr': (5, 50)
        }

        print("Loading master data (SPY + Macro) for evolution v3...")
        self.data = load_spy_data("1993-01-01", force_refresh=False)
        from src.helpers.data_provider import CACHE_FILE
        self.cache_file = CACHE_FILE
        
        self.population = []
        
        # ── Seed Injection ──
        if seed_vault and os.path.exists(seed_vault):
            print(f"Injecting seeds from: {seed_vault}...")
            seeds = []
            for f in os.listdir(seed_vault):
                if f.endswith(".json"):
                    with open(os.path.join(seed_vault, f), "r") as jf:
                        try:
                            genome = json.load(jf)
                            # Minimal V3 structure check (lookbacks are nested in brains)
                            if 'panic' not in genome or 'bull' not in genome or 'lookbacks' not in genome['panic']:
                                # Skip non-V3 genomes (V1/V2)
                                continue
                            seeds.append(genome)
                        except: continue
            
            self.population.extend(seeds[:self.population_size])
            print(f"  Successfully injected {len(seeds)} V3 seeds.")

        # Fill the rest with random genomes
        while len(self.population) < self.population_size:
            self.population.append(self._random_genome())

    def _random_genome(self):
        genome = {}
        for b in self.brains:
            genome[b] = {
                'w': {k: random.uniform(-4, 4) for k in self.indicators},
                'a': {k: (random.random() > 0.4 if self.use_ablation else True) for k in self.indicators},
                't': random.uniform(-1.5, 1.5),
                'lookbacks': {}
            }
            for k, (mn, mx) in self.lb_bounds.items():
                genome[b]['lookbacks'][k] = random.randint(mn, mx)
                
        genome['lock_days'] = random.uniform(0, 10)
        return genome

    def _crossover(self, p1, p2):
        child = {}
        for b in self.brains:
            child[b] = {
                'w': {}, 'a': {}, 't': p1[b]['t'] if random.random() > 0.5 else p2[b]['t'],
                'lookbacks': {}
            }
            # Crossover Lookbacks per brain
            for k in self.lb_bounds.keys():
                child[b]['lookbacks'][k] = p1[b]['lookbacks'][k] if random.random() > 0.5 else p2[b]['lookbacks'][k]
                
            for k in self.indicators:
                child[b]['w'][k] = p1[b]['w'][k] if random.random() > 0.5 else p2[b]['w'][k]
                child[b]['a'][k] = p1[b]['a'][k] if random.random() > 0.5 else p2[b]['a'][k]
        
        child['lock_days'] = p1['lock_days'] if random.random() > 0.5 else p2['lock_days']
        return child

    def _mutate(self, genome):
        mutated = {}
        
        for b in self.brains:
            mutated[b] = {'w': {}, 'a': {}, 't': genome[b]['t'], 'lookbacks': {}}
            
            # Mutate Lookbacks per brain
            for k, (mn, mx) in self.lb_bounds.items():
                val = genome[b]['lookbacks'][k]
                if random.random() < self.mutation_rate:
                    val += int(random.gauss(0, (mx - mn) * 0.1))
                    val = max(mn, min(mx, val))
                    if k == 'macd_s' and val <= mutated[b]['lookbacks'].get('macd_f', 0):
                        val = mutated[b]['lookbacks']['macd_f'] + 1
                mutated[b]['lookbacks'][k] = val
                
            if mutated[b]['lookbacks']['macd_f'] >= mutated[b]['lookbacks']['macd_s']:
                mutated[b]['lookbacks']['macd_s'] = mutated[b]['lookbacks']['macd_f'] + 1

            if random.random() < self.mutation_rate:
                mutated[b]['t'] += random.gauss(0, 0.2)
            
            for k in self.indicators:
                w = genome[b]['w'][k]
                if random.random() < self.mutation_rate:
                    mutated[b]['w'][k] = w + random.gauss(0, 0.5)
                else:
                    mutated[b]['w'][k] = w
                
                a = genome[b]['a'][k]
                if self.use_ablation and random.random() < 0.05:
                    mutated[b]['a'][k] = not a
                else:
                    mutated[b]['a'][k] = True if not self.use_ablation else a
                    
        mutated['lock_days'] = genome['lock_days']
        if random.random() < self.mutation_rate:
            mutated['lock_days'] = max(0, min(20, mutated['lock_days'] + random.gauss(0, 2)))
            
        return mutated

    def run(self):
        best_overall_fitness = -9999
        best_overall_metrics = None
        best_overall_genome = None

        max_workers = max(1, os.cpu_count() - 4)
        print(f"Starting Evolution V3: {self.generations} generations, pop {self.population_size}, ablation {'ON' if self.use_ablation else 'OFF'}, mutation {self.mutation_rate:.2f} (using {max_workers} cores)")
        
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=max_workers,
            initializer=_init_worker, 
            initargs=(self.cache_file,)
        ) as executor:
            for gen in range(self.generations):
                start_time = time.time()
                
                futures = [executor.submit(_evaluate_genome_worker, g) for g in self.population]
                scored = [f.result() for f in concurrent.futures.as_completed(futures)]
                scored.sort(key=lambda x: x[0], reverse=True)
                
                best_fit, best_genome, best_metrics = scored[0]
                if best_fit > best_overall_fitness:
                    best_overall_fitness = best_fit
                    best_overall_genome = best_genome
                    best_overall_metrics = best_metrics
                    
                    vault_dir = "champions/v3_precision/vault"
                    if not os.path.exists(vault_dir): os.makedirs(vault_dir)
                    c, d = best_metrics['cagr']*100, best_metrics['max_dd']*100
                    with open(f"{vault_dir}/v3_cagr_{c:.2f}_dd_{d:.2f}.json", "w") as f:
                        json.dump(best_genome, f, indent=2)

                elapsed = time.time() - start_time
                print(f"V3 Gen {gen+1:02d} | Fit: {best_fit:6.2f} | CAGR: {best_metrics['cagr']*100:6.2f}% | MaxDD: {best_metrics['max_dd']*100:6.2f}% | Time: {elapsed:.1f}s")
                
                elites = [x[1] for x in scored[:max(2, int(self.population_size * 0.2))]]
                new_pop = list(elites)
                while len(new_pop) < self.population_size:
                    child = self._mutate(self._crossover(random.choice(elites), random.choice(elites)))
                    new_pop.append(child)
                self.population = new_pop

        save_path = "champions/v3_precision/genome.json"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(best_overall_genome, f, indent=2)
        print(f"Saved best genome to {save_path}")
        print(f"\nEvolution V3 Complete. Best CAGR: {best_overall_metrics['cagr']*100:.2f}%")
        return best_overall_genome
