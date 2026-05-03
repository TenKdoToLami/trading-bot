# V7 Deep Fluid — Continuous Neural Scaling

## 🧠 Strategy Logic
V7 Deep Fluid is the **Dynamic Exposure** engine. It uses a Multi-Layer Perceptron to determine a continuous leverage value between **0.0 (CASH)** and **3.0 (3xSPY)**. Unlike the discrete states of V7 Standard or Binary, Fluid can scale exposure in 0.1 increments based on its neural conviction.

### ⚙️ Decision Engine
- **Continuous Output**: The neural network's final layer uses a scaled Tanh or Sigmoid activation to map to a continuous leverage range.
- **Micro-Scaling**: Perfectly suited for choppy markets where 1x is too much but 0x is too little.
- **Genetic Topology**: Evolves weights and biases optimized for regression (continuous value prediction) rather than classification.

### 📈 Leverage States
- **0.0 to 3.0 (Continuous)**

---

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v7_deep_fluid/genome.json

# Behavioral X-Ray (Allocation DNA)
python tests/genome_xray.py champions/v7_deep_fluid/genome.json
```

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows)
python tests/vault_sweep.py --vault champions/v7_deep_fluid/vault --promote --top 20
```

### 🧬 Evolution
```bash
# Standard Evolution run
python tests/run_evolution_universal.py --version v7_deep_fluid --pop 500 --gen 100 --ablation

# Seeded Evolution (Refine from vault)
python tests/run_evolution_universal.py --version v7_deep_fluid --pop 300 --gen 50 --ablation --seed champions/v7_deep_fluid/vault
```

#### ⚙️ Evolution Parameters
| Flag | Default | Description |
|------|---------|-------------|
| `--pop` | 100 | Population size. Recommend `500+` for regression-MLPs. |
| `--gen` | 50 | Number of generations. |
| `--mut` | 0.20 | Mutation rate (Gaussian noise). |
| `--seed`| `None` | Path to vault dir for seed injection. |
| `--ablation` | `Off` | Enable **Indicator Ablation**. |
| `--min-cagr` | `30.0` | **Vault-Lock**. Minimum CAGR threshold for saving results. |
