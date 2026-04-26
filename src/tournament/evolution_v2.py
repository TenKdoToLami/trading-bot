import random
import json
import concurrent.futures
import time
import os

from strategies.genome_v2_strategy import GenomeV2Strategy
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data


# ──────────────────────────────────────────────────────
# Worker-Local Data
# ──────────────────────────────────────────────────────

_worker_price_data = None
_worker_dates = None

def _init_worker(cache_file):
    global _worker_price_data, _worker_dates
    import pandas as pd
    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_price_data = df[['open', 'high', 'low', 'close', 'volume']].to_dict('records')
    _worker_dates = df.index


def _evaluate_genome_worker(genome):
    res = _execute_simulation(
        strategy_type=GenomeV2Strategy,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome}
    )
    metrics = res['metrics']
    # Fitness = CAGR, penalize blowouts
    fitness = metrics['cagr'] * 100 if metrics['max_dd'] > -0.98 else -9999
    return fitness, genome, metrics


class EvolutionEngineV2:
    """
    Genetic Algorithm Engine for Genome V2 (Multi-Brain Architecture).
    """
    def __init__(self, population_size=50, generations=20, mutation_rate=0.15, seed_vault=None):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']
        self.brains = ['panic', '3x', '2x', '1x']
        
        print("Loading master data (SPY + Macro) for evolution v2...")
        self.data = load_spy_data("1993-01-01", force_refresh=False)
        from src.helpers.data_provider import CACHE_FILE
        self.cache_file = CACHE_FILE
        
        self.population = [self._random_genome() for _ in range(self.population_size)]

    def _random_genome(self):
        genome = {}
        for b in self.brains:
            genome[b] = {
                'w': {k: random.uniform(-2, 2) for k in self.indicators},
                'a': {k: random.random() > 0.3 for k in self.indicators},
                't': random.uniform(-1.0, 1.0)
            }
        genome['lock_days'] = random.uniform(0, 15)
        return genome

    def _crossover(self, p1, p2):
        child = {}
        for b in self.brains:
            child[b] = {
                'w': {}, 'a': {}, 't': p1[b]['t'] if random.random() > 0.5 else p2[b]['t']
            }
            for k in self.indicators:
                child[b]['w'][k] = p1[b]['w'][k] if random.random() > 0.5 else p2[b]['w'][k]
                child[b]['a'][k] = p1[b]['a'][k] if random.random() > 0.5 else p2[b]['a'][k]
        
        child['lock_days'] = p1['lock_days'] if random.random() > 0.5 else p2['lock_days']
        return child

    def _mutate(self, genome):
        mutated = {}
        for b in self.brains:
            mutated[b] = {'w': {}, 'a': {}, 't': genome[b]['t']}
            if random.random() < self.mutation_rate:
                mutated[b]['t'] += random.gauss(0, 0.2)
            
            for k in self.indicators:
                # Mutate weight
                w = genome[b]['w'][k]
                if random.random() < self.mutation_rate:
                    mutated[b]['w'][k] = w + random.gauss(0, 0.5)
                else:
                    mutated[b]['w'][k] = w
                
                # Mutate active status
                a = genome[b]['a'][k]
                if random.random() < 0.05: # 5% ablation flip
                    mutated[b]['a'][k] = not a
                else:
                    mutated[b]['a'][k] = a
                    
        mutated['lock_days'] = genome['lock_days']
        if random.random() < self.mutation_rate:
            mutated['lock_days'] = max(0, min(20, mutated['lock_days'] + random.gauss(0, 2)))
            
        return mutated

    def run(self):
        best_overall_fitness = -9999
        best_overall_metrics = None
        best_overall_genome = None

        print(f"Starting Evolution V2: {self.generations} generations, pop {self.population_size}")
        
        with concurrent.futures.ProcessPoolExecutor(initializer=_init_worker, initargs=(self.cache_file,)) as executor:
            for gen in range(self.generations):
                start_time = time.time()
                
                futures = [executor.submit(_evaluate_genome_worker, g) for g in self.population]
                scored = [f.result() for f in concurrent.futures.as_completed(futures)]
                scored.sort(key=lambda x: x[0], reverse=True)
                
                best_fit, best_genome, best_metrics = scored[0]
                if best_fit > best_overall_fitness:
                    best_overall_fitness = best_fit
                    best_overall_genome = best_genome
                    best_overall_metrics = best_metrics
                    
                    # Save to Vault V2
                    vault_dir = "vault_v2"
                    if not os.path.exists(vault_dir): os.makedirs(vault_dir)
                    c, d = best_metrics['cagr']*100, best_metrics['max_dd']*100
                    with open(f"{vault_dir}/v2_cagr_{c:.2f}_dd_{d:.2f}.json", "w") as f:
                        json.dump(best_genome, f, indent=2)

                elapsed = time.time() - start_time
                print(f"V2 Gen {gen+1:02d} | Fit: {best_fit:6.2f} | CAGR: {best_metrics['cagr']*100:6.2f}% | MaxDD: {best_metrics['max_dd']*100:6.2f}% | Time: {elapsed:.1f}s")
                
                elites = [x[1] for x in scored[:max(2, int(self.population_size * 0.2))]]
                new_pop = list(elites)
                while len(new_pop) < self.population_size:
                    child = self._mutate(self._crossover(random.choice(elites), random.choice(elites)))
                    new_pop.append(child)
                self.population = new_pop

        with open("best_genome_v2.json", "w") as f:
            json.dump(best_overall_genome, f, indent=2)
        print(f"\nEvolution V2 Complete. Best CAGR: {best_overall_metrics['cagr']*100:.2f}%")
        return best_overall_genome
