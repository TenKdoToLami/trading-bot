import random
import json
import concurrent.futures
import time
import os
import pandas as pd

from strategies.genome_v4_chameleon import ChameleonV4
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data

_worker_features = None

def _init_worker(cache_file):
    global _worker_price_data, _worker_dates, _worker_features
    import pandas as pd
    import numpy as np
    from src.helpers.indicators import rsi, linear_regression_slope

    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_dates = [str(d.date()) for d in df.index]
    _worker_price_data = df.to_dict('records')
    
    print(f"  [Worker {os.getpid()}] Pre-calculating V4 Nitro Matrix...")
    features = {}
    
    # 1. SMAs (Mom Period: 50-300)
    for p in range(50, 301, 1):
        features[f"sma_{p}"] = df['close'].rolling(p).mean().values
        
    # 2. VIX EMAs (Vix EMA: 10-100)
    for p in range(10, 101, 1):
        features[f"vix_ema_{p}"] = df['vix'].ewm(span=p, adjust=False).mean().values
        
    # 3. Slopes (Slope Period: 10-60)
    # Slopes are slower, we use a vectorized approach or pre-loop
    for p in range(10, 61, 2): # Stepping by 2 to save time/mem
        slopes = [linear_regression_slope(df['close'].iloc[max(0, i-p+1):i+1].tolist(), p) for i in range(len(df))]
        features[f"slope_{p}"] = np.array(slopes)
        
    # 4. RSIs (RSI Period: 2-30)
    for p in range(2, 31, 1):
        # We'll use a simplified RSI or pre-calculate it
        deltas = df['close'].diff()
        gain = (deltas.where(deltas > 0, 0)).rolling(window=p).mean()
        loss = (-deltas.where(deltas < 0, 0)).rolling(window=p).mean()
        rs = gain / loss
        features[f"rsi_{p}"] = (100 - (100 / (1 + rs))).values

    # Store features as a lookup by date string for the strategy
    # BUT to save memory, we keep them as arrays and the strategy will use the index
    _worker_features = features

def _evaluate_genome_worker(genome):
    # ── STAGE 1: LITE SCREENING (Last ~4 years) ──
    lite_window = 1000
    lite_offset = len(_worker_price_data) - lite_window
    lite_res = _execute_simulation(
        strategy_type=ChameleonV4,
        price_data_list=_worker_price_data[-lite_window:],
        dates=_worker_dates[-lite_window:],
        strategy_kwargs={'genome': genome, 'precalculated_features': _worker_features, 'index_offset': lite_offset}
    )
    if lite_res['metrics']['cagr'] <= 0:
        return -500.0, genome, lite_res['metrics']

    # ── STAGE 2: FULL AUDIT (30+ years) ──
    res = _execute_simulation(
        strategy_type=ChameleonV4,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome, 'precalculated_features': _worker_features, 'index_offset': 0}
    )
    metrics = res['metrics']
    cagr = metrics['cagr'] * 100
    max_dd = abs(metrics['max_dd']) * 100
    
    # ── RISK-ADJUSTED FITNESS (Institutional Standard) ──
    fitness = cagr - (max_dd * 0.15)
    if max_dd >= 95.0: fitness -= 1000
    
    return fitness, genome, metrics

