import optuna
import json
import os
import numpy as np
import pandas as pd
from copy import deepcopy
import time
from tqdm import tqdm

from src.helpers.data_provider import CACHE_FILE
from strategies.genome_v13_moe_conviction import GenomeV13MOEConviction
from src.tournament.runner import _execute_simulation

# --- CONFIG ---
TARGET_VERSION = "v13_moe_conviction"
CHAMPION_PATH = f"champions/{TARGET_VERSION}/genome.json"
OUTPUT_PATH = f"champions/{TARGET_VERSION}/genome_optuna.json"
N_TRIALS = 600
CONCURRENCY = 18

# --- GLOBAL WORKER DATA ---
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
    # 1. Seed from primary champion
    if os.path.exists(CHAMPION_PATH):
        with open(CHAMPION_PATH, 'r') as f:
            genome = json.load(f)
    else:
        # Fallback to a random base if no champion exists
        from src.tournament.evolution_v13_moe_conviction import EvolutionV13MOEConviction
        eng = EvolutionV13MOEConviction()
        genome = eng._random_genome()
    
    # 2. Optimize Conviction Parameters (The New Engine)
    genome['skew_power'] = trial.suggest_float('skew_power', 1.0, 4.0)
    genome['conviction_cap'] = trial.suggest_float('conviction_cap', 0.75, 0.99)
    
    # 3. Optimize Standard Params
    lb = genome['lookbacks']
    lb['sma'] = trial.suggest_int('sma', 20, 500)
    lb['ema'] = trial.suggest_int('ema', 10, 300)
    lb['rsi'] = trial.suggest_int('rsi', 5, 60)
    lb['vol'] = trial.suggest_int('vol', 5, 100)
    
    genome['smoothing'] = trial.suggest_float('smoothing', 0.05, 0.6)
    genome['hysteresis'] = trial.suggest_float('hysteresis', 0.01, 0.4)
    genome['temp'] = trial.suggest_float('temp', 0.1, 3.0)

    # 4. Neural Gains (Ablation Style)
    def apply_neuron_gains(brain, gains, master):
        out_w = np.array(brain['out_w'])
        out_b = np.array(brain['out_b'])
        for i, g in enumerate(gains):
            if i < out_w.shape[0]: out_w[i, :] *= g
        out_w *= master
        out_b *= master
        brain['out_w'] = out_w.tolist()
        brain['out_b'] = out_b.tolist()
        return brain

    s_master = trial.suggest_float('s_master', 0.0, 2.5)
    s_neurons = [trial.suggest_float(f's_n_{i}', 0.0, 4.0) for i in range(10)]
    genome['sentinel'] = apply_neuron_gains(genome['sentinel'], s_neurons, s_master)
    
    bear_master = trial.suggest_float('bear_master', 0.0, 2.5)
    bear_neurons = [trial.suggest_float(f'bear_n_{i}', 0.0, 4.0) for i in range(6)]
    genome['bear_commander'] = apply_neuron_gains(genome['bear_commander'], bear_neurons, bear_master)

    # 5. Evaluation
    _init_worker_lazy()
    res = _execute_simulation(
        strategy_type=GenomeV13MOEConviction,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome},
        early_exit_dd=-0.95,
        warmup_days=200
    )
    
    m = res['metrics']
    cagr, dd = m['cagr'] * 100, abs(m['max_dd']) * 100
    
    trial.set_user_attr('cagr', cagr)
    trial.set_user_attr('dd', dd)
    
    # Fitness logic (Aggressive 50 + Sparsity)
    fitness = cagr
    if dd > 50.0:
        fitness -= (dd - 50.0)
    
    complexity = s_master + bear_master + sum(s_neurons) + sum(bear_neurons)
    fitness -= (complexity * 0.05)
    
    return fitness

