from src.tournament.evolution_registry import register_evolution
import os
import json
import random
import numpy as np
import concurrent.futures
import time
from copy import deepcopy
from tqdm import tqdm
from strategies.genome_v10_expert import GenomeV10Expert
from src.tournament.runner import TournamentRunner, _execute_simulation

# --- GLOBAL WORKER STATE ---
_worker_price_data = None
_worker_dates = None
_worker_profile_path = None

def _init_worker(cache_file, profile_path):
    global _worker_price_data, _worker_dates, _worker_profile_path
    import pandas as pd
    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_dates = df.index
    _worker_price_data = df[['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve']].to_dict('records')
    _worker_profile_path = profile_path

def _evaluate_v10_worker(genome):
    import sys
    import os
    from contextlib import redirect_stdout
    
    # Silence all worker output
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=GenomeV10Expert,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome, 'profile_path': _worker_profile_path}
            )
            
    metrics = res['metrics']
    cagr_pct = metrics['cagr'] * 100
    dd_pct = abs(metrics['max_dd']) * 100
    trades = metrics['num_rebalances']
    
    # Standard V9/V4 Fitness
    fitness = cagr_pct - (dd_pct * 0.15)
    
    if dd_pct >= 95.0: fitness -= 1000
    if trades == 0: fitness -= 2000
    
    return fitness, metrics, genome

@register_evolution("v10_expert")
class EvolutionEngineV10Expert:
    def __init__(self, population_size=100, generations=50, mutation_rate=0.2, seed_vault=None, use_ablation=False, min_cagr=0.0, workers=None, **kwargs):
        self.workers = workers or os.cpu_count()
        self.use_ablation = use_ablation
        self.data_path = "data/history_SPY.csv"
        self.profile_path = "champions/v10_alpha/indicator_profiles.json"
        self.pop_size = population_size
        self.generations = generations
        self.mut_rate = mutation_rate
        self.seed_vault = seed_vault
        self.min_cagr = min_cagr
        
        with open(self.profile_path, 'r') as f:
            self.profile_data = json.load(f)['profiles']
        self.expert_keys = sorted(list(self.profile_data.keys()))
        self.num_experts = len(self.expert_keys)
        
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
            self.population.append(self._create_random_genome())
        self.population = self.population[:self.pop_size]
        
        self.best_fitness = -float('inf')
        self._best_seen = {"cagr": 0, "dd": 100}

    def _create_random_genome(self):
        w_a = np.random.uniform(0, 1, (self.num_experts, 1)).tolist()
        w_b = np.random.uniform(-1, 1, (self.num_experts, 1)).tolist()
        w_c = np.random.uniform(-1, 1, (3, 4)).tolist()
        b_c = [-1.0, 1.0, 0.0, -1.0]
        
        return {
            'brain_a': {'w': w_a, 'b': [0.0]},
            'brain_b': {'w': w_b, 'b': [0.0]},
            'brain_c': {'w': w_c, 'b': b_c},
            'overrides': {'bear_veto_threshold': random.uniform(0.7, 0.95)},
            'indicator_profiles': self.profile_data,
            'version': 'v10_expert'
        }

    def _mutate(self, genome):
        new_genome = deepcopy(genome)
        def _mutate_matrix(m):
            m = np.array(m)
            mask = np.random.rand(*m.shape) < self.mut_rate
            m[mask] += np.random.normal(0, 0.1, m[mask].shape)
            return m.tolist()
        new_genome['brain_a']['w'] = _mutate_matrix(new_genome['brain_a']['w'])
        new_genome['brain_b']['w'] = _mutate_matrix(new_genome['brain_b']['w'])
        new_genome['brain_c']['w'] = _mutate_matrix(new_genome['brain_c']['w'])
        if random.random() < self.mut_rate:
            new_genome['overrides']['bear_veto_threshold'] = max(0.1, min(0.99, new_genome['overrides']['bear_veto_threshold'] + random.gauss(0, 0.05)))
        return new_genome

    def run(self):
        vault_path = self.seed_vault or "champions/v10_alpha/vault"
        os.makedirs(vault_path, exist_ok=True)
        from src.helpers.data_provider import CACHE_FILE
        
        print(f"Starting V10 Evolution: {self.generations} gens, pop {self.pop_size}, mut {self.mut_rate:.2f}")
        print(f"{'Gen':<4} | {'Fit':<7} | {'CAGR':<8} | {'DD':<7} | {'Trades':<6} | {'Veto':<5} | {'Time':<5}")
        print("-" * 65)

        with concurrent.futures.ProcessPoolExecutor(max_workers=self.workers, initializer=_init_worker, initargs=(CACHE_FILE, self.profile_path)) as executor:
            for gen in range(self.generations):
                start_time = time.time()
                futures = [executor.submit(_evaluate_v10_worker, g) for g in self.population]
                
                scored_pop = []
                for f in tqdm(concurrent.futures.as_completed(futures), total=self.pop_size, desc=f"G{gen+1}", leave=False):
                    try:
                        res = f.result()
                        scored_pop.append(res)
                    except Exception as e: print(f"\nWorker Error: {e}")

                scored_pop.sort(key=lambda x: x[0], reverse=True)
                best_fit, best_stats, best_genome = scored_pop[0]
                elapsed = time.time() - start_time

                # Print clean summary
                veto = best_genome['overrides']['bear_veto_threshold']
                print(f"{gen+1:02d}  | {best_fit:7.1f} | {best_stats['cagr']*100:7.2f}% | {abs(best_stats['max_dd'])*100:6.1f}% | {best_stats['num_rebalances']:6.0f} | {veto:4.2f} | {elapsed:4.1f}s")

                # Smart Vaulting
                cagr, dd = best_stats['cagr'] * 100, abs(best_stats['max_dd']) * 100
                if cagr >= self.min_cagr and (cagr > (self._best_seen["cagr"] + 0.1) or dd < (self._best_seen["dd"] - 0.5)):
                    self._best_seen["cagr"], self._best_seen["dd"] = max(cagr, self._best_seen["cagr"]), min(dd, self._best_seen["dd"])
                    v_path = os.path.join(vault_path, f"v10_cagr_{cagr:.1f}_dd_{dd:.1f}.json")
                    with open(v_path, 'w') as f: json.dump(best_genome, f, indent=4)

                # Selection
                elites = [x[2] for x in scored_pop[:max(2, self.pop_size // 5)]]
                new_pop = list(elites)
                while len(new_pop) < self.pop_size:
                    new_pop.append(self._mutate(random.choice(elites)))
                self.population = new_pop

        print(f"\nEvolution Complete. Best Fitness: {scored_pop[0][0]:.2f}")
