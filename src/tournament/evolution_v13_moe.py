"""
Evolution Engine for V13 MOE Pro — The Institutional Commander.
Specialized for 3-brain MoE evolution (Sentinel, Bull Expert, Bear Expert).
"""

import numpy as np
import random
import json
import os
import pandas as pd
from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution
from strategies.genome_v13_moe import GenomeV13MOE
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import CACHE_FILE

# --- GLOBAL WORKER STATE ---
_worker_price_data = None
_worker_dates = None
_worker_target = 'all' 

def _init_worker(cache_file, target='all'):
    global _worker_price_data, _worker_dates, _worker_target
    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_target = target
    _worker_dates = df.index
    
    cols = ['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve', 'credit_spread', 
            'month_sin', 'month_cos', 'is_tom', 'tlt_proxy', 'shy_proxy', 'gold']
    
    existing_cols = [c for c in cols if c in df.columns]
    _worker_price_data = df[existing_cols].to_dict('records')

def _evaluate_v13_moe_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=GenomeV13MOE,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    
    # 1. Performance Fitness (Institutional weighting)
    fitness = cagr_pct - (dd_pct * 0.4)

    # 2. Leverage Incentive (Alpha pursuit)
    avg_lev = metrics.get('avg_leverage', 1.0)
    leverage_bonus = (avg_lev - 1.0) * 5.0 
    fitness += max(0, leverage_bonus)

    # 3. Defensive Stability (No blowups)
    if dd_pct > 50.0: 
        fitness -= (dd_pct - 50.0) * 5.0 
    
    trades_per_year = metrics.get('trades_per_year', metrics['num_rebalances'] / 31.0)
    if trades_per_year > 25:
        fitness -= (trades_per_year - 25) * 2.0

    if metrics['num_rebalances'] <= 1: fitness -= 100

    return fitness, metrics, genome

@register_evolution("v13_moe")
class EvolutionEngineV13MOE(BaseEvolutionEngine):
    def __init__(self, target='all', **kwargs):
        self.target = target
        self.lb_bounds = {
            'sma': (20, 500), 'ema': (10, 300), 'rsi': (5, 60), 'macd_f': (5, 40),
            'macd_s': (15, 80), 'adx': (5, 60), 'trix': (5, 60), 'slope': (5, 80),
            'vol': (5, 100), 'atr': (5, 60), 'mfi': (5, 80), 'bb': (5, 80)
        }
        super().__init__(version_id=f"v13_moe", **kwargs)

    def _random_genome(self):
        def rand_brain(in_dim, hid_dim, out_dim):
            return {
                'w': np.random.uniform(-0.5, 0.5, (in_dim, hid_dim)).tolist(),
                'b': np.zeros(hid_dim).tolist(),
                'out_w': np.random.uniform(-1, 1, (hid_dim, out_dim)).tolist(),
                'out_b': np.zeros(out_dim).tolist()
            }
        return {
            'version': 13.5,
            'sentinel': rand_brain(18, 10, 2),
            'bull_expert': rand_brain(18, 10, 3), 
            'bear_expert': rand_brain(18, 10, 5), 
            'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()},
            'hysteresis': random.uniform(0.05, 0.25),
            'smoothing': random.uniform(0.2, 0.6)
        }

    def _mutate(self, genome):
        mutated = json.loads(json.dumps(genome))
        m = self.mut_rate
        def mut_brain(brain):
            for key in ['w', 'b', 'out_w', 'out_b']:
                arr = np.array(brain[key])
                if random.random() < m:
                    mask = np.random.random(arr.shape) < 0.2
                    noise = np.random.normal(0, 0.1 * self.mut_strength, arr.shape)
                    arr[mask] += noise[mask]
                brain[key] = arr.tolist()
            return brain
            
        mutated['sentinel'] = mut_brain(mutated['sentinel'])
        mutated['bull_expert'] = mut_brain(mutated['bull_expert'])
        mutated['bear_expert'] = mut_brain(mutated['bear_expert'])
        
        for k, v in mutated['lookbacks'].items():
            if random.random() < m:
                mn, mx = self.lb_bounds[k]
                mutated['lookbacks'][k] = max(mn, min(mx, v + int(random.gauss(0, (mx-mn) * 0.1 * self.mut_strength))))
        
        if random.random() < m:
            mutated['smoothing'] = np.clip(mutated['smoothing'] + random.gauss(0, 0.05 * self.mut_strength), 0.1, 0.9)
        if random.random() < m:
            mutated['hysteresis'] = np.clip(mutated['hysteresis'] + random.gauss(0, 0.05 * self.mut_strength), 0.01, 0.4)
        
        return mutated

    def _crossover(self, g1, g2):
        child = json.loads(json.dumps(g1))
        child['sentinel'] = random.choice([g1, g2])['sentinel']
        child['bull_expert'] = random.choice([g1, g2])['bull_expert']
        child['bear_expert'] = random.choice([g1, g2])['bear_expert']
        for k in child['lookbacks']:
            child['lookbacks'][k] = random.choice([g1, g2])['lookbacks'][k]
        child['smoothing'] = (g1['smoothing'] + g2['smoothing']) / 2
        return child

    def _get_worker_config(self):
        return _evaluate_v13_moe_worker, (_init_worker, (CACHE_FILE, self.target))
