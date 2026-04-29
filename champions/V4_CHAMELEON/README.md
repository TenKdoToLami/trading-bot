# V4 Chameleon — Volatility Adaptive Brain

## 🧠 Strategy Logic
V4 Chameleon is designed for **Regime Resilience**. It monitors market volatility (VIX EMA) and automatically adjusts its logic tree based on whether the market is in a "Quiet Accumulation" phase or a "High-Volatility Shock" phase.

### ⚙️ Decision Engine
- **Volatility Scaling**: Dynamically adjusts indicator importance based on market stress.
- **Genetic Lookbacks**: Every indicator's lookback period is evolved for maximum fidelity.
- **Ablation Ready**: Supports evolutionary pruning of useless indicators.

### 📈 Leverage States
- **CASH / 1x / 3x**

---

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/V4_CHAMELEON/genome.json
```

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows). 
# --promote: Update main genome.json with the best performer.
# --top X: Retain only Top X most resilient genomes and prune the rest.
python tests/vault_sweep.py --vault champions/V4_CHAMELEON/vault --promote --top 20
```

### 🧬 Evolution
Optimizes the adaptive logic tree using Gaussian Neuroevolution.
```bash
# Adaptive Volatility Evolution
python tests/run_evolution_v4.py --pop 40 --gen 15 --seed champions/V4_CHAMELEON/vault
```

#### ⚙️ Evolution Parameters
| Flag | Default | Description |
|------|---------|-------------|
| `--pop` | 40 | Population size (Lower for V4 due to higher computational cost). |
| `--gen` | 15 | Number of generations. |
| `--mut` | 0.20 | Mutation rate (regime switching probability). |
| `--seed`| champions/V4_CHAMELEON/vault | Path to vault dir to seed population. |
