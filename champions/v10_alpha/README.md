# Model V10: The Triple-Brain Ensemble (Expert System)

Model V10 represents a paradigm shift from monolithic neural networks to a **Hierarchical Expert Ensemble**. It treats the market as a series of asymmetric "Market Physics" events.

### 🧠 The Triple-Brain Architecture
1.  **Brain A (The Bull Specialist)**: A high-precision neural network trained exclusively on "Perfect Rallies." It is fed with indicators that the Profiler has determined to be most predictive in uptrends.
2.  **Brain B (The Bear Specialist)**: A specialized "Crash Detector." This brain has **Priority Veto Power**. If its confidence exceeds a specific threshold, it overrides Brain A, forcing the system into CASH regardless of how bullish the other indicators look.
3.  **Brain C (The MixMaster)**: A final decision layer that ingests the outputs of Brains A & B along with macro volatility (VIX). It calculates the final optimal portfolio mix (0x to 3x leverage).

### 🔬 Phase 1: The Indicator Profiler
Before the brains are trained, the **V10 Profiler** performs an exhaustive "Sensitivity Analysis" on every technical indicator.

**It answers two critical questions:**
- **Duration**: At what lookback (e.g., SMA 50 vs SMA 200) does this indicator have the most "Certainty"?
- **Threshold**: At what specific value (e.g., RSI < 28.5) does the historical Win Rate exceed 75%?

**Usage:**
```bash
# Scan data/SPY.csv to find optimal indicator profiles for a 20-day horizon
python src/tournament/v10_profiler.py --data data/history_SPY.csv --horizon 20 --out champions/v10_alpha/indicator_profiles.json
```

**Workflow:**
1.  **Profile**: Run the Profiler to generate `indicator_profiles.json`.
    ```bash
    python src/tournament/v10_profiler.py --data data/history_SPY.csv --horizon 20 --out champions/v10_alpha/indicator_profiles.json
    ```
2.  **Evolve**: Use the evolution engine to train the three brains.
    ```bash
    # Train with a population of 100 for 50 generations
    python tests/run_evolution_v10_expert.py --pop 100 --gen 50
    ```
3.  **Promote**: Identify the best genome in the vault and use it in your live strategy.

---

### 🧬 Evolution Parameters
| Flag | Default | Description |
|------|---------|-------------|
| `--pop` | 50 | Population size. Higher = more diversity. |
| `--gen` | 20 | Number of generations to train. |
| `--mut` | 0.2 | Mutation rate (probability of DNA change). |
| `--vault`| `vault/` | Directory where winning brains are saved. |
