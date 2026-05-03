# V10 Alpha — The Institutional Ensemble

## 🧠 Strategy Logic
V10 Alpha (Expert) is the ultimate evolution of the tactical bot. It uses a **Hierarchical Expert Ensemble** architecture. Instead of processing raw indicators, it consumes "Indicator Profiles" (pre-calculated expert signals) and synthesizes them through three independent neural brains (A, B, and C) to reach a final allocation.

### 🔬 Decision Engine Anatomy
1.  **Expert Signal Synthesis**: Consumes 20+ specialized "Indicator Profiles" that represent the best-of-breed logic from previous V-series models.
2.  **Triple-Brain Consensus**:
    *   **Brain A**: Focuses on long-term structural trends.
    *   **Brain B**: Analyzes short-term volatility regimes.
    *   **Brain C**: Synthesizes A & B into a finalized probability distribution.
3.  **Institutional Bear Veto**: Features a dedicated "Veto" layer that can force a retreat to CASH even if the neural consensus is bullish, based on extreme risk parameters.
4.  **Version 10 Logic**: The first model to be fully "Strategy-Aware," meaning it understands its own historical behavior and adjusts sensitivity dynamically.

---

## ⚡ QUICK LAUNCH: V10 Alpha Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_universal.py --version v10_alpha --pop 100 --gen 100` |
| **Seed Run** | `python tests/run_evolution_universal.py --version v10_alpha --pop 100 --gen 100 --vault champions/v10_alpha/vault --mut 0.4` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v10_alpha/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v10_alpha/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v10_alpha/vault --promote --top 20` |

### 📉 Data Management (Refresh Indicators)
The V10 engine calculates its internal expert signals automatically from the master cache. To ensure the bot is training on the latest market data, refresh the cache before running:
```bash
python src/helpers/data_provider.py
```

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size. |
| `--gen` | `50` | Number of generations. |
| `--mut` | `0.20` | Mutation rate (adjusts ensemble weighting variance). |
| `--vault` | `None` | Path to load seeds from. |
| `--min-cagr` | `30.0` | Minimum CAGR threshold for saving results. |

---

## 🛡️ Best Used For
The "Sovereign Wealth" play. V10 Alpha is designed for maximum resilience across decades of market data. It is the most sophisticated model in the library, offering the best risk-adjusted returns (Sharpe/Sortino) by using an ensemble of experts rather than a single point of failure.
