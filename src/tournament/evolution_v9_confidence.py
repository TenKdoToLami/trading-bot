import random
import json
import concurrent.futures
import time
import os
import numpy as np
import pandas as pd

from strategies.genome_v9_confidence import GenomeV9Confidence
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
    _worker_price_data = df.to_dict('records')
    print(f"  [Worker {os.getpid()}] V9-Confidence Ready.")

def _evaluate_genome_worker(genome):
    res = _execute_simulation(
        strategy_type=GenomeV9Confidence,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome}
    )
    metrics = res['metrics']
    cagr = metrics['cagr'] * 100
    max_dd = abs(metrics['max_dd']) * 100
    
    trade_count = metrics['num_rebalances']
    
    # Standardized Fitness (V4 Style): Heavy CAGR focus, light DD penalty
    fitness = cagr - (max_dd * 0.15)
    
    if max_dd >= 95.0: 
        fitness -= 1000
    if trade_count == 0:
        fitness -= 2000 
        
    return fitness, genome, metrics

class EvolutionEngineV9Confidence:
    def __init__(self, population_size=50, generations=20, mutation_rate=0.2, seed_vault=None, use_ablation=False, min_cagr=20.0):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.use_ablation = use_ablation
        self.min_cagr = min_cagr
        self.lb_bounds = {
            'sma': (20, 300), 'ema': (10, 200), 'rsi': (5, 50), 'macd_f': (5, 30),
            'macd_s': (15, 60), 'adx': (5, 50), 'trix': (5, 50), 'slope': (5, 50),
            'vol': (5, 60), 'atr': (5, 50), 'mfi': (5, 60), 'bb': (5, 60)
        }

        print("Loading master data for Evolution V9 Confidence...")
        self.data = load_spy_data("1993-01-01")
        from src.helpers.data_provider import CACHE_FILE
        self.cache_file = CACHE_FILE
        
        self.population = []
        if seed_vault and os.path.exists(seed_vault):
            seeds = []
            vault_files = [f for f in os.listdir(seed_vault) if f.endswith(".json")]
            for f in vault_files:
                with open(os.path.join(seed_vault, f), "r") as jf:
                    try:
                        g = json.load(jf)
                        # Adapt V7 genomes to V9 if seeded
                        if 'layers' in g:
                            g['version'] = 9.0
                            g['hysteresis'] = g.get('hysteresis', 0.15)
                            g['smoothing'] = g.get('smoothing', 0.5)
                            seeds.append(g)
                    except: continue
            
            num_seeds = min(len(seeds), self.population_size)
            self.population.extend(seeds[:num_seeds])
            print(f"  SUCCESS: Injected {num_seeds} seeds for V9 evolution.")

        while len(self.population) < self.population_size:
            self.population.append(self._random_genome())

    def _random_genome(self):
        layers = []
        layers.append({
            'w': (np.random.randn(13, 24) * 0.8).tolist(),
            'b': (np.random.randn(24) * 0.2).tolist()
        })
        layers.append({
            'w': np.random.uniform(-3, 3, (24, 4)).tolist(),
            'b': np.random.uniform(-0.2, 0.2, 4).tolist()
        })
        return {
            'version': 9.0,
            'layers': layers,
            'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()},
            'hysteresis': random.uniform(0.01, 0.6),
            'lock_days': random.uniform(1, 20),
            'smoothing': random.uniform(0.1, 0.9)
        }

    def _crossover(self, p1, p2):
        child = {
            'version': 9.0,
            'layers': [],
            'lookbacks': {k: (p1['lookbacks'][k] if random.random() > 0.5 else p2['lookbacks'][k]) for k in self.lb_bounds},
            'hysteresis': p1['hysteresis'] if random.random() > 0.5 else p2['hysteresis'],
            'lock_days': p1['lock_days'] if random.random() > 0.5 else p2['lock_days'],
            'smoothing': p1['smoothing'] if random.random() > 0.5 else p2['smoothing']
        }
        for i in range(len(p1['layers'])):
            if random.random() > 0.5: child['layers'].append(p1['layers'][i])
            else: child['layers'].append(p2['layers'][i])
        return child

    def _mutate(self, genome):
        mutated = json.loads(json.dumps(genome))
        for layer in mutated['layers']:
            w = np.array(layer['w'])
            b = np.array(layer['b'])
            if random.random() < self.mutation_rate:
                w += np.random.normal(0, 0.05, w.shape)
                b += np.random.normal(0, 0.02, b.shape)
            
            # Ablation Logic: Structural Sparsity Pressure
            if self.use_ablation and random.random() < 0.1:
                # Randomly zero out one entire input feature connection set (Ablation)
                input_idx = random.randint(0, w.shape[0] - 1)
                w[input_idx, :] = 0.0
                
            layer['w'] = w.tolist()
            layer['b'] = b.tolist()

        for k, v in mutated['lookbacks'].items():
            if random.random() < self.mutation_rate:
                mn, mx = self.lb_bounds[k]
                new_v = v + int(random.gauss(0, (mx-mn)*0.1))
                mutated['lookbacks'][k] = max(mn, min(mx, new_v))
                
        if random.random() < self.mutation_rate:
            mutated['hysteresis'] = max(0.005, min(0.8, mutated['hysteresis'] + random.gauss(0, 0.05)))
        if random.random() < self.mutation_rate:
            mutated['lock_days'] = max(1, min(30, mutated['lock_days'] + random.gauss(0, 2)))
        if random.random() < self.mutation_rate:
            mutated['smoothing'] = max(0.05, min(0.98, mutated['smoothing'] + random.gauss(0, 0.1)))
            
        return mutated

    def run(self):
        max_workers = max(1, os.cpu_count() - 2)
        print(f"Starting Evolution V9 Confidence: {self.generations} generations, pop {self.population_size}, mut {self.mutation_rate:.2f}, ablation {'ON' if self.use_ablation else 'OFF'}")
        
        vault_dir = "champions/v9_confidence/vault"
        os.makedirs(vault_dir, exist_ok=True)
        best_overall_genome = None

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers, initializer=_init_worker, initargs=(self.cache_file, self.min_cagr)) as executor:
            for gen in range(self.generations):
                start_time = time.time()
                
                payloads = self.population
                futures = [executor.submit(_evaluate_genome_worker, p) for p in payloads]
                scored = [f.result() for f in concurrent.futures.as_completed(futures)]
                scored.sort(key=lambda x: x[0], reverse=True)
                
                best_fit, best_genome, best_metrics = scored[0]
                best_overall_genome = best_genome
                elapsed = time.time() - start_time
                
                print(f"Gen {gen+1:02d} | Fit: {best_fit:6.1f} | CAGR: {best_metrics['cagr']*100:5.2f}% | DD: {best_metrics['max_dd']*100:5.2f}% | Trades: {best_metrics['num_rebalances']:.0f} | Time: {elapsed:.1f}s")
                
                # Save only meaningful "Record Breakers" to the vault
                if not hasattr(self, '_best_seen'): self._best_seen = {"cagr": 0, "dd": 100}
                
                cagr, dd = best_metrics['cagr'] * 100, abs(best_metrics['max_dd']) * 100
                if cagr >= self.min_cagr:
                    is_better_cagr = cagr > (self._best_seen["cagr"] + 0.1)
                    is_better_dd = dd < (self._best_seen["dd"] - 0.5)
                    
                    if is_better_cagr or is_better_dd:
                        v_path = os.path.join(vault_dir, f"v9c_cagr_{cagr:.2f}_dd_{dd:.2f}.json")
                        with open(v_path, 'w') as f:
                            json.dump(best_genome, f, indent=4)
                        # Update records
                        if is_better_cagr: self._best_seen["cagr"] = cagr
                        if is_better_dd: self._best_seen["dd"] = dd
                
                # Selection
                elites = [x[1] for x in scored[:max(2, int(self.population_size * 0.2))]]

                new_pop = list(elites)
                while len(new_pop) < self.population_size:
                    p1, p2 = random.choice(elites), random.choice(elites)
                    child = self._crossover(p1, p2)
                    new_pop.append(self._mutate(child))
                
                self.population = new_pop
        return best_overall_genome
