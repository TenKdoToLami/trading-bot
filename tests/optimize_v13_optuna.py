"""
Optuna Optimizer for V13 MOE Full (v13.9) — The Grand Commander.
Aggressive mode: Bull Expert removed, 100% 3xSPY on Bull Authority.
"""

import optuna
import numpy as np
import pandas as pd
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from strategies.genome_v13_moe_full import GenomeV13MOEFull
from src.tournament.runner import _execute_simulation
from src.helpers.data_provider import load_spy_data, CACHE_FILE

# --- CONFIG ---
TARGET_VERSION = "v13_moe_full"
CHAMPION_PATH = "champions/v13_moe_full/genome.json"
OUTPUT_PATH = "champions/v13_moe_full/genome_optuna.json"
N_TRIALS = 600
CONCURRENCY = max(1, os.cpu_count() - 2)

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
    # 1. Always seed from the primary champion
    with open(CHAMPION_PATH, 'r') as f:
        genome = json.load(f)
    
    # 2. Optimize Lookbacks
    lb = genome['lookbacks']
    lb['sma'] = trial.suggest_int('sma', 20, 500)
    lb['ema'] = trial.suggest_int('ema', 10, 300)
    lb['rsi'] = trial.suggest_int('rsi', 5, 60)
    lb['vol'] = trial.suggest_int('vol', 5, 100)
    lb['macd_f'] = trial.suggest_int('macd_f', 5, 40)
    lb['macd_s'] = trial.suggest_int('macd_s', 15, 80)
    
    # 3. Optimize Top-Level Params
    genome['smoothing'] = trial.suggest_float('smoothing', 0.1, 0.9)
    genome['hysteresis'] = trial.suggest_float('hysteresis', 0.01, 0.5)
    genome['temp'] = trial.suggest_float('temp', 0.1, 5.0)
    
    # 4. Brain Scaling (Surgeon Mode: Neuron-Level Gains)
    def apply_neuron_gains(brain, neuron_gains, master_gain):
        brain = deepcopy(brain)
        out_w = np.array(brain['out_w'])
        out_b = np.array(brain['out_b'])
        for i in range(len(neuron_gains)):
            if i < out_w.shape[0]:
                out_w[i, :] *= neuron_gains[i]
        out_w *= master_gain
        out_b *= master_gain
        brain['out_w'] = out_w.tolist()
        brain['out_b'] = out_b.tolist()
        return brain

    s_master = trial.suggest_float('s_master', 0.0, 3.0)
    s_neurons = [trial.suggest_float(f's_n_{i}', 0.0, 5.0) for i in range(10)]
    genome['sentinel'] = apply_neuron_gains(genome['sentinel'], s_neurons, s_master)
    
    bear_master = trial.suggest_float('bear_master', 0.0, 3.0)
    bear_neurons = [trial.suggest_float(f'bear_n_{i}', 0.0, 5.0) for i in range(6)]
    genome['bear_commander'] = apply_neuron_gains(genome['bear_commander'], bear_neurons, bear_master)
    
    # 5. Run evaluation
    _init_worker_lazy()
    res = _execute_simulation(
        strategy_type=GenomeV13MOEFull,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': genome},
        early_exit_dd=-0.95, # Aggressive 95% limit
        warmup_days=200
    )
    
    metrics = res['metrics']
    cagr_pct, dd_pct = metrics['cagr'] * 100, abs(metrics['max_dd']) * 100
    
    # Store CAGR for callback
    trial.set_user_attr('cagr', cagr_pct)
    trial.set_user_attr('dd', dd_pct)
    
    # 1. Base Score
    fitness = cagr_pct
    
    if metrics.get('pruned'):
        return -100.0 # Massive penalty for near-total wipeout
    
    # 2. Aggressive 50 Penalty: 1% DD above 50% = 1 point hit
    if dd_pct > 50.0:
        fitness -= (dd_pct - 50.0) / 10
    
    # 3. Sparsity Penalty (Ablation Bias)
    # Penalty: 0.05 points per 1.0 of gain.
    # Encourages Optuna to set negligible neurons to 0.0.
    complexity = s_master + bear_master + sum(s_neurons) + sum(bear_neurons)
    fitness -= (complexity * 0.05)
    
    return fitness

