from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution
import random
import json
import os
from strategies.genome_v6_balancer import GenomeV6
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

def _evaluate_v6b_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=GenomeV6,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    fitness = cagr_pct - (dd_pct * 0.15)
    if dd_pct >= 95.0: fitness -= 1000
    return fitness, metrics, genome

@register_evolution("v6_balancer")
class EvolutionEngineV6(BaseEvolutionEngine):
    def __init__(self, **kwargs):
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc', 'mfi', 'bbw']
        self.brains = ['cash', '1x', '2x', '3x']
        self.lb_bounds = {'sma': (20, 300), 'ema': (10, 200), 'rsi': (5, 50), 'macd_f': (5, 30), 'macd_s': (15, 60), 'adx': (5, 50), 'trix': (5, 50), 'slope': (5, 50), 'vol': (5, 60), 'atr': (5, 50), 'mfi': (5, 60), 'bbw': (5, 60)}
        super().__init__(version_id="v6_balancer", **kwargs)

    def _random_genome(self):
        genome = {'brains': {b: {'w': {k: random.uniform(-4, 4) for k in self.indicators}, 'a': {k: (random.random() > 0.4 if self.use_ablation else True) for k in self.indicators}, 't': random.uniform(-1.0, 3.0)} for b in self.brains}, 'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()}, 'temp': random.uniform(0.1, 1.5), 'lock_days': random.uniform(1, 10), 'version': 'v6_balancer'}
        return genome

    def _mutate(self, genome):
        mut = json.loads(json.dumps(genome))
        for k, v in mut['lookbacks'].items():
            if random.random() < self.mut_rate: mn, mx = self.lb_bounds[k]; mut['lookbacks'][k] = max(mn, min(mx, v + int(random.gauss(0, (mx-mn)*0.1))))
        for b in self.brains:
            for k, v in mut['brains'][b]['w'].items():
                if random.random() < self.mut_rate: mut['brains'][b]['w'][k] += random.gauss(0, 0.8)
                if self.use_ablation and random.random() < 0.05: mut['brains'][b]['a'][k] = not mut['brains'][b]['a'][k]
            if random.random() < self.mut_rate:
                t = mut['brains'][b].get('t', 0.0)
                mut['brains'][b]['t'] = t + random.gauss(0, 0.5)
        if random.random() < self.mut_rate: mut['temp'] = max(0.1, min(3.0, mut['temp'] + random.gauss(0, 0.1)))
        if random.random() < self.mut_rate: mut['lock_days'] = max(1, min(20, mut['lock_days'] + random.gauss(0, 2)))
        return mut

    def _get_worker_config(self):
        return _evaluate_v6b_worker, (_init_worker, (CACHE_FILE,))

