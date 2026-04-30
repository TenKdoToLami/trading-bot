# V9 Confidence Spread — Hysteresis-based Macro Intelligence

## 🧠 Strategy Logic
V9 Confidence Spread is the **Stability-First** evolution of the V7 neural engine. It solves the "trade slippage" problem by implementing a discrete confidence-based decision engine with built-in hysteresis and signal smoothing.

### ⚙️ Decision Engine
- **Confidence Scores**: The neural network outputs 4 discrete scores mapping to **CASH, 1x, 2x, and 3x**.
- **Signal Smoothing**: Applies a low-pass filter (Exponential Moving Average) to the confidence scores before a decision is made. This filters out daily market noise.
- **Hysteresis (Stickiness)**: To switch from state A to state B, the confidence in B must exceed the confidence in A by a set `hysteresis` margin (e.g., 0.15).
- **Minimum Hold**: Enforces a minimum holding period after every switch to prevent high-frequency rebalancing.

### 📈 Leverage States
- **CASH (0x)**: Defensive posture.
- **SPY (1x)**: Standard market exposure.
- **2xSPY**: Bullish momentum.
- **3xSPY**: High-conviction aggressive scaling.

---

## 🚀 Execution Commands
```bash
```
python tests/vault_sweep.py --vault champions/v9_confidence/vault --promote --top 20


### 🧬 Evolution
```bash
# Standard Evolution (Optimized for Hysteresis)
python tests/run_evolution_v9_confidence.py --pop 100 --gen 50 --min-cagr 30.0

# Seeded Evolution (Refine from V7 or existing V9 vault)
python tests/run_evolution_v9_confidence.py --pop 200 --gen 30 --seed champions/v9_confidence/vault
```

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v9_confidence/genome.json
```

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
|------|---------|-------------|
| `--pop` | 100 | Population size. |
| `--gen` | 50 | Number of generations. |
| `--mut` | 0.20 | Mutation rate. |
| `--seed`| `None` | Path to seed vault for transfer learning. |
| `--min-cagr` | `25.0` | Minimum CAGR threshold for saving to vault. |
