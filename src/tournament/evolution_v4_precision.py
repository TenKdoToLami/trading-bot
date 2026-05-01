import random
import json
import concurrent.futures
import time
import os
import pandas as pd

from strategies.genome_v4_precision import GenomeV4Precision
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data

_worker_price_data = None
_worker_dates = None
_worker_min_cagr = 0.0

def _init_worker(cache_file, min_cagr):
    global _worker_price_data, _worker_dates, _worker_min_cagr
    import pandas as pd
    _worker_min_cagr = min_cagr
    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_dates = df.index
    # Turbo I/O: 10x faster than iterrows()
    _worker_price_data = df.to_dict('records')
    print(f"  [Worker {os.getpid()}] V4-Precision Ready. Min CAGR: {min_cagr:.1f}%")

def _evaluate_genome_worker(genome):
    # ── STAGE 1: LITE SCREENING (Last ~4 years) ──
    lite_window = 1000
    lite_res = _execute_simulation(
        strategy_type=GenomeV4Precision,
        price_data_list=_worker_price_data[-lite_window:],
        dates=_worker_dates[-lite_window:],
        strategy_kwargs={'genome': genome}
    )
    
    # Kill genomes that fail in the recent regime
    if lite_res['metrics']['cagr'] <= 0:
        return -500.0, genome, lite_res['metrics']

    # ── STAGE 2: FULL AUDIT (30+ years) ──
    res = _execute_simulation(
        strategy_type=GenomeV4Precision,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome}
    )
    metrics = res['metrics']
    cagr = metrics['cagr'] * 100
    max_dd = abs(metrics['max_dd']) * 100
    
    # ── RISK-ADJUSTED FITNESS (Institutional Standard) ──
    fitness = cagr - (max_dd * 0.15)
    
    # Blowout Penalty
    if max_dd >= 95.0: 
        fitness -= 1000
        
    return fitness, genome, metrics

