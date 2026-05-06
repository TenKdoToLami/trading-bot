import json
import random
import os
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Callable
import copy

from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution
from strategies.genome_v14_nas import GenomeV14NAS
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import CACHE_FILE

# --- GLOBAL WORKER DATA ---
_worker_price_data = None
_worker_dates = None

def _init_worker_lazy():
    global _worker_price_data, _worker_dates
    if _worker_price_data is not None:
        return
    df = pd.read_csv(CACHE_FILE, index_col=0, parse_dates=True)
    _worker_dates = df.index
    cols = ['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve', 'credit_spread', 
            'month_sin', 'month_cos', 'is_tom', 'tlt_proxy', 'shy_proxy', 'gold']
    existing_cols = [c for c in cols if c in df.columns]
    _worker_price_data = df[existing_cols].to_dict('records')

def _evaluate_v14_nas_worker(genome):
    _init_worker_lazy()
    res = _execute_simulation(
        strategy_type=GenomeV14NAS,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome},
        early_exit_dd=-0.95,
        warmup_days=200
    )
    
    m = res['metrics']
    cagr = m['cagr'] * 100
    dd = abs(m['max_dd']) * 100
    
    # 1. Aggressive 50 Penalty (1:1)
    fitness = cagr
    if dd > 50.0:
        fitness -= (dd - 50.0)
    
    # 2. NAS SPARSITY PENALTY
    s_dim = genome.get('sentinel_dim', 10)
    c_dim = genome.get('commander_dim', 6)
    sparsity_penalty = (s_dim + c_dim) * 0.05
    fitness -= sparsity_penalty
        
    return fitness, m, genome

@register_evolution("v14_nas")
class EvolutionV14NAS(BaseEvolutionEngine):
    def __init__(self, **kwargs):
        self.lb_bounds = {
            'sma': (20, 500), 'ema': (10, 300), 'rsi': (5, 60),
            'macd_f': (5, 40), 'macd_s': (15, 80), 'vol': (5, 100),
            'atr': (5, 40), 'mfi': (5, 40), 'bb': (10, 50),
            'trix': (5, 40), 'adx': (5, 40), 'slope': (5, 60)
        }
        super().__init__(version_id="v14_nas", **kwargs)

    def _get_worker_config(self) -> Tuple[Callable, Tuple]:
        return _evaluate_v14_nas_worker, (_init_worker_lazy, ())

    def _random_genome(self) -> Dict[str, Any]:
        def master_brain(in_dim, max_hid, out_dim):
            return {
                'w': np.random.uniform(-0.5, 0.5, (in_dim, max_hid)).tolist(),
                'b': np.zeros(max_hid).tolist(),
                'out_w': np.random.uniform(-1, 1, (max_hid, out_dim)).tolist(),
                'out_b': np.zeros(out_dim).tolist()
            }
        return {
            'version': 14.0,
            'sentinel_dim': random.randint(4, 16),
            'commander_dim': random.randint(4, 10),
            'sentinel': master_brain(28, 32, 2), 
            'bear_commander': master_brain(10, 16, 3), 
            'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()},
            'hysteresis': random.uniform(0.05, 0.25),
            'smoothing': random.uniform(0.1, 0.5),
            'temp': 1.0,
            'skew_power': random.uniform(1.0, 3.5),
            'conviction_cap': random.uniform(0.70, 0.95)
        }

    def _mutate(self, genome: Dict[str, Any]) -> Dict[str, Any]:
        g = copy.deepcopy(genome)
        rate = self.mut_rate
        strength = self.mut_strength
        
        # 1. Mutate Brains (All 32 slots)
        def mut_brain(brain):
            brain['w'] = (np.array(brain['w']) + np.random.normal(0, 0.05 * strength, np.array(brain['w']).shape)).tolist()
            brain['out_w'] = (np.array(brain['out_w']) + np.random.normal(0, 0.1 * strength, np.array(brain['out_w']).shape)).tolist()
            
        mut_brain(g['sentinel'])
        mut_brain(g['bear_commander'])
        
        # 2. Mutate NAS Dimensions (Turbo NAS: High Probability)
        nas_rate = 0.5 # 50% chance to shift architecture when mutating
        if random.random() < nas_rate:
            # Sentinel jumps: allow more aggressive exploration (+/- 4)
            g['sentinel_dim'] = int(np.clip(g.get('sentinel_dim', 10) + random.choice([-4, -2, -1, 1, 2, 4]), 2, 32))
        if random.random() < nas_rate:
            g['commander_dim'] = int(np.clip(g.get('commander_dim', 6) + random.choice([-2, -1, 1, 2]), 2, 16))
            
        # 3. Standard Params
        if random.random() < rate:
            k = random.choice(list(self.lb_bounds.keys()))
            mn, mx = self.lb_bounds[k]
            g['lookbacks'][k] = random.randint(mn, mx)
        
        if random.random() < rate: g['skew_power'] = np.clip(g.get('skew_power', 2.0) * random.uniform(0.9, 1.1), 1.0, 5.0)
        if random.random() < rate: g['conviction_cap'] = np.clip(g.get('conviction_cap', 0.9) * random.uniform(0.95, 1.05), 0.7, 0.99)
            
        return g

    def _crossover(self, g1: Dict[str, Any], g2: Dict[str, Any]) -> Dict[str, Any]:
        child = copy.deepcopy(g1)
        
        # 1. Dimension Blending (NAS Breed)
        if random.random() < 0.5:
            # Pick one parent
            child['sentinel_dim'] = random.choice([g1, g2]).get('sentinel_dim', 10)
            child['commander_dim'] = random.choice([g1, g2]).get('commander_dim', 6)
        else:
            # Blend both parents (The average size)
            child['sentinel_dim'] = int((g1.get('sentinel_dim', 10) + g2.get('sentinel_dim', 10)) / 2)
            child['commander_dim'] = int((g1.get('commander_dim', 6) + g2.get('commander_dim', 6)) / 2)
        
        # Brain crossover (Pick one parent's master weights)
        child['sentinel'] = random.choice([g1, g2])['sentinel']
        child['bear_commander'] = random.choice([g1, g2])['bear_commander']
        
        # Crossover lookbacks robustly
        all_keys = set(g1['lookbacks'].keys()).union(set(g2['lookbacks'].keys()))
        for k in all_keys:
            if k in g1['lookbacks'] and k in g2['lookbacks']:
                child['lookbacks'][k] = random.choice([g1, g2])['lookbacks'][k]
            elif k in g1['lookbacks']:
                child['lookbacks'][k] = g1['lookbacks'][k]
            else:
                child['lookbacks'][k] = g2['lookbacks'][k]
        
        child['skew_power'] = (g1.get('skew_power', 2.0) + g2.get('skew_power', 2.0)) / 2
        return child
