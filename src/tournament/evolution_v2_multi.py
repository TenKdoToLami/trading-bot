import random
import json
import concurrent.futures
import time
import os

from strategies.genome_v2_multi import GenomeV2Strategy
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data


# ──────────────────────────────────────────────────────
# Worker-Local Data
# ──────────────────────────────────────────────────────

_worker_price_data = None
_worker_dates = None
_worker_nitro_features = None
_worker_push_mid = False

def _init_worker(cache_file, push_mid=False):
    global _worker_price_data, _worker_dates, _worker_push_mid, _worker_nitro_features
    import pandas as pd
    from src.helpers.indicators import (
        sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility
    )

    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_price_data = df.to_dict('records')
    _worker_dates = df.index
    _worker_push_mid = push_mid

    # ──────────────────────────────────────────────────────
    # NITRO MODE: Pre-calculate V2 features
    # ──────────────────────────────────────────────────────
    print(f"  [Worker {os.getpid()}] Pre-calculating V2 Nitro features...")
    nitro = {}
    prices, highs, lows = [], [], []
    prev_ema, prev_atr, indicator_state = None, None, {}

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
            'atr': ((v_atr or 0.0) / spy_price) * 50,
            'vix': (float(row.get('vix', 15.0)) - 20) / 10.0,
            'yc': float(row.get('yield_curve', 0.0))
        }
    _worker_nitro_features = nitro


def _evaluate_genome_worker(genome):
    res = _execute_simulation(
        strategy_type=GenomeV2Strategy,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome, 'precalculated_features': _worker_nitro_features}
    )
    metrics = res['metrics']
    cagr = metrics['cagr'] * 100
    max_dd = abs(metrics['max_dd']) * 100
    
    # ── RISK-ADJUSTED FITNESS (Institutional Standard) ──
    # Formula: CAGR - (MaxDD * 0.15)
    fitness = cagr - (max_dd * 0.15)
    
    # Extreme Blowout Penalty
    if max_dd >= 95.0: fitness -= 1000

    if _worker_push_mid:
        holdings = [h[1] for h in res['portfolio'].holdings_log]
        mid_tier_days = sum(1 for h in holdings if 'SPY' in h or '2xSPY' in h)
        residency_pct = mid_tier_days / len(holdings)
        fitness += (residency_pct * 15.0)

    return fitness, genome, metrics


class EvolutionEngineV2:
    """
    Genetic Algorithm Engine for Genome V2 (Multi-Brain Architecture).
    """
    def __init__(self, population_size=50, generations=20, mutation_rate=0.15, seed_vault=None, use_ablation=True, push_mid_tiers=False, min_cagr=0.0):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.use_ablation = use_ablation
        self.push_mid_tiers = push_mid_tiers
        self.min_cagr = min_cagr
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']
        self.brains = ['panic', '3x', '2x', '1x']
        
        print(f"Loading master data (SPY + Macro) for evolution v2 (Push Mid: {self.push_mid_tiers})...")
        self.data = load_spy_data("1993-01-01", force_refresh=False)
        from src.helpers.data_provider import CACHE_FILE
        self.cache_file = CACHE_FILE
        
        self.population = []
        
        # ── Seed Injection ──
        if seed_vault and os.path.exists(seed_vault):
            print(f"Injecting seeds from: {seed_vault}...")
            seeds = []
            for f in os.listdir(seed_vault):
                if f.endswith(".json"):
                    with open(os.path.join(seed_vault, f), "r") as jf:
                        try:
                            genome = json.load(jf)
                            # Upgrade V1 to V2 if necessary
                            if 'panic' not in genome:
                                print(f"  Upgrading V1 seed to V2: {f}")
                                v2_seed = {'lock_days': genome.get('lock_days', 3.0)}
                                for b in self.brains:
                                    v2_seed[b] = {
                                        'w': genome['base_weights'].copy() if 'base' in b else genome['panic_weights'].copy(),
                                        'a': {k: True for k in self.indicators},
                                        't': 0.0
                                    }
                                genome = v2_seed
                            seeds.append(genome)
                        except: continue
            
            # Fill population with seeds first
            self.population.extend(seeds[:self.population_size])
            print(f"  Successfully injected {len(seeds)} seeds.")

        # Fill the rest with random genomes
        while len(self.population) < self.population_size:
            self.population.append(self._random_genome())

    def _random_genome(self):
        genome = {}
        for b in self.brains:
            # Start with higher variance weights to encourage aggression
            genome[b] = {
                'w': {k: random.uniform(-4, 4) for k in self.indicators},
                'a': {k: (random.random() > 0.4 if self.use_ablation else True) for k in self.indicators},
                't': random.uniform(-1.5, 1.5)
            }
        genome['lock_days'] = random.uniform(0, 10)
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
                if self.use_ablation and random.random() < 0.05: # 5% ablation flip
                    mutated[b]['a'][k] = not a
                else:
                    mutated[b]['a'][k] = True if not self.use_ablation else a
                    
        mutated['lock_days'] = genome['lock_days']
        if random.random() < self.mutation_rate:
            mutated['lock_days'] = max(0, min(20, mutated['lock_days'] + random.gauss(0, 2)))
            
        return mutated

    def run(self):
        best_overall_fitness = -9999
        best_overall_metrics = None
        best_overall_genome = None

        # Leave 4 cores free for system responsiveness
        max_workers = max(1, (os.cpu_count() or 4) - 4)
        print(f"Starting Evolution V2: {self.generations} generations, pop {self.population_size} (using {max_workers} cores)")
        print(f"  Ablation: {'ON' if self.use_ablation else 'OFF'} | Mutation: {self.mutation_rate} | Push-Mid: {self.push_mid_tiers}")
        
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=max_workers,
            initializer=_init_worker, 
            initargs=(self.cache_file, self.push_mid_tiers)
        ) as executor:
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
                    
                    # Save to Vault V2 (only if above CAGR threshold)
                    if (best_metrics['cagr'] * 100) >= self.min_cagr:
                        vault_dir = "champions/v2_multi/vault"
                        if not os.path.exists(vault_dir): os.makedirs(vault_dir)
                        c, d = best_metrics['cagr']*100, best_metrics['max_dd']*100
                        with open(f"{vault_dir}/v2_cagr_{c:.2f}_dd_{d:.2f}.json", "w") as f:
                            json.dump(best_genome, f, indent=2)
                    else:
                        print(f"  [SKIPPED] CAGR {best_metrics['cagr']*100:.2f}% < {self.min_cagr}% (Vault not updated)")

                elapsed = time.time() - start_time
                print(f"V2 Gen {gen+1:02d} | Fit: {best_fit:6.2f} | CAGR: {best_metrics['cagr']*100:6.2f}% | MaxDD: {best_metrics['max_dd']*100:6.2f}% | Time: {elapsed:.1f}s")
                
                # --- PURE GA SELECTION ---
                elites = [x[1] for x in scored[:max(2, int(self.population_size * 0.2))]]
                new_pop = list(elites)
                
                while len(new_pop) < self.population_size:
                    p1, p2 = random.choice(elites), random.choice(elites)
                    child = self._crossover(p1, p2)
                    new_pop.append(self._mutate(child))
                    
                self.population = new_pop

        print(f"\nEvolution V2 Complete. Best CAGR: {best_overall_metrics['cagr']*100:.2f}%")
        print(f"Results stored in vault.")
        return best_overall_genome
