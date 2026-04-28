import random
import json
import concurrent.futures
import time
import os
import pandas as pd

from strategies.v6_balancer.genome import GenomeV6
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data

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
        strategy_type=GenomeV6,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome}
    )
    metrics = res['metrics']
    cagr = metrics['cagr']
    max_dd = abs(metrics['max_dd'])
    
    # Balancer Fitness: CAGR vs DD with a heavy Sharpe/Resilience focus
    # Because it's a balancer, we expect higher Sharpe ratios.
    fitness = (cagr * 100) - (max_dd * 12) + (metrics.get('sharpe', 0) * 5)
    
    if metrics['max_dd'] < -0.95: fitness = -9999
    return fitness, genome, metrics

class EvolutionEngineV6:
    def __init__(self, population_size=50, generations=20, mutation_rate=0.2, seed_vault=None, use_ablation=True):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.use_ablation = use_ablation
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']
        self.brains = ['cash', '1x', '2x', '3x']
        
        self.lb_bounds = {
            'sma': (20, 300), 'ema': (10, 200), 'rsi': (5, 50), 'macd_f': (5, 30),
            'macd_s': (15, 60), 'adx': (5, 50), 'trix': (5, 50), 'slope': (5, 50),
            'vol': (5, 60), 'atr': (5, 50)
        }

        print("Loading master data for Evolution V6 Balancer...")
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
                            # V6 is too different for auto-conversion usually, 
                            # but we can try to load V6 genomes.
                            g = json.load(jf)
                            if 'brains' in g: seeds.append(g)
                        except: continue
            self.population.extend(seeds[:self.population_size])

        while len(self.population) < self.population_size:
            self.population.append(self._random_genome())

    def _random_genome(self):
        genome = {
            'brains': {},
            'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()},
            'temp': random.uniform(0.5, 2.0),
            'lock_days': random.uniform(1, 5),
            'version': 6.0
        }
        for b in self.brains:
            genome['brains'][b] = {
                'w': {k: random.uniform(-4, 4) for k in self.indicators},
                'a': {k: (random.random() > 0.4 if self.use_ablation else True) for k in self.indicators}
            }
        return genome

    def _crossover(self, p1, p2):
        child = {
            'brains': {},
            'lookbacks': {k: (p1['lookbacks'][k] if random.random() > 0.5 else p2['lookbacks'][k]) for k in self.lb_bounds},
            'temp': p1['temp'] if random.random() > 0.5 else p2['temp'],
            'lock_days': p1['lock_days'] if random.random() > 0.5 else p2['lock_days'],
            'version': 6.0
        }
        for b in self.brains:
            child['brains'][b] = {
                'w': {k: (p1['brains'][b]['w'][k] if random.random() > 0.5 else p2['brains'][b]['w'][k]) for k in self.indicators},
                'a': {k: (p1['brains'][b]['a'][k] if random.random() > 0.5 else p2['brains'][b]['a'][k]) for k in self.indicators}
            }
        return child

    def _mutate(self, genome):
        mutated = {
            'brains': {},
            'lookbacks': {},
            'temp': max(0.1, genome['temp'] + random.gauss(0, 0.2)) if random.random() < self.mutation_rate else genome['temp'],
            'lock_days': max(1, min(10, genome['lock_days'] + random.gauss(0, 1))) if random.random() < self.mutation_rate else genome['lock_days'],
            'version': 6.0
        }
        for b in self.brains:
            mutated['brains'][b] = {
                'w': {k: (v + random.gauss(0, 0.8) if random.random() < self.mutation_rate else v) for k, v in genome['brains'][b]['w'].items()},
                'a': {k: (not v if random.random() < 0.05 else v) for k, v in genome['brains'][b]['a'].items()}
            }
        for k, v in genome['lookbacks'].items():
            mn, mx = self.lb_bounds[k]
            new_v = v + int(random.gauss(0, (mx-mn)*0.1)) if random.random() < self.mutation_rate else v
            mutated['lookbacks'][k] = max(mn, min(mx, new_v))
        
        mutated['lookbacks']['macd_s'] = mutated['lookbacks']['macd_f'] + 1
        return mutated

    def run(self):
        best_overall_fitness = -9999
        best_overall_genome = None
        max_workers = max(1, os.cpu_count() - 4)
        print(f"Starting Evolution V6 Balancer: {self.generations} generations, pop {self.population_size}, ablation {'ON' if self.use_ablation else 'OFF'}, mutation {self.mutation_rate:.2f}")
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers, initializer=_init_worker, initargs=(self.cache_file,)) as executor:
            for gen in range(self.generations):
                start_time = time.time()
                futures = [executor.submit(_evaluate_genome_worker, g) for g in self.population]
                scored = [f.result() for f in concurrent.futures.as_completed(futures)]
                scored.sort(key=lambda x: x[0], reverse=True)
                best_fit, best_genome, best_metrics = scored[0]
                
                if best_fit > best_overall_fitness:
                    best_overall_fitness = best_fit
                    best_overall_genome = best_genome
                    vault_dir = "champions/v6_balancer/vault"
                    if not os.path.exists(vault_dir): os.makedirs(vault_dir)
                    c, d = best_metrics['cagr']*100, best_metrics['max_dd']*100
                    with open(f"{vault_dir}/v6b_cagr_{c:.2f}_dd_{d:.2f}.json", "w") as f:
                        json.dump(best_genome, f, indent=2)
                
                elapsed = time.time() - start_time
                print(f"V6-Bal  Gen {gen+1:02d} | Fit: {best_fit:6.2f} | CAGR: {best_metrics['cagr']*100:6.2f}% | MaxDD: {best_metrics['max_dd']*100:6.2f}% | Time: {elapsed:.1f}s")
                
                elites = [x[1] for x in scored[:max(2, int(self.population_size * 0.2))]]
                new_pop = list(elites)
                while len(new_pop) < self.population_size:
                    new_pop.append(self._mutate(self._crossover(random.choice(elites), random.choice(elites))))
                self.population = new_pop

        save_path = "champions/v6_balancer/genome.json"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w") as f: json.dump(best_overall_genome, f, indent=2)
        return best_overall_genome
