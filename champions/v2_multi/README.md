# V2 Multi — Multi-Leverage AI
		
## 🧠 Strategy Logic
V2 was the first version to explore **Multi-Asset Leverage**. It uses four distinct "Brain states" (Panic, 3x, 2x, 1x) to select between discrete leverage levels based on market conditions.

### 🔬 Decision Engine Anatomy
1.  **Multi-Brain Scoring**: Simultaneously runs 4 independent scoring engines to determine the optimal exposure level.
2.  **Priority Waterfall**: Uses a hierarchical selection process where safety (Panic/CASH) always overrides aggression.
3.  **Hysteresis Locking**: Implements a `lock_days` timer to prevent rapid cycling between regimes, ensuring rebalances are intentional.
4.  **Indicator Ablation**: Capable of dynamically "turning off" noise-heavy indicators during the evolutionary process.

---

## ⚡ QUICK LAUNCH: V2 Multi Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_universal.py --version v2_multi --pop 100 --gen 100` |
| **Seed Run** | `python tests/run_evolution_universal.py --version v2_multi --pop 100 --gen 100 --vault champions/v2_multi/vault --mut 0.4` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v2_multi/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v2_multi/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v2_multi/vault --promote --top 20` |

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size. |
| `--gen` | `50` | Number of generations. |
| `--mut` | `0.20` | Mutation rate. |
| `--vault` | `None` | Path to load seeds from. |
| `--min-cagr` | `35.0` | Minimum CAGR threshold for saving results. |
| `--push-mid` | `False` | Reward strategies that prefer SPY/2xSPY over flipping between 3x and CASH. |
| `--no-ablation`| `True` | Disable "Indicator Ablation" (forces all indicators to stay active). |

---

## 🛡️ Best Used For
The "Diversified Leverage" play. V2 is ideal for traders who want more granularity than a binary "CASH vs 3x" switch, allowing the bot to downshift into 1x or 2x positions when market confidence is moderate but not yet panicked.
