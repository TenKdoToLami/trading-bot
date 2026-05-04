import random
import json
import os
from strategies.genome_v3_precision import GenomeV3Strategy
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import CACHE_FILE
from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution

# --- GLOBAL WORKER STATE ---
_worker_price_data = None
_worker_dates = None

def _init_worker(cache_file):
    global _worker_price_data, _worker_dates
    import pandas as pd
    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_price_data = df.to_dict('records')
    _worker_dates = df.index

def _evaluate_v3_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            # STAGE 1: LITE SCREENING (Last ~4 years)
            lite_res = _execute_simulation(
                strategy_type=GenomeV3Strategy,
                price_data_list=_worker_price_data[-1000:],
                dates=_worker_dates[-1000:],
                strategy_kwargs={'genome': genome}
            )
            if lite_res['metrics']['cagr'] <= 0: return -500.0, lite_res['metrics'], genome

            # STAGE 2: FULL AUDIT
            res = _execute_simulation(
                strategy_type=GenomeV3Strategy,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    fitness = cagr_pct - (dd_pct * 0.15)
    if dd_pct >= 95.0: fitness -= 1000
    return fitness, metrics, genome

@register_evolution("v3_precision")
class EvolutionEngineV3(BaseEvolutionEngine):
    def __init__(self, **kwargs):
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']
        self.brains = ['panic', 'bull']
        self.lb_bounds = {'sma': (20, 300), 'ema': (10, 200), 'rsi': (5, 50), 'macd_f': (5, 30), 'macd_s': (15, 60), 'adx': (5, 50), 'trix': (5, 50), 'slope': (5, 50), 'vol': (5, 60), 'atr': (5, 50)}
        super().__init__(version_id="v3_precision", **kwargs)

    def _random_genome(self):
        genome = {b: {'w': {k: random.uniform(-4, 4) for k in self.indicators}, 'a': {k: (random.random() > 0.4 if self.use_ablation else True) for k in self.indicators}, 't': random.uniform(-1.5, 1.5), 'lookbacks': {k: random.randint(mn, mx) for k, (mn, mx) in self.lb_bounds.items()}} for b in self.brains}
        genome['lock_days'] = random.uniform(0, 10)
        genome['version'] = 'v3_precision'
        return genome

    def _mutate(self, genome):
        mut = json.loads(json.dumps(genome))
        
        for b in ['panic', 'bull']:
            for k, v in mut[b]['lookbacks'].items():
                if random.random() < self.mut_rate: 
                    mn, mx = self.lb_bounds[k]
                    mut[b]['lookbacks'][k] = max(mn, min(mx, mut[b]['lookbacks'][k] + int(random.gauss(0, (mx-mn) * 0.15 * self.mut_strength))))
            if random.random() < self.mut_rate: 
                mut[b]['t'] += random.gauss(0, 0.2 * self.mut_strength)
            for k, v in mut[b]['w'].items():
                if random.random() < self.mut_rate: 
                    mut[b]['w'][k] += random.gauss(0, 0.5 * self.mut_strength)
                if self.use_ablation and random.random() < 0.05: 
                    mut[b]['a'][k] = not mut[b]['a'][k]
                    
        if random.random() < self.mut_rate: 
            mut['lock_days'] = max(0, min(40, mut['lock_days'] + random.gauss(0, 4 * self.mut_strength)))
        return mut

    def _get_worker_config(self):
        return _evaluate_v3_worker, (_init_worker, (CACHE_FILE,))
