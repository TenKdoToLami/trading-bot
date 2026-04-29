# V7 Deep — Neuroevolutionary Logic

## 🧠 Strategy Logic
V7 Deep uses a **Multi-Layer Perceptron (MLP)** neural network evolved via Gaussian Neuroevolution. Unlike traditional weighted-brain strategies, V7 evolves high-dimensional non-linear relationships between 11 market signals to determine the optimal leverage state.

### ⚙️ Decision Engine
- **Non-Linear Inference**: Captures complex market regimes that simple weighted sums might miss.
- **Genetic Topology**: Eevolves the weights and biases of the hidden layers.
- **Indicator Ablation**: Supports evolutionary pruning of input signals directly from the neural network's input vector.
- **Institutional Guardrails**: Includes evolved "Decision Thresholds" to control the activation sensitivity of the network.

### 📈 Leverage States
- **CASH / 1x / 2x / 3x** (Neural-scaled allocation)

---

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v7_deep/genome.json

# Behavioral X-Ray (Allocation DNA)
python tests/genome_xray.py champions/v7_deep/genome.json
```

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows)
python tests/vault_sweep.py --vault champions/v7_deep/vault --promote --top 20
```

### 🧬 Evolution
Optimizes neural network weights using **Gaussian Neuroevolution**.
```bash
# Standard high-diversity run
python tests/run_evolution_v7_deep.py --pop 500 --gen 100 --ablation

# Seeded Evolution (Refine using your best neural genomes)
python tests/run_evolution_v7_deep.py --pop 300 --gen 50 --ablation --seed champions/v7_deep/vault
```

#### ⚙️ Evolution Parameters
| Flag | Default | Description |
|------|---------|-------------|
| `--pop` | 100 | Population size. Recommend `500+` for MLPs. |
| `--gen` | 50 | Number of generations. |
| `--mut` | 0.20 | Mutation rate (Gaussian noise applied to weights). |
| `--seed`| `None` | Path to vault dir for seed injection. |
| `--ablation` | `Off` | Enable **Indicator Ablation** (Network learns to ignore weak inputs). |
| `--min-cagr` | `30.0` | **Vault-Lock**. Minimum CAGR threshold for saving results. |
