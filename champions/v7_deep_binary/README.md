# V7 Deep Binary — The Defensive Switch

## 🧠 Strategy Logic
V7 Deep Binary is the **Neuro-Switch** engine. It uses a Multi-Layer Perceptron to make high-conviction decisions between **3x Leverage** and **CASH**. By stripping away intermediate states (1x, 2x), it focuses entirely on identifying major regime shifts with maximum precision.

### 🔬 Decision Engine Anatomy
1.  **Binary MLP Architecture**: Features a single-hidden-layer neural network specifically evolved for **Binary Classification**.
2.  **Argmax Softmax Mapping**: The output layer generates probabilities for "Aggressive" vs "Defensive" regimes. The bot selects the dominant state daily.
3.  **High-Conviction Filtering**: Designed to ignore market "noise" and only rebalance when the neural network detects a fundamental shift in technical indicators.
4.  **Ablative Pruning**: Supports Indicator Ablation to genetically disable weak features, resulting in a sparse and robust decision tree.

---

## ⚡ QUICK LAUNCH: V7 Binary Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_universal.py --version v7_deep_binary --pop 100 --gen 100` |
| **Seed Run** | `python tests/run_evolution_universal.py --version v7_deep_binary --pop 100 --gen 100 --vault champions/v7_deep_binary/vault --mut 0.4` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v7_deep_binary/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v7_deep_binary/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v7_deep_binary/vault --promote --top 20` |

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size. Recommend `500+` for Neuroevolution. |
| `--gen` | `50` | Number of generations. |
| `--mut` | `0.20` | Mutation rate (adjusts weight/bias variance). |
| `--vault` | `None` | Path to load seeds from. |
| `--min-cagr` | `30.0` | Minimum CAGR threshold for saving results. |

---

## 🛡️ Best Used For
The "Sentry." V7 Binary is best for aggressive portfolios that want to be "All In" during bull runs and "All Out" during crashes, skipping the volatility and friction of intermediate leverage tiers.
