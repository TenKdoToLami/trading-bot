# V9 Confidence Spread — Hysteresis-based Macro Intelligence

## 🧠 Strategy Logic
V9 Confidence Spread is the **Stability-First** evolution of the V7 neural engine. It solves the "trade slippage" problem by implementing a discrete confidence-based decision engine with built-in hysteresis and signal smoothing.

### 🔬 Decision Engine Anatomy
1.  **Feature Ingestion**: Ingests 13 normalized technical indicators (SMA/EMA Distances, RSI, MACD, ADX, TRIX, Slope, Volatility, ATR) + Macro context (VIX, Yield Curve).
2.  **Neural Inference**: A Multilayer Perceptron (MLP) performs a weighted forward pass to calculate "conviction energy" for 4 discrete regimes.
3.  **Softmax Normalization**: Raw neural outputs are converted into probabilities (0.0 to 1.0) that sum to unity.
4.  **Temporal Smoothing**: Probabilities are processed through an Exponential Moving Average (EMA) window to filter high-frequency market noise.
5.  **Hysteresis Gating**: To prevent "flip-flopping," a transition to a new regime only occurs if its smoothed probability exceeds the current regime by the `hysteresis` threshold (e.g., +0.15).
6.  **Allocation Selection**: The regime with the highest gated probability (Argmax) is selected for the next trading day.

### 📈 Leverage States
- **CASH (0x)**: Defensive posture / Panic mitigation.
- **SPY (1x)**: Standard market exposure.
- **2xSPY**: Bullish momentum / Trend following.
- **3xSPY**: High-conviction aggressive scaling.

---

## 🚀 Execution Commands
```bash
python tests/vault_sweep.py --vault champions/v9_confidence/vault --promote --top 20
```


### 🧬 Evolution
```bash
# Standard Evolution (Optimized for Hysteresis)
python tests/run_evolution_v9_confidence.py --pop 100 --gen 50 --min-cagr 30.0 --ablation

# Seeded Evolution (Refine from V7 or existing V9 vault)
python tests/run_evolution_v9_confidence.py --pop 200 --gen 30 --seed champions/v9_confidence/vault --ablation
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
| `--ablation` | `Off` | Enable **Neural Ablation** (Network learns to ignore weak inputs). |
| `--min-cagr` | `25.0` | Minimum CAGR threshold for saving to vault. |
