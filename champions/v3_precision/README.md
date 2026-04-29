# V3 Precision — The Aggressive Switcher

## 🧠 Strategy Logic
V3 is a highly optimized **Binary State Machine**. It is the first version to use Genetic evolution for both indicator weights and thresholds.

### ⚙️ Decision Engine
- **Bull vs Panic**: Compares two brain scores to decide between maximum exposure or safety.
- **Time Lock**: Uses a `lock_days` parameter to prevent high-frequency flipping (whipsaw).

### 📈 Leverage States
- **CASH**: Total defense.
- **3x SPY**: Maximum aggression.

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v3_precision/genome.json

# Behavioral X-Ray (Allocation DNA)
python tests/genome_xray.py champions/v3_precision/genome.json
```

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows). 
# --promote: Update main genome.json with the best performer.
# --top X: Retain only Top X most resilient genomes and prune the rest.
python tests/vault_sweep.py --vault champions/v3_precision/vault --promote --top 20
```

### 🧬 Evolution
```bash
# Cold Start Evolution
python tests/run_evolution_v3_precision.py --pop 500 --gen 100

# Seeded Evolution (Refine Champions)
python tests/run_evolution_v3_precision.py --pop 500 --gen 50 --mut 0.25 --seed champions/v3_precision/vault

#### ⚙️ Evolution Parameters
| Parameter | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `50` | Population size (higher = more diversity). |
| `--gen` | `20` | Number of generations to evolve. |
| `--mut` | `0.15` | Mutation rate (DNA change probability). Use `0.25+` for seeding. |
| `--seed` | `None` | Path to the vault directory for seed injection. |
| `--ablation` | `False` | Enable "Indicator Ablation" (allows GA to disable weak indicators). |
