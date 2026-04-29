# V5 Sniper — High-Fidelity Mean Reversion

## 🧠 Strategy Logic
V5 Sniper is a **Precision Mean-Reversion** engine. Unlike the trend-following logic of V1-V3, the Sniper focuses on identifying overextended market conditions using RSI, ADX, and Realized Volatility to "Snipe" entries and exits with high accuracy.

### ⚙️ Decision Engine
- **RSI Snapback**: Evolved thresholds for deep-value entry during bull regimes.
- **Vol-Adaptive Exit**: Dynamically tightens exit criteria as realized volatility spikes.
- **Genetic Lookbacks**: All indicator lookbacks are evolved to match the specific "Sniper" frequency.
- **Ablation Mode**: Supports evolutionary pruning of weak signals for better generalization.

### 📈 Leverage States
- **CASH / 1x / 2x / 3x** (Precision-scaled exposure)

---

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v5_sniper/genome.json

# Behavioral X-Ray (Allocation DNA)
python tests/genome_xray.py champions/v5_sniper/genome.json
```

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows)
python tests/vault_sweep.py --vault champions/v5_sniper/vault --promote --top 20
```

### 🧬 Evolution
```bash
# Standard Evolution run
python tests/run_evolution_v5_sniper.py --pop 1000 --gen 100 --ablation

# Seeded Evolution (Refine from vault)
python tests/run_evolution_v5_sniper.py --pop 1000 --gen 100 --ablation --seed champions/v5_sniper/vault
```

#### ⚙️ Evolution Parameters
| Flag | Default | Description |
|------|---------|-------------|
| `--pop` | 300 | Population size. |
| `--gen` | 100 | Number of generations. |
| `--mut` | 0.20 | Mutation rate. Use `0.40` for aggressive exploration. |
| `--seed`| `None` | Path to vault dir for seed injection. |
| `--ablation` | `Off` | Enable **Indicator Ablation** (AI prunes its own logic tree). |
| `--min-cagr` | `30.0` | **Vault-Lock**. Minimum CAGR threshold for saving results. |
