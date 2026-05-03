from src.tournament.evolution_registry import register_evolution
import random
import json
import concurrent.futures
import time
import os
import numpy as np
from tqdm import tqdm
from strategies.genome_v1_classic import GenomeV1 as GenomeStrategy
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data, CACHE_FILE

# --- GLOBAL WORKER STATE ---
_worker_price_data = None
_worker_dates = None
_worker_nitro_features = None

def _init_worker(cache_file):
    global _worker_price_data, _worker_dates, _worker_nitro_features
    import pandas as pd
    import os
    from contextlib import redirect_stdout
    from src.helpers.indicators import (
        sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility
    )

    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            _worker_price_data = df[['open', 'high', 'low', 'close', 'volume']].to_dict('records')
            _worker_dates = df.index
            
            nitro = {}
            prices, highs, lows = [], [], []
            prev_ema, prev_atr = None, None
            indicator_state = {}
            
            for i in range(len(_worker_price_data)):
                row = _worker_price_data[i]
                date = str(_worker_dates[i].date())
                spy_price = row['close']
                prices.append(spy_price); highs.append(row['high']); lows.append(row['low'])
                
                v_sma = sma(prices, 200)
                v_ema = ema(prices, 50, prev_ema=prev_ema); prev_ema = v_ema
                v_rsi = rsi(prices, 14, state=indicator_state)
                v_macd = macd(prices, 12, 26, state=indicator_state)[0] or 0.0
                v_adx = adx(highs, lows, prices, 14, state=indicator_state)
                v_trix = trix(prices, 15, state=indicator_state)
                v_slope = linear_regression_slope(prices, 20)
                v_vol = realized_volatility(prices, 20)
                v_atr = atr(highs, lows, prices, 14, prev_atr=prev_atr); prev_atr = v_atr

                nitro[date] = {
                    'sma': ((spy_price - v_sma) / v_sma * 5) if v_sma else 0.0,
                    'ema': ((spy_price - v_ema) / v_ema * 10) if v_ema else 0.0,
                    'rsi': ((v_rsi or 50) - 50) / 50.0,
                    'macd': v_macd / spy_price * 100,
                    'adx': ((v_adx or 25) - 25) / 25.0,
                    'trix': v_trix or 0.0,
                    'slope': (v_slope or 0.0) / spy_price * 1000,
                    'vol': (v_vol or 0.15) * 5,
                    'atr': ((v_atr or 0.0) / spy_price) * 50
                }
            _worker_nitro_features = nitro

def _evaluate_v1_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=GenomeStrategy,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome, 'precalculated_features': _worker_nitro_features}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    fitness = cagr_pct - (dd_pct * 0.15)
    if dd_pct >= 95.0: fitness -= 1000
    if metrics['num_rebalances'] == 0: fitness -= 2000
    return fitness, metrics, genome

