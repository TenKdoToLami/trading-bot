from src.tournament.evolution_registry import register_evolution
import os
import json
import random
import numpy as np
import concurrent.futures
import time
from copy import deepcopy
from tqdm import tqdm
from strategies.genome_v9_confidence import GenomeV9Confidence
from src.tournament.runner import TournamentRunner, _execute_simulation

# --- GLOBAL WORKER STATE ---
_worker_price_data = None
_worker_dates = None

def _init_worker(cache_file):
    global _worker_price_data, _worker_dates
    import pandas as pd
    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_dates = df.index
    _worker_price_data = df[['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve']].to_dict('records')

def _evaluate_v9_worker(genome):
    import sys
    import os
    from contextlib import redirect_stdout
    
    # Silence all worker output
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=GenomeV9Confidence,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome}
            )
            
    metrics = res['metrics']
    cagr_pct = metrics['cagr'] * 100
    dd_pct = abs(metrics['max_dd']) * 100
    trades = metrics['num_rebalances']
    
    # Standard V9/V4 Fitness: CAGR % - (MaxDD % * 0.15)
    fitness = cagr_pct - (dd_pct * 0.15)
    
    if dd_pct >= 95.0: fitness -= 1000
    if trades == 0: fitness -= 2000
    
    return fitness, metrics, genome

@register_evolution("v9_confidence")
class EvolutionEngineV9Confidence:
    def __init__(self, population_size=100, generations=50, mutation_rate=0.2, seed_vault=None, use_ablation=False, min_cagr=20.0):
        self.pop_size = population_size
        self.generations = generations
        self.mut_rate = mutation_rate
        self.use_ablation = use_ablation
        self.min_cagr = min_cagr
        self.lb_bounds = {
            'sma': (20, 300), 'ema': (10, 200), 'rsi': (5, 50), 'macd_f': (5, 30),
            'macd_s': (15, 60), 'adx': (5, 50), 'trix': (5, 50), 'slope': (5, 50),
            'vol': (5, 60), 'atr': (5, 50), 'mfi': (5, 60), 'bb': (5, 60)
        }
        
        self.population = []
        if seed_vault and os.path.exists(seed_vault):
            self._load_seeds(seed_vault)

        while len(self.population) < self.pop_size:
            self.population.append(self._random_genome())
            
        self._best_seen = {"cagr": 0, "dd": 100}

    def _load_seeds(self, seed_vault):
        vault_files = [f for f in os.listdir(seed_vault) if f.endswith(".json")]
        for f in vault_files:
            with open(os.path.join(seed_vault, f), "r") as jf:
                try:
                    g = json.load(jf)
                    if 'layers' in g:
                        g['version'] = 'v9_confidence'
                        self.population.append(g)
                except: continue
        print(f"  SUCCESS: Injected {len(self.population)} seeds for V9 evolution.")

    def _random_genome(self):
        layers = []
        layers.append({'w': (np.random.randn(13, 24) * 0.8).tolist(), 'b': (np.random.randn(24) * 0.2).tolist()})
        layers.append({'w': np.random.uniform(-3, 3, (24, 4)).tolist(), 'b': np.random.uniform(-0.2, 0.2, 4).tolist()})
        return {
            'version': 'v9_confidence', 'layers': layers,
            'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()},
            'hysteresis': random.uniform(0.01, 0.6), 'lock_days': random.uniform(1, 20), 'smoothing': random.uniform(0.1, 0.9)
        }

    def _mutate(self, genome):
        mutated = json.loads(json.dumps(genome))
        for layer in mutated['layers']:
            w, b = np.array(layer['w']), np.array(layer['b'])
            if random.random() < self.mut_rate:
                w += np.random.normal(0, 0.05, w.shape)
                b += np.random.normal(0, 0.02, b.shape)
            if self.use_ablation and random.random() < 0.1:
                w[random.randint(0, w.shape[0] - 1), :] = 0.0
            layer['w'], layer['b'] = w.tolist(), b.tolist()

        for k, v in mutated['lookbacks'].items():
            if random.random() < self.mut_rate:
                mn, mx = self.lb_bounds[k]
                mutated['lookbacks'][k] = max(mn, min(mx, v + int(random.gauss(0, (mx-mn)*0.1))))
        
        if random.random() < self.mut_rate: mutated['hysteresis'] = max(0.005, min(0.8, mutated['hysteresis'] + random.gauss(0, 0.05)))
        if random.random() < self.mut_rate: mutated['lock_days'] = max(1, min(30, mutated['lock_days'] + random.gauss(0, 2)))
        if random.random() < self.mut_rate: mutated['smoothing'] = max(0.05, min(0.98, mutated['smoothing'] + random.gauss(0, 0.1)))
        return mutated

    def run(self):
        os.makedirs("champions/v9_confidence/vault", exist_ok=True)
        from src.helpers.data_provider import CACHE_FILE
        
        print(f"Starting V9 Evolution: {self.generations} gens, pop {self.pop_size}, mut {self.mut_rate:.2f}")
        print(f"{'Gen':<4} | {'Fit':<7} | {'CAGR':<8} | {'DD':<7} | {'Trades':<6} | {'Hyst':<5} | {'Time':<5}")
        print("-" * 65)

        with concurrent.futures.ProcessPoolExecutor(initializer=_init_worker, initargs=(CACHE_FILE,)) as executor:
            for gen in range(self.generations):
                start_time = time.time()
                futures = [executor.submit(_evaluate_v9_worker, g) for g in self.population]
                
                scored_pop = []
                for f in tqdm(concurrent.futures.as_completed(futures), total=self.pop_size, desc=f"G{gen+1}", leave=False):
                    try: scored_pop.append(f.result())
                    except Exception as e: print(f"\nWorker Error: {e}")

                scored_pop.sort(key=lambda x: x[0], reverse=True)
                best_fit, best_stats, best_genome = scored_pop[0]
                elapsed = time.time() - start_time

                # Print clean summary
                hyst = best_genome['hysteresis']
                print(f"{gen+1:02d}  | {best_fit:7.1f} | {best_stats['cagr']*100:7.2f}% | {abs(best_stats['max_dd'])*100:6.1f}% | {best_stats['num_rebalances']:6.0f} | {hyst:4.2f} | {elapsed:4.1f}s")

                # Smart Vaulting
                cagr, dd = best_stats['cagr'] * 100, abs(best_stats['max_dd']) * 100
                if cagr > (self._best_seen["cagr"] + 0.1) or dd < (self._best_seen["dd"] - 0.5):
                    self._best_seen["cagr"], self._best_seen["dd"] = max(cagr, self._best_seen["cagr"]), min(dd, self._best_seen["dd"])
                    v_path = os.path.join("champions/v9_confidence/vault", f"v9c_cagr_{cagr:.1f}_dd_{dd:.1f}.json")
                    with open(v_path, 'w') as f: json.dump(best_genome, f, indent=4)

                # Selection
                elites = [x[2] for x in scored_pop[:max(2, self.pop_size // 5)]]
                new_pop = list(elites)
                while len(new_pop) < self.pop_size:
                    new_pop.append(self._mutate(random.choice(elites)))
                self.population = new_pop
        return scored_pop[0][2]
