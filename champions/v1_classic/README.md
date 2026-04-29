# V1 Classic — The Original GA Hybrid

## 🧠 Strategy Logic
V1 Classic is the first evolved version of the Tactical Bot. It uses a **Linear Weight-Sum** brain to switch between Risk-On and Risk-Off states. It combines historical SMA rules with genetically optimized weights for indicators like RSI and Volatility.

### ⚙️ Decision Engine
- **Panic vs Base**: Uses two distinct weight sets (`panic_weights` and `base_weights`).
- **Threshold Switching**: Evolved thresholds determine when to flip into defensive mode.
- **Genetic Selection**: Optimized via tournament-based evolution.

### 📈 Leverage States
- **CASH / 1x / 3x**

---

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v1_classic/genome.json
```

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows). 
# --promote: Update main genome.json with the best performer.
# --top X: Retain only Top X most resilient genomes and prune the rest.
python tests/vault_sweep.py --vault champions/v1_classic/vault --promote --top 20
```

### 🧬 Evolution
Breeds the optimal weight-sum brain using a Genetic Algorithm.
```bash
# Standard Evolution run
python tests/run_evolution_v1_classic.py --pop 500 --gen 100

# Seeded Evolution (Refine using your best vaulted genomes)
python tests/run_evolution_v1_classic.py --pop 500 --gen 100 --seed champions/v1_classic/vault
```

#### ⚙️ Evolution Parameters
| Flag | Default | Description |
|------|---------|-------------|
| `--pop` | 30 | Population size. Higher = more diversity, slower generations. |
| `--gen` | 10 | Number of generations to evolve. |
| `--mut` | 0.15 | Mutation rate. Use `0.25 - 0.40` for exploration, `0.05` for fine-tuning. |
| `--seed`| None | Path to a `vault/` directory to load initial winners from. |
| `--ablation` | Off | **Feature Selection**: Disables indicators randomly to find the most robust subset. |
