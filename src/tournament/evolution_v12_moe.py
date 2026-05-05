"""
Evolution Engine for V12 MOE — Hierarchical Mixture of Experts.
Optimizes 3 separate brains (Regime, Bull, Bear) and lookbacks.
"""

import numpy as np
import random
import json
import os
from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution
from strategies.genome_v12_moe import GenomeV12MOE
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import CACHE_FILE

# --- GLOBAL WORKER STATE ---
_worker_price_data = None
_worker_dates = None

def _init_worker(cache_file):
    global _worker_price_data, _worker_dates
    import pandas as pd
    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_dates = df.index
    # Include all needed columns for V12
    cols = ['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve', 'credit_spread', 
            'month_sin', 'month_cos', 'is_tom', 'tlt_proxy', 'shy_proxy', 'gold']
    _worker_price_data = df[cols].to_dict('records')

def _evaluate_v12_moe_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=GenomeV12MOE,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    
    # Fitness: CAGR - (DD * 0.1)
    # V12 is more complex, so we reward low DD more aggressively
    fitness = cagr_pct - (dd_pct * 0.2) 

    # Penalty for high DD
    if dd_pct > 30.0:
        fitness -= ((dd_pct - 30.0) ** 1.5)

    # Dormancy protection
    if metrics['num_rebalances'] <= 1: fitness -= 2000 

    return fitness, metrics, genome

@register_evolution("v12_moe")
class EvolutionEngineV12MOE(BaseEvolutionEngine):
    def __init__(self, **kwargs):
        self.lb_bounds = {
            'sma': (20, 500), 'ema': (10, 300), 'rsi': (5, 60), 'macd_f': (5, 40),
            'macd_s': (15, 80), 'adx': (5, 60), 'trix': (5, 60), 'slope': (5, 80),
            'vol': (5, 100), 'atr': (5, 60), 'mfi': (5, 80), 'bb': (5, 80)
        }
        super().__init__(version_id="v12_moe", **kwargs)

    def _random_genome(self):
        def rand_brain(in_dim, hid_dim, out_dim):
            return {
                'w': np.random.uniform(-0.5, 0.5, (in_dim, hid_dim)).tolist(),
                'b': np.zeros(hid_dim).tolist(),
                'out_w': np.random.uniform(-1, 1, (hid_dim, out_dim)).tolist(),
                'out_b': np.zeros(out_dim).tolist()
            }

        return {
            'version': 12.0,
            'regime': rand_brain(18, 16, 2),
            'bull': rand_brain(18, 16, 3),
            'bear': rand_brain(18, 16, 4),
            'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()},
            'smoothing': random.uniform(0.1, 0.6),
            'regime_hysteresis': random.uniform(0.05, 0.25)
        }

    def _mutate(self, genome):
        # Create deep copy
        mutated = json.loads(json.dumps(genome))
        m = self.mut_rate
        
        def mut_brain(brain):
            for key in ['w', 'b', 'out_w', 'out_b']:
                arr = np.array(brain[key])
                if random.random() < m:
                    mask = np.random.random(arr.shape) < 0.2
                    noise = np.random.normal(0, 0.05 * self.mut_strength, arr.shape)
                    arr[mask] += noise[mask]
                brain[key] = arr.tolist()
            return brain

        mutated['regime'] = mut_brain(mutated['regime'])
        mutated['bull'] = mut_brain(mutated['bull'])
        mutated['bear'] = mut_brain(mutated['bear'])

        # Mutate lookbacks
        for k, v in mutated['lookbacks'].items():
            if random.random() < m:
                mn, mx = self.lb_bounds[k]
                mutated['lookbacks'][k] = max(mn, min(mx, v + int(random.gauss(0, (mx-mn) * 0.1 * self.mut_strength))))

        # Mutate params
        if random.random() < m:
            mutated['smoothing'] = np.clip(mutated['smoothing'] + random.gauss(0, 0.05 * self.mut_strength), 0.01, 0.9)
        if random.random() < m:
            mutated['regime_hysteresis'] = np.clip(mutated['regime_hysteresis'] + random.gauss(0, 0.02 * self.mut_strength), 0.01, 0.5)

        return mutated

    def _crossover(self, g1, g2):
        child = json.loads(json.dumps(g1))
        
        # Brain-level crossover
        child['regime'] = random.choice([g1, g2])['regime']
        child['bull'] = random.choice([g1, g2])['bull']
        child['bear'] = random.choice([g1, g2])['bear']
        
        # Parameter-level crossover
        for k in child['lookbacks']:
            child['lookbacks'][k] = random.choice([g1, g2])['lookbacks'][k]
            
        child['smoothing'] = (g1['smoothing'] + g2['smoothing']) / 2
        child['regime_hysteresis'] = random.choice([g1, g2])['regime_hysteresis']
        
        return child

    def _get_worker_config(self):
        return _evaluate_v12_moe_worker, (_init_worker, (CACHE_FILE,))
