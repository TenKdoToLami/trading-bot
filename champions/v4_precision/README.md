# V4 Precision — The Adaptive Machine

## 🧠 Strategy Logic
V4 Precision introduces **Adaptive Lookbacks**, allowing the AI to not only evolve the importance of indicators but also the specific time-windows they monitor. This makes it significantly more resilient to shifting market regimes than previous versions.

### 🔬 Decision Engine Anatomy
1.  **Dynamic Feature Engineering**: Evolution optimizes 10 distinct indicator lookbacks (SMA, RSI, MACD, etc.) for both Bull and Panic states.
2.  **Regime-Specific DNA**: Maintains two independent "brains" that process market data through different lenses depending on current volatility.
3.  **Hysteresis Safety**: Implements a sticky rebalance timer to filter out high-frequency noise and minimize slippage.
4.  **Ablation Support**: The Genetic Algorithm can dynamically disable indicators that contribute more noise than signal, simplifying the resulting logic.

---

## ⚡ QUICK LAUNCH: V4 Precision Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_universal.py --version v4_precision --pop 100 --gen 100` |
| **Seed Run** | `python tests/run_evolution_universal.py --version v4_precision --pop 100 --gen 100 --vault champions/v4_precision/vault --mut 0.4` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v4_precision/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v4_precision/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v4_precision/vault --promote --top 20` |

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size. |
| `--gen` | `50` | Number of generations. |
| `--mut` | `0.20` | Mutation rate. |
| `--vault` | `None` | Path to load seeds from. |
| `--min-cagr` | `30.0` | Minimum CAGR threshold for saving results. |
| `--no-ablation`| `True` | Disable indicator ablation (forces all indicators to stay active). |

---

## 🛡️ Best Used For
The "Professional Standard." V4 Precision is the sweet spot between the simplicity of V1 and the complexity of the neural models. It offers excellent risk-adjusted returns and is highly understandable through X-Ray diagnostics.
