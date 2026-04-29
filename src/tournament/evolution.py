import random
import json
import concurrent.futures
import time
import os

from strategies._genome_strategy import GenomeStrategy
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data


# ──────────────────────────────────────────────────────
# Worker-Local Data (loaded once per process, not serialized)
# ──────────────────────────────────────────────────────

_worker_price_data = None
_worker_dates = None


def _init_worker(cache_file):
    """Called once per worker process to load data into process-local memory."""
    global _worker_price_data, _worker_dates
    import pandas as pd
    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_price_data = df[['open', 'high', 'low', 'close', 'volume']].to_dict('records')
    _worker_dates = df.index


def _evaluate_genome_worker(genome):
    """Runs a full simulation using worker-local data. Only the genome is serialized."""
    res = _execute_simulation(
        strategy_type=GenomeStrategy,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome}
    )
    
    metrics = res['metrics']
    cagr = metrics['cagr'] * 100
    max_dd = abs(metrics['max_dd']) * 100
    
    # Fitness: Pure returns, penalize total blowouts
    if max_dd >= 98.0:
        fitness = -9999
    else:
        fitness = cagr

    return fitness, genome, metrics


class EvolutionEngine:
    """
    Genetic Algorithm Engine to breed the optimal GenomeStrategy.
    
    Optimized for speed:
    - Worker processes load data once via initializer (no cross-process serialization of price data).
    - Persistent process pool across all generations (no respawning overhead).
    - Only the tiny genome dict (~1KB) is sent to each worker.
    """
    def __init__(self, population_size=50, generations=20, mutation_rate=0.15, seed_vault=None):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        
        # Load data once to ensure cache exists
        print("Loading data for evolution...")
        self.data = load_spy_data("1993-01-01", force_refresh=False)
        
        # Resolve the cache file path for workers
        from src.helpers.data_provider import CACHE_FILE
        self.cache_file = CACHE_FILE
        
        # Build initial population (with optional vault seeding)
        seeds = []
        if seed_vault and os.path.isdir(seed_vault):
            seeds = self._load_vault_seeds(seed_vault)
        
        # Cap seeds at 20% of population to preserve diversity
        max_seeds = int(self.population_size * 0.2)
        seeds = seeds[:max_seeds]
        
        if seeds:
            print(f"Seeded {len(seeds)} genomes from vault (max {max_seeds})")
        
        # Fill remaining slots with random genomes
        random_count = self.population_size - len(seeds)
        self.population = seeds + [self._random_genome() for _ in range(random_count)]

    def _load_vault_seeds(self, vault_dir):
        """Load genomes from vault, sorted by CAGR (best first)."""
        import re
        seeds = []
        for filename in os.listdir(vault_dir):
            if not filename.endswith('.json'):
                continue
            filepath = os.path.join(vault_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    genome = json.load(f)
                # Validate minimum structure
                if 'panic_weights' in genome and 'base_weights' in genome:
                    # Extract CAGR from filename for sorting
                    match = re.search(r'cagr_([\d.]+)', filename)
                    cagr = float(match.group(1)) if match else 0.0
                    seeds.append((cagr, genome))
            except Exception:
                continue
        
        # Sort by CAGR descending, return just the genomes
        seeds.sort(key=lambda x: x[0], reverse=True)
        return [g for _, g in seeds]

    def _random_genome(self):
        def _rand_weights():
            return {
                'sma': random.uniform(-2, 2),
                'ema': random.uniform(-2, 2),
                'rsi': random.uniform(-2, 2),
                'macd': random.uniform(-2, 2),
                'adx': random.uniform(-2, 2),
                'trix': random.uniform(-2, 2),
                'slope': random.uniform(-2, 2),
                'vol': random.uniform(-2, 2),
                'atr': random.uniform(-2, 2)
            }
        def _rand_active():
            return {
                'sma': random.random() > 0.5,
                'ema': random.random() > 0.5,
                'rsi': random.random() > 0.5,
                'macd': random.random() > 0.5,
                'adx': random.random() > 0.5,
                'trix': random.random() > 0.5,
                'slope': random.random() > 0.5,
                'vol': random.random() > 0.5,
                'atr': random.random() > 0.5
            }
        
        return {
            'panic_weights': _rand_weights(),
            'panic_active': _rand_active(),
            'panic_threshold': random.uniform(0.5, 3.0),
            'base_weights': _rand_weights(),
            'base_active': _rand_active(),
            'base_thresholds': {
                'tier_3x': random.uniform(0.5, 2.0),
                'tier_2x': random.uniform(0.0, 0.5),
                'tier_1x': random.uniform(-1.0, 0.0)
            },
            'lock_days': random.uniform(0, 20)
        }

    def _crossover(self, p1, p2):
        """Uniform crossover."""
        child = {
            'panic_weights': {},
            'panic_active': {},
            'base_weights': {},
            'base_active': {},
            'base_thresholds': {}
        }
        
        for key in p1['panic_weights']:
            child['panic_weights'][key] = p1['panic_weights'][key] if random.random() > 0.5 else p2['panic_weights'][key]
            child['panic_active'][key] = p1.get('panic_active', {}).get(key, True) if random.random() > 0.5 else p2.get('panic_active', {}).get(key, True)
            child['base_weights'][key] = p1['base_weights'][key] if random.random() > 0.5 else p2['base_weights'][key]
            child['base_active'][key] = p1.get('base_active', {}).get(key, True) if random.random() > 0.5 else p2.get('base_active', {}).get(key, True)
            
        for key in p1['base_thresholds']:
            child['base_thresholds'][key] = p1['base_thresholds'][key] if random.random() > 0.5 else p2['base_thresholds'][key]
            
        child['panic_threshold'] = p1['panic_threshold'] if random.random() > 0.5 else p2['panic_threshold']
        child['lock_days'] = p1['lock_days'] if random.random() > 0.5 else p2['lock_days']
        
        # Repair thresholds to maintain tier_3x > tier_2x > tier_1x
        t = child['base_thresholds']
        ordered = sorted([t['tier_1x'], t['tier_2x'], t['tier_3x']])
        child['base_thresholds'] = {
            'tier_1x': ordered[0],
            'tier_2x': ordered[1],
            'tier_3x': ordered[2]
        }
        return child

    def _mutate(self, genome):
        """Randomly alters genes."""
        mutated = {
            'panic_weights': {},
            'panic_active': {},
            'base_weights': {},
            'base_active': {},
            'base_thresholds': {}
        }
        
        for group in ['panic', 'base']:
            w_group = f"{group}_weights"
            a_group = f"{group}_active"
            for key, val in genome[w_group].items():
                # Mutate weight
                if random.random() < self.mutation_rate:
                    mutated[w_group][key] = val + random.gauss(0, 0.5)
                else:
                    mutated[w_group][key] = val
                    
                # Mutate active mask (Ablation toggle: 5% chance to flip)
                current_active = genome.get(a_group, {}).get(key, True)
                if random.random() < 0.05:
                    mutated[a_group][key] = not current_active
                else:
                    mutated[a_group][key] = current_active
                    
        for key, val in genome['base_thresholds'].items():
            if random.random() < self.mutation_rate:
                mutated['base_thresholds'][key] = val + random.gauss(0, 0.2)
            else:
                mutated['base_thresholds'][key] = val
                
        if random.random() < self.mutation_rate:
            mutated['panic_threshold'] = genome['panic_threshold'] + random.gauss(0, 0.5)
        else:
            mutated['panic_threshold'] = genome['panic_threshold']
            
        if random.random() < self.mutation_rate:
            mutated['lock_days'] = max(0.0, min(20.0, genome['lock_days'] + random.gauss(0, 2.0)))
        else:
            mutated['lock_days'] = genome['lock_days']
                
        # Repair thresholds
        t = mutated['base_thresholds']
        ordered = sorted([t['tier_1x'], t['tier_2x'], t['tier_3x']])
        mutated['base_thresholds'] = {
            'tier_1x': ordered[0],
            'tier_2x': ordered[1],
            'tier_3x': ordered[2]
        }
        return mutated

    def run(self):
        best_overall_genome = None
        best_overall_fitness = -9999
        best_overall_metrics = None

        print(f"Starting evolution: {self.generations} generations, pop size {self.population_size}, mutation {self.mutation_rate}")
        
        # Create a PERSISTENT process pool with worker-local data
        with concurrent.futures.ProcessPoolExecutor(
            initializer=_init_worker,
            initargs=(self.cache_file,)
        ) as executor:
            
            for gen in range(self.generations):
                start_time = time.time()
                
                # Evaluate population in parallel (only genome is serialized, not price data)
                scored_population = []
                futures = [executor.submit(_evaluate_genome_worker, g) for g in self.population]
                for future in concurrent.futures.as_completed(futures):
                    scored_population.append(future.result())
                
                # Sort by fitness descending
                scored_population.sort(key=lambda x: x[0], reverse=True)
                
                best_fitness, best_genome, best_metrics = scored_population[0]
                if best_fitness > best_overall_fitness:
                    best_overall_fitness = best_fitness
                    best_overall_genome = best_genome
                    best_overall_metrics = best_metrics
                    
                    # Save to vault when a new record is found
                    cagr_pct = best_overall_metrics['cagr'] * 100
                    dd_pct = best_overall_metrics['max_dd'] * 100
                    vault_dir = "champions/v1_classic/vault"
                    if not os.path.exists(vault_dir):
                        os.makedirs(vault_dir)
                    filename = f"{vault_dir}/genome_cagr_{cagr_pct:.2f}_dd_{dd_pct:.2f}.json"
                    with open(filename, "w") as f:
                        json.dump(best_genome, f, indent=2)

                cagr = best_metrics['cagr'] * 100
                dd = best_metrics['max_dd'] * 100
                trades = best_metrics['num_rebalances']
                
                elapsed = time.time() - start_time
                print(f"Gen {gen+1:02d} | Best Fitness: {best_fitness:6.2f} | CAGR: {cagr:6.2f}% | MaxDD: {dd:6.2f}% | Trades: {trades} | Time: {elapsed:.1f}s")
                
                # Selection: keep top 20%
                elites = [x[1] for x in scored_population[: max(2, int(self.population_size * 0.2))]]
                
                # Breed new generation
                new_population = list(elites) # Carry over elites (Elitism)
                
                while len(new_population) < self.population_size:
                    # Tournament selection for parents
                    p1 = random.choice(elites)
                    p2 = random.choice(elites)
                    
                    child = self._crossover(p1, p2)
                    child = self._mutate(child)
                    new_population.append(child)
                    
                self.population = new_population

        print("\nEvolution Complete.")
        print(f"Best Overall CAGR: {best_overall_metrics['cagr']*100:.2f}%")
        print(f"Best Overall MaxDD: {best_overall_metrics['max_dd']*100:.2f}%")
        
        # Save to file
        save_path = "champions/v1_classic/genome.json"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(best_overall_genome, f, indent=2)
        print(f"Saved best genome to {save_path}")
        
        return best_overall_genome
