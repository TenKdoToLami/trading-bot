import random
import json
import concurrent.futures
import time
import os
import pandas as pd

from strategies.genome_v6_balancer import GenomeV6
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
    # Turbo I/O
    _worker_price_data = df.to_dict('records')
    print(f"  [Worker {os.getpid()}] V6-Balancer Ready. Min CAGR: {min_cagr:.1f}%")

def _evaluate_genome_worker(genome):
    res = _execute_simulation(
        strategy_type=GenomeV6,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome}
    )
    metrics = res['metrics']
    cagr = metrics['cagr'] * 100
    max_dd = abs(metrics['max_dd']) * 100
    
    # ── RISK-ADJUSTED FITNESS (Institutional Standard) ──
    fitness = cagr - (max_dd * 0.15)
    
    if max_dd >= 95.0: 
        fitness -= 1000
        
    return fitness, genome, metrics

class EvolutionEngineV6:
    def __init__(self, population_size=50, generations=20, mutation_rate=0.2, seed_vault=None, use_ablation=True, min_cagr=0.0):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.use_ablation = use_ablation
        self.min_cagr = min_cagr
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc', 'mfi', 'bbw']
        self.brains = ['cash', '1x', '2x', '3x']
        
        self.lb_bounds = {
            'sma': (20, 300), 'ema': (10, 200), 'rsi': (5, 50), 'macd_f': (5, 30),
            'macd_s': (15, 60), 'adx': (5, 50), 'trix': (5, 50), 'slope': (5, 50),
            'vol': (5, 60), 'atr': (5, 50), 'mfi': (5, 60), 'bbw': (5, 60)
        }

        print("Loading master data for Evolution V6 Balancer...")
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
                            g['version'] = 6.0
                            seeds.append(g)
                        except: continue
            
            num_seeds = min(len(seeds), self.population_size)
            self.population.extend(seeds[:num_seeds])
            print(f"  SUCCESS: Injected {num_seeds} V6 seeds from vault.")

        while len(self.population) < self.population_size:
            self.population.append(self._random_genome())

    def _random_genome(self):
        genome = {
            'brains': {},
            'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()},
            'temp': random.uniform(0.1, 1.5),
            'lock_days': random.uniform(1, 10),
            'version': 6.0
        }
        for b in self.brains:
            genome['brains'][b] = {
                'w': {k: random.uniform(-4, 4) for k in self.indicators},
                'a': {k: (random.random() > 0.4 if self.use_ablation else True) for k in self.indicators},
                't': random.uniform(-1.0, 3.0)
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
                'a': {k: (p1['brains'][b]['a'][k] if random.random() > 0.5 else p2['brains'][b]['a'][k]) for k in self.indicators},
                't': p1['brains'][b]['t'] if random.random() > 0.5 else p2['brains'][b]['t']
            }
        return child

    def _mutate(self, genome):
        mutated = {
            'brains': {},
            'lookbacks': {},
            'temp': max(0.1, min(3.0, genome['temp'] + random.gauss(0, 0.1))) if random.random() < self.mutation_rate else genome['temp'],
            'lock_days': max(1, min(20, genome['lock_days'] + random.gauss(0, 2))) if random.random() < self.mutation_rate else genome['lock_days'],
            'version': 6.0
        }
        for k, v in genome['lookbacks'].items():
            mn, mx = self.lb_bounds[k]
            new_v = v + int(random.gauss(0, (mx-mn)*0.1)) if random.random() < self.mutation_rate else v
            mutated['lookbacks'][k] = max(mn, min(mx, new_v))
            
        for b in self.brains:
            mutated['brains'][b] = {
                'w': {k: (v + random.gauss(0, 0.8) if random.random() < self.mutation_rate else v) for k, v in genome['brains'][b]['w'].items()},
                'a': {k: (not v if random.random() < 0.05 else v) for k, v in genome['brains'][b]['a'].items()},
                't': genome['brains'][b]['t'] + random.gauss(0, 0.5) if random.random() < self.mutation_rate else genome['brains'][b]['t']
            }
            
        return mutated

    def run(self):
        max_workers = max(1, os.cpu_count() - 2)
        print(f"Starting Evolution V6 Balancer: {self.generations} generations, pop {self.population_size}, mut {self.mutation_rate:.2f}, MinCAGR: {self.min_cagr:.1f}%")
        
        vault_dir = "champions/v6_balancer/vault"
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
                    v_path = os.path.join(vault_dir, f"v6b_cagr_{best_metrics['cagr']*100:.2f}_dd_{best_metrics['max_dd']*100:.2f}.json")
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
