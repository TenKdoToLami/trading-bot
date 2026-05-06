import json
import numpy as np
import pandas as pd
from src.helpers.data_provider import CACHE_FILE
from strategies.genome_v13_moe_full import GenomeV13MOEFull
from strategies.genome_v13_moe_conviction import GenomeV13MOEConviction
from src.tournament.runner import _execute_simulation

def analyze_regime_split(name, strategy_cls, genome_path):
    with open(genome_path, 'r') as f:
        genome = json.load(f)
    
    df = pd.read_csv(CACHE_FILE, index_col=0, parse_dates=True)
    res = _execute_simulation(strategy_type=strategy_cls, price_data_list=df.to_dict('records'), dates=df.index, strategy_kwargs={'genome': genome}, warmup_days=200)
    
    p_bull = np.array(res['telemetry'].get('p_bull', []))
    total = len(p_bull)
    
    return {
        "Pure Bull (100%)": np.sum(p_bull >= 0.999) / total * 100,
        "Strong Bull (80-99%)": np.sum((p_bull >= 0.80) & (p_bull < 0.999)) / total * 100,
        "Mild Bull (60-80%)": np.sum((p_bull >= 0.60) & (p_bull < 0.80)) / total * 100,
        "Hedged (40-60%)": np.sum((p_bull >= 0.40) & (p_bull < 0.60)) / total * 100,
        "Mild Bear (20-40%)": np.sum((p_bull >= 0.20) & (p_bull < 0.40)) / total * 100,
        "Strong Bear (1-20%)": np.sum((p_bull > 0.001) & (p_bull < 0.20)) / total * 100,
        "Pure Bear (100%)": np.sum(p_bull <= 0.001) / total * 100
    }

if __name__ == "__main__":
    v13_9 = analyze_regime_split("V13.9 Full", GenomeV13MOEFull, "champions/v13_moe_full/genome.json")
    v13_10 = analyze_regime_split("V13.10 Convict", GenomeV13MOEConviction, "champions/v13_moe_conviction/genome.json")
    
    print("\n=== REGIME EXPOSURE MATRIX: ASSET SPLIT COMPARISON ===")
    print(f"{'Regime Bracket':<22} | {'V13.9 (Full)':<15} | {'V13.10 (Convict)':<15}")
    print("-" * 60)
    for k in v13_9.keys():
        print(f"{k:<22} | {v13_9[k]:>13.1f}% | {v13_10[k]:>13.1f}%")
    print("-" * 60)
