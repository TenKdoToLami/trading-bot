import random
import json
import concurrent.futures
import time
import os
import pandas as pd

from strategies.genome_v5_sniper import GenomeV5Sniper
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
    _worker_price_data = [row.to_dict() for _, row in df.iterrows()]
    print(f"  [Worker {os.getpid()}] V5 Ready. Min CAGR: {_worker_min_cagr*100:.1f}%")

def _evaluate_genome_worker(genome):
    res = _execute_simulation(
        strategy_type=GenomeV5Sniper,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome}
    )
    
    metrics = res['metrics']
    cagr = metrics['cagr']
    max_dd = abs(metrics['max_dd'])
    
    # CAGR Threshold Enforcement
    if cagr < _worker_min_cagr:
        return -99999, genome, metrics
        
    # Tiered Sniper Fitness: CAGR vs DD Balance
    fitness = (cagr * 100) - (max_dd * 15)
    
    if metrics['max_dd'] < -0.95: fitness = -99999
    return fitness, genome, metrics

class EvolutionEngineV5Sniper:
    def __init__(self, population_size=50, generations=20, mutation_rate=0.2, seed_vault=None, use_ablation=True, min_cagr=0.0):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.use_ablation = use_ablation
        self.min_cagr = min_cagr
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']
        
        self.lb_bounds = {
            'sma': (20, 300), 'ema': (10, 200), 'rsi': (5, 50), 'macd_f': (5, 30),
            'macd_s': (15, 60), 'adx': (5, 50), 'trix': (5, 50), 'slope': (5, 50),
            'vol': (5, 60), 'atr': (5, 50)
        }

        print("Loading master data for Evolution V5 Tiered Sniper...")
        self.data = load_spy_data("1993-01-01")
        from src.helpers.data_provider import CACHE_FILE
        self.cache_file = CACHE_FILE
        
        self.population = []
        if seed_vault and os.path.exists(seed_vault):
            print(f"Injecting seeds from: {seed_vault}...")
            seeds = []
            for f in os.listdir(seed_vault):
                if f.endswith(".json"):
                    with open(os.path.join(seed_vault, f), "r") as jf:
                        try:
                            g = json.load(jf)
                            # Only load if it's a valid V5 Tiered Sniper
                            if 'sniper' in g and 't_low' in g['sniper']:
                                seeds.append(g)
                        except: continue
            self.population.extend(seeds[:self.population_size])

        while len(self.population) < self.population_size:
            self.population.append(self._random_genome())

    def _random_genome(self):
        t1 = random.uniform(0.5, 3.0)
        t2 = t1 + random.uniform(0.5, 3.0)
        return {
            'sniper': {
                'w': {k: random.uniform(-4, 4) for k in self.indicators},
                'a': {k: (random.random() > 0.4 if self.use_ablation else True) for k in self.indicators},
                't_low': t1,
                't_high': t2,
                'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()}
            },
            'lock_days': random.uniform(1, 10),
            'version': 5.0
        }

    def _crossover(self, p1, p2):
        res = {
            'sniper': {
                'w': {k: (p1['sniper']['w'][k] if random.random() > 0.5 else p2['sniper']['w'][k]) for k in self.indicators},
                'a': {k: (p1['sniper']['a'][k] if random.random() > 0.5 else p2['sniper']['a'][k]) for k in self.indicators},
                't_low': p1['sniper']['t_low'] if random.random() > 0.5 else p2['sniper']['t_low'],
                't_high': p1['sniper']['t_high'] if random.random() > 0.5 else p2['sniper']['t_high'],
                'lookbacks': {k: (p1['sniper']['lookbacks'][k] if random.random() > 0.5 else p2['sniper']['lookbacks'][k]) for k in self.lb_bounds}
            },
            'lock_days': p1['lock_days'] if random.random() > 0.5 else p2['lock_days'],
            'version': 5.0
        }
        # Enforce t_high > t_low
        if res['sniper']['t_high'] < res['sniper']['t_low']:
            res['sniper']['t_high'], res['sniper']['t_low'] = res['sniper']['t_low'], res['sniper']['t_high']
        if res['sniper']['t_high'] == res['sniper']['t_low']:
            res['sniper']['t_high'] += 0.5
        return res

    def _mutate(self, genome):
        mutated = {
            'sniper': {
                'w': {k: (v + random.gauss(0, 0.8) if random.random() < self.mutation_rate else v) for k, v in genome['sniper']['w'].items()},
                'a': {k: (not v if random.random() < 0.05 else v) for k, v in genome['sniper']['a'].items()},
                't_low': genome['sniper']['t_low'] + random.gauss(0, 0.8) if random.random() < self.mutation_rate else genome['sniper']['t_low'],
                't_high': genome['sniper']['t_high'] + random.gauss(0, 0.8) if random.random() < self.mutation_rate else genome['sniper']['t_high'],
                'lookbacks': {}
            },
            'lock_days': max(1, min(20, genome['lock_days'] + random.gauss(0, 2))) if random.random() < self.mutation_rate else genome['lock_days'],
            'version': 5.0
        }
        for k, v in genome['sniper']['lookbacks'].items():
            mn, mx = self.lb_bounds[k]
            new_v = v + int(random.gauss(0, (mx-mn)*0.15)) if random.random() < self.mutation_rate else v
            mutated['sniper']['lookbacks'][k] = max(mn, min(mx, new_v))
        
        # Repair thresholds
        if mutated['sniper']['t_high'] < mutated['sniper']['t_low']:
            mutated['sniper']['t_high'] = mutated['sniper']['t_low'] + 0.5
        
        mutated['sniper']['lookbacks']['macd_s'] = mutated['sniper']['lookbacks']['macd_f'] + 1
        return mutated

    def run(self):
        best_overall_fitness = -9999
        best_overall_genome = None
        max_workers = max(1, os.cpu_count() - 4)
        print(f"Starting Evolution V5 Sniper: {self.generations} generations, pop {self.population_size}, ablation {'ON' if self.use_ablation else 'OFF'}, mutation {self.mutation_rate:.2f}, MinCAGR: {self.min_cagr*100:.1f}%")
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers, initializer=_init_worker, initargs=(self.cache_file, self.min_cagr)) as executor:
            for gen in range(self.generations):
                start_time = time.time()
                futures = [executor.submit(_evaluate_genome_worker, g) for g in self.population]
                scored = [f.result() for f in concurrent.futures.as_completed(futures)]
                scored.sort(key=lambda x: x[0], reverse=True)
                best_fit, best_genome, best_metrics = scored[0]
                
                if best_fit > best_overall_fitness:
                    best_overall_fitness = best_fit
                    best_overall_genome = best_genome
                    
                    # Vault-Lock: Only write to disk if threshold is met
                    if best_metrics['cagr'] >= self.min_cagr:
                        vault_dir = "champions/v5_sniper/vault"
                        if not os.path.exists(vault_dir): os.makedirs(vault_dir)
                        c, d = best_metrics['cagr']*100, best_metrics['max_dd']*100
                        with open(f"{vault_dir}/v5_cagr_{c:.2f}_dd_{d:.2f}.json", "w") as f:
                            json.dump(best_genome, f, indent=2)
                        
                        # Update main champion file
                        save_path = "champions/v5_sniper/genome.json"
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        with open(save_path, "w") as f: json.dump(best_genome, f, indent=2)
                    else:
                        print(f"  [Vault-Lock] Gen {gen+1} champion blocked (CAGR {best_metrics['cagr']*100:.2f}% < {self.min_cagr*100:.1f}%)")
                
                elapsed = time.time() - start_time
                print(f"V5-Snipe Gen {gen+1:02d} | Fit: {best_fit:6.2f} | CAGR: {best_metrics['cagr']*100:6.2f}% | MaxDD: {best_metrics['max_dd']*100:6.2f}% | Time: {elapsed:.1f}s")
                
                elites = [x[1] for x in scored[:max(2, int(self.population_size * 0.2))]]
                new_pop = list(elites)
                while len(new_pop) < self.population_size:
                    new_pop.append(self._mutate(self._crossover(random.choice(elites), random.choice(elites))))
                self.population = new_pop

        return best_overall_genome
