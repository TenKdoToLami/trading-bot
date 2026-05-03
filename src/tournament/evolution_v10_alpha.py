from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution
import random
import json
import os
import numpy as np
from copy import deepcopy
from strategies.genome_v10_alpha import GenomeV10Alpha
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import CACHE_FILE

# --- GLOBAL WORKER STATE ---
_worker_price_data = None
_worker_dates = None
_worker_profile_path = None

def _init_worker(cache_file, profile_path):
    global _worker_price_data, _worker_dates, _worker_profile_path
    import pandas as pd
    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    _worker_dates = df.index
    _worker_price_data = df[['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve']].to_dict('records')
    _worker_profile_path = profile_path

def _evaluate_v10_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=GenomeV10Alpha,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome, 'profile_path': _worker_profile_path}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    fitness = cagr_pct - (dd_pct * 0.15)
    if dd_pct >= 95.0: fitness -= 1000
    if metrics['num_rebalances'] == 0: fitness -= 2000
    return fitness, metrics, genome

@register_evolution("v10_alpha")
class EvolutionEngineV10Alpha(BaseEvolutionEngine):
    def __init__(self, **kwargs):
        self.profile_path = "champions/v10_alpha/indicator_profiles.json"
        with open(self.profile_path, 'r') as f:
            self.profile_data = json.load(f)['profiles']
        self.expert_keys = sorted(list(self.profile_data.keys()))
        self.num_experts = len(self.expert_keys)
        super().__init__(version_id="v10_alpha", **kwargs)

    def _random_genome(self):
        w_a = np.random.uniform(0, 1, (self.num_experts, 1)).tolist()
        w_b = np.random.uniform(-1, 1, (self.num_experts, 1)).tolist()
        w_c = np.random.uniform(-1, 1, (3, 4)).tolist()
        b_c = [-1.0, 1.0, 0.0, -1.0]
        
        return {
            'brain_a': {'w': w_a, 'b': [0.0]},
            'brain_b': {'w': w_b, 'b': [0.0]},
            'brain_c': {'w': w_c, 'b': b_c},
            'overrides': {'bear_veto_threshold': random.uniform(0.7, 0.95)},
            'indicator_profiles': self.profile_data,
            'version': 'v10_alpha'
        }

    def _mutate(self, genome):
        new_genome = deepcopy(genome)
        def _mutate_matrix(m, strength=0.2):
            m = np.array(m)
            mask = np.random.rand(*m.shape) < self.mut_rate
            m[mask] += np.random.normal(0, strength, m[mask].shape)
            return m.tolist()
        
        # Mutate Weights
        new_genome['brain_a']['w'] = _mutate_matrix(new_genome['brain_a']['w'])
        new_genome['brain_b']['w'] = _mutate_matrix(new_genome['brain_b']['w'])
        new_genome['brain_c']['w'] = _mutate_matrix(new_genome['brain_c']['w'])
        
        # Mutate Biases (New)
        new_genome['brain_a']['b'] = _mutate_matrix(new_genome['brain_a']['b'], 0.1)
        new_genome['brain_b']['b'] = _mutate_matrix(new_genome['brain_b']['b'], 0.1)
        new_genome['brain_c']['b'] = _mutate_matrix(new_genome['brain_c']['b'], 0.2)
        
        if random.random() < self.mut_rate:
            new_genome['overrides']['bear_veto_threshold'] = max(0.1, min(0.99, new_genome['overrides']['bear_veto_threshold'] + random.gauss(0, 0.05)))
        return new_genome

    def _crossover(self, p1, p2):
        """Hierarchical Brain Crossover."""
        child = deepcopy(p1)
        # Randomly swap entire brain modules
        if random.random() < 0.5: child['brain_a'] = deepcopy(p2['brain_a'])
        if random.random() < 0.5: child['brain_b'] = deepcopy(p2['brain_b'])
        if random.random() < 0.3: child['brain_c'] = deepcopy(p2['brain_c'])
        if random.random() < 0.3: child['overrides'] = deepcopy(p2['overrides'])
        return child

    def _get_worker_config(self):
        return _evaluate_v10_worker, (_init_worker, (CACHE_FILE, self.profile_path))
