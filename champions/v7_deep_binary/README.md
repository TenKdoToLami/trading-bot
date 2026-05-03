# V7 Deep Binary — Neuroevolutionary Risk Control

## 🧠 Strategy Logic
V7 Deep Binary is the **Defensive MLP** engine. It uses a Multi-Layer Perceptron to make a binary decision between **3x Leverage** and **CASH**. By stripping away the intermediate states, it focuses entirely on high-conviction regime switches.

### 🔬 Decision Engine Anatomy
1.  **Binary Input Vector**: Consumes 13 normalized technical indicators + Macro VIX/Yield Curve.
2.  **Neural MLP Architecture**: Uses a single-hidden-layer MLP with ReLU activation, specifically evolved for **Binary Classification**.
3.  **Binary Softmax Mapping**: The output layer generates two probabilities:
    *   **Node 0**: Probability of Defensive Regime (**CASH**).
    *   **Node 1**: Probability of Aggressive Regime (**3x SPY**).
4.  **Argmax Selection**: The highest-probability state is selected daily, creating a "Switch" behavior with no intermediate 1x/2x states.
5.  **Ablation Pruning**: The model can genetically disable weak signals to maintain a sparse, robust logic tree.

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
python tests/run_evolution_universal.py --version v7_deep_binary --pop 500 --gen 100 --ablation

# Seeded Evolution (Refine from vault)
python tests/run_evolution_universal.py --version v7_deep_binary --pop 300 --gen 50 --ablation --seed champions/v7_deep_binary/vault
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
