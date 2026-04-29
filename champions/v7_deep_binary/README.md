# V7 Deep Binary — Deep Risk-On / Risk-Off

## 🧠 Strategy Logic
This is a streamlined version of the V7 Deep Brain. It uses a Neural Network (MLP) to make a **Binary Decision**: either 3x Leveraged SPY or CASH.

### ⚙️ The Deep Binary Brain
- **Architecture**: 13 Inputs -> 24 Hidden Neurons (ReLU) -> 2 Output Neurons.
- **Goal**: By removing the 1x and 2x tiers, we force the AI to focus entirely on the "Switch" between extreme aggression and extreme safety. This simplifies the search space for the Genetic Algorithm.
- **Decision Engine**: High-confidence Risk-On (3x) vs. High-confidence Risk-Off (CASH).

### 📈 Leverage States
- **CASH / 3xSPY**

---

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v7_deep_binary/genome.json

# Behavioral X-Ray (Logic DNA)
python tests/genome_xray.py champions/v7_deep_binary/genome.json
```

### 🧬 Genetic Evolution (Binary Neuroevolution)
```bash
# Blind Start
python tests/run_evolution_v7_deep_binary.py --pop 200 --gen 100 --min-cagr 0.35

# Seeded Evolution
python tests/run_evolution_v7_deep_binary.py --seed champions/v7_deep_binary/vault --pop 100 --gen 50
```

#### ⚙️ Evolution Parameters
| Parameter | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size. |
| `--gen` | `50` | Generations. |
| `--mut` | `0.20` | Mutation rate (Gaussian noise). |
| `--min-cagr`| `0.30` | Vault threshold. |

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep
python tests/vault_sweep.py --vault champions/v7_deep_binary/vault --promote
```
