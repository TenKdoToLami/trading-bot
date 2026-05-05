"""
Evolution Engine for V13 Lite — Dual-Brain Precision.
Supports Phased Training: Sentinel (Regime) vs Pilot (Allocation).
"""

import numpy as np
import random
import json
import os
import pandas as pd
from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution
from strategies.genome_v13_lite import GenomeV13Lite
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import CACHE_FILE

# --- GLOBAL WORKER STATE ---
_worker_price_data = None
_worker_dates = None
_worker_god_labels = None 
_worker_target = 'all' # sentinel, pilot, all

def _init_worker(cache_file, target='all'):
    global _worker_price_data, _worker_dates, _worker_god_labels, _worker_target
    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_target = target
    
    # Calculate God-Mode Path
    god_path = _calculate_god_path(df)
    _worker_god_labels = np.array([1 if x in ['SPY', '2xSPY', '3xSPY'] else 0 for x in god_path])
    
    _worker_dates = df.index
    cols = ['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve', 'credit_spread', 
            'month_sin', 'month_cos', 'is_tom', 'tlt_proxy', 'shy_proxy', 'gold']
    _worker_price_data = df[cols].to_dict('records')

def _calculate_god_path(df):
    assets = ["CASH", "SPY", "2xSPY", "3xSPY"]
    L = 5 
    friction = 0.0012
    n = len(df)
    rets = {a: np.zeros(n) for a in assets}
    spy_rets = df['close'].pct_change().fillna(0).values
    rets["CASH"] = np.full(n, 0.0350 / 252)
    rets["SPY"] = spy_rets - (0.0003 / 252)
    rets["2xSPY"] = (spy_rets * 2.0) - (0.0091 / 252)
    rets["3xSPY"] = (spy_rets * 3.0) - (0.0091 / 252)
    dp = [{} for _ in range(n)]
    for a in assets: dp[0][a] = (1.0, None, None)
    for i in range(1, n):
        for a in assets:
            best_eq = dp[i-1][a][0] * (1.0 + rets[a][i])
            best_prev_a, best_prev_i = a, i-1
            if i >= L:
                for prev_a in assets:
                    if prev_a == a: continue
                    switch_eq = dp[i-L][prev_a][0]
                    for k in range(i-L+1, i+1): switch_eq *= (1.0 + rets[a][k])
                    switch_eq *= (1.0 - friction)
                    if switch_eq > best_eq:
                        best_eq = switch_eq
                        best_prev_a = prev_a
                        best_prev_i = i-L
            dp[i][a] = (best_eq, best_prev_a, best_prev_i)
    path = ["CASH"] * n
    curr_i, curr_a = n-1, max(dp[n-1], key=lambda x: dp[n-1][x][0])
    while curr_i is not None and curr_i >= 0:
        _, prev_a, prev_i = dp[curr_i][curr_a]
        for k in range(max(0, prev_i if prev_i is not None else 0), curr_i + 1): path[k] = curr_a
        if prev_i is None: break
        curr_i, curr_a = prev_i, prev_a
    return path

def _evaluate_v13_lite_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=GenomeV13Lite,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome}
            )
    metrics = res['metrics']
    tel = res.get('telemetry', {})
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    
    # 1. Supervised Sentinel Accuracy
    accuracy_bonus = 0
    if 'p_bull' in tel:
        preds = np.array(tel['p_bull'])
        min_len = min(len(preds), len(_worker_god_labels))
        if min_len > 0:
            accuracy = np.mean((preds[:min_len] > 0.5) == _worker_god_labels[:min_len])
            accuracy_bonus = accuracy * 1000

    # 2. Pilot Profitability Bonus (Scale fitness based on CAGR)
    fitness = cagr_pct - (dd_pct * 0.4) + accuracy_bonus
    
    # 3. Penalties
    if dd_pct > 25.0: fitness -= ((dd_pct - 25.0) ** 2.0)
    if metrics['num_rebalances'] <= 1: fitness -= 10000 

    return fitness, metrics, genome

@register_evolution("v13_lite")
class EvolutionEngineV13Lite(BaseEvolutionEngine):
    def __init__(self, target='all', **kwargs):
        self.target = target
        self.lb_bounds = {
            'sma': (20, 500), 'ema': (10, 300), 'rsi': (5, 60), 'macd_f': (5, 40),
            'macd_s': (15, 80), 'adx': (5, 60), 'trix': (5, 60), 'slope': (5, 80),
            'vol': (5, 100), 'atr': (5, 60), 'mfi': (5, 80), 'bb': (5, 80)
        }
        super().__init__(version_id=f"v13_lite_{target}", **kwargs)

    def _random_genome(self):
        def rand_brain(in_dim, hid_dim, out_dim):
            return {
                'w': np.random.uniform(-0.5, 0.5, (in_dim, hid_dim)).tolist(),
                'b': np.zeros(hid_dim).tolist(),
                'out_w': np.random.uniform(-1, 1, (hid_dim, out_dim)).tolist(),
                'out_b': np.zeros(out_dim).tolist()
            }
        return {
            'version': 13.0,
            'sentinel': rand_brain(18, 10, 2),
            'pilot': rand_brain(18, 10, 3),
            'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()},
            'hysteresis': random.uniform(0.1, 0.4),
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
            
        if self.target in ['all', 'sentinel']:
            mutated['sentinel'] = mut_brain(mutated['sentinel'])
        if self.target in ['all', 'pilot']:
            mutated['pilot'] = mut_brain(mutated['pilot'])
            
        if self.target in ['all', 'sentinel']:
            for k, v in mutated['lookbacks'].items():
                if random.random() < m:
                    mn, mx = self.lb_bounds[k]
                    mutated['lookbacks'][k] = max(mn, min(mx, v + int(random.gauss(0, (mx-mn) * 0.1 * self.mut_strength))))
        
        return mutated

    def _get_worker_config(self):
        return _evaluate_v13_lite_worker, (_init_worker, (CACHE_FILE, self.target))
