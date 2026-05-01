# V7 Deep — Neuroevolutionary Logic

## 🧠 Strategy Logic
V7 Deep uses a **Multi-Layer Perceptron (MLP)** neural network evolved via Gaussian Neuroevolution. Unlike traditional weighted-brain strategies, V7 evolves high-dimensional non-linear relationships between 11 market signals to determine the optimal leverage state.

### 🔬 Decision Engine Anatomy
1.  **Direct Feature Injection**: Consumes 13 raw technical indicators (SMA/EMA, RSI, MACD, etc.) + Macro context (VIX, Yield Curve).
2.  **Neural MLP Architecture**: Uses a single-hidden-layer Multilayer Perceptron (MLP) with **ReLU activation** to model non-linear market relationships.
3.  **Conviction Normalization**: Converts the hidden layer output into 4 absolute confidence values using a **Softmax** layer for **CASH, 1x, 2x, and 3x**.
4.  **Argmax Selection**: The allocation with the highest daily probability is selected for execution.
5.  **Indicator Ablation**: During evolution, the network can "turn off" specific indicator weights, allowing it to ignore market noise and focus only on high-alpha signals.

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
