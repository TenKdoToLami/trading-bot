import random
import json
import concurrent.futures
import time
import os
import pandas as pd

from strategies.genome_v4_chameleon import ChameleonV4
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data

_worker_price_data = None
_worker_dates = None

def _init_worker(cache_file):
    global _worker_price_data, _worker_dates
    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_dates = df.index
    _worker_price_data = df.to_dict('records')

def _evaluate_genome_worker(genome):
    # ── STAGE 1: LITE SCREENING (Last ~4 years) ──
    lite_window = 1000
    lite_res = _execute_simulation(
        strategy_type=ChameleonV4,
        price_data_list=_worker_price_data[-lite_window:],
        dates=_worker_dates[-lite_window:],
        strategy_kwargs={'genome': genome}
    )
    if lite_res['metrics']['cagr'] <= 0:
        return -500.0, genome, lite_res['metrics']

    # ── STAGE 2: FULL AUDIT (30+ years) ──
    res = _execute_simulation(
        strategy_type=ChameleonV4,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome}
    )
    metrics = res['metrics']
    cagr = metrics['cagr'] * 100
    max_dd = abs(metrics['max_dd']) * 100
    
    # ── RISK-ADJUSTED FITNESS (Institutional Standard) ──
    fitness = cagr - (max_dd * 0.15)
    if max_dd >= 95.0: fitness -= 1000
    
    return fitness, genome, metrics

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
            "rsi_period": (2, 30),
            "rsi_entry": (5, 45),
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
        
        if self.use_ablation:
            # 60% chance for an indicator to stay ON by default in a random genome
            genome['a'] = {
                'vix': random.random() > 0.4,
                'mom': random.random() > 0.4,
                'rsi': random.random() > 0.4
            }
        return genome

    def _crossover(self, p1, p2):
        child = {}
        for k in self.bounds:
            child[k] = p1[k] if random.random() > 0.5 else p2[k]
        return child

    def _mutate(self, genome):
        mutated = dict(genome)
        for k, (mn, mx) in self.bounds.items():
            if random.random() < self.mutation_rate:
                if isinstance(mn, float):
                    mutated[k] = max(mn, min(mx, mutated[k] + random.gauss(0, (mx-mn)*0.1)))
                else:
                    mutated[k] = max(mn, min(mx, mutated[k] + random.randint(-5, 5)))
        
        if self.use_ablation:
            if 'a' not in mutated:
                # Retrofit missing mask (default all ON)
                mutated['a'] = {'vix': True, 'mom': True, 'rsi': True}
            
            # Mutate the activation bits
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
