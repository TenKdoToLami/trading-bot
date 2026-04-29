import random
import json
import concurrent.futures
import time
import os
import numpy as np

from strategies._genome_strategy import GenomeStrategy
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data


# ──────────────────────────────────────────────────────
# Worker-Local Data (loaded once per process, not serialized)
# ──────────────────────────────────────────────────────

_worker_price_data = None
_worker_dates = None
_worker_nitro_features = None


def _init_worker(cache_file):
    """Called once per worker process to load data into process-local memory."""
    global _worker_price_data, _worker_dates, _worker_nitro_features
    import pandas as pd
    from src.helpers.indicators import (
        sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility
    )

    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_price_data = df[['open', 'high', 'low', 'close', 'volume']].to_dict('records')
    _worker_dates = df.index
    
    # ──────────────────────────────────────────────────────
    # NITRO MODE: Pre-calculate all V1 features for the entire series
    # ──────────────────────────────────────────────────────
    print(f"  [Worker {os.getpid()}] Pre-calculating Nitro features...")
    
    nitro = {}
    prices = []
    highs = []
    lows = []
    
    prev_ema = None
    prev_atr = None
    indicator_state = {}
    
    for i in range(len(_worker_price_data)):
        row = _worker_price_data[i]
        date = str(_worker_dates[i].date())
        spy_price = row['close']
        
        prices.append(spy_price)
        highs.append(row['high'])
        lows.append(row['low'])

        # 1. Calculate Indicators
        val_sma = sma(prices, 200)
        val_ema = ema(prices, 50, prev_ema=prev_ema)
        prev_ema = val_ema
        val_rsi = rsi(prices, 14, state=indicator_state)
        val_macd_tuple = macd(prices, 12, 26, state=indicator_state)
        val_macd = val_macd_tuple[0] if val_macd_tuple[0] is not None else 0.0
        val_adx = adx(highs, lows, prices, 14, state=indicator_state)
        val_trix = trix(prices, 15, state=indicator_state)
        val_slope = linear_regression_slope(prices, 20)
        val_vol = realized_volatility(prices, 20)
        val_atr = atr(highs, lows, prices, 14, prev_atr=prev_atr)
        prev_atr = val_atr

        # 2. Normalize Indicators
        norm_sma = ((spy_price - val_sma) / val_sma * 5) if val_sma else 0.0
        norm_ema = ((spy_price - val_ema) / val_ema * 10) if val_ema else 0.0
        norm_rsi = ((val_rsi or 50) - 50) / 50.0
        norm_macd = val_macd / spy_price * 100
        norm_adx = ((val_adx or 25) - 25) / 25.0
        norm_trix = val_trix or 0.0
        norm_slope = (val_slope or 0.0) / spy_price * 1000
        norm_vol = (val_vol or 0.15) * 5
        norm_atr = ((val_atr or 0.0) / spy_price) * 50

        nitro[date] = {
            'sma': norm_sma, 'ema': norm_ema, 'rsi': norm_rsi, 'macd': norm_macd,
            'adx': norm_adx, 'trix': norm_trix, 'slope': norm_slope,
            'vol': norm_vol, 'atr': norm_atr
        }
    
    _worker_nitro_features = nitro
    print(f"  [Worker {os.getpid()}] Nitro features ready ({len(nitro)} days).")


def _evaluate_genome_worker(genome):
    """Runs a full simulation using worker-local data. Only the genome is serialized."""
    res = _execute_simulation(
        strategy_type=GenomeStrategy,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome, 'precalculated_features': _worker_nitro_features}
    )
    
    metrics = res['metrics']
    cagr = metrics['cagr'] * 100
    max_dd = abs(metrics['max_dd']) * 100
    
    # ──────────────────────────────────────────────────────
    # RISK-ADJUSTED FITNESS (Institutional Standard)
    # Penalizes drawdown while rewarding raw returns.
    # Formula: CAGR - (MaxDD * 0.15)
    # ──────────────────────────────────────────────────────
    fitness = cagr - (max_dd * 0.15)
    
    # Extreme Blowout Protection
    if max_dd >= 95.0:
        fitness -= 1000  # Severe penalty for near-total loss
    
    return fitness, genome, metrics


