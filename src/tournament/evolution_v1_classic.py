from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution
import random
import json
import os
import numpy as np
from strategies.genome_v1_classic import GenomeV1 as GenomeStrategy
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import CACHE_FILE

# --- GLOBAL WORKER STATE ---
_worker_price_data = None
_worker_dates = None
_worker_nitro_features = None

def _init_worker(cache_file):
    global _worker_price_data, _worker_dates, _worker_nitro_features
    import pandas as pd
    import os
    from contextlib import redirect_stdout
    from src.helpers.indicators import (
        sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility
    )

    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            _worker_price_data = df[['open', 'high', 'low', 'close', 'volume']].to_dict('records')
            _worker_dates = df.index
            
            nitro = {}
            prices, highs, lows = [], [], []
            prev_ema, prev_atr = None, None
            indicator_state = {}
            
            for i in range(len(_worker_price_data)):
                row = _worker_price_data[i]
                date = str(_worker_dates[i].date())
                spy_price = row['close']
                prices.append(spy_price); highs.append(row['high']); lows.append(row['low'])
                
                v_sma = sma(prices, 200)
                v_ema = ema(prices, 50, prev_ema=prev_ema); prev_ema = v_ema
                v_rsi = rsi(prices, 14, state=indicator_state)
                v_macd = macd(prices, 12, 26, state=indicator_state)[0] or 0.0
                v_adx = adx(highs, lows, prices, 14, state=indicator_state)
                v_trix = trix(prices, 15, state=indicator_state)
                v_slope = linear_regression_slope(prices, 20)
                v_vol = realized_volatility(prices, 20)
                v_atr = atr(highs, lows, prices, 14, prev_atr=prev_atr); prev_atr = v_atr

                nitro[date] = {
                    'sma': ((spy_price - v_sma) / v_sma * 5) if v_sma else 0.0,
                    'ema': ((spy_price - v_ema) / v_ema * 10) if v_ema else 0.0,
                    'rsi': ((v_rsi or 50) - 50) / 50.0,
                    'macd': v_macd / spy_price * 100,
                    'adx': ((v_adx or 25) - 25) / 25.0,
                    'trix': v_trix or 0.0,
                    'slope': (v_slope or 0.0) / spy_price * 1000,
                    'vol': (v_vol or 0.15) * 5,
                    'atr': ((v_atr or 0.0) / spy_price) * 50
                }
            _worker_nitro_features = nitro

def _evaluate_v1_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=GenomeStrategy,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome, 'precalculated_features': _worker_nitro_features}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    fitness = cagr_pct - (dd_pct * 0.15)
    if dd_pct >= 95.0: fitness -= 1000
    if metrics['num_rebalances'] == 0: fitness -= 2000
    return fitness, metrics, genome

@register_evolution("v1_classic")
class EvolutionEngineV1Classic(BaseEvolutionEngine):
    def __init__(self, **kwargs):
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr']
        super().__init__(version_id="v1_classic", **kwargs)

    def _random_genome(self):
        _rw = lambda: {k: random.uniform(-2, 2) for k in self.indicators}
        _ra = lambda: {k: (random.random() > 0.4 if self.use_ablation else True) for k in self.indicators}
        return {
            'panic_weights': _rw(), 'panic_active': _ra(), 'panic_threshold': random.uniform(0.5, 3.0),
            'base_weights': _rw(), 'base_active': _ra(), 'lock_days': random.uniform(0, 20),
            'version': 'v1_classic',
            'base_thresholds': {'tier_3x': 1.0, 'tier_2x': 0.3, 'tier_1x': -0.5}
        }

    def _mutate(self, genome):
        mut = json.loads(json.dumps(genome))
        # Adaptive strength: scale with mutation rate boost
        strength_multiplier = max(1.0, self.mut_rate / self.base_mut_rate)
        
        for g in ['panic', 'base']:
            for k in self.indicators:
                if random.random() < self.mut_rate: 
                    mut[f'{g}_weights'][k] += random.gauss(0, 0.5 * strength_multiplier)
                if self.use_ablation and random.random() < 0.05: 
                    mut[f'{g}_active'][k] = not mut[f'{g}_active'][k]
                    
        if random.random() < self.mut_rate: 
            mut['panic_threshold'] += random.gauss(0, 0.5 * strength_multiplier)
        if random.random() < self.mut_rate: 
            mut['lock_days'] = max(0, min(20, mut['lock_days'] + random.gauss(0, 2 * strength_multiplier)))
        return mut

    def _get_worker_config(self):
        return _evaluate_v1_worker, (_init_worker, (CACHE_FILE,))

