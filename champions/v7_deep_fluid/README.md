# V7 Deep Fluid — Neural Portfolio Distribution

## 🧠 Strategy Logic
V7 Deep Fluid is the most advanced version of the neuroevolutionary series. Instead of picking a single leverage tier, it treats the market as a continuum.

### 🌊 The Fluid Brain
- **Architecture**: 13 Inputs -> 24 Hidden Neurons -> 4 Output Neurons (Softmax Layer).
- **Decision Engine**: It produces a probability distribution across **CASH**, **1x**, **2x**, and **3x**.
- **Portfolio Weighting**: The strategy holds a weighted average. If the AI is 50% Bullish (3x) and 50% Bearish (CASH), it will effectively hold **1.5x leverage**.
- **Friction Shield**: Includes a `rebalance_threshold` parameter. The bot will only adjust its positions if the suggested shift is significant (default > 5%), protecting you from "fee bleed" during low-confidence market noise.

### 📈 Leverage States
- **Dynamic Distribution** (CASH / SPY / 2xSPY / 3xSPY)

---

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v7_deep_fluid/genome.json

# Behavioral X-Ray (Logic DNA)
python tests/genome_xray.py champions/v7_deep_fluid/genome.json
```

### 🧬 Genetic Evolution (Fluid Neuroevolution)
```bash
# Blind Start (Recommended)
python tests/run_evolution_v7_deep_fluid.py --pop 300 --gen 100 --min-cagr 0.35

# Seeded Evolution (Can seed from V7 Deep or V7 Fluid)
python tests/run_evolution_v7_deep_fluid.py --seed champions/v7_deep/vault --pop 100 --gen 50
```

#### ⚙️ Evolution Parameters
| Parameter | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size. |
| `--gen` | `50` | Generations. |
| `--mut` | `0.20` | Mutation rate. |
| `--min-cagr`| `0.30` | Vault threshold. |

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows). 
# --promote: Update main genome.json with the best performer.
# --top X: Retain only Top X most resilient genomes and prune the rest.
python tests/vault_sweep.py --vault champions/v7_deep_fluid/vault --promote --top 20
```
