from src.tournament.base_evolution import BaseEvolutionEngine
from src.tournament.evolution_registry import register_evolution
import random
import json
import os
import numpy as np
from strategies.genome_v2_multi import GenomeV2Strategy
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import CACHE_FILE

# --- GLOBAL WORKER STATE ---
_worker_price_data = None
_worker_dates = None
_worker_nitro_features = None
_worker_push_mid = False

def _init_worker(cache_file, push_mid=False):
    global _worker_price_data, _worker_dates, _worker_push_mid, _worker_nitro_features
    import pandas as pd
    from contextlib import redirect_stdout
    from src.helpers.indicators import (
        sma, ema, rsi, macd, adx, atr, trix, linear_regression_slope, realized_volatility
    )

    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            _worker_price_data = df.to_dict('records')
            _worker_dates = df.index
            _worker_push_mid = push_mid
            
            nitro = {}
            prices, highs, lows = [], [], []
            prev_ema, prev_atr, indicator_state = None, None, {}
            
            for i in range(len(_worker_price_data)):
                row = _worker_price_data[i]
                date = str(_worker_dates[i].date()); spy_price = row['close']
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
                    'atr': ((v_atr or 0.0) / spy_price) * 50,
                    'vix': (float(row.get('vix', 15.0)) - 20) / 10.0,
                    'yc': float(row.get('yield_curve', 0.0))
                }
            _worker_nitro_features = nitro

def _evaluate_v2_worker(genome):
    from contextlib import redirect_stdout
    import os
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull):
            res = _execute_simulation(
                strategy_type=GenomeV2Strategy,
                price_data_list=_worker_price_data,
                dates=_worker_dates,
                strategy_kwargs={'genome': genome, 'precalculated_features': _worker_nitro_features}
            )
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    fitness = cagr_pct - (dd_pct * 0.15)
    if dd_pct >= 95.0: fitness -= 1000
    
    if _worker_push_mid:
        holdings = [h[1] for h in res['portfolio'].holdings_log]
        mid_tier_days = sum(1 for h in holdings if 'SPY' in h or '2xSPY' in h)
        fitness += (mid_tier_days / len(holdings) * 15.0)
        
    return fitness, metrics, genome

@register_evolution("v2_multi")
class EvolutionEngineV2(BaseEvolutionEngine):
    def __init__(self, push_mid_tiers=False, **kwargs):
        self.push_mid_tiers = push_mid_tiers
        self.indicators = ['sma', 'ema', 'rsi', 'macd', 'adx', 'trix', 'slope', 'vol', 'atr', 'vix', 'yc']
        self.brains = ['panic', '3x', '2x', '1x']
        super().__init__(version_id="v2_multi", **kwargs)

    def _random_genome(self):
        genome = {b: {'w': {k: random.uniform(-4, 4) for k in self.indicators}, 'a': {k: (random.random() > 0.4 if self.use_ablation else True) for k in self.indicators}, 't': random.uniform(-1.5, 1.5)} for b in self.brains}
        genome['lock_days'] = random.uniform(0, 10)
        genome['version'] = 'v2_multi'
        return genome

    def _mutate(self, genome):
        mut = json.loads(json.dumps(genome))
        for b in self.brains:
            if random.random() < self.mut_rate: mut[b]['t'] += random.gauss(0, 0.2)
            for k in self.indicators:
                if random.random() < self.mut_rate: mut[b]['w'][k] += random.gauss(0, 0.5)
                if self.use_ablation and random.random() < 0.05: mut[b]['a'][k] = not mut[b]['a'][k]
        if random.random() < self.mut_rate: mut['lock_days'] = max(0, min(20, mut['lock_days'] + random.gauss(0, 2)))
        return mut

    def _get_worker_config(self):
        return _evaluate_v2_worker, (_init_worker, (CACHE_FILE, self.push_mid_tiers))

