from src.tournament.evolution_registry import register_evolution
import random
import json
import concurrent.futures
import time
import os
import numpy as np
from tqdm import tqdm
from strategies.genome_v4_chameleon import ChameleonV4
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data, CACHE_FILE

# --- GLOBAL WORKER STATE ---
_worker_price_data = None
_worker_dates = None
_worker_features = None

def _init_worker(cache_file):
    global _worker_price_data, _worker_dates, _worker_features
    import pandas as pd
    from contextlib import redirect_stdout
    from src.helpers.indicators import linear_regression_slope

    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            _worker_dates = [str(d.date()) for d in df.index]
            _worker_price_data = df.to_dict('records')
            
            features = {}
            for p in range(50, 301, 1): features[f"sma_{p}"] = df['close'].rolling(p).mean().values
            for p in range(10, 101, 1): features[f"vix_ema_{p}"] = df['vix'].ewm(span=p, adjust=False).mean().values
            for p in range(10, 61, 2): features[f"slope_{p}"] = np.array([linear_regression_slope(df['close'].iloc[max(0, i-p+1):i+1].tolist(), p) for i in range(len(df))])
            for p in range(2, 31, 1):
                deltas = df['close'].diff()
                gain, loss = (deltas.where(deltas > 0, 0)).rolling(window=p).mean(), (-deltas.where(deltas < 0, 0)).rolling(window=p).mean()
                rs = gain / loss
                features[f"rsi_{p}"] = (100 - (100 / (1 + rs))).values
            _worker_features = features

def _evaluate_v4c_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            lite_res = _execute_simulation(strategy_type=ChameleonV4, price_data_list=_worker_price_data[-1000:], dates=_worker_dates[-1000:], strategy_kwargs={'genome': genome, 'precalculated_features': _worker_features, 'index_offset': len(_worker_price_data)-1000})
            if lite_res['metrics']['cagr'] <= 0: return -500.0, lite_res['metrics'], genome
            res = _execute_simulation(strategy_type=ChameleonV4, price_data_list=_worker_price_data, dates=_worker_dates, strategy_kwargs={'genome': genome, 'precalculated_features': _worker_features, 'index_offset': 0})
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    fitness = cagr_pct - (dd_pct * 0.15)
    if dd_pct >= 95.0: fitness -= 1000
    return fitness, metrics, genome

@register_evolution("v4_chameleon")
class EvolutionEngineV4:
    def __init__(self, population_size=100, generations=50, mutation_rate=0.2, seed_vault=None, use_ablation=False, min_cagr=0.0):
        self.pop_size, self.generations, self.mut_rate = population_size, generations, mutation_rate
        self.use_ablation, self.min_cagr = use_ablation, min_cagr
        self.bounds = {"vix_ema": (10, 100), "vol_stretch": (1.0, 3.0), "mom_period": (50, 300), "slope_period": (10, 60), "slope_threshold": (-1.0, 1.0), "rsi_period": (2, 30), "rsi_entry": (5, 45), "rsi_exit": (60, 95), "lev_bull": (1.0, 3.0), "lev_calm": (0.0, 3.0), "lev_stress": (0.0, 2.0), "lev_panic": (0.0, 1.0)}
        self.population = [self._random_genome() for _ in range(self.pop_size)]
        self._best_seen = {"cagr": 0, "dd": 100}

    def _random_genome(self):
        genome = {k: random.uniform(mn, mx) if isinstance(mn, float) else random.randint(mn, mx) for k, (mn, mx) in self.bounds.items()}
        genome['a'] = {bit: random.random() > 0.4 for bit in ['vix', 'mom', 'rsi', 'slope']}
        genome['version'] = 'v4_chameleon'
        return genome

    def _mutate(self, genome):
        mut = json.loads(json.dumps(genome))
        for k, (mn, mx) in self.bounds.items():
            if random.random() < self.mut_rate:
                if isinstance(mn, float): mut[k] = max(mn, min(mx, mut[k] + random.gauss(0, (mx-mn)*0.1)))
                else: mut[k] = max(mn, min(mx, mut[k] + random.randint(-5, 5)))
        if self.use_ablation:
            for bit in mut['a']:
                if random.random() < self.mut_rate: mut['a'][bit] = not mut['a'][bit]
        return mut

    def run(self):
        vault_dir = "champions/v4_chameleon/vault"
        os.makedirs(vault_dir, exist_ok=True)
        print(f"Starting V4C Evolution: {self.generations} gens, pop {self.pop_size}, mut {self.mut_rate:.2f}")
        print(f"{'Gen':<4} | {'Fit':<7} | {'CAGR':<8} | {'DD':<7} | {'Trades':<6} | {'Time':<5}")
        print("-" * 60)

        with concurrent.futures.ProcessPoolExecutor(max_workers=self.workers, initializer=_init_worker, initargs=(CACHE_FILE,)) as executor:
            for gen in range(self.generations):
                start_time = time.time()
                futures = [executor.submit(_evaluate_v4c_worker, g) for g in self.population]
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
                    v_path = os.path.join(vault_dir, f"v4c_cagr_{cagr:.1f}_dd_{dd:.1f}.json")
                    with open(v_path, 'w') as f: json.dump(best_g, f, indent=4)
                
                elites = [x[2] for x in scored[:max(2, self.pop_size // 5)]]
                self.population = elites + [self._mutate(random.choice(elites)) for _ in range(self.pop_size - len(elites))]
        return scored[0][2]