class EvolutionEngineV1Classic:
    """
    Genetic Algorithm Engine to breed the optimal V1 Classic GenomeStrategy.
    """
    def __init__(self, population_size=50, generations=20, mutation_rate=0.15, seed_vault=None, use_ablation=True, min_cagr=0.0):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.use_ablation = use_ablation
        self.min_cagr = min_cagr
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr']
        
        # Load data once to ensure cache exists
        print("Loading data for V1 Classic evolution...")
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
                if 'panic_weights' in genome and 'base_weights' in genome:
                    match = re.search(r'cagr_([\d.]+)', filename)
                    cagr = float(match.group(1)) if match else 0.0
                    seeds.append((cagr, genome))
            except Exception:
                continue
        
        seeds.sort(key=lambda x: x[0], reverse=True)
        return [g for _, g in seeds]

    def _random_genome(self):
        def _rand_weights():
            return {k: random.uniform(-2, 2) for k in self.indicators}
        
        def _rand_active():
            # If ablation is off, everything is active
            return {k: (random.random() > 0.4 if self.use_ablation else True) for k in self.indicators}
        
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
        
        for key in self.indicators:
            child['panic_weights'][key] = p1['panic_weights'][key] if random.random() > 0.5 else p2['panic_weights'][key]
            child['panic_active'][key] = p1.get('panic_active', {}).get(key, True) if random.random() > 0.5 else p2.get('panic_active', {}).get(key, True)
            child['base_weights'][key] = p1['base_weights'][key] if random.random() > 0.5 else p2['base_weights'][key]
            child['base_active'][key] = p1.get('base_active', {}).get(key, True) if random.random() > 0.5 else p2.get('base_active', {}).get(key, True)
            
        for key in p1['base_thresholds']:
            child['base_thresholds'][key] = p1['base_thresholds'][key] if random.random() > 0.5 else p2['base_thresholds'][key]
            
        child['panic_threshold'] = p1['panic_threshold'] if random.random() > 0.5 else p2['panic_threshold']
        child['lock_days'] = p1['lock_days'] if random.random() > 0.5 else p2['lock_days']
        
        # Repair thresholds
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
            for key in self.indicators:
                val = genome[w_group][key]
                # Mutate weight
                if random.random() < self.mutation_rate:
                    mutated[w_group][key] = val + random.gauss(0, 0.5)
                else:
                    mutated[w_group][key] = val
                    
                # Mutate active mask (only if ablation is enabled)
                current_active = genome.get(a_group, {}).get(key, True)
                if self.use_ablation and random.random() < 0.05:
                    mutated[a_group][key] = not current_active
                else:
                    mutated[a_group][key] = current_active if self.use_ablation else True
                    
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

        print(f"Starting V1 Classic evolution: {self.generations} generations, pop {self.population_size}, mut {self.mutation_rate:.2f}, ablation {'ON' if self.use_ablation else 'OFF'}")
        
        with concurrent.futures.ProcessPoolExecutor(
            initializer=_init_worker,
            initargs=(self.cache_file,)
        ) as executor:
            
            for gen in range(self.generations):
                start_time = time.time()
                futures = [executor.submit(_evaluate_genome_worker, g) for g in self.population]
                scored_population = [f.result() for f in concurrent.futures.as_completed(futures)]
                scored_population.sort(key=lambda x: x[0], reverse=True)
                
                best_fitness, best_genome, best_metrics = scored_population[0]
                if best_fitness > best_overall_fitness:
                    best_overall_fitness = best_fitness
                    best_overall_genome = best_genome
                    best_overall_metrics = best_metrics
                    
                    # Save to vault (only if above CAGR threshold)
                    if (best_overall_metrics['cagr'] * 100) >= self.min_cagr:
                        cagr_pct = best_overall_metrics['cagr'] * 100
                        dd_pct = best_overall_metrics['max_dd'] * 100
                        vault_dir = "champions/v1_classic/vault"
                        os.makedirs(vault_dir, exist_ok=True)
                        filename = f"{vault_dir}/genome_cagr_{cagr_pct:.2f}_dd_{dd_pct:.2f}.json"
                        with open(filename, "w") as f:
                            json.dump(best_genome, f, indent=2)
                    else:
                        print(f"  [SKIPPED] CAGR {best_overall_metrics['cagr']*100:.2f}% < {self.min_cagr}% (Vault not updated)")

                cagr = best_metrics['cagr'] * 100
                dd = best_metrics['max_dd'] * 100
                trades = best_metrics['num_rebalances']
                
                elapsed = time.time() - start_time
                num_elites = max(2, int(self.population_size * 0.2))
                
                print(f"Gen {gen+1:03d}/{self.generations:03d} | Fit: {best_fitness:6.2f} | CAGR: {cagr:6.2f}% | MaxDD: {dd:6.2f}% | Trades: {trades} | Time: {elapsed:.1f}s")
                
                # --- PURE GA SELECTION ---
                elites = [x[1] for x in scored_population[:num_elites]]
                new_population = list(elites) 
                while len(new_population) < self.population_size:
                    p1, p2 = random.choice(elites), random.choice(elites)
                    child = self._crossover(p1, p2)
                    new_population.append(self._mutate(child))
                self.population = new_population

        print("\nEvolution Complete.")
        print(f"Best Overall CAGR: {best_overall_metrics['cagr']*100:.2f}%")
        print(f"Best Overall MaxDD: {best_overall_metrics['max_dd']*100:.2f}%")
        print(f"Results stored in vault.")
        return best_overall_genome
