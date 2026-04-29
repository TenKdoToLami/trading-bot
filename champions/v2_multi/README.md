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

### 🧬 Genetic Evolution (Seeding)
Improve the champion by evolving from existing "seeds" in the vault.

```bash
# Basic Seeded Run
python tests/run_evolution_v2.py --seed champions/v2_multi/vault --pop 100 --gen 50
```

#### ⚙️ Evolution Parameters
| Parameter | Default | Description |
| :--- | :--- | :--- |
| `--seed` | `None` | Path to the vault directory for seed injection. |
| `--pop` | `50` | Population size (higher = more diversity, slower). |
| `--gen` | `20` | Number of generations to evolve. |
| `--mut` | `0.15` | Mutation rate (probability of DNA change). |
| `--no-ablation` | `False` | Disable "Indicator Ablation" (forces all indicators to stay active). |
| `--push-mid` | `False` | Reward strategies that prefer SPY/2xSPY over flipping between 3x and CASH. |



### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows). Use --promote to update champion.
python tests/vault_sweep.py --vault champions/v2_multi/vault --promote
```