def save_best_callback(study, trial, baseline_fitness):
    if study.best_trial.number != trial.number: return
    if trial.value <= baseline_fitness: return
    
    cagr = trial.user_attrs.get('cagr', 0)
    dd = trial.user_attrs.get('dd', 0)
    print(f"\n  [NEW BEST] Fitness: {trial.value:.2f} (Base: {baseline_fitness:.2f}) | CAGR: {cagr:.1f}% | DD: {dd:.1f}%")
    
    # Reconstruct and Save (Logic truncated for brevity, identical to v13.9 but with Conviction params)
    # [Saving Logic Here]

def run_optimization():
    print(f"=== OPTUNA: {TARGET_VERSION} (CONVICTION FOCUS) ===")
    _init_worker_lazy()
    
    # Establish Baseline
    baseline_fitness = -100.0
    if os.path.exists(CHAMPION_PATH):
        with open(CHAMPION_PATH, 'r') as f:
            base_g = json.load(f)
        res = _execute_simulation(GenomeV13MOEConviction, _worker_price_data, _worker_dates, {'genome': base_g}, early_exit_dd=-0.95, warmup_days=200)
        m = res['metrics']
        baseline_fitness = (m['cagr']*100) - ((abs(m['max_dd']*100)-50) if abs(m['max_dd']*100)>50 else 0) - (18 * 0.05)
        print(f"  [BASELINE] Fitness: {baseline_fitness:.2f}")

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(multivariate=True))
    
    # Enqueue Hot Seed if it exists
    if os.path.exists(CHAMPION_PATH):
        with open(CHAMPION_PATH, 'r') as f:
            cg = json.load(f)
        lb = cg['lookbacks']
        init_p = {
            'skew_power': cg.get('skew_power', 2.0),
            'conviction_cap': cg.get('conviction_cap', 0.90),
            'sma': lb['sma'], 'ema': lb['ema'], 'rsi': lb['rsi'], 'vol': lb['vol'],
            'smoothing': cg['smoothing'], 'hysteresis': cg['hysteresis'], 'temp': cg['temp'],
            's_master': 1.0, 'bear_master': 1.0
        }
        for i in range(10): init_p[f's_n_{i}'] = 1.0
        for i in range(6): init_p[f'bear_n_{i}'] = 1.0
        study.enqueue_trial(init_p)

    study.optimize(objective, n_trials=N_TRIALS, n_jobs=CONCURRENCY)

    # --- RECONSTRUCT AND SAVE BEST ---
    print("\n[+] Optimization Finished!")
    best_trial = study.best_trial
    print(f"[+] Best Fitness: {best_trial.value:.2f}")
    
    if os.path.exists(CHAMPION_PATH):
        with open(CHAMPION_PATH, 'r') as f: genome = json.load(f)
    else:
        from src.tournament.evolution_v13_moe_conviction import EvolutionV13MOEConviction
        genome = EvolutionV13MOEConviction()._random_genome()
    
    bp = best_trial.params
    
    # Apply Standard Params
    for k in ['skew_power', 'conviction_cap', 'smoothing', 'hysteresis', 'temp']:
        if k in bp: genome[k] = bp[k]
    for k in ['sma', 'ema', 'rsi', 'vol']:
        if k in bp: genome['lookbacks'][k] = bp[k]
        
    # Apply Neural Gains
    def apply_neuron_gains(brain, gains, master):
        out_w = np.array(brain['out_w'])
        out_b = np.array(brain['out_b'])
        for i, g in enumerate(gains):
            if i < out_w.shape[0]: out_w[i, :] *= g
        out_w *= master
        out_b *= master
        brain['out_w'] = out_w.tolist()
        brain['out_b'] = out_b.tolist()
        return brain

    s_gains = [bp.get(f's_n_{i}', 1.0) for i in range(10)]
    genome['sentinel'] = apply_neuron_gains(genome['sentinel'], s_gains, bp.get('s_master', 1.0))
    
    bear_gains = [bp.get(f'bear_n_{i}', 1.0) for i in range(6)]
    genome['bear_commander'] = apply_neuron_gains(genome['bear_commander'], bear_gains, bp.get('bear_master', 1.0))
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(genome, f, indent=4)
    print(f"[+] Optimized genome saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    run_optimization()
