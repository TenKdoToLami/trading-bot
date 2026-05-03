from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution
import random
import json
import os
import numpy as np
from strategies.genome_v7_deep import GenomeV7Deep
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

def _evaluate_v7d_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=GenomeV7Deep,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    fitness = cagr_pct - (dd_pct * 0.15)
    if dd_pct >= 95.0: fitness -= 1000
    return fitness, metrics, genome

@register_evolution("v7_deep")
class EvolutionEngineV7(BaseEvolutionEngine):
    def __init__(self, **kwargs):
        self.lb_bounds = {'sma': (20, 300), 'ema': (10, 200), 'rsi': (5, 50), 'macd_f': (5, 30), 'macd_s': (15, 60), 'adx': (5, 50), 'trix': (5, 50), 'slope': (5, 50), 'vol': (5, 60), 'atr': (5, 50), 'mfi': (5, 60), 'bb': (5, 60)}
        super().__init__(version_id="v7_deep", **kwargs)

    def _random_genome(self):
        return {'version': 'v7_deep', 'layers': [{'w': np.random.uniform(-1, 1, (13, 24)).tolist(), 'b': np.random.uniform(-0.1, 0.1, 24).tolist()}, {'w': np.random.uniform(-1, 1, (24, 4)).tolist(), 'b': np.random.uniform(-0.1, 0.1, 4).tolist()}], 'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()}, 'lock_days': random.uniform(1, 10)}

    def _mutate(self, genome):
        mut = json.loads(json.dumps(genome))
        for layer in mut['layers']:
            w, b = np.array(layer['w']), np.array(layer['b'])
            if random.random() < self.mut_rate: w += np.random.normal(0, 0.05, w.shape); b += np.random.normal(0, 0.02, b.shape)
            layer['w'], layer['b'] = w.tolist(), b.tolist()
        for k, v in mut['lookbacks'].items():
            if random.random() < self.mut_rate: mn, mx = self.lb_bounds[k]; mut['lookbacks'][k] = max(mn, min(mx, v + int(random.gauss(0, (mx-mn)*0.1))))
        mut['lock_days'] = max(1, min(14, mut['lock_days'] + random.gauss(0, 1))) if random.random() < self.mut_rate else mut['lock_days']
        return mut

    def _get_worker_config(self):
        return _evaluate_v7d_worker, (_init_worker, (CACHE_FILE,))