def save_best_callback(study, trial, baseline_fitness):
    """Callback to save the best genome to vault only if it beats the baseline."""
    if study.best_trial.number != trial.number:
        return
        
    if trial.value <= baseline_fitness:
        return # Skip if not a real improvement over original

    cagr = trial.user_attrs.get('cagr', 0)
    dd = trial.user_attrs.get('dd', 0)
    
    if cagr < 20.0:
        return

    print(f"\n  [NEW BEST] Fitness: {trial.value:.2f} (Baseline: {baseline_fitness:.2f}) | CAGR: {cagr:.1f}% | DD: {dd:.1f}%")
    
    # Reconstruct from primary champion
    with open(CHAMPION_PATH, 'r') as f:
        best_genome = json.load(f)

    bp = trial.params
    for k in ['sma', 'ema', 'rsi', 'vol', 'macd_f', 'macd_s']:
        best_genome['lookbacks'][k] = bp[k]
    best_genome['smoothing'] = bp['smoothing']
    best_genome['hysteresis'] = bp['hysteresis']
    best_genome['temp'] = bp['temp']
    
    def apply_neuron_gains_inplace(brain, neuron_gains, master_gain):
        out_w = np.array(brain['out_w'])
        out_b = np.array(brain['out_b'])
        for i in range(len(neuron_gains)):
            if i < out_w.shape[0]:
                out_w[i, :] *= neuron_gains[i]
        out_w *= master_gain
        out_b *= master_gain
        brain['out_w'] = out_w.tolist()
        brain['out_b'] = out_b.tolist()

    apply_neuron_gains_inplace(best_genome['sentinel'], [bp[f's_n_{i}'] for i in range(10)], bp['s_master'])
    apply_neuron_gains_inplace(best_genome['bear_commander'], [bp[f'bear_n_{i}'] for i in range(6)], bp['bear_master'])

    # Final Save
    vault_name = f"v13_moe_full_cagr_{cagr:.1f}_dd_{dd:.1f}.json"
    vault_path = os.path.join("champions", TARGET_VERSION, "vault", vault_name)
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(best_genome, f, indent=4)
        
    os.makedirs(os.path.dirname(vault_path), exist_ok=True)
    with open(vault_path, 'w') as f:
        json.dump(best_genome, f, indent=4)

def run_optimization():
    print(f"=== OPTUNA OPTIMIZER (CHAMPION FOCUS MODE): {TARGET_VERSION} ===")
    print(f"  [SEED] Evaluating baseline from: {CHAMPION_PATH}")
    
    # 1. Evaluate baseline fitness
    _init_worker_lazy()
    with open(CHAMPION_PATH, 'r') as f:
        original_genome = json.load(f)
    
    res = _execute_simulation(
        strategy_type=GenomeV13MOEFull,
        price_data_list=_worker_price_data,
        dates=_worker_dates,
        strategy_kwargs={'genome': original_genome},
        early_exit_dd=-0.95,
        warmup_days=200
    )
    
    m = res['metrics']
    cagr_pct, dd_pct = m['cagr'] * 100, abs(m['max_dd']) * 100
    baseline_fitness = cagr_pct
    if dd_pct > 50.0:
        baseline_fitness -= (dd_pct - 50.0) / 10
        
    # Subtract same Sparsity Penalty as objective
    # Original genome has all gains at 1.0 implicitly for the baseline
    complexity = 1.0 + 1.0 + 10.0 + 6.0 # s_master + bear_master + 10 s_neurons + 6 bear_neurons
    baseline_fitness -= (complexity * 0.05)
    
    print(f"  [BASELINE] Adjusted Fitness: {baseline_fitness:.2f} | CAGR: {cagr_pct:.1f}% | DD: {dd_pct:.1f}%")

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(multivariate=True)
    )
    
    # 2. THE ABLATION SUITE (Local Sensitivity Mapping)
    lb = original_genome['lookbacks']
    
    def get_base():
        base = {
            'sma': lb['sma'], 'ema': lb['ema'], 'rsi': lb['rsi'],
            'vol': lb['vol'], 'macd_f': lb['macd_f'], 'macd_s': lb['macd_s'],
            'smoothing': original_genome['smoothing'],
            'hysteresis': original_genome['hysteresis'],
            'temp': original_genome['temp'],
            's_master': 1.0, 'bear_master': 1.0
        }
        for i in range(10): base[f's_n_{i}'] = 1.0
        for i in range(6): base[f'bear_n_{i}'] = 1.0
        return base

    # Trial 1: Exact Champion
    study.enqueue_trial(get_base())

    # Trials 2-11: Sentinel Neuron Ablation (One by one)
    for i in range(10):
        ab = get_base()
        ab[f's_n_{i}'] = 0.0 # Kill this neuron
        study.enqueue_trial(ab)

    # Trials 12-17: Bear Neuron Ablation (One by one)
    for i in range(6):
        ab = get_base()
        ab[f'bear_n_{i}'] = 0.0 # Kill this neuron
        study.enqueue_trial(ab)

    # Trials 18-21: Parameter Extremes
    for t_val in [0.1, 2.0]:
        ab = get_base()
        ab['temp'] = t_val
        study.enqueue_trial(ab)
    
    for s_val in [0.1, 0.8]:
        ab = get_base()
        ab['smoothing'] = s_val
        study.enqueue_trial(ab)

    print(f"  [ABLATION SUITE] Enqueued 21 trials to map local sensitivity.")
    
    print(f"  [START] Running {N_TRIALS} trials (Multivariate TPE) with {CONCURRENCY} workers...")
    
    try:
        study.optimize(
            objective,
            n_trials=N_TRIALS,
            n_jobs=CONCURRENCY,
            callbacks=[lambda s, t: save_best_callback(s, t, baseline_fitness)]
        )
    except KeyboardInterrupt:
        print("\n  [INTERRUPT] Optimization stopped by user.")

    print("\n==================================================")
    print(f"  OPTIMIZATION COMPLETE")
    try:
        print(f"  Best Fitness: {study.best_value:.2f}")
    except:
        pass
    print("==================================================")

if __name__ == "__main__":
    run_optimization()
