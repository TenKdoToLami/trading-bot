import optuna
import json
import os
import numpy as np
import pandas as pd
from copy import deepcopy
from src.helpers.data_provider import CACHE_FILE
from strategies.genome_v14_nas import GenomeV14NAS
from src.tournament.runner import _execute_simulation

# --- CONFIG ---
TARGET_VERSION = "v14_nas"
CHAMPION_PATH = f"champions/{TARGET_VERSION}/genome.json"
N_TRIALS = 600
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
    # 1. Start with V13.10 Baseline
    if os.path.exists(CHAMPION_PATH):
        with open(CHAMPION_PATH, 'r') as f:
            genome = json.load(f)
    else:
        from src.tournament.evolution_v14_nas import EvolutionV14NAS
        genome = EvolutionV14NAS()._random_genome()
    
    # 2. Map V13 weights into V14 master slots if not already V14
    if genome.get('version', 0) < 14.0:
        # Re-init as Master Brains (32/16 max)
        old_sent = genome['sentinel']
        old_comm = genome['bear_commander']
        
        def upgrade_brain(old_b, max_hid):
            w = np.random.uniform(-0.5, 0.5, (np.array(old_b['w']).shape[0], max_hid))
            w[:, :np.array(old_b['w']).shape[1]] = np.array(old_b['w'])
            out_w = np.random.uniform(-1, 1, (max_hid, np.array(old_b['out_w']).shape[1]))
            out_w[:np.array(old_b['out_w']).shape[0], :] = np.array(old_b['out_w'])
            return {
                'w': w.tolist(),
                'b': np.zeros(max_hid).tolist(),
                'out_w': out_w.tolist(),
                'out_b': old_b['out_b']
            }
        
        genome['sentinel'] = upgrade_brain(old_sent, 32)
        genome['bear_commander'] = upgrade_brain(old_comm, 16)
        genome['version'] = 14.0

    # 3. NAS Optimization
    genome['sentinel_dim'] = trial.suggest_int('sentinel_dim', 2, 32)
    genome['commander_dim'] = trial.suggest_int('commander_dim', 2, 16)
    
    # 4. Conviction Params
    genome['skew_power'] = trial.suggest_float('skew_power', 1.0, 4.0)
    genome['conviction_cap'] = trial.suggest_float('conviction_cap', 0.75, 0.98)
    
    # 5. Standard Params
    lb = genome['lookbacks']
    lb['sma'] = trial.suggest_int('sma', 50, 500)
    lb['ema'] = trial.suggest_int('ema', 20, 200)
    lb['rsi'] = trial.suggest_int('rsi', 5, 60)
    
    genome['smoothing'] = trial.suggest_float('smoothing', 0.1, 0.6)
    
    # 6. Evaluation
    _init_worker_lazy()
    res = _execute_simulation(GenomeV14NAS, _worker_price_data, _worker_dates, {'genome': genome}, warmup_days=200)
    
    m = res['metrics']
    cagr, dd = m['cagr'] * 100, abs(m['max_dd']) * 100
    
    fitness = cagr
    if dd > 50.0:
        fitness -= (dd - 50.0) / 10
    
    # Sparsity Penalty
    fitness -= (genome['sentinel_dim'] + genome['commander_dim']) * 0.03
    
    return fitness

def run():
    print(f"=== OPTUNA: {TARGET_VERSION} (NAS) ===")
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(multivariate=True))
    
    if os.path.exists(CHAMPION_PATH):
        with open(CHAMPION_PATH, 'r') as f:
            cg = json.load(f)
            study.enqueue_trial({
                'sentinel_dim': 10,
                'commander_dim': 6,
                'skew_power': cg.get('skew_power', 2.0),
                'conviction_cap': cg.get('conviction_cap', 0.90),
                'sma': cg['lookbacks']['sma'],
                'ema': cg['lookbacks']['ema'],
                'rsi': cg['lookbacks']['rsi'],
                'smoothing': cg['smoothing']
            })

    study.optimize(objective, n_trials=N_TRIALS, n_jobs=CONCURRENCY)
    
    # --- SAVE BEST GENOME ---
    print("\n[+] Optimization Finished!")
    best_params = study.best_params
    print(f"[+] Best Fitness: {study.best_value:.2f}")
    
    # Rebuild the final genome
    with open(CHAMPION_PATH, 'r') as f:
        genome = json.load(f)
        
    # Apply NAS Upgrades
    old_sent = genome['sentinel']
    old_comm = genome['bear_commander']
    def upgrade_brain(old_b, max_hid):
        w = np.random.uniform(-0.5, 0.5, (np.array(old_b['w']).shape[0], max_hid))
        w[:, :np.array(old_b['w']).shape[1]] = np.array(old_b['w'])
        out_w = np.random.uniform(-1, 1, (max_hid, np.array(old_b['out_w']).shape[1]))
        out_w[:np.array(old_b['out_w']).shape[0], :] = np.array(old_b['out_w'])
        return { 'w': w.tolist(), 'b': np.zeros(max_hid).tolist(), 'out_w': out_w.tolist(), 'out_b': old_b['out_b'] }
    
    genome['sentinel'] = upgrade_brain(old_sent, 32)
    genome['bear_commander'] = upgrade_brain(old_comm, 16)
    genome['version'] = 14.0
    
    # Apply Best Params
    for k, v in best_params.items():
        if k in ['sma', 'ema', 'rsi']:
            genome['lookbacks'][k] = v
        else:
            genome[k] = v
            
    os.makedirs("champions/v14_nas", exist_ok=True)
    with open("champions/v14_nas/genome.json", "w") as f:
        json.dump(genome, f, indent=4)
    print(f"[+] Champion saved to: champions/v14_nas/genome.json")

if __name__ == "__main__":
    run()
