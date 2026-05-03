from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution
import random
import json
import os
from strategies.genome_v4_precision import GenomeV4Precision
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
    _worker_price_data = df.to_dict('records')

def _evaluate_v4p_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            lite_res = _execute_simulation(
                strategy_type=GenomeV4Precision,
                price_data_list=_worker_price_data[-1000:],
                dates=_worker_dates[-1000:],
                strategy_kwargs={'genome': genome}
            )
            if lite_res['metrics']['cagr'] <= 0: return -500.0, lite_res['metrics'], genome
            res = _execute_simulation(
                strategy_type=GenomeV4Precision,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    fitness = cagr_pct - (dd_pct * 0.15)
    if dd_pct >= 95.0: fitness -= 1000
    return fitness, metrics, genome

@register_evolution("v4_precision")
class EvolutionEngineV4Precision(BaseEvolutionEngine):
    def __init__(self, **kwargs):
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']
        self.brains = ['panic', 'bull']
        self.lb_bounds = {'sma': (10, 500), 'ema': (10, 300), 'rsi': (5, 100), 'macd_f': (5, 50), 'macd_s': (15, 120), 'adx': (5, 100), 'trix': (5, 100), 'slope': (5, 200), 'vol': (5, 252), 'atr': (5, 100)}
        super().__init__(version_id="v4_precision", **kwargs)

    def _random_genome(self):
        genome = {b: {'w': {k: random.uniform(-10, 10) for k in self.indicators}, 'a': {k: (random.random() > 0.4 if self.use_ablation else True) for k in self.indicators}, 't': random.uniform(-50, 50), 'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()}} for b in self.brains}
        genome['lock_days'], genome['version'] = random.uniform(0, 20), 'v4_precision'
        return genome

    def _mutate(self, genome):
        mut = json.loads(json.dumps(genome))
        for b in self.brains:
            for k, v in mut[b]['lookbacks'].items():
                if random.random() < self.mut_rate: mn, mx = self.lb_bounds[k]; mut[b]['lookbacks'][k] = max(mn, min(mx, v + int(random.gauss(0, (mx-mn)*0.15))))
            if random.random() < self.mut_rate: mut[b]['t'] += random.gauss(0, 1.2)
            for k, v in mut[b]['w'].items():
                if random.random() < self.mut_rate: mut[b]['w'][k] += random.gauss(0, 1.2)
                if self.use_ablation and random.random() < 0.05: mut[b]['a'][k] = not mut[b]['a'][k]
        mut['lock_days'] = max(0, min(40, mut['lock_days'] + random.gauss(0, 4))) if random.random() < self.mut_rate else mut['lock_days']
        return mut

    def _get_worker_config(self):
        return _evaluate_v4p_worker, (_init_worker, (CACHE_FILE,))

