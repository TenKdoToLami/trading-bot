# V7 Deep Fluid — Continuous Neural Scaling

## 🧠 Strategy Logic
V7 Deep Fluid is the **Dynamic Exposure** engine. It uses a Multi-Layer Perceptron to determine a continuous leverage value between **0.0 (CASH)** and **3.0 (3xSPY)**. Unlike discrete engines, Fluid can scale exposure in 0.1 increments based on its neural conviction.

### 🔬 Decision Engine Anatomy
1.  **Continuous Output Layer**: The final layer uses a scaled activation function to map neural output to a precise leverage value (e.g., 1.4x).
2.  **Micro-Scaling Capability**: Perfectly suited for choppy markets where 1x is too much exposure but 0x is too defensive.
3.  **Smooth Transitioning**: Minimizes the slippage and psychological impact of large, binary portfolio shifts by "easing" into and out of positions.
4.  **Regression-Based Evolution**: Evolved using a fitness function that rewards precision in scaling exposure relative to indicator volatility.

---

## ⚡ QUICK LAUNCH: V7 Fluid Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_universal.py --version v7_deep_fluid --pop 100 --gen 100` |
| **Seed Run** | `python tests/run_evolution_universal.py --version v7_deep_fluid --pop 100 --gen 100 --vault champions/v7_deep_fluid/vault --mut 0.4` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v7_deep_fluid/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v7_deep_fluid/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v7_deep_fluid/vault --promote --top 20` |

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size. Recommend `500+` for regression-MLPs. |
| `--gen` | `50` | Number of generations. |
| `--mut` | `0.20` | Mutation rate (adjusts weight/bias variance). |
| `--vault` | `None` | Path to load seeds from. |
| `--min-cagr` | `30.0` | Minimum CAGR threshold for saving results. |

---

## 🛡️ Best Used For
The "Smooth Operator." V7 Fluid is designed for environments where market trends are murky or transition slowly. Its ability to maintain "mid-tier" leverage (e.g., 1.5x) allows it to stay in the game without over-committing.
