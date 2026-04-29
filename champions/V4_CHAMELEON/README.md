# V4 Chameleon — Volatility Adaptive Brain

## 🧠 Strategy Logic
V4 Chameleon is designed for **Regime Resilience**. It monitors market volatility (VIX EMA) and automatically adjusts its logic tree based on whether the market is in a "Quiet Accumulation" phase or a "High-Volatility Shock" phase.

### ⚙️ Decision Engine
- **Volatility Scaling**: Dynamically adjusts indicator importance based on market stress.
- **Genetic Lookbacks**: Every indicator's lookback period is evolved for maximum fidelity.
- **Ablation Ready**: Supports evolutionary pruning of useless indicators.

### 📈 Leverage States
- **CASH / 1x / 2x / 3x**

---

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v4_chameleon/genome.json
```

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows). 
# --promote: Update main genome.json with the best performer.
# --top X: Retain only Top X most resilient genomes and prune the rest.
python tests/vault_sweep.py --vault champions/v4_chameleon/vault --promote --top 20
```

### 🧬 Evolution
Optimizes the adaptive logic tree using Gaussian Neuroevolution.
```bash
python tests/run_evolution_v4_chameleon.py --pop 1000 --gen 100 --mut 0.25 --ablation

# High-Diversity Seeded Evolution
python tests/run_evolution_v4_chameleon.py --pop 1000 --gen 100 --mut 0.25 --ablation --seed champions/v4_chameleon/vault
```

#### ⚙️ Evolution Parameters
| Flag | Default | Description |
|------|---------|-------------|
| `--pop` | 40 | Population size. Recommend `100+` for diverse runs. |
| `--gen` | 15 | Number of generations. |
| `--mut` | 0.20 | Mutation rate (DNA change probability). |
| `--seed`| `None` | Path to vault dir to seed population. |
| `--ablation` | `Off` | Enable "Indicator Ablation" (Dynamic pruning of weak signals). |
