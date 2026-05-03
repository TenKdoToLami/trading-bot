from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution
import random
import json
import os
from strategies.genome_v5_sniper import GenomeV5Sniper
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

def _evaluate_v5s_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=GenomeV5Sniper,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    fitness = cagr_pct - (dd_pct * 0.15)
    if dd_pct >= 95.0: fitness -= 1000
    return fitness, metrics, genome

@register_evolution("v5_sniper")
class EvolutionEngineV5Sniper(BaseEvolutionEngine):
    def __init__(self, **kwargs):
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']
        self.lb_bounds = {'sma': (20, 300), 'ema': (10, 200), 'rsi': (5, 50), 'macd_f': (5, 30), 'macd_s': (15, 60), 'adx': (5, 50), 'trix': (5, 50), 'slope': (5, 50), 'vol': (5, 60), 'atr': (5, 50)}
        super().__init__(version_id="v5_sniper", **kwargs)

    def _random_genome(self):
        t1 = random.uniform(0.5, 3.0); t2 = t1 + random.uniform(0.5, 3.0)
        return {'sniper': {'w': {k: random.uniform(-4, 4) for k in self.indicators}, 'a': {k: (random.random() > 0.4 if self.use_ablation else True) for k in self.indicators}, 't_low': t1, 't_high': t2, 'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()}}, 'lock_days': random.uniform(1, 10), 'version': 'v5_sniper'}

    def _mutate(self, genome):
        mut = json.loads(json.dumps(genome))
        for k, v in mut['sniper']['lookbacks'].items():
            if random.random() < self.mut_rate: mn, mx = self.lb_bounds[k]; mut['sniper']['lookbacks'][k] = max(mn, min(mx, v + int(random.gauss(0, (mx-mn)*0.1))))
        if random.random() < self.mut_rate: mut['sniper']['t_low'] += random.gauss(0, 0.5)
        if random.random() < self.mut_rate: mut['sniper']['t_high'] = max(mut['sniper']['t_low'] + 0.1, mut['sniper']['t_high'] + random.gauss(0, 0.5))
        for k, v in mut['sniper']['w'].items():
            if random.random() < self.mut_rate: mut['sniper']['w'][k] += random.gauss(0, 0.8)
            if self.use_ablation and random.random() < 0.05: mut['sniper']['a'][k] = not mut['sniper']['a'][k]
        mut['lock_days'] = max(1, min(20, mut['lock_days'] + random.gauss(0, 2))) if random.random() < self.mut_rate else mut['lock_days']
        return mut

    def _get_worker_config(self):
        return _evaluate_v5s_worker, (_init_worker, (CACHE_FILE,))

