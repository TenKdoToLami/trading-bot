# V4 Precision — 3-State AI Architecture

## 🧠 Strategy Logic
V4 Precision introduces a **Neutral Baseline** (1x SPY) to act as a buffer between Panic and Bullish extremes.

### ⚙️ Decision Engine
- **Dual Brains**: Uses a `Panic` brain and a `Bull` brain.
- **Evolved Perception**: Evolves independent **Lookback Periods** for every indicator (SMA, RSI, etc.) for each brain.

### 📈 Leverage States
- **CASH (Panic)**: Triggered if `Panic Brain > Threshold`.
- **3x SPY (Bullish)**: Triggered if `Bull Brain > Threshold`.
- **1x SPY (Neutral)**: The default state if neither brain is triggered.

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v4_precision/genome.json

# Behavioral X-Ray (Allocation DNA)
python tests/genome_xray.py champions/v4_precision/genome.json
```

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows). 
# --promote: Update main genome.json with the best performer.
# --top X: Retain only Top X most resilient genomes and prune the rest.
python tests/vault_sweep.py --vault champions/v4_precision/vault --promote --top 20
```

### 🧬 Evolution
```bash
# Cold Start Evolution
python tests/run_evolution_v4_precision.py --pop 300 --gen 100

# Seeded Evolution (Refine Champions)
python tests/run_evolution_v4_precision.py --pop 300 --gen 50 --seed champions/v4_precision/vault

### 🧪 Special Modifiers
- `--mutation 0.4`: Increase "Creative" mutation for exploration.
- `--min-cagr 0.40`: **Vault-Lock**. Prevents disk saves (vault and genome.json) for any genome failing to hit 40% CAGR, while allowing genetic discovery to continue.
- `--ablation`: Enable **Ablation Mode**. Allows the AI to evolve "False" states for indicators, effectively pruning its own logic tree for better generalization.
