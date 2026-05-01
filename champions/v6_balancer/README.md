# V6 Balancer — Multi-Asset Risk Parity

## 🧠 Strategy Logic
V6 Balancer is a **Dynamic Asset Allocation** engine. Unlike the SPY-focused logic of previous versions, the Balancer manages a diversified portfolio (e.g., SPY, QQQ, TLT) and dynamically rebalances between them based on volatility-weighted risk parity and momentum signals.

### 🔬 Decision Engine Anatomy
1.  **Portfolio Ingestion**: Monitors price and volatility data across multiple asset classes (Equity, Bonds, Cash).
2.  **Volatility Weighting**: Calculates the relative risk contribution of each asset using evolved lookback periods.
3.  **Softmax Allocation**: Applies a **Softmax normalization** across raw scores to determine the target capital distribution.
4.  **Momentum Filter**: Overlays a trend-following logic that can prune or down-weight assets exhibiting negative macro-momentum.
5.  **Rebalance Optimization**: Only executes a trade if the suggested weight change exceeds the evolved efficiency threshold, minimizing transaction costs.

### 📈 Leverage States
- **Multi-Asset Allocation** (Dynamic weights across the portfolio)

---

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v6_balancer/genome.json

# Behavioral X-Ray (Allocation DNA)
python tests/genome_xray.py champions/v6_balancer/genome.json
```

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows)
python tests/vault_sweep.py --vault champions/v6_balancer/vault --promote --top 20
```

### 🧬 Evolution
```bash
# Standard Evolution run
python tests/run_evolution_v6_balancer.py --pop 1000 --gen 100 --ablation

# Seeded Evolution (Refine from vault)
python tests/run_evolution_v6_balancer.py --pop 1000 --gen 100 --ablation --seed champions/v6_balancer/vault
```

#### ⚙️ Evolution Parameters
| Flag | Default | Description |
|------|---------|-------------|
| `--pop` | 300 | Population size. |
| `--gen` | 100 | Number of generations. |
| `--mut` | 0.20 | Mutation rate. |
| `--seed`| `None` | Path to vault dir for seed injection. |
| `--ablation` | `Off` | Enable **Indicator Ablation** (AI prunes its own logic tree). |
| `--min-cagr` | `20.0` | **Vault-Lock**. Minimum CAGR threshold for saving results. |