class EvolutionEngineV4Precision:
    def __init__(self, population_size=50, generations=20, mutation_rate=0.2, seed_vault=None, use_ablation=True, min_cagr=0.0):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.use_ablation = use_ablation
        self.min_cagr = min_cagr
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']
        self.brains = ['panic', 'bull']
        
        self.lb_bounds = {
            'sma': (10, 500), 'ema': (10, 300), 'rsi': (5, 100), 'macd_f': (5, 50),
            'macd_s': (15, 120), 'adx': (5, 100), 'trix': (5, 100), 'slope': (5, 200),
            'vol': (5, 252), 'atr': (5, 100)
        }

        print("Loading master data for Evolution V4 Precision...")
        self.data = load_spy_data("1993-01-01")
        from src.helpers.data_provider import CACHE_FILE
        self.cache_file = CACHE_FILE
        
        self.population = []
        if seed_vault and os.path.exists(seed_vault):
            seeds = []
            vault_files = sorted(os.listdir(seed_vault), reverse=True)
            for f in vault_files:
                if f.endswith(".json"):
                    with open(os.path.join(seed_vault, f), "r") as jf:
                        try:
                            g = json.load(jf)
                            g['version'] = 4.0
                            seeds.append(g)
                        except: continue
            
            num_seeds = min(len(seeds), self.population_size)
            self.population.extend(seeds[:num_seeds])
            print(f"  SUCCESS: Injected {num_seeds} V4 seeds from vault.")

        while len(self.population) < self.population_size:
            self.population.append(self._random_genome())

    def _random_genome(self):
        genome = {}
        for b in self.brains:
            genome[b] = {
                'w': {k: random.uniform(-10, 10) for k in self.indicators},
                'a': {k: (random.random() > 0.4 if self.use_ablation else True) for k in self.indicators},
                't': random.uniform(-50, 50),
                'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()}
            }
        genome['lock_days'] = random.uniform(0, 20)
        genome['version'] = 4.0
        return genome

    def _crossover(self, p1, p2):
        child = {}
        for b in self.brains:
            child[b] = {
                'w': {k: (p1[b]['w'][k] if random.random() > 0.5 else p2[b]['w'][k]) for k in self.indicators},
                'a': {k: (p1[b]['a'][k] if random.random() > 0.5 else p2[b]['a'][k]) for k in self.indicators},
                't': p1[b]['t'] if random.random() > 0.5 else p2[b]['t'],
                'lookbacks': {k: (p1[b]['lookbacks'][k] if random.random() > 0.5 else p2[b]['lookbacks'][k]) for k in self.lb_bounds}
            }
        child['lock_days'] = p1['lock_days'] if random.random() > 0.5 else p2['lock_days']
        child['version'] = 4.0
        return child

    def _mutate(self, genome):
        mutated = {}
        for b in self.brains:
            mutated[b] = {
                'w': {k: (v + random.gauss(0, 1.2) if random.random() < self.mutation_rate else v) for k, v in genome[b]['w'].items()},
                'a': {k: (not v if random.random() < 0.05 else v) for k, v in genome[b]['a'].items()},
                't': genome[b]['t'] + random.gauss(0, 1.2) if random.random() < self.mutation_rate else genome[b]['t'],
                'lookbacks': {}
            }
            for k, v in genome[b]['lookbacks'].items():
                mn, mx = self.lb_bounds[k]
                new_v = v + int(random.gauss(0, (mx-mn)*0.15)) if random.random() < self.mutation_rate else v
                mutated[b]['lookbacks'][k] = max(mn, min(mx, new_v))
        mutated['lock_days'] = max(0, min(40, genome['lock_days'] + random.gauss(0, 4))) if random.random() < self.mutation_rate else genome['lock_days']
        # Enforce MACD order
        for b in self.brains:
            if mutated[b]['lookbacks']['macd_s'] <= mutated[b]['lookbacks']['macd_f']:
                mutated[b]['lookbacks']['macd_s'] = mutated[b]['lookbacks']['macd_f'] + 1
        mutated['version'] = 4.0
        return mutated

    def run(self):
        max_workers = max(1, os.cpu_count() - 2)
        print(f"Starting Evolution V4 Precision: {self.generations} generations, pop {self.population_size}, mut {self.mutation_rate:.2f}, MinCAGR: {self.min_cagr:.1f}%")
        
        vault_dir = "champions/v4_precision/vault"
        os.makedirs(vault_dir, exist_ok=True)
        best_overall_genome = None

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers, initializer=_init_worker, initargs=(self.cache_file, self.min_cagr)) as executor:
            for gen in range(self.generations):
                start_time = time.time()
                futures = [executor.submit(_evaluate_genome_worker, g) for g in self.population]
                scored = [f.result() for f in concurrent.futures.as_completed(futures)]
                scored.sort(key=lambda x: x[0], reverse=True)
                
                best_fit, best_genome, best_metrics = scored[0]
                best_overall_genome = best_genome
                elapsed = time.time() - start_time
                
                print(f"Gen {gen+1:02d} | Fit: {best_fit:6.2f} | CAGR: {best_metrics['cagr']*100:5.2f}% | DD: {best_metrics['max_dd']*100:5.2f}% | Time: {elapsed:.1f}s")
                
                # Save to vault
                if (best_metrics['cagr'] * 100) >= self.min_cagr:
                    v_path = os.path.join(vault_dir, f"v4p_cagr_{best_metrics['cagr']*100:.2f}_dd_{best_metrics['max_dd']*100:.2f}.json")
                    with open(v_path, 'w') as f:
                        json.dump(best_genome, f, indent=4)
                
                # Selection
                elites = [x[1] for x in scored[:max(2, int(self.population_size * 0.2))]]
                new_pop = list(elites)
                while len(new_pop) < self.population_size:
                    p1, p2 = random.choice(elites), random.choice(elites)
                    child = self._crossover(p1, p2)
                    new_pop.append(self._mutate(child))
                
                self.population = new_pop

        return best_overall_genome
