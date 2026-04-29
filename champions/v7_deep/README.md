# V7 Deep — Neuroevolutionary Brain

## 🧠 Strategy Logic
V7 replaces the linear weight-sum approach with a **Deep Multi-Layer Perceptron (MLP)**. This is the first "Truly Intelligent" version of the bot, capable of complex logic.

### ⚙️ The Deep Brain
- **Architecture**: 13 Inputs -> 24 Hidden Neurons (ReLU) -> 4 Output Neurons.
- **Decision Engine**: The network processes all indicators simultaneously and outputs a "Confidence Score" for each tier (CASH, 1x, 2x, 3x). The highest score dictates the portfolio.
- **Non-Linearity**: Because it uses ReLU activation functions, it can learn non-linear patterns (e.g., "Momentum is only good if Volatility is decreasing").

### 📈 Leverage States
- **CASH / 1x / 2x / 3x**

---

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v7_deep/genome.json

# Behavioral X-Ray (Logic DNA)
python tests/genome_xray.py champions/v7_deep/genome.json
```

### 🧬 Genetic Evolution (Neuroevolution)
Since V7 uses a neural network, it is trained using **Neuroevolution**.
```bash
# Blind Start (Highly Recommended for V7 to find new logic)
python tests/run_evolution_v7_deep.py --pop 500 --gen 100 --mut 0.35

# Seeded Evolution (Refinement)
python tests/run_evolution_v7_deep.py --seed champions/v7_deep/vault --pop 100 --gen 50
```

#### ⚙️ Evolution Parameters
| Parameter | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size (MLPs need higher diversity, suggest 200+). |
| `--gen` | `50` | Generations. |
| `--mut` | `0.20` | Mutation rate (Gaussian noise on matrices). |
| `--min-cagr`| `0.30` | Vault threshold (only saves "Quality" results). |

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows).
python tests/vault_sweep.py --vault champions/v7_deep/vault --promote
```
