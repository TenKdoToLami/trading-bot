# V6 Balancer — Multi-Asset Risk Parity

## 🧠 Strategy Logic
V6 Balancer is a **Dynamic Asset Allocation** engine. Unlike the SPY-focused logic of previous versions, the Balancer manages a diversified portfolio (e.g., SPY, QQQ, TLT) and dynamically rebalances between them based on volatility-weighted risk parity and momentum signals.

### ⚙️ Decision Engine
- **Volatility Weighting**: Automatically scales asset weights based on their relative risk contribution.
- **Momentum Overlay**: Enhances risk parity with trend-following filters to avoid "catching falling knives."
- **Genetic Rebalancing**: Evolved lookback periods for calculating volatility and momentum.
- **Institutional Guardrails**: Includes evolved friction modeling to optimize rebalancing frequency.

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
