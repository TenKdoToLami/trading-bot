from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution
import random
import json
import os
from strategies.genome_v1_manual import ManualV1
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

def _evaluate_v1m_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=ManualV1,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    fitness = cagr_pct - (dd_pct * 0.15)
    if dd_pct >= 95.0: fitness -= 1000
    if metrics['num_rebalances'] == 0: fitness -= 2000
    return fitness, metrics, genome

@register_evolution("v1_manual")
class EvolutionEngineV1Manual(BaseEvolutionEngine):
    def __init__(self, **kwargs):
        super().__init__(version_id="v1_manual", **kwargs)

    def _random_genome(self):
        return {
            "sma": random.randint(50, 400),
            "min_b_days": random.randint(1, 20),
            "bounds_p": sorted([random.uniform(10, 30), random.uniform(30, 50), random.uniform(50, 80)]),
            "weights_p": [[random.random(), random.random(), random.random()] for _ in range(4)],
            "version": "v1_manual"
        }

    def _mutate(self, genome):
        mut = json.loads(json.dumps(genome))
        if random.random() < self.mut_rate: mut['sma'] = max(50, min(500, mut['sma'] + int(random.gauss(0, 20))))
        if random.random() < self.mut_rate: mut['min_b_days'] = max(1, min(60, mut['min_b_days'] + int(random.gauss(0, 2))))
        if random.random() < self.mut_rate: 
            mut['bounds_p'] = sorted([max(5, min(100, b + random.gauss(0, 5))) for b in mut['bounds_p']])
        for i in range(len(mut['weights_p'])):
            for j in range(len(mut['weights_p'][i])):
                if random.random() < self.mut_rate: mut['weights_p'][i][j] = max(0, min(1.0, mut['weights_p'][i][j] + random.gauss(0, 0.1)))
        return mut

    def _get_worker_config(self):
        return _evaluate_v1m_worker, (_init_worker, (CACHE_FILE,))

