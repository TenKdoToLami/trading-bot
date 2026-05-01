# V4 Precision — 3-State AI Architecture

## 🧠 Strategy Logic
V4 Precision is the most advanced "Weighted Brain" engine in the fleet. It uses a **Dual-Brain Architecture** (Panic vs Bull) to determine transitions between CASH, SPY (Neutral), and 3xSPY (Bullish). 

### 🔬 Decision Engine Anatomy
1.  **Genetic Feature Lookbacks**: Unlike V1-V2, every indicator lookback (SMA, RSI, MACD, etc.) is an evolved gene, allowing the AI to "tune" its temporal resolution for each signal.
2.  **Dual-Brain Scoring**: Calculates a **Panic Score** and a **Bull Score** using a high-dimensional weight matrix.
3.  **Conviction Gating**:
    *   **Panic State**: Triggered if Panic Score > Threshold. Force-exits to **CASH**.
    *   **Bull State**: Triggered if Bull Score > Threshold. Scales to **3x SPY**.
    *   **Neutral State**: Default behavior. Holds **1x SPY** (unleveraged index).
4.  **Temporal Lockout**: Implements an evolved `lock_days` parameter to stabilize the regime and prevent high-frequency rebalancing costs.

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
