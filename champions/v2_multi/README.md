# V2 Multi — Multi-Leverage AI

## 🧠 Strategy Logic
V2 was the first version to explore **Multi-Asset Leverage**. It uses four distinct "Brain states" to select between discrete leverage levels.

### 🔬 Decision Engine Anatomy
1.  **Multi-Brain Scoring**: Simultaneously runs 4 independent scoring engines—Panic, Neutral, Moderate, and Aggressive.
2.  **Priority Waterfall**:
    *   **Tier 1 (Panic)**: If Panic Brain > Threshold, all other signals are overridden; exit to **CASH**.
    *   **Tier 2 (Aggressive)**: If Bull Brain > Threshold, scale to **3x SPY**.
    *   **Tier 3 (Moderate)**: If Neutral Brain > Threshold, hold **2x SPY**.
    *   **Tier 4 (Baseline)**: Default to **1x SPY**.
3.  **Hysteresis Locking**: Implements a `lock_days` timer to prevent rapid cycling between regimes, ensuring the strategy remains "sticky" during volatile transitions.

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
| `--min-cagr` | `35.0` | Minimum CAGR % threshold for saving to the vault. |



### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows). 
# --promote: Update main genome.json with the best performer.
# --top X: Retain only Top X most resilient genomes and prune the rest.
python tests/vault_sweep.py --vault champions/v2_multi/vault --promote --top 20
```


