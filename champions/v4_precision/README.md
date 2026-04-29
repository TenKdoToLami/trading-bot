# V4 Precision — 3-State AI Architecture

## 🧠 Strategy Logic
V4 Precision is the most advanced "Weighted Brain" engine in the fleet. It uses a **Dual-Brain Architecture** (Panic vs Bull) to determine transitions between CASH, SPY (Neutral), and 3xSPY (Bullish). 

### ⚙️ Decision Engine
- **Genetic Lookbacks**: Unlike V1-V2, every indicator lookback (SMA, RSI, MACD, etc.) is evolved as a distinct gene.
- **Dynamic Weighting**: Scores indicators across 11 market signals to build a high-fidelity "Confidence Score".
- **Indicator Ablation**: Supports evolutionary pruning of weak indicators to prevent overfitting.
- **Institutional Guardrails**: Includes evolved "Lockout" periods to prevent over-trading.

### 📈 Leverage States
- **CASH / 1x / 3x** (Regime-based switching)

---

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
# Cross-Regime Sweep (Rolling 5yr Windows)
python tests/vault_sweep.py --vault champions/v4_precision/vault --promote --top 20
```

### 🧬 Evolution
```bash
# Standard Evolution run
python tests/run_evolution_v4_precision.py --pop 500 --gen 100 --ablation

# Seeded Evolution (Refine from vault)
python tests/run_evolution_v4_precision.py --pop 500 --gen 100 --ablation --seed champions/v4_precision/vault
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
