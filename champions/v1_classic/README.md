# V1 Classic — The Linear Indicator Baseline

## 🧠 Strategy Logic
The original weighted-sum approach. This model calculates a "Base Score" and a "Panic Score" using a linear combination of 9 technical indicators (SMA, EMA, RSI, MACD, ADX, TRIX, Slope, Volatility, ATR).

### 🔬 Decision Engine Anatomy
1.  **Weighted Sum**: Each indicator is multiplied by a genetic weight and summed.
2.  **Ablation Support**: The AI can "disable" specific indicators if they are contributing to overfitting.
3.  **Panic Override**: If the Panic Score exceeds the threshold, the bot immediately retreats to CASH.
4.  **Tiered Leverage**: Maps the Base Score to 4 levels (CASH, 1x, 2x, 3x).

---

## ⚡ QUICK LAUNCH: V1 Classic Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_universal.py --version v1_classic --pop 100 --gen 100` |
| **Seed Run** | `python tests/run_evolution_universal.py --version v1_classic --pop 100 --gen 100 --vault champions/v1_classic/vault --mut 0.4` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v1_classic/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v1_classic/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v1_classic/vault --promote --top 20` |

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size. |
| `--gen` | `50` | Number of generations. |
| `--mut` | `0.20` | Mutation rate. Use `0.35 - 0.50` for aggressive jumps when seeding. |
| `--vault`| `None` | Path to load seeds from. |
| `--min-cagr`| `30.0` | **Vault-Lock**. Minimum CAGR threshold for saving results. |
| `--ablation` | `False` | Set to True to let the AI disable redundant indicators. |

---

## 🛡️ Best Used For
The "Institutional Baseline." This model represents the standard way tactical portfolios have been managed for decades. Use it to verify that more complex neural models (V7-V10) are actually adding value over simple linear logic.
