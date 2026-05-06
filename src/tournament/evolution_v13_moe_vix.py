import json
import random
import os
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Callable
from datetime import datetime
import copy

from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution
from strategies.genome_v13_moe_vix import GenomeV13MOEVIX
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

def _evaluate_v13_moe_vix_worker(genome):
    _init_worker_lazy()
    res = _execute_simulation(
        strategy_type=GenomeV13MOEVIX,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome},
        early_exit_dd=-0.95,
        warmup_days=200
    )
    
    m = res['metrics']
    cagr = m['cagr'] * 100
    dd = abs(m['max_dd']) * 100
    
    # Aggressive 50 Penalty
    fitness = cagr
    if dd > 50.0:
        fitness -= (dd - 50.0) / 10
        
    return fitness, m, genome

@register_evolution("v13_moe_vix")
class EvolutionV13MOEVIX(BaseEvolutionEngine):
    def __init__(self, **kwargs):
        self.lb_bounds = {
            'sma': (20, 500), 'ema': (10, 300), 'rsi': (5, 60),
            'macd_f': (5, 40), 'macd_s': (15, 80), 'vol': (5, 100),
            'adx': (5, 40), 'trix': (5, 40), 'slope': (5, 60),
            'atr': (5, 40), 'mfi': (5, 40), 'bb': (10, 50)
        }
        super().__init__(version_id="v13_moe_vix", **kwargs)

    def _get_worker_config(self) -> Tuple[Callable, Tuple]:
        return _evaluate_v13_moe_vix_worker, (_init_worker_lazy, ())

    def _random_genome(self) -> Dict[str, Any]:
        def rand_brain(in_dim, hid_dim, out_dim):
            return {
                'w': np.random.uniform(-0.5, 0.5, (in_dim, hid_dim)).tolist(),
                'b': np.zeros(hid_dim).tolist(),
                'out_w': np.random.uniform(-1, 1, (hid_dim, out_dim)).tolist(),
                'out_b': np.zeros(out_dim).tolist()
            }
        return {
            'version': 13.11,
            'sentinel': rand_brain(28, 10, 2), 
            'bear_commander': rand_brain(10, 6, 3), 
            'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()},
            'hysteresis': random.uniform(0.05, 0.25),
            'smoothing': random.uniform(0.1, 0.5),
            'temp': 1.0,
            'skew_power': random.uniform(1.0, 3.5),
            'vix_base_cap': random.uniform(0.70, 0.95),
            'vix_sensitivity': random.uniform(0.005, 0.03),
            'features': ['sma', 'ema', 'rsi', 'macd', 'vol', 'vix', 'yc', 'gold', 'tlt', 'shy']
        }

    def _mutate(self, genome: Dict[str, Any]) -> Dict[str, Any]:
        g = copy.deepcopy(genome)
        rate = self.mut_rate
        strength = self.mut_strength
        
        def mut_brain(brain):
            brain['w'] = (np.array(brain['w']) + np.random.normal(0, 0.05 * strength, np.array(brain['w']).shape)).tolist()
            brain['out_w'] = (np.array(brain['out_w']) + np.random.normal(0, 0.1 * strength, np.array(brain['out_w']).shape)).tolist()
            
        mut_brain(g['sentinel'])
        mut_brain(g['bear_commander'])
        
        if random.random() < rate:
            k = random.choice(list(self.lb_bounds.keys()))
            mn, mx = self.lb_bounds[k]
            g['lookbacks'][k] = random.randint(mn, mx)
        
        if random.random() < rate: g['vix_base_cap'] = np.clip(g.get('vix_base_cap', 0.85) * random.uniform(0.9, 1.1), 0.6, 0.99)
        if random.random() < rate: g['vix_sensitivity'] = np.clip(g.get('vix_sensitivity', 0.01) * random.uniform(0.8, 1.2), 0.0, 0.05)
        if random.random() < rate: g['skew_power'] = np.clip(g.get('skew_power', 2.0) * random.uniform(0.9, 1.1), 1.0, 5.0)
            
        return g

    def _crossover(self, g1: Dict[str, Any], g2: Dict[str, Any]) -> Dict[str, Any]:
        child = copy.deepcopy(g1)
        child['sentinel'] = random.choice([g1, g2])['sentinel']
        child['bear_commander'] = random.choice([g1, g2])['bear_commander']
        for k in child['lookbacks']:
            child['lookbacks'][k] = random.choice([g1, g2])['lookbacks'][k]
        
        child['vix_base_cap'] = (g1.get('vix_base_cap', 0.85) + g2.get('vix_base_cap', 0.85)) / 2
        child['vix_sensitivity'] = (g1.get('vix_sensitivity', 0.01) + g2.get('vix_sensitivity', 0.01)) / 2
        child['skew_power'] = (g1.get('skew_power', 2.0) + g2.get('skew_power', 2.0)) / 2
        return child
