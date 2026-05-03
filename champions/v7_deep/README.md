# V7 Deep — The Neural Frontier

## 🧠 Strategy Logic
V7 Deep is a complete departure from heuristic logic. It uses a **Deep Neural Network** (MLP) architecture evolved through Genetic Algorithms. Instead of human-defined rules, the network learns complex non-linear relationships between indicators to predict the optimal leverage state.

### 🔬 Decision Engine Anatomy
1.  **Neural Architecture**: Features a multi-layer perceptron (MLP) with evolved weights and biases, processing 13 distinct market features.
2.  **Softmax Output Layer**: The final layer produces a probability distribution across four assets (Cash, 1x, 2x, 3x), resolving into a weighted portfolio allocation.
3.  **Black-Box Optimization**: Evolution treats the entire network as a genome, optimizing the weights to maximize CAGR while penalizing drawdown through the fitness function.
4.  **Non-Linear Feature Interaction**: Capable of detecting subtle correlations (e.g., VIX spikes coinciding with specific Yield Curve inversions) that discrete logic would miss.

---

## ⚡ QUICK LAUNCH: V7 Deep Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_v7_deep.py --pop 100 --gen 100` |
| **Seed Run** | `python tests/run_evolution_v7_deep.py --pop 100 --gen 100 --vault champions/v7_deep/vault --mut 0.4` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v7_deep/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v7_deep/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v7_deep/vault --promote --top 20` |

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size. |
| `--gen` | `50` | Number of generations. |
| `--mut` | `0.20` | Mutation rate (adjusts weight/bias variance). |
| `--vault` | `None` | Path to load seeds from. |
| `--min-cagr` | `25.0` | Minimum CAGR threshold for saving results. |

---

## 🛡️ Best Used For
The "Edge Seeker." V7 is for environments where traditional indicators are failing or the market has become highly efficient. Its neural structure allows it to find "pockets" of alpha that are invisible to linear models.
