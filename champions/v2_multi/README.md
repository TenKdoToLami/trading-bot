# V2 Multi — Multi-Leverage AI

## 🧠 Strategy Logic
V2 was the first version to explore **Multi-Asset Leverage**. It uses four distinct "Brain states" to select between discrete leverage levels.

### ⚙️ Decision Engine
- **4-Regime Selection**: Panic, 1x, 2x, and 3x brains.
- **Priority Waterfall**: Safety (Panic) first, then Aggression (3x), then Stability (2x/1x).
- **Lockout Mechanism**: Prevents churn with a configurable `lock_days` window (bypassed by Panic exits).

### 📈 Leverage States
- **CASH / 1x / 2x / 3x**

---

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v2_multi/genome.json

# Behavioral X-Ray (Logic DNA)
python tests/genome_xray.py champions/v2_multi/genome.json
```

### 🧬 Genetic Evolution (Nitro Mode)
V2 now supports **Nitro Mode** (pre-calculated indicators), allowing for massive population sizes.

```bash
# High-Diversity Seeded Evolution (Fast)
python tests/run_evolution_v2_multi.py --pop 1000 --gen 100 --seed champions/v2_multi/vault
```

#### ⚙️ Evolution Parameters
| Parameter | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `50` | Population size. Recommend `500+` for Nitro. |
| `--gen` | `20` | Generations to evolve. Recommend `100+`. |
| `--mut` | `0.15` | Mutation rate (DNA change probability). |
| `--seed` | `None` | Path to the vault directory for seed injection. |
| `--push-mid` | `False` | Reward strategies that prefer SPY/2xSPY over flipping between 3x and CASH. |
| `--no-ablation` | `False` | Disable "Indicator Ablation" (forces all indicators to stay active). |



### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows). 
# --promote: Update main genome.json with the best performer.
# --top X: Retain only Top X most resilient genomes and prune the rest.
python tests/vault_sweep.py --vault champions/v2_multi/vault --promote --top 20
```


