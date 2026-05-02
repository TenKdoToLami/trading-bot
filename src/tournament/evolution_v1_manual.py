import random
import json
import concurrent.futures
import time
import os
import numpy as np
from tqdm import tqdm
from strategies.genome_v1_manual import ManualV1
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

def _evaluate_v1m_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=ManualV1,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    fitness = cagr_pct - (dd_pct * 0.15)
    if dd_pct >= 95.0: fitness -= 1000
    if metrics['num_rebalances'] == 0: fitness -= 2000
    return fitness, metrics, genome

class EvolutionEngineV1Manual:
    def __init__(self, population_size=100, generations=50, mutation_rate=0.2, seed_vault=None):
        self.pop_size, self.generations, self.mut_rate = population_size, generations, mutation_rate
        self.population = [self._random_genome() for _ in range(self.pop_size)]
        
        if seed_vault and os.path.exists(seed_vault):
            for f in os.listdir(seed_vault):
                if f.endswith(".json"):
                    with open(os.path.join(seed_vault, f), "r") as jf:
                        self.population.append(json.load(jf))
        
        while len(self.population) < self.pop_size:
            self.population.append(self._random_genome())
        self.population = self.population[:self.pop_size]
        self._best_seen = {"cagr": 0, "dd": 100}

    def _random_genome(self):
        return {
            "sma": random.randint(50, 400),
            "min_b_days": random.randint(1, 20),
            "bounds_p": sorted([random.uniform(10, 30), random.uniform(30, 50), random.uniform(50, 80)]),
            "weights_p": [[random.random(), random.random(), random.random()] for _ in range(4)],
            "version": 1
        }

    def _mutate(self, genome):
        mut = json.loads(json.dumps(genome))
        if random.random() < self.mut_rate: mut['sma'] = max(50, min(500, mut['sma'] + int(random.gauss(0, 20))))
        if random.random() < self.mut_rate: mut['min_b_days'] = max(1, min(60, mut['min_b_days'] + int(random.gauss(0, 2))))
        if random.random() < self.mut_rate: 
            mut['bounds_p'] = sorted([max(5, min(100, b + random.gauss(0, 5))) for b in mut['bounds_p']])
        for i in range(len(mut['weights_p'])):
            for j in range(len(mut['weights_p'][i])):
                if random.random() < self.mut_rate: mut['weights_p'][i][j] = max(0, min(1.0, mut['weights_p'][i][j] + random.gauss(0, 0.1)))
        return mut

    def run(self):
        vault_dir = "champions/v1_manual/vault"
        os.makedirs(vault_dir, exist_ok=True)
        print(f"Starting V1 Manual Evolution: {self.generations} gens, pop {self.pop_size}, mut {self.mut_rate:.2f}")
        print(f"{'Gen':<4} | {'Fit':<7} | {'CAGR':<8} | {'DD':<7} | {'Trades':<6} | {'Time':<5}")
        print("-" * 60)

        with concurrent.futures.ProcessPoolExecutor(initializer=_init_worker, initargs=(CACHE_FILE,)) as executor:
            for gen in range(self.generations):
                start_time = time.time()
                futures = [executor.submit(_evaluate_v1m_worker, g) for g in self.population]
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
                    v_path = os.path.join(vault_dir, f"v1m_cagr_{cagr:.1f}_dd_{dd:.1f}.json")
                    with open(v_path, 'w') as f: json.dump(best_g, f, indent=4)
                
                elites = [x[2] for x in scored[:max(2, self.pop_size // 5)]]
                self.population = elites + [self._mutate(random.choice(elites)) for _ in range(self.pop_size - len(elites))]
        return scored[0][2]