class EvolutionEngineV4:
    def __init__(self, population_size=40, generations=15, mutation_rate=0.2, seed_vault=None, use_ablation=False, min_cagr=0.0):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.use_ablation = use_ablation
        self.min_cagr = min_cagr
        
        self.bounds = {
            "vix_ema": (10, 100),
            "vol_stretch": (1.0, 3.0),
            "mom_period": (50, 300),
            "slope_period": (10, 60),
            "slope_threshold": (-1.0, 1.0),
            "rsi_period": (2, 30),
            "rsi_entry": (5, 45),
            "rsi_exit": (60, 95),
            "lev_bull": (1.0, 3.0),
            "lev_calm": (0.0, 3.0),
            "lev_stress": (0.0, 2.0),
            "lev_panic": (0.0, 1.0)
        }

        print("Loading data for V4 Chameleon evolution...")
        self.data = load_spy_data("1993-01-01")
        from src.helpers.data_provider import CACHE_FILE
        self.cache_file = CACHE_FILE
        
        self.population = []
        if seed_vault and os.path.exists(seed_vault):
            seeds = []
            for f in os.listdir(seed_vault):
                if f.endswith(".json"):
                    with open(os.path.join(seed_vault, f), "r") as jf:
                        try:
                            seeds.append(json.load(jf))
                        except: continue
            
            num_seeds = min(len(seeds), int(self.population_size * 0.5))
            self.population.extend(random.sample(seeds, num_seeds))
            print(f"  Injected {num_seeds} seeds from vault.")

        while len(self.population) < self.population_size:
            self.population.append(self._random_genome())

    def _random_genome(self):
        genome = {k: random.uniform(mn, mx) if isinstance(mn, float) else random.randint(mn, mx) 
                for k, (mn, mx) in self.bounds.items()}
        
        # Default ablation mask (60% ON)
        genome['a'] = {
            'vix': random.random() > 0.4,
            'mom': random.random() > 0.4,
            'rsi': random.random() > 0.4,
            'slope': random.random() > 0.4
        }
        return genome

    def _crossover(self, p1, p2):
        child = {}
        for k in self.bounds:
            child[k] = p1[k] if random.random() > 0.5 else p2[k]
        
        # Crossover for ablation mask
        if 'a' in p1 and 'a' in p2:
            child['a'] = {bit: (p1['a'][bit] if random.random() > 0.5 else p2['a'][bit]) for bit in p1['a']}
        elif 'a' in p1: child['a'] = p1['a'].copy()
        elif 'a' in p2: child['a'] = p2['a'].copy()
            
        return child

    def _mutate(self, genome):
        mutated = dict(genome)
        
        # Retrofit V4.1 keys for legacy seeds
        if "slope_period" not in mutated: mutated["slope_period"] = 20
        if "slope_threshold" not in mutated: mutated["slope_threshold"] = 0.0
        if "rsi_exit" not in mutated: mutated["rsi_exit"] = 85
        if "lev_bull" not in mutated: mutated["lev_bull"] = 3.0
        if "a" not in mutated: mutated["a"] = {"vix": True, "mom": True, "rsi": True, "slope": True}
        if "slope" not in mutated["a"]: mutated["a"]["slope"] = True

        for k, (mn, mx) in self.bounds.items():
            if random.random() < self.mutation_rate:
                if isinstance(mn, float):
                    mutated[k] = max(mn, min(mx, mutated[k] + random.gauss(0, (mx-mn)*0.1)))
                else:
                    mutated[k] = max(mn, min(mx, mutated[k] + random.randint(-5, 5)))
        
        # Mutate the activation bits
        if self.use_ablation:
            for bit in mutated['a']:
                if random.random() < self.mutation_rate:
                    mutated['a'][bit] = not mutated['a'][bit]
                    
        return mutated

    def run(self):
        max_workers = max(1, os.cpu_count() - 2)
        print(f"Starting Evolution V4 Chameleon: {self.generations} generations, pop {self.population_size}, mut {self.mutation_rate:.2f}, ablation {'ON' if self.use_ablation else 'OFF'} (using {max_workers} cores)")
        
        vault_dir = "champions/v4_chameleon/vault"
        os.makedirs(vault_dir, exist_ok=True)

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers, initializer=_init_worker, initargs=(self.cache_file,)) as executor:
            for gen in range(self.generations):
                start_time = time.time()
                futures = [executor.submit(_evaluate_genome_worker, g) for g in self.population]
                scored = [f.result() for f in concurrent.futures.as_completed(futures)]
                scored.sort(key=lambda x: x[0], reverse=True)
                
                best_fit, best_genome, best_metrics = scored[0]
                elapsed = time.time() - start_time
                
                print(f"Gen {gen+1:02d} | Best Fit: {best_fit:6.2f} | CAGR: {best_metrics['cagr']*100:5.2f}% | DD: {best_metrics['max_dd']*100:5.2f}% | Time: {elapsed:.1f}s")
                
                # Save to vault (only if above CAGR threshold)
                if (best_metrics['cagr'] * 100) >= self.min_cagr:
                    v_path = os.path.join(vault_dir, f"v4_cagr_{best_metrics['cagr']*100:.2f}_dd_{abs(best_metrics['max_dd']*100):.2f}.json")
                    with open(v_path, 'w') as f:
                        json.dump(best_genome, f, indent=4)
                else:
                    print(f"  [SKIPPED] CAGR {best_metrics['cagr']*100:.2f}% < {self.min_cagr}% (Vault not updated)")

                # Selection
                elites = [x[1] for x in scored[:max(2, int(self.population_size * 0.2))]]
                new_pop = list(elites)
                while len(new_pop) < self.population_size:
                    p1, p2 = random.choice(elites), random.choice(elites)
                    child = self._crossover(p1, p2)
                    new_pop.append(self._mutate(child))
                
                self.population = new_pop
                best_overall_genome = best_genome

        return best_overall_genome
