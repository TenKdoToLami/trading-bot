"""
Evolution Engine for V12 MOE — Supervised God-Guided Training.
Uses "God Mode" look-ahead data as a hard target for supervised learning.
Includes trade-count penalties to eliminate jitter and friction bleeding.
"""

import numpy as np
import random
import json
import os
import pandas as pd
from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution
from strategies.genome_v12_moe import GenomeV12MOE
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import CACHE_FILE

# --- GLOBAL WORKER STATE ---
_worker_price_data = None
_worker_dates = None
_worker_target_brain = 'all' 
_worker_regime_filter = 'none' 
_worker_god_labels = None # Binary labels from God-Teacher

def _init_worker(cache_file, target_brain='all', regime_filter='none'):
    global _worker_price_data, _worker_dates, _worker_target_brain, _worker_regime_filter, _worker_god_labels
    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    
    _worker_target_brain = target_brain
    _worker_regime_filter = regime_filter

    # 1. Calculate God-Mode Path for ALL days (for supervised correlation)
    god_path = _calculate_god_path(df)
    # 1 = Bullish (SPY family), 0 = Bearish (Defense/Cash)
    all_god_labels = np.array([1 if x in ['SPY', '2xSPY', '3xSPY'] else 0 for x in god_path])
    df['god_regime'] = god_path

    # 2. Filter data for specialist training
    if regime_filter == 'god_bullish':
        mask = df['god_regime'].isin(['SPY', '2xSPY', '3xSPY']).values
        df = df.iloc[mask]
        _worker_god_labels = all_god_labels[mask]
    elif regime_filter == 'god_bearish':
        mask = df['god_regime'].isin(['TLT', 'SHY', 'GOLD', '2xSHORT_SPY', 'CASH']).values
        df = df.iloc[mask]
        _worker_god_labels = all_god_labels[mask]
    else:
        _worker_god_labels = all_god_labels
    
    # 3. Finalize worker state
    _worker_dates = df.index
    cols = ['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve', 'credit_spread', 
            'month_sin', 'month_cos', 'is_tom', 'tlt_proxy', 'shy_proxy', 'gold']
    _worker_price_data = df[cols].to_dict('records')

def _calculate_god_path(df):
    assets = ["CASH", "SPY", "2xSPY", "3xSPY", "TLT", "SHY", "GOLD", "2xSHORT_SPY"]
    L = 5 
    friction = 0.0012
    n = len(df)
    rets = {a: np.zeros(n) for a in assets}
    spy_rets = df['close'].pct_change().fillna(0).values
    rets["CASH"] = np.full(n, 0.0350 / 252)
    rets["SPY"] = spy_rets - (0.0003 / 252)
    rets["2xSPY"] = (spy_rets * 2.0) - (0.0091 / 252)
    rets["3xSPY"] = (spy_rets * 3.0) - (0.0091 / 252)
    if 'tlt_proxy' in df: rets["TLT"] = df['tlt_proxy'].pct_change().fillna(0).values
    if 'shy_proxy' in df: rets["SHY"] = df['shy_proxy'].pct_change().fillna(0).values
    if 'gold' in df:      rets["GOLD"] = df['gold'].pct_change().fillna(0).values
    rets["2xSHORT_SPY"] = (spy_rets * -2.0) - (0.0091 / 252)
    
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