@register_evolution("v1_classic")
class EvolutionEngineV1Classic:
    def __init__(self, population_size=100, generations=50, mutation_rate=0.2, seed_vault=None, use_ablation=True, min_cagr=0.0, workers=None, **kwargs):
        self.workers = workers or os.cpu_count()
        self.pop_size = population_size
        self.generations = generations
        self.mut_rate = mutation_rate
        self.use_ablation = use_ablation
        self.min_cagr = min_cagr
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr']
        self.population = []
        
        # Seeding ONLY occurs if seed_vault is provided
        if seed_vault:
            # 1. Try parent genome
            parent_genome = os.path.join(os.path.dirname(seed_vault), "genome.json")
            if os.path.exists(parent_genome):
                try:
                    with open(parent_genome, "r") as f:
                        self.population.append(json.load(f))
                except: pass

            # 2. Load vault seeds sorted by CAGR
            if os.path.exists(seed_vault):
                seeds = []
                for f in os.listdir(seed_vault):
                    if f.endswith(".json"):
                        try:
                            cagr = float(f.split("cagr_")[1].split("_")[0])
                            seeds.append((cagr, f))
                        except:
                            seeds.append((0, f))
                seeds.sort(key=lambda x: x[0], reverse=True)
                for _, f in seeds:
                    if len(self.population) >= self.pop_size: break
                    try:
                        with open(os.path.join(seed_vault, f), "r") as jf:
                            self.population.append(json.load(jf))
                    except: pass

        while len(self.population) < self.pop_size:
            self.population.append(self._random_genome())
        self.population = self.population[:self.pop_size]
        self._best_seen = {"cagr": 0, "dd": 100}

    def _random_genome(self):
        _rw = lambda: {k: random.uniform(-2, 2) for k in self.indicators}
        _ra = lambda: {k: (random.random() > 0.4 if self.use_ablation else True) for k in self.indicators}
        return {
            'panic_weights': _rw(), 'panic_active': _ra(), 'panic_threshold': random.uniform(0.5, 3.0),
            'base_weights': _rw(), 'base_active': _ra(), 'lock_days': random.uniform(0, 20),
            'version': 'v1_classic',
            'base_thresholds': {'tier_3x': 1.0, 'tier_2x': 0.3, 'tier_1x': -0.5}
        }

    def _mutate(self, genome):
        mut = json.loads(json.dumps(genome))
        for g in ['panic', 'base']:
            for k in self.indicators:
                if random.random() < self.mut_rate: mut[f'{g}_weights'][k] += random.gauss(0, 0.5)
                if self.use_ablation and random.random() < 0.05: mut[f'{g}_active'][k] = not mut[f'{g}_active'][k]
        if random.random() < self.mut_rate: mut['panic_threshold'] += random.gauss(0, 0.5)
        if random.random() < self.mut_rate: mut['lock_days'] = max(0, min(20, mut['lock_days'] + random.gauss(0, 2)))
        return mut

    def run(self):
        vault_dir = "champions/v1_classic/vault"
        os.makedirs(vault_dir, exist_ok=True)
        print(f"Starting V1 Evolution: {self.generations} gens, pop {self.pop_size}, mut {self.mut_rate:.2f}")
        print(f"{'Gen':<4} | {'Fit':<7} | {'CAGR':<8} | {'DD':<7} | {'Trades':<6} | {'Time':<5}")
        print("-" * 60)

        with concurrent.futures.ProcessPoolExecutor(max_workers=self.workers, initializer=_init_worker, initargs=(CACHE_FILE,)) as executor:
            for gen in range(self.generations):
                start_time = time.time()
                futures = [executor.submit(_evaluate_v1_worker, g) for g in self.population]
                scored = []
                for f in tqdm(concurrent.futures.as_completed(futures), total=self.pop_size, desc=f"G{gen+1}", leave=False):
                    try: scored.append(f.result())
                    except Exception as e: print(f"\nWorker Error: {e}")
                
                scored.sort(key=lambda x: x[0], reverse=True)
                fit, stats, best_g = scored[0]
                elapsed = time.time() - start_time
                print(f"{gen+1:02d}  | {fit:7.1f} | {stats['cagr']*100:7.2f}% | {abs(stats['max_dd'])*100:6.1f}% | {stats['num_rebalances']:6.0f} | {elapsed:4.1f}s")
                
                cagr, dd = stats['cagr'] * 100, abs(stats['max_dd']) * 100
                if cagr >= self.min_cagr and (cagr > (self._best_seen["cagr"] + 0.1) or dd < (self._best_seen["dd"] - 0.5)):
                    self._best_seen["cagr"], self._best_seen["dd"] = max(cagr, self._best_seen["cagr"]), min(dd, self._best_seen["dd"])
                    v_path = os.path.join(vault_dir, f"v1_cagr_{cagr:.1f}_dd_{dd:.1f}.json")
                    with open(v_path, 'w') as f: json.dump(best_g, f, indent=4)
                
                elites = [x[2] for x in scored[:max(2, self.pop_size // 5)]]
                self.population = elites + [self._mutate(random.choice(elites)) for _ in range(self.pop_size - len(elites))]
        return scored[0][2]
