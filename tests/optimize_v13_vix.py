import optuna
import json
import os
import numpy as np
import pandas as pd
from copy import deepcopy
from src.helpers.data_provider import CACHE_FILE
from strategies.genome_v13_moe_vix import GenomeV13MOEVIX
from src.tournament.runner import _execute_simulation

# --- CONFIG ---
TARGET_VERSION = "v13_moe_vix"
CHAMPION_PATH = f"champions/{TARGET_VERSION}/genome.json"
N_TRIALS = 400
CONCURRENCY = 18

_worker_price_data = None
_worker_dates = None

def _init_worker_lazy():
    global _worker_price_data, _worker_dates
    if _worker_price_data is not None:
        return
    df = pd.read_csv(CACHE_FILE, index_col=0, parse_dates=True)
    _worker_dates = df.index
    cols = ['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve', 'credit_spread', 
            'month_sin', 'month_cos', 'is_tom', 'tlt_proxy', 'shy_proxy', 'gold']
    existing_cols = [c for c in cols if c in df.columns]
    _worker_price_data = df[existing_cols].to_dict('records')

def objective(trial):
    # Load Seed
    if os.path.exists(CHAMPION_PATH):
        with open(CHAMPION_PATH, 'r') as f: genome = json.load(f)
    else:
        from src.tournament.evolution_v13_moe_vix import EvolutionV13MOEVIX
        genome = EvolutionV13MOEVIX()._random_genome()
    
    # Optimize VIX Parameters
    genome['vix_base_cap'] = trial.suggest_float('vix_base_cap', 0.65, 0.95)
    genome['vix_sensitivity'] = trial.suggest_float('vix_sensitivity', 0.0, 0.04)
    genome['skew_power'] = trial.suggest_float('skew_power', 1.0, 4.0)
    
    # Standard Params
    lb = genome['lookbacks']
    lb['sma'] = trial.suggest_int('sma', 50, 500)
    lb['ema'] = trial.suggest_int('ema', 20, 200)
    genome['smoothing'] = trial.suggest_float('smoothing', 0.1, 0.6)
    
    _init_worker_lazy()
    res = _execute_simulation(GenomeV13MOEVIX, _worker_price_data, _worker_dates, {'genome': genome}, warmup_days=200)
    
    m = res['metrics']
    cagr, dd = m['cagr'] * 100, abs(m['max_dd']) * 100
    
    fitness = cagr
    if dd > 50.0:
        fitness -= (dd - 50.0)
        
    return fitness

def run():
    print(f"=== OPTUNA: {TARGET_VERSION} (ADAPTIVE VIX) ===")
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(multivariate=True))
    
    # Hot Seed from V13.10 if available
    if not os.path.exists(CHAMPION_PATH) and os.path.exists("champions/v13_moe_conviction/genome.json"):
        with open("champions/v13_moe_conviction/genome.json", "r") as f:
            cg = json.load(f)
            init_p = {
                'vix_base_cap': cg.get('conviction_cap', 0.90),
                'vix_sensitivity': 0.01,
                'skew_power': cg.get('skew_power', 2.0),
                'sma': cg['lookbacks']['sma'],
                'ema': cg['lookbacks']['ema'],
                'smoothing': cg['smoothing']
            }
            study.enqueue_trial(init_p)

    study.optimize(objective, n_trials=N_TRIALS, n_jobs=CONCURRENCY)

if __name__ == "__main__":
    run()
