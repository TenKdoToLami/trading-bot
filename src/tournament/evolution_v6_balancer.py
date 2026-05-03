import random
import json
import concurrent.futures
import time
import os
import numpy as np
from tqdm import tqdm
from strategies.genome_v6_balancer import GenomeV6
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

def _evaluate_v6b_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=GenomeV6,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    fitness = cagr_pct - (dd_pct * 0.15)
    if dd_pct >= 95.0: fitness -= 1000
    return fitness, metrics, genome

class EvolutionEngineV6:
    def __init__(self, population_size=100, generations=50, mutation_rate=0.2, seed_vault=None, use_ablation=True, min_cagr=0.0):
        self.pop_size, self.generations, self.mut_rate = population_size, generations, mutation_rate
        self.use_ablation, self.min_cagr = use_ablation, min_cagr
        self.seed_vault = seed_vault
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc', 'mfi', 'bbw']
        self.brains = ['cash', '1x', '2x', '3x']
        self.lb_bounds = {'sma': (20, 300), 'ema': (10, 200), 'rsi': (5, 50), 'macd_f': (5, 30), 'macd_s': (15, 60), 'adx': (5, 50), 'trix': (5, 50), 'slope': (5, 50), 'vol': (5, 60), 'atr': (5, 50), 'mfi': (5, 60), 'bbw': (5, 60)}
        
        self.population = []
        if self.seed_vault and os.path.exists(self.seed_vault):
            main_champ = os.path.join(os.path.dirname(self.seed_vault), "genome.json")
            if os.path.exists(main_champ):
                try:
                    with open(main_champ, "r") as f:
                        self.population.append(json.load(f))
                except: pass
            
            files = [f for f in os.listdir(self.seed_vault) if f.endswith(".json")]
            seeds = []
            for f in files:
                try:
                    cagr = float(f.split("cagr_")[1].split("_")[0])
                    seeds.append((cagr, f))
                except: seeds.append((0, f))
            seeds.sort(key=lambda x: x[0], reverse=True)
            for _, f in seeds:
                if len(self.population) >= self.pop_size: break
                try:
                    with open(os.path.join(self.seed_vault, f), "r") as jf:
                        self.population.append(json.load(jf))
                except: pass
            print(f"  SUCCESS: Injected {len(self.population)} seeds from {self.seed_vault}")

        while len(self.population) < self.pop_size:
            self.population.append(self._random_genome())

        self._best_seen = {"cagr": 0, "dd": 100}

    def _random_genome(self):
        genome = {'brains': {b: {'w': {k: random.uniform(-4, 4) for k in self.indicators}, 'a': {k: (random.random() > 0.4 if self.use_ablation else True) for k in self.indicators}, 't': random.uniform(-1.0, 3.0)} for b in self.brains}, 'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()}, 'temp': random.uniform(0.1, 1.5), 'lock_days': random.uniform(1, 10), 'version': 'v6_balancer'}
        return genome

    def _mutate(self, genome):
        mut = json.loads(json.dumps(genome))
        for k, v in mut['lookbacks'].items():
            if random.random() < self.mut_rate: mn, mx = self.lb_bounds[k]; mut['lookbacks'][k] = max(mn, min(mx, v + int(random.gauss(0, (mx-mn)*0.1))))
        for b in self.brains:
            for k, v in mut['brains'][b]['w'].items():
                if random.random() < self.mut_rate: mut['brains'][b]['w'][k] += random.gauss(0, 0.8)
                if self.use_ablation and random.random() < 0.05: mut['brains'][b]['a'][k] = not mut['brains'][b]['a'][k]
            if random.random() < self.mut_rate: mut['brains'][b]['t'] += random.gauss(0, 0.5)
        if random.random() < self.mut_rate: mut['temp'] = max(0.1, min(3.0, mut['temp'] + random.gauss(0, 0.1)))
        if random.random() < self.mut_rate: mut['lock_days'] = max(1, min(20, mut['lock_days'] + random.gauss(0, 2)))
        return mut

    def run(self):
        vault_dir = "champions/v6_balancer/vault"
        os.makedirs(vault_dir, exist_ok=True)
        print(f"Starting V6B Evolution: {self.generations} gens, pop {self.pop_size}, mut {self.mut_rate:.2f}")
        print(f"{'Gen':<4} | {'Fit':<7} | {'CAGR':<8} | {'DD':<7} | {'Trades':<6} | {'Time':<5}")
        print("-" * 60)

        with concurrent.futures.ProcessPoolExecutor(initializer=_init_worker, initargs=(CACHE_FILE,)) as executor:
            for gen in range(self.generations):
                start_time = time.time()
                futures = [executor.submit(_evaluate_v6b_worker, g) for g in self.population]
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
                    v_path = os.path.join(vault_dir, f"v6b_cagr_{cagr:.1f}_dd_{dd:.1f}.json")
                    with open(v_path, 'w') as f: json.dump(best_g, f, indent=4)
                
                elites = [x[2] for x in scored[:max(2, self.pop_size // 5)]]
                self.population = elites + [self._mutate(random.choice(elites)) for _ in range(self.pop_size - len(elites))]
        return scored[0][2]