def _evaluate_v12_phased_worker(genome):
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
    tel = res.get('telemetry', {})
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    
    correlation_bonus = 0
    if _worker_target_brain == 'regime' or _worker_target_brain == 'all':
        if 'regime' in tel:
            preds = np.array(tel['regime'])
            min_len = min(len(preds), len(_worker_god_labels))
            if min_len > 0:
                p = preds[:min_len]
                g = _worker_god_labels[:min_len]
                accuracy = np.mean((p > 0.5) == g)
                correlation_bonus = accuracy * 1000 

    trades_per_year = metrics.get('trades_per_year', metrics['num_rebalances'] / 31.0)
    friction_penalty = 0
    if trades_per_year > 25:
        friction_penalty = (trades_per_year - 25) * 50 

    specialist_bonus = 0
    if _worker_target_brain == 'bull':
        if 'bull_split' in tel:
            leverage_score = np.mean([s[2] for s in tel['bull_split']]) 
            specialist_bonus = leverage_score * 500
    elif _worker_target_brain == 'bear':
        if 'bear_split' in tel:
            defense_score = np.mean([1.0 - s[1] for s in tel['bear_split']]) 
            specialist_bonus = defense_score * 300

    fitness = cagr_pct - (dd_pct * 0.3) + correlation_bonus + specialist_bonus - friction_penalty
    if dd_pct > 25.0: fitness -= ((dd_pct - 25.0) ** 2.5)
    if metrics['num_rebalances'] <= 1: fitness -= 10000 

    return fitness, metrics, genome

@register_evolution("v12_phased")
class EvolutionEngineV12Phased(BaseEvolutionEngine):
    def __init__(self, target_brain='all', regime_filter='none', **kwargs):
        self.target_brain = target_brain
        self.regime_filter = regime_filter
        self.lb_bounds = {
            'sma': (20, 500), 'ema': (10, 300), 'rsi': (5, 60), 'macd_f': (5, 40),
            'macd_s': (15, 80), 'adx': (5, 60), 'trix': (5, 60), 'slope': (5, 80),
            'vol': (5, 100), 'atr': (5, 60), 'mfi': (5, 80), 'bb': (5, 80)
        }
        super().__init__(version_id=f"v12_{target_brain}", **kwargs)

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
            'smoothing': random.uniform(0.1, 0.4),
            'regime_hysteresis': random.uniform(0.1, 0.4),
            'allocation_hysteresis': random.uniform(0.05, 0.25)
        }

    def _mutate(self, genome):
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
        if self.target_brain in ['all', 'regime']: mutated['regime'] = mut_brain(mutated['regime'])
        if self.target_brain in ['all', 'bull']: mutated['bull'] = mut_brain(mutated['bull'])
        if self.target_brain in ['all', 'bear']: mutated['bear'] = mut_brain(mutated['bear'])
        if self.target_brain in ['all', 'regime']:
            for k, v in mutated['lookbacks'].items():
                if random.random() < m:
                    mn, mx = self.lb_bounds[k]
                    mutated['lookbacks'][k] = max(mn, min(mx, v + int(random.gauss(0, (mx-mn) * 0.1 * self.mut_strength))))
            if random.random() < m:
                mutated['smoothing'] = np.clip(mutated['smoothing'] + random.gauss(0, 0.05 * self.mut_strength), 0.01, 0.8)
            if random.random() < m:
                mutated['regime_hysteresis'] = np.clip(mutated['regime_hysteresis'] + random.gauss(0, 0.05 * self.mut_strength), 0.01, 0.6)
            if random.random() < m:
                mutated['allocation_hysteresis'] = np.clip(mutated['allocation_hysteresis'] + random.gauss(0, 0.05 * self.mut_strength), 0.01, 0.5)
        return mutated

    def _crossover(self, g1, g2):
        child = json.loads(json.dumps(g1))
        if self.target_brain in ['all', 'regime']: child['regime'] = random.choice([g1, g2])['regime']
        if self.target_brain in ['all', 'bull']: child['bull'] = random.choice([g1, g2])['bull']
        if self.target_brain in ['all', 'bear']: child['bear'] = random.choice([g1, g2])['bear']
        if self.target_brain in ['all', 'regime']:
            for k in child['lookbacks']: child['lookbacks'][k] = random.choice([g1, g2])['lookbacks'][k]
            child['smoothing'] = (g1['smoothing'] + g2['smoothing']) / 2
        return child

    def _get_worker_config(self):
        return _evaluate_v12_phased_worker, (_init_worker, (CACHE_FILE, self.target_brain, self.regime_filter))
