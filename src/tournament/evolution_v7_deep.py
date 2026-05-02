import random
import json
import concurrent.futures
import time
import os
import numpy as np
from tqdm import tqdm
from strategies.genome_v7_deep import GenomeV7Deep
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data, CACHE_FILE

# --- GLOBAL WORKER STATE ---
_worker_price_data = None
_worker_dates = None

def _init_worker(cache_file):
    global _worker_price_data, _worker_dates
    import pandas as pd
    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_dates = df.index
    _worker_price_data = df.to_dict('records')

def _evaluate_v7d_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=GenomeV7Deep,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    fitness = cagr_pct - (dd_pct * 0.15)
    if dd_pct >= 95.0: fitness -= 1000
    return fitness, metrics, genome

class EvolutionEngineV7:
    def __init__(self, population_size=100, generations=50, mutation_rate=0.2, seed_vault=None, use_ablation=True, min_cagr=0.0):
        self.pop_size, self.generations, self.mut_rate = population_size, generations, mutation_rate
        self.use_ablation, self.min_cagr = use_ablation, min_cagr
        self.lb_bounds = {'sma': (20, 300), 'ema': (10, 200), 'rsi': (5, 50), 'macd_f': (5, 30), 'macd_s': (15, 60), 'adx': (5, 50), 'trix': (5, 50), 'slope': (5, 50), 'vol': (5, 60), 'atr': (5, 50), 'mfi': (5, 60), 'bb': (5, 60)}
        self.population = [self._random_genome() for _ in range(self.pop_size)]
        self._best_seen = {"cagr": 0, "dd": 100}

    def _random_genome(self):
        return {'version': 7.0, 'layers': [{'w': np.random.uniform(-1, 1, (13, 24)).tolist(), 'b': np.random.uniform(-0.1, 0.1, 24).tolist()}, {'w': np.random.uniform(-1, 1, (24, 4)).tolist(), 'b': np.random.uniform(-0.1, 0.1, 4).tolist()}], 'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()}, 'lock_days': random.uniform(1, 10)}

    def _mutate(self, genome):
        mut = json.loads(json.dumps(genome))
        for layer in mut['layers']:
            w, b = np.array(layer['w']), np.array(layer['b'])
            if random.random() < self.mut_rate: w += np.random.normal(0, 0.05, w.shape); b += np.random.normal(0, 0.02, b.shape)
            layer['w'], layer['b'] = w.tolist(), b.tolist()
        for k, v in mut['lookbacks'].items():
            if random.random() < self.mut_rate: mn, mx = self.lb_bounds[k]; mut['lookbacks'][k] = max(mn, min(mx, v + int(random.gauss(0, (mx-mn)*0.1))))
        mut['lock_days'] = max(1, min(14, mut['lock_days'] + random.gauss(0, 1))) if random.random() < self.mut_rate else mut['lock_days']
        return mut

    def run(self):
        vault_dir = "champions/v7_deep/vault"
        os.makedirs(vault_dir, exist_ok=True)
        print(f"Starting V7D Evolution: {self.generations} gens, pop {self.pop_size}, mut {self.mut_rate:.2f}")
        print(f"{'Gen':<4} | {'Fit':<7} | {'CAGR':<8} | {'DD':<7} | {'Trades':<6} | {'Time':<5}")
        print("-" * 60)

        with concurrent.futures.ProcessPoolExecutor(initializer=_init_worker, initargs=(CACHE_FILE,)) as executor:
            for gen in range(self.generations):
                start_time = time.time()
                futures = [executor.submit(_evaluate_v7d_worker, g) for g in self.population]
                scored = []
                for f in tqdm(concurrent.futures.as_completed(futures), total=self.pop_size, desc=f"G{gen+1}", leave=False):
                    try: scored.append(f.result())
                    except Exception as e: print(f"\nWorker Error: {e}")
                
                scored.sort(key=lambda x: x[0], reverse=True)
                fit, stats, best_g = scored[0]
                elapsed = time.time() - start_time
                print(f"{gen+1:02d}  | {fit:7.1f} | {stats['cagr']*100:7.2f}% | {abs(stats['max_dd'])*100:6.1f}% | {stats['num_rebalances']:6.0f} | {elapsed:4.1f}s")
                
                cagr, dd = stats['cagr'] * 100, abs(stats['max_dd']) * 100
                if cagr > (self._best_seen["cagr"] + 0.1) or dd < (self._best_seen["dd"] - 0.5):
                    self._best_seen["cagr"], self._best_seen["dd"] = max(cagr, self._best_seen["cagr"]), min(dd, self._best_seen["dd"])
                    v_path = os.path.join(vault_dir, f"v7d_cagr_{cagr:.1f}_dd_{dd:.1f}.json")
                    with open(v_path, 'w') as f: json.dump(best_g, f, indent=4)
                
                elites = [x[2] for x in scored[:max(2, self.pop_size // 5)]]
                self.population = elites + [self._mutate(random.choice(elites)) for _ in range(self.pop_size - len(elites))]
        return scored[0][2]
