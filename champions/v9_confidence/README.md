# V9 Confidence — The Institutional Neuro-Ensemble

## 🧠 Strategy Logic
V9 Confidence represents the peak of the V-series neural architectures. It combines a **Deep Neural Network** with a **Confidence Thresholding** layer. Instead of simply predicting the best asset, it calculates a conviction score—if the network is "unsure," it automatically defaults to a defensive posture.

### 🔬 Decision Engine Anatomy
1.  **Confidence-Weighted MLP**: A deep neural network that outputs both a target allocation and a confidence coefficient.
2.  **Dynamic Hysteresis & Smoothing**: Uses evolved exponential smoothing on signals to filter out high-frequency volatility and "ghost" signals.
3.  **Conviction Gating**: If the conviction score falls below an evolved threshold, the model downshifts leverage regardless of the raw signal.
4.  **Multi-Brain Synthesis**: Leverages 13 market features with non-linear cross-correlations, allowing it to "anticipate" regime shifts.

---

## ⚡ QUICK LAUNCH: V9 Confidence Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_universal.py --version v9_confidence --pop 100 --gen 100` |
| **Seed Run** | `python tests/run_evolution_universal.py --version v9_confidence --pop 100 --gen 100 --vault champions/v9_confidence/vault --mut 0.4` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v9_confidence/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v9_confidence/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v9_confidence/vault --promote --top 20` |

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size. |
| `--gen` | `50` | Number of generations. |
| `--mut` | `0.20` | Mutation rate (DNA change probability). |
| `--vault` | `None` | Path to load seeds from. |
| `--min-cagr` | `35.0` | Minimum CAGR threshold for saving results. |

---

## 🛡️ Best Used For
The "Professional Allocator." V9 is designed for large portfolios where drawdown protection and signal conviction are just as important as raw CAGR. It is the most "stable" of the high-performance neural models.
