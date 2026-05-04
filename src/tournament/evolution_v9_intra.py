from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution
import random
import json
import os
import numpy as np
from strategies.genome_v9_intra import GenomeV9Intra
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
    _worker_price_data = df[['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve']].to_dict('records')

def _evaluate_v9_intra_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=GenomeV9Intra,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    fitness = cagr_pct - (dd_pct * 0.15)
    
    # INSTITUTIONAL STANDARDS
    if dd_pct >= 90.0: fitness -= 1000   # Protect against near-total wipeouts
    if metrics['num_rebalances'] <= 1: fitness -= 2000 # Penalize Buy & Hold / Dormancy
    return fitness, metrics, genome

@register_evolution("v9_intra")
class EvolutionEngineV9Intra(BaseEvolutionEngine):
    def __init__(self, **kwargs):
        self.lb_bounds = {
            'sma': (20, 300), 'ema': (10, 200), 'rsi': (5, 50), 'macd_f': (5, 30),
            'macd_s': (15, 60), 'adx': (5, 50), 'trix': (5, 50), 'slope': (5, 50),
            'vol': (5, 60), 'atr': (5, 50), 'mfi': (5, 60), 'bb': (5, 60)
        }
        super().__init__(version_id="v9_intra", **kwargs)

    def _random_genome(self):
        layers = []
        # Tighter weights for hidden layer, more sensitive for output layer
        layers.append({'w': (np.random.randn(14, 24) * 0.5).tolist(), 'b': (np.random.randn(24) * 0.1).tolist()})
        layers.append({'w': np.random.uniform(-1, 1, (24, 4)).tolist(), 'b': np.random.uniform(-0.1, 0.1, 4).tolist()})
        return {
            'version': 'v9_intra', 'layers': layers,
            'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()},
            'hysteresis': random.uniform(0.01, 0.4), 'smoothing': random.uniform(0.1, 0.8)
        }

    def _mutate(self, genome):
        mutated = json.loads(json.dumps(genome))
        mutated.pop('lock_days', None); mutated['version'] = 'v9_intra' # Scrub seeding metadata
        
        for layer in mutated['layers']:
            w, b = np.array(layer['w']), np.array(layer['b'])
            if random.random() < self.mut_rate:
                w += np.random.normal(0, 0.05 * self.mut_strength, w.shape)
                b += np.random.normal(0, 0.02 * self.mut_strength, b.shape)
            layer['w'], layer['b'] = w.tolist(), b.tolist()

        for k, v in mutated['lookbacks'].items():
            if random.random() < self.mut_rate:
                mn, mx = self.lb_bounds[k]
                mutated['lookbacks'][k] = max(mn, min(mx, v + int(random.gauss(0, (mx-mn) * 0.1 * self.mut_strength))))
        
        if random.random() < self.mut_rate: 
            mutated['hysteresis'] = max(0.005, min(0.8, mutated['hysteresis'] + random.gauss(0, 0.05 * self.mut_strength)))
        if random.random() < self.mut_rate: 
            mutated['smoothing'] = max(0.05, min(0.98, mutated['smoothing'] + random.gauss(0, 0.1 * self.mut_strength)))
        return mutated

    def _get_worker_config(self):
        return _evaluate_v9_intra_worker, (_init_worker, (CACHE_FILE,))
