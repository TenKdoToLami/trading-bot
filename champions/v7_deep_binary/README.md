# V7 Deep Binary — Neuroevolutionary Risk Control

## 🧠 Strategy Logic
V7 Deep Binary is the **Defensive MLP** engine. It uses a Multi-Layer Perceptron to make a binary decision between **3x Leverage** and **CASH**. By stripping away the intermediate states, it focuses entirely on high-conviction regime switches.

### ⚙️ Decision Engine
- **Binary Softmax**: The neural network's final layer is mapped to a binary decision vector (Aggressive vs. Defensive).
- **Regime Filtering**: Specialized for identifying macro-economic "Breaking Points" using the same 13-signal input vector as V7 Standard.
- **Genetic Topology**: Evolves the weights and biases specifically for binary classification of market trends.

### 📈 Leverage States
- **CASH / 3xSPY** (Binary regime switching)

---

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v7_deep_binary/genome.json

# Behavioral X-Ray (Allocation DNA)
python tests/genome_xray.py champions/v7_deep_binary/genome.json
```

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows)
python tests/vault_sweep.py --vault champions/v7_deep_binary/vault --promote --top 20
```

### 🧬 Evolution
```bash
# Standard Evolution run
python tests/run_evolution_v7_deep_binary.py --pop 500 --gen 100 --ablation

# Seeded Evolution (Refine from vault)
python tests/run_evolution_v7_deep_binary.py --pop 300 --gen 50 --ablation --seed champions/v7_deep_binary/vault
```

#### ⚙️ Evolution Parameters
| Flag | Default | Description |
|------|---------|-------------|
| `--pop` | 100 | Population size. Recommend `500+` for Neuroevolution. |
| `--gen` | 50 | Number of generations. |
| `--mut` | 0.20 | Mutation rate (Gaussian noise). |
| `--seed`| `None` | Path to vault dir for seed injection. |
| `--ablation` | `Off` | Enable **Indicator Ablation**. |
| `--min-cagr` | `30.0` | **Vault-Lock**. Minimum CAGR threshold for saving results. |
